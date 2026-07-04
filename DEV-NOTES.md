# Local dev notes

Gotchas when running the stack locally (`uvicorn` on :8000 + `vite` on :5173).
None of these affect production — see each note. (Broader docs refresh is F3.)

## Vite dev proxy: DELETE 204 occasionally surfaces as 503 in the browser

**Symptom.** A `DELETE` (e.g. removing a photo or a shop-inventory item) that the
backend answers `204 No Content` *intermittently* shows up as a `503` to a
**browser `fetch`** through the Vite dev proxy. The delete still succeeds
server-side — the row is gone.

**Cause.** The Vite dev server proxies API paths to FastAPI via `http-proxy`,
which has a long-standing race handling body-less responses (`204`/`304`) on a
**reused keep-alive** connection. Browsers pool and reuse connections
aggressively, so they occasionally land on a socket in that bad state and the
proxy answers `503`. `curl` opens a fresh connection per call and never sees it.

**Why we didn't "fix" it.** It is:
- **Benign** — the DELETE is applied; only the proxy's response to the browser is
  wrong, and the mechanic UI already treats a failed delete as an optimistic
  rollback + retry (§9), so a stray 503 self-corrects on the next load.
- **Not reproducible on demand** — 32 browser-`fetch` DELETEs through the proxy
  (12 sequential + 20 parallel) all returned 204; the race is rare.
- **Dev-only** — production serves the frontend from the **nginx sidecar**
  (deploy E1), not the Vite dev proxy, so this code path does not exist in prod.

Patching the shared `vite.config.ts` with an unverifiable `http-proxy` workaround
would risk a real regression to paper over a rare cosmetic dev artifact, so we
left it. If it ever gets annoying: hard-refresh, or restart the dev server.

## Cleaning up dev-DB test projects

Seed/demo projects accumulate in the local Postgres. Convention:

- **`id=2` (`simple-24-inch-paperback-wall-shelf`) is the canonical seed** — keep
  it. It's the handy end-to-end demo (filled materials/tools/steps/research).
- **`id=3`, `id=4`, `id=5` are disposable test projects** left by the build
  agents (phone stands, pull-up bar). They're fine to keep as demo variety, or
  remove when the dev DB gets noisy.

**Remove one test project (soft delete, matches the app).** `DELETE /projects/{id}`
sets `deleted_at`, so it disappears from every list/read but stays referentially
intact:

```bash
curl -X DELETE http://localhost:8000/projects/3   # hides id=3
```

**Full reset to a clean schema + seeds.** Drops all data and recreates the
schema with only the seeds (user `id=1` + the `mechanic` module):

```bash
cd backend && source .venv/Scripts/activate   # or activate the venv your way
alembic downgrade base && alembic upgrade head
```

Then, to regenerate a realistic demo project via the live generate→import→research
flow (needs `ANTHROPIC_API_KEY`; hits real Claude + web search):

```bash
python scripts/e2e_smoke.py                    # recreates a filled demo project
```

Note: a full reset **restarts the id sequence**, so the demo won't necessarily be
`id=2` again — update any hard-coded demo links if you rely on a specific id/slug.
