# my-buddy — Architecture & Scaffold Spec

**Audience:** Claude Code agents building this project in parallel worktrees.
**Status:** Source of truth. If code and this doc disagree, update this doc in the same PR.
**Owner:** Ryan.

---

## 1. What we're building

`my-buddy` is a personal, self-hosted web app that helps its single user pick and complete skill-building projects. It's a **shell** with pluggable **modules**; the first module is **`mechanic`** (hands-on DIY builds to become more mechanically inclined).

For any given project, `mechanic` renders four things off one structured spec:

1. **Shopping cart** — consumables to buy (wood, screws, glue, finish), with a running cost total.
2. **Tool list** — split into *you already own* vs. *you need to acquire*, computed by diffing against a persistent "My Shop" inventory.
3. **Tutorial** — ordered, novice-level steps with per-step safety notes and time estimates.
4. **Research-first** — topics to review before starting, each with links to learning resources (videos/articles), populated via web search.

On top of that, the app is a **learning journal**: per-step notes ("where I got stuck"), progress photos, and an end-of-project retrospective. It must be usable **on a phone in a lumber aisle with no signal** — so it ships as an installable, offline-capable PWA.

→ **Visual design language and the full screen flow (mocks 1a–1f) are in §16.**

---

## 2. Decision points — confirm before building

These are the only open calls. Everything else below is decided. Ryan: sign off (or override) these first, then agents proceed.

| # | Decision | Recommendation | Alternative |
|---|----------|----------------|-------------|
| D1 | **Backend language** | **✓ DECIDED: FastAPI (Python)** — locked. Lightweight, first-class Anthropic SDK, matches Ryan's personal-project stack | ~~.NET minimal API~~ — not chosen |
| D2 | **Auth** | **✓ DECIDED: Cloudflare Access at the edge** — zero auth code, email-gated, protects the whole app; app assumes requests are authenticated. Local dev runs open. | ~~App-level single-user login (JWT cookie)~~ — not chosen |
| D3 | **Image storage for v1** | **✓ DECIDED: Hetzner volume mount** behind an S3-style abstraction, so a later swap to Cloudflare R2 (free tier, no egress fees) is a config change | ~~Go straight to R2 now~~ — not chosen |
| D4 | **In-app Claude generation in v1?** | **✓ DECIDED: Yes — and now central.** The approved mocks (1d–1f, §16) are built entirely around the generate-via-chat flow, so generation is the **primary v1 experience**, not a deferred add-on. The import path (§7, §11) stays as a seed/test seam. | ~~Import-only for v1~~ — superseded by the mocks |

**Status:** All §2 decisions are closed (Ryan, 2026-07-03): D1 FastAPI · D2 Cloudflare Access · D3 volume-behind-adapter · D4 generation-in-v1. Stack confirmed (React / PostgreSQL, §3); the Claude Design mocks are folded in — see **§16 (Design & UI)**, which also revises the generation flow (§7.1) and endpoints (§11) to match the approved chat UX. Per-phase task decomposition, v1 scope, and agent assignments live in the bus `TASKS.md` (COORDINATION.md §3).

---

## 3. Tech stack (decided)

**Frontend**
- React + **Vite** + **TypeScript**
- PWA via **`vite-plugin-pwa`** (Workbox) — app-shell precache + runtime caching of the active project
- Server state: **TanStack Query**; offline mutations queued in **IndexedDB** and replayed on reconnect
- Types are **generated from the backend's OpenAPI schema** via `openapi-typescript` (do not hand-write API types)

**Backend** (per D1: FastAPI)
- **FastAPI** + **SQLModel** (Pydantic-native models that double as schemas) + **Alembic** migrations
- **Anthropic Python SDK** for Claude calls, **proxied** — the API key never reaches the client
- OpenAPI schema is auto-generated and is **the frontend contract**

**Data**
- **PostgreSQL** (Coolify one-click)
- Object storage: **Hetzner volume** for v1 via an S3-style abstraction (per D3)

**Infra**
- **Coolify on Hetzner**, **Cloudflare** DNS + proxy in front (see `SERVER-SETUP.md`)

---

## 4. System shape

