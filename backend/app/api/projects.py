"""Projects router (§11 Projects + item-state mutations).

Item-state PATCH endpoints are nested under the project and are designed to be
offline-queued / replay-safe (§9, §14).
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from ..db import get_session
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
from ..services import projects as project_service

router = APIRouter(prefix="/projects", tags=["projects"])


# ── Project CRUD ─────────────────────────────────────────────────────────────
@router.get("", response_model=List[ProjectSummary], summary="List projects")
def list_projects(
    module: Optional[str] = None,
    status: Optional[ProjectStatus] = None,
    session: Session = Depends(get_session),
) -> List[ProjectSummary]:
    return project_service.list_projects(session, module=module, status_filter=status)


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Import a spec (validates, persists, runs shop diff §8)",
)
def create_project(spec: ProjectSpec, session: Session = Depends(get_session)) -> ProjectRead:
    # Import path (§7/§11): the request body is already gated by ProjectSpec.
    return project_service.create_project_from_spec(session, spec)


@router.get("/{project_id}", response_model=ProjectRead, summary="Get hydrated project")
def get_project(project_id: int, session: Session = Depends(get_session)) -> ProjectRead:
    return project_service.get_project_by_id(session, project_id)


@router.patch("/{project_id}", response_model=ProjectRead, summary="Update project status")
def update_project(
    project_id: int,
    body: ProjectStatusUpdate,
    session: Session = Depends(get_session),
) -> ProjectRead:
    return project_service.update_project_status(session, project_id, body)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a project",
)
def delete_project(project_id: int, session: Session = Depends(get_session)) -> None:
    project_service.soft_delete_project(session, project_id)


# ── Item-state mutations (offline-queued, replay-safe) ───────────────────────
@router.patch(
    "/{project_id}/materials/{material_id}",
    response_model=MaterialRead,
    summary="Toggle a material's checked state",
)
def update_material(
    project_id: int,
    material_id: int,
    body: MaterialUpdate,
    session: Session = Depends(get_session),
) -> MaterialRead:
    return project_service.update_material_checked(session, project_id, material_id, body.checked)


@router.patch(
    "/{project_id}/tools/{tool_id}",
    response_model=ToolRead,
    summary="Toggle a tool's checked / owned state",
)
def update_tool(
    project_id: int,
    tool_id: int,
    body: ToolUpdate,
    session: Session = Depends(get_session),
) -> ToolRead:
    return project_service.update_tool_state(session, project_id, tool_id, body)


@router.patch(
    "/{project_id}/steps/{step_id}",
    response_model=StepRead,
    summary="Toggle a step's completed state / set its note",
)
def update_step(
    project_id: int,
    step_id: int,
    body: StepUpdate,
    session: Session = Depends(get_session),
) -> StepRead:
    return project_service.update_step_state(session, project_id, step_id, body)


@router.patch(
    "/{project_id}/retrospective",
    response_model=RetrospectiveRead,
    summary="Upsert the project retrospective",
)
def upsert_retrospective(
    project_id: int,
    body: RetrospectiveUpsert,
    session: Session = Depends(get_session),
) -> RetrospectiveRead:
    return project_service.upsert_project_retrospective(session, project_id, body)
