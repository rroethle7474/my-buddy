"""Add photos.content_type (additive).

Captures the upload's MIME type so ``GET /photos/{id}/content`` serves the
stored type instead of sniffing the storage-key suffix. Nullable with no
backfill: existing rows keep NULL and fall back to suffix inference at serve
time (F1 item 3).

Revision ID: 20260704_0002
Revises: 20260704_0001
Create Date: 2026-07-04 14:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260704_0002"
down_revision: str | None = "20260704_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "photos",
        sa.Column("content_type", sa.String(length=128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("photos", "content_type")
