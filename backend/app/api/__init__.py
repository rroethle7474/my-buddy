"""API routers (ARCHITECTURE.md §11).

Phase 0: every endpoint below has the correct path, method, and request/response
type — but the body is a stub that raises 501 Not Implemented. Only ``/health``
does real work. This freezes the OpenAPI surface (the frontend contract, §13)
without implementing any business logic (§12 Phase 0).
"""

from __future__ import annotations

from fastapi import HTTPException, status


def not_implemented() -> None:
    """Raise a uniform 501 for Phase 0 stub bodies."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Phase 0 stub - endpoint not implemented yet.",
    )
