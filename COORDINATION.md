# my-buddy — Agent Coordination & Message Bus

**Audience:** the parallel build agents (Claude Code and/or Codex) + Ryan.
**Complements:** `ARCHITECTURE.md` §12 (build phases) and §13 (worktree ownership). §13 says *who owns what*; this doc says *how they talk and stay out of each other's way*.
**Wiring:** point each toolchain's bootstrap file at this doc so agents load it every session — Claude Code: reference it from `CLAUDE.md`; Codex: reference it from `AGENTS.md`. The bus itself is plain markdown on disk, so both toolchains share one bus.

---

## 1. The core problem

Git worktrees share one `.git` but have **separate working directories**. A file committed on `agent/backend-core` is invisible in the `mechanic-ui` working tree until it's merged into that branch. So a committed, in-repo file can't serve as a real-time channel. The bus therefore lives **outside all worktrees**, as loose files on the local filesystem that every agent can read and write immediately.

---

## 2. Worktree layout

```
my-buddy/                         # main clone — branch: main (holds the frozen contract)
../worktrees/
   backend-core/                  # agent/backend-core
   claude-service/                # agent/claude-service
   frontend-shell/                # agent/frontend-shell
   mechanic-ui/                   # agent/mechanic-ui
../my-buddy-bus/                  # the shared message bus (NOT tracked by the product repo)
```

Setup:

```bash
# from the main clone, after Phase 0 has landed on main
git worktree add ../worktrees/backend-core   -b agent/backend-core
git worktree add ../worktrees/claude-service -b agent/claude-service
git worktree add ../worktrees/frontend-shell -b agent/frontend-shell
git worktree add ../worktrees/mechanic-ui    -b agent/mechanic-ui
mkdir -p ../my-buddy-bus/STATUS
```

Branch naming: `agent/<name>`. Integration: small PRs into `main`. **Phase 0 (scaffold + contract, §12) lands on `main` first** — the worktrees branch off it so everyone starts from the same frozen contract.

---

## 3. Bus layout

Kept deliberately minimal to avoid write contention. Three parts:

```
my-buddy-bus/
├─ BROADCAST.md          # append-only feed everyone reads (the main channel)
├─ TASKS.md              # the work ledger — claim before you build
└─ STATUS/
    ├─ backend-core.md   # each agent writes ONLY its own file (a heartbeat)
    ├─ claude-service.md
    ├─ frontend-shell.md
    └─ mechanic-ui.md
```

- **`STATUS/<agent>.md`** — you write only your own file. No two agents ever touch the same status file, so there's zero write conflict. It's your current state at a glance: *working on / blocked on / ready-for-integration*.
- **`BROADCAST.md`** — append-only. Everything others need to know: contract changes, readiness, questions. Append conflicts are rare at this scale; if a write races, re-read and re-append.
- **`TASKS.md`** — the ledger. Edit your task's row to claim it and advance its status.

*(If BROADCAST ever gets noisy, split directed messages into `INBOX/<recipient>/<msg>.md`, one file per message — zero contention. Not needed to start.)*

The bus is **not** tracked by the product repo. If you want a history, make `my-buddy-bus/` its own throwaway git repo and let agents commit there freely — it never touches the product's git.

---

## 4. Message format (BROADCAST entries)

One consistent shape — parseable and human-readable:

```markdown
### 2026-07-03T14:32Z · backend-core · CONTRACT-CHANGE
**Re:** shared/project-spec.schema.json
Adding `materials[].category`. Pausing integration against the spec schema.
**PR:** #12 (agent/backend-core → main)
**Needs:** ack from mechanic-ui before merge.
```

Header line: `<UTC timestamp> · <from> · <TYPE>`, then a short structured body.

**Types (fixed vocabulary):**

| Type | Meaning |
|------|---------|
| `CONTRACT-CHANGE` | About to change a shared contract file (spec schema / router signatures / generated types). The serialization signal. |
| `READY` | An endpoint/component is built and matches the contract — safe to integrate against. |
| `BLOCKED` | Can't proceed without something from another agent. |
| `QUESTION` | Needs a decision. If it's architectural/scope (an `ARCHITECTURE.md` §2-style call), address it to **Ryan** and wait. |
| `DECISION` | A resolved question, recorded so everyone sees the outcome. |
| `DONE` | A task or phase is complete. |
| `FYI` | General announcement. |

---

## 5. The rules

1. **Read before you write.** Start each work cycle by reading new BROADCAST entries + TASKS. Re-read BROADCAST before touching any shared contract file.
2. **Contract changes are serialized.** (§13, made mechanical.) Post `CONTRACT-CHANGE` → wait for ack → land it as its own small PR → post `DONE` → everyone rebases onto `main`. Never edit a contract file while someone else has an open, unacked `CONTRACT-CHANGE` on it.
3. **Claim before you build.** Set your task's row in TASKS to `in-progress` (with your name) before starting, so no two agents grab the same work.
4. **Announce readiness.** When an endpoint/component is done and matches the contract, post `READY` so dependents can integrate against it.
5. **Escalate, don't guess.** Anything resembling an `ARCHITECTURE.md` §2 decision, or a contract change others push back on → `QUESTION` to Ryan, then stop. Guessing on the contract is the expensive mistake; a blocked agent is cheap.
6. **Keep STATUS current.** Update your STATUS file whenever your state changes. It's how Ryan reads the whole board at a glance.

---

## 6. The contract files (what rule #2 protects)

From `ARCHITECTURE.md` §13 — changing any of these is a `CONTRACT-CHANGE`:

- `shared/project-spec.schema.json` — the project spec (§6)
- FastAPI router signatures / the OpenAPI surface (§11)
- The generated `frontend/src/api` types (regenerated from OpenAPI — never hand-edited)

As long as these hold steady, the four worktrees proceed independently. The bus exists mostly to coordinate the moments they *don't*.

---

## 7. Integration cadence

- Phase 0 → `main` first (blocking). Then A/B/C/D branch off and run in parallel per §12.
- Small, frequent PRs into `main` beat big-bang merges.
- Contract-file PRs jump the queue — merge them fast so no one stays blocked; everyone rebases after.

---

## 8. Ryan's view

You don't need to read the whole bus. Two things tell you everything:

- **`STATUS/`** — the live board: who's on what, who's blocked, what's ready.
- **`BROADCAST.md`** — filter for `QUESTION` (waiting on you) and `CONTRACT-CHANGE` (structural moves in flight).

The `ARCHITECTURE.md` §2 decision points are the canonical "human decides" set — agents route those to you rather than guessing.

---

## 9. TASKS.md seed

Start the ledger from the §12 phases:

```markdown
| Task | Phase | Owner | Status | Notes |
|------|-------|-------|--------|-------|
| Repo scaffold + contract freeze          | 0 | (shared)        | todo | blocks everything |
| Data model + migrations                  | 1 | backend-core    | todo | §5 |
| CRUD + storage adapter                    | 1 | backend-core    | todo | §5, §14 |
| Import path + shop diff                   | 1 | backend-core    | todo | §8 |
| my-buddy shell + routing + PWA           | 1 | frontend-shell  | todo | offline caching |
| Generation flow (constraints→candidates→spec) | 2 | claude-service | todo | §7.1 |
| Research web-search pass                  | 2 | claude-service  | todo | §7.2 |
| Mechanic UI (cart/tools/tutorial/journal) | 2 | mechanic-ui     | todo | renders off spec §6 |
| Offline replay + retrospective + photos   | 3 | (frontend)      | todo | §9 |
```
