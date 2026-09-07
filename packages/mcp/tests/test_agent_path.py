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
COMMANDS = ROOT / "clients" / "claude" / "commands"
PLUGIN = ROOT / "clients" / "claude" / ".claude-plugin" / "plugin.json"
MCP_JSON = ROOT / "clients" / "claude" / ".mcp.json"
AGENT = ROOT / "clients" / "claude" / "agents" / "open-ux.md"
HELPER = ROOT / "scripts" / "mcp_call.py"
AUDIT_SCRIPT = ROOT / "scripts" / "audit.py"
BANNED_BODIES = ("pass_when", "fail_when")
ENFORCE_SCRIPT = (
    "must run this script",
    "must run the script",
    "must run the audit script",
    "must run scripts/audit",
    "must run",
    "audit is required",
    "required open ux audit wire",
    "do not improvise the open-ux:audit wire",
    "do not call `open-ux:audit` instead",
    "required script",
    "required audit path",
    "prefer `scripts/audit.py`",
    "prefer the audit helper",
    "prefer the script",
)
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
    assert not (SKILL_DIR / "scripts").exists()
    for fluff in ("review.md", "map.md", "cite.md"):
        assert not (SKILL_DIR / fluff).exists()
    assert not (SKILL_DIR / "commands").exists()


def test_skill_description_informs_and_promotes() -> None:
    text = SKILL.read_text(encoding="utf-8")
    desc = _frontmatter_description(text)
    assert len(desc) <= 1024
    lower = desc.lower()
    assert "building or checking UI" in desc
    assert "composing or reviewing" in lower
    assert "form" in lower
    assert "cited" in lower
    assert "pass" in lower and "fail" in lower
    assert "invent" in lower or "memory" in lower
    assert "open ux" in lower
    assert "Open-UX:get_situation" in desc
    assert "Open-UX:audit" in desc
    assert "jobs=<card_id>" in desc
    assert "target" not in desc
    assert "verdict" not in desc
    assert "must run" not in lower
    assert "scripts/" not in desc
    assert "audit.py" not in desc
    assert "required script" not in lower


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
    assert "Open-UX:audit" in body
    assert "must run" not in body.lower()
    assert "prefer `scripts/audit.py`" not in body


def test_skill_examples_and_tools_not_sermons() -> None:
    text = SKILL.read_text(encoding="utf-8")
    _empty, _meta, body = text.split("---", 2)
    lower = body.lower()
    assert "MUST" not in text
    for banned in ENFORCE_SCRIPT:
        assert banned not in lower
    assert "signup" in lower
    assert "`design_a_form`" in body
    assert "`protect_destructive_and_leave`" in body
    assert "Open-UX:suggest_situations" in body
    assert "Open-UX:get_guideline" in body
    assert "Open-UX:audit" in body
    assert "need in" in lower
    assert "scripts/audit.py" in body
    assert "available" in lower
    assert "not required" in lower
    assert "choice" in lower
    assert body.index("Open-UX:audit") < body.index("scripts/audit.py")


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


