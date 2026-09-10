#!/usr/bin/env python3
"""Apply cite hints[] from scripts/cite_hints.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "rules"
MANIFEST = ROOT / "scripts" / "cite_hints.json"


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cites: dict[str, list[str]] = data.get("cites") or {}
    if not cites:
        print("cite_hints.json has no cites.", file=sys.stderr)
        return 1

    by_id: dict[str, Path] = {}
    for path in CATALOG.rglob("*.json"):
        record = json.loads(path.read_text(encoding="utf-8"))
        by_id[str(record["id"])] = path

    missing = sorted(set(cites) - set(by_id))
    if missing:
        print("Unknown cite ids:", ", ".join(missing), file=sys.stderr)
        return 1

    touched = 0
    for cid, hints in sorted(cites.items()):
        path = by_id[cid]
        record = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(hints, list) or not hints or not all(isinstance(h, str) for h in hints):
            print(f"Bad hints for {cid!r}", file=sys.stderr)
            return 1
        record["hints"] = hints
        path.write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        touched += 1

    print(f"Applied hints to {touched} cites.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
