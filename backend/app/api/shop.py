"""Shop inventory router — "My Shop" (§11 Shop inventory, §8)."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, status

from ..schemas.dtos import ShopInventoryCreate, ShopInventoryRead
from . import not_implemented

router = APIRouter(prefix="/shop", tags=["shop"])


@router.get("/inventory", response_model=List[ShopInventoryRead], summary="List My Shop")
def list_inventory() -> List[ShopInventoryRead]:
    not_implemented()


@router.post(
    "/inventory",
    response_model=ShopInventoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Add a tool to My Shop",
)
def add_inventory(body: ShopInventoryCreate) -> ShopInventoryRead:
    not_implemented()


@router.delete(
    "/inventory/{inventory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a tool from My Shop",
)
def delete_inventory(inventory_id: int) -> None:
    not_implemented()
