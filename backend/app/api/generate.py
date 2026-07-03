"""Claude generate-via-chat router (§7.1, §11, mocks 1d–1f).

A bounded conversation that ends by emitting a §6 spec. All Claude calls are
server-side (§7); Phase 0 has no Claude wiring — these are stubs. The generation
flow itself is Phase 2 (claude-service, §12/§13).
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, status

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


@router.post(
    "/sessions",
    response_model=GenerateSessionStart,
    status_code=status.HTTP_201_CREATED,
    summary="Start a generation session from the setup payload (mock 1d)",
)
def start_session(body: GenerateSessionCreate) -> GenerateSessionStart:
    not_implemented()


@router.post(
    "/sessions/{session_id}/messages",
    response_model=AgentTurn,
    summary="Send one user turn, get the agent's reply (mock 1e)",
)
def send_message(session_id: str, body: GenerateMessageCreate) -> AgentTurn:
    not_implemented()


@router.post(
    "/sessions/{session_id}/finalize",
    response_model=ProjectSpec,
    summary="Emit the full §6 spec as strict JSON (mock 1e → 1f)",
)
def finalize_session(session_id: str) -> ProjectSpec:
    not_implemented()


# Research refresh (§7.2) is a Claude/web-search flow (claude-service, worktree
# B) but is addressed under /projects/{id}. It rides its own prefix-less router.
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
