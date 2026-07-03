# my-buddy backend

FastAPI app (ARCHITECTURE.md §3). **Phase 0 scaffold:** `/health` is live; all
17 §11 endpoints are stubbed (`501 Not Implemented`); no DB tables, migrations,
or business logic yet (those are Phase 1+, §12/§13).

## First-time setup (per worktree)

`.venv/` is gitignored and **not** shared across worktrees — bootstrap it once
in each. Needs [`uv`](https://docs.astral.sh/uv/) and Python ≥ 3.11.

```bash
cd backend
uv venv --python 3.12          # creates ./.venv
uv pip install -e ".[dev]"     # installs the app + ruff
```

## Run

```bash
# activate the venv first:
#   PowerShell:  .venv\Scripts\Activate.ps1
#   bash:        source .venv/Scripts/activate   (Windows)  |  source .venv/bin/activate (*nix)
uvicorn app.main:app --reload --port 8000
```

…or, without activating, `uv run uvicorn app.main:app --reload --port 8000`.

Or bring up the whole stack (app + Postgres) with **`docker-compose up`** from the
repo root once Docker is available.

Check it:

```bash
curl http://localhost:8000/health      # -> {"status":"ok"}
# interactive docs: http://localhost:8000/docs
```

## Regenerate the API contract (after any router/DTO change)

The OpenAPI surface is the frontend contract (§3/§13). A change to it is a
`CONTRACT-CHANGE` (COORDINATION.md §5/§6) and must ship the regenerated
artifacts:

```bash
python scripts/dump_openapi.py         # -> ../shared/openapi.json
cd ../frontend && npm run gen:api      # -> src/api/schema.d.ts
```

## Lint / format

```bash
ruff check .
ruff format .
```

## Layout (§10)

- `app/main.py` — entrypoint; mounts every §11 router + `/health`.
- `app/api/` — routers (stubs in Phase 0). `app/schemas/` — the spec (§6) + DTOs.
- `app/models/` — SQLModel tables (§5), **empty until Phase 1**.
- `app/claude/` — Claude client/prompts/flows (§7), **empty until Phase 2**.
- `app/storage/` — S3-style adapter interface + local-volume stub (§3, D3).
- `app/db.py` — engine/session (lazy; no tables). `alembic/` — migrations (Phase 1).
