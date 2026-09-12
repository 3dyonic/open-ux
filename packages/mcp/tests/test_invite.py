from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from open_ux.auth import AuthError, hash_key, normalize_email, register, request_invite
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
        waitlist = client.get(
            "/admin/invite/waitlist",
            headers={"Authorization": "Bearer test-admin-token"},
        )
        assert waitlist.status_code == 400
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


@pytest.mark.parametrize(
    "payload",
    [
        "<script>alert(1)</script>@x.com",
        'ada@example.com"><img src=x onerror=alert(1)>',
        '"ada"@example.com',
        "ada@example.com\r\nBcc:evil@x.com",
        "ada@example.com\x00",
        {"$gt": ""},
        ["ada@example.com"],
        "a" * 300 + "@example.com",
        "ada@exam ple.com",
        "javascript:alert(1)@x.com",
        "ada..tag@example.com",
    ],
)
def test_normalize_email_rejects_injection(payload: object) -> None:
    with pytest.raises(AuthError):
        normalize_email(payload)


def test_normalize_email_accepts_plus_and_casefold() -> None:
    assert normalize_email("Ada+Tag@Example.com") == "ada+tag@example.com"


def test_invite_request_rejects_script_and_object(tmp_env: Path) -> None:
    settings = Settings.load(hosted=True)
    store = get_store(settings)
    with _hosted_client(tmp_env) as client:
        scripted = client.post(
            "/invite/request",
            json={"email": "<script>alert(1)</script>@x.com"},
        )
        typed = client.post("/invite/request", json={"email": {"$gt": ""}})
    assert scripted.status_code == 400
    assert typed.status_code == 400
    assert store.waitlist_count() == 0


