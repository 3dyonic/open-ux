#!/usr/bin/env python3
"""Repo shim — same as ``open-ux rank-pack`` (ships with pip).

LLM-local: run after Open-UX:pack returns a page. Not a substitute for pack.

    open-ux rank-pack --query "delete confirm" < pack.json
    python3 helpers/rank_pack.py --query "delete confirm" < pack.json
"""

from __future__ import annotations

import sys

from open_ux.rank_pack_cmd import run_rank_pack


def main(argv: list[str] | None = None) -> int:
    return run_rank_pack(list(sys.argv[1:] if argv is None else argv))


if __name__ == "__main__":
    raise SystemExit(main())
