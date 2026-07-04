"""Live end-to-end smoke of the full backend loop against a RUNNING app.

Drives the real HTTP surface (not in-process calls) through the whole v1 path:

    generate session -> chat turns -> finalize -> POST /projects
    -> research/refresh -> GET hydrated project

It hits real Claude (generation + web search) and a real Postgres, so the app
must be running with a valid ANTHROPIC_API_KEY and DATABASE_URL. The generated
project is left in the DB as seed data (no cleanup).

Usage (app already running on :8000):

    python scripts/e2e_smoke.py
    SMOKE_BASE_URL=http://localhost:8000 python scripts/e2e_smoke.py

Exits non-zero on any failed step or assertion.
"""

from __future__ import annotations

import os
import sys

import httpx

# Robust output regardless of the host console encoding (agent messages may
# contain em-dashes / emoji).
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # pragma: no cover - older interpreters
    pass

BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://localhost:8000")
DESCRIPTION = os.environ.get(
    "SMOKE_DESCRIPTION", "A small wall-mounted shelf for paperback books"
)
# A canned answer that covers the usual clarifying questions in one go.
CANNED_ANSWER = (
    "About 24 inches wide. I have a power drill and basic hand tools, and it "
    "will hang on a living-room wall. Keep it simple and cheap."
)
MAX_TURNS = 6


def _fail(msg: str, resp: httpx.Response | None = None) -> None:
    print(f"\nFAILED: {msg}")
    if resp is not None:
        print(f"  {resp.request.method} {resp.request.url} -> {resp.status_code}")
        print(f"  body: {resp.text[:500]}")
    sys.exit(1)


def main() -> None:
    client = httpx.Client(base_url=BASE_URL, timeout=300.0)
    print(f"Base URL: {BASE_URL}")

    # 0. Health -----------------------------------------------------------------
    r = client.get("/health")
    if r.status_code != 200:
        _fail("health check", r)
    print(f"[health] {r.json()}")

    # 1. Start a generation session --------------------------------------------
    print("\n=== POST /generate/sessions ===")
    r = client.post(
        "/generate/sessions",
        json={
            "description": DESCRIPTION,
            "skill_level": "beginner",
            "budget_band": "under_30",
        },
    )
    if r.status_code != 201:
        _fail("start session", r)
    start = r.json()
    session_id = start["session_id"]
    assert start["agent_message"], "opening message was empty"
    print(f"[session] {session_id}")
    print(f"[opening] {start['agent_message'][:200]}")

    # 2. Bounded chat until the agent is ready ----------------------------------
    print("\n=== POST /generate/sessions/{id}/messages (chat loop) ===")

    def send(body: dict) -> dict:
        resp = client.post(f"/generate/sessions/{session_id}/messages", json=body)
        if resp.status_code != 200:
            _fail("send message", resp)
        return resp.json()

    turn = send({"message": f"Yes, let's build that. {CANNED_ANSWER}"})
    reached_ready = False
    for i in range(MAX_TURNS):
        kind = turn["kind"]
        print(f"  turn {i}: kind={kind} :: {turn['agent_message'][:120]}")
        if kind == "ready":
            reached_ready = True
            break
        if kind == "proposing":
            pick = turn["candidates"][0]
            print(f"    proposing {[c['title'] for c in turn['candidates']]}; picking {pick['id']}")
            turn = send({"select_candidate_id": pick["id"]})
        else:  # clarifying
            turn = send({"message": CANNED_ANSWER})
    print(f"[chat] reached_ready={reached_ready}")

    # 3. Finalize -> §6 spec ----------------------------------------------------
    print("\n=== POST /generate/sessions/{id}/finalize ===")
    r = client.post(f"/generate/sessions/{session_id}/finalize")
    if r.status_code != 200:
        _fail("finalize", r)
    spec = r.json()
    assert spec["project"]["module"] == "mechanic", spec["project"]["module"]
    print(f"[finalize] {spec['project']['name']} "
          f"(difficulty={spec['project']['difficulty']}, ${spec['project']['estimated_cost_usd']})")
    print(f"           materials/tools/steps/research = "
          f"{len(spec['materials'])}/{len(spec['tools'])}/{len(spec['steps'])}/{len(spec['research_topics'])}")

    # 4. Commit the spec via the import path (runs the shop diff §8) -------------
    print("\n=== POST /projects (import the generated spec) ===")
    r = client.post("/projects", json=spec)
    if r.status_code != 201:
        _fail("create project", r)
    project = r.json()
    project_id, slug = project["id"], project["slug"]
    print(f"[project] id={project_id} slug={slug} status={project['status']}")
    before = sum(len(t["resources"]) for t in project["research_topics"])
    print(f"[project] research resources before refresh = {before}")

    # 5. Research refresh (§7.2 web-search pass) ---------------------------------
    print("\n=== POST /projects/{id}/research/refresh ===")
    r = client.post(f"/projects/{project_id}/research/refresh")
    if r.status_code != 200:
        _fail("research refresh", r)
    topics = r.json()
    refreshed = sum(len(t["resources"]) for t in topics)
    for t in topics:
        print(f"  - {t['topic']}: {len(t['resources'])} resource(s)")
    print(f"[refresh] {len(topics)} topics, {refreshed} resources")

    # 6. GET the hydrated project — resources must now be persisted -------------
    print("\n=== GET /projects/{id} (hydrated) ===")
    r = client.get(f"/projects/{project_id}")
    if r.status_code != 200:
        _fail("get hydrated project", r)
    hydrated = r.json()
    persisted = sum(len(t["resources"]) for t in hydrated["research_topics"])
    owned = [t["name"] for t in hydrated["tools"] if t["owned"]]
    acquire = [t["name"] for t in hydrated["tools"] if t["acquire"]]
    print(f"[hydrated] steps={len(hydrated['steps'])} materials={len(hydrated['materials'])} "
          f"tools={len(hydrated['tools'])} research_resources={persisted}")
    print(f"[hydrated] shop diff (§8): owned={owned} | acquire={acquire}")

    # Assertions ----------------------------------------------------------------
    assert project_id and slug, "project id/slug missing"
    assert refreshed >= 1, "research refresh returned no resources"
    assert persisted >= 1, "resources were not persisted / not visible on hydrated GET"
    assert len(hydrated["steps"]) >= 1, "no steps persisted"
    # Shop diff (§8): every tool is exactly one of owned / acquire.
    for tool in hydrated["tools"]:
        assert tool["owned"] != tool["acquire"], f"tool {tool['name']} owned/acquire not exclusive"

    print(f"\nE2E SMOKE PASSED — seed project id={project_id} slug={slug} left in DB")


if __name__ == "__main__":
    main()
