from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client

from open_ux.jobs import (
    CARD_IDS,
    CONTAINER_IDS,
    LEAF_IDS,
    expand_need,
    leaf_by_id,
    load_job_tree,
    resolve_need,
)
from open_ux.server import create_mcp
from open_ux.settings import Settings
from open_ux.jobs import Card
from open_ux.situations import (
    MAP_ROW_KEYS,
    NO_SUGGEST_MATCH,
    SPEC_ROW_KEYS,
    SUGGEST_MENU_NOTE,
    _card_payload,
    _map_row,
    _spec_row,
    get_situation,
    list_situations,
    suggest_card_ids,
    suggest_situations,
)

SKILL_DIR = (
    Path(__file__).resolve().parents[3] / "clients" / "claude" / "skills" / "open-ux"
)
SKILL = SKILL_DIR / "SKILL.md"
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
    assert "Open-UX:pack" in desc
    assert "target" not in desc
    assert "verdict" not in desc
    assert "pass_when" not in rest
    assert "forms.field_labels" not in rest
    routing = "\n".join(
        (SKILL_DIR / name).read_text(encoding="utf-8") for name in ROUTING_REFERENCES
    )
    assert "MANIFEST.md" in routing
    for card_id in CARD_IDS:
        assert card_id in routing
    for title in (
        "Forms & input",
        "Actions & decisions",
        "Feedback & status",
        "Navigation & wayfinding",
        "Layout & data display",
        "Overlays & content structure",
        "Multi-step flows",
    ):
        assert title in routing


def test_expand_need_cards_and_leaves(live_catalog: Path) -> None:
    tree = _tree(live_catalog)
    assert "avoid_placeholder_as_label" in expand_need("design_a_form", tree)
    assert "explain_failure_next_to_cause" in expand_need("handle_form_errors", tree)
    assert expand_need("avoid_placeholder_as_label", tree) == ["avoid_placeholder_as_label"]
    assert expand_need("forms", tree) == expand_need("forms_and_input", tree)
    assert "avoid_placeholder_as_label" in expand_need("forms", tree)
    assert "avoid_placeholder_as_label" in expand_need("forms_and_input", tree)
    assert "chart_has_a_story" in expand_need("compose_a_data_display", tree)
    display = resolve_need("compose_a_data_display", tree)
    assert "chart_has_a_story" in display.tags
    assert "nsw.charts-start-with-story" in display.guideline_ids
    overlay = resolve_need("choose_an_overlay", tree)
    assert "mui.non-modal-dialogs-allowed" in overlay.guideline_ids
    steps = resolve_need("build_a_multi_step_flow", tree)
    assert "nl.step-n-of-m-in-title-and-above-form" in steps.guideline_ids
    placeholder = resolve_need("avoid_placeholder_as_label", tree)
    assert placeholder.tags == ("avoid_placeholder_as_label",)
    assert placeholder.guideline_ids
    primary = resolve_need("pick_primary_action", tree)
    assert primary.tags == ("pick_primary_action",)
    assert "ant.one-cta-per-screen" in primary.guideline_ids


def test_list_situations_returns_allowlist_only(live_catalog: Path) -> None:
    result = list_situations(_tree(live_catalog))
    ids = [row["id"] for row in result["situations"]]
    assert ids == list(CARD_IDS)
    assert result["total"] == 13
    for row in result["situations"]:
        assert set(row) == {"id", "title", "container", "facet_count", "provisional"}
        assert BODY_KEYS.isdisjoint(row)


def test_list_situations_filters_container_alias(live_catalog: Path) -> None:
    result = list_situations(_tree(live_catalog), container="forms")
    ids = [row["id"] for row in result["situations"]]
    assert ids == ["design_a_form", "handle_form_errors", "compose_sign_in"]
    for row in result["situations"]:
        assert set(row) == set(SPEC_ROW_KEYS)
        assert row["overview"]
        assert row["when"]
        assert row["reject"]
    form = next(row for row in result["situations"] if row["id"] == "design_a_form")
    assert any(item["id"] == "handle_form_errors" for item in form["reject"])


def test_unscoped_list_stays_index(live_catalog: Path) -> None:
    result = list_situations(_tree(live_catalog))
    for row in result["situations"]:
        assert "when" not in row
        assert "reject" not in row
        assert "overview" not in row


def test_get_situation_includes_component(live_catalog: Path) -> None:
    result = get_situation("design_actions_and_ctas", _tree(live_catalog))
    assert result["found"] is True
    assert result["situation"]["component"] == ["button", "link"]


def test_component_omitted_when_empty() -> None:
    bare = Card(
        id="x",
        title="t",
        container="forms_and_input",
        overview="o",
        when=(),
        reject=(),
        hints=(),
        facets=(),
    )
    assert "component" not in _map_row(bare)
    assert "component" not in _spec_row(bare)
    assert "component" not in _card_payload(bare)

    stamped = Card(
        id="x",
        title="t",
        container="forms_and_input",
        overview="o",
        when=(),
        reject=(),
        hints=(),
        facets=(),
        component=("button", "link"),
    )
    assert _map_row(stamped)["component"] == ["button", "link"]
    assert _spec_row(stamped)["component"] == ["button", "link"]
    assert _card_payload(stamped)["component"] == ["button", "link"]


def test_get_situation_returns_pointers_not_bodies(live_catalog: Path) -> None:
    result = get_situation("design_a_form", _tree(live_catalog))
    assert result["found"] is True
    card = result["situation"]
    assert card["id"] == "design_a_form"
    assert card["when"]
    assert any(item["id"] == "handle_form_errors" for item in card["reject"])
    leaf_rows = [leaf for facet in card["facets"] for leaf in facet["leaves"]]
    leaf_ids = [leaf["id"] for leaf in leaf_rows]
    assert "avoid_placeholder_as_label" in leaf_ids
    for leaf in leaf_rows:
        assert set(leaf) == {"id", "count"}
        assert leaf["count"] >= 0
    dumped = str(card)
    assert "pass_when" not in dumped
    assert "Place a clear label" not in dumped


