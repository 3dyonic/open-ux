#!/usr/bin/env python3
"""Thin get_component helper: widget id in, record out.

Same wire as Open-UX:get_component. Section switches mirror the MCP tool.

Available, not required — Open-UX:get_component stays first-class.

Usage (from repo root, after ``pip install open-ux`` or an editable install):

    python3 helpers/get_component.py button
    python3 helpers/get_component.py button --include-used-on
    open-ux component button --include-used-on
"""

from __future__ import annotations

import sys

from open_ux.cli import main as cli_main


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    return cli_main(["component", *raw])


if __name__ == "__main__":
    raise SystemExit(main())
