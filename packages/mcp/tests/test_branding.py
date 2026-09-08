from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_plugin_title_is_open_ux() -> None:
    plugin = json.loads(
        (ROOT / "clients/claude/.claude-plugin/plugin.json").read_text(encoding="utf-8")
    )
    assert plugin["displayName"] == "Open UX"
    assert "MCP" not in plugin["displayName"]
    assert "MCP" not in plugin["name"]
    assert "MCP" not in plugin.get("description", "")


def test_readme_embeds_relative_hero() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# Open UX\n")
    assert "MCP" not in readme.split("\n", 1)[0]
    assert "![Open UX](docs/readme-hero.svg)" in readme
    assert "[docs/LANDING.md](docs/LANDING.md)" not in readme
    assert "pip install open-ux" in readme
    assert "python -m open_ux stdio" in readme
    assert "OPEN_UX_MODE=hosted python -m open_ux http" in readme
    assert "pip install -e \"packages/mcp[dev]\"" in readme
    assert readme.index("pip install open-ux") < readme.index(
        "pip install -e \"packages/mcp[dev]\""
    )
    assert "python -m pytest" in readme
    assert "open-ux.dev" in readme
    assert "list_guidelines" in readme
    assert "[MIT](LICENSE)" in readme
    assert "UNS-" not in readme
    assert "Apple HIG" not in readme


def test_designer_landing_craft_is_not_in_the_public_repo() -> None:
    assert not (ROOT / "docs/LANDING.md").exists()


def test_readme_hero_svg_is_parseable_and_complete() -> None:
    path = ROOT / "docs/readme-hero.svg"
    raw = path.read_bytes()
    assert raw, "docs/readme-hero.svg must be committed and non-empty"
    text = raw.decode("utf-8")
    assert "Â·" not in text
    assert "forms.field_labels&" not in text
    assert 'aria-label="Open UX: catalog to audit flow"' in text
    root = ET.fromstring(text)
    assert root.tag.endswith("svg")
    assert root.get("width") == "1280"
    assert root.get("height") == "420"
    assert "Catalog" in text
    assert "Agent tools" in text
    assert "Criteria" in text
    assert "Pip" in text or "pipReadme" in text
    assert "Verdict" not in text
    assert "Pass / fail" not in text
    assert "Cited UX rules agents audit against" in text
    assert "#FF4B00" in text
    assert "#F9F6F2" in text
