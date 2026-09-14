from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PACK = ROOT / "clients" / "plugin"
PLACEHOLDER = re.compile(r"\$\{([A-Z][A-Z0-9_]*)\}")


def test_marketplace_points_at_pack() -> None:
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    plugin = market["plugins"][0]
    assert plugin["source"] == "./clients/plugin"
    assert plugin["version"] == "1.2.1"
    assert plugin.get("homepage") == "https://open-ux.dev"


def test_cursor_marketplace_points_at_same_pack() -> None:
    market = json.loads((ROOT / ".cursor-plugin" / "marketplace.json").read_text())
    plugin = market["plugins"][0]
    assert plugin["source"] == "./clients/plugin"
    assert plugin["version"] == "1.2.1"
    assert market["metadata"]["version"] == "1.2.1"
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
    assert "OPEN_UX_API_KEY" in readme
    assert "public marketplaces yet" in readme
    assert "paused" not in readme.lower()
    assert "do not submit" not in readme.lower()
    assert "cursor.com/marketplace/publish" in readme
    assert "Listing submit" in readme


def _after_heading(text: str, heading: str) -> str:
    idx = text.find(heading)
    assert idx != -1, heading
    rest = text[idx + len(heading) :]
    next_heading = re.search(r"\n## ", rest)
    return rest if next_heading is None else rest[: next_heading.start()]


def test_plugin_docs_cover_cli_code_and_desktop_local_only() -> None:
    readme = (PACK / "README.md").read_text(encoding="utf-8")
    setup = (PACK / "SETUP.md").read_text(encoding="utf-8")
    assert "MCP" not in setup.split("\n", 1)[0]
    for text in (readme, setup):
        assert "claude plugin marketplace add 3dyonic/open-ux" in text
        assert "claude plugin install open-ux@open-ux" in text
        assert "api_key" in text
        assert "local plugins only" in text
        assert "cannot add a remote GitHub marketplace" in text
        assert "### Claude Cowork" not in text
        assert "## Claude Cowork" not in text
        assert "Claude Desktop (Chat)" not in text
        assert "Customize" not in text
        assert "public marketplaces yet" in text
        assert "paused" not in text.lower()
        assert "do not submit" not in text.lower()
        assert "not into mcp.json first" in text or "not mcp.json first" in text
        code = _after_heading(
            text, "### Claude Code" if "### Claude Code" in text else "## Claude Code"
        )
        assert "enable" in code.lower()
        assert "api_key" in code
        assert "local plugins only" in code
        advanced = _after_heading(text, "## Advanced / other clients")
        assert "mcp.json" in advanced
        assert "${user_config.api_key}" in advanced
        assert "https://open-ux.dev/mcp" in advanced
        assert "Authorization: Bearer" in advanced
        before_advanced = text[: text.find("## Advanced / other clients")]
        assert "Authorization: Bearer" not in before_advanced
        cursor = _after_heading(
            text, "### Cursor" if "### Cursor" in text else "## Cursor"
        )
        assert "OPEN_UX_API_KEY" in cursor
        assert "Plugins → Configure" in cursor


def test_host_mounts_are_symlinks_into_pack() -> None:
    mounts = (
        ROOT / ".cursor" / "skills" / "open-ux",
        ROOT / ".cursor" / "rules" / "open-ux.mdc",
        ROOT / ".claude" / "skills" / "open-ux",
        ROOT / ".claude" / "agents" / "open-ux.md",
    )
    command_mounts = (
        "list.md",
        "get.md",
        "pack.md",
        "forms.md",
        "actions.md",
        "feedback.md",
    )
    for name in command_mounts:
        assert not (ROOT / ".claude" / "commands" / name).exists(), name
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
    assert "First Open UX call" in rule
    assert "bare-invoke.md" in rule
    bare = (PACK / "skills" / "open-ux" / "bare-invoke.md").read_text(encoding="utf-8")
    reply = bare.split("## Verbatim reply", 1)[1]
    assert "Verbatim reply" in bare
    assert "every time" in bare
    assert "It helps you review and compose UI from evidence" in reply
    assert "How it guides me." in reply
    assert "Tools and helpers." in reply
    assert "Open-UX MCP tools" in reply
    assert "open-ux rank-pack" in reply
    assert "What's on screen, and what's bugging you?" in reply
    assert "with a task" not in reply.lower()
    assert "design systems" not in bare.lower()
    assert "Open-UX:pack" in rule
    assert "pass_when" not in rule
