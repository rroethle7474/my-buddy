"""Projects router (§11 Projects + item-state mutations).

Item-state PATCH endpoints are nested under the project and are designed to be
offline-queued / replay-safe (§9, §14).
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, status

from ..schemas.dtos import (
    MaterialRead,
    MaterialUpdate,
    ProjectRead,
    ProjectStatus,
    ProjectStatusUpdate,
    ProjectSummary,
    RetrospectiveRead,
    RetrospectiveUpsert,
    StepRead,
    StepUpdate,
    ToolRead,
    ToolUpdate,
)
from ..schemas.spec import ProjectSpec
from . import not_implemented

router = APIRouter(prefix="/projects", tags=["projects"])


# ── Project CRUD ─────────────────────────────────────────────────────────────
@router.get("", response_model=List[ProjectSummary], summary="List projects")
def list_projects(
    module: Optional[str] = None,
    status: Optional[ProjectStatus] = None,
) -> List[ProjectSummary]:
    not_implemented()


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Import a spec (validates, persists, runs shop diff §8)",
)
def create_project(spec: ProjectSpec) -> ProjectRead:
    # Import path (§7/§11): the request body is a full §6 spec. Phase 1 validates
    # it (already gated by the Pydantic model), persists it, and runs the shop
    # diff (§8) before returning the hydrated project.
    not_implemented()


@router.get("/{project_id}", response_model=ProjectRead, summary="Get hydrated project")
def get_project(project_id: int) -> ProjectRead:
    not_implemented()


@router.patch("/{project_id}", response_model=ProjectRead, summary="Update project status")
def update_project(project_id: int, body: ProjectStatusUpdate) -> ProjectRead:
    not_implemented()


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a project",
)
def delete_project(project_id: int) -> None:
    not_implemented()


# ── Item-state mutations (offline-queued, replay-safe) ───────────────────────
@router.patch(
    "/{project_id}/materials/{material_id}",
    response_model=MaterialRead,
    summary="Toggle a material's checked state",
)
def update_material(
    project_id: int, material_id: int, body: MaterialUpdate
) -> MaterialRead:
    not_implemented()


@router.patch(
    "/{project_id}/tools/{tool_id}",
    response_model=ToolRead,
    summary="Toggle a tool's checked / owned state",
)
def update_tool(project_id: int, tool_id: int, body: ToolUpdate) -> ToolRead:
    not_implemented()


@router.patch(
    "/{project_id}/steps/{step_id}",
    response_model=StepRead,
    summary="Toggle a step's completed state / set its note",
)
def update_step(project_id: int, step_id: int, body: StepUpdate) -> StepRead:
    not_implemented()


@router.patch(
    "/{project_id}/retrospective",
    response_model=RetrospectiveRead,
    summary="Upsert the project retrospective",
)
def upsert_retrospective(
    project_id: int, body: RetrospectiveUpsert
) -> RetrospectiveRead:
    not_implemented()
