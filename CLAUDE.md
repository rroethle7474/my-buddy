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

**Phase 0 (scaffold + contract) is complete and frozen on `main`.** The four
worktrees (backend-core, claude-service, frontend-shell, mechanic-ui) branch off
`main` per COORDINATION.md §2. Endpoint bodies are stubs (501) except `/health`;
no business logic, DB tables, or migrations exist yet — those are Phase 1+.

## Regenerating the API contract

```bash
cd backend && python scripts/dump_openapi.py   # -> shared/openapi.json
cd ../frontend && npm run gen:api              # -> src/api/schema.d.ts
```
