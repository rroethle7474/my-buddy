"""Server-side Anthropic SDK wrapper (ARCHITECTURE.md §7).

All Claude calls run server-side through this client — the API key never reaches
the browser (§4 rule, §7). The model is config-driven (``ANTHROPIC_MODEL``,
default ``claude-opus-4-8``) so it is swappable without code changes.

Two primitives that the generation flow (B2) and research pass (B3) build on:

- ``chat`` — one natural-language turn of the bounded conversation (§7.1). Uses
  adaptive thinking (the only supported thinking mode on Opus 4.8).
- ``generate_spec`` — the finalize call: constrained structured output +
  defensive parsing through the single spec gate, with a corrective re-request
  on validation failure (§7.1).

The SDK client is constructed lazily so importing this module never requires a
key (Phase-0 imports, tests, and tooling stay green without one).
"""

from __future__ import annotations

import time
from typing import List, Optional

import anthropic
from pydantic import ValidationError

from ..config import settings
from ..schemas.spec import ProjectSpec
from .prompts import PROMPTS_VERSION
from .spec_gate import SpecValidationError, parse_spec

# Sensible output ceilings. Chat turns are short; a finalized spec can be large
# (materials + tools + multi-step tutorial). Both stay under the SDK's
# non-streaming timeout guard (~16k). See the claude-api reference.
_CHAT_MAX_TOKENS = 4096
_SPEC_MAX_TOKENS = 16000


class ClaudeError(RuntimeError):
    """A Claude call failed (transport, auth, refusal, or empty output)."""


