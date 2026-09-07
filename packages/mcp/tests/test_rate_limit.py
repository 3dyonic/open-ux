from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from open_ux.auth import register
from open_ux.http_app import build_app
from open_ux.server import create_mcp
from open_ux.settings import MCP_IP_PER_MINUTE, RATE_PER_MINUTE, Settings
from open_ux.store import get_store


def _limited_client(_tmp_env: Path) -> TestClient:
    return TestClient(build_app())


def test_unauthenticated_mcp_ip_rate_limited(tmp_env: Path) -> None:
    with _limited_client(tmp_env) as client:
        statuses = [
            client.post("/mcp", json={}).status_code
            for _ in range(MCP_IP_PER_MINUTE)
        ]
        limited = client.post("/mcp", json={})
    assert statuses == [401] * MCP_IP_PER_MINUTE
    assert limited.status_code == 429
    assert limited.json()["error"] == "rate_limited"


def test_valid_key_hits_per_key_limit(tmp_env: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    store = get_store(settings)
    for _ in range(RATE_PER_MINUTE - 1):
        ok, _window = store.consume_rate(issued.key_hash)
        assert ok
    with _limited_client(tmp_env) as client:
        headers = {"Authorization": f"Bearer {issued.key}"}
        first = client.post("/mcp", headers=headers, json={})
        second = client.post("/mcp", headers=headers, json={})
    assert first.status_code != 401
    assert first.status_code != 429
    assert second.status_code == 429
    assert second.json()["error"] == "rate_limited"


def test_health_is_not_rate_limited(tmp_env: Path) -> None:
    with _limited_client(tmp_env) as client:
        statuses = [client.get("/health").status_code for _ in range(MCP_IP_PER_MINUTE + 10)]
    assert statuses == [200] * (MCP_IP_PER_MINUTE + 10)


def test_self_host_mcp_is_not_ip_limited(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=False)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        statuses = [client.post("/mcp", json={}).status_code for _ in range(MCP_IP_PER_MINUTE + 1)]
    assert 429 not in statuses