```
   Phone / Laptop (PWA, offline-capable)
        │  HTTPS
        ▼
   Cloudflare (DNS + proxy + Access auth wall)   ← D2
        │
        ▼
   Coolify on Hetzner
   ┌─────────────────────────────────────────┐
   │  FastAPI app                             │
   │   ├─ REST API  (OpenAPI = FE contract)   │
   │   ├─ Claude service (proxied SDK calls)  │
   │   └─ Storage adapter (volume ▸ R2 later) │
   │                                          │
   │  PostgreSQL   (specs, state, learnings)  │
   │  Volume       (progress photos)          │
   └─────────────────────────────────────────┘
```

**Rule:** the browser never talks to the Anthropic API or the DB directly. Everything goes through FastAPI.

---

## 5. Data model

Separation of concerns: the **spec** (§6) is the plan and is treated as write-once. Runtime **state** (checked/completed/notes) lives in normalized tables so it's cheap to mutate from a phone. Read-only reference data (research resources) is stored as JSONB.

| Table | Key fields | Notes |
|-------|-----------|-------|
| `users` | id, email, created_at | Single user for v1; still needed for ownership + shop scope |
| `modules` | id, slug, name, description | Seed with `mechanic`. Future modules are rows, not code forks |
| `projects` | id, user_id, module_id, name, **slug**, skill_focus[], difficulty, time_budget, estimated_cost_usd, summary, workspace_required, status, spec_version, created_at | `slug` powers URLs (`/my-mechanic/doorway-pull-up-bar/…`, §16). `status`: `planning \| active \| complete` |
| `materials` | id, project_id, name, quantity, unit, est_cost_usd, where_to_find, notes, **checked** | Mutable: `checked` toggled from shopping cart |
| `tools` | id, project_id, name, essential, est_cost_usd, notes, alternatives, **owned**, **acquire**, **checked** | `owned`/`acquire` set by the shop diff (§8) at import; `checked` for use in-cart |
| `steps` | id, project_id, order, title, instruction, safety_note, est_time_minutes, tools_used[], materials_used[], **completed**, **note** | `note` = per-step learning ("where I got stuck") |
| `research_topics` | id, project_id, topic, why, **resources (JSONB)** | `resources`: `[{title, url, type}]`, populated via web search |
| `photos` | id, project_id, step_id (nullable), storage_key, caption, created_at | `step_id` null ⇒ project-level photo |
| `shop_inventory` | id, user_id, tool_name, category, notes | **"My Shop"** — persistent across projects; the diff source |
| `retrospectives` | id, project_id (unique), what_went_well, what_i_would_do_differently, skills_practiced[], created_at | One per project |

---

## 6. The project spec schema (the linchpin)

Both ingestion paths (import from a Cowork/chat brainstorm, and in-app Claude generation) **produce this exact shape**. Every UI section renders off it. Version it from day one.

```jsonc
{
  "schema_version": "1.0",
  "project": {
    "name": "Wall-mounted pegboard tool organizer",
    "module": "mechanic",
    "skill_focus": ["measuring", "drilling", "wall anchoring"],
    "difficulty": "beginner",            // beginner | handy | pro  (user-facing labels from setup, §16 / mock 1d)
    "time_budget": "afternoon",          // afternoon | weekend | multi-weekend
    "estimated_cost_usd": 45,
    "summary": "One-paragraph description of the finished piece and what you'll learn.",
    "workspace_required": "A wall, a drill, floor space to lay out the board."
  },
  "materials": [
    {
      "name": "Pegboard panel, 2ft x 4ft",
      "quantity": 1,
      "unit": "panel",
      "est_cost_usd": 20,
      "where_to_find": "Hardware store, panel/plywood aisle",
      "notes": "Pre-cut sizes are common; ask for a cut if larger."
    }
  ],
  "tools": [
    {
      "name": "Power drill",
      "essential": true,
      "est_cost_usd": 0,
      "notes": "For pilot holes and driving anchors.",
      "alternatives": "Manual screwdriver works but is slow for anchors."
    }
  ],
  "steps": [
    {
      "order": 1,
      "title": "Mark the mounting points",
      "instruction": "Detailed novice-level instruction. Assume no prior knowledge.",
      "safety_note": "Check for wiring/pipes before drilling into a wall.",
      "est_time_minutes": 15,
      "tools_used": ["Tape measure", "Pencil", "Level"],
      "materials_used": []
    }
  ],
  "research_topics": [
    {
      "topic": "How to find a wall stud",
      "why": "Anchoring into a stud vs. drywall changes which fasteners you use.",
      "resources": [
        { "title": "Placeholder — filled by web search", "url": "https://…", "type": "video" }
      ]
    }
  ]
}
```

