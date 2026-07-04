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

from typing import List, Optional

import anthropic

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
    ):
        """Return a validated instance of ``output_format`` (a Pydantic model).

        Used for the structured turn decision on each /messages turn. No
        thinking — the classification is simple and this keeps turns fast (the
        finalize path likewise runs structured output without thinking).
        """
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

        if getattr(resp, "stop_reason", None) == "refusal":
            raise ClaudeError("Claude declined to respond to this request.")

        parsed = getattr(resp, "parsed_output", None)
        if parsed is None:
            raise ClaudeError(
                f"Claude returned no structured output (stop_reason="
                f"{getattr(resp, 'stop_reason', None)})."
            )
        return parsed

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
