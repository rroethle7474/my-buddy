"""Generate-via-chat orchestration (ARCHITECTURE.md §7.1, mocks 1d–1f).

The engine that the ``/generate/*`` endpoints (B2) call. It ties together the
B1 foundation — the in-memory session store, the versioned prompts, the Claude
client, and the spec gate — into the three moves of the bounded conversation:

- ``start_session``  : create a session, return the agent's opening message.
- ``send_message``   : one user turn → a typed agent turn (clarify / propose /
                       ready). Structured output drives the turn ``kind`` so the
                       client renders deterministically (§16.1); candidates get
                       server-assigned ids stored on the session so a later
                       ``select_candidate_id`` resolves without a round-trip.
- ``finalize``       : emit the validated §6 ``ProjectSpec``.

State is in-memory and process-local (Ryan 2026-07-03) — no DB dependency.
"""

from __future__ import annotations

import secrets
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..schemas.dtos import (
    AgentTurn,
    Candidate,
    ClarifyTurn,
    GenerateMessageCreate,
    GenerateProgress,
    GenerateSessionCreate,
    GenerateSessionStart,
    ProposeTurn,
    ReadyTurn,
)
from ..schemas.spec import Difficulty, ProjectSpec
from . import prompts
from .client import ClaudeClient
from .session_store import Session, SessionStore

# Soft progress denominator for the bounded chat (mock 1e: "Design step · 3 of 5").
_TOTAL_STEPS = 5
_MAX_CANDIDATES = 3


class CandidateNotFound(KeyError):
    """Raised when ``select_candidate_id`` names a candidate this session never
    proposed. Callers map it to an HTTP 400."""


# ── Internal structured-output shape for one /messages turn ───────────────────
class _CandidateDraft(BaseModel):
    """A candidate as the model drafts it — no id (the server assigns those)."""

    model_config = ConfigDict(extra="forbid")

    title: str
    summary: str
    difficulty: Optional[Difficulty] = None
    est_cost_usd: Optional[float] = None


class _TurnDraft(BaseModel):
    """The model's structured decision for one agent turn (§7.1)."""

    model_config = ConfigDict(extra="forbid")

    kind: str = Field(description='One of "clarifying", "proposing", "ready".')
    agent_message: str
    candidates: List[_CandidateDraft] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Public engine
# ─────────────────────────────────────────────────────────────────────────────
def start_session(
    store: SessionStore,
    claude: ClaudeClient,
    body: GenerateSessionCreate,
) -> GenerateSessionStart:
    """Create a session and return the agent's opening message (mock 1d → 1e)."""
    session = store.create(
        skill_level=body.skill_level,
        budget_band=body.budget_band,
        description=body.description,
    )

    seed = body.description.strip() or (
        "I'm not sure what to build yet — surprise me with a few ideas at my "
        "skill level."
    )
    session.add_user_turn(seed)

    system = (
        prompts.build_generation_system_prompt(body.skill_level, body.budget_band)
        + "\n\n"
        + prompts.OPENING_SYSTEM_ADDENDUM
    )
    text = claude.chat(system=system, messages=session.messages, thinking=False, max_tokens=1024)
    session.add_assistant_turn(text)

    return GenerateSessionStart(session_id=session.id, agent_message=text)


def send_message(
    store: SessionStore,
    claude: ClaudeClient,
    session_id: str,
    body: GenerateMessageCreate,
) -> AgentTurn:
    """Advance the conversation by one user turn and return a typed agent turn."""
    session = store.get(session_id)  # raises SessionNotFound → 404

    # Turn the user's input into a history entry. Exactly one of the two fields
    # is set (enforced by GenerateMessageCreate's validator).
    if body.select_candidate_id is not None:
        chosen = session.candidates.get(body.select_candidate_id)
        if chosen is None:
            raise CandidateNotFound(body.select_candidate_id)
        session.add_user_turn(f'I\'ll go with "{chosen.title}" — {chosen.summary}')
    else:
        session.add_user_turn(body.message or "")

    system = (
        prompts.build_generation_system_prompt(session.skill_level, session.budget_band)
        + "\n\n"
        + prompts.TURN_PROTOCOL_ADDENDUM
    )
    draft: _TurnDraft = claude.parse(
        system=system, messages=session.messages, output_format=_TurnDraft
    )

    return _render_turn(session, draft)


def finalize(
    store: SessionStore,
    claude: ClaudeClient,
    session_id: str,
) -> ProjectSpec:
    """Emit the validated §6 spec for the agreed project (mock 1e → 1f)."""
    session = store.get(session_id)  # raises SessionNotFound → 404

    system = prompts.build_generation_system_prompt(
        session.skill_level, session.budget_band
    )
    messages = session.messages + [
        {
            "role": "user",
            "content": prompts.build_finalize_instruction(
                session.skill_level, session.budget_band
            ),
        }
    ]
    spec = claude.generate_spec(system=system, messages=messages)
    session.finalized = True
    return spec


# ─────────────────────────────────────────────────────────────────────────────
# Internals
# ─────────────────────────────────────────────────────────────────────────────
def _render_turn(session: Session, draft: _TurnDraft) -> AgentTurn:
    """Translate the model's ``_TurnDraft`` into the contract ``AgentTurn`` and
    fold the reply into the session history."""
    message_id = "m_" + secrets.token_urlsafe(8)
    kind = draft.kind.strip().lower()
    has_candidates = bool(draft.candidates)

    # Only treat it as a proposal when the model actually offered candidates —
    # guards against a "proposing" label with an empty list.
    if kind == "proposing" and has_candidates:
        candidates = _assign_candidate_ids(draft.candidates[:_MAX_CANDIDATES])
        session.remember_candidates(candidates)
        session.add_assistant_turn(_proposal_history(draft.agent_message, candidates))
        return ProposeTurn(
            session_id=session.id,
            message_id=message_id,
            agent_message=draft.agent_message,
            progress=_progress(session),
            candidates=candidates,
        )

    if kind == "ready":
        session.add_assistant_turn(draft.agent_message)
        return ReadyTurn(
            session_id=session.id,
            message_id=message_id,
            agent_message=draft.agent_message,
            progress=_progress(session, ready=True),
        )

    # Default / fallback: clarifying (also covers a "proposing" label that
    # arrived with no candidates).
    session.add_assistant_turn(draft.agent_message)
    return ClarifyTurn(
        session_id=session.id,
        message_id=message_id,
        agent_message=draft.agent_message,
        progress=_progress(session),
    )


def _assign_candidate_ids(drafts: List[_CandidateDraft]) -> List[Candidate]:
    return [
        Candidate(
            id=f"c{i + 1}",
            title=d.title,
            summary=d.summary,
            difficulty=d.difficulty,
            est_cost_usd=d.est_cost_usd,
        )
        for i, d in enumerate(drafts)
    ]


def _proposal_history(agent_message: str, candidates: List[Candidate]) -> str:
    """History entry for a proposal — includes the candidate details so later
    turns (and ``select_candidate_id`` resolution) stay coherent."""
    lines = "\n".join(f"{c.id}. {c.title} — {c.summary}" for c in candidates)
    return f"{agent_message}\n\n{lines}"


def _progress(session: Session, ready: bool = False) -> GenerateProgress:
    if ready:
        current = _TOTAL_STEPS
    else:
        # One "step" per user turn so far, capped just short of the total.
        current = min(session.turn_count, _TOTAL_STEPS - 1)
    return GenerateProgress(label="Design step", current=current, total=_TOTAL_STEPS)
