"""Claude generate-via-chat router (§7.1, §11, mocks 1d–1f).

A bounded conversation that ends by emitting a §6 spec. All Claude calls are
server-side (§7). The route bodies are thin: they map request → engine call →
typed response, and translate the engine's domain errors into HTTP status
codes. The orchestration lives in ``app.claude.generation``; generation session
state is an in-memory store inside claude-service (no DB — Ryan 2026-07-03).

Signatures, paths, and response models are unchanged from the Phase-0 contract
(§11) — only the bodies moved from 501 stubs to real logic.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..claude import generation
from ..claude.client import ClaudeClient, ClaudeError, get_claude_client
from ..claude.generation import CandidateNotFound
from ..claude.session_store import SessionNotFound, SessionStore, get_session_store
from ..schemas.dtos import (
    AgentTurn,
    GenerateMessageCreate,
    GenerateSessionCreate,
    GenerateSessionStart,
    ResearchTopicRead,
)
from ..schemas.spec import ProjectSpec
from . import not_implemented

router = APIRouter(prefix="/generate", tags=["generate"])

# Upstream (Claude) failure → 502 Bad Gateway: the app is fine, the model call
# failed. Clients can retry the turn.
_UPSTREAM = status.HTTP_502_BAD_GATEWAY


@router.post(
    "/sessions",
    response_model=GenerateSessionStart,
    status_code=status.HTTP_201_CREATED,
    summary="Start a generation session from the setup payload (mock 1d)",
)
def start_session(
    body: GenerateSessionCreate,
    store: SessionStore = Depends(get_session_store),
    claude: ClaudeClient = Depends(get_claude_client),
) -> GenerateSessionStart:
    try:
        return generation.start_session(store, claude, body)
    except ClaudeError as exc:
        raise HTTPException(status_code=_UPSTREAM, detail=str(exc)) from exc


@router.post(
    "/sessions/{session_id}/messages",
    response_model=AgentTurn,
    summary="Send one user turn, get the agent's reply (mock 1e)",
)
def send_message(
    session_id: str,
    body: GenerateMessageCreate,
    store: SessionStore = Depends(get_session_store),
    claude: ClaudeClient = Depends(get_claude_client),
) -> AgentTurn:
    try:
        return generation.send_message(store, claude, session_id, body)
    except SessionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Generation session not found."
        ) from exc
    except CandidateNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown candidate id: {exc.args[0] if exc.args else ''}",
        ) from exc
    except ClaudeError as exc:
        raise HTTPException(status_code=_UPSTREAM, detail=str(exc)) from exc


@router.post(
    "/sessions/{session_id}/finalize",
    response_model=ProjectSpec,
    summary="Emit the full §6 spec as strict JSON (mock 1e → 1f)",
)
def finalize_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
    claude: ClaudeClient = Depends(get_claude_client),
) -> ProjectSpec:
    try:
        return generation.finalize(store, claude, session_id)
    except SessionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Generation session not found."
        ) from exc
    except ClaudeError as exc:
        raise HTTPException(status_code=_UPSTREAM, detail=str(exc)) from exc


# Research refresh (§7.2) is a Claude/web-search flow (claude-service, worktree
# B) but is addressed under /projects/{id}. It rides its own prefix-less router.
# Wired in B3 (depends on projects-api for persistence); still a stub here.
research_router = APIRouter(tags=["generate"])


@research_router.post(
    "/projects/{project_id}/research/refresh",
    response_model=List[ResearchTopicRead],
    summary="Re-populate research resources[] via web search (§7.2)",
)
def refresh_research(project_id: int) -> List[ResearchTopicRead]:
    # Returns only the refreshed research topics (the exact delta — refresh
    # touches nothing else on the project). The client patches its cache by
    # ResearchTopicRead.id.
    not_implemented()
