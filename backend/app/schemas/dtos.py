"""API request/response DTOs (ARCHITECTURE.md §11).

These give every §11 endpoint a complete, frozen signature so the four parallel
worktrees build against a stable OpenAPI surface (§13, COORDINATION.md §6). The
read models mirror the §5 data model *including* the runtime state fields
(checked / completed / note / owned / acquire) that are added when a spec is
ingested — those are part of the hydrated API shape even though they are not in
the spec (§6).

Phase 0: these are contract types only. No DB, no persistence — routers are
stubs (§12 Phase 0).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator

from .spec import Difficulty, ResearchResource, TimeBudget


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────
class ProjectStatus(str, Enum):
    """§5 projects.status."""

    planning = "planning"
    active = "active"
    complete = "complete"


class SkillLevel(str, Enum):
    """Generation setup skill level (§7.1 / mock 1d). Mirrors spec difficulty."""

    beginner = "beginner"
    handy = "handy"
    pro = "pro"


class BudgetBand(str, Enum):
    """Generation setup budget band (§7.1 / mock 1d): Under $30 / $30–75 / $75+.

    NOTE (judgment call — confirm before forking): the docs give display labels,
    not wire tokens. These machine values are inferred.
    """

    under_30 = "under_30"
    from_30_to_75 = "30_to_75"
    over_75 = "over_75"


# ─────────────────────────────────────────────────────────────────────────────
# Modules (§5 modules, §11 Modules)
# ─────────────────────────────────────────────────────────────────────────────
class ModuleRead(BaseModel):
    id: int
    slug: str
    name: str
    description: str


# ─────────────────────────────────────────────────────────────────────────────
# Project children — read models (§5 + runtime state fields)
# ─────────────────────────────────────────────────────────────────────────────
class MaterialRead(BaseModel):
    id: int
    project_id: int
    name: str
    quantity: float
    unit: str
    est_cost_usd: float
    where_to_find: str
    notes: str
    checked: bool = Field(description="Runtime: toggled from the shopping cart.")


class ToolRead(BaseModel):
    id: int
    project_id: int
    name: str
    essential: bool
    est_cost_usd: float
    notes: str
    alternatives: str
    owned: bool = Field(description="Runtime: set by the shop diff (§8).")
    acquire: bool = Field(description="Runtime: set by the shop diff (§8).")
    checked: bool = Field(description="Runtime: for in-cart use.")


class StepRead(BaseModel):
    id: int
    project_id: int
    order: int
    title: str
    instruction: str
    safety_note: str
    est_time_minutes: int
    tools_used: List[str]
    materials_used: List[str]
    completed: bool = Field(description="Runtime.")
    note: Optional[str] = Field(
        default=None, description="Runtime: per-step learning ('where I got stuck')."
    )


class ResearchTopicRead(BaseModel):
    id: int
    project_id: int
    topic: str
    why: str
    resources: List[ResearchResource]


class PhotoRead(BaseModel):
    id: int
    project_id: int
    step_id: Optional[int] = Field(
        default=None, description="null ⇒ project-level photo (§5)."
    )
    storage_key: str
    caption: Optional[str] = None
    created_at: datetime


class RetrospectiveRead(BaseModel):
    id: int
    project_id: int
    what_went_well: str
    what_i_would_do_differently: str
    skills_practiced: List[str]
    created_at: datetime


# ─────────────────────────────────────────────────────────────────────────────
# Projects (§5 projects, §11 Projects)
# ─────────────────────────────────────────────────────────────────────────────
class ProjectSummary(BaseModel):
    """List view (§11 GET /projects → the 1a 'Your projects' grid). Row-level
    fields only; no hydrated children."""

    id: int
    user_id: int
    module_id: int
    name: str
    slug: str = Field(description="Powers URLs, e.g. /my-mechanic/<slug>/… (§16).")
    skill_focus: List[str]
    difficulty: Difficulty
    time_budget: TimeBudget
    estimated_cost_usd: float
    summary: str
    workspace_required: str
    status: ProjectStatus
    spec_version: str
    created_at: datetime


class ProjectRead(ProjectSummary):
    """Full hydrated project (§11 GET /projects/{id}): spec + state + research +
    photos + retrospective."""

    materials: List[MaterialRead]
    tools: List[ToolRead]
    steps: List[StepRead]
    research_topics: List[ResearchTopicRead]
    photos: List[PhotoRead]
    retrospective: Optional[RetrospectiveRead] = None


class ProjectStatusUpdate(BaseModel):
    """§11 PATCH /projects/{id} — update status."""

    status: ProjectStatus


# ─────────────────────────────────────────────────────────────────────────────
# Item state mutations (§11 — designed to be offline-queued / replay-safe, §14)
# ─────────────────────────────────────────────────────────────────────────────
class MaterialUpdate(BaseModel):
    """§11 PATCH /projects/{id}/materials/{mid} — toggle checked."""

    checked: bool


class ToolUpdate(BaseModel):
    """§11 PATCH /projects/{id}/tools/{tid} — toggle checked / mark owned."""

    checked: Optional[bool] = None
    owned: Optional[bool] = None


class StepUpdate(BaseModel):
    """§11 PATCH /projects/{id}/steps/{sid} — toggle completed, set note."""

    completed: Optional[bool] = None
    note: Optional[str] = None


class RetrospectiveUpsert(BaseModel):
    """§11 PATCH /projects/{id}/retrospective — upsert retrospective."""

    what_went_well: str
    what_i_would_do_differently: str
    skills_practiced: List[str]


# ─────────────────────────────────────────────────────────────────────────────
# Shop inventory — "My Shop" (§5 shop_inventory, §11 Shop inventory)
# ─────────────────────────────────────────────────────────────────────────────
class ShopInventoryRead(BaseModel):
    id: int
    user_id: int
    tool_name: str
    category: Optional[str] = None
    notes: Optional[str] = None


class ShopInventoryCreate(BaseModel):
    """§11 POST /shop/inventory."""

    tool_name: str
    category: Optional[str] = None
    notes: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Photos (§11 Photos)
# ─────────────────────────────────────────────────────────────────────────────
# POST /projects/{id}/photos is multipart (file + optional step_id/caption) and
# is declared inline on the router. GET returns List[PhotoRead].


# ─────────────────────────────────────────────────────────────────────────────
# Claude — generate-via-chat (§7.1, §11, mocks 1d–1f)
# ─────────────────────────────────────────────────────────────────────────────
class GenerateSessionCreate(BaseModel):
    """§11 POST /generate/sessions — the setup payload (mock 1d)."""

    description: str = Field(
        description="Short free-text description (or the idea chip) of what to build."
    )
    skill_level: SkillLevel
    budget_band: BudgetBand


class GenerateSessionStart(BaseModel):
    """Response for POST /generate/sessions."""

    session_id: str
    agent_message: str = Field(description="The agent's opening message.")


class GenerateMessageCreate(BaseModel):
    """§11 POST /generate/sessions/{id}/messages — one user turn.

    Conversation state lives server-side keyed by session_id (§7.1), so a turn is
    tiny: EITHER a free-text reply OR selecting a previously proposed candidate
    (by its ``Candidate.id``). Exactly one of the two must be set.
    """

    message: Optional[str] = Field(
        default=None, min_length=1, description="A free-text user turn."
    )
    select_candidate_id: Optional[str] = Field(
        default=None,
        description="Accept a proposed candidate by its id (from a ProposeTurn).",
    )

    @model_validator(mode="after")
    def _exactly_one(self) -> "GenerateMessageCreate":
        provided = sum(
            x is not None for x in (self.message, self.select_candidate_id)
        )
        if provided != 1:
            raise ValueError(
                "Provide exactly one of 'message' or 'select_candidate_id'."
            )
        return self


class Candidate(BaseModel):
    """A proposed candidate project for vague/'surprise me' input (§7.1). The
    ``id`` is stable within the session and is echoed back via
    ``GenerateMessageCreate.select_candidate_id`` to pick it."""

    id: str = Field(description="Stable within the session; used to select this candidate.")
    title: str
    summary: str
    # Optional teasers so the picker can show badges without another round-trip.
    difficulty: Optional[Difficulty] = None
    est_cost_usd: Optional[float] = None


class GenerateProgress(BaseModel):
    """Rough progress sense for the bounded chat (§7.1: 'Design step · 3 of 5')."""

    label: str = Field(description='e.g. "Design step".')
    current: int
    total: Optional[int] = Field(
        default=None, description="Agent may not always know the total up front."
    )


# ── AgentTurn: a discriminated union on `kind` (mock 1e) ──────────────────────
# The reply names what kind of turn it is, so the client renders deterministically
# and new turn kinds are additive (consumers switch on `kind` with a default).
class _AgentTurnBase(BaseModel):
    session_id: str
    message_id: str = Field(description="Stable id for this agent turn; dedupe on retry.")
    agent_message: str = Field(description="Always-present natural-language text.")
    progress: Optional[GenerateProgress] = None


class ClarifyTurn(_AgentTurnBase):
    """Agent asked a clarifying question — awaiting a free-text answer."""

    kind: Literal["clarifying"] = "clarifying"


class ProposeTurn(_AgentTurnBase):
    """Agent proposed 2–3 candidate projects — awaiting a pick (§7.1, capped at 3)."""

    kind: Literal["proposing"] = "proposing"
    candidates: List[Candidate] = Field(min_length=1, max_length=3)


class ReadyTurn(_AgentTurnBase):
    """Agent has enough ('✓ Ready to generate documents') — client may call finalize."""

    kind: Literal["ready"] = "ready"


AgentTurn = Annotated[
    Union[ClarifyTurn, ProposeTurn, ReadyTurn],
    Field(discriminator="kind"),
]
"""Response for POST /generate/sessions/{id}/messages — the agent's reply (mock 1e)."""


# POST /generate/sessions/{id}/finalize → ProjectSpec (§6), declared on router.
# POST /projects/{id}/research/refresh → ProjectRead (hydrated), declared on router.
