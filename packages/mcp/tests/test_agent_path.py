from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from open_ux.jobs import CARD_IDS

ROOT = Path(__file__).resolve().parents[3]
SKILL_DIR = ROOT / "clients" / "claude" / "skills" / "open-ux"
SKILL = SKILL_DIR / "SKILL.md"
SKILL_AUDIT = SKILL_DIR / "scripts" / "audit.py"
COMMANDS = ROOT / "clients" / "claude" / "commands"
PLUGIN = ROOT / "clients" / "claude" / ".claude-plugin" / "plugin.json"
MCP_JSON = ROOT / "clients" / "claude" / ".mcp.json"
AGENT = ROOT / "clients" / "claude" / "agents" / "open-ux.md"
HELPER = ROOT / "scripts" / "mcp_call.py"
BANNED_BODIES = ("pass_when", "fail_when")
GUIDELINE_ID = re.compile(r"`[a-z]+(?:\.[a-z0-9_-]+){1,}`")
ALLOWED_SKILL_CLIS = {"audit.py"}
REQUIRE_AUDIT = ("audit.md", "forms.md", "actions.md", "feedback.md")
TOOL_ONLY = ("list.md", "get.md")


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
    assert SKILL_AUDIT.is_file()


def test_only_audit_script_is_a_skill_cli() -> None:
    scripts = SKILL_DIR / "scripts"
    assert scripts.is_dir()
    names = {p.name for p in scripts.iterdir() if p.is_file() and p.suffix == ".py"}
    extra = names - ALLOWED_SKILL_CLIS
    assert extra == set(), f"do not add a Python CLI per command: {sorted(extra)}"
    assert "audit.py" in names


def test_skill_description_requires_audit_script() -> None:
    text = SKILL.read_text(encoding="utf-8")
    desc = _frontmatter_description(text)
    assert len(desc) <= 1024
    assert "building or checking UI" in desc
    assert "Open-UX:get_situation" in desc
    assert "Open-UX:audit" in desc
    assert "jobs=<card_id>" in desc
    assert "scripts/audit.py" in desc
    assert "target" not in desc
    assert "verdict" not in desc


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
    assert "must run" in body.lower()
    assert "scripts/audit.py" in body
    assert "not a script" in body.lower()


def test_skill_compose_review_must_run_audit_script() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "must run" in text.lower()
    assert "scripts/audit.py" in text
    assert "`design_a_form`" in text
    assert "`protect_destructive_and_leave`" in text
    assert "Open-UX:suggest_situations" in text
    assert "Open-UX:get_guideline" in text
    assert "Open-UX:list_situations" in text
    assert "Open-UX:get_situation" in text


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


def test_audit_commands_must_run_the_script() -> None:
    names = {"list.md", "get.md", "audit.md", "forms.md", "actions.md", "feedback.md"}
    found = {p.name for p in COMMANDS.glob("*.md")}
    assert names <= found
    assert not (COMMANDS / "critique.md").exists()
    for name in REQUIRE_AUDIT:
        text = (COMMANDS / name).read_text(encoding="utf-8")
        lower = text.lower()
        assert "scripts/audit.py" in text
        assert "must" in lower
        assert "upload" not in lower
        assert "no file" in lower or "send a file" in lower
        for token in BANNED_BODIES:
            assert token not in text
    audit = (COMMANDS / "audit.md").read_text(encoding="utf-8")
    assert "--jobs" in audit or "jobs=" in audit
    assert "guideline_ids" in audit or "--guideline-ids" in audit


def test_list_and_get_stay_mcp_tools() -> None:
    for name in TOOL_ONLY:
        text = (COMMANDS / name).read_text(encoding="utf-8")
        lower = text.lower()
        assert "not a script" in lower
        assert "Open-UX:" in text
        assert "audit.py" not in text
        assert "must run" not in lower
        for token in BANNED_BODIES:
            assert token not in text
    listed = (COMMANDS / "list.md").read_text(encoding="utf-8")
    assert "Open-UX:list_situations" in listed
    got = (COMMANDS / "get.md").read_text(encoding="utf-8")
    assert "Open-UX:get_situation" in got


def test_pointer_docs_require_audit_script() -> None:
    for path in (ROOT / "AGENTS.md", ROOT / "CLAUDE.md", AGENT):
        text = path.read_text(encoding="utf-8")
        assert path.is_file()
        assert len(text) < 4000
        assert "https://open-ux.dev/mcp" in text
        assert "jobs=" in text
        assert "uxmcp_" in text or "OPEN_UX_API_KEY" in text
        assert "pass_when" not in text
        assert "forms.field_labels" not in text
        assert "scripts/audit.py" in text
        assert "must" in text.lower()
        for card_id in CARD_IDS:
            if path.name in {"AGENTS.md", "CLAUDE.md"}:
                assert card_id not in text
    assert not (COMMANDS / "critique.md").exists()


def test_audit_script_tight_wire(live_catalog: Path) -> None:
    env = {**os.environ}
    packed = subprocess.check_output(
        [sys.executable, str(SKILL_AUDIT), "--jobs", "design_a_form"],
        text=True,
        cwd=ROOT,
        env=env,
    )
    payload = json.loads(packed)
    assert "guidelines" in payload
    assert payload["count"] >= 1
    assert "verdict" not in payload

    empty = subprocess.run(
        [sys.executable, str(SKILL_AUDIT)],
        text=True,
        cwd=ROOT,
        env=env,
        capture_output=True,
    )
    assert empty.returncode != 0

    banned = subprocess.run(
        [sys.executable, str(SKILL_AUDIT), "--file", "ui.png"],
        text=True,
        cwd=ROOT,
        env=env,
        capture_output=True,
    )
    assert banned.returncode != 0
    assert "file" in (banned.stderr + banned.stdout).lower()

    wrapper = ROOT / "scripts" / "audit.py"
    assert wrapper.is_file()
    wrapped = subprocess.check_output(
        [sys.executable, str(wrapper), "--jobs", "design_a_form"],
        text=True,
        cwd=ROOT,
        env=env,
    )
    assert json.loads(wrapped)["count"] >= 1


def test_optional_mcp_call_helper_still_works() -> None:
    assert HELPER.is_file()
    env = {**os.environ, "OPEN_UX_TRANSPORT": "inprocess"}
    listed = subprocess.check_output(
        [sys.executable, str(HELPER), "list"],
        text=True,
        cwd=ROOT,
        env=env,
    )
    names = {row["name"] for row in json.loads(listed)}
    assert {"audit", "list_situations", "get_situation"}.issubset(names)


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
        assert "python -m open_ux stdio" in text
        assert "uxmcp_" in text or "OPEN_UX_API_KEY" in text
