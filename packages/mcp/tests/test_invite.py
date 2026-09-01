from __future__ import annotations

import json
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from open_ux.auth import hash_key, register, request_invite
from open_ux.server import create_mcp
from open_ux.settings import Settings
from open_ux.store import get_store
from open_ux.__main__ import main


def _hosted_client(tmp_env: Path) -> TestClient:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    return TestClient(app)


def test_mcp_unauthorized_without_key(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        response = client.post("/mcp", json={})
        assert response.status_code == 401


def test_register_get_redirects_to_invite(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        page = client.get("/register", follow_redirects=False)
        assert page.status_code == 302
        assert page.headers["location"] == "/invite"


def test_register_post_waitlists_and_does_not_mint(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        response = client.post("/register", json={"email": "ada@example.com"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "waitlisted"
        assert "key" not in data
        denied = client.post("/mcp", json={})
        assert denied.status_code == 401


def test_self_host_has_no_invite(tmp_env: Path) -> None:
    mcp = create_mcp(hosted=False)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        response = client.post("/invite/request", json={"email": "ada@example.com"})
        assert response.status_code == 400
        legacy = client.post("/register", json={"email": "ada@example.com"})
        assert legacy.status_code == 400
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


def test_invite_request_approve_redeem_burn(tmp_env: Path) -> None:
    settings = Settings.load(hosted=True)
    store = get_store(settings)
    with _hosted_client(tmp_env) as client:
        first = client.post("/invite/request", json={"email": "Ada@Example.com"})
        assert first.status_code == 200
        assert first.json()["email"] == "ada@example.com"
        assert first.json()["status"] == "waitlisted"
        assert store.waitlist_has("ada@example.com")
        assert store.waitlist_count() == 1

        again = client.post("/invite/request", json={"email": "ada@example.com"})
        assert again.status_code == 200
        assert store.waitlist_count() == 1

        denied = client.post(
            "/admin/invite/approve",
            json={"email": "ada@example.com"},
        )
        assert denied.status_code == 401

        wrong = client.post(
            "/admin/invite/approve",
            headers={"Authorization": "Bearer nope"},
            json={"email": "ada@example.com"},
        )
        assert wrong.status_code == 401

        approved = client.post(
            "/admin/invite/approve",
            headers={"Authorization": "Bearer test-admin-token"},
            json={"email": "ada@example.com"},
        )
        assert approved.status_code == 200
        body = approved.json()
        token = body["token"]
        assert token.startswith("inv_")
        assert body["redeem_url"].startswith("https://open-ux.test/invite/redeem?token=")
        assert token not in store.dump_text()

        minted = client.post("/invite/redeem", json={"token": token})
        assert minted.status_code == 200
        key = minted.json()["key"]
        assert key.startswith("uxmcp_")
        assert minted.json()["email"] == "ada@example.com"
        assert key not in store.dump_text()
        assert hash_key(key, settings.pepper) in store.dump_text()

        burned = client.post("/invite/redeem", json={"token": token})
        assert burned.status_code == 400
        assert "Invite invalid or already used" in burned.json()["error"]

        allowed = client.post(
            "/mcp",
            headers={"Authorization": f"Bearer {key}"},
            json={},
        )
        assert allowed.status_code != 401


def test_invalid_email_request_error(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        response = client.post("/invite/request", json={"email": "not-an-email"})
        assert response.status_code == 400
        assert response.json()["error"] == "Enter a valid email to request an invite."


def test_expired_invite_cannot_redeem(tmp_env: Path) -> None:
    settings = Settings.load(hosted=True)
    store = get_store(settings)
    request_invite("ada@example.com", settings=settings, store=store)
    raw = "inv_expiredtokenvalue"
    store.create_invite(
        "ada@example.com",
        hash_key(raw, settings.pepper),
        "2000-01-01T00:00:00+00:00",
    )
    with _hosted_client(tmp_env) as client:
        response = client.post("/invite/redeem", json={"token": raw})
        assert response.status_code == 400


def test_approve_invite_cli(tmp_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["approve-invite", "ada@example.com"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["email"] == "ada@example.com"
    assert out["token"].startswith("inv_")
    assert "/invite/redeem?token=" in out["redeem_url"]