def test_commands_are_short_mcp_prompts() -> None:
    names = {"list.md", "get.md", "audit.md", "forms.md", "actions.md", "feedback.md"}
    found = {p.name for p in COMMANDS.glob("*.md")}
    assert names <= found
    assert not (COMMANDS / "critique.md").exists()
    for path in COMMANDS.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        assert "verdict" not in lower
        assert "pass/fail" not in lower
        assert "upload" not in lower
        assert "no file" in lower or "send a file" in lower or "not ask for a file" in lower
        assert "Open-UX:" in text
        assert "python3 skills/open-ux/scripts" not in lower
        assert "clients/claude/skills/open-ux/scripts" not in text
        for banned in ENFORCE_SCRIPT:
            assert banned not in lower
        for token in BANNED_BODIES:
            assert token not in text
        assert len(text.splitlines()) <= 12
        if path.name != "audit.md":
            assert "audit.py" not in text
    audit = (COMMANDS / "audit.md").read_text(encoding="utf-8")
    assert "Open-UX:audit" in audit
    assert "jobs=" in audit
    assert "guideline_ids" in audit
    assert "scripts/audit.py" in audit
    assert "available" in audit.lower()
    assert audit.index("Open-UX:audit") < audit.index("scripts/audit.py")
    list_cmd = (COMMANDS / "list.md").read_text(encoding="utf-8")
    get_cmd = (COMMANDS / "get.md").read_text(encoding="utf-8")
    assert "Open-UX:list_situations" in list_cmd
    assert "Open-UX:get_situation" in get_cmd


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
        assert "must run" not in text.lower()
        assert "Open-UX:audit" in text
        for card_id in CARD_IDS:
            if path.name in {"AGENTS.md", "CLAUDE.md"}:
                assert card_id not in text
    assert not (COMMANDS / "critique.md").exists()


def test_audit_helper_available_not_required() -> None:
    assert AUDIT_SCRIPT.is_file()
    help_text = subprocess.check_output(
        [sys.executable, str(AUDIT_SCRIPT), "--help"],
        text=True,
        cwd=ROOT,
    )
    assert "--jobs" in help_text
    assert "--guideline-ids" in help_text
    assert "--file" not in help_text
    assert "verdict" not in help_text.lower()
    scoped = subprocess.check_output(
        [sys.executable, str(AUDIT_SCRIPT), "--jobs", "design_a_form"],
        text=True,
        cwd=ROOT,
    )
    payload = json.loads(scoped)
    assert "guidelines" in payload
    assert "verdict" not in payload
    assert payload["count"] >= 1
    empty = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert empty.returncode != 0
    skill = SKILL.read_text(encoding="utf-8")
    lower = skill.lower()
    assert "scripts/audit.py" in skill
    assert "not required" in lower
    assert "Open-UX:audit" in skill
    for banned in ENFORCE_SCRIPT:
        assert banned not in lower


def test_optional_helper_is_protocol_not_path() -> None:
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
    scoped = subprocess.check_output(
        [sys.executable, str(HELPER), "audit", '{"jobs":"design_a_form"}'],
        text=True,
        cwd=ROOT,
        env=env,
    )
    payload = json.loads(scoped)
    assert "guidelines" in payload
    assert "verdict" not in payload
    assert payload["count"] >= 1
    skill = SKILL.read_text(encoding="utf-8")
    assert "mcp_call.py" in skill
    assert "do not treat `mcp_call.py`" in skill.lower()
    assert "must run" not in skill.lower()


def test_connect_offers_hosted_or_package() -> None:
    paths = (
        SKILL,
        ROOT / "AGENTS.md",
        ROOT / "CLAUDE.md",
        ROOT / "clients" / "claude" / "README.md",
        AGENT,
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "https://open-ux.dev/mcp" in text
        assert "pip install open-ux" in text
        assert "python -m open_ux validate-catalog" in text
        assert "python -m open_ux stdio" in text
        assert "OPEN_UX_MODE=hosted python -m open_ux http" in text
        assert "uxmcp_" in text or "OPEN_UX_API_KEY" in text
        assert "package" in text.lower() or "pip install" in text.lower()
    skill = SKILL.read_text(encoding="utf-8")
    assert 'pip install -e "packages/mcp[dev]"' not in skill
    assert "clone" not in skill.lower()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "### Self-host" in readme
    assert "pip install open-ux" in readme
    assert "python -m open_ux validate-catalog" in readme
    assert "python -m open_ux stdio" in readme
    assert "OPEN_UX_MODE=hosted python -m open_ux http" in readme
    assert "### Contribute from this repo" in readme
    assert readme.index("### Self-host") < readme.index("### Contribute from this repo")
    assert readme.index("pip install open-ux") < readme.index(
        'pip install -e "packages/mcp[dev]"'
    )
