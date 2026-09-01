from __future__ import annotations

from pathlib import Path

import pytest
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


def test_register_issues_uxmcp_key(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        page = client.get("/register")
        assert page.status_code == 200
        assert "text/html" in page.headers.get("content-type", "")
        assert ">Get a key</p>" in page.text

        response = client.post("/register", json={"email": "ada@example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["key"].startswith("uxmcp_")
        assert data["email"] == "ada@example.com"

        denied = client.post("/mcp", json={})
        assert denied.status_code == 401

        allowed = client.post(
            "/mcp",
            headers={"Authorization": f"Bearer {data['key']}"},
            json={},
        )
        assert allowed.status_code != 401


def test_self_host_has_no_register(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=False)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        response = client.post("/register", json={"email": "ada@example.com"})
        assert response.status_code == 400
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
