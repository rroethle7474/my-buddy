# `frontend/src/api` — the generated API contract

**`schema.d.ts` is generated, never hand-edited** (ARCHITECTURE.md §3/§14,
COORDINATION.md §6). It is produced by `openapi-typescript` from the backend's
OpenAPI schema and is committed so a CONTRACT-CHANGE shows up as a diff here.

Regenerate:

```bash
# 1) dump the OpenAPI schema from the backend (writes shared/openapi.json)
cd ../backend && python scripts/dump_openapi.py

# 2) regenerate the TypeScript types
cd ../frontend && npm run gen:api
```

Query hooks (TanStack Query) that consume these types are built in Phase 1
(frontend-shell, §12/§13) and live alongside `schema.d.ts` here.
