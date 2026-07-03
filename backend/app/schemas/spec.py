"""The project spec schema (ARCHITECTURE.md §6) — the linchpin.

Both ingestion paths (import from a Cowork/chat brainstorm, and in-app Claude
generation) produce this *exact* shape. Every UI section renders off it.

This Pydantic model is the centralized validation gate (§6 note 3, §14): every
ingested spec is validated here before persisting, and rejected with a clear
error on mismatch. It is field-for-field equivalent to
``shared/project-spec.schema.json`` — the cross-language contract of record.
Changing either is a coordinated CONTRACT-CHANGE (COORDINATION.md §5/§6).

Runtime state fields (``checked``, ``completed``, ``note``, ``owned``,
``acquire``) are deliberately NOT in the spec — they are created in the DB when
a spec is ingested (§6 note 2).
"""

from __future__ import annotations

from enum import Enum
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field


class _SpecModel(BaseModel):
    """Base for all spec models: reject unknown fields so validation is strict
    (§6 note 3 — 'Reject with a clear error on mismatch')."""

    model_config = ConfigDict(extra="forbid")


class Difficulty(str, Enum):
    beginner = "beginner"
    handy = "handy"
    pro = "pro"


class TimeBudget(str, Enum):
    afternoon = "afternoon"
    weekend = "weekend"
    multi_weekend = "multi-weekend"


class ProjectMeta(_SpecModel):
    name: str
    module: str = Field(description='Module slug, e.g. "mechanic".')
    skill_focus: List[str]
    difficulty: Difficulty
    time_budget: TimeBudget
    estimated_cost_usd: float = Field(ge=0)
    summary: str = Field(
        description="One-paragraph description of the finished piece and what you'll learn."
    )
    workspace_required: str


class Material(_SpecModel):
    name: str
    quantity: float
    unit: str
    est_cost_usd: float = Field(ge=0)
    where_to_find: str
    notes: str


class Tool(_SpecModel):
    name: str
    essential: bool
    est_cost_usd: float = Field(ge=0)
    notes: str
    alternatives: str


class Step(_SpecModel):
    order: int = Field(ge=1)
    title: str
    instruction: str = Field(
        description="Detailed novice-level instruction. Assume no prior knowledge."
    )
    safety_note: str
    est_time_minutes: int = Field(ge=0)
    tools_used: List[str]
    materials_used: List[str]


class ResearchResource(_SpecModel):
    title: str
    url: str
    type: str = Field(description='e.g. "video", "article".')


class ResearchTopic(_SpecModel):
    topic: str
    why: str
    resources: List[ResearchResource] = Field(
        description="May arrive empty from generation; the research web-search "
        "pass (§7.2) fills them."
    )


class ProjectSpec(_SpecModel):
    """The full project spec (§6). This is the request body for the import path
    (``POST /projects``) and the response body for generation finalize
    (``POST /generate/sessions/{id}/finalize``)."""

    schema_version: Literal["1.0"] = Field(
        description="Spec schema version. Required and pinned; versioned from day one.",
    )
    project: ProjectMeta
    materials: List[Material]
    tools: List[Tool]
    steps: List[Step]
    research_topics: List[ResearchTopic]
