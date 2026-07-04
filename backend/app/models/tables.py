"""SQLModel table definitions for the persisted v1 backend state.

The project spec is the immutable plan (§6); these tables hold that plan plus
the mutable runtime state needed by the mechanic UI (§5).
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(sa_column=Column(String(320), nullable=False, unique=True))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    projects: list["Project"] = Relationship(back_populates="user")
    shop_inventory: list["ShopInventory"] = Relationship(back_populates="user")


class Module(SQLModel, table=True):
    __tablename__ = "modules"

    id: int | None = Field(default=None, primary_key=True)
    slug: str = Field(sa_column=Column(String(64), nullable=False, unique=True))
    name: str = Field(sa_column=Column(String(120), nullable=False))
    description: str = Field(sa_column=Column(Text, nullable=False))

    projects: list["Project"] = Relationship(back_populates="module")


class Project(SQLModel, table=True):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_user_status", "user_id", "status"),
        Index("ix_projects_module_status", "module_id", "status"),
        Index("uq_projects_user_slug", "user_id", "slug", unique=True),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    module_id: int = Field(
        sa_column=Column(Integer, ForeignKey("modules.id", ondelete="RESTRICT"), nullable=False)
    )
    name: str = Field(sa_column=Column(String(200), nullable=False))
    slug: str = Field(sa_column=Column(String(220), nullable=False))
    skill_focus: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    difficulty: str = Field(sa_column=Column(String(32), nullable=False))
    time_budget: str = Field(sa_column=Column(String(32), nullable=False))
    estimated_cost_usd: Decimal = Field(
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    summary: str = Field(sa_column=Column(Text, nullable=False))
    workspace_required: str = Field(sa_column=Column(Text, nullable=False))
    status: str = Field(default="planning", sa_column=Column(String(32), nullable=False))
    spec_version: str = Field(default="1.0", sa_column=Column(String(16), nullable=False))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    deleted_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    user: User = Relationship(back_populates="projects")
    module: Module = Relationship(back_populates="projects")
    materials: list["Material"] = Relationship(back_populates="project")
    tools: list["Tool"] = Relationship(back_populates="project")
    steps: list["Step"] = Relationship(back_populates="project")
    research_topics: list["ResearchTopic"] = Relationship(back_populates="project")
    photos: list["Photo"] = Relationship(back_populates="project")
    retrospective: Optional["Retrospective"] = Relationship(back_populates="project")


class Material(SQLModel, table=True):
    __tablename__ = "materials"
    __table_args__ = (Index("ix_materials_project_id", "project_id"),)

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(
        sa_column=Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    )
    name: str = Field(sa_column=Column(String(200), nullable=False))
    quantity: Decimal = Field(sa_column=Column(Numeric(10, 3), nullable=False))
    unit: str = Field(sa_column=Column(String(64), nullable=False))
    est_cost_usd: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    where_to_find: str = Field(sa_column=Column(Text, nullable=False))
    notes: str = Field(default="", sa_column=Column(Text, nullable=False))
    checked: bool = Field(default=False, nullable=False)

    project: Project = Relationship(back_populates="materials")


class Tool(SQLModel, table=True):
    __tablename__ = "tools"
    __table_args__ = (Index("ix_tools_project_id", "project_id"),)

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(
        sa_column=Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    )
    name: str = Field(sa_column=Column(String(200), nullable=False))
    essential: bool = Field(default=True, nullable=False)
    est_cost_usd: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    notes: str = Field(default="", sa_column=Column(Text, nullable=False))
    alternatives: str = Field(default="", sa_column=Column(Text, nullable=False))
    owned: bool = Field(default=False, nullable=False)
    acquire: bool = Field(default=True, nullable=False)
    checked: bool = Field(default=False, nullable=False)

    project: Project = Relationship(back_populates="tools")


class Step(SQLModel, table=True):
    __tablename__ = "steps"
    __table_args__ = (
        Index("ix_steps_project_id", "project_id"),
        Index("uq_steps_project_order", "project_id", "order", unique=True),
    )

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(
        sa_column=Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    )
    order: int = Field(sa_column=Column("order", Integer, nullable=False))
    title: str = Field(sa_column=Column(String(200), nullable=False))
    instruction: str = Field(sa_column=Column(Text, nullable=False))
    safety_note: str = Field(sa_column=Column(Text, nullable=False))
    est_time_minutes: int = Field(nullable=False)
    tools_used: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    materials_used: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    completed: bool = Field(default=False, nullable=False)
    note: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    project: Project = Relationship(back_populates="steps")
    photos: list["Photo"] = Relationship(back_populates="step")


class ResearchTopic(SQLModel, table=True):
    __tablename__ = "research_topics"
    __table_args__ = (Index("ix_research_topics_project_id", "project_id"),)

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(
        sa_column=Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    )
    topic: str = Field(sa_column=Column(String(200), nullable=False))
    why: str = Field(sa_column=Column(Text, nullable=False))
    resources: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )

    project: Project = Relationship(back_populates="research_topics")


class Photo(SQLModel, table=True):
    __tablename__ = "photos"
    __table_args__ = (
        Index("ix_photos_project_id", "project_id"),
        Index("ix_photos_step_id", "step_id"),
    )

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(
        sa_column=Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    )
    step_id: int | None = Field(
        default=None,
        sa_column=Column(Integer, ForeignKey("steps.id", ondelete="SET NULL"), nullable=True),
    )
    storage_key: str = Field(sa_column=Column(String(512), nullable=False, unique=True))
    caption: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    project: Project = Relationship(back_populates="photos")
    step: Step | None = Relationship(back_populates="photos")


class ShopInventory(SQLModel, table=True):
    __tablename__ = "shop_inventory"
    __table_args__ = (
        Index("ix_shop_inventory_user_id", "user_id"),
        Index("ix_shop_inventory_user_tool_name", "user_id", "tool_name"),
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(
        sa_column=Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    tool_name: str = Field(sa_column=Column(String(200), nullable=False))
    category: str | None = Field(default=None, sa_column=Column(String(120), nullable=True))
    notes: str | None = Field(default=None, sa_column=Column(Text, nullable=True))

    user: User = Relationship(back_populates="shop_inventory")


class Retrospective(SQLModel, table=True):
    __tablename__ = "retrospectives"
    __table_args__ = (Index("uq_retrospectives_project_id", "project_id", unique=True),)

    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(
        sa_column=Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    )
    what_went_well: str = Field(sa_column=Column(Text, nullable=False))
    what_i_would_do_differently: str = Field(sa_column=Column(Text, nullable=False))
    skills_practiced: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
    )
    created_at: datetime = Field(
        default_factory=utc_now,
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )

    project: Project = Relationship(back_populates="retrospective")
