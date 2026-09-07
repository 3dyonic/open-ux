from __future__ import annotations

import json
import re
from pathlib import Path

from open_ux.jobs import CARD_IDS

ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = ROOT / "clients" / "claude" / "skills" / "open-ux"
SKILL = SKILL_DIR / "SKILL.md"
COMMANDS = ROOT / "clients" / "claude" / "commands"
PLUGIN = ROOT / "clients" / "claude" / ".claude-plugin" / "plugin.json"
MCP_JSON = ROOT / "clients" / "claude" / ".mcp.json"
AGENT = ROOT / "clients" / "claude" / "agents" / "open-ux.md"
BANNED_BODIES = ("pass_when", "fail_when")
# Catalog ids look like `forms.labels.clickable` — not URLs, not `jobs=`.
GUIDELINE_ID = re.compile(r"`[a-z]+(?:\.[a-z0-9_-]+){1,}`")


def _frontmatter_description(text: str) -> str:
    _empty, meta, _rest = text.split("---", 2)
    desc = meta.split("description:", 1)[1]
    return " ".join(desc.replace(">-", "").split())


def _skill_files() -> list[Path]:
    return sorted(SKILL_DIR.glob("*.md"))


def test_one_skill_package_named_open_ux() -> None:
    skills_root = ROOT / "clients" / "claude" / "skills"
    packages = [p.name for p in skills_root.iterdir() if p.is_dir()]
    assert packages == ["open-ux"]
    assert (skills_root / "open-ux" / "SKILL.md").is_file()
    for banned in ("open-ux-forms", "open-ux-actions", "open-ux-feedback"):
        assert not (skills_root / banned).exists()


def test_skill_description_compose_review_trigger() -> None:
    text = SKILL.read_text(encoding="utf-8")
    desc = _frontmatter_description(text)
    assert len(desc) <= 1024
    assert "building or checking UI" in desc
    assert "form" in desc.lower()
    assert "Open-UX:get_situation" in desc
    assert "Open-UX:audit" in desc
    assert "jobs=<card_id>" in desc
    assert "target" not in desc
    assert "verdict" not in desc
    assert "Open-UX:suggest_situations" in desc
    assert "Open-UX:search_guidelines" in desc or "Open-UX:get_guideline" in desc


def test_skill_routing_table_has_when_and_cross_container_reject() -> None:
    text = SKILL.read_text(encoding="utf-8")
    _empty, _meta, body = text.split("---", 2)
    assert "MANIFEST.md" in body
    assert "pass_when" not in body
    assert "forms.field_labels" not in body
    for card_id in CARD_IDS:
        assert f"`{card_id}`" in body
    for title in (
        "Forms & input",
        "Actions & decisions",
        "Feedback & status",
        "Navigation & wayfinding",
        "Layout & data display",
        "Overlays & content structure",
        "Multi-step flows",
    ):
        assert title in body
    assert "`forms`" in body and "`actions`" in body and "`feedback`" in body
    assert "handle_form_errors" in body
    assert "build_a_multi_step_flow" in body
    assert "design_actions_and_ctas" in body
    assert "Field labels stay `design_a_form`" in body
    assert "jobs=" in body
    assert "verdict" not in body


def test_skill_files_point_at_tools_not_catalog_bodies() -> None:
    for path in _skill_files():
        text = path.read_text(encoding="utf-8")
        for token in BANNED_BODIES:
            assert token not in text, f"{path.name} must not contain {token}"
        leaked = GUIDELINE_ID.findall(text)
        assert leaked == [], f"{path.name} must not embed guideline ids {leaked}"


def test_plugin_points_at_hosted_mcp() -> None:
    plugin = json.loads(PLUGIN.read_text(encoding="utf-8"))
    mcp = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    assert plugin["name"] == "open-ux"
    assert plugin["displayName"] == "Open UX"
    assert "MCP" not in plugin["displayName"]
    server = mcp["mcpServers"]["open-ux"]
    assert server["url"] == "https://open-ux.dev/mcp"
    assert "OPEN_UX_API_KEY" in server["headers"]["Authorization"]


def test_commands_are_thin_and_never_verdict_or_file() -> None:
    names = {"list.md", "get.md", "audit.md", "forms.md", "actions.md", "feedback.md"}
    found = {p.name for p in COMMANDS.glob("*.md")}
    assert names <= found
    for path in COMMANDS.glob("*.md"):
        text = path.read_text(encoding="utf-8").lower()
        assert "verdict" not in text
        assert "pass/fail" not in text
        assert "upload" not in text
        assert "send a file" in text or "not ask for a file" in text or "do not send a file" in text
        for token in BANNED_BODIES:
            assert token not in text


def test_pointer_docs_exist_and_stay_thin() -> None:
    for path in (ROOT / "AGENTS.md", ROOT / "CLAUDE.md", AGENT):
        text = path.read_text(encoding="utf-8")
        assert path.is_file()
        assert len(text) < 4000
        assert "https://open-ux.dev/mcp" in text
        assert "jobs=" in text
        assert "uxmcp_" in text or "OPEN_UX_API_KEY" in text
        assert "pass_when" not in text
        assert "forms.field_labels" not in text
        for card_id in CARD_IDS:
            # Root pointers must not duplicate the full routing table.
            if path.name in {"AGENTS.md", "CLAUDE.md"}:
                assert card_id not in text
    assert not (COMMANDS / "critique.md").exists()


def test_connect_offers_hosted_or_package() -> None:
    paths = (
        SKILL,
        ROOT / "AGENTS.md",
        ROOT / "CLAUDE.md",
        ROOT / "clients" / "claude" / "README.md",
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "https://open-ux.dev/mcp" in text
        assert "github.com/3dyonic/open-ux" in text
        assert "python -m open_ux stdio" in text
        assert "download" in text.lower() or "package" in text.lower()
