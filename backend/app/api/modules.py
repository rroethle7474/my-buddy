"""Modules router (§11 Modules)."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter

from ..schemas.dtos import ModuleRead
from . import not_implemented

router = APIRouter(prefix="/modules", tags=["modules"])


@router.get("", response_model=List[ModuleRead], summary="List modules")
def list_modules() -> List[ModuleRead]:
    not_implemented()


@router.get("/{slug}", response_model=ModuleRead, summary="Get a module by slug")
def get_module(slug: str) -> ModuleRead:
    not_implemented()
