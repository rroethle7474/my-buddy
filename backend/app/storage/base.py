"""Storage adapter interface (ARCHITECTURE.md §3/§4/§14, D3).

All object storage (progress photos) goes through this S3-style abstraction so
the volume→R2 swap is a config change, never a code change. §14: 'Storage access
goes ONLY through the adapter — no direct filesystem/R2 calls in handlers.'

Phase 0: interface only. Implementations are stubs (no real file handling).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class StoredObject:
    """Reference to a stored object. ``key`` is what gets persisted on the
    ``photos.storage_key`` column (§5)."""

    key: str
    url: str


class StorageAdapter(ABC):
    """S3-style object storage interface (volume now ▸ R2 later, D3)."""

    @abstractmethod
    def put(self, key: str, data: bytes, content_type: str) -> StoredObject:
        """Store ``data`` under ``key`` and return a reference to it."""

    @abstractmethod
    def get(self, key: str) -> bytes:
        """Return the bytes stored under ``key``."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the object stored under ``key``."""

    @abstractmethod
    def url_for(self, key: str) -> str:
        """Return a (possibly presigned) URL the client can use to read ``key``."""
