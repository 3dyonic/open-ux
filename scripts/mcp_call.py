#!/usr/bin/env python3
"""Optional: tools/list and tools/call without a Claude session.

Not the skill path. In Claude, call Open-UX:* tools from the plugin MCP.

Usage (from repo root, after ``pip install open-ux`` or an editable install):

    python3 scripts/mcp_call.py list
    python3 scripts/mcp_call.py audit '{"jobs":"design_a_form"}'
    open-ux tools list
    open-ux tools call audit '{"jobs":"design_a_form"}'
"""

from __future__ import annotations

import sys

from open_ux.cli import main as cli_main


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    if not raw:
        return cli_main(["tools", "list"])
    tool, *rest = raw
    if tool in {"list", "tools/list"}:
        return cli_main(["tools", "list", *rest])
    return cli_main(["tools", "call", tool, *rest])


if __name__ == "__main__":
    raise SystemExit(main())
