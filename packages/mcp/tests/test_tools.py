from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastmcp import Client

from open_ux.catalog import EMPTY_NOTE, citations
from open_ux.jobs import CARD_IDS, CONTAINER_IDS, JOB_ALIASES, LEAF_IDS
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
CATALOG_COUNT = 203
FORM_COUNT = 14
EXTRA_COUNT = 46
HARVEST3_COUNT = 56
HARVEST4_COUNT = 43
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
        assert "UNS-44" in data["note"]

        got = await client.call_tool("get_guideline", {"id": "forms.field_labels.visible_label"})
        body = got.data
        assert body["found"] is False
        assert "forms.field_labels.visible_label" in body["error"]

        audited = await client.call_tool("audit", {})
        result = audited.data
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
        audited = await client.call_tool(
            "audit",
            {"guideline_ids": ["not.a.real.rule"]},
        )
        result = audited.data
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
async def test_search_query_orders_without_filtering(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        wide = await client.call_tool("search_guidelines", {"limit": 50, "offset": 0})
        ranked = await client.call_tool(
            "search_guidelines",
            {"query": "helper text", "limit": 50, "offset": 0},
        )
        assert ranked.data["total"] == wide.data["total"]
        ranked_ids = [row["id"] for row in ranked.data["guidelines"]]
        assert "fluent.helper-text-below" in ranked_ids[:10]


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
async def test_audit_without_scope_fails(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        audited = await client.call_tool("audit", {})
        result = audited.data
        assert "requires jobs or guideline_ids" in result["error"]
        assert result["guidelines"] == []


@pytest.mark.asyncio
async def test_audit_guideline_ids_only_those_rules(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        audited = await client.call_tool(
            "audit",
            {
                "guideline_ids": [
                    FORM_SEED,
                    "actions.button_groups",
                ],
            },
        )
        result = audited.data
        ids = [row["id"] for row in result["guidelines"]]
        assert ids == [
            FORM_SEED,
            "actions.button_groups",
        ]
        assert "error" not in result
        assert "verdict" not in result
        for row in result["guidelines"]:
            assert set(row) == {
                "id",
                "title",
                "name",
                "rule",
                "pass_when",
                "fail_when",
                "facet",
            }


@pytest.mark.asyncio
async def test_audit_schema_shows_jobs_enum_not_target(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        tools = await client.list_tools()
    audit_tool = next(t for t in tools if t.name == "audit")
    schema = getattr(audit_tool, "input_schema", None) or getattr(
        audit_tool, "inputSchema"
    )
    props = schema["properties"]
    assert "target" not in props
    assert "content" not in props
    jobs_enum = next(
        branch["enum"]
        for branch in props["jobs"]["anyOf"]
        if "enum" in branch
    )
    assert set(jobs_enum) == set(CARD_IDS) | set(CONTAINER_IDS) | set(JOB_ALIASES)
    assert len(jobs_enum) == 13 + 7 + 3
    for leaf in LEAF_IDS:
        assert leaf not in jobs_enum
    assert "checkout" not in jobs_enum
    description = audit_tool.description or ""
    assert "Situation Card or container" in description
    assert "Does not take a file" in description
    assert "Does not return pass or fail" in description
    assert "Leaf ids are not needs" in description


@pytest.mark.asyncio
async def test_audit_jobs_returns_criteria(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        audited = await client.call_tool(
            "audit", {"jobs": "design_a_form"}
        )
        result = audited.data
        assert result["count"] >= 1
        assert "verdict" not in result
        assert "summary" not in result
        assert result["host"] == "citations_only"
        row = result["guidelines"][0]
        assert set(row) == {
            "id",
            "title",
            "name",
            "rule",
            "pass_when",
            "fail_when",
            "facet",
        }
