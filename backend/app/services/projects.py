"""Persistence helpers for modules, projects, item state, and shop inventory."""

from __future__ import annotations

import re
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.models import (
    Material as MaterialRow,
    Module as ModuleRow,
    Photo as PhotoRow,
    Project as ProjectRow,
    ResearchTopic as ResearchTopicRow,
    Retrospective as RetrospectiveRow,
    ShopInventory as ShopInventoryRow,
    Step as StepRow,
    Tool as ToolRow,
    User as UserRow,
)
from app.schemas.dtos import (
    MaterialRead,
    ModuleRead,
    PhotoRead,
    ProjectRead,
    ProjectStatus,
    ProjectStatusUpdate,
    ProjectSummary,
    ResearchTopicRead,
    RetrospectiveRead,
    RetrospectiveUpsert,
    ShopInventoryCreate,
    ShopInventoryRead,
    StepRead,
    StepUpdate,
    ToolRead,
    ToolUpdate,
)
from app.schemas.spec import ProjectSpec

DEFAULT_USER_ID = 1


def list_modules(session: Session) -> list[ModuleRead]:
    modules = session.exec(select(ModuleRow).order_by(ModuleRow.name)).all()
    return [to_module_read(module) for module in modules]


def get_module_by_slug(session: Session, slug: str) -> ModuleRead:
    module = session.exec(select(ModuleRow).where(ModuleRow.slug == slug)).first()
    if module is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found.")
    return to_module_read(module)


def list_projects(
    session: Session,
    module: str | None = None,
    status_filter: ProjectStatus | None = None,
) -> list[ProjectSummary]:
    statement = select(ProjectRow).where(
        ProjectRow.user_id == DEFAULT_USER_ID,
        ProjectRow.deleted_at.is_(None),
    )
    if module is not None:
        statement = statement.join(ModuleRow).where(ModuleRow.slug == module)
    if status_filter is not None:
        statement = statement.where(ProjectRow.status == status_filter.value)
    statement = statement.order_by(ProjectRow.created_at.desc())

    projects = session.exec(statement).all()
    return [to_project_summary(project) for project in projects]


def create_project_from_spec(session: Session, spec: ProjectSpec) -> ProjectRead:
    user = get_default_user(session)
    module = session.exec(select(ModuleRow).where(ModuleRow.slug == spec.project.module)).first()
    if module is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown module '{spec.project.module}'.",
        )

    project = ProjectRow(
        user_id=user.id,
        module_id=module.id,
        name=spec.project.name,
        slug=make_unique_project_slug(session, spec.project.name, user.id),
        skill_focus=spec.project.skill_focus,
        difficulty=spec.project.difficulty.value,
        time_budget=spec.project.time_budget.value,
        estimated_cost_usd=to_decimal(spec.project.estimated_cost_usd),
        summary=spec.project.summary,
        workspace_required=spec.project.workspace_required,
        status=ProjectStatus.planning.value,
        spec_version=spec.schema_version,
    )
    session.add(project)
    session.flush()
    if project.id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Project id was not assigned.",
        )

    owned_tool_names = [
        row.tool_name
        for row in session.exec(
            select(ShopInventoryRow).where(ShopInventoryRow.user_id == user.id)
        ).all()
    ]

    for material in spec.materials:
        session.add(
            MaterialRow(
                project_id=project.id,
                name=material.name,
                quantity=to_decimal(material.quantity),
                unit=material.unit,
                est_cost_usd=to_decimal(material.est_cost_usd),
                where_to_find=material.where_to_find,
                notes=material.notes,
                checked=False,
            )
        )

    for tool in spec.tools:
        owned = is_tool_owned(tool.name, owned_tool_names)
        session.add(
            ToolRow(
                project_id=project.id,
                name=tool.name,
                essential=tool.essential,
                est_cost_usd=to_decimal(tool.est_cost_usd),
                notes=tool.notes,
                alternatives=tool.alternatives,
                owned=owned,
                acquire=not owned,
                checked=owned,
            )
        )

    for step in spec.steps:
        session.add(
            StepRow(
                project_id=project.id,
                order=step.order,
                title=step.title,
                instruction=step.instruction,
                safety_note=step.safety_note,
                est_time_minutes=step.est_time_minutes,
                tools_used=step.tools_used,
                materials_used=step.materials_used,
                completed=False,
                note=None,
            )
        )

    for topic in spec.research_topics:
        session.add(
            ResearchTopicRow(
                project_id=project.id,
                topic=topic.topic,
                why=topic.why,
                resources=[resource.model_dump(mode="json") for resource in topic.resources],
            )
        )

    session.commit()
    return get_project_by_id(session, project.id)


