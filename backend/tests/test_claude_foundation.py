"""Offline tests for the claude-service Phase-1 foundation (TASKS row B1).

Pure-Python, no network: exercises the spec gate, session store, prompt
builders, and the ClaudeClient parse/fallback/retry logic against a fake SDK
client. Run from ``backend/`` with the venv active:

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import json
import unittest

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


def _client_with(create_fn=None, parse_fn=None) -> ClaudeClient:
    c = ClaudeClient(api_key="test-key")
    c._client = _FakeAnthropic(create_fn=create_fn, parse_fn=parse_fn)
    return c


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


if __name__ == "__main__":
    unittest.main()
