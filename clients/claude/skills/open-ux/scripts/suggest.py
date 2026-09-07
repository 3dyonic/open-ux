#!/usr/bin/env python3
"""Rank Situation Cards from a vague task or pasted UI (map fallback)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

import _mcp  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="suggest.py",
        description="suggest_situations — ranking only. Surfaces are never ids.",
    )
    parser.add_argument("task_text", nargs="*", help="What you are composing, in task language.")
    parser.add_argument(
        "--surface",
        help="Optional page/flow context (home, cart, checkout). Ranking bias only.",
    )
    args = parser.parse_args(argv)
    text = " ".join(args.task_text).strip()
    if not text:
        return _mcp.fail("pass task text (a vague surface or pasted UI).")
    arguments: dict = {"task_text": text}
    if args.surface:
        arguments["surface"] = args.surface
    return _mcp.main_call("suggest_situations", arguments)


if __name__ == "__main__":
    raise SystemExit(main())
