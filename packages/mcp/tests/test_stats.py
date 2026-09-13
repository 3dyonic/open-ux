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


def test_admin_telemetry_page_hosted(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        response = client.get("/admin/telemetry")
        assert response.status_code == 200


def test_admin_telemetry_page_disabled_self_host(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=False)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        response = client.get("/admin/telemetry")
        assert response.status_code == 404


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
        assert len(body["requests_by_day"]) == body["window_days"]
        assert set(body["requests_by_day"].values()) == {0}
        assert body["top_guideline_ids"] == []
        assert body["accounts"] == 0
        assert body["invites"] == 0
        assert body["waitlist"] == 0


def test_admin_stats_zero_fills_missing_days(tmp_env: Path) -> None:
    from datetime import datetime, timedelta, timezone

    settings = Settings.load(hosted=True)
    store = get_store(settings)
    today = datetime.now(timezone.utc).date()
    with store.cursor() as cur:
        cur.execute(
            "INSERT INTO telemetry(key_hash, tool, created_at) VALUES (?, ?, ?)",
            ("hash-a", "pack", f"{today.isoformat()}T00:00:00+00:00"),
        )

    with _hosted_client(tmp_env) as client:
        response = client.get(
            "/admin/stats", headers={"Authorization": "Bearer test-admin-token"}
        )
        body = response.json()
        by_day = body["requests_by_day"]
        assert len(by_day) == body["window_days"]
        days = list(by_day.keys())
        assert days == sorted(days)
        expected_days = [
            (today - timedelta(days=offset)).isoformat()
            for offset in range(body["window_days"] - 1, -1, -1)
        ]
        assert days == expected_days
        assert by_day[today.isoformat()] == 1
        yesterday = (today - timedelta(days=1)).isoformat()
        assert by_day[yesterday] == 0


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


def test_admin_sessions_requires_bearer(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        missing = client.get("/admin/sessions")
        assert missing.status_code == 401
        wrong = client.get("/admin/sessions", headers={"Authorization": "Bearer nope"})
        assert wrong.status_code == 401


def test_admin_sessions_disabled_self_host(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=False)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        response = client.get(
            "/admin/sessions", headers={"Authorization": "Bearer test-admin-token"}
        )
        assert response.status_code == 400


def test_admin_sessions_empty(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        response = client.get(
            "/admin/sessions", headers={"Authorization": "Bearer test-admin-token"}
        )
        assert response.status_code == 200
        assert response.json() == {"items": [], "next_cursor": None}


def test_admin_sessions_groups_by_gap(tmp_env: Path) -> None:
    from datetime import datetime, timedelta, timezone

    settings = Settings.load(hosted=True)
    store = get_store(settings)
    now = datetime.now(timezone.utc)
    with store.cursor() as cur:
        rows = [
            ("hash-a", "suggest_situations", None, None, now - timedelta(hours=2)),
            (
                "hash-a",
                "pack",
                "card",
                "protect_destructive_and_leave",
                now - timedelta(hours=2) + timedelta(seconds=5),
            ),
            (
                "hash-a",
                "pack",
                "container",
                "forms_and_input",
                now - timedelta(minutes=10),
            ),
            ("hash-b", "get_component", "component", "popconfirm", now - timedelta(minutes=5)),
        ]
        for key_hash, tool, target_type, target_id, created_at in rows:
            cur.execute(
                "INSERT INTO telemetry(key_hash, tool, target_type, target_id, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (key_hash, tool, target_type, target_id, created_at.isoformat()),
            )

    with _hosted_client(tmp_env) as client:
        response = client.get(
            "/admin/sessions", headers={"Authorization": "Bearer test-admin-token"}
        )
        assert response.status_code == 200
        items = {row["key_hash"]: row for row in response.json()["items"]}
        assert items["hash-a"]["call_count"] == 3
        assert items["hash-a"]["session_count"] == 2
        assert items["hash-b"]["call_count"] == 1
        assert items["hash-b"]["session_count"] == 1
        assert items["hash-b"]["top_target"] == "popconfirm"


def test_admin_sessions_detail_returns_ordered_steps(tmp_env: Path) -> None:
    from datetime import datetime, timedelta, timezone

    settings = Settings.load(hosted=True)
    store = get_store(settings)
    now = datetime.now(timezone.utc)
    with store.cursor() as cur:
        rows = [
            ("hash-a", "suggest_situations", None, None, now - timedelta(hours=2)),
            (
                "hash-a",
                "get_guideline",
                "guideline",
                "ant.checkbox-vs-switch",
                now - timedelta(hours=2) + timedelta(seconds=5),
            ),
            (
                "hash-a",
                "pack",
                "container",
                "forms_and_input",
                now - timedelta(minutes=10),
            ),
        ]
        for key_hash, tool, target_type, target_id, created_at in rows:
            cur.execute(
                "INSERT INTO telemetry(key_hash, tool, target_type, target_id, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (key_hash, tool, target_type, target_id, created_at.isoformat()),
            )

    with _hosted_client(tmp_env) as client:
        response = client.get(
            "/admin/sessions/hash-a", headers={"Authorization": "Bearer test-admin-token"}
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["items"]) == 2
        newest, oldest = body["items"]
        assert newest["call_count"] == 1
        assert newest["steps"][0]["tool"] == "pack"
        assert oldest["call_count"] == 2
        assert [s["tool"] for s in oldest["steps"]] == ["suggest_situations", "get_guideline"]
        assert newest["session_id"].startswith("sess_")
        assert oldest["tool_sequence"] == "suggest_situations→get_guideline"
        assert oldest["target_id"] == "ant.checkbox-vs-switch"
        assert newest["target_id"] == "forms_and_input"
        assert "duration_seconds" in oldest

        summary = body["summary"]
        assert summary["key_hash"] == "hash-a"
        assert summary["call_count"] == 3
        assert summary["session_count"] == 2
        assert summary["top_target"] == "ant.checkbox-vs-switch"
        assert summary["first_seen"] is not None
        assert summary["last_seen"] is not None


def test_admin_sessions_detail_includes_req_flags_and_result_ids(tmp_env: Path) -> None:
    settings = Settings.load(hosted=True)
    store = get_store(settings)
    store.record_telemetry(
        key_hash="hash-a",
        tool="get_component",
        target_type="component",
        target_id="checkbox",
        content_length=None,
        content_hash=None,
        guideline_ids=None,
        verdicts=None,
        req_flags={"include_keywords": True},
        result_count=None,
        result_ids=None,
    )
    store.record_telemetry(
        key_hash="hash-a",
        tool="list_situations",
        target_type=None,
        target_id=None,
        content_length=None,
        content_hash=None,
        guideline_ids=None,
        verdicts=None,
        req_flags=None,
        result_count=2,
        result_ids=["card.one", "card.two"],
    )

    with _hosted_client(tmp_env) as client:
        response = client.get(
            "/admin/sessions/hash-a", headers={"Authorization": "Bearer test-admin-token"}
        )
        assert response.status_code == 200
        body = response.json()
        steps = body["items"][0]["steps"]
        assert len(steps) == 2
        get_component_step, list_situations_step = steps
        assert get_component_step["tool"] == "get_component"
        assert get_component_step["req_flags"] == {"include_keywords": True}
        assert get_component_step["result_count"] is None
        assert get_component_step["result_ids"] is None
        assert list_situations_step["tool"] == "list_situations"
        assert list_situations_step["req_flags"] is None
        assert list_situations_step["result_count"] == 2
        assert list_situations_step["result_ids"] == ["card.one", "card.two"]


def test_admin_sessions_detail_empty_summary(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        response = client.get(
            "/admin/sessions/nobody", headers={"Authorization": "Bearer test-admin-token"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["items"] == []
        assert body["summary"] == {
            "key_hash": "nobody",
            "call_count": 0,
            "session_count": 0,
            "first_seen": None,
            "last_seen": None,
            "top_target": None,
        }


def test_admin_sessions_detail_requires_bearer(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        response = client.get("/admin/sessions/hash-a")
        assert response.status_code == 401


def test_admin_sessions_keyset_pagination(tmp_env: Path) -> None:
    from datetime import datetime, timedelta, timezone

    settings = Settings.load(hosted=True)
    store = get_store(settings)
    now = datetime.now(timezone.utc)
    with store.cursor() as cur:
        for i, key_hash in enumerate(["hash-a", "hash-b", "hash-c"]):
            cur.execute(
                "INSERT INTO telemetry(key_hash, tool, created_at) VALUES (?, ?, ?)",
                (key_hash, "pack", (now - timedelta(minutes=i)).isoformat()),
            )

    with _hosted_client(tmp_env) as client:
        first = client.get(
            "/admin/sessions?limit=2", headers={"Authorization": "Bearer test-admin-token"}
        )
        first_body = first.json()
        assert [r["key_hash"] for r in first_body["items"]] == ["hash-a", "hash-b"]
        assert first_body["next_cursor"] is not None

        second = client.get(
            f"/admin/sessions?limit=2&before={first_body['next_cursor']}",
            headers={"Authorization": "Bearer test-admin-token"},
        )
        second_body = second.json()
        assert [r["key_hash"] for r in second_body["items"]] == ["hash-c"]
        assert second_body["next_cursor"] is None
