from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from starlette.testclient import TestClient

from open_ux.auth import register
from open_ux.server import create_mcp
from open_ux.settings import Settings
from open_ux.store import get_store


def _hosted_client(_tmp_env: Path) -> TestClient:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    return TestClient(app)


def _call(client: TestClient, key: str, name: str, arguments: dict[str, Any]) -> None:
    headers = {
        "Authorization": f"Bearer {key}",
        "Accept": "application/json, text/event-stream",
        "Content-Type": "application/json",
    }
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }
    response = client.post("/mcp", headers=headers, json=body)
    assert response.status_code == 200, response.text


def _rows(tmp_env: Path) -> list[dict[str, Any]]:
    settings = Settings.load(hosted=True)
    store = get_store(settings)
    with store.cursor() as cur:
        cur.execute(
            "SELECT tool, target_type, target_id, req_offset, req_limit, "
            "content_length, verdicts, guideline_ids FROM telemetry ORDER BY id"
        )
        return [dict(row) for row in cur.fetchall()]


def test_get_guideline_records_target_and_helpful_verdict(live_catalog: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    with _hosted_client(live_catalog) as client:
        _call(
            client,
            issued.key,
            "get_guideline",
            {"id": "ant.checkbox-vs-switch", "helpful": True},
        )
    row = _rows(live_catalog)[0]
    assert row["tool"] == "get_guideline"
    assert row["target_type"] == "guideline"
    assert row["target_id"] == "ant.checkbox-vs-switch"
    assert json.loads(row["verdicts"]) == {"helpful": True}


def test_get_guideline_without_helpful_records_no_verdict(live_catalog: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    with _hosted_client(live_catalog) as client:
        _call(client, issued.key, "get_guideline", {"id": "ant.checkbox-vs-switch"})
    row = _rows(live_catalog)[0]
    assert row["verdicts"] is None


def test_get_guideline_helpful_false_is_recorded_not_dropped(live_catalog: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    with _hosted_client(live_catalog) as client:
        _call(
            client,
            issued.key,
            "get_guideline",
            {"id": "ant.checkbox-vs-switch", "helpful": False},
        )
    row = _rows(live_catalog)[0]
    assert json.loads(row["verdicts"]) == {"helpful": False}


def test_pack_classifies_card_scope(live_catalog: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    with _hosted_client(live_catalog) as client:
        _call(
            client,
            issued.key,
            "pack",
            {"jobs": "protect_destructive_and_leave", "limit": 5},
        )
    row = _rows(live_catalog)[0]
    assert row["tool"] == "pack"
    assert row["target_type"] == "card"
    assert row["target_id"] == "protect_destructive_and_leave"
    assert row["req_offset"] == 0
    assert row["req_limit"] == 5
    assert json.loads(row["guideline_ids"])


def test_pack_classifies_container_scope(live_catalog: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    with _hosted_client(live_catalog) as client:
        _call(client, issued.key, "pack", {"jobs": "forms", "limit": 5})
    row = _rows(live_catalog)[0]
    assert row["target_type"] == "container"
    assert row["target_id"] == "forms_and_input"


def test_pack_classifies_guideline_ids_scope(live_catalog: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    with _hosted_client(live_catalog) as client:
        _call(
            client,
            issued.key,
            "pack",
            {"guideline_ids": ["ant.checkbox-vs-switch"]},
        )
    row = _rows(live_catalog)[0]
    assert row["target_type"] == "guideline_ids"
    assert row["target_id"] is None


def test_search_guidelines_classifies_leaf_scope(live_catalog: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    with _hosted_client(live_catalog) as client:
        _call(
            client,
            issued.key,
            "search_guidelines",
            {"jobs": "disable_or_confirm_destructive", "limit": 5, "offset": 0},
        )
    row = _rows(live_catalog)[0]
    assert row["tool"] == "search_guidelines"
    assert row["target_type"] == "leaf"
    assert row["target_id"] == "disable_or_confirm_destructive"
    assert row["req_offset"] == 0
    assert row["req_limit"] == 5


def test_list_situations_classifies_container_scope(live_catalog: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    with _hosted_client(live_catalog) as client:
        _call(client, issued.key, "list_situations", {"container": "actions"})
    row = _rows(live_catalog)[0]
    assert row["tool"] == "list_situations"
    assert row["target_type"] == "container"


def test_get_situation_records_card_target(live_catalog: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    with _hosted_client(live_catalog) as client:
        _call(
            client,
            issued.key,
            "get_situation",
            {"id": "protect_destructive_and_leave"},
        )
    row = _rows(live_catalog)[0]
    assert row["tool"] == "get_situation"
    assert row["target_type"] == "card"
    assert row["target_id"] == "protect_destructive_and_leave"


def test_get_component_records_component_target(live_catalog: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    with _hosted_client(live_catalog) as client:
        _call(client, issued.key, "get_component", {"id": "popconfirm"})
    row = _rows(live_catalog)[0]
    assert row["tool"] == "get_component"
    assert row["target_type"] == "component"
    assert row["target_id"] == "popconfirm"


def test_list_guidelines_records_paging(live_catalog: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    with _hosted_client(live_catalog) as client:
        _call(client, issued.key, "list_guidelines", {"limit": 10, "offset": 20})
    row = _rows(live_catalog)[0]
    assert row["tool"] == "list_guidelines"
    assert row["req_offset"] == 20
    assert row["req_limit"] == 10


def test_suggest_situations_records_content_length(live_catalog: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    with _hosted_client(live_catalog) as client:
        _call(
            client,
            issued.key,
            "suggest_situations",
            {"task_text": "help the user leave a form without losing work"},
        )
    row = _rows(live_catalog)[0]
    assert row["tool"] == "suggest_situations"
    assert row["content_length"] == len("help the user leave a form without losing work")
