from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastmcp import Client

from open_ux.catalog import EMPTY_NOTE
from open_ux.server import create_mcp

LIVE_SEED = (
    "forms.field_labels.visible_label",
    "forms.field_labels.label_stays_visible",
    "forms.field_labels.error_identifies_and_fixes",
)
INDEX_KEYS = {"id", "title", "jobs", "lane"}
BODY_KEYS = {"pass_when", "fail_when", "rule", "citation", "check"}
EXTRA_SAMPLE = "govuk.date-input-only-memorable"
HARVEST3_SAMPLE = "spectrum.quiet-vs-standard-background"
HARVEST4_SAMPLE = "uswds.filled-next-outline-this-page"
HARVEST5_SAMPLE = "gold.consistent-not-uniform"
EXTRA_PREFIXES = ("govuk.", "nng.", "fluent.", "polar.")
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
        assert data["total"] == 309
        _assert_index_rows(data["guidelines"])
        ids = {row["id"] for row in data["guidelines"]}
        for seed in LIVE_SEED:
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
        assert len(extra) == 73
        assert len(harvest3) == 56
        assert len(harvest4) == 46
        assert len(harvest5) == 40
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
            "get_guideline", {"id": "forms.field_labels.visible_label"}
        )
        body = got.data
        assert body["found"] is True
        g = body["guideline"]
        assert g["id"] == "forms.field_labels.visible_label"
        assert "lane" not in g
        assert g["rule"]
        assert g["pass_when"]
        assert g["fail_when"]
        assert g["citation"]["url"].startswith("https://")
        assert "](<" not in g["citation"]["url"]


@pytest.mark.asyncio
async def test_search_jobs_actions_only(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        found = await client.call_tool(
            "search_guidelines", {"jobs": "actions", "limit": 200}
        )
        data = found.data
        assert data["total"] == 40
        _assert_index_rows(data["guidelines"])
        assert all(row["id"].startswith("actions.") for row in data["guidelines"])
        assert all("actions" in row["jobs"] for row in data["guidelines"])
        assert not any(row["id"].startswith("forms.") for row in data["guidelines"])


@pytest.mark.asyncio
async def test_search_lane_forms_only(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        found = await client.call_tool(
            "search_guidelines", {"lane": "forms", "limit": 200}
        )
        data = found.data
        assert data["total"] == 54
        _assert_index_rows(data["guidelines"])
        assert all(row["lane"] == "forms" for row in data["guidelines"])
        assert all(row["id"].startswith("forms.") for row in data["guidelines"])
        for seed in LIVE_SEED:
            assert seed in {row["id"] for row in data["guidelines"]}


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
        assert g["citation"]["url"].startswith("https://")
        assert "](<" not in g["citation"]["url"]


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
        assert g["citation"]["url"].startswith("https://")
        assert "](<" not in g["citation"]["url"]


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
        assert g["citation"]["url"].startswith("https://")
        assert "](<" not in g["citation"]["url"]


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
        assert g["citation"]["url"].startswith("https://")
        assert "](<" not in g["citation"]["url"]


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
                    "forms.field_labels.visible_label",
                    "actions.button_groups",
                ],
            },
        )
        result = audited.data
        ids = [row["id"] for row in result["guidelines"]]
        assert ids == [
            "forms.field_labels.visible_label",
            "actions.button_groups",
        ]
        assert "error" not in result
        assert "verdict" not in result
        for row in result["guidelines"]:
            assert set(row) == {"id", "title", "rule", "pass_when", "fail_when"}


@pytest.mark.asyncio
async def test_audit_schema_shows_jobs_enum_not_target(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        tools = await client.list_tools()
    audit_tool = next(t for t in tools if t.name == "audit")
    schema = audit_tool.inputSchema
    props = schema["properties"]
    assert "target" not in props
    assert "content" not in props
    assert "avoid_placeholder_as_label" in props["jobs"]["enum"]
    assert "forms" in props["jobs"]["enum"]
    assert "Does not take a file" in (audit_tool.description or "")
    assert "Does not return pass or fail" in (audit_tool.description or "")


@pytest.mark.asyncio
async def test_audit_jobs_returns_criteria(live_catalog: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        audited = await client.call_tool(
            "audit", {"jobs": "avoid_placeholder_as_label"}
        )
        result = audited.data
        assert result["count"] >= 1
        assert "verdict" not in result
        assert "summary" not in result
        row = result["guidelines"][0]
        assert set(row) == {"id", "title", "rule", "pass_when", "fail_when"}
