"""Photo persistence and storage orchestration."""

from __future__ import annotations

import mimetypes
import re
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlmodel import Session, select

from app.models import Photo as PhotoRow
from app.models import Project as ProjectRow
from app.models import Step as StepRow
from app.schemas.dtos import PhotoRead
from app.storage import StorageAdapter


def upload_project_photo(
    session: Session,
    storage: StorageAdapter,
    project_id: int,
    file: UploadFile,
    step_id: int | None = None,
    caption: str | None = None,
) -> PhotoRead:
    ensure_project_exists(session, project_id)
    if step_id is not None:
        ensure_step_belongs_to_project(session, project_id, step_id)

    content_type = file.content_type or "application/octet-stream"
    if content_type != "application/octet-stream" and not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded photo must be an image.",
        )

    data = file.file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded photo was empty.",
        )

    key = make_photo_key(project_id, file.filename, content_type)
    storage.put(key, data, content_type)

    row = PhotoRow(
        project_id=project_id,
        step_id=step_id,
        storage_key=key,
        caption=caption,
    )
    try:
        session.add(row)
        session.commit()
        session.refresh(row)
    except Exception:
        storage.delete(key)
        raise

    return to_photo_read(row)


def list_project_photos(session: Session, project_id: int) -> list[PhotoRead]:
    ensure_project_exists(session, project_id)
    rows = session.exec(
        select(PhotoRow).where(PhotoRow.project_id == project_id).order_by(PhotoRow.created_at)
    ).all()
    return [to_photo_read(row) for row in rows]


def delete_project_photo(session: Session, storage: StorageAdapter, photo_id: int) -> None:
    row = session.get(PhotoRow, photo_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Photo not found.")

    storage.delete(row.storage_key)
    session.delete(row)
    session.commit()


def ensure_project_exists(session: Session, project_id: int) -> None:
    project_exists = session.exec(
        select(ProjectRow.id).where(ProjectRow.id == project_id, ProjectRow.deleted_at.is_(None))
    ).first()
    if project_exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found.")


def ensure_step_belongs_to_project(session: Session, project_id: int, step_id: int) -> None:
    step_exists = session.exec(
        select(StepRow.id).where(StepRow.id == step_id, StepRow.project_id == project_id)
    ).first()
    if step_exists is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="step_id does not belong to this project.",
        )


def make_photo_key(project_id: int, filename: str | None, content_type: str) -> str:
    suffix = safe_suffix(filename)
    if suffix is None:
        suffix = mimetypes.guess_extension(content_type) or ".bin"
    return f"projects/{project_id}/photos/{uuid4().hex}{suffix}"


def safe_suffix(filename: str | None) -> str | None:
    suffix = Path(filename or "").suffix.lower()
    if re.fullmatch(r"\.[a-z0-9]{1,10}", suffix):
        return suffix
    return None


def to_photo_read(photo: PhotoRow) -> PhotoRead:
    return PhotoRead(
        id=photo.id,
        project_id=photo.project_id,
        step_id=photo.step_id,
        storage_key=photo.storage_key,
        caption=photo.caption,
        created_at=photo.created_at,
    )
