"""Database session / engine (ARCHITECTURE.md §10).

Phase 0 scaffold only: the engine is created lazily and does not connect at
import time, so the app boots without Postgres reachable. No models, no tables,
no migrations here — that is Phase 1 (backend-core, §12/§13). SQLModel table
definitions land in ``app/models`` and migrations in ``alembic/`` later.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlmodel import Session, create_engine

from .config import settings

# ``create_engine`` does not open a connection until first use, so importing
# this module never requires a live database.
engine = create_engine(settings.database_url, echo=False, pool_pre_ping=True)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a DB session. Unused by Phase 0 stubs;
    provided so Phase 1 routers can depend on it without touching db wiring."""
    with Session(engine) as session:
        yield session
