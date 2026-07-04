"""Database session / engine (ARCHITECTURE.md §10).

The engine is created lazily and does not connect at import time, so the app
still boots without Postgres reachable. SQLModel table definitions live in
``app/models`` and schema changes are applied through Alembic.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, create_engine

from .config import settings

# ``create_engine`` does not open a connection until first use, so importing
# this module never requires a live database.
engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a DB session."""
    with Session(engine) as session:
        yield session
