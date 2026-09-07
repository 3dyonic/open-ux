#!/usr/bin/env python3
"""Repo-root wrapper. The required audit script is clients/claude/skills/open-ux/scripts/audit.py."""
from __future__ import annotations

import runpy
from pathlib import Path

runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "clients/claude/skills/open-ux/scripts/audit.py"),
    run_name="__main__",
)
