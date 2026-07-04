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


def extract_json(text: str) -> Any:
    """Best-effort parse of a JSON value out of a model's text response.

    Tries, in order: a direct parse, a fence-stripped parse, then a parse of the
    substring between the first ``{`` and the last ``}``. Raises
    ``SpecValidationError`` with the raw head of the text if none succeed.
    """
    if not text or not text.strip():
        raise SpecValidationError("Model returned an empty response; expected JSON.")

    candidates = []
    stripped = text.strip()
    candidates.append(stripped)

    fenced = _strip_code_fences(text)
    if fenced != stripped:
        candidates.append(fenced)

    # Last resort: carve out the outermost braces from surrounding prose.
    start = fenced.find("{")
    end = fenced.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(fenced[start : end + 1])

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
