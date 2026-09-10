from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "helpers" / "registry.json"
HELPERS = ROOT / "helpers"


def test_registry_splits_agent_helpers_and_contributor_wire() -> None:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    agent = data["agent_helpers"]
    contrib = data["contributor_wire"]
    assert len(agent) == 1
    assert agent[0]["id"] == "rank_pack"
    assert {row["id"] for row in contrib} == {"pack", "mcp_call", "get_component"}
    for row in agent + contrib:
        path = ROOT / row["path"]
        assert path.is_file(), row["path"]
        assert row["path"].startswith("helpers/")
        assert "summary" in row
        assert "usage" in row
    assert "not the agent skill path" in contrib[0]["summary"].lower()


def test_scripts_dir_has_no_agent_helpers() -> None:
    for name in ("pack.py", "rank_pack.py", "mcp_call.py", "get_component.py"):
        assert not (ROOT / "scripts" / name).exists()