**Notes for agents**
- `resources` may arrive empty from generation; the research web-search pass (§7.2) fills them. Import path may also arrive empty and be enriched on demand.
- Runtime fields (`checked`, `completed`, `note`, `owned`, `acquire`) are **not** in the spec. They're created in the DB when a spec is ingested.
- Validate every ingested spec against this schema (Pydantic model) before persisting. Reject with a clear error on mismatch.

---

## 7. Claude integration

All Claude calls run **server-side** through the Anthropic SDK. Two flows.

### 7.1 Project generation (the generate-via-chat flow)

This is the app's centerpiece (mocks 1d → 1e → 1f). It's a **bounded conversation** that ends by emitting a spec — not open-ended chat.

**Setup (mock 1d).** The user gives a short free-text description of what they want to build (or taps an idea chip), plus a **skill level** (Beginner / Handy / Pro) and a **budget band** (Under $30 / $30–75 / $75+). These are the generation constraints. `POST /generate/sessions` starts a session with this payload and returns a session id + the agent's opening message.

**Chat (mock 1e).** A stateful loop: `POST /generate/sessions/{id}/messages` sends a user turn and returns the agent's reply. The agent clarifies the specifics it needs (dimensions, what's on hand, constraints), then proposes an approach. The conversation is **bounded** — a handful of turns with a rough progress sense ("Design step · 3 of 5"), not an open thread. Two entry behaviors share this one surface:
- **User arrives with a project** (typed it or picked a chip) → the agent clarifies *that* project directly.
- **User is vague / "surprise me"** → the agent's first move is to propose **2–3 candidate projects** (capped at 3) at the chosen skill level; the user picks, then clarifies. *(This is the old candidate-selection step, folded into the chat instead of a separate screen.)*

**Finalize (mock 1e → 1f).** When the agent signals it has enough ("✓ Ready to generate documents"), `POST /generate/sessions/{id}/finalize` returns the full **spec (§6)** as strict JSON. The client commits it via `POST /projects` (which runs the shop diff, §8) and routes to the rendered documents (1f).

**Conversation state** is keyed by session id server-side (or passed back each turn) — the Anthropic API is stateless, so the full history goes into every call.

**Structured output:** only the **finalize** call returns JSON — instruct Claude to return **only** valid JSON, no prose, no fences; parse defensively (strip stray fences, `try/parse`, re-request on failure); a Pydantic model is the validation gate. Chat turns are natural language.

### 7.2 Research resource lookup

Given a spec's `research_topics`, run a pass that uses the **web search tool** to find one or two solid learning resources per topic (prefer short how-to videos and reputable guides) and fills each topic's `resources[]`.

- Runs as part of the create-project flow — `finalize` returns `resources: []` (fast, deterministic); the client fires `POST /projects/{id}/research/refresh` immediately after committing the spec via `POST /projects`, showing a loading state on the research section. Re-runnable on demand via the same endpoint. *(Decided 2026-07-04; supersedes the earlier "at generation time" wording.)*
- **Resilience (decided 2026-07-04):** topics are searched in **pair chunks** with per-chunk tolerance — a failed chunk loses only its pair; partial fills persist and return 200 (502 only if every chunk fails). Writes are **non-destructive** (a topic is overwritten only when the pass found resources for it), every search call runs under explicit timeouts with SDK retries disabled, and the client auto-fires the refresh **only once, on the just-created visit** — anything else is an explicit user action, so page loads never silently spend web searches.
- This is the **only** place external web lookup is used. We do **not** scrape retailer sites for project ideas or materials — materials are described generically ("one 2×4×8 pine stud, lumber aisle").

