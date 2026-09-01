from __future__ import annotations

from pathlib import Path

import pytest
from fastmcp import Client

from open_ux.auth import register
from open_ux.server import create_mcp
from open_ux.settings import Settings
from open_ux.store import get_store

MARKER = "UNIQUE_RAW_PAYLOAD_SHOULD_NEVER_BE_STORED_xyzzy"


@pytest.mark.asyncio
async def test_audit_tool_does_not_write_raw_content(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=True)
    async with Client(mcp) as client:
        await client.call_tool(
            "audit",
            {"target": {"type": "html", "content": f"<form>{MARKER}</form>"}},
        )
    store = get_store(Settings.load(hosted=True))
    dump = store.dump_text()
    assert MARKER not in dump


def test_telemetry_stores_length_and_hash_only(tmp_env: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    store = get_store(settings)
    from open_ux.catalog import content_hash

    payload = f"<form>{MARKER}</form>"
    store.record_telemetry(
        key_hash=issued.key_hash,
        tool="audit",
        target_type="html",
        content_length=len(payload.encode("utf-8")),
        content_hash=content_hash(payload),
        guideline_ids=[],
        verdicts={"pass": 0, "fail": 0, "incomplete": 0},
    )
    dump = store.dump_text()
    assert MARKER not in dump
    assert issued.key not in dump
    assert issued.key_hash in dump
    rows = store.telemetry_rows()
    assert rows[-1]["content_length"] == len(payload.encode("utf-8"))
    assert rows[-1]["content_hash"] == content_hash(payload)
    assert "content" not in rows[-1] or rows[-1].get("content") is None


def test_sqlite_schema_has_no_content_column(tmp_env: Path) -> None:
    dump = get_store(Settings.load(hosted=True)).dump_text()
    assert "CREATE TABLE telemetry" in dump
    # Fail if a raw payload column is added later.
    assert "audit_content" not in dump
    assert "prompt" not in dump.lower() or "prompt" not in dump.split("CREATE TABLE telemetry")[1].split(";")[0]


@pytest.mark.asyncio
async def test_stdio_has_no_hosted_telemetry(tmp_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPEN_UX_TELEMETRY", "0")
    from open_ux.store import reset_store_for_tests

    reset_store_for_tests()
    mcp = create_mcp(hosted=False)
    async with Client(mcp) as client:
        await client.call_tool(
            "audit",
            {"target": {"type": "description", "content": MARKER}},
        )
    store = get_store(Settings.load(hosted=False))
    assert store.telemetry_rows() == []
    assert MARKER not in store.dump_text()