def get_project_by_id(session: Session, project_id: int) -> ProjectRead:
    project = load_project_row(session, project_id)
    return to_project_read(project)


def update_project_status(
    session: Session, project_id: int, body: ProjectStatusUpdate
) -> ProjectRead:
    project = load_project_row(session, project_id)
    project.status = body.status.value
    session.add(project)
    session.commit()
    return get_project_by_id(session, project_id)


def soft_delete_project(session: Session, project_id: int) -> None:
    from app.models.tables import utc_now

    project = load_project_row(session, project_id)
    project.deleted_at = utc_now()
    session.add(project)
    session.commit()


def update_material_checked(
    session: Session, project_id: int, material_id: int, checked: bool
) -> MaterialRead:
    material = session.exec(
        select(MaterialRow).where(
            MaterialRow.id == material_id,
            MaterialRow.project_id == project_id,
        )
    ).first()
    if material is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material not found.")
    ensure_project_is_active(session, project_id)
    material.checked = checked
    session.add(material)
    session.commit()
    session.refresh(material)
    return to_material_read(material)


def update_tool_state(
    session: Session, project_id: int, tool_id: int, body: ToolUpdate
) -> ToolRead:
    tool = session.exec(
        select(ToolRow).where(
            ToolRow.id == tool_id,
            ToolRow.project_id == project_id,
        )
    ).first()
    if tool is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool not found.")
    ensure_project_is_active(session, project_id)

    if body.owned is not None:
        tool.owned = body.owned
        tool.acquire = not body.owned
        if body.owned:
            tool.checked = True
        elif body.checked is None:
            tool.checked = False
    if body.checked is not None:
        tool.checked = body.checked

    session.add(tool)
    session.commit()
    session.refresh(tool)
    return to_tool_read(tool)


def update_step_state(
    session: Session, project_id: int, step_id: int, body: StepUpdate
) -> StepRead:
    step = session.exec(
        select(StepRow).where(
            StepRow.id == step_id,
            StepRow.project_id == project_id,
        )
    ).first()
    if step is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Step not found.")
    ensure_project_is_active(session, project_id)

    if body.completed is not None:
        step.completed = body.completed
    if "note" in body.model_fields_set:
        step.note = body.note

    session.add(step)
    session.commit()
    session.refresh(step)
    return to_step_read(step)


def upsert_project_retrospective(
    session: Session,
    project_id: int,
    body: RetrospectiveUpsert,
) -> RetrospectiveRead:
    ensure_project_is_active(session, project_id)
    retrospective = session.exec(
        select(RetrospectiveRow).where(RetrospectiveRow.project_id == project_id)
    ).first()
    if retrospective is None:
        retrospective = RetrospectiveRow(
            project_id=project_id,
            what_went_well=body.what_went_well,
            what_i_would_do_differently=body.what_i_would_do_differently,
            skills_practiced=body.skills_practiced,
        )
    else:
        retrospective.what_went_well = body.what_went_well
        retrospective.what_i_would_do_differently = body.what_i_would_do_differently
        retrospective.skills_practiced = body.skills_practiced

    session.add(retrospective)
    session.commit()
    session.refresh(retrospective)
    return to_retrospective_read(retrospective)


