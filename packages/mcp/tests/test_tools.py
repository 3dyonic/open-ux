from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastmcp import Client

from open_ux.catalog import EMPTY_NOTE, citations
from open_ux.jobs import CARD_IDS, CONTAINER_IDS, JOB_ALIASES, LEAF_IDS
from open_ux.pack import PACK_KEYS, PACK_ROW_KEYS
from open_ux.server import create_mcp

REMAINING_SEED = (
    "ant.checkbox-vs-switch",
    "ant.one-cta-per-screen",
    "fluent.multistep-next-not-continue",
    "govuk.date-input-only-memorable",
)
FORM_SEED = "ant.checkbox-vs-switch"
INDEX_KEYS = {"id", "title", "name", "jobs", "lane", "container", "card", "facet", "leaf"}
BODY_KEYS = {"pass_when", "fail_when", "rule", "citation", "check"}
EXTRA_SAMPLE = "govuk.date-input-only-memorable"
CATALOG_COUNT = 204
FORM_COUNT = 14
EXTRA_COUNT = 46
HARVEST3_COUNT = 56
HARVEST4_COUNT = 44
HARVEST5_COUNT = 34
HARVEST3_SAMPLE = "spectrum.quiet-vs-standard-background"
HARVEST4_SAMPLE = "uswds.filled-next-outline-this-page"
HARVEST5_SAMPLE = "gold.consistent-not-uniform"
EXTRA_PREFIXES = ("govuk.", "fluent.", "polar.")
HARVEST3_PREFIXES = ("spectrum.", "ant.", "mui.")
HARVEST4_PREFIXES = ("uswds.", "canada.", "nsw.")
HARVEST5_PREFIXES = ("gold.", "nl.", "suomi.")


