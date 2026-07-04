# `modules/mechanic` — the mechanic UI (agent D)

Renders a project's plan as the **four interactive sections** (ARCHITECTURE.md
§1 / §16.3), not the mock's placeholder document grid:

1. **Shopping cart** — consumables + running cost total (`ShoppingCartSection`)
2. **Tools** — the shop-diff buckets: owned vs. to-acquire (`ToolListSection`, §8)
3. **Tutorial** — ordered steps, per-step safety note + time + journal note
   (`TutorialSection`, §1.3/§5)
4. **Research first** — topics + learning-resource links (`ResearchSection`, §7.2)

`MechanicProject` composes them into the **1f "documents" read view** (success
banner, header, sticky section nav, safety disclaimer §16.4). All styling is in
`styles.css`, scoped under `.mech`, tokens from §16.1 (no invented values).

## Status: D1 (scaffold-ahead) — mocked data

- Data flows through **`useMechanicProject(project)`** (`hooks/`), which holds the
  hydrated project in local state and applies mutations in-memory.
- The fixture **`fixtures/doorwayPullUpBar.ts`** is a full `ProjectRead`
  (`GET /projects/{id}` shape), used until the live endpoint exists.
- Types are aliased from the generated contract in **`types.ts`** — never
  hand-write API types (COORDINATION.md §6).

## Swapping to live endpoints (D3, on `READY: projects-api`)

Only `useMechanicProject` changes — components are untouched:

- `project` ← `useQuery(['project', id], () => GET /projects/{id})`
- each mutation fn ← a TanStack `useMutation` with an optimistic update, hitting
  the matching PATCH (shapes already match §11):
  - `toggleMaterial` → `PATCH /projects/{id}/materials/{mid}` `{ checked }`
  - `toggleTool` / `setToolOwned` → `PATCH /projects/{id}/tools/{tid}` `{ checked, owned }`
  - `toggleStep` / `setStepNote` → `PATCH /projects/{id}/steps/{sid}` `{ completed, note }`

Offline mutation replay is **deferred** (TASKS): offline mutations should fail
gracefully with a "you're offline" message, not queue.

## Preview it

Dev-only harness, no shell required:

```bash
npm run dev
# open http://localhost:5173/src/modules/mechanic/dev/preview.html
```

`dev/` and everything here live entirely under `src/modules/mechanic/` (agent D's
worktree, §13) — nothing in `src/app`, `src/offline`, or `src/pwa` is touched.
