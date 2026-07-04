"""Tests for the out-of-schema ``GET /photos/{id}/content`` byte route (D4).

Serving stays behind the storage adapter (§3); the content type is inferred from
the storage-key suffix (no ``content_type`` column). DB and storage are faked at
their dependency boundaries — no live Postgres/volume needed.

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import app
from app.models import Photo as PhotoRow
from app.storage import get_storage


class _FakePhotoSession:
    """Minimal Session stand-in exposing the one call the route makes."""

    def __init__(self, photo: PhotoRow | None = None) -> None:
        self._photo = photo

    def get(self, _model, _pk):  # mirrors Session.get(Model, id)
        return self._photo


class _FakeStorage:
    """In-memory StorageAdapter: get() raises FileNotFoundError for missing keys."""

    def __init__(self, blobs: dict[str, bytes] | None = None) -> None:
        self._blobs = dict(blobs or {})

    def put(self, key, data, content_type):  # noqa: ARG002 - unused here
        self._blobs[key] = data

    def get(self, key):
        if key not in self._blobs:
            raise FileNotFoundError(key)
        return self._blobs[key]

    def delete(self, key):
        self._blobs.pop(key, None)

    def url_for(self, key):
        return f"/storage/{key}"


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 24


def _photo(storage_key: str = "projects/2/photos/abc123.png") -> PhotoRow:
    return PhotoRow(
        id=1,
        project_id=2,
        step_id=None,
        storage_key=storage_key,
        caption="a caption",
        created_at=datetime.now(timezone.utc),
    )


class PhotoContentRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = _FakePhotoSession(photo=_photo())
        self.storage = _FakeStorage({"projects/2/photos/abc123.png": PNG_BYTES})
        app.dependency_overrides[get_session] = lambda: self.session
        app.dependency_overrides[get_storage] = lambda: self.storage
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_serves_bytes_with_inferred_content_type(self) -> None:
        r = self.client.get("/photos/1/content")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["content-type"], "image/png")
        self.assertEqual(r.content, PNG_BYTES)

    def test_missing_row_returns_404(self) -> None:
        self.session._photo = None
        r = self.client.get("/photos/1/content")
        self.assertEqual(r.status_code, 404)

    def test_missing_object_returns_404(self) -> None:
        self.storage._blobs.clear()
        r = self.client.get("/photos/1/content")
        self.assertEqual(r.status_code, 404)

    def test_unknown_suffix_falls_back_to_octet_stream(self) -> None:
        self.session._photo = _photo(storage_key="projects/2/photos/blob.bin")
        self.storage._blobs = {"projects/2/photos/blob.bin": PNG_BYTES}
        r = self.client.get("/photos/1/content")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["content-type"], "application/octet-stream")

    def test_route_is_not_in_openapi_schema(self) -> None:
        # include_in_schema=False → the byte route must NOT appear in the frozen
        # §11 surface, so the 17-path OpenAPI invariant still holds.
        paths = self.client.get("/openapi.json").json()["paths"]
        self.assertNotIn("/photos/{photo_id}/content", paths)


if __name__ == "__main__":
    unittest.main()
