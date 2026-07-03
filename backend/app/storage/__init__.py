"""Storage adapter (§3/§14): S3-style interface + local-volume stub (D3)."""

from .base import StorageAdapter, StoredObject
from .local import LocalVolumeStorage, get_storage

__all__ = ["StorageAdapter", "StoredObject", "LocalVolumeStorage", "get_storage"]
