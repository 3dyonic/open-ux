from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STAMP = ROOT / "scripts" / "apply_stamped_catalog.py"


def test_stamp_script_fails_closed_without_rewrite_tree() -> None:
    result = subprocess.run(
        [sys.executable, str(STAMP)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "--rewrite-tree" in result.stderr


def test_stamp_script_rewrite_tree_still_needs_csv() -> None:
    result = subprocess.run(
        [sys.executable, str(STAMP), "--rewrite-tree"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "consolidated-309.csv" in result.stderr
