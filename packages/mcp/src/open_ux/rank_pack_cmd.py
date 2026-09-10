"""LLM-local BM25 reorder of one pack page — ships with pip as ``open-ux rank-pack``."""

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
        raise SystemExit("rank-pack: expected a pack object with guidelines, or a list of cites.")
    return raw


def run_rank_pack(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="open-ux rank-pack",
        description=(
            "Reorder one pack page after Open-UX:pack. LLM-local; host does not rank. "
            "No winner. Fail-open."
        ),
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
