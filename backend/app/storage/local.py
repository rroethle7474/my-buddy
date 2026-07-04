"""Local-volume storage implementation (ARCHITECTURE.md §3, D3).

Backs the ``StorageAdapter`` interface with a Hetzner volume mount for v1. A
later swap to Cloudflare R2 is a new adapter + a config change (STORAGE_BACKEND),
with no handler changes.

Keys are S3-style POSIX paths. The implementation validates every key resolves
under the configured root before it touches the filesystem.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from urllib.parse import quote

from .base import StorageAdapter, StoredObject


class LocalVolumeStorage(StorageAdapter):
    """Stores objects on a local volume mount at ``STORAGE_LOCAL_PATH``."""

    def __init__(self, root_path: str) -> None:
        self.root_path = Path(root_path).resolve()

    def put(self, key: str, data: bytes, content_type: str) -> StoredObject:
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return StoredObject(key=key, url=self.url_for(key))

    def get(self, key: str) -> bytes:
        path = self._path_for(key)
        if not path.exists():
            raise FileNotFoundError(key)
        return path.read_bytes()

    def delete(self, key: str) -> None:
        path = self._path_for(key)
        if path.exists():
            path.unlink()

    def url_for(self, key: str) -> str:
        return f"/storage/{quote(key, safe='/')}"

    def _path_for(self, key: str) -> Path:
        parts = PurePosixPath(key).parts
        if not parts or any(part in {"", ".", ".."} for part in parts):
            raise ValueError("Storage key must be a relative POSIX path.")

        path = self.root_path.joinpath(*parts).resolve()
        try:
            path.relative_to(self.root_path)
        except ValueError as exc:
            raise ValueError("Storage key escapes the configured storage root.") from exc
        return path


def get_storage() -> StorageAdapter:
    """Factory: select the storage adapter from config (§3 / D3)."""
    from ..config import settings

    if settings.storage_backend != "local":
        raise NotImplementedError(f"Unsupported storage backend: {settings.storage_backend}")
    return LocalVolumeStorage(settings.storage_local_path)