@pytest.mark.asyncio
async def test_empty_catalog_tools_are_honest(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        listed = await client.call_tool("list_guidelines", {})
        data = listed.data
        assert data["guidelines"] == []
        assert data["count"] == 0
        assert data["catalog"]["status"] == "empty"
        assert data["note"] == EMPTY_NOTE

        got = await client.call_tool("get_guideline", {"id": "forms.field_labels.visible_label"})
        body = got.data
        assert body["found"] is False
        assert "forms.field_labels.visible_label" in body["error"]

        packed = await client.call_tool("pack", {})
        result = packed.data
        assert result["guidelines"] == []
        assert "requires jobs or guideline_ids" in result["error"]
        assert EMPTY_NOTE in result["note"]
        assert "verdict" not in result
        assert result["host"] == "citations_only"
        assert "summary" not in result


@pytest.mark.asyncio
async def test_unknown_id_is_empty_not_invented(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        packed = await client.call_tool(
            "pack",
            {"guideline_ids": ["not.a.real.rule"]},
        )
        result = packed.data
        assert result["guidelines"] == []
        assert result["count"] == 0
        assert "verdict" not in result


def _assert_index_rows(rows: list[dict]) -> None:
    for row in rows:
        assert set(row) <= INDEX_KEYS
        assert BODY_KEYS.isdisjoint(row)


@pytest.mark.asyncio
async def test_list_index_has_no_rule_bodies(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        listed = await client.call_tool("list_guidelines", {"limit": 400, "offset": 0})
        data = listed.data
        assert data["catalog"]["status"] == "ok"
        assert data["total"] == CATALOG_COUNT
        _assert_index_rows(data["guidelines"])
        ids = {row["id"] for row in data["guidelines"]}
        for seed in REMAINING_SEED:
            assert seed in ids
        extra = [row for row in data["guidelines"] if row["id"].startswith(EXTRA_PREFIXES)]
        harvest3 = [
            row for row in data["guidelines"] if row["id"].startswith(HARVEST3_PREFIXES)
        ]
        harvest4 = [
            row for row in data["guidelines"] if row["id"].startswith(HARVEST4_PREFIXES)
        ]
        harvest5 = [
            row for row in data["guidelines"] if row["id"].startswith(HARVEST5_PREFIXES)
        ]
        assert len(extra) == EXTRA_COUNT
        assert len(harvest3) == HARVEST3_COUNT
        assert len(harvest4) == HARVEST4_COUNT
        assert len(harvest5) == HARVEST5_COUNT
        assert EXTRA_SAMPLE in ids
        assert HARVEST3_SAMPLE in ids
        assert HARVEST4_SAMPLE in ids
        assert HARVEST5_SAMPLE in ids
        for row in extra + harvest3 + harvest4 + harvest5:
            dumped = json.dumps(row)
            assert "pass_when" not in dumped
            assert '"rule"' not in dumped
            assert "do_not_claim" not in dumped


@pytest.mark.asyncio
async def test_get_guideline_returns_full_body(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        got = await client.call_tool(
            "get_guideline", {"id": FORM_SEED}
        )
        body = got.data
        assert body["found"] is True
        g = body["guideline"]
        assert g["id"] == FORM_SEED
        assert g["name"] == "Checkbox vs switch — Ant"
        assert "lane" not in g
        assert g["rule"]
        assert g["pass_when"]
        assert g["fail_when"]
        cites = citations(g)
        assert cites
        for cite in cites:
            assert cite["url"].startswith("https://")
            assert "](<" not in cite["url"]


@pytest.mark.asyncio
async def test_search_jobs_actions_only(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        found = await client.call_tool(
            "search_guidelines", {"jobs": "actions", "limit": 200}
        )
        data = found.data
        action_cards = {"design_actions_and_ctas", "protect_destructive_and_leave"}
        assert data["total"] >= 1
        _assert_index_rows(data["guidelines"])
        assert all(row["card"] in action_cards for row in data["guidelines"])
        assert {row["card"] for row in data["guidelines"]} <= action_cards


@pytest.mark.asyncio
async def test_search_lane_forms_only(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        found = await client.call_tool(
            "search_guidelines", {"lane": "forms", "limit": 200}
        )
        data = found.data
        assert data["total"] == FORM_COUNT
        _assert_index_rows(data["guidelines"])
        assert all(row["lane"] == "forms" for row in data["guidelines"])
        assert all(row["id"].startswith("forms.") for row in data["guidelines"])
        assert "forms.labels.clickable" in {row["id"] for row in data["guidelines"]}


@pytest.mark.asyncio
async def test_search_query_does_not_reorder(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        wide = await client.call_tool("search_guidelines", {"limit": 50, "offset": 0})
        ranked = await client.call_tool(
            "search_guidelines",
            {"query": "helper text", "limit": 50, "offset": 0},
        )
        assert ranked.data["total"] == wide.data["total"]
        assert [row["id"] for row in ranked.data["guidelines"]] == [
            row["id"] for row in wide.data["guidelines"]
        ]


@pytest.mark.asyncio
async def test_get_extra_harvest_guideline_returns_full_body(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        got = await client.call_tool("get_guideline", {"id": EXTRA_SAMPLE})
        body = got.data
        assert body["found"] is True
        g = body["guideline"]
        assert g["id"] == EXTRA_SAMPLE
        assert "lane" not in g
        assert g["rule"]
        assert g["pass_when"]
        assert g["fail_when"]
        assert g["do_not_claim"]
        assert "when_to_use" not in g
        assert "when_not" not in g
        cites = citations(g)
        assert cites
        assert isinstance(g["citation"], list)
        for cite in cites:
            assert cite["url"].startswith("https://")
            assert "](<" not in cite["url"]


@pytest.mark.asyncio
async def test_get_harvest3_guideline_returns_full_body(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        got = await client.call_tool("get_guideline", {"id": HARVEST3_SAMPLE})
        body = got.data
        assert body["found"] is True
        g = body["guideline"]
        assert g["id"] == HARVEST3_SAMPLE
        assert "lane" not in g
        assert g["rule"]
        assert g["pass_when"]
        assert g["fail_when"]
        assert g["do_not_claim"]
        assert "when_to_use" not in g
        assert "when_not" not in g
        cites = citations(g)
        assert cites
        for cite in cites:
            assert cite["url"].startswith("https://")
            assert "](<" not in cite["url"]


@pytest.mark.asyncio
async def test_get_harvest4_guideline_returns_full_body(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        got = await client.call_tool("get_guideline", {"id": HARVEST4_SAMPLE})
        body = got.data
        assert body["found"] is True
        g = body["guideline"]
        assert g["id"] == HARVEST4_SAMPLE
        assert "lane" not in g
        assert g["rule"]
        assert g["pass_when"]
        assert g["fail_when"]
        assert g["do_not_claim"]
        assert "when_to_use" not in g
        assert "when_not" not in g
        cites = citations(g)
        assert cites
        for cite in cites:
            assert cite["url"].startswith("https://")
            assert "](<" not in cite["url"]


@pytest.mark.asyncio
async def test_get_harvest5_guideline_returns_full_body(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        got = await client.call_tool("get_guideline", {"id": HARVEST5_SAMPLE})
        body = got.data
        assert body["found"] is True
        g = body["guideline"]
        assert g["id"] == HARVEST5_SAMPLE
        assert "lane" not in g
        assert g["rule"]
        assert g["pass_when"]
        assert g["fail_when"]
        assert g["do_not_claim"]
        assert "when_to_use" not in g
        assert "when_not" not in g
        cites = citations(g)
        assert cites
        for cite in cites:
            assert cite["url"].startswith("https://")
            assert "](<" not in cite["url"]


@pytest.mark.asyncio
async def test_pack_query_does_not_reorder(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        baseline = await client.call_tool(
            "pack", {"jobs": "design_actions_and_ctas", "limit": 50}
        )
        with_query = await client.call_tool(
            "pack",
            {
                "jobs": "design_actions_and_ctas",
                "query": "action panel",
                "limit": 50,
            },
        )
        assert with_query.data["total"] == baseline.data["total"]
        assert [row["id"] for row in with_query.data["guidelines"]] == [
            row["id"] for row in baseline.data["guidelines"]
        ]
        assert "query_fallback" not in with_query.data


@pytest.mark.asyncio
async def test_pack_without_scope_fails(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        packed = await client.call_tool("pack", {})
        result = packed.data
        assert "requires jobs or guideline_ids" in result["error"]
        assert result["guidelines"] == []


@pytest.mark.asyncio
async def test_pack_guideline_ids_only_those_rules(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        packed = await client.call_tool(
            "pack",
            {
                "guideline_ids": [
                    FORM_SEED,
                    "actions.button_groups",
                ],
            },
        )
        result = packed.data
        ids = [row["id"] for row in result["guidelines"]]
        assert ids == [
            FORM_SEED,
            "actions.button_groups",
        ]
        assert "error" not in result
        assert "verdict" not in result
        for row in result["guidelines"]:
            assert set(PACK_ROW_KEYS) <= set(row)
            assert set(row) <= set(PACK_KEYS)


@pytest.mark.asyncio
async def test_pack_schema_shows_jobs_enum_not_target(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        tools = await client.list_tools()
    pack_tool = next(t for t in tools if t.name == "pack")
    schema = getattr(pack_tool, "input_schema", None) or getattr(
        pack_tool, "inputSchema"
    )
    props = schema["properties"]
    assert "target" not in props
    assert "content" not in props
    jobs_enum = next(
        branch["enum"]
        for branch in props["jobs"]["anyOf"]
        if "enum" in branch
    )
    assert set(jobs_enum) == set(CARD_IDS) | set(CONTAINER_IDS) | set(JOB_ALIASES) | set(
        LEAF_IDS
    )
    assert len(jobs_enum) == 13 + 7 + 3 + len(LEAF_IDS)
    assert "pick_primary_action" in jobs_enum
    assert "checkout" not in jobs_enum
    description = pack_tool.description or ""
    assert "Situation Card" in description
    assert "Leaf" in description
    assert "Does not take a file" in description
    assert "Does not return pass or fail" in description


@pytest.mark.asyncio
async def test_pack_leaf_jobs_scopes_criteria(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        packed = await client.call_tool("pack", {"jobs": "pick_primary_action"})
        result = packed.data
        assert result["count"] >= 1
        ids = {row["id"] for row in result["guidelines"]}
        assert "ant.one-cta-per-screen" in ids
        assert all(row["leaf"] == "pick_primary_action" for row in result["guidelines"])


@pytest.mark.asyncio
async def test_pack_jobs_returns_criteria(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        packed = await client.call_tool(
            "pack", {"jobs": "design_a_form"}
        )
        result = packed.data
        assert result["count"] >= 1
        assert "verdict" not in result
        assert "summary" not in result
        assert result["host"] == "citations_only"
        row = result["guidelines"][0]
        assert set(PACK_ROW_KEYS) <= set(row)
        assert set(row) <= set(PACK_KEYS)


@pytest.mark.asyncio
async def test_list_components_returns_index(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        listed = await client.call_tool("list_components", {})
        payload = listed.data
        assert payload["count"] == 38
        assert payload["total"] == 38
        assert set(payload["components"][0]) == {"id", "title", "overview"}


@pytest.mark.asyncio
async def test_get_component_default_and_used_on(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        got = await client.call_tool("get_component", {"id": "button"})
        payload = got.data
        assert payload["found"] is True
        component = payload["component"]
        assert component["id"] == "button"
        assert "variants" in component
        assert "keywords" not in component
        assert "used_on" not in component

        with_used_on = await client.call_tool(
            "get_component",
            {"id": "button", "include_used_on": True},
        )
        used_on = with_used_on.data["component"]["used_on"]
        assert used_on["cards_total"] == 8
        assert used_on["cites_total"] == 32

        missing = await client.call_tool("get_component", {"id": "not_a_widget"})
        assert missing.data["found"] is False


@pytest.mark.asyncio
async def test_mcp_tool_names_include_pack_and_components_not_audit(
    live_catalog: Path,
) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        names = {tool.name for tool in await client.list_tools()}
    assert "pack" in names
    assert "list_components" in names
    assert "get_component" in names
    assert "audit" not in names
