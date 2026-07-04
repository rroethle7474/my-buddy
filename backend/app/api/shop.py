"""Shop inventory router — "My Shop" (§11 Shop inventory, §8)."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from ..db import get_session
from ..schemas.dtos import ShopInventoryCreate, ShopInventoryRead
from ..services import projects as project_service

router = APIRouter(prefix="/shop", tags=["shop"])


@router.get("/inventory", response_model=List[ShopInventoryRead], summary="List My Shop")
def list_inventory(session: Session = Depends(get_session)) -> List[ShopInventoryRead]:
    return project_service.list_shop_inventory(session)


@router.post(
    "/inventory",
    response_model=ShopInventoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a tool to My Shop",
)
def add_inventory(
    body: ShopInventoryCreate,
    session: Session = Depends(get_session),
) -> ShopInventoryRead:
    return project_service.create_shop_inventory(session, body)


@router.delete(
    "/inventory/{inventory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a tool from My Shop",
)
def delete_inventory(
    inventory_id: int,
    session: Session = Depends(get_session),
) -> None:
    project_service.delete_shop_inventory(session, inventory_id)