### 7.3 Prompt guardrails (both flows)
- Audience is always **novice**: assume zero prior knowledge, name every tool, include a safety note per step.
- Bias toward **common materials** and a **modest home/family shop** — no specialty machinery. If a project needs an uncommon tool, prefer an alternative or list it explicitly in the acquire bucket with a cheap option.
- Keep prompt templates in one module (`app/claude/prompts.py` or equivalent) so they're versioned and easy to tune.

---

## 8. "My Shop" diff logic

When a spec is ingested (`POST /projects`, either path):

1. For each `tools[]` entry, compare against the user's `shop_inventory` (case/fuzzy-normalized name match).
2. Present → `owned = true`, `acquire = false`. Absent → `owned = false`, `acquire = true`.
3. The tool list UI renders three buckets: **consumables** (that's the shopping cart, from `materials`), **owned tools** (auto-checked), **tools to acquire** (with cost).
4. When the user acquires a tool, `POST /shop/inventory` adds it — future projects then see it as owned.

**Bonus behavior (nice-to-have, not blocking):** project *selection* can bias toward what's already owned, so early projects aren't gated on buying gear.

---

## 9. Offline / PWA behavior

- **Installable** PWA (manifest + icons); app-shell precached via Workbox.
- Opening a project caches its full payload (spec + current state) so it's readable offline.
- **Mutations while offline** (toggling a shopping item, completing a step, writing a note) are queued in IndexedDB and **replayed on reconnect**. Use last-write-wins; single user so conflicts are rare.
- Photos captured offline queue their upload and flush when back online.
- If D2 = Cloudflare Access: cached reads work offline fine; queued mutations replay once the session re-authenticates. Note this in the FE so a 401-after-reconnect triggers a re-auth + replay, not data loss.

---

## 10. Repo structure (Phase 0 scaffold — the immediate task)

Monorepo. Scaffold this first, wire the contract, then parallelize.

```
my-buddy/
├─ ARCHITECTURE.md            # this doc
├─ SERVER-SETUP.md            # Ryan's infra runbook
├─ docker-compose.yml         # local dev: app + postgres
├─ backend/
│  ├─ app/
│  │  ├─ main.py              # FastAPI entrypoint
│  │  ├─ models/              # SQLModel tables (§5)
│  │  ├─ schemas/             # Pydantic: spec (§6) + API DTOs
│  │  ├─ api/                 # routers (§11)
│  │  ├─ claude/              # SDK client, prompts, generation + research flows
│  │  ├─ storage/             # S3-style adapter (volume now ▸ R2 later)
│  │  └─ db.py                # session/engine
│  ├─ alembic/                # migrations
│  └─ pyproject.toml
├─ frontend/
│  ├─ src/
│  │  ├─ app/                 # my-buddy shell + routing + module registry
│  │  ├─ modules/mechanic/    # mechanic UI (cart, tools, tutorial, research, journal)
│  │  ├─ api/                 # generated OpenAPI types + query hooks
│  │  ├─ offline/             # IndexedDB queue + sync
│  │  └─ pwa/                 # manifest, service worker registration
│  └─ package.json
└─ shared/
   └─ project-spec.schema.json   # §6 as JSON Schema — the cross-language contract
```

**`shared/project-spec.schema.json` is the contract of record.** Backend Pydantic model and any FE validation both derive from it. Changing it is a coordinated change (§13).

---

## 11. API contract (REST)

Auth: if D2 = Cloudflare Access, there are **no** auth endpoints — the edge handles it and the app trusts the request. If D2 = app-level, add `POST /auth/login` (JWT cookie).

**Modules**
- `GET /modules` · `GET /modules/{slug}`

**Projects**
- `GET /projects?module=&status=` — list
- `POST /projects` — **import path**: accepts a full spec (§6); validates, persists, **runs shop diff** (§8), returns hydrated project
- `GET /projects/{id}` — full hydrated project (spec + state + research + photos)
- `PATCH /projects/{id}` — update `status`
- `DELETE /projects/{id}` — soft delete preferred

**Item state (mutations designed to be offline-queued)**
- `PATCH /projects/{id}/materials/{mid}` — toggle `checked`
- `PATCH /projects/{id}/tools/{tid}` — toggle `checked` / mark owned
- `PATCH /projects/{id}/steps/{sid}` — toggle `completed`, set `note`
- `PATCH /projects/{id}/retrospective` — upsert retrospective

**Shop inventory ("My Shop")**
- `GET /shop/inventory` · `POST /shop/inventory` · `DELETE /shop/inventory/{id}`

**Photos**
- `POST /projects/{id}/photos` (multipart; optional `step_id`) · `GET /projects/{id}/photos` · `DELETE /photos/{id}`
- `GET /photos/{id}/content` — **out-of-schema** byte route (`include_in_schema=False`, decided 2026-07-04). Serves a photo's bytes for the client's `<img>` src, streaming via the storage adapter (§3) so an R2/presigned-URL swap stays a config change; content type is inferred from the storage-key suffix. Deliberately excluded from the OpenAPI surface so the frozen §11 contract / generated types are unchanged. *(Added in the mechanic-ui worktree as a cross-ownership exception since backend-core was closed.)*

**Claude — generate-via-chat (§7.1, mocks 1d–1f)**
- `POST /generate/sessions` — start a session from the setup payload `{ description, skill_level, budget_band }` → `{ session_id, agent_message }`
- `POST /generate/sessions/{id}/messages` — one user turn → agent reply (may include 2–3 candidate proposals for vague input)
- `POST /generate/sessions/{id}/finalize` — emit the full spec (§6) as strict JSON
- `POST /projects/{id}/research/refresh` — re-populate `resources[]` via web search

---

## 12. Build phases

> **Status (2026-07-04): the build is complete and v1 is deployed.** Everything
> below shipped, in a slightly different decomposition than planned — the
> as-built ledger (per-task rows, verification notes, decisions) is the bus
> `TASKS.md`. A "Phase 4 — ship it" (production packaging + `SERVER-SETUP.md`
> + hardening) followed Phase 3 and is also done. Two planned Phase-3 items
> moved to the post-v1 backlog by decision: offline mutation replay and
> shop-aware project selection.

Phase 0 is shared/blocking. After it, the columns run in parallel (§13).

- **Phase 0 — Scaffold + contract (blocking).** Repo layout (§10), `docker-compose` (app + Postgres), the spec schema (§6) as JSON Schema + Pydantic model, empty routers matching §11, OpenAPI emitting, `openapi-typescript` wired on the FE. *Nothing real works yet, but the contract is frozen.*
- **Phase 1 — Deployable core.**
  - *Backend:* data model + migrations + CRUD + storage adapter + **import path** (`POST /projects` incl. shop diff).
  - *Frontend:* my-buddy shell + routing + PWA install + offline caching of a project.
  - *Exit:* import a hand-written spec, render all four sections, toggle checkboxes offline. **This is the first thing worth deploying to Hetzner.**
- **Phase 2 — Mechanic depth + generation.**
  - *Frontend:* full mechanic module — three-bucket tool list, tutorial with per-step notes, research section, journal, photos.
  - *Backend/Claude:* generation flow (§7.1) + research lookup (§7.2).
  - *Exit:* generate a project in-app end to end, or import; both land as identical specs.
- **Phase 3 — Polish.** Offline mutation replay hardening, retrospective, photo capture/upload flush, shop-aware project selection, error states.

---

## 13. Working in parallel (worktree boundaries)

> **Status (2026-07-04): historical.** The parallel build is finished and the
> worktrees are retired; new work starts from `main`. The Phase-4 staffing
> (deploy + polish agents) superseded this table for the ship-it phase — see
> the bus `TASKS.md`. The **contract-file coordination rules below remain in
> force** for any future work.

Map agents to worktrees so they don't collide. The **contract files** below are shared; touching them requires coordination (announce on the message queue, land as its own PR, others rebase).

| Worktree / agent | Owns | Depends on |
|------------------|------|-----------|
| **A — backend-core** | `backend/app/models`, `api`, `storage`, `db`, `alembic` | contract |
| **B — claude-service** | `backend/app/claude/*`, `/generate/*`, research refresh | contract, A's models |
| **C — frontend-shell** | `frontend/src/app`, `offline`, `pwa` | contract (generated types) |
| **D — mechanic-ui** | `frontend/src/modules/mechanic/*` | contract, C's shell, A's endpoints |

**Contract files (coordinate before changing):**
- `shared/project-spec.schema.json` (§6)
- The FastAPI router signatures / OpenAPI surface (§11)
- The generated `frontend/src/api` types (regenerated from OpenAPI — never hand-edited)

As long as those hold steady, A/B/C/D proceed independently. **The message-bus mechanics — bus layout, message format, and the coordination rules — live in `COORDINATION.md`.** In short: the queue is for "I'm about to change the contract" and "endpoint X is ready to integrate against."

---

## 14. Conventions (keep parallel agents consistent)

- **API types are generated**, never hand-written (`openapi-typescript` off the live schema).
- Spec validation is **centralized** in one Pydantic model; all ingestion goes through it.
- Claude prompts live in **one module**, versioned; no inline prompt strings scattered around.
- Mutation endpoints are **idempotent-friendly** (safe to replay) to support offline sync.
- Storage access goes **only** through the adapter — no direct filesystem/R2 calls in handlers.
- Money is stored as integer cents or `Decimal`, not float.
- No secrets in the repo; config via env (see `SERVER-SETUP.md`).

---

## 15. Out of scope for v1 / future

- Multi-user / sharing (schema already scopes by `user_id`, so it's reachable later).
- Additional modules beyond `mechanic` — but the shell + module registry must make adding one a matter of a new `modules` row + a new `frontend/src/modules/<name>` folder, **not** a fork. That reuse is the whole point of `my-buddy`.
- Retailer price/SKU integration — deliberately avoided; materials stay generic.

---

## 16. Design & UI

Direction comes from the Claude Design mocks (`design/mocks.html` — the visual reference kept in the repo; the raw Claude Design export is cleaned of tool markup before it lands there). Six screens: **1a Homepage — Spotlight** ✓ *chosen*, 1b Homepage — Split *(alternative, not chosen)*, 1c My Mechanic module, 1d New Project Setup, 1e Chat with Agent, 1f Generated Documents. Every screen is drawn at **desktop and mobile** — the mobile frames are the source of truth for the PWA layout.

### 16.1 Design language (tokens)

The palette is lifted from the "Buddy" mascot (16.4) — a warm-neutral canvas with the doll's colors as accents. That subject-grounding is deliberate: it keeps the app off the generic cream/terracotta AI-default look. Agents building UI derive every color and type choice from this set; don't invent new ones.

**Color**
- Canvas / surfaces: `#ffffff`, warm off-whites `#f7f7f3` `#f5f5f1` `#f0f0eb` `#eaeae4`
- Borders / dividers: `#e6e6e0` `#e4e4de` `#e0e0d9`
- Ink: `#1b1b19` (primary), `#141414` (max); muted `#54544e` `#7a7a72` `#83837b` `#8a8a82`; faint `#b4b4ac` `#c4c4bc`
- **Red `#de3b2c`** — primary action (buttons). Tint `#fbecea`, hover `#e5675c`, focus ring `0 0 0 4px #fbecea`. Red buttons carry a red glow: `0 10px 22px -10px rgba(222,59,44,.7)`
- **Blue `#2e7cc2`** — module accent, links, secondary. Tint `#eaf2fb`
- **Green `#2e8b57`** — success / "✓ ready" states. Tints `#e7f3ec` `#cde7d8`
- **Gold `#edc24c`** — highlights / badges. Tint `#fbf3dc`

**Type** — **Instrument Sans** (single family, wired via the same `@font-face` the mock uses). Scale: display 40–52 · h1/h2 24–34 · section 18–20 · body 13–15 · meta 11–12 (px). Weights: 700 headings, 600 for most UI, 400/500 body. The heavy semibold/bold treatment is part of the identity — don't flatten it.

**Shape** — rounded and soft. Radius: cards 16–20 · controls 10–14 · chips/pills 7–13 · full-round 46. Card lift shadow: `0 24px 60px -26px rgba(20,20,20,.32)`.

**Signature & motion** — the Buddy mascot with a gentle idle bob (`buddyBob` + a syncing `buddyShadow`). It's the one memorable element; keep everything around it quiet. The bob is ambient — gate it behind `prefers-reduced-motion`. (Mascot "moving around the page" is noted as a later step, not v1.)

### 16.2 Screen inventory → what it drives

| Mock | Screen | Backend it drives |
|------|--------|-------------------|
| **1a** ✓ | Homepage — mascot hero ("Let's build something together") + **Your projects** grid | Shell + module registry; `GET /projects` |
| 1b | Homepage — Split *(not chosen; keep as reference)* | — |
| **1c** | My Mechanic — "Start new" + past projects | `GET /modules/{slug}` + `GET /projects?module=mechanic` |
| **1d** | New Project Setup — stepper (Describe → Chat → Documents); free-text + idea chips; **skill: Beginner/Handy/Pro**; **budget: <$30 / $30–75 / $75+** | `POST /generate/sessions` (§7.1) |
| **1e** | Chat with Agent — clarify → propose → "✓ Generate documents" | `POST /generate/sessions/{id}/messages` → `…/finalize` (§7.1) |
| **1f** | Generated Documents — viewable + **Download all** | Rendered spec §6; PDF export (16.3) |

**Routing** (from the mock URLs): `/{module-slug}/{project-slug}/{view}`, e.g. `/my-mechanic/doorway-pull-up-bar/docs`. Requires `slug` on `projects` (§5). The three flow screens are the primary path; the import path (§7/§11) has no screen — it's a seed/test seam behind the same spec.

### 16.3 Output = the four sections (not the mock's document split)

**Decided:** the finished plan is the **four interactive sections from §1** — shopping cart, three-bucket tool list, tutorial, and research-first — plus the journal. The mock's three-document grouping (*Materials & Cut List / Step-by-Step Guide / Fit & Safety Notes*) was **placeholder framing** and is not the information architecture; don't build to it.

- The sections are the live surface (source of truth = spec + state in Postgres): checkboxes, per-step notes, and photos happen here. Tool list and research-first are each **first-class sections**, not folded into anything.
- 1f's "documents" screen is just the **finished/viewing layout** for those same sections once a plan is generated — a clean read-only presentation of the four sections, with an optional **PDF export** ("Download all", spec-driven via the `pdf` skill) that closes Ryan's original "keep these anywhere without printing" goal. Offline *viewing* is the PWA (§9); *export* covers keeping and sharing.

### 16.4 Safety & the mascot — two practical flags

- **Safety disclaimers are part of the product, not boilerplate.** The mock footer already carries "My Buddy can make mistakes — double-check load ratings." Enshrine it: every generated plan shows a disclaimer, and load-bearing / structural / electrical / power-tool content gets emphasized cautions. The mock's **"test routine"** (verify the build is safe before real use) is a good pattern to bake into finalize output for anything that bears weight.
- **The mascot is an original character** (`design/buddy-mascot.svg`). The Hasbro *My Buddy* doll in the Claude Design mocks was only a stand-in — we're not shipping it. The original "Buddy" is a friendly maker-bot that keeps the doll's spirit and palette (red body, a blue cap, a gold heart badge nodding to the "My Buddy" nameplate, freckles, and a rainbow collar echoing the striped shirt) as an **SVG** — so it scales from a hero down to a home-screen icon, recolors straight from the tokens, and drives the idle bob. No trademark exposure.

### 16.5 Handoff for agents C (shell) and D (mechanic-ui)

- **Design skill — toolchain-specific (Claude Code vs Codex).** Claude Code agents have a built-in **`frontend-design` skill** — invoke it first, then build to the tokens in 16.1. This is a Claude Code skill, **not** a file in the repo, so **Codex agents don't have it**; Codex builds straight from the §16.1 tokens + the mock markup instead. Either way, **`design/mocks.html`** is the shared reference for exact spacing and component structure for both toolchains — pull from it rather than approximating.
- **Mobile frames are canonical** for the PWA — every mock has one. Hit the quality floor: responsive to mobile, visible keyboard focus, `prefers-reduced-motion` honored (the bob).
- **Copy voice** (matches the mocks + the skill): warm, plain, active. Buttons name the outcome — "Open My Mechanic →", "Start chatting →", "Generate documents →" — and keep that name through the flow. Empty states invite action; errors say what happened and how to fix it.
