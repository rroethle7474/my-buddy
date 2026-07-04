# `modules/mechanic` — the mechanic UI (agent D)

> **Status:** D1 (four sections on a fixture) and D5 (PDF export) are done.
> D2/D3/D4 wire live endpoints — see the swap notes below.

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

## Data flow — live (D3)

- The docs screen loads the project via **`useProjectBySlug`** (`api/projects.ts`),
  which resolves the URL slug → id and caches it under `['project', module, slug]`.
- **`useMechanicProject(project, { moduleSlug, projectSlug })`** (`hooks/`) is the
  seam: it holds the project for rendering and, in live mode, applies each mutation
  **optimistically** to both local state and that query-cache entry, then PATCHes
  the matching §11 endpoint and reconciles the returned entity by id. On failure it
  rolls back the one changed entity and shows a transient toast (`.mech-toast`) —
  the graceful offline/error path (§9). Components are untouched (same
  `MechanicProjectApi`):
  - `toggleMaterial` → `PATCH /projects/{id}/materials/{mid}` `{ checked }`
  - `toggleTool` / `setToolOwned` → `PATCH /projects/{id}/tools/{tid}` `{ checked }` / `{ owned }`
  - `toggleStep` / `setStepNote` → `PATCH /projects/{id}/steps/{sid}` `{ completed }` / `{ note }` (note saves on blur)
  - `saveRetrospective` → `PATCH /projects/{id}/retrospective` (upsert; the
    `RetrospectiveSection` form, D4) — returns a promise so the form shows its own
    pending/saved state; on success the cached `project.retrospective` updates.
  - `uploadPhoto` / `deletePhoto` → `POST /projects/{id}/photos` (multipart) /
    `DELETE /photos/{id}` (the `PhotosSection` gallery, D4). Upload appends the
    returned `PhotoRead`; delete is optimistic with rollback. Photo **bytes** are
    served by the out-of-schema byte route `GET /photos/{id}/content` (see
    `api/photos.ts` `photoSrc`) — that route is deliberately not in the generated
    contract (ARCHITECTURE.md §11), so we build the `<img>` src by id.
- Called **without** `options` (the fixture preview), the hook stays local-only —
  no PATCH, no cache writes — so the read view is demoable offline against
  **`fixtures/doorwayPullUpBar.ts`**.
- Types are aliased from the generated contract in **`types.ts`** — never
  hand-write API types (COORDINATION.md §6).

Offline mutation *replay* is **deferred** (TASKS): offline mutations fail
gracefully (rollback + toast), they do not queue. Marking a tool "I have this now"
currently flips its bucket via the tool PATCH; also adding it to My Shop inventory
(`POST /shop/inventory`, §8) is a follow-up.

## PDF export — "Download all" (D5)

Client-side print (v1): "Download all" (header button + the plan-ready banner)
calls `window.print()` → the user picks **Save as PDF**. The `@media print`
block in `styles.css` produces the clean copy — strips interactive chrome (nav,
banner, buttons), turns the journal textareas into static text, reveals each
research link's URL for paper copies, keeps section colors, avoids awkward page
breaks, and keeps the **§16.4 safety disclaimer**. `@media print` (not a
`beforeprint` class) so it also works on iOS Safari with no JS. The shell can
inject its own `onDownloadAll`; otherwise the default sets the document title to
the project name so the PDF filename is sensible.

## Preview it

Dev-only harness, no shell required:

```bash
npm run dev
# open http://localhost:5173/src/modules/mechanic/dev/preview.html
```

`dev/` and everything here live entirely under `src/modules/mechanic/` (agent D's
worktree, §13) — nothing in `src/app`, `src/offline`, or `src/pwa` is touched.
