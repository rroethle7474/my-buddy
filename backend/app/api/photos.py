"""Photos router (§11 Photos).

Upload is multipart (§11). Storage access goes only through the storage adapter
(§14) — wired in Phase 1.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from sqlmodel import Session

from ..db import get_session
from ..schemas.dtos import PhotoRead
from ..services import photos as photo_service
from ..storage import StorageAdapter, get_storage

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
    session: Session = Depends(get_session),
    storage: StorageAdapter = Depends(get_storage),
) -> PhotoRead:
    return photo_service.upload_project_photo(
        session,
        storage,
        project_id,
        file,
        step_id=step_id,
        caption=caption,
    )


@router.get(
    "/projects/{project_id}/photos",
    response_model=List[PhotoRead],
    summary="List a project's photos",
)
def list_photos(
    project_id: int,
    session: Session = Depends(get_session),
) -> List[PhotoRead]:
    return photo_service.list_project_photos(session, project_id)


@router.delete(
    "/photos/{photo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a photo",
)
def delete_photo(
    photo_id: int,
    session: Session = Depends(get_session),
    storage: StorageAdapter = Depends(get_storage),
) -> None:
    photo_service.delete_project_photo(session, storage, photo_id)


# Out-of-schema byte route (decided with Ryan 2026-07-04): serves a photo's bytes
# for the client's <img> src. `include_in_schema=False` keeps the §11 OpenAPI
# surface (the 17-path invariant) frozen — this is deliberately NOT part of the
# generated contract. Serving stays behind the storage adapter (§3) so a future
# swap to R2/presigned URLs is a config change. See ARCHITECTURE.md §11.
@router.get("/photos/{photo_id}/content", include_in_schema=False)
def get_photo_content(
    photo_id: int,
    session: Session = Depends(get_session),
    storage: StorageAdapter = Depends(get_storage),
) -> Response:
    data, media_type = photo_service.read_photo_content(session, storage, photo_id)
    return Response(
        content=data,
        media_type=media_type,
        headers={"Cache-Control": "private, max-age=3600"},
    )
