# my-buddy — agent bootstrap (Claude Code)

**Before you do anything, read both source-of-truth docs in full:**

1. [`ARCHITECTURE.md`](./ARCHITECTURE.md) — what we're building, the tech stack,
   the data model, the **project spec schema (§6)**, and the **API contract
   (§11)**. If code and this doc disagree, update the doc in the same PR.
2. [`COORDINATION.md`](./COORDINATION.md) — how the parallel build agents talk
   and stay out of each other's way (the message bus, worktree ownership §13,
   and the rules for changing contract files).

These are authoritative. Follow them exactly. **Do not reshape the contract** —
if something looks wrong, missing, or ambiguous, escalate a `QUESTION` to Ryan
(COORDINATION.md §4/§5) rather than guessing.

## The frozen contract (coordinate before changing — COORDINATION.md §6)

- `shared/project-spec.schema.json` — the project spec (§6), the cross-language
  contract of record.
- `backend/app/schemas/spec.py` — the Pydantic gate for the same spec (kept in
  sync with the JSON Schema).
- The FastAPI router signatures / OpenAPI surface (§11), dumped to
  `shared/openapi.json`.
- `frontend/src/api/schema.d.ts` — **generated** from the OpenAPI schema
  (`openapi-typescript`), never hand-edited.

Changing any of these is a `CONTRACT-CHANGE`: announce on the bus, land it as
its own small PR, everyone rebases (COORDINATION.md §5).

## Where things live (ARCHITECTURE.md §10, §13)

- `backend/` — FastAPI app. `app/api` routers (§11), `app/schemas` (spec + DTOs),
  `app/models` (SQLModel, §5), `app/claude` (§7), `app/storage` (adapter, §3),
  `alembic/` (migrations).
- `frontend/` — Vite + React + TS PWA. `src/app` (shell), `src/modules/mechanic`,
  `src/api` (generated types + query hooks), `src/offline`, `src/pwa`.
- `shared/` — the cross-language contract.

## Status

**v1 is complete and deployed (2026-07-04).** All build phases — Phase 0
(scaffold + contract), Phases 1–3 (foundation, integration, polish), and
Phase 4 (ship-it: production packaging, hardening, deploy) — are done and on
`main`. All 17 §11 endpoints are live (plus one deliberate out-of-schema byte
route, `GET /photos/{id}/content` — see §11); Alembic migrations are the schema
source of truth. The app runs in production via `SERVER-SETUP.md`
(Coolify-on-Hetzner behind Cloudflare Access — the app has **zero auth code by
design**, so Access is the security model; never add auth code).

The parallel-build worktrees and the per-phase agent staffing are **historical**
— see the bus `TASKS.md` for the full ledger. New work starts from `main`.
Dev-environment quirks and dev-DB cleanup live in `DEV-NOTES.md`. Post-v1
backlog (in order): offline mutation replay, shop-aware selection bias.

## First-time setup (per worktree)

Each worktree is its own working dir; `backend/.venv` and `frontend/node_modules`
are gitignored and **not** shared, so bootstrap them once per worktree. (The
committed contract artifacts — `shared/openapi.json`, `frontend/src/api/schema.d.ts`
— are already present.)

```bash
# backend — needs `uv` + Python >=3.11 (see backend/README.md)
cd backend && uv venv --python 3.12 && uv pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000        # after activating .venv, or `uv run uvicorn ...`

# frontend — needs Node >=20 (see frontend/README.md)
cd frontend && npm install && npm run dev
```

Or bring up the whole stack (app + Postgres) with `docker-compose up` from the
repo root (Docker Desktop must be running). Production uses
`docker-compose.prod.yml` — see `SERVER-SETUP.md`.

Dev tips: run uvicorn with `--timeout-graceful-shutdown 3` (keep-alive sockets
otherwise hang Ctrl+C), and avoid bare `uv run` (it syncs away the `[dev]`
extras and regenerates the gitignored `uv.lock`) — activate the venv or use
`uv run --no-sync`. More in `DEV-NOTES.md`.

## Regenerating the API contract

```bash
cd backend && python scripts/dump_openapi.py   # -> shared/openapi.json
cd ../frontend && npm run gen:api              # -> src/api/schema.d.ts
```
