from __future__ import annotations

import json
from pathlib import Path

from open_ux.helpers_registry import load_helpers_registry

ROOT = Path(__file__).resolve().parents[3]
REGISTRY = ROOT / "helpers" / "registry.json"
HELPERS = ROOT / "helpers"


def test_registry_splits_agent_helpers_and_contributor_wire() -> None:
    data = load_helpers_registry()
    agent = data["agent_helpers"]
    contrib = data["contributor_wire"]
    assert len(agent) == 1
    assert agent[0]["id"] == "rank_pack"
    assert agent[0]["cli"] == "open-ux rank-pack"
    assert {row["id"] for row in contrib} == {"pack", "mcp_call", "get_component"}
    for row in agent + contrib:
        assert row["cli"].startswith("open-ux")
        assert "resource" not in row
        assert "summary" in row
        assert "usage" in row
    assert "mcp_resources" not in data
    assert "pip install open-ux" in data["note"].lower()
    disk = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert data == disk


def test_cli_helpers_list(capsys) -> None:
    from open_ux.cli import main

    assert main(["helpers", "list"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["agent_helpers"][0]["cli"] == "open-ux rank-pack"


def test_scripts_dir_has_no_agent_helpers() -> None:
    for name in ("pack.py", "rank_pack.py", "mcp_call.py", "get_component.py"):
        assert not (ROOT / "scripts" / name).exists()


def test_bundled_registry_in_src_tree() -> None:
    bundled = (
        ROOT / "packages" / "mcp" / "src" / "open_ux" / "data" / "helpers" / "registry.json"
    )
    assert bundled.is_file()
    assert json.loads(bundled.read_text()) == json.loads(REGISTRY.read_text())
