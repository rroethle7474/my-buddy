"""Research resource lookup (ARCHITECTURE.md §7.2) — the web-search pass.

Given a spec's ``research_topics``, run one web-search pass that finds 1–2
beginner-friendly resources per topic (short how-to videos, reputable guides)
and returns them shaped as spec ``ResearchResource`` objects. This is the ONLY
place the app reaches the web (§7.2): materials/tools are described generically,
never scraped.

Scaffold-ahead status (B3): this logic is independent of the DB and fully
usable now. The endpoint ``POST /projects/{id}/research/refresh`` (§11) that
persists the refreshed resources waits on ``READY: projects-api`` (A2). Results
are degrade-gracefully: a parse failure or a topic with no hits yields an empty
resources list, never an error — the plan is still usable without links.
"""

from __future__ import annotations

from typing import Dict, Iterable, List

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..schemas.spec import ProjectSpec, ResearchResource
from . import prompts
from .client import ClaudeClient, ClaudeError
from .spec_gate import SpecValidationError, extract_json

_ALLOWED_TYPES = {"video", "article"}

# Topics per web-search call. Chunking (vs. one call for all topics) gives
# per-chunk failure tolerance so a single hung/failed search doesn't lose every
# topic — the all-or-nothing loss confirmed during the 2026-07-04 incident.
# Option B (Ryan 2026-07-04): pairs cap the blast radius while keeping the cost
# multiplier modest (~2× for a typical 4-topic spec).
_CHUNK_SIZE = 2


# ── Tolerant drafts for parsing the model's JSON (extra fields ignored) ───────
class _ResourceDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = ""
    url: str = ""
    type: str = "article"


class _TopicDraft(BaseModel):
    model_config = ConfigDict(extra="ignore")

    topic: str = ""
    resources: List[_ResourceDraft] = Field(default_factory=list)


def _norm(s: str) -> str:
    return s.strip().lower()


def run_research(
    client: ClaudeClient,
    topics: Iterable[str],
    *,
    max_per_topic: int = 2,
    chunk_size: int = _CHUNK_SIZE,
) -> Dict[str, List[ResearchResource]]:
    """Return a ``{topic: [ResearchResource, ...]}`` map for the given topics.

    Runs the web-search pass in **chunks of ``chunk_size`` topics** (default 2)
    with **per-chunk tolerance**: each chunk is an independent ``web_search``
    call, so one chunk failing (timeout / deadline / API error) costs only its
    own topics — the rest still fill and persist. A topic in a failed chunk, or
    one the search found nothing for, gets an empty list. It only raises
    ``ClaudeError`` when *every* chunk fails, so the endpoint's 502 path is kept
    for a total outage but a partial result returns 200 (Option B, Ryan
    2026-07-04). Within a chunk, results map back by exact topic text, else
    positionally; a garbage/empty model response is not a failure, just empties.

    Cost / latency: N topics → ``ceil(N / chunk_size)`` sequential ``web_search``
    calls (≈2× the single-call cost for a typical 4-topic spec — accepted by
    Ryan in exchange for killing the all-or-nothing loss). Each call keeps its
    own bounds (``web_search``'s 90s round / 180s deadline), so the worst case is
    ``ceil(N / chunk_size) × 180s`` — e.g. ~360s for 4 topics if both chunks run
    to their full deadline (real calls are far shorter).
    """
    topics = list(topics)
    if not topics:
        return {}

    step = max(1, chunk_size)
    chunks = [topics[i : i + step] for i in range(0, len(topics), step)]
    result: Dict[str, List[ResearchResource]] = {}
    failed_chunks = 0

    for chunk in chunks:
        try:
            text = client.web_search(
                system=prompts.RESEARCH_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompts.build_research_user_prompt(chunk)}
                ],
            )
        except ClaudeError:
            # Tolerated: this chunk's topics stay empty; the other chunks proceed.
            failed_chunks += 1
            for topic in chunk:
                result[topic] = []
            continue

        drafts = _parse_topic_drafts(text)
        result.update(_map_to_topics(chunk, drafts, max_per_topic))

    if failed_chunks == len(chunks):
        # Every chunk failed → a real upstream outage; surface it so the endpoint
        # returns 502 (rather than persisting an all-empty "success").
        raise ClaudeError(f"All {len(chunks)} research search chunk(s) failed.")

    return result


def apply_research_to_spec(
    spec: ProjectSpec,
    resources_by_topic: Dict[str, List[ResearchResource]],
) -> ProjectSpec:
    """Return a copy of ``spec`` with each topic's ``resources`` filled in.

    A topic absent from the map keeps whatever resources it already had.
    """
    updated = [
        topic.model_copy(
            update={"resources": resources_by_topic.get(topic.topic, topic.resources)}
        )
        for topic in spec.research_topics
    ]
    return spec.model_copy(update={"research_topics": updated})


def research_for_spec(client: ClaudeClient, spec: ProjectSpec) -> ProjectSpec:
    """Convenience: run the pass over a spec's topics and return the filled spec."""
    resources = run_research(client, [t.topic for t in spec.research_topics])
    return apply_research_to_spec(spec, resources)


# ─────────────────────────────────────────────────────────────────────────────
# Internals
# ─────────────────────────────────────────────────────────────────────────────
def _parse_topic_drafts(text: str) -> List[_TopicDraft]:
    try:
        data = extract_json(text)
    except SpecValidationError:
        return []
    if not isinstance(data, list):
        return []
    drafts: List[_TopicDraft] = []
    for item in data:
        try:
            drafts.append(_TopicDraft.model_validate(item))
        except ValidationError:
            drafts.append(_TopicDraft())
    return drafts


def _map_to_topics(
    topics: List[str],
    drafts: List[_TopicDraft],
    max_per_topic: int,
) -> Dict[str, List[ResearchResource]]:
    # Index drafts by normalized topic for exact-match mapping; fall back to
    # position when the model didn't echo the topic text.
    by_norm: Dict[str, int] = {}
    for i, d in enumerate(drafts):
        by_norm.setdefault(_norm(d.topic), i)

    used = [False] * len(drafts)
    result: Dict[str, List[ResearchResource]] = {}

    for idx, topic in enumerate(topics):
        draft = None
        j = by_norm.get(_norm(topic))
        if j is not None and not used[j]:
            draft, used[j] = drafts[j], True
        elif idx < len(drafts) and not used[idx]:
            draft, used[idx] = drafts[idx], True
        result[topic] = _clean_resources(draft, max_per_topic) if draft else []

    return result


def _clean_resources(draft: _TopicDraft, max_per_topic: int) -> List[ResearchResource]:
    out: List[ResearchResource] = []
    for r in draft.resources:
        title, url = r.title.strip(), r.url.strip()
        if not title or not url.startswith("http"):
            continue
        rtype = r.type.strip().lower()
        if rtype not in _ALLOWED_TYPES:
            rtype = "article"
        out.append(ResearchResource(title=title, url=url, type=rtype))
        if len(out) >= max_per_topic:
            break
    return out