def test_invite_request_accepts_plus_tag(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        response = client.post(
            "/invite/request", json={"email": "Ada+Tag@Example.com"}
        )
    assert response.status_code == 200
    assert response.json()["email"] == "ada+tag@example.com"


@pytest.mark.parametrize(
    "token",
    ["<script>", "uxmcp_notaninvite", {"x": 1}, "inv_<script>alert(1)"],
)
def test_redeem_rejects_bad_tokens(tmp_env: Path, token: object) -> None:
    with _hosted_client(tmp_env) as client:
        response = client.post("/invite/redeem", json={"token": token})
    assert response.status_code == 400
    assert "Invite invalid or already used" in response.json()["error"]


def test_invite_request_rate_limited(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        statuses = [
            client.post(
                "/invite/request", json={"email": f"ada{i}@example.com"}
            ).status_code
            for i in range(6)
        ]
        assert statuses[:5] == [200, 200, 200, 200, 200]
        assert statuses[5] == 429


def test_invite_pages_send_security_headers(tmp_env: Path, monkeypatch) -> None:
    dist = tmp_env / "web-dist"
    dist.mkdir()
    (dist / "index.html").write_text(
        "<!DOCTYPE html><html><body>open-ux-shell</body></html>",
        encoding="utf-8",
    )
    monkeypatch.setenv("OPEN_UX_WEB_DIST", str(dist))
    with _hosted_client(tmp_env) as client:
        for path in ("/invite", "/invite/requested", "/invite/redeem"):
            response = client.get(path)
            assert response.status_code == 200, path
            assert response.headers["x-content-type-options"] == "nosniff"
            assert response.headers["x-frame-options"] == "DENY"
            assert (
                response.headers["referrer-policy"]
                == "strict-origin-when-cross-origin"
            )


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


def test_admin_approve_is_json_only_no_html(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        get = client.get("/admin/invite/approve")
        assert get.status_code != 200
        assert "text/html" not in get.headers.get("content-type", "")

        posted = client.post(
            "/admin/invite/approve",
            headers={"Authorization": "Bearer test-admin-token"},
            json={"email": "ada@example.com"},
        )
        assert posted.status_code == 200
        assert posted.headers.get("content-type", "").startswith("application/json")
        assert "text/html" not in posted.headers.get("content-type", "")


def test_admin_waitlist_empty(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        response = client.get(
            "/admin/invite/waitlist",
            headers={"Authorization": "Bearer test-admin-token"},
        )
        assert response.status_code == 200
        assert response.headers.get("content-type", "").startswith("application/json")
        assert response.json() == {"items": [], "next_cursor": None}


def test_admin_waitlist_after_request_invite(tmp_env: Path) -> None:
    settings = Settings.load(hosted=True)
    store = get_store(settings)
    request_invite("Ada@Example.com", settings=settings, store=store)
    request_invite("second@example.com", settings=settings, store=store)
    with _hosted_client(tmp_env) as client:
        response = client.get(
            "/admin/invite/waitlist",
            headers={"Authorization": "Bearer test-admin-token"},
        )
    assert response.status_code == 200
    body = response.json()
    items = body["items"]
    emails = [row["email"] for row in items]
    assert emails == ["second@example.com", "ada@example.com"]
    for row in items:
        assert set(row.keys()) == {"email", "created_at"}
        parsed = datetime.fromisoformat(row["created_at"])
        assert parsed.tzinfo is not None


def test_admin_waitlist_keyset_pagination(tmp_env: Path) -> None:
    settings = Settings.load(hosted=True)
    store = get_store(settings)
    rows = [
        ("a@example.com", "2024-01-01T00:00:00+00:00"),
        ("b@example.com", "2024-01-02T00:00:00+00:00"),
        ("c@example.com", "2024-01-03T00:00:00+00:00"),
    ]
    with store.cursor() as cur:
        for email, created_at in rows:
            cur.execute(
                "INSERT INTO waitlist(email, created_at) VALUES (?, ?)",
                (email, created_at),
            )

    with _hosted_client(tmp_env) as client:
        first = client.get(
            "/admin/invite/waitlist?limit=2",
            headers={"Authorization": "Bearer test-admin-token"},
        )
        assert first.status_code == 200
        first_body = first.json()
        assert [r["email"] for r in first_body["items"]] == [
            "c@example.com",
            "b@example.com",
        ]
        assert first_body["next_cursor"] is not None

        second = client.get(
            f"/admin/invite/waitlist?limit=2&before={first_body['next_cursor']}",
            headers={"Authorization": "Bearer test-admin-token"},
        )
        assert second.status_code == 200
        second_body = second.json()
        assert [r["email"] for r in second_body["items"]] == ["a@example.com"]
        assert second_body["next_cursor"] is None


def test_admin_waitlist_pagination_limit_caps_at_page_size(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        response = client.get(
            "/admin/invite/waitlist?limit=99999",
            headers={"Authorization": "Bearer test-admin-token"},
        )
        assert response.status_code == 200
        assert response.json() == {"items": [], "next_cursor": None}


def test_admin_waitlist_bad_cursor_returns_first_page(tmp_env: Path) -> None:
    settings = Settings.load(hosted=True)
    store = get_store(settings)
    store.add_waitlist("only@example.com")
    with _hosted_client(tmp_env) as client:
        response = client.get(
            "/admin/invite/waitlist?before=not-a-real-cursor",
            headers={"Authorization": "Bearer test-admin-token"},
        )
        assert response.status_code == 200
        body = response.json()
        assert [r["email"] for r in body["items"]] == ["only@example.com"]
        assert body["next_cursor"] is None


def test_admin_waitlist_requires_bearer(tmp_env: Path) -> None:
    with _hosted_client(tmp_env) as client:
        missing = client.get("/admin/invite/waitlist")
        assert missing.status_code == 401
        wrong = client.get(
            "/admin/invite/waitlist",
            headers={"Authorization": "Bearer nope"},
        )
        assert wrong.status_code == 401


def test_admin_waitlist_response_has_no_secrets(tmp_env: Path) -> None:
    settings = Settings.load(hosted=True)
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
        listed = client.get(
            "/admin/invite/waitlist",
            headers={"Authorization": "Bearer test-admin-token"},
        )
    assert listed.status_code == 200
    body = listed.json()
    raw = listed.text
    assert set(body.keys()) == {"items", "next_cursor"}
    for row in body["items"]:
        assert set(row.keys()) == {"email", "created_at"}
    assert "uxmcp_" not in raw
    assert "inv_" not in raw
    assert "audit.content" not in raw
    assert '"content"' not in raw
    assert hash_key(token, settings.pepper) not in raw
    assert hash_key(key, settings.pepper) not in raw
    payload = json.dumps(body)
    assert "uxmcp_" not in payload
    assert "inv_" not in payload
    assert "content" not in payload
