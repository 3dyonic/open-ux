from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from open_ux.auth import register
from open_ux.server import create_mcp
from open_ux.settings import Settings
from open_ux.store import get_store


def _hosted_client(tmp_env: Path) -> TestClient:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    return TestClient(app)


def test_mcp_unauthorized_without_key(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        response = client.post("/mcp", json={})
        assert response.status_code == 401


def test_redeemed_key_authorizes_mcp(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        client.post("/invite/request", json={"email": "ada@example.com"})
        approved = client.post(
            "/admin/invite/approve",
            headers={"Authorization": "Bearer test-admin-token"},
            json={"email": "ada@example.com"},
        )
        token = approved.json()["token"]
        minted = client.post("/invite/redeem", json={"token": token})
        key = minted.json()["key"]
        allowed = client.post(
            "/mcp",
            headers={"Authorization": f"Bearer {key}"},
            json={},
        )
        assert allowed.status_code != 401


def test_self_host_mcp_open_without_key(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=False)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        open_mcp = client.post("/mcp", json={})
        assert open_mcp.status_code != 401


def test_account_delete_wipes_keys(tmp_env: Path) -> None:
    settings = Settings.load(hosted=True)
    issued = register("ada@example.com", settings=settings)
    store = get_store(settings)
    assert store.lookup_key(issued.key_hash) is not None
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        gone = client.post(
            "/account/delete",
            json={"email": "ada@example.com", "key": issued.key},
        )
        assert gone.status_code == 200
        assert gone.json()["deleted"] is True
    assert store.lookup_key(issued.key_hash) is None
