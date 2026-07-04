"""The finalize→spec validation gate (ARCHITECTURE.md §7.1, §6 note 3).

Generation's finalize call returns a §6 spec as JSON. Structured output makes
the model return well-formed JSON, but we still route everything through ONE
defensive gate so that:

- stray prose or `````json`` fences are tolerated (§7.1: "parse defensively —
  strip stray fences, try/parse, re-request on failure"),
- the result is validated against the single Pydantic model (``ProjectSpec``),
  the same gate the import path uses (§14: "spec validation is centralized"),
- failures raise a clear, re-requestable error instead of a stack trace.

This module has NO Claude dependency — it is pure parsing/validation, so it is
cheap to unit-test and reusable by the import path.
"""

from __future__ import annotations

import json
from typing import Any, Union

from pydantic import ValidationError

from ..schemas.spec import ProjectSpec


class SpecValidationError(ValueError):
    """Raised when a payload can't be parsed/validated into a ``ProjectSpec``.

    ``message`` is human-readable and safe to feed back to Claude as a
    correction prompt on a re-request.
    """


def _strip_code_fences(text: str) -> str:
    """Remove a single leading/trailing markdown code fence if present.

    Handles ```json\n...\n``` and bare ```\n...\n``` wrappers that models
    sometimes add despite being told not to.
    """
    s = text.strip()
    if not s.startswith("```"):
        return s
    # Drop the opening fence line (```
    # or ```json) and the trailing fence.
    first_newline = s.find("\n")
    if first_newline == -1:
        return s
    s = s[first_newline + 1 :]
    if s.rstrip().endswith("```"):
        s = s.rstrip()[: -len("```")]
    return s.strip()


def _carve_json(s: str) -> Union[str, None]:
    """Carve the outermost JSON value (object or array) from surrounding prose.

    Picks the earliest opening bracket (``{`` or ``[``) and matches it to the
    last closing bracket of the same kind — so a JSON array emitted after a
    prose preamble (common with web-search answers that concatenate several
    text blocks) is recovered, not just objects.
    """
    starts = [i for i in (s.find("{"), s.find("[")) if i != -1]
    if not starts:
        return None
    start = min(starts)
    closer = "}" if s[start] == "{" else "]"
    end = s.rfind(closer)
    return s[start : end + 1] if end > start else None


def extract_json(text: str) -> Any:
    """Best-effort parse of a JSON value out of a model's text response.

    Tries, in order: a direct parse, a fence-stripped parse, then a carve of the
    outermost object/array from surrounding prose. Raises ``SpecValidationError``
    with the raw head of the text if none succeed.
    """
    if not text or not text.strip():
        raise SpecValidationError("Model returned an empty response; expected JSON.")

    stripped = text.strip()
    fenced = _strip_code_fences(text)

    candidates = [stripped]
    if fenced != stripped:
        candidates.append(fenced)
    for carved in (_carve_json(fenced), _carve_json(stripped)):
        if carved and carved not in candidates:
            candidates.append(carved)

    last_err: Union[json.JSONDecodeError, None] = None
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:  # noqa: PERF203 - small, clear loop
            last_err = exc
            continue

    head = stripped[:200]
    raise SpecValidationError(
        f"Response was not valid JSON ({last_err}). First 200 chars: {head!r}"
    )


def parse_spec(payload: Union[str, dict, Any]) -> ProjectSpec:
    """Validate a raw payload into a ``ProjectSpec`` — the one spec gate.

    ``payload`` may be the model's raw text (defensively parsed) or an already
    decoded dict (the import path passes a dict straight through). Any parse or
    validation failure is normalised to ``SpecValidationError`` with a message
    suitable both for an API 4xx and for a correction re-request to Claude.
    """
    data = extract_json(payload) if isinstance(payload, str) else payload

    if not isinstance(data, dict):
        raise SpecValidationError(
            f"Expected a JSON object for the spec, got {type(data).__name__}."
        )

    try:
        return ProjectSpec.model_validate(data)
    except ValidationError as exc:
        raise SpecValidationError(_summarize_validation_error(exc)) from exc


def _summarize_validation_error(exc: ValidationError) -> str:
    """Condense a Pydantic ValidationError into a short, actionable string."""
    parts = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", ())) or "<root>"
        parts.append(f"{loc}: {err.get('msg', 'invalid')}")
    joined = "; ".join(parts[:8])
    if len(parts) > 8:
        joined += f"; (+{len(parts) - 8} more)"
    return f"Spec failed validation against the §6 schema: {joined}"
