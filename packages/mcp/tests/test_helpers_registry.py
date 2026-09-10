from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "helpers" / "registry.json"
HELPERS = ROOT / "helpers"


def test_registry_lists_agent_helpers_only() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = data["helpers"]
    assert len(rows) == 4
    ids = {row["id"] for row in rows}
    assert ids == {"pack", "rank_pack", "mcp_call", "get_component"}
    for row in rows:
        path = ROOT / row["path"]
        assert path.is_file(), row["path"]
        assert row["path"].startswith("helpers/")
        assert "summary" in row
        assert "usage" in row


def test_scripts_dir_has_no_agent_helpers() -> None:
    for name in ("pack.py", "rank_pack.py", "mcp_call.py", "get_component.py"):
        assert not (ROOT / "scripts" / name).exists()
