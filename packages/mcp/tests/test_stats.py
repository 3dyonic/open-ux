from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from open_ux.server import create_mcp
from open_ux.settings import Settings
from open_ux.store import get_store


def _hosted_client(tmp_env: Path) -> TestClient:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    return TestClient(app)


def test_admin_stats_requires_bearer(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        missing = client.get("/admin/stats")
        assert missing.status_code == 401
        wrong = client.get("/admin/stats", headers={"Authorization": "Bearer nope"})
        assert wrong.status_code == 401


def test_admin_stats_disabled_self_host(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=False)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        response = client.get(
            "/admin/stats", headers={"Authorization": "Bearer test-admin-token"}
        )
        assert response.status_code == 400


def test_admin_stats_empty(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        response = client.get(
            "/admin/stats", headers={"Authorization": "Bearer test-admin-token"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total_requests"] == 0
        assert body["unique_keys"] == 0
        assert body["requests_by_tool"] == {}
        assert body["requests_by_day"] == {}
        assert body["top_guideline_ids"] == []
        assert body["accounts"] == 0
        assert body["invites"] == 0
        assert body["waitlist"] == 0


def test_admin_stats_aggregates_telemetry(tmp_env: Path) -> None:
    settings = Settings.load(hosted=True)
    store = get_store(settings)
    store.record_telemetry(
        key_hash="hash-a",
        tool="pack",
        target_type=None,
        content_length=None,
        content_hash=None,
        guideline_ids=["rule.one", "rule.two"],
        verdicts=None,
    )
    store.record_telemetry(
        key_hash="hash-a",
        tool="pack",
        target_type=None,
        content_length=None,
        content_hash=None,
        guideline_ids=["rule.one"],
        verdicts=None,
    )
    store.record_telemetry(
        key_hash="hash-b",
        tool="list_components",
        target_type=None,
        content_length=None,
        content_hash=None,
        guideline_ids=None,
        verdicts=None,
    )
    store.add_waitlist("ada@example.com")

    with _hosted_client(tmp_env) as client:
        response = client.get(
            "/admin/stats", headers={"Authorization": "Bearer test-admin-token"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["total_requests"] == 3
        assert body["unique_keys"] == 2
        assert body["requests_by_tool"] == {"pack": 2, "list_components": 1}
        assert sum(body["requests_by_day"].values()) == 3
        assert body["top_guideline_ids"][0] == {"id": "rule.one", "count": 2}
        assert body["waitlist"] == 1
        assert "hash-a" not in response.text
        assert "hash-b" not in response.text
