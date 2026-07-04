"""Offline tests for the claude-service Phase-1 foundation (TASKS row B1).

Pure-Python, no network: exercises the spec gate, session store, prompt
builders, and the ClaudeClient parse/fallback/retry logic against a fake SDK
client. Run from ``backend/`` with the venv active:

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import unittest

from pydantic import TypeAdapter
from pydantic import ValidationError as PydanticValidationError

from app.claude import prompts
from app.claude.client import ClaudeClient, ClaudeError
from app.claude.session_store import SessionNotFound, SessionStore
from app.claude.spec_gate import SpecValidationError, extract_json, parse_spec
from app.schemas.dtos import BudgetBand, Candidate, SkillLevel
from app.schemas.spec import ProjectSpec

# A minimal but complete §6 spec (mirrors ARCHITECTURE.md §6 example).
VALID_SPEC = {
    "schema_version": "1.0",
    "project": {
        "name": "Wall-mounted pegboard tool organizer",
        "module": "mechanic",
        "skill_focus": ["measuring", "drilling"],
        "difficulty": "beginner",
        "time_budget": "afternoon",
        "estimated_cost_usd": 45,
        "summary": "A pegboard to hang tools, teaching wall anchoring.",
        "workspace_required": "A wall, a drill, floor space.",
    },
    "materials": [
        {
            "name": "Pegboard panel, 2ft x 4ft",
            "quantity": 1,
            "unit": "panel",
            "est_cost_usd": 20,
            "where_to_find": "Hardware store, panel aisle",
            "notes": "Pre-cut sizes are common.",
        }
    ],
    "tools": [
        {
            "name": "Power drill",
            "essential": True,
            "est_cost_usd": 0,
            "notes": "For pilot holes.",
            "alternatives": "A manual screwdriver works but is slow.",
        }
    ],
    "steps": [
        {
            "order": 1,
            "title": "Mark the mounting points",
            "instruction": "Measure and mark where the board will hang.",
            "safety_note": "Check for wiring before drilling.",
            "est_time_minutes": 15,
            "tools_used": ["Tape measure", "Pencil"],
            "materials_used": [],
        }
    ],
    "research_topics": [
        {
            "topic": "How to find a wall stud",
            "why": "Anchoring changes the fasteners you use.",
            "resources": [],
        }
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Spec gate
# ─────────────────────────────────────────────────────────────────────────────
class SpecGateTests(unittest.TestCase):
    def test_parse_dict(self):
        spec = parse_spec(VALID_SPEC)
        self.assertIsInstance(spec, ProjectSpec)
        self.assertEqual(spec.project.module, "mechanic")

    def test_parse_raw_json_string(self):
        spec = parse_spec(json.dumps(VALID_SPEC))
        self.assertEqual(spec.project.name, VALID_SPEC["project"]["name"])

    def test_parse_json_with_code_fence(self):
        fenced = "```json\n" + json.dumps(VALID_SPEC) + "\n```"
        self.assertIsInstance(parse_spec(fenced), ProjectSpec)

    def test_parse_json_with_prose_wrapper(self):
        wrapped = "Sure! Here is the spec:\n" + json.dumps(VALID_SPEC) + "\nHope that helps."
        self.assertIsInstance(parse_spec(wrapped), ProjectSpec)

    def test_extract_json_bare_fence(self):
        fenced = "```\n{\"a\": 1}\n```"
        self.assertEqual(extract_json(fenced), {"a": 1})

    def test_extract_json_array_after_prose(self):
        # Mirrors a web-search answer: prose text blocks then the JSON array.
        text = 'I\'ll search now.Let me look.[{"topic": "a", "resources": []}]'
        self.assertEqual(extract_json(text), [{"topic": "a", "resources": []}])

    def test_extract_json_object_after_prose(self):
        self.assertEqual(extract_json('Here you go: {"a": 1} thanks'), {"a": 1})

    def test_empty_string_raises(self):
        with self.assertRaises(SpecValidationError):
            parse_spec("   ")

    def test_non_object_raises(self):
        with self.assertRaises(SpecValidationError):
            parse_spec("[1, 2, 3]")

    def test_unparseable_raises(self):
        with self.assertRaises(SpecValidationError):
            parse_spec("this is not json at all")

    def test_extra_field_rejected(self):
        bad = json.loads(json.dumps(VALID_SPEC))
        bad["project"]["surprise"] = "nope"  # extra="forbid" on spec models
        with self.assertRaises(SpecValidationError) as ctx:
            parse_spec(bad)
        self.assertIn("project", str(ctx.exception))

    def test_missing_required_field_rejected(self):
        bad = json.loads(json.dumps(VALID_SPEC))
        del bad["schema_version"]
        with self.assertRaises(SpecValidationError):
            parse_spec(bad)

    def test_bad_enum_rejected(self):
        bad = json.loads(json.dumps(VALID_SPEC))
        bad["project"]["difficulty"] = "expert"  # not beginner|handy|pro
        with self.assertRaises(SpecValidationError):
            parse_spec(bad)


# ─────────────────────────────────────────────────────────────────────────────
# Session store
# ─────────────────────────────────────────────────────────────────────────────
class SessionStoreTests(unittest.TestCase):
    def setUp(self):
        self.store = SessionStore()

    def _mk(self):
        return self.store.create(
            skill_level=SkillLevel.beginner,
            budget_band=BudgetBand.under_30,
            description="a small shelf",
        )

    def test_create_and_get(self):
        s = self._mk()
        self.assertEqual(self.store.get(s.id).id, s.id)
        self.assertEqual(len(self.store), 1)

    def test_get_missing_raises(self):
        with self.assertRaises(SessionNotFound):
            self.store.get("nope")

    def test_ids_are_unique(self):
        ids = {self._mk().id for _ in range(50)}
        self.assertEqual(len(ids), 50)

    def test_turn_history_and_count(self):
        s = self._mk()
        s.add_user_turn("hi")
        s.add_assistant_turn("hello, what are we building?")
        s.add_user_turn("a spice rack")
        self.assertEqual(s.turn_count, 2)  # user turns only
        self.assertEqual([m["role"] for m in s.messages], ["user", "assistant", "user"])

    def test_remember_and_resolve_candidates(self):
        s = self._mk()
        c = Candidate(id="c1", title="Spice rack", summary="A small wall rack.")
        s.remember_candidates([c])
        self.assertIs(s.candidates["c1"], c)

    def test_delete(self):
        s = self._mk()
        self.store.delete(s.id)
        with self.assertRaises(SessionNotFound):
            self.store.get(s.id)

    def test_eviction_respects_cap(self):
        store = SessionStore(max_sessions=5)
        made = []
        for _ in range(8):
            made.append(
                store.create(
                    skill_level=SkillLevel.handy,
                    budget_band=BudgetBand.over_75,
                    description="x",
                )
            )
        self.assertLessEqual(len(store), 5)
        # The most-recently-created sessions survive.
        self.assertEqual(store.get(made[-1].id).id, made[-1].id)


# ─────────────────────────────────────────────────────────────────────────────
# Prompts
# ─────────────────────────────────────────────────────────────────────────────
class PromptTests(unittest.TestCase):
    def test_generation_prompt_embeds_constraints_and_guardrails(self):
        p = prompts.build_generation_system_prompt(SkillLevel.beginner, BudgetBand.under_30)
        self.assertIn("Beginner", p)
        self.assertIn("Under $30", p)
        self.assertIn("novice", p.lower())
        self.assertIn("safety note", p.lower())
        self.assertIn("never more than 3", p.lower())  # candidate cap (§7.1)
        self.assertIn("do not output json", p.lower())

    def test_generation_prompt_accepts_raw_string_values(self):
        p = prompts.build_generation_system_prompt("pro", "over_75")
        self.assertIn("Pro", p)
        self.assertIn("$75 or more", p)

    def test_finalize_instruction_pins_fields(self):
        f = prompts.build_finalize_instruction(SkillLevel.handy, BudgetBand.from_30_to_75)
        self.assertIn('"mechanic"', f)
        self.assertIn('"handy"', f)
        self.assertIn('"1.0"', f)
        self.assertIn("resources list EMPTY", f)

    def test_research_prompt_lists_topics(self):
        u = prompts.build_research_user_prompt(["find a stud", "pick a drill bit"])
        self.assertIn("find a stud", u)
        self.assertIn("pick a drill bit", u)

    def test_version_present(self):
        self.assertTrue(prompts.PROMPTS_VERSION)


# ─────────────────────────────────────────────────────────────────────────────
# Client — offline, against a fake SDK
# ─────────────────────────────────────────────────────────────────────────────
class _Block:
    def __init__(self, type_, text=None):
        self.type = type_
        self.text = text


class _Resp:
    def __init__(self, content, stop_reason="end_turn", parsed_output=None):
        self.content = content
        self.stop_reason = stop_reason
        self.parsed_output = parsed_output


class _Messages:
    def __init__(self, create_fn=None, parse_fn=None):
        self._create_fn = create_fn
        self._parse_fn = parse_fn

    def create(self, **kwargs):
        return self._create_fn(**kwargs)

    def parse(self, **kwargs):
        return self._parse_fn(**kwargs)


class _FakeAnthropic:
    def __init__(self, create_fn=None, parse_fn=None):
        self.messages = _Messages(create_fn, parse_fn)
        self.option_calls: list = []

    def with_options(self, **kwargs):
        self.option_calls.append(kwargs)
        return self


def _client_with(create_fn=None, parse_fn=None) -> ClaudeClient:
    c = ClaudeClient(api_key="test-key")
    c._client = _FakeAnthropic(create_fn=create_fn, parse_fn=parse_fn)
    return c


def _invalid_json_error() -> PydanticValidationError:
    """A real pydantic ValidationError of the kind the SDK's structured-output
    parser raises on malformed/truncated model JSON (seen live 2026-07-04)."""
    try:
        TypeAdapter(dict).validate_json('{"kind": "truncat')
    except PydanticValidationError as exc:
        return exc
    raise AssertionError("expected invalid JSON to raise")


class ClientTests(unittest.TestCase):
    def test_construction_without_key_is_lazy(self):
        # No key, no network — must not raise until the SDK is actually used.
        ClaudeClient(api_key=None)

    def test_chat_returns_text(self):
        c = _client_with(create_fn=lambda **kw: _Resp([_Block("text", "Hi there!")]))
        out = c.chat(system="s", messages=[{"role": "user", "content": "hi"}])
        self.assertEqual(out, "Hi there!")

    def test_chat_skips_thinking_blocks(self):
        resp = _Resp([_Block("thinking", "hmm"), _Block("text", "Answer.")])
        c = _client_with(create_fn=lambda **kw: resp)
        self.assertEqual(c.chat(system="s", messages=[]), "Answer.")

    def test_chat_passes_adaptive_thinking_when_enabled(self):
        seen = {}

        def create_fn(**kw):
            seen.update(kw)
            return _Resp([_Block("text", "ok")])

        c = _client_with(create_fn=create_fn)
        c.chat(system="s", messages=[], thinking=True)
        self.assertEqual(seen["thinking"], {"type": "adaptive"})

    def test_chat_omits_thinking_when_disabled(self):
        seen = {}

        def create_fn(**kw):
            seen.update(kw)
            return _Resp([_Block("text", "ok")])

        c = _client_with(create_fn=create_fn)
        c.chat(system="s", messages=[], thinking=False)
        self.assertNotIn("thinking", seen)

    def test_chat_refusal_raises(self):
        resp = _Resp([], stop_reason="refusal")
        c = _client_with(create_fn=lambda **kw: resp)
        with self.assertRaises(ClaudeError):
            c.chat(system="s", messages=[])

    def test_generate_spec_uses_parsed_output(self):
        spec = ProjectSpec.model_validate(VALID_SPEC)
        resp = _Resp([_Block("text", "{...}")], parsed_output=spec)
        c = _client_with(parse_fn=lambda **kw: resp)
        out = c.generate_spec(system="s", messages=[{"role": "user", "content": "go"}])
        self.assertIs(out, spec)

    def test_generate_spec_falls_back_to_text_gate(self):
        resp = _Resp([_Block("text", json.dumps(VALID_SPEC))], parsed_output=None)
        c = _client_with(parse_fn=lambda **kw: resp)
        out = c.generate_spec(system="s", messages=[])
        self.assertIsInstance(out, ProjectSpec)

    def test_generate_spec_retries_then_succeeds(self):
        calls = {"n": 0}

        def parse_fn(**kw):
            calls["n"] += 1
            if calls["n"] == 1:
                return _Resp([_Block("text", "not json")], parsed_output=None)
            return _Resp([_Block("text", json.dumps(VALID_SPEC))], parsed_output=None)

        c = _client_with(parse_fn=parse_fn)
        out = c.generate_spec(system="s", messages=[], max_retries=1)
        self.assertIsInstance(out, ProjectSpec)
        self.assertEqual(calls["n"], 2)

    def test_generate_spec_gives_up_after_retries(self):
        c = _client_with(parse_fn=lambda **kw: _Resp([_Block("text", "nope")], parsed_output=None))
        with self.assertRaises(ClaudeError):
            c.generate_spec(system="s", messages=[], max_retries=1)

    def test_generate_spec_refusal_raises(self):
        resp = _Resp([], stop_reason="refusal", parsed_output=None)
        c = _client_with(parse_fn=lambda **kw: resp)
        with self.assertRaises(ClaudeError):
            c.generate_spec(system="s", messages=[])

    def test_parse_retries_malformed_json_then_succeeds(self):
        calls = {"n": 0}
        parsed = {"kind": "clarifying"}

        def parse_fn(**kw):
            calls["n"] += 1
            if calls["n"] == 1:
                raise _invalid_json_error()
            return _Resp([_Block("text", "{}")], parsed_output=parsed)

        c = _client_with(parse_fn=parse_fn)
        out = c.parse(system="s", messages=[], output_format=dict)
        self.assertIs(out, parsed)
        self.assertEqual(calls["n"], 2)

    def test_parse_malformed_json_exhausts_to_claude_error(self):
        def parse_fn(**kw):
            raise _invalid_json_error()

        c = _client_with(parse_fn=parse_fn)
        with self.assertRaises(ClaudeError):
            c.parse(system="s", messages=[], output_format=dict, max_retries=1)

    def test_generate_spec_malformed_json_retries_then_succeeds(self):
        calls = {"n": 0}
        spec = ProjectSpec.model_validate(VALID_SPEC)

        def parse_fn(**kw):
            calls["n"] += 1
            if calls["n"] == 1:
                raise _invalid_json_error()
            return _Resp([_Block("text", "{...}")], parsed_output=spec)

        c = _client_with(parse_fn=parse_fn)
        out = c.generate_spec(system="s", messages=[], max_retries=1)
        self.assertIs(out, spec)
        self.assertEqual(calls["n"], 2)

    def test_web_search_deadline_exceeded_raises(self):
        c = _client_with(create_fn=lambda **kw: _Resp([_Block("text", "[]")]))
        with self.assertRaises(ClaudeError):
            c.web_search(system="s", messages=[], deadline_s=0)

    def test_web_search_sets_timeout_and_disables_sdk_retries(self):
        c = _client_with(create_fn=lambda **kw: _Resp([_Block("text", "[]")]))
        out = c.web_search(
            system="s", messages=[], round_timeout_s=60, deadline_s=150
        )
        self.assertEqual(out, "[]")
        opts = c._client.option_calls[0]
        self.assertEqual(opts["max_retries"], 0)
        self.assertGreater(opts["timeout"], 0)
        self.assertLessEqual(opts["timeout"], 60)


# ─────────────────────────────────────────────────────────────────────────────
# Generation engine + routes (offline, against a fake ClaudeClient)
# ─────────────────────────────────────────────────────────────────────────────
from app.claude import generation  # noqa: E402
from app.claude.client import get_claude_client  # noqa: E402
from app.claude.generation import (  # noqa: E402
    CandidateNotFound,
    _CandidateDraft,
    _TurnDraft,
)
from app.claude.session_store import SessionStore as _Store  # noqa: E402
from app.claude.session_store import get_session_store  # noqa: E402
from app.schemas.dtos import (  # noqa: E402
    ClarifyTurn,
    GenerateMessageCreate,
    GenerateSessionCreate,
    ProposeTurn,
    ReadyTurn,
)


class FakeClaude:
    """Stand-in for ClaudeClient — programmable, no network."""

    def __init__(self, *, chat_text="Hi! What are we building?", turn=None, spec=None, search_text="[]"):
        self.chat_text = chat_text
        self.turn = turn
        self.spec = spec
        self.search_text = search_text
        self.chat_error = None
        self.search_error = None

    def chat(self, *, system, messages, thinking=True, max_tokens=4096):
        if self.chat_error:
            raise self.chat_error
        return self.chat_text

    def parse(self, *, system, messages, output_format, max_tokens=2048):
        return self.turn

    def generate_spec(self, *, system, messages, max_tokens=16000, max_retries=1):
        return self.spec

    def web_search(self, *, system, messages, max_tokens=8000, max_uses=5, max_rounds=6):
        if self.search_error:
            raise self.search_error
        return self.search_text


def _new_session(store, claude):
    body = GenerateSessionCreate(
        description="a small bookshelf",
        skill_level=SkillLevel.beginner,
        budget_band=BudgetBand.under_30,
    )
    return generation.start_session(store, claude, body)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.store = _Store()
        self.claude = FakeClaude()

    def test_start_session_returns_opening(self):
        start = _new_session(self.store, self.claude)
        self.assertTrue(start.session_id)
        self.assertEqual(start.agent_message, "Hi! What are we building?")
        s = self.store.get(start.session_id)
        self.assertEqual([m["role"] for m in s.messages], ["user", "assistant"])

    def test_start_session_blank_description_seeds_surprise(self):
        body = GenerateSessionCreate(
            description="   ",
            skill_level=SkillLevel.handy,
            budget_band=BudgetBand.over_75,
        )
        start = generation.start_session(self.store, self.claude, body)
        seed = self.store.get(start.session_id).messages[0]["content"]
        self.assertIn("surprise me", seed.lower())

    def test_clarifying_turn(self):
        start = _new_session(self.store, self.claude)
        self.claude.turn = _TurnDraft(kind="clarifying", agent_message="How wide?")
        turn = generation.send_message(
            self.store, self.claude, start.session_id,
            GenerateMessageCreate(message="around 24 inches"),
        )
        self.assertIsInstance(turn, ClarifyTurn)
        self.assertEqual(turn.kind, "clarifying")
        self.assertEqual(turn.agent_message, "How wide?")
        self.assertEqual(turn.session_id, start.session_id)
        self.assertIsNotNone(turn.progress)

    def test_proposing_turn_assigns_ids_and_stores(self):
        start = _new_session(self.store, self.claude)
        self.claude.turn = _TurnDraft(
            kind="proposing",
            agent_message="Here are a few ideas:",
            candidates=[
                _CandidateDraft(title="Spice rack", summary="A small wall rack."),
                _CandidateDraft(title="Phone stand", summary="A desk phone stand."),
            ],
        )
        turn = generation.send_message(
            self.store, self.claude, start.session_id,
            GenerateMessageCreate(message="surprise me"),
        )
        self.assertIsInstance(turn, ProposeTurn)
        self.assertEqual([c.id for c in turn.candidates], ["c1", "c2"])
        s = self.store.get(start.session_id)
        self.assertEqual(set(s.candidates), {"c1", "c2"})

    def test_proposing_with_no_candidates_falls_back_to_clarify(self):
        start = _new_session(self.store, self.claude)
        self.claude.turn = _TurnDraft(kind="proposing", agent_message="Hmm", candidates=[])
        turn = generation.send_message(
            self.store, self.claude, start.session_id,
            GenerateMessageCreate(message="dunno"),
        )
        self.assertIsInstance(turn, ClarifyTurn)

    def test_candidate_cap_of_three(self):
        start = _new_session(self.store, self.claude)
        self.claude.turn = _TurnDraft(
            kind="proposing",
            agent_message="Ideas:",
            candidates=[_CandidateDraft(title=f"P{i}", summary="s") for i in range(5)],
        )
        turn = generation.send_message(
            self.store, self.claude, start.session_id,
            GenerateMessageCreate(message="surprise me"),
        )
        self.assertEqual(len(turn.candidates), 3)

    def test_select_candidate_resolves(self):
        start = _new_session(self.store, self.claude)
        self.claude.turn = _TurnDraft(
            kind="proposing",
            agent_message="Ideas:",
            candidates=[_CandidateDraft(title="Spice rack", summary="A small rack.")],
        )
        generation.send_message(
            self.store, self.claude, start.session_id,
            GenerateMessageCreate(message="surprise me"),
        )
        # Now select c1; the model replies ready.
        self.claude.turn = _TurnDraft(kind="ready", agent_message="Great, ready to build!")
        turn = generation.send_message(
            self.store, self.claude, start.session_id,
            GenerateMessageCreate(select_candidate_id="c1"),
        )
        self.assertIsInstance(turn, ReadyTurn)
        s = self.store.get(start.session_id)
        self.assertIn("Spice rack", s.messages[-2]["content"])  # the resolved user turn

    def test_select_unknown_candidate_raises(self):
        start = _new_session(self.store, self.claude)
        with self.assertRaises(CandidateNotFound):
            generation.send_message(
                self.store, self.claude, start.session_id,
                GenerateMessageCreate(select_candidate_id="nope"),
            )

    def test_ready_progress_is_full(self):
        start = _new_session(self.store, self.claude)
        self.claude.turn = _TurnDraft(kind="ready", agent_message="Ready!")
        turn = generation.send_message(
            self.store, self.claude, start.session_id,
            GenerateMessageCreate(message="go"),
        )
        self.assertEqual(turn.progress.current, turn.progress.total)

    def test_send_message_unknown_session_raises(self):
        from app.claude.session_store import SessionNotFound
        with self.assertRaises(SessionNotFound):
            generation.send_message(
                self.store, self.claude, "nope",
                GenerateMessageCreate(message="hi"),
            )

    def test_finalize_returns_spec(self):
        start = _new_session(self.store, self.claude)
        self.claude.spec = ProjectSpec.model_validate(VALID_SPEC)
        spec = generation.finalize(self.store, self.claude, start.session_id)
        self.assertIsInstance(spec, ProjectSpec)
        self.assertTrue(self.store.get(start.session_id).finalized)


class RouteTests(unittest.TestCase):
    """Endpoint-level tests via FastAPI TestClient with injected fakes."""

    def setUp(self):
        from fastapi.testclient import TestClient

        from app.main import app

        self.app = app
        self.store = _Store()
        self.claude = FakeClaude(spec=ProjectSpec.model_validate(VALID_SPEC))
        app.dependency_overrides[get_session_store] = lambda: self.store
        app.dependency_overrides[get_claude_client] = lambda: self.claude
        self.client = TestClient(app)

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def _start(self):
        return self.client.post(
            "/generate/sessions",
            json={"description": "a shelf", "skill_level": "beginner", "budget_band": "under_30"},
        )

    def test_start_then_message_then_finalize(self):
        r = self._start()
        self.assertEqual(r.status_code, 201)
        sid = r.json()["session_id"]
        self.assertTrue(r.json()["agent_message"])

        self.claude.turn = _TurnDraft(kind="ready", agent_message="Ready to build!")
        m = self.client.post(
            f"/generate/sessions/{sid}/messages", json={"message": "24 inches, I have a drill"}
        )
        self.assertEqual(m.status_code, 200)
        self.assertEqual(m.json()["kind"], "ready")

        f = self.client.post(f"/generate/sessions/{sid}/finalize")
        self.assertEqual(f.status_code, 200)
        self.assertEqual(f.json()["project"]["module"], "mechanic")

    def test_message_unknown_session_404(self):
        self.claude.turn = _TurnDraft(kind="clarifying", agent_message="hi")
        r = self.client.post("/generate/sessions/nope/messages", json={"message": "hi"})
        self.assertEqual(r.status_code, 404)

    def test_select_unknown_candidate_400(self):
        sid = self._start().json()["session_id"]
        r = self.client.post(
            f"/generate/sessions/{sid}/messages", json={"select_candidate_id": "nope"}
        )
        self.assertEqual(r.status_code, 400)

    def test_message_requires_exactly_one_field_422(self):
        sid = self._start().json()["session_id"]
        r = self.client.post(f"/generate/sessions/{sid}/messages", json={})
        self.assertEqual(r.status_code, 422)

    def test_upstream_failure_is_502(self):
        self.claude.chat_error = ClaudeError("boom")
        r = self._start()
        self.assertEqual(r.status_code, 502)

    def test_proposing_turn_shape(self):
        sid = self._start().json()["session_id"]
        self.claude.turn = _TurnDraft(
            kind="proposing",
            agent_message="Ideas:",
            candidates=[_CandidateDraft(title="Rack", summary="a rack")],
        )
        r = self.client.post(f"/generate/sessions/{sid}/messages", json={"message": "surprise me"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["kind"], "proposing")
        self.assertEqual(body["candidates"][0]["id"], "c1")


# ─────────────────────────────────────────────────────────────────────────────
# Research web-search pass (offline; fake web_search)
# ─────────────────────────────────────────────────────────────────────────────
from app.claude.research import (  # noqa: E402
    apply_research_to_spec,
    research_for_spec,
    run_research,
)
from app.schemas.spec import ResearchResource  # noqa: E402

_SEARCH_JSON = json.dumps(
    [
        {
            "topic": "How to find a wall stud",
            "resources": [
                {"title": "Stud finder basics", "url": "https://ex.com/stud", "type": "video"},
                {"title": "Drywall anchors", "url": "https://ex.com/anchor", "type": "article"},
                {"title": "Overflow", "url": "https://ex.com/x", "type": "article"},
            ],
        },
        {
            "topic": "Pilot holes",
            "resources": [
                {"title": "No url", "url": "", "type": "video"},  # filtered (no url)
                {"title": "Pilot hole guide", "url": "https://ex.com/pilot", "type": "guide"},
            ],
        },
    ]
)


class ResearchTests(unittest.TestCase):
    def test_empty_topics_returns_empty(self):
        self.assertEqual(run_research(FakeClaude(), []), {})

    def test_maps_caps_and_filters(self):
        claude = FakeClaude(search_text=_SEARCH_JSON)
        out = run_research(claude, ["How to find a wall stud", "Pilot holes"], max_per_topic=2)
        stud = out["How to find a wall stud"]
        self.assertEqual(len(stud), 2)  # capped
        self.assertIsInstance(stud[0], ResearchResource)
        self.assertEqual(stud[0].type, "video")
        pilot = out["Pilot holes"]
        self.assertEqual(len(pilot), 1)  # bad url filtered out
        self.assertEqual(pilot[0].type, "article")  # "guide" normalized

    def test_garbage_response_degrades_gracefully(self):
        claude = FakeClaude(search_text="the search failed, sorry")
        out = run_research(claude, ["a", "b"])
        self.assertEqual(out, {"a": [], "b": []})

    def test_positional_fallback_when_topic_text_differs(self):
        payload = json.dumps(
            [
                {"topic": "reworded one", "resources": [{"title": "T", "url": "https://ex.com/1", "type": "article"}]},
                {"topic": "reworded two", "resources": [{"title": "U", "url": "https://ex.com/2", "type": "video"}]},
            ]
        )
        out = run_research(FakeClaude(search_text=payload), ["orig one", "orig two"])
        self.assertEqual(out["orig one"][0].url, "https://ex.com/1")
        self.assertEqual(out["orig two"][0].url, "https://ex.com/2")

    def test_apply_research_to_spec(self):
        spec = ProjectSpec.model_validate(VALID_SPEC)
        self.assertEqual(spec.research_topics[0].resources, [])
        mapping = {
            "How to find a wall stud": [
                ResearchResource(title="Stud video", url="https://ex.com/s", type="video")
            ]
        }
        filled = apply_research_to_spec(spec, mapping)
        self.assertEqual(len(filled.research_topics[0].resources), 1)
        # original spec is untouched (model_copy)
        self.assertEqual(spec.research_topics[0].resources, [])

    def test_research_for_spec_end_to_end(self):
        spec = ProjectSpec.model_validate(VALID_SPEC)  # topic: "How to find a wall stud"
        claude = FakeClaude(search_text=_SEARCH_JSON)
        filled = research_for_spec(claude, spec)
        self.assertTrue(filled.research_topics[0].resources)
        self.assertEqual(filled.research_topics[0].resources[0].url, "https://ex.com/stud")


# ─────────────────────────────────────────────────────────────────────────────
# Research refresh endpoint + service (B3 part 2) — fake DB session
# ─────────────────────────────────────────────────────────────────────────────
# A's models use Postgres JSONB columns, which SQLite can't create, and Docker
# is unavailable in this shell — so the DB is faked at the Session boundary. The
# web-search half is verified live separately (research smoke); here we cover
# the wiring: project 404, empty topics, upstream 502, and resource writeback.
from fastapi import HTTPException  # noqa: E402

from app.db import get_session  # noqa: E402
from app.models import ResearchTopic as ResearchTopicRow  # noqa: E402
from app.services.research import refresh_project_research  # noqa: E402


class _FakeResult:
    def __init__(self, first_val=None, all_val=None):
        self._first = first_val
        self._all = all_val or []

    def first(self):
        return self._first

    def all(self):
        return self._all


class _FakeSession:
    """Minimal Session stand-in: exec()→result, plus add/commit/refresh no-ops.

    The service issues two exec() calls — a project-existence check (.first())
    then the topics query (.all()) — so one result shape carrying both serves
    both call sites.
    """

    def __init__(self, project_exists=True, topics=None):
        self._first = 1 if project_exists else None
        self._topics = list(topics or [])
        self.committed = False

    def exec(self, statement):  # noqa: ARG002 - statement ignored by the fake
        return _FakeResult(first_val=self._first, all_val=self._topics)

    def add(self, obj):
        pass

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        pass


def _research_rows():
    return [
        ResearchTopicRow(id=1, project_id=7, topic="How to find a wall stud", why="w1", resources=[]),
        ResearchTopicRow(id=2, project_id=7, topic="Pilot holes", why="w2", resources=[]),
    ]


class ResearchServiceTests(unittest.TestCase):
    def test_happy_fills_and_commits(self):
        session = _FakeSession(topics=_research_rows())
        out = refresh_project_research(session, FakeClaude(search_text=_SEARCH_JSON), 7)
        self.assertEqual([t.id for t in out], [1, 2])
        self.assertTrue(out[0].resources)  # "wall stud" topic got resources
        self.assertEqual(out[0].resources[0].type, "video")
        self.assertTrue(session.committed)

    def test_missing_project_raises_404(self):
        with self.assertRaises(HTTPException) as ctx:
            refresh_project_research(_FakeSession(project_exists=False), FakeClaude(), 7)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_no_topics_returns_empty(self):
        out = refresh_project_research(_FakeSession(topics=[]), FakeClaude(search_text=_SEARCH_JSON), 7)
        self.assertEqual(out, [])

    def test_upstream_failure_raises_502(self):
        claude = FakeClaude()
        claude.search_error = ClaudeError("web search down")
        with self.assertRaises(HTTPException) as ctx:
            refresh_project_research(_FakeSession(topics=_research_rows()), claude, 7)
        self.assertEqual(ctx.exception.status_code, 502)


class ResearchRouteTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient

        from app.main import app

        self.app = app
        self.session = _FakeSession(topics=_research_rows())
        self.claude = FakeClaude(search_text=_SEARCH_JSON)
        app.dependency_overrides[get_session] = lambda: self.session
        app.dependency_overrides[get_claude_client] = lambda: self.claude
        self.client = TestClient(app)

    def tearDown(self):
        self.app.dependency_overrides.clear()

    def test_refresh_returns_refreshed_topics(self):
        r = self.client.post("/projects/7/research/refresh")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual([t["id"] for t in body], [1, 2])
        self.assertTrue(body[0]["resources"])
        self.assertEqual(body[0]["resources"][0]["type"], "video")

    def test_refresh_missing_project_404(self):
        self.session._first = None
        r = self.client.post("/projects/7/research/refresh")
        self.assertEqual(r.status_code, 404)


if __name__ == "__main__":
    unittest.main()
