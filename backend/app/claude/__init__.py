"""Claude integration: SDK client, prompts, generation + research flows (§7).

Phase 1 (B1) foundation — the reusable building blocks the live generation
endpoints (B2) and research pass (B3) wire up:

- ``client``       — server-side Anthropic SDK wrapper (``ClaudeClient``, §7).
- ``prompts``      — versioned prompt templates with §7.3/§16.4 guardrails.
- ``session_store``— in-memory generation session store (§7.1; no DB, by design).
- ``spec_gate``    — defensive finalize→spec validation via the ``ProjectSpec``
                     Pydantic gate (§6/§7.1).
"""

from __future__ import annotations

from .client import ClaudeClient, ClaudeError, get_claude_client
from .prompts import (
    PROMPTS_VERSION,
    build_finalize_instruction,
    build_generation_system_prompt,
    build_research_user_prompt,
)
from .research import apply_research_to_spec, research_for_spec, run_research
from .session_store import (
    Session,
    SessionNotFound,
    SessionStore,
    get_session_store,
)
from .spec_gate import SpecValidationError, extract_json, parse_spec

__all__ = [
    "ClaudeClient",
    "ClaudeError",
    "get_claude_client",
    "PROMPTS_VERSION",
    "build_generation_system_prompt",
    "build_finalize_instruction",
    "build_research_user_prompt",
    "run_research",
    "apply_research_to_spec",
    "research_for_spec",
    "Session",
    "SessionNotFound",
    "SessionStore",
    "get_session_store",
    "SpecValidationError",
    "extract_json",
    "parse_spec",
]
