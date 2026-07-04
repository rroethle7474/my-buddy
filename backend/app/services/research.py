"""Persistence for the research refresh pass (ARCHITECTURE.md §7.2, §11).

Bridges claude-service's web-search logic (``app.claude.research``) to
backend-core's persisted ``research_topics`` rows: load a project's topics, run
the web-search pass over them, write the found resources back into each row's
JSONB ``resources``, and return the refreshed topics (the exact delta the client
patches its cache with, by ``ResearchTopicRead.id``).

Kept out of ``services/projects.py`` (backend-core's file) so the two worktrees
don't collide; this module owns only the research-refresh feature (worktree B).
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.claude.client import ClaudeClient, ClaudeError
from app.claude.research import run_research
from app.models import Project as ProjectRow, ResearchTopic as ResearchTopicRow
from app.schemas.dtos import ResearchTopicRead


def refresh_project_research(
    session: Session,
    claude: ClaudeClient,
    project_id: int,
) -> list[ResearchTopicRead]:
    """Re-populate ``resources[]`` for every research topic of a project (§7.2).

    Raises 404 if the project is missing/soft-deleted, 502 if the upstream
    web-search call fails. A topic the search found nothing for is written as an
    empty list (idempotent-friendly, replay-safe — §14).
    """
    project_exists = session.exec(
        select(ProjectRow.id).where(
            ProjectRow.id == project_id, ProjectRow.deleted_at.is_(None)
        )
    ).first()
    if project_exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")

    topics = session.exec(
        select(ResearchTopicRow)
        .where(ResearchTopicRow.project_id == project_id)
        .order_by(ResearchTopicRow.id)
    ).all()
    if not topics:
        return []

    try:
        resources_by_topic = run_research(claude, [topic.topic for topic in topics])
    except ClaudeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Research lookup failed: {exc}",
        ) from exc

    for topic in topics:
        found = resources_by_topic.get(topic.topic, [])
        topic.resources = [resource.model_dump(mode="json") for resource in found]
        session.add(topic)
    session.commit()

    for topic in topics:
        session.refresh(topic)

    return [
        ResearchTopicRead(
            id=topic.id,
            project_id=topic.project_id,
            topic=topic.topic,
            why=topic.why,
            resources=topic.resources,
        )
        for topic in topics
    ]
