from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client

from open_ux.catalog import EMPTY_NOTE
from open_ux.server import create_mcp


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

        audited = await client.call_tool(
            "audit",
            {
                "target": {
                    "type": "html",
                    "content": "<input placeholder='email only'>",
                }
            },
        )
        result = audited.data
        assert result["results"] == []
        assert result["summary"] == {"pass": 0, "fail": 0, "incomplete": 0}
        assert result["catalog"]["status"] == "empty"
        assert EMPTY_NOTE in result["note"]


@pytest.mark.asyncio
async def test_unknown_id_is_incomplete_not_invented(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        audited = await client.call_tool(
            "audit",
            {
                "target": {"type": "jsx", "content": "<input />"},
                "guideline_ids": ["not.a.real.rule"],
            },
        )
        result = audited.data
        assert result["results"][0]["verdict"] == "incomplete"
        assert result["results"][0]["guideline_id"] == "not.a.real.rule"
        assert "Unknown guideline_id" in result["results"][0]["reasons"][0]
