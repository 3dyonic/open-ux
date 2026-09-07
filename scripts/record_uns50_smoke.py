#!/usr/bin/env python3
"""Record the UNS-50 audit call against the local catalog.

Hosted play (needs a human invite key; this script does not mint one):

    POST https://open-ux.dev/mcp
    Authorization: Bearer uxmcp_…
    tool audit  arguments {"jobs": "design_a_form"}
    expect id forms.field_labels.visible_label  + name
    expect no verdict

Usage (from repo root, after ``pip install -e packages/mcp``):

    python3 scripts/record_uns50_smoke.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "packages" / "mcp" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from open_ux.audit import audit  # noqa: E402
from open_ux.catalog import load_catalog  # noqa: E402
from open_ux.settings import Settings  # noqa: E402

SEED_ID = "forms.field_labels.visible_label"
CALL = {"jobs": "design_a_form"}


def main() -> int:
    result = audit(load_catalog(Settings.load()), **CALL)
    ids = [row["id"] for row in result.get("guidelines", [])]
    seed = next((row for row in result.get("guidelines", []) if row["id"] == SEED_ID), None)
    record = {
        "call": {"tool": "audit", "arguments": CALL},
        "hosted": "https://open-ux.dev/mcp",
        "count": result.get("count"),
        "ids": ids,
        "seed_present": seed is not None,
        "seed": (
            {"id": seed["id"], "name": seed["name"]} if seed else None
        ),
        "has_verdict": "verdict" in result,
        "note": (
            "Local recording only. Live UNS-50 play still needs a human with an invite."
        ),
    }
    json.dump(record, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
