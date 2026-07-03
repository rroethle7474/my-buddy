# my-buddy frontend

Vite + React + TypeScript PWA (ARCHITECTURE.md §3). **Phase 0 scaffold: an empty
shell that boots.** Screens, routing, the module registry, offline sync, and the
mechanic module are built in later phases (§12/§13).

## Develop

```bash
npm install
npm run dev          # http://localhost:5173 (proxies /api paths to the backend on :8000)
```

Run the backend separately (see repo root `docker-compose.yml` or
`backend/`). The browser only ever talks to the FastAPI app (§4).

## API types are generated, never hand-written (§14)

`src/api/schema.d.ts` is generated from the backend's OpenAPI schema:

```bash
cd ../backend && python scripts/dump_openapi.py   # -> ../shared/openapi.json
cd ../frontend && npm run gen:api                 # -> src/api/schema.d.ts (committed)
```

Changing it is a coordinated CONTRACT-CHANGE (COORDINATION.md §5/§6).
