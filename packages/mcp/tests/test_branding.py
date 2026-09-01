from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

from starlette.testclient import TestClient

from open_ux.server import create_mcp

ROOT = Path(__file__).resolve().parents[3]


def test_landing_h1_is_open_ux(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        html = client.get("/").text
        assert "<h1>Open UX</h1>" in html
        h1 = html.split("<h1>", 1)[1].split("</h1>", 1)[0]
        assert "MCP" not in h1
        assert "Cited UX rules agents audit against" in html


def test_plugin_title_is_open_ux() -> None:
    plugin = json.loads(
        (ROOT / "clients/claude/.claude-plugin/plugin.json").read_text(encoding="utf-8")
    )
    assert plugin["displayName"] == "Open UX"
    assert "MCP" not in plugin["displayName"]
    assert "MCP" not in plugin["name"]
    assert "MCP" not in plugin.get("description", "")


def test_readme_embeds_relative_hero_and_landing() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# Open UX\n")
    assert "MCP" not in readme.split("\n", 1)[0]
    assert "![Open UX: catalog to audit flow](docs/readme-hero.svg)" in readme
    assert "[docs/LANDING.md](docs/LANDING.md)" in readme
    assert "pip install -e \"packages/mcp[dev]\"" in readme
    assert "python -m pytest" in readme


def test_designer_landing_craft_is_not_a_stub() -> None:
    landing = (ROOT / "docs/LANDING.md").read_text(encoding="utf-8")
    assert landing.startswith("# Open UX — landing craft (v1)\n")
    assert "STUB" not in landing.upper()
    assert "placeholder for designer" not in landing.lower()
    assert "## Claude plugin card" in landing
    assert "## Footer / trust" in landing
    assert "**H1:** Open UX" in landing
    assert "**Subtitle:** Cited UX rules agents audit against" in landing


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
    assert "Verdict" in text
    assert "Cited UX rules agents audit against" in text
