"""Local-volume storage implementation (ARCHITECTURE.md §3, D3).

Backs the ``StorageAdapter`` interface with a Hetzner volume mount for v1. A
later swap to Cloudflare R2 is a new adapter + a config change (STORAGE_BACKEND),
with no handler changes.

Phase 0: STUB ONLY. Every method raises NotImplementedError — no real file
handling is wired here (that is Phase 1, backend-core, §12/§13). Only the shape
of the adapter is frozen.
"""

from __future__ import annotations

from .base import StorageAdapter, StoredObject


class LocalVolumeStorage(StorageAdapter):
    """Stores objects on a local volume mount at ``STORAGE_LOCAL_PATH``."""

    def __init__(self, root_path: str) -> None:
        self.root_path = root_path

    def put(self, key: str, data: bytes, content_type: str) -> StoredObject:
        raise NotImplementedError("Phase 0 stub — implemented in Phase 1 (backend-core).")

    def get(self, key: str) -> bytes:
        raise NotImplementedError("Phase 0 stub — implemented in Phase 1 (backend-core).")

    def delete(self, key: str) -> None:
        raise NotImplementedError("Phase 0 stub — implemented in Phase 1 (backend-core).")

    def url_for(self, key: str) -> str:
        raise NotImplementedError("Phase 0 stub — implemented in Phase 1 (backend-core).")


def get_storage() -> StorageAdapter:
    """Factory: select the storage adapter from config (§3 / D3).

    Phase 0 returns the local stub regardless of backend; the R2 adapter arrives
    with the swap. Wired as a FastAPI dependency in Phase 1.
    """
    from ..config import settings

    return LocalVolumeStorage(settings.storage_local_path)
