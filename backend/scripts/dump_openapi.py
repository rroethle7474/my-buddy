"""Dump the app's OpenAPI schema to a file (default: shared/openapi.json).

The OpenAPI surface is the frontend contract (ARCHITECTURE.md §3/§13). This
script emits it without needing a running server, so the frontend can regenerate
types (``openapi-typescript``) reproducibly:

    python scripts/dump_openapi.py            # -> ../shared/openapi.json
    python scripts/dump_openapi.py path.json  # -> custom path

Committing ``shared/openapi.json`` makes CONTRACT-CHANGEs visible as a diff
(COORDINATION.md §5/§6).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure the backend package is importable when run from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

DEFAULT_OUT = Path(__file__).resolve().parents[2] / "shared" / "openapi.json"


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    out.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote OpenAPI schema to {out}")


if __name__ == "__main__":
    main()
