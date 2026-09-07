#!/usr/bin/env python3
"""Fetch the cited criteria pack for a Card/container or known guideline ids.

Never takes a file. Never scores. Never invents a rule.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

import _mcp  # noqa: E402

BANNED_FLAGS = (
    "--file",
    "--content",
    "--target",
    "--scan",
    "--html",
    "--markup",
    "--screenshot",
    "--verdict",
)
FILE_SUFFIXES = (".html", ".htm", ".tsx", ".jsx", ".vue", ".svg", ".png", ".jpg", ".fig")


def _looks_like_file(raw: str) -> bool:
    if raw.startswith("jobs=") or raw.startswith("guideline_ids="):
        return False
    if raw.startswith("-"):
        return False
    if os.path.isfile(raw):
        return True
    return raw.lower().endswith(FILE_SUFFIXES)


def _split_ids(raw: str) -> list[str]:
    return [part.strip() for part in raw.replace(",", " ").split() if part.strip()]


def parse_args(argv: list[str] | None) -> argparse.Namespace | str:
    argv = list(sys.argv[1:] if argv is None else argv)
    for flag in BANNED_FLAGS:
        if flag in argv:
            return (
                "audit never takes a file and never scores. "
                "Pass jobs=<card_id> or --guideline-ids."
            )
    for raw in argv:
        if _looks_like_file(raw):
            return (
                "audit never takes a file. "
                "Pass jobs=<card_id> or --guideline-ids."
            )

    parser = argparse.ArgumentParser(
        prog="audit.py",
        description="Print the Open UX criteria pack JSON for a Card or guideline ids.",
    )
    parser.add_argument(
        "need",
        nargs="?",
        help="Card / container, or jobs=<card_id>",
    )
    parser.add_argument(
        "--jobs",
        dest="jobs_flag",
        help="Situation Card or container alias (forms / actions / feedback).",
    )
    parser.add_argument(
        "--guideline-ids",
        dest="guideline_ids",
        help="Comma or space separated ids already known from get/list.",
    )
    parser.add_argument("--query", help="Optional words to narrow within that job.")
    parser.add_argument("--limit", type=int, help="Max rules to return (server default 10).")
    args = parser.parse_args(argv)

    jobs = args.jobs_flag
    guideline_ids = _split_ids(args.guideline_ids or "")
    need = (args.need or "").strip()
    if need.startswith("jobs="):
        jobs = need.split("=", 1)[1].strip() or jobs
    elif need.startswith("guideline_ids="):
        guideline_ids.extend(_split_ids(need.split("=", 1)[1]))
    elif need:
        jobs = need

    args.jobs = jobs
    args.ids = guideline_ids
    return args


def main(argv: list[str] | None = None) -> int:
    parsed = parse_args(argv)
    if isinstance(parsed, str):
        return _mcp.fail(parsed)
    if not parsed.jobs and not parsed.ids:
        return _mcp.fail("audit requires jobs=<card_id> or --guideline-ids.")
    arguments: dict = {}
    if parsed.jobs:
        arguments["jobs"] = parsed.jobs
    if parsed.ids:
        arguments["guideline_ids"] = parsed.ids
    if parsed.query:
        arguments["query"] = parsed.query
    if parsed.limit is not None:
        arguments["limit"] = parsed.limit
    return _mcp.main_call("audit", arguments)


if __name__ == "__main__":
    raise SystemExit(main())
