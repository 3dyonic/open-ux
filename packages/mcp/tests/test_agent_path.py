from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from open_ux.jobs import CARD_IDS

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "packages" / "mcp" / "src"
SKILL_DIR = ROOT / "clients" / "plugin" / "skills" / "open-ux"
SKILL = SKILL_DIR / "SKILL.md"
CONNECT = SKILL_DIR / "connect.md"
TOOLS_REFERENCE = SKILL_DIR / "tools.md"
ROUTING_REFERENCES = (
    "SKILL.md",
    "glossary.md",
    "ask-shapes.md",
    "examples.md",
    "shapes.md",
    "cards.md",
    "tools.md",
    "connect.md",
)
COMMANDS = ROOT / "clients" / "plugin" / "commands"
PLUGIN = ROOT / "clients" / "plugin" / ".claude-plugin" / "plugin.json"
MCP_JSON = ROOT / "clients" / "plugin" / ".mcp.json"
AGENT = ROOT / "clients" / "plugin" / "agents" / "open-ux.md"
HELPER = ROOT / "helpers" / "mcp_call.py"
PACK_SCRIPT = ROOT / "helpers" / "pack.py"
BANNED_BODIES = ("pass_when", "fail_when")
ENFORCE_SCRIPT = (
    "must run this script",
    "must run the script",
    "must run the audit script",
    "must run helpers/pack",
    "must run scripts/pack",
    "must run scripts/audit",
    "must run",
    "audit is required",
    "required open ux audit wire",
    "do not improvise the open-ux:pack wire",
    "do not call `open-ux:pack` instead",
    "required script",
    "required audit path",
    "prefer `helpers/pack.py`",
    "prefer `scripts/pack.py`",
    "prefer `scripts/audit.py`",
    "prefer the pack helper",
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


def _skill_corpus() -> str:
    """Hub + references — one skill package, progressive disclosure."""
    return "\n".join(path.read_text(encoding="utf-8") for path in _skill_files())


def _skill_routing_corpus() -> str:
    """Routing references only — excludes field guides with pass_when in shape examples."""
    return "\n".join(
        (SKILL_DIR / name).read_text(encoding="utf-8") for name in ROUTING_REFERENCES
    )


def _script_env(**extra: str) -> dict[str, str]:
    env = {**os.environ, **extra}
    existing = env.get("PYTHONPATH", "")
    src = str(SRC)
    env["PYTHONPATH"] = src if not existing else f"{src}{os.pathsep}{existing}"
    return env


def test_one_skill_package_named_open_ux() -> None:
    skills_root = ROOT / "clients" / "plugin" / "skills"
    packages = [p.name for p in skills_root.iterdir() if p.is_dir()]
    assert packages == ["open-ux"]
    assert (skills_root / "open-ux" / "SKILL.md").is_file()
    assert (skills_root / "open-ux" / "guideline.md").is_file()
    for reference in (
        "glossary.md",
        "ask-shapes.md",
        "examples.md",
        "shapes.md",
        "cards.md",
        "tools.md",
        "connect.md",
    ):
        assert (skills_root / "open-ux" / reference).is_file()
    assert (skills_root / "open-ux" / "component.md").is_file()
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
    assert "Open-UX:pack" in desc
    assert "jobs=<card_id>" in desc
    assert "target" not in desc
    assert "verdict" not in desc
    assert "must run" not in lower
    assert "scripts/" not in desc
    assert "audit.py" not in desc
    assert "required script" not in lower


def test_skill_routing_table_has_when_and_cross_container_reject() -> None:
    body = _skill_routing_corpus()
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
    assert "Open-UX:pack" in body
    assert "must run" not in body.lower()
    assert "prefer `helpers/pack.py`" not in body
    assert "prefer `scripts/pack.py`" not in body
    assert "prefer `scripts/audit.py`" not in body


def test_skill_examples_and_tools_not_sermons() -> None:
    text = _skill_corpus()
    body = text
    lower = body.lower()
    assert "MUST" not in text
    for banned in ENFORCE_SCRIPT:
        assert banned not in lower
    assert "signup" in lower
    assert "`design_a_form`" in body
    assert "`protect_destructive_and_leave`" in body
    assert "Open-UX:suggest_situations" in body
    assert "Open-UX:get_guideline" in body
    assert "Open-UX:pack" in body
    assert "need in" in lower
    assert "open-ux rank-pack" in body or "rank-pack" in body
    assert "helpers list" in lower or "open-ux helpers" in lower
    assert "pip install open-ux" in lower
    assert "mcp" in lower
    assert "choice" in lower
    assert "helpers/pack.py" not in body


def test_skill_files_point_at_tools_not_catalog_bodies() -> None:
    for path in _skill_files():
        text = path.read_text(encoding="utf-8")
        leaked = GUIDELINE_ID.findall(text)
        assert leaked == [], f"{path.name} must not embed guideline ids {leaked}"
        if path.name in ("guideline.md", "component.md"):
            assert "overview" in text
            continue
        if path.name in ("examples.md",):
            continue
        for token in BANNED_BODIES:
            assert token not in text, f"{path.name} must not contain {token}"


def test_plugin_points_at_hosted_mcp() -> None:
    plugin = json.loads(PLUGIN.read_text(encoding="utf-8"))
    mcp = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    assert plugin["name"] == "open-ux"
    assert plugin["displayName"] == "Open UX"
    assert "MCP" not in plugin["displayName"]
    server = mcp["mcpServers"]["open-ux"]
    assert server["url"] == "https://open-ux.dev/mcp"
    assert "${user_config.api_key}" in server["headers"]["Authorization"]
    user_config = plugin.get("userConfig") or {}
    assert user_config["api_key"]["sensitive"] is True
    assert user_config["api_key"]["required"] is True
    assert plugin.get("homepage") == "https://open-ux.dev"


def test_commands_are_short_mcp_prompts() -> None:
    names = {"list.md", "get.md", "pack.md", "forms.md", "actions.md", "feedback.md"}
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
        assert "clients/plugin/skills/open-ux/scripts" not in text
        for banned in ENFORCE_SCRIPT:
            assert banned not in lower
        for token in BANNED_BODIES:
            assert token not in text
        assert len(text.splitlines()) <= 12
        if path.name != "pack.md":
            assert "audit.py" not in text
            assert "pack.py" not in text
    pack_cmd = (COMMANDS / "pack.md").read_text(encoding="utf-8")
    assert "Open-UX:pack" in pack_cmd
    assert "jobs=" in pack_cmd
    assert "guideline_ids" in pack_cmd
    assert "rank-pack" in pack_cmd
    assert "helpers/pack.py" not in pack_cmd
    assert pack_cmd.index("Open-UX:pack") < pack_cmd.index("rank-pack")
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
        assert "Open-UX:pack" in text
        for card_id in CARD_IDS:
            if path.name in {"AGENTS.md", "CLAUDE.md"}:
                assert card_id not in text
    assert not (COMMANDS / "critique.md").exists()


def test_no_audit_tool_name_in_docs() -> None:
    paths = (
        ROOT / "README.md",
        ROOT / "AGENTS.md",
        ROOT / "CLAUDE.md",
        ROOT / "docs/TOOLS.md",
        ROOT / "clients/plugin/README.md",
        AGENT,
        SKILL,
    )
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "Open-UX:audit" in line:
                assert "no " in line.lower(), f"{path.name} must not offer Open-UX:audit: {line!r}"


def test_contributor_pack_wire_and_skill_uses_mcp() -> None:
    assert PACK_SCRIPT.is_file()
    help_text = subprocess.check_output(
        [sys.executable, str(PACK_SCRIPT), "--help"],
        text=True,
        cwd=ROOT,
        env=_script_env(),
    )
    assert "--jobs" in help_text
    assert "--guideline-ids" in help_text
    assert "--file" not in help_text
    assert "verdict" not in help_text.lower()
    scoped = subprocess.check_output(
        [sys.executable, str(PACK_SCRIPT), "--jobs", "design_a_form"],
        text=True,
        cwd=ROOT,
        env=_script_env(),
    )
    payload = json.loads(scoped)
    assert "guidelines" in payload
    assert "verdict" not in payload
    assert payload["count"] >= 1
    empty = subprocess.run(
        [sys.executable, str(PACK_SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=_script_env(),
    )
    assert empty.returncode != 0
    tools = TOOLS_REFERENCE.read_text(encoding="utf-8")
    lower = tools.lower()
    assert "rank-pack" in tools
    assert "helpers list" in lower
    assert "pip install open-ux" in lower
    assert "Open-UX:pack" in tools
    for banned in ENFORCE_SCRIPT:
        assert banned not in lower


def test_optional_helper_is_protocol_not_path() -> None:
    assert HELPER.is_file()
    env = _script_env(OPEN_UX_TRANSPORT="inprocess")
    listed = subprocess.check_output(
        [sys.executable, str(HELPER), "list"],
        text=True,
        cwd=ROOT,
        env=env,
    )
    names = {row["name"] for row in json.loads(listed)}
    assert {"pack", "list_situations", "get_situation"}.issubset(names)
    scoped = subprocess.check_output(
        [sys.executable, str(HELPER), "pack", '{"jobs":"design_a_form"}'],
        text=True,
        cwd=ROOT,
        env=env,
    )
    payload = json.loads(scoped)
    assert "guidelines" in payload
    assert "verdict" not in payload
    assert payload["count"] >= 1
    tools = TOOLS_REFERENCE.read_text(encoding="utf-8")
    assert "open-ux tools list" in tools
    assert "helpers list" in tools.lower()
    assert "must run" not in tools.lower()


def test_connect_offers_hosted_or_package() -> None:
    paths = (
        CONNECT,
        ROOT / "AGENTS.md",
        ROOT / "CLAUDE.md",
        ROOT / "clients/plugin/README.md",
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
    connect = CONNECT.read_text(encoding="utf-8")
    assert 'pip install -e "packages/mcp[dev]"' not in connect
    assert "clone" not in connect.lower()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "### Self-host" in readme
    assert "pip install open-ux" in readme
    assert "python -m open_ux validate-catalog" in readme
    assert "python -m open_ux stdio" in readme
    assert "OPEN_UX_MODE=hosted python -m open_ux http" in readme
    assert "### Contribute" in readme
    assert readme.index("### Self-host") < readme.index("### Contribute")
    assert readme.index("pip install open-ux") < readme.index(
        'pip install -e "packages/mcp[dev]"'
    )
