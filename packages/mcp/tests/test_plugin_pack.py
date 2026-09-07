from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "clients" / "claude"


def test_marketplace_points_at_pack() -> None:
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    plugin = market["plugins"][0]
    assert plugin["source"] == "./clients/claude"
    assert plugin["version"] == "1.0.0"
    assert plugin.get("homepage") == "https://open-ux.dev"


def test_listing_assets_and_setup_exist() -> None:
    assets = PACK / "assets"
    for name in ("icon.svg", "hero.svg", "offerings.svg", "icon-512.png", "hero.png"):
        path = assets / name
        assert path.is_file(), name
        assert path.stat().st_size > 0
    assert (PACK / "SETUP.md").is_file()
    readme = (PACK / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# Open UX\n")
    assert "MCP" not in readme.split("\n", 1)[0]
    assert "https://open-ux.dev" in readme
    assert "claude plugin marketplace add 3dyonic/open-ux" in readme
    assert "assets/hero.svg" in readme


def test_host_mounts_are_symlinks_into_pack() -> None:
    mounts = (
        ROOT / ".cursor" / "skills" / "open-ux",
        ROOT / ".claude" / "skills" / "open-ux",
        ROOT / ".claude" / "agents" / "open-ux.md",
        ROOT / ".claude" / "commands" / "list.md",
        ROOT / ".claude" / "commands" / "get.md",
        ROOT / ".claude" / "commands" / "audit.md",
        ROOT / ".claude" / "commands" / "forms.md",
        ROOT / ".claude" / "commands" / "actions.md",
        ROOT / ".claude" / "commands" / "feedback.md",
    )
    pack = PACK.resolve()
    for path in mounts:
        assert path.is_symlink(), path
        resolved = path.resolve()
        assert resolved.exists(), path
        assert pack in resolved.parents or resolved == pack or pack in resolved.parents
        assert str(resolved).startswith(str(pack))
