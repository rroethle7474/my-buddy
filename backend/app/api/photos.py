"""Photos router (§11 Photos).

Upload is multipart (§11). Storage access goes only through the storage adapter
(§14) — wired in Phase 1.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, File, Form, UploadFile, status

from ..schemas.dtos import PhotoRead
from . import not_implemented

router = APIRouter(tags=["photos"])


@router.post(
    "/projects/{project_id}/photos",
    response_model=PhotoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a progress photo (multipart; optional step_id)",
)
def upload_photo(
    project_id: int,
    file: UploadFile = File(...),
    step_id: Optional[int] = Form(default=None),
    caption: Optional[str] = Form(default=None),
) -> PhotoRead:
    not_implemented()


@router.get(
    "/projects/{project_id}/photos",
    response_model=List[PhotoRead],
    summary="List a project's photos",
)
def list_photos(project_id: int) -> List[PhotoRead]:
    not_implemented()


@router.delete(
    "/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a photo",
)
def delete_photo(photo_id: int) -> None:
    not_implemented()
