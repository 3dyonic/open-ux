#!/usr/bin/env python3
"""Reorder a pack page with BM25 over pack scan fields.

Host still serves the pack (catalog order / facet page). This script is
optional: the model can run it locally after Open-UX:pack. No winner,
no scores. Fail-open if the query hits nothing.

Blob: id, name, overview, apply_when, not_when, rule, hints, component,
leaf, card, facet. Not description or pass/fail.

Available, not required. Open-UX:pack stays first-class.

Usage (from repo root, after ``pip install open-ux`` or an editable install):

    python3 helpers/rank_pack.py --query "delete confirm" < pack.json
    python3 helpers/rank_pack.py --query "landing cta" pack.json
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, TextIO

from open_ux.bm25 import rank_pack


def _load(stream: TextIO) -> dict[str, Any]:
    raw = json.load(stream)
    if isinstance(raw, list):
        return {"guidelines": raw, "count": len(raw), "total": len(raw)}
    if not isinstance(raw, dict) or "guidelines" not in raw:
        raise SystemExit("rank_pack: expected a pack object with guidelines, or a list of cites.")
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reorder a pack page. You decide what to take.",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="Words to rank this page. Does not drop cites.",
    )
    parser.add_argument(
        "pack",
        nargs="?",
        help="Pack JSON path. Default: stdin.",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Single-line JSON.",
    )
    args = parser.parse_args(argv)
    if args.pack:
        with open(args.pack, encoding="utf-8") as handle:
            payload = _load(handle)
    else:
        payload = _load(sys.stdin)
    ranked = rank_pack(payload, args.query)
    if args.compact:
        print(json.dumps(ranked, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(ranked, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
