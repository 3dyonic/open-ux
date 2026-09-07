#!/usr/bin/env python3
"""Required audit runner. Hosts must execute this file — do not improvise the wire.

Wire: --jobs or --guideline-ids only. Criteria pack via open_ux.audit.audit
(the same helper as the Open-UX:audit MCP tool). No file. No host pass or fail.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[5]
_SRC = _REPO / "packages" / "mcp" / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_BANNED = ("--file", "--content", "--target", "--verdict", "--upload")


def run_audit(*, jobs: str | None = None, guideline_ids: list[str] | None = None) -> dict[str, Any]:
    from open_ux.audit import audit
    from open_ux.catalog import load_catalog
    from open_ux.settings import Settings

    return audit(load_catalog(Settings.load()), jobs=jobs, guideline_ids=guideline_ids or None)


def main(argv: list[str] | None = None) -> int:
    raw = list(argv if argv is not None else sys.argv[1:])
    if any(flag in raw for flag in _BANNED):
        print(
            "audit accepts --jobs or --guideline-ids only (no file, no content, no target, no verdict)",
            file=sys.stderr,
        )
        return 2

    parser = argparse.ArgumentParser(description="Run an Open-UX audit (criteria pack, no host pass or fail).")
    parser.add_argument("--jobs", help="Card id or container alias (jobs=).")
    parser.add_argument("--guideline-ids", help="Comma-separated guideline ids.")
    args = parser.parse_args(raw)

    jobs = (args.jobs or "").strip() or None
    guideline_ids = [p.strip() for p in (args.guideline_ids or "").split(",") if p.strip()] or None
    if not jobs and not guideline_ids:
        print("audit requires --jobs or --guideline-ids", file=sys.stderr)
        return 2

    print(json.dumps(run_audit(jobs=jobs, guideline_ids=guideline_ids), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
