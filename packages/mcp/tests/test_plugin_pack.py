from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "clients" / "claude"
PLACEHOLDER = re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}")


def test_marketplace_points_at_pack() -> None:
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    plugin = market["plugins"][0]
    assert plugin["source"] == "./clients/claude"
    assert plugin["version"] == "1.1.0"
    assert plugin.get("homepage") == "https://open-ux.dev"


def test_cursor_marketplace_points_at_same_pack() -> None:
    market = json.loads((ROOT / ".cursor-plugin" / "marketplace.json").read_text())
    plugin = market["plugins"][0]
    assert plugin["source"] == "./clients/claude"
    assert plugin["version"] == "1.1.0"
    assert plugin.get("homepage") == "https://open-ux.dev"
    assert plugin.get("logo") == "assets/icon.svg"
    assert ".." not in plugin["source"]


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
    assert "assets/icon.svg" in readme
    assert "assets/offerings.svg" in readme
    assert "cursor.com/marketplace/publish" in readme
    assert "OPEN_UX_API_KEY" in readme
    assert "Not listed yet." in readme
    assert "not published" in readme.lower()


def test_host_mounts_are_symlinks_into_pack() -> None:
    mounts = (
        ROOT / ".cursor" / "skills" / "open-ux",
        ROOT / ".cursor" / "rules" / "open-ux.mdc",
        ROOT / ".claude" / "skills" / "open-ux",
        ROOT / ".claude" / "agents" / "open-ux.md",
        ROOT / ".claude" / "commands" / "list.md",
        ROOT / ".claude" / "commands" / "get.md",
        ROOT / ".claude" / "commands" / "pack.md",
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


def test_cursor_pack_uses_variables_not_user_config() -> None:
    plugin = json.loads((PACK / ".cursor-plugin" / "plugin.json").read_text())
    mcp = json.loads((PACK / "mcp.json").read_text())
    assert plugin["name"] == "open-ux"
    assert "MCP" not in plugin["name"]
    assert "MCP" not in plugin.get("description", "")
    assert plugin.get("logo") == "assets/icon.svg"
    assert plugin.get("homepage") == "https://open-ux.dev"
    assert "userConfig" not in plugin
    assert "hooks" not in plugin
    assert not (PACK / "hooks").exists()
    schema = plugin["variables"]
    assert schema["type"] == "object"
    assert "OPEN_UX_API_KEY" in schema["properties"]
    assert "OPEN_UX_API_KEY" in schema["required"]
    server = mcp["mcpServers"]["open-ux"]
    assert server["url"] == "https://open-ux.dev/mcp"
    assert server["headers"]["Authorization"] == "Bearer ${OPEN_UX_API_KEY}"
    declared = set(schema["properties"])
    used = set(PLACEHOLDER.findall(json.dumps(mcp)))
    assert used <= declared
    assert ".." not in plugin["logo"]
    rule = (PACK / "rules" / "open-ux.mdc").read_text(encoding="utf-8")
    assert "alwaysApply: true" in rule
    assert "Open-UX:pack" in rule
    assert "pass_when" not in rule