def list_shop_inventory(session: Session) -> list[ShopInventoryRead]:
    get_default_user(session)
    rows = session.exec(
        select(ShopInventoryRow)
        .where(ShopInventoryRow.user_id == DEFAULT_USER_ID)
        .order_by(ShopInventoryRow.tool_name)
    ).all()
    return [to_shop_inventory_read(row) for row in rows]


def create_shop_inventory(session: Session, body: ShopInventoryCreate) -> ShopInventoryRead:
    user = get_default_user(session)
    existing = find_matching_shop_inventory(session, user.id, body.tool_name)
    if existing is not None:
        if body.category is not None:
            existing.category = body.category
        if body.notes is not None:
            existing.notes = body.notes
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return to_shop_inventory_read(existing)

    row = ShopInventoryRow(
        user_id=user.id,
        tool_name=body.tool_name,
        category=body.category,
        notes=body.notes,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return to_shop_inventory_read(row)


def delete_shop_inventory(session: Session, inventory_id: int) -> None:
    row = session.exec(
        select(ShopInventoryRow).where(
            ShopInventoryRow.id == inventory_id,
            ShopInventoryRow.user_id == DEFAULT_USER_ID,
        )
    ).first()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Inventory item not found."
        )
    session.delete(row)
    session.commit()


def find_matching_shop_inventory(
    session: Session, user_id: int, tool_name: str
) -> ShopInventoryRow | None:
    rows = session.exec(select(ShopInventoryRow).where(ShopInventoryRow.user_id == user_id)).all()
    for row in rows:
        if tool_names_match(tool_name, row.tool_name):
            return row
    return None


def load_project_row(session: Session, project_id: int) -> ProjectRow:
    statement = (
        select(ProjectRow)
        .where(ProjectRow.id == project_id, ProjectRow.deleted_at.is_(None))
        .options(
            selectinload(ProjectRow.materials),
            selectinload(ProjectRow.tools),
            selectinload(ProjectRow.steps),
            selectinload(ProjectRow.research_topics),
            selectinload(ProjectRow.photos),
            selectinload(ProjectRow.retrospective),
        )
    )
    project = session.exec(statement).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")
    return project


def ensure_project_is_active(session: Session, project_id: int) -> None:
    project_exists = session.exec(
        select(ProjectRow.id).where(ProjectRow.id == project_id, ProjectRow.deleted_at.is_(None))
    ).first()
    if project_exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")


def get_default_user(session: Session) -> UserRow:
    user = session.get(UserRow, DEFAULT_USER_ID)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user seed is missing. Run Alembic migrations.",
        )
    return user


def make_unique_project_slug(session: Session, name: str, user_id: int) -> str:
    base = slugify(name)
    slug = base
    suffix = 2
    while project_slug_exists(session, slug, user_id):
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


def project_slug_exists(session: Session, slug: str, user_id: int) -> bool:
    existing = session.exec(
        select(ProjectRow.id).where(
            ProjectRow.user_id == user_id,
            ProjectRow.slug == slug,
            ProjectRow.deleted_at.is_(None),
        )
    ).first()
    return existing is not None


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "project"


def is_tool_owned(tool_name: str, owned_tool_names: list[str]) -> bool:
    return any(tool_names_match(tool_name, owned_tool_name) for owned_tool_name in owned_tool_names)


def tool_names_match(left: str, right: str) -> bool:
    left_tokens = tool_tokens(left)
    right_tokens = tool_tokens(right)
    if not left_tokens or not right_tokens:
        return False
    return (
        left_tokens == right_tokens
        or left_tokens.issubset(right_tokens)
        or right_tokens.issubset(left_tokens)
    )


def tool_tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def to_decimal(value: float | Decimal) -> Decimal:
    return Decimal(str(value))


