#!/usr/bin/env python3
"""Thin audit helper: jobs= or guideline_ids in, cited criteria out.

Same tight wire as Open-UX:audit. No file. No host pass or fail.
Cited criteria help you decide; the decision is yours.

Available, not required — Open-UX:audit stays first-class. Your choice.

Usage (from repo root, after ``pip install open-ux`` or an editable install):

    python3 scripts/audit.py --jobs design_a_form
    python3 scripts/audit.py --guideline-ids forms.field_labels.visible_label
    open-ux audit --jobs design_a_form
"""

from __future__ import annotations

import sys

from open_ux.cli import main as cli_main


def main(argv: list[str] | None = None) -> int:
    raw = list(sys.argv[1:] if argv is None else argv)
    return cli_main(["audit", *raw])


if __name__ == "__main__":
    raise SystemExit(main())