class ClaudeClient:
    """Thin wrapper over ``anthropic.Anthropic`` scoped to this app's needs."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        # Fall back to config; pass None (not "") so the SDK can still resolve a
        # key from the environment / an `ant` profile if config is unset.
        self._api_key = api_key if api_key is not None else (settings.anthropic_api_key or None)
        self.model = model or settings.anthropic_model
        self.prompts_version = PROMPTS_VERSION
        self._client: Optional[anthropic.Anthropic] = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    # ── one conversational turn (§7.1 clarify/propose/ready) ─────────────────
    def chat(
        self,
        *,
        system: str,
        messages: List[dict],
        thinking: bool = True,
        max_tokens: int = _CHAT_MAX_TOKENS,
    ) -> str:
        """Send the conversation and return the agent's natural-language reply.

        ``thinking=True`` enables adaptive thinking (Opus 4.8's only thinking
        mode); ``False`` omits the param entirely (runs without thinking).
        """
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if thinking:
            kwargs["thinking"] = {"type": "adaptive"}

        try:
            resp = self.client.messages.create(**kwargs)
        except anthropic.APIError as exc:
            raise ClaudeError(f"Claude chat call failed: {exc}") from exc

        if resp.stop_reason == "refusal":
            raise ClaudeError("Claude declined to respond to this request.")

        text = _text_of(resp)
        if not text:
            raise ClaudeError(
                f"Claude returned no text (stop_reason={resp.stop_reason})."
            )
        return text

    # ── one structured turn (§7.1 clarify/propose/ready classification) ───────
    def parse(
        self,
        *,
        system: str,
        messages: List[dict],
        output_format: type,
        max_tokens: int = 2048,
        max_retries: int = 1,
    ):
        """Return a validated instance of ``output_format`` (a Pydantic model).

        Used for the structured turn decision on each /messages turn. No
        thinking — the classification is simple and this keeps turns fast (the
        finalize path likewise runs structured output without thinking).

        The SDK raises pydantic ``ValidationError`` when the model emits
        malformed/truncated JSON — a transient model flake, so it is retried up
        to ``max_retries`` times, then surfaced as ``ClaudeError`` (→ the
        endpoint's 502 path) rather than escaping as an unhandled 500.
        """
        last_exc: Optional[ValidationError] = None
        for _ in range(max_retries + 1):
            try:
                resp = self.client.messages.parse(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=messages,
                    output_format=output_format,
                )
            except anthropic.APIError as exc:
                raise ClaudeError(f"Claude structured call failed: {exc}") from exc
            except ValidationError as exc:
                last_exc = exc
                continue

            if getattr(resp, "stop_reason", None) == "refusal":
                raise ClaudeError("Claude declined to respond to this request.")

            parsed = getattr(resp, "parsed_output", None)
            if parsed is None:
                raise ClaudeError(
                    f"Claude returned no structured output (stop_reason="
                    f"{getattr(resp, 'stop_reason', None)})."
                )
            return parsed

        raise ClaudeError(
            f"Claude returned malformed structured output after "
            f"{max_retries + 1} attempt(s): {last_exc}"
        ) from last_exc

    # ── finalize → validated §6 spec (§7.1) ──────────────────────────────────
    def generate_spec(
        self,
        *,
        system: str,
        messages: List[dict],
        max_tokens: int = _SPEC_MAX_TOKENS,
        max_retries: int = 1,
    ) -> ProjectSpec:
        """Run the finalize call and return a validated ``ProjectSpec``.

        Uses structured output (``output_format=ProjectSpec``) to constrain the
        JSON, then routes the result through the single ``parse_spec`` gate. On a
        validation failure, re-requests up to ``max_retries`` times with the
        error fed back as a correction (§7.1 "re-request on failure").
        """
        convo = list(messages)
        last_error: Optional[SpecValidationError] = None

        for attempt in range(max_retries + 1):
            try:
                resp = self.client.messages.parse(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=convo,
                    output_format=ProjectSpec,
                )
            except anthropic.APIError as exc:
                raise ClaudeError(f"Claude finalize call failed: {exc}") from exc
            except ValidationError as exc:
                # The SDK's structured-output parser raises on malformed or
                # truncated model JSON — recoverable the same way as a spec-gate
                # failure, so it joins the corrective re-request loop.
                last_error = SpecValidationError(f"response was not valid JSON: {exc}")
                if attempt >= max_retries:
                    break
                convo = convo + [
                    {
                        "role": "user",
                        "content": (
                            "That response was not valid JSON. Return only the "
                            "corrected JSON object matching the schema."
                        ),
                    }
                ]
                continue

            if getattr(resp, "stop_reason", None) == "refusal":
                raise ClaudeError("Claude declined to generate the project spec.")

            # Preferred path: the SDK validated the structured output for us.
            parsed = getattr(resp, "parsed_output", None)
            if isinstance(parsed, ProjectSpec):
                return parsed

            # Fallback: defensively parse the raw text through the same gate.
            try:
                return parse_spec(_text_of(resp))
            except SpecValidationError as exc:
                last_error = exc
                if attempt >= max_retries:
                    break
                convo = convo + [
                    {
                        "role": "user",
                        "content": (
                            "That response was not a valid project spec: "
                            f"{exc}. Return only the corrected JSON object "
                            "matching the schema."
                        ),
                    }
                ]

        raise ClaudeError(
            f"Claude could not produce a valid spec after "
            f"{max_retries + 1} attempt(s): {last_error}"
        )


    # ── research web-search pass (§7.2) ───────────────────────────────────────
    def web_search(
        self,
        *,
        system: str,
        messages: List[dict],
        max_tokens: int = 8000,
        max_uses: int = 5,
        max_rounds: int = 6,
        round_timeout_s: float = 90.0,
        deadline_s: float = 180.0,
    ) -> str:
        """Run a web-search-enabled call and return the model's final text.

        Declares the server-side ``web_search`` tool (dynamic-filtering variant,
        Opus 4.8) and drives the server-tool loop, re-sending on ``pause_turn``
        (the server hit its per-turn tool-iteration cap). This is the ONLY place
        the app reaches the web (§7.2).

        Every round runs with an explicit request timeout and SDK-level retries
        disabled, all under one ``deadline_s`` budget. Without these, a hung
        upstream call holds the request for the SDK's ~10-minute default times
        its retry count — pinning the caller (and any UI waiting on it) while
        still billing the searches.
        """
        tools = [
            {"type": "web_search_20260209", "name": "web_search", "max_uses": max_uses}
        ]
        convo = list(messages)
        resp = None
        started = time.monotonic()
        for _ in range(max_rounds):
            remaining = deadline_s - (time.monotonic() - started)
            if remaining <= 0:
                raise ClaudeError(
                    f"Research web search exceeded its {deadline_s:.0f}s deadline."
                )
            try:
                resp = self.client.with_options(
                    timeout=min(round_timeout_s, remaining), max_retries=0
                ).messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    system=system,
                    messages=convo,
                    tools=tools,
                )
            except anthropic.APIError as exc:
                raise ClaudeError(f"Claude web-search call failed: {exc}") from exc

            if resp.stop_reason == "refusal":
                raise ClaudeError("Claude declined the research request.")
            if resp.stop_reason == "pause_turn":
                # Server paused mid-tool-loop; echo its partial turn back to
                # resume (per the server-tool continuation pattern).
                convo = convo + [{"role": "assistant", "content": resp.content}]
                continue
            return _text_of(resp)

        # Ran out of rounds — return whatever text the last turn produced.
        return _text_of(resp) if resp is not None else ""


def _text_of(resp: object) -> str:
    """Join the text of all ``text`` content blocks in a Messages response."""
    content = getattr(resp, "content", None) or []
    return "".join(
        block.text
        for block in content
        if getattr(block, "type", None) == "text" and getattr(block, "text", None)
    ).strip()


# Process-wide singleton, lazily built. Endpoints get it via this accessor.
_client: Optional[ClaudeClient] = None


def get_claude_client() -> ClaudeClient:
    global _client
    if _client is None:
        _client = ClaudeClient()
    return _client
