from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client

from open_ux.jobs import CARD_IDS, LEAF_IDS, expand_need, load_job_tree, resolve_need
from open_ux.server import create_mcp
from open_ux.settings import Settings
from open_ux.situations import (
    NO_SUGGEST_MATCH,
    get_situation,
    list_situations,
    suggest_situations,
)

SKILL = (
    Path(__file__).resolve().parents[3]
    / "clients"
    / "claude"
    / "skills"
    / "open-ux"
    / "SKILL.md"
)
BODY_KEYS = {"pass_when", "fail_when", "rule", "citation", "check"}


def _tree(live_catalog: Path):
    return load_job_tree(Settings.load())


def test_skill_description_is_compose_task_and_short() -> None:
    text = SKILL.read_text(encoding="utf-8")
    _empty, meta, rest = text.split("---", 2)
    desc = meta.split("description:", 1)[1]
    desc = " ".join(desc.replace(">-", "").split())
    assert len(desc) <= 1024
    assert "form" in desc.lower()
    assert "Open-UX:get_situation" in desc
    assert "Open-UX:audit" in desc
    assert "target" not in desc
    assert "verdict" not in desc
    assert "pass_when" not in rest
    assert "forms.field_labels" not in rest
    for card_id in CARD_IDS:
        assert card_id in rest
    for title in (
        "Forms & input",
        "Actions & decisions",
        "Feedback & status",
        "Navigation & wayfinding",
        "Layout & data display",
        "Overlays & content structure",
        "Multi-step flows",
    ):
        assert title in rest


def test_expand_need_cards_not_leaves(live_catalog: Path) -> None:
    tree = _tree(live_catalog)
    assert "avoid_placeholder_as_label" in expand_need("design_a_form", tree)
    assert "explain_failure_next_to_cause" in expand_need("handle_form_errors", tree)
    assert expand_need("avoid_placeholder_as_label", tree) == []
    assert expand_need("forms", tree) == expand_need("forms_and_input", tree)
    assert "avoid_placeholder_as_label" in expand_need("forms", tree)
    assert "avoid_placeholder_as_label" in expand_need("forms_and_input", tree)
    assert expand_need("compose_a_data_display", tree) == []
    display = resolve_need("compose_a_data_display", tree)
    assert display.tags == ()
    assert "canada.tables-no-blank-cells" in display.guideline_ids
    overlay = resolve_need("choose_an_overlay", tree)
    assert "nng.modal-and-nonmodal-dialogs" in overlay.guideline_ids
    steps = resolve_need("build_a_multi_step_flow", tree)
    assert "nl.step-n-of-m-in-title-and-above-form" in steps.guideline_ids
    assert resolve_need("avoid_placeholder_as_label", tree).empty


def test_list_situations_returns_allowlist_only(live_catalog: Path) -> None:
    result = list_situations(_tree(live_catalog))
    ids = [row["id"] for row in result["situations"]]
    assert ids == list(CARD_IDS)
    assert result["total"] == 9
    for row in result["situations"]:
        assert set(row) == {"id", "title", "container", "facet_count", "provisional"}
        assert BODY_KEYS.isdisjoint(row)


def test_list_situations_filters_container_alias(live_catalog: Path) -> None:
    result = list_situations(_tree(live_catalog), container="forms")
    ids = [row["id"] for row in result["situations"]]
    assert ids == ["design_a_form", "handle_form_errors"]


def test_get_situation_returns_pointers_not_bodies(live_catalog: Path) -> None:
    result = get_situation("design_a_form", _tree(live_catalog))
    assert result["found"] is True
    card = result["situation"]
    assert card["id"] == "design_a_form"
    assert card["when"]
    assert any(item["id"] == "handle_form_errors" for item in card["reject"])
    leaf_ids = [leaf for facet in card["facets"] for leaf in facet["leaves"]]
    assert "avoid_placeholder_as_label" in leaf_ids
    dumped = str(card)
    assert "pass_when" not in dumped
    assert "Place a clear label" not in dumped


def test_get_situation_rejects_leaf_and_container(live_catalog: Path) -> None:
    leaf = get_situation("avoid_placeholder_as_label", _tree(live_catalog))
    assert leaf["found"] is False
    assert "Leaf" in leaf["error"]
    container = get_situation("forms_and_input", _tree(live_catalog))
    assert container["found"] is False
    assert "container" in container["error"]
    unknown = get_situation("checkout", _tree(live_catalog))
    assert unknown["found"] is False


def test_suggest_allowlist_only_and_empty_when_no_match(live_catalog: Path) -> None:
    tree = _tree(live_catalog)
    hit = suggest_situations("design a signup form and label these fields", tree=tree)
    ids = [row["id"] for row in hit["situations"]]
    assert ids
    assert ids[0] == "design_a_form"
    assert set(ids) <= set(CARD_IDS)
    assert "avoid_placeholder_as_label" not in ids
    assert "checkout" not in ids
    assert "forms_and_input" not in ids
    miss = suggest_situations("qwerty zxcvbn asdfgh", tree=tree)
    assert miss["situations"] == []
    assert miss["note"] == NO_SUGGEST_MATCH


def test_suggest_surface_is_bias_not_an_id(live_catalog: Path) -> None:
    tree = _tree(live_catalog)
    result = suggest_situations(
        "split this long form into steps for checkout",
        surface="checkout",
        tree=tree,
    )
    ids = [row["id"] for row in result["situations"]]
    assert "build_a_multi_step_flow" in ids
    dumped = str(result)
    assert '"checkout"' not in dumped or result["situations"][0]["id"] != "checkout"


@pytest.mark.asyncio
async def test_situation_tools_on_empty_catalog(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        listed = await client.call_tool("list_situations", {})
        assert listed.data["situations"] == []
        got = await client.call_tool("get_situation", {"id": "design_a_form"})
        assert got.data["found"] is False
        suggested = await client.call_tool(
            "suggest_situations", {"task_text": "design a form"}
        )
        assert suggested.data["situations"] == []


@pytest.mark.asyncio
async def test_situation_tools_live(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        tools = {tool.name for tool in await client.list_tools()}
        assert {"list_situations", "get_situation", "suggest_situations"} <= tools
        listed = await client.call_tool("list_situations", {})
        assert [row["id"] for row in listed.data["situations"]] == list(CARD_IDS)
        got = await client.call_tool(
            "get_situation", {"id": "avoid_placeholder_as_label"}
        )
        assert got.data["found"] is False
        assert "Leaf" in got.data["error"]
        suggested = await client.call_tool(
            "suggest_situations",
            {"task_text": "add a delete confirmation"},
        )
        ids = [row["id"] for row in suggested.data["situations"]]
        assert ids[0] == "protect_destructive_and_leave"
        assert set(ids) <= set(CARD_IDS)
        assert not set(ids) & set(LEAF_IDS)
