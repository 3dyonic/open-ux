#!/usr/bin/env python3
"""Fetch one Situation Card or one guideline by id."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

import _mcp  # noqa: E402


def looks_like_guideline_id(raw: str) -> bool:
    # Cards / containers are snake_case tokens. Guideline ids always contain a dot.
    return "." in raw


def route(raw: str) -> tuple[str, dict]:
    wanted = raw.strip()
    if looks_like_guideline_id(wanted):
        return "get_guideline", {"id": wanted}
    return "get_situation", {"id": wanted}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="get.py",
        description="get_situation for a Card/container; get_guideline if the id has a dot.",
    )
    parser.add_argument("id", nargs="?", help="Card id, container alias, or guideline id.")
    args = parser.parse_args(argv)
    if not (args.id or "").strip():
        return _mcp.fail("pass a Card, container, or guideline id.")
    name, arguments = route(args.id.strip())
    return _mcp.main_call(name, arguments)


if __name__ == "__main__":
    raise SystemExit(main())
