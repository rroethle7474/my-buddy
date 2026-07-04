"""Modules router (§11 Modules)."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..db import get_session
from ..schemas.dtos import ModuleRead
from ..services import projects as project_service

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("", response_model=List[ModuleRead], summary="List modules")
def list_modules(session: Session = Depends(get_session)) -> List[ModuleRead]:
    return project_service.list_modules(session)


@router.get("/{slug}", response_model=ModuleRead, summary="Get a module by slug")
def get_module(slug: str, session: Session = Depends(get_session)) -> ModuleRead:
    return project_service.get_module_by_slug(session, slug)