def to_module_read(module: ModuleRow) -> ModuleRead:
    return ModuleRead(
        id=module.id,
        slug=module.slug,
        name=module.name,
        description=module.description,
    )


def to_project_summary(project: ProjectRow) -> ProjectSummary:
    return ProjectSummary(
        id=project.id,
        user_id=project.user_id,
        module_id=project.module_id,
        name=project.name,
        slug=project.slug,
        skill_focus=project.skill_focus,
        difficulty=project.difficulty,
        time_budget=project.time_budget,
        estimated_cost_usd=float(project.estimated_cost_usd),
        summary=project.summary,
        workspace_required=project.workspace_required,
        status=project.status,
        spec_version=project.spec_version,
        created_at=project.created_at,
    )


def to_project_read(project: ProjectRow) -> ProjectRead:
    return ProjectRead(
        **to_project_summary(project).model_dump(),
        materials=[
            to_material_read(row) for row in sorted(project.materials, key=lambda row: row.id)
        ],
        tools=[to_tool_read(row) for row in sorted(project.tools, key=lambda row: row.id)],
        steps=[to_step_read(row) for row in sorted(project.steps, key=lambda row: row.order)],
        research_topics=[
            to_research_topic_read(row)
            for row in sorted(project.research_topics, key=lambda row: row.id)
        ],
        photos=[to_photo_read(row) for row in sorted(project.photos, key=lambda row: row.id)],
        retrospective=(
            to_retrospective_read(project.retrospective)
            if project.retrospective is not None
            else None
        ),
    )


def to_material_read(material: MaterialRow) -> MaterialRead:
    return MaterialRead(
        id=material.id,
        project_id=material.project_id,
        name=material.name,
        quantity=float(material.quantity),
        unit=material.unit,
        est_cost_usd=float(material.est_cost_usd),
        where_to_find=material.where_to_find,
        notes=material.notes,
        checked=material.checked,
    )


def to_tool_read(tool: ToolRow) -> ToolRead:
    return ToolRead(
        id=tool.id,
        project_id=tool.project_id,
        name=tool.name,
        essential=tool.essential,
        est_cost_usd=float(tool.est_cost_usd),
        notes=tool.notes,
        alternatives=tool.alternatives,
        owned=tool.owned,
        acquire=tool.acquire,
        checked=tool.checked,
    )


def to_step_read(step: StepRow) -> StepRead:
    return StepRead(
        id=step.id,
        project_id=step.project_id,
        order=step.order,
        title=step.title,
        instruction=step.instruction,
        safety_note=step.safety_note,
        est_time_minutes=step.est_time_minutes,
        tools_used=step.tools_used,
        materials_used=step.materials_used,
        completed=step.completed,
        note=step.note,
    )


def to_research_topic_read(topic: ResearchTopicRow) -> ResearchTopicRead:
    return ResearchTopicRead(
        id=topic.id,
        project_id=topic.project_id,
        topic=topic.topic,
        why=topic.why,
        resources=topic.resources,
    )


def to_photo_read(photo: PhotoRow) -> PhotoRead:
    return PhotoRead(
        id=photo.id,
        project_id=photo.project_id,
        step_id=photo.step_id,
        storage_key=photo.storage_key,
        caption=photo.caption,
        created_at=photo.created_at,
    )


def to_retrospective_read(retrospective: RetrospectiveRow) -> RetrospectiveRead:
    return RetrospectiveRead(
        id=retrospective.id,
        project_id=retrospective.project_id,
        what_went_well=retrospective.what_went_well,
        what_i_would_do_differently=retrospective.what_i_would_do_differently,
        skills_practiced=retrospective.skills_practiced,
        created_at=retrospective.created_at,
    )


def to_shop_inventory_read(row: ShopInventoryRow) -> ShopInventoryRead:
    return ShopInventoryRead(
        id=row.id,
        user_id=row.user_id,
        tool_name=row.tool_name,
        category=row.category,
        notes=row.notes,
    )
