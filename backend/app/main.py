"""FastAPI entrypoint (ARCHITECTURE.md §10).

Phase 0: mounts every §11 router as a stub + a real /health. The OpenAPI schema
this app emits is THE frontend contract (§3/§13) — the frontend's types are
generated from it via openapi-typescript.
"""

from __future__ import annotations

from fastapi import FastAPI

from .api import generate, health, modules, photos, projects, shop

app = FastAPI(
    title="my-buddy API",
    version="0.0.0",
    description=(
        "Personal skill-building project companion. Phase 0 scaffold: the API "
        "contract is frozen; endpoint bodies are stubs (501) except /health. "
        "Contract of record: shared/project-spec.schema.json + this OpenAPI "
        "surface (see COORDINATION.md §6)."
    ),
)

# §11 routers. Auth is at the edge (Cloudflare Access, D2) — no auth endpoints.
app.include_router(health.router)
app.include_router(modules.router)
app.include_router(projects.router)
app.include_router(shop.router)
app.include_router(photos.router)
app.include_router(generate.router)
app.include_router(generate.research_router)
