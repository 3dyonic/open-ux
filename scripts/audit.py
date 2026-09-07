#!/usr/bin/env python3
"""Thin audit helper: jobs= or guideline_ids in, criteria pack out.

Same tight wire as Open-UX:audit. Pack only. No file. No host pass or fail.

Available and preferred when composing or reviewing so you do not invent
args. Not required — Open-UX:audit stays first-class.

Usage (from repo root, after ``pip install open-ux`` or an editable install):

    python3 scripts/audit.py --jobs design_a_form
    python3 scripts/audit.py --guideline-ids forms.field_labels.visible_label
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "packages" / "mcp" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from open_ux.audit import audit  # noqa: E402
from open_ux.catalog import load_catalog  # noqa: E402
from open_ux.jobs import DEFAULT_LIMIT  # noqa: E402
from open_ux.settings import Settings  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts/audit.py",
        description=(
            "Fetch a cited UX criteria pack. Pass --jobs or --guideline-ids. "
            "No file. No host pass or fail."
        ),
    )
    parser.add_argument(
        "--jobs",
        help="Situation Card id or container alias (forms / actions / feedback).",
    )
    parser.add_argument(
        "--guideline-ids",
        nargs="+",
        metavar="ID",
        help="Known guideline ids. Prefer a Card on --jobs when composing.",
    )
    parser.add_argument("--query", help="Optional text filter inside the pack.")
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Max rows (default {DEFAULT_LIMIT}).",
    )
    args = parser.parse_args(argv)

    if not args.jobs and not args.guideline_ids:
        parser.error("requires --jobs or --guideline-ids")

    result = audit(
        load_catalog(Settings.load()),
        jobs=args.jobs,
        guideline_ids=args.guideline_ids,
        query=args.query,
        limit=args.limit,
    )
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
