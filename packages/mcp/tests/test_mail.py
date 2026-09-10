from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from starlette.testclient import TestClient

from open_ux.auth import approve_invite
from open_ux.mail import INVITE_SUBJECT, mail_configured, send_invite_email
from open_ux.server import create_mcp
from open_ux.settings import Settings


def _settings(**overrides: object) -> Settings:
    base = Settings.load(hosted=True)
    return Settings(
        hosted=base.hosted,
        catalog_path=base.catalog_path,
        schema_path=base.schema_path,
        database_path=base.database_path,
        pepper=base.pepper,
        admin_token=base.admin_token,
        telemetry=base.telemetry,
        public_url=base.public_url,
        mail_provider=str(overrides.get("mail_provider", "")),
        mail_api_key=str(overrides.get("mail_api_key", "")),
        mail_from=str(overrides.get("mail_from", "")),
    )


def test_mail_configured_requires_all_fields() -> None:
    assert not mail_configured(_settings())
    assert mail_configured(
        _settings(
            mail_provider="resend",
            mail_api_key="re_test",
            mail_from="Open UX <hello@open-ux.dev>",
        )
    )


def test_send_invite_email_skipped_when_unconfigured(tmp_env: Path) -> None:
    issued = approve_invite("ada@example.com", settings=Settings.load(hosted=True))
    assert send_invite_email(issued, settings=_settings()) is False


def test_send_invite_email_resend_success(
    tmp_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    issued = approve_invite("ada@example.com", settings=Settings.load(hosted=True))
    settings = _settings(
        mail_provider="resend",
        mail_api_key="re_test",
        mail_from="Open UX <hello@open-ux.dev>",
    )
    captured: dict[str, object] = {}

    def fake_urlopen(request, timeout=30):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return MagicMock(status=200, __enter__=lambda s: s, __exit__=lambda *a: None)

    monkeypatch.setattr("open_ux.mail.urllib.request.urlopen", fake_urlopen)
    assert send_invite_email(issued, settings=settings) is True
    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["headers"]["Authorization"] == "Bearer re_test"
    body = captured["body"]
    assert body["from"] == "Open UX <hello@open-ux.dev>"
    assert body["to"] == ["ada@example.com"]
    assert body["subject"] == INVITE_SUBJECT
    assert "html" in body
    assert issued.redeem_url in body["html"]
    assert "#FF4B00" in body["html"]
    assert "Redeem invite" in body["html"]
    assert "If the button does not work" not in body["html"]
    assert "display:inline-block;padding:11px 18px" not in body["html"]
    assert "/pip.svg" in body["html"]
    assert "Pip, Open UX mascot" in body["html"]
    assert "icon.png" in body["html"]
    assert "MCP endpoint" not in body["html"]


def test_send_invite_email_resend_failure_is_best_effort(
    tmp_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import urllib.error

    issued = approve_invite("ada@example.com", settings=Settings.load(hosted=True))
    settings = _settings(
        mail_provider="resend",
        mail_api_key="re_test",
        mail_from="Open UX <hello@open-ux.dev>",
    )

    def boom(*args, **kwargs):
        raise urllib.error.HTTPError("https://api.resend.com/emails", 500, "fail", {}, None)

    monkeypatch.setattr("open_ux.mail.urllib.request.urlopen", boom)
    assert send_invite_email(issued, settings=settings) is False


def test_send_invite_email_unknown_provider(
    tmp_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    issued = approve_invite("ada@example.com", settings=Settings.load(hosted=True))
    settings = _settings(
        mail_provider="postmark",
        mail_api_key="pm_test",
        mail_from="Open UX <hello@open-ux.dev>",
    )
    called = {"n": 0}

    def fake_urlopen(*args, **kwargs):
        called["n"] += 1
        return MagicMock(__enter__=lambda s: s, __exit__=lambda *a: None)

    monkeypatch.setattr("open_ux.mail.urllib.request.urlopen", fake_urlopen)
    assert send_invite_email(issued, settings=settings) is False
    assert called["n"] == 0


def test_admin_approve_calls_send_invite_email(
    tmp_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def fake_send(issued, *, settings=None):
        calls.append(issued.email)
        return True

    monkeypatch.setattr("open_ux.server.send_invite_email", fake_send)
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    with TestClient(app) as client:
        client.post("/invite/request", json={"email": "ada@example.com"})
        approved = client.post(
            "/admin/invite/approve",
            headers={"Authorization": "Bearer test-admin-token"},
            json={"email": "ada@example.com"},
        )
    assert approved.status_code == 200
    assert calls == ["ada@example.com"]
