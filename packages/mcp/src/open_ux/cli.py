"""Product CLI: cards, get, audit, cite, tools — plus existing server modes."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import TextIO

from open_ux import __version__
from open_ux.client import McpError, call_tool, list_tools
from open_ux.jobs import CARD_IDS, CONTAINER_IDS, DEFAULT_LIMIT, JOB_ALIASES

BANNED_AUDIT_FLAGS = ("--file", "--content", "--target", "--verdict", "--upload")
KNOWN_NEEDS = CARD_IDS + CONTAINER_IDS + JOB_ALIASES
SERVER_MODES = ("stdio", "http", "validate-catalog", "approve-invite")

EPILOG = """\
examples:
  open-ux cards
  open-ux get design_a_form
  open-ux audit --jobs design_a_form
  open-ux cite forms.field_labels.visible_label
  open-ux tools list
  python -m open_ux stdio
  OPEN_UX_MODE=hosted python -m open_ux http
"""


def _use_color(*, no_color: bool, stream: TextIO) -> bool:
    if no_color or os.environ.get("NO_COLOR"):
        return False
    return stream.isatty()


def _err(message: str, *, color: bool) -> None:
    if color:
        print(f"\033[31m{message}\033[0m", file=sys.stderr)
    else:
        print(message, file=sys.stderr)


def _dump(payload: object, *, compact: bool) -> None:
    if compact:
        print(json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":")))
        return
    print(json.dumps(payload, indent=2, ensure_ascii=False, default=str))


def _known_needs_hint() -> str:
    cards = ", ".join(CARD_IDS)
    aliases = ", ".join(JOB_ALIASES)
    return f"known Cards: {cards}\naliases: {aliases}"


def _validate_need(need: str) -> str | None:
    job = need.strip()
    if job in KNOWN_NEEDS:
        return None
    return f"unknown Card or container {job!r}.\n{_known_needs_hint()}"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="open-ux",
        description=(
            "Open UX — cited UX criteria via the same wire as Open-UX:* tools. "
            "No file. No host pass or fail."
        ),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"open-ux {__version__}",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Print JSON on one line.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Never color stderr.",
    )
    parser.add_argument(
        "--transport",
        choices=("http", "stdio", "inprocess"),
        help="Override OPEN_UX_TRANSPORT (default: http if OPEN_UX_API_KEY, else inprocess).",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("HOST", "0.0.0.0"),
        help="HTTP bind host (http mode).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", os.environ.get("OPEN_UX_PORT", "8080"))),
        help="HTTP bind port (http mode).",
    )
    sub = parser.add_subparsers(dest="command")

    cards = sub.add_parser("cards", help="list_situations — Card index")
    cards.add_argument("--container", help="Optional container id or alias.")

    getter = sub.add_parser("get", help="get_situation — one Card")
    getter.add_argument("card_id", help="Situation Card id.")

    audit = sub.add_parser(
        "audit",
        help="Open-UX:audit — cited pack",
        epilog=_known_needs_hint(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    audit.add_argument(
        "--jobs",
        help="Situation Card id or container alias (forms / actions / feedback).",
    )
    audit.add_argument(
        "--guideline-ids",
        nargs="+",
        metavar="ID",
        help="Known guideline ids. Prefer a Card on --jobs when composing.",
    )
    audit.add_argument("--query", help="Optional text filter inside the pack.")
    audit.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Max rows (default {DEFAULT_LIMIT}).",
    )

    cite = sub.add_parser("cite", help="get_guideline — one cited body")
    cite.add_argument("guideline_id", help="Guideline id.")

    tools = sub.add_parser("tools", help="tools/list and tools/call")
    tools_sub = tools.add_subparsers(dest="tools_cmd")
    tools_sub.add_parser("list", help="tools/list")
    tools_call = tools_sub.add_parser("call", help="tools/call")
    tools_call.add_argument("name", help="Tool name.")
    tools_call.add_argument(
        "arguments",
        nargs="?",
        default="{}",
        help='JSON object of arguments, e.g. \'{"jobs":"design_a_form"}\'.',
    )

    sub.add_parser("stdio", help="Run the local MCP server on stdio.")
    sub.add_parser("http", help="Run the HTTP server.")
    sub.add_parser("validate-catalog", help="Load and check the catalog.")
    invite = sub.add_parser("approve-invite", help="Issue an invite token.")
    invite.add_argument("email", nargs="?", default="")
    return parser


def _run_server(command: str, args: argparse.Namespace) -> int:
    if command == "validate-catalog":
        from open_ux.catalog import load_catalog

        catalog = load_catalog()
        print(
            f"catalog ok guidelines={len(catalog.guidelines)} bytes={catalog.size_bytes}"
        )
        return 0

    if command == "approve-invite":
        email = getattr(args, "email", "") or ""
        if not email:
            print("usage: open-ux approve-invite EMAIL", file=sys.stderr)
            return 2
        from open_ux.auth import AuthError, approve_invite

        try:
            issued = approve_invite(email)
        except AuthError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(
            json.dumps(
                {
                    "email": issued.email,
                    "token": issued.token,
                    "token_prefix": "inv_",
                    "redeem_url": issued.redeem_url,
                    "expires_at": issued.expires_at,
                },
                indent=2,
            )
        )
        return 0

    if command == "stdio":
        from open_ux.server import create_mcp

        create_mcp(hosted=False).run(transport="stdio")
        return 0

    from open_ux.http_app import serve_http

    serve_http(host=args.host, port=args.port)
    return 0


def _tool_payload(
    command: str,
    args: argparse.Namespace,
    *,
    color: bool,
) -> tuple[str, dict[str, object]] | int:
    if command == "cards":
        payload: dict[str, object] = {}
        if args.container:
            payload["container"] = args.container
        return "list_situations", payload
    if command == "get":
        hint = _validate_need(args.card_id)
        if hint:
            _err(hint, color=color)
            return 2
        return "get_situation", {"id": args.card_id}
    if command == "audit":
        if not args.jobs and not args.guideline_ids:
            _err("requires --jobs or --guideline-ids", color=color)
            return 2
        if args.jobs:
            hint = _validate_need(args.jobs)
            if hint:
                _err(hint, color=color)
                return 2
        body: dict[str, object] = {}
        if args.jobs:
            body["jobs"] = args.jobs
        if args.guideline_ids:
            body["guideline_ids"] = args.guideline_ids
        if args.query:
            body["query"] = args.query
        body["limit"] = args.limit
        return "audit", body
    if command == "cite":
        return "get_guideline", {"id": args.guideline_id}
    if command == "tools":
        if args.tools_cmd == "list":
            return "list", {}
        if args.tools_cmd == "call":
            try:
                arguments = json.loads(args.arguments) if args.arguments else {}
            except json.JSONDecodeError as exc:
                _err(f"arguments must be JSON: {exc}", color=color)
                return 2
            if not isinstance(arguments, dict):
                _err("arguments must be a JSON object", color=color)
                return 2
            return args.name, arguments
        _err("usage: open-ux tools list|call", color=color)
        return 2
    _err(f"unknown command {command!r}", color=color)
    return 2


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if any(flag in raw for flag in BANNED_AUDIT_FLAGS) and (
        not raw or raw[0] == "audit" or "--jobs" in raw or "--guideline-ids" in raw
    ):
        print(
            "audit accepts --jobs or --guideline-ids only "
            "(no file, no content, no target, no verdict)",
            file=sys.stderr,
        )
        return 2

    parser = _build_parser()
    args = parser.parse_args(raw)
    color = _use_color(no_color=args.no_color, stream=sys.stderr)
    command = args.command or os.environ.get("OPEN_UX_MODE") or "stdio"

    if command in SERVER_MODES:
        return _run_server(command, args)

    called = _tool_payload(command, args, color=color)
    if isinstance(called, int):
        return called
    name, arguments = called
    try:
        if name == "list":
            payload = list_tools(transport=args.transport)
        else:
            payload = call_tool(name, arguments, transport=args.transport)
    except McpError as exc:
        _err(str(exc), color=color)
        return 1
    _dump(payload, compact=args.compact)
    return 0