def test_get_situation_leaf_counts_match_tree(live_catalog: Path) -> None:
    tree = _tree(live_catalog)
    result = get_situation("design_a_form", tree)
    facet = next(
        f for f in result["situation"]["facets"] if f["id"] == "wrong_control_for_the_choice"
    )
    leaf = next(row for row in facet["leaves"] if row["id"] == "choose_control_for_choice")
    source = leaf_by_id(tree, "choose_control_for_choice")
    assert source is not None
    assert leaf["count"] == len(source.guideline_ids)


def test_get_situation_multi_step_has_go_back_and_leave_warn(live_catalog: Path) -> None:
    result = get_situation("build_a_multi_step_flow", _tree(live_catalog))
    assert result["found"] is True
    card = result["situation"]
    when = " ".join(card["when"]).lower()
    assert "go back" in when
    assert any(item["id"] == "protect_destructive_and_leave" for item in card["reject"])


def test_get_situation_rejects_leaf_and_container(live_catalog: Path) -> None:
    leaf = get_situation("avoid_placeholder_as_label", _tree(live_catalog))
    assert leaf["found"] is False
    assert "Leaf" in leaf["error"]
    assert "design_a_form" in leaf["error"]
    step = get_situation("show_step_progress", _tree(live_catalog))
    assert step["found"] is False
    assert "build_a_multi_step_flow" in step["error"]
    assert "design_a_form" not in step["error"]
    container = get_situation("forms_and_input", _tree(live_catalog))
    assert container["found"] is False
    assert "container" in container["error"]
    unknown = get_situation("checkout", _tree(live_catalog))
    assert unknown["found"] is False


def test_suggest_allowlist_only_and_empty_when_no_match(live_catalog: Path) -> None:
    tree = _tree(live_catalog)
    hit = suggest_situations("design a signup form and label these fields", tree=tree)
    ids = suggest_card_ids(hit)
    assert ids
    assert set(ids) <= set(CARD_IDS)
    assert ids == list(CARD_IDS)
    assert "avoid_placeholder_as_label" not in ids
    assert "checkout" not in ids
    empty = suggest_situations("", tree=tree)
    assert empty["containers"] == []
    assert empty["note"] == NO_SUGGEST_MATCH


def test_suggest_is_a_lock_order_map(live_catalog: Path) -> None:
    """Same grouping for any non-empty query. Never hide. No Card BM25 flag."""
    tree = _tree(live_catalog)
    nonsense = suggest_situations("qwerty zxcvbn asdfgh", tree=tree)
    real = suggest_situations(
        "can they go back and change an earlier answer", tree=tree
    )
    assert [c["id"] for c in nonsense["containers"]] == list(CONTAINER_IDS)
    assert [c["id"] for c in real["containers"]] == list(CONTAINER_IDS)
    assert suggest_card_ids(nonsense) == list(CARD_IDS)
    assert suggest_card_ids(real) == list(CARD_IDS)
    assert nonsense["note"] == SUGGEST_MENU_NOTE
    for container in nonsense["containers"] + real["containers"]:
        for row in container["situations"]:
            assert set(row) == set(MAP_ROW_KEYS)
            assert row["overview"]
            assert "attention" not in row
            assert "why" not in row
            assert "hint_score" not in row
            assert "caution" not in row
    cluttered = suggest_situations(
        "the dashboard feels cluttered and I don't know what to look at first",
        tree=tree,
    )
    assert "compose_the_layout" in suggest_card_ids(cluttered)


def test_suggest_has_no_rejected_list(live_catalog: Path) -> None:
    tree = _tree(live_catalog)
    result = suggest_situations(
        "we split checkout into 3 screens, is that ok",
        surface="checkout",
        tree=tree,
    )
    assert "rejected" not in result
    assert "build_a_multi_step_flow" in suggest_card_ids(result)
    dumped = str(result)
    assert "caution" not in dumped


def test_suggest_surface_is_not_an_id(live_catalog: Path) -> None:
    tree = _tree(live_catalog)
    result = suggest_situations(
        "split this long form into steps for checkout",
        surface="checkout",
        tree=tree,
    )
    assert "build_a_multi_step_flow" in suggest_card_ids(result)
    dumped = str(result)
    assert '"id": "checkout"' not in dumped


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
        assert suggested.data["containers"] == []


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
        assert "design_a_form" in got.data["error"]
        suggested = await client.call_tool(
            "suggest_situations",
            {"task_text": "add a delete confirmation"},
        )
        ids = suggest_card_ids(suggested.data)
        assert "protect_destructive_and_leave" in ids
        assert ids == list(CARD_IDS)
        assert not set(ids) & set(LEAF_IDS)


@pytest.mark.asyncio
async def test_suggest_situations_tool_does_not_claim_ranking(
    live_catalog: Path,
) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        tool = next(t for t in await client.list_tools() if t.name == "suggest_situations")
    desc = tool.description or ""
    lower = desc.lower()
    assert "heuristic" not in lower
    assert "not a verdict" not in lower
    assert "ranking bias" not in lower
    assert "catalog map" in lower
    assert "no ranking" in lower
    assert "lock order" in lower
    schema = getattr(tool, "input_schema", None) or getattr(tool, "inputSchema")
    blob = str(schema).lower()
    assert "ranking" not in blob
    assert "heuristic" not in blob
