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

Kept deliberately minimal to avoid write contention. Two channels split by stakes, a status board, and a task ledger:

```
my-buddy-bus/
├─ README.md             # protocol quick-reference (points back to this doc)
├─ BROADCAST.md          # append-only — low-stakes only: FYI / READY / DONE
├─ INBOX/                # directed, must-be-seen msgs — ONE FILE PER MESSAGE
│   ├─ backend-core/
│   ├─ claude-service/
│   ├─ frontend-shell/
│   ├─ mechanic-ui/
│   └─ ryan/             # QUESTIONs addressed to Ryan land here
├─ TASKS.md              # the work ledger — claim before you build
└─ STATUS/
    ├─ backend-core.md   # each agent writes ONLY its own file (a heartbeat)
    ├─ claude-service.md
    ├─ frontend-shell.md
    └─ mechanic-ui.md
```

**Two channels, split by stakes — the one rule that prevents lost messages:**

- **`INBOX/<recipient>/<ts>-<from>-<TYPE>.md`** — one file per message, so writes never collide. Everything that MUST be seen or is directed at someone: `CONTRACT-CHANGE`, `QUESTION`, `BLOCKED`, `ACK`. The recipient **deletes the file once actioned**, so *files sitting in your INBOX = your open items*.
- **`BROADCAST.md`** — append-only, **low-stakes only** (`FYI` / `READY` / `DONE`) — things others may want but no one must ack. Write protocol: **re-read the tail immediately before appending**; if it moved since you last read, re-append. A lost `FYI` is survivable — that's exactly why nothing critical lives here.
- **`STATUS/<agent>.md`** — you write only your own file, so zero contention. Your state at a glance (template in §4.1), including a `last_updated` so a stale heartbeat reads as *offline*, not *stuck*.
- **`TASKS.md`** — the ledger. Claim coarsely (a whole row, not sub-items): read → edit only your row → write.

The bus **is its own throwaway git repo** (`git init` inside `my-buddy-bus/`), so every INBOX/BROADCAST/STATUS change is a `git log`-able commit. It is **never** tracked by, or merged into, the product's git.

---

## 4. Message format (INBOX + BROADCAST entries)

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
| `ACK` | Acknowledges a directed ask (usually a `CONTRACT-CHANGE`): "seen — no objection / rebased." Sent back into the originator's INBOX. |

**Channel routing:** `CONTRACT-CHANGE`, `QUESTION`, `BLOCKED`, `ACK` → `INBOX/<recipient>/` (must be seen). `READY`, `DONE`, `FYI` → `BROADCAST.md`.

### 4.1 STATUS file template

Each agent keeps its own `STATUS/<agent>.md` current. Minimal shape:

```markdown
# backend-core
state:        working    # idle | working | blocked | ready | offline
last_updated: 2026-07-03T14:32Z
branch:       agent/backend-core @ <short-sha>
working_on:   TASKS row "Data model + migrations"
blocked_on:   —          # e.g. "claude-service ACK on CONTRACT-CHANGE re: spec schema"
ready:        —          # endpoints/components others can integrate against now
```

---

## 5. The rules

1. **Read before you write.** Start each work cycle by draining your `INBOX/`, reading new BROADCAST entries, and checking TASKS. Re-read both before touching any shared contract file.
2. **Contract changes are serialized (the one protocol that can't be sloppy).**
   1. Drop a `CONTRACT-CHANGE` into every other agent's `INBOX/`, naming the file and the change.
   2. **Wait for an `ACK` from each affected agent.** No ack within your work session → escalate a `QUESTION` to Ryan; never merge on silence.
   3. Land it as its own small PR into `main`, **including the regenerated `shared/openapi.json` + `frontend/src/api/schema.d.ts`** if the OpenAPI surface moved.
   4. Post `DONE` to BROADCAST with the merge SHA.
   5. Everyone then **pauses → rebases onto `main` → re-runs `dump_openapi.py` + `gen:api` → resumes.**
   Never edit a contract file while someone else has an open, unacked `CONTRACT-CHANGE` on it.
3. **Claim before you build.** Set your task's row in TASKS to `in-progress` (with your name) before starting, so no two agents grab the same work.
4. **Announce readiness.** When an endpoint/component is done and matches the contract, post `READY` so dependents can integrate against it.
5. **Escalate, don't guess.** Anything resembling an `ARCHITECTURE.md` §2 decision, or a contract change others push back on → `QUESTION` to Ryan, then stop. Guessing on the contract is the expensive mistake; a blocked agent is cheap.
6. **Keep STATUS current, with a timestamp.** Update your STATUS file — including `last_updated` — whenever your state changes. A heartbeat older than your active session reads as *offline*, so Ryan and blocked agents can tell "stuck" from "gone." It's how Ryan reads the whole board at a glance.

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

- **`STATUS/`** — the live board: who's on what, who's blocked, what's ready (watch for stale `last_updated` = offline).
- **`INBOX/ryan/`** — `QUESTION`s waiting on you. And any `INBOX/<agent>/` with files still sitting in it = `CONTRACT-CHANGE`s mid-flight, not yet acked.
- **`BROADCAST.md`** — skim `READY` / `DONE` for progress.

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
