#!/usr/bin/env python3
"""Index only: Situation Cards and/or a paged guideline list."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_DIR = Path(__file__).resolve().parent
if str(_DIR) not in sys.path:
    sys.path.insert(0, str(_DIR))

import _mcp  # noqa: E402

CONTAINER_TOKENS = frozenset(
    {
        "forms",
        "actions",
        "feedback",
        "forms_and_input",
        "actions_and_decisions",
        "feedback_and_status",
        "navigation_and_wayfinding",
        "layout_and_data_display",
        "overlays_and_content_structure",
        "multi_step_flows",
    }
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="list.py",
        description="Print Situation Card and/or guideline index JSON. Never dumps bodies.",
    )
    parser.add_argument(
        "container",
        nargs="?",
        help="Optional container alias (forms / actions / feedback) for Cards.",
    )
    parser.add_argument(
        "--situations",
        action="store_true",
        help="List Situation Cards (default when --guidelines is omitted).",
    )
    parser.add_argument(
        "--guidelines",
        action="store_true",
        help="List the paged guideline index (no rule bodies).",
    )
    parser.add_argument("--container", dest="container_flag", help="Container filter for Cards.")
    parser.add_argument("--query", help="Search the guideline index (search_guidelines).")
    parser.add_argument("--limit", type=int, help="Page size.")
    parser.add_argument("--offset", type=int, default=0, help="Page offset.")
    args = parser.parse_args(argv)

    container = (args.container_flag or args.container or "").strip() or None
    if container and container not in CONTAINER_TOKENS and "." in container:
        return _mcp.fail("list is an index. Use get.py for a guideline id.")

    want_guidelines = bool(args.guidelines or args.query)
    want_situations = bool(args.situations) or not want_guidelines
    if args.situations and not args.guidelines and not args.query:
        want_guidelines = False

    payload: dict = {}
    try:
        if want_situations:
            sit_args: dict = {"offset": args.offset}
            if container:
                sit_args["container"] = container
            if args.limit is not None:
                sit_args["limit"] = args.limit
            payload["situations"] = _mcp.call_tool("list_situations", sit_args)
        if want_guidelines:
            guide_args: dict = {"offset": args.offset}
            if args.limit is not None:
                guide_args["limit"] = args.limit
            if args.query:
                guide_args["query"] = args.query
            tool = "search_guidelines" if args.query else "list_guidelines"
            payload["guidelines"] = _mcp.call_tool(tool, guide_args)
    except _mcp.McpError as exc:
        _mcp.dump({"error": str(exc)})
        return 1

    if want_situations and not want_guidelines:
        _mcp.dump(payload["situations"])
    elif want_guidelines and not want_situations:
        _mcp.dump(payload["guidelines"])
    else:
        _mcp.dump(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
