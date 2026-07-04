"""Initial backend schema.

Revision ID: 20260704_0001
Revises:
Create Date: 2026-07-04 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260704_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "modules",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_modules_slug"),
    )

    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "module_id",
            sa.Integer(),
            sa.ForeignKey("modules.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False),
        sa.Column("skill_focus", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("difficulty", sa.String(length=32), nullable=False),
        sa.Column("time_budget", sa.String(length=32), nullable=False),
        sa.Column("estimated_cost_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("workspace_required", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="planning", nullable=False),
        sa.Column("spec_version", sa.String(length=16), server_default="1.0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_projects_user_status", "projects", ["user_id", "status"])
    op.create_index("ix_projects_module_status", "projects", ["module_id", "status"])
    op.create_index("uq_projects_user_slug", "projects", ["user_id", "slug"], unique=True)

    op.create_table(
        "materials",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 3), nullable=False),
        sa.Column("unit", sa.String(length=64), nullable=False),
        sa.Column("est_cost_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("where_to_find", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), server_default="", nullable=False),
        sa.Column("checked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("ix_materials_project_id", "materials", ["project_id"])

    op.create_table(
        "tools",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("essential", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("est_cost_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("notes", sa.Text(), server_default="", nullable=False),
        sa.Column("alternatives", sa.Text(), server_default="", nullable=False),
        sa.Column("owned", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("acquire", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("checked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.create_index("ix_tools_project_id", "tools", ["project_id"])

    op.create_table(
        "steps",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("order", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("safety_note", sa.Text(), nullable=False),
        sa.Column("est_time_minutes", sa.Integer(), nullable=False),
        sa.Column("tools_used", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("materials_used", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("completed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_index("ix_steps_project_id", "steps", ["project_id"])
    op.create_index("uq_steps_project_order", "steps", ["project_id", "order"], unique=True)

    op.create_table(
        "research_topics",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("topic", sa.String(length=200), nullable=False),
        sa.Column("why", sa.Text(), nullable=False),
        sa.Column("resources", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    )
    op.create_index("ix_research_topics_project_id", "research_topics", ["project_id"])

    op.create_table(
        "photos",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "step_id",
            sa.Integer(),
            sa.ForeignKey("steps.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("storage_key", name="uq_photos_storage_key"),
    )
    op.create_index("ix_photos_project_id", "photos", ["project_id"])
    op.create_index("ix_photos_step_id", "photos", ["step_id"])

    op.create_table(
        "shop_inventory",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tool_name", sa.String(length=200), nullable=False),
        sa.Column("category", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_shop_inventory_user_id", "shop_inventory", ["user_id"])
    op.create_index(
        "ix_shop_inventory_user_tool_name",
        "shop_inventory",
        ["user_id", "tool_name"],
    )

    op.create_table(
        "retrospectives",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "project_id",
            sa.Integer(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("what_went_well", sa.Text(), nullable=False),
        sa.Column("what_i_would_do_differently", sa.Text(), nullable=False),
        sa.Column("skills_practiced", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("uq_retrospectives_project_id", "retrospectives", ["project_id"], unique=True)

    op.bulk_insert(
        sa.table(
            "users",
            sa.column("id", sa.Integer()),
            sa.column("email", sa.String()),
        ),
        [{"id": 1, "email": "owner@my-buddy.local"}],
    )
    op.bulk_insert(
        sa.table(
            "modules",
            sa.column("id", sa.Integer()),
            sa.column("slug", sa.String()),
            sa.column("name", sa.String()),
            sa.column("description", sa.String()),
        ),
        [
            {
                "id": 1,
                "slug": "mechanic",
                "name": "My Mechanic",
                "description": "Hands-on DIY builds for becoming more mechanically inclined.",
            }
        ],
    )


def downgrade() -> None:
    op.drop_index("uq_retrospectives_project_id", table_name="retrospectives")
    op.drop_table("retrospectives")
    op.drop_index("ix_shop_inventory_user_tool_name", table_name="shop_inventory")
    op.drop_index("ix_shop_inventory_user_id", table_name="shop_inventory")
    op.drop_table("shop_inventory")
    op.drop_index("ix_photos_step_id", table_name="photos")
    op.drop_index("ix_photos_project_id", table_name="photos")
    op.drop_table("photos")
    op.drop_index("ix_research_topics_project_id", table_name="research_topics")
    op.drop_table("research_topics")
    op.drop_index("uq_steps_project_order", table_name="steps")
    op.drop_index("ix_steps_project_id", table_name="steps")
    op.drop_table("steps")
    op.drop_index("ix_tools_project_id", table_name="tools")
    op.drop_table("tools")
    op.drop_index("ix_materials_project_id", table_name="materials")
    op.drop_table("materials")
    op.drop_index("uq_projects_user_slug", table_name="projects")
    op.drop_index("ix_projects_module_status", table_name="projects")
    op.drop_index("ix_projects_user_status", table_name="projects")
    op.drop_table("projects")
    op.drop_table("modules")
    op.drop_table("users")
