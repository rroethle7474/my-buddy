"""In-memory generation session store (ARCHITECTURE.md §7.1; Ryan 2026-07-03).

Decision in force: generation session state lives in an **in-memory store inside
claude-service, keyed by session id** — no DB table, no dependency on
backend-core's models. The app is single-user and self-hosted, so a restart
mid-chat simply restarts the conversation (the client can start a fresh
session). The Anthropic API is stateless, so the full turn history is kept here
and replayed into every call.

The store is process-local and guarded by a lock because FastAPI runs sync
endpoints in a threadpool, so concurrent access to the dict is possible. A soft
capacity cap evicts the least-recently-updated sessions so a long-lived process
can't grow without bound.
"""

from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

from ..schemas.dtos import BudgetBand, Candidate, SkillLevel


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SessionNotFound(KeyError):
    """Raised by ``SessionStore.get`` when the session id is unknown/expired.

    Callers map this to an HTTP 404 (the session isn't there — or the process
    restarted and dropped in-memory state).
    """


@dataclass
class Session:
    """One bounded generation conversation (mocks 1d–1f).

    ``messages`` is the Anthropic-format history (``[{"role", "content"}, ...]``)
    replayed into every call. ``candidates`` maps a proposed candidate's id to
    the ``Candidate`` so a later ``select_candidate_id`` turn can be resolved
    server-side without the client re-sending the full pitch.
    """

    id: str
    skill_level: SkillLevel
    budget_band: BudgetBand
    description: str
    messages: List[dict] = field(default_factory=list)
    candidates: Dict[str, Candidate] = field(default_factory=dict)
    turn_count: int = 0
    finalized: bool = False
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    # ── history helpers (keep updated_at fresh on every mutation) ────────────
    def add_user_turn(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})
        self.turn_count += 1
        self.updated_at = _now()

    def add_assistant_turn(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})
        self.updated_at = _now()

    def remember_candidates(self, candidates: List[Candidate]) -> None:
        for c in candidates:
            self.candidates[c.id] = c
        self.updated_at = _now()

    def touch(self) -> None:
        self.updated_at = _now()


class SessionStore:
    """Thread-safe, process-local map of session id → ``Session``."""

    def __init__(self, max_sessions: int = 500) -> None:
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.Lock()
        self._max_sessions = max_sessions

    def create(
        self,
        *,
        skill_level: SkillLevel,
        budget_band: BudgetBand,
        description: str,
    ) -> Session:
        """Create and store a new session, returning it. Ids are opaque."""
        session = Session(
            id=secrets.token_urlsafe(16),
            skill_level=skill_level,
            budget_band=budget_band,
            description=description,
        )
        with self._lock:
            self._sessions[session.id] = session
            self._evict_if_needed_locked()
        return session

    def get(self, session_id: str) -> Session:
        """Return the session or raise ``SessionNotFound``."""
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise SessionNotFound(session_id)
        return session

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def __len__(self) -> int:
        with self._lock:
            return len(self._sessions)

    def _evict_if_needed_locked(self) -> None:
        """Drop least-recently-updated sessions past the soft cap.

        Caller must hold ``self._lock``.
        """
        overflow = len(self._sessions) - self._max_sessions
        if overflow <= 0:
            return
        stale = sorted(self._sessions.values(), key=lambda s: s.updated_at)[:overflow]
        for session in stale:
            self._sessions.pop(session.id, None)


# Process-wide singleton. Generation endpoints (B2) share this instance; a
# restart clears it, which is the documented behaviour.
_store: Optional[SessionStore] = None


def get_session_store() -> SessionStore:
    """FastAPI-dependency-friendly accessor for the singleton store."""
    global _store
    if _store is None:
        _store = SessionStore()
    return _store
