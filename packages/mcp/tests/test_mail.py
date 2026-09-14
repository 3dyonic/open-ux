from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from open_ux.__main__ import main
from open_ux.auth import approve_invite
from open_ux.mail import (
    INVITE_SUBJECT,
    RESEND_SMTP_HOST,
    RESEND_SMTP_PORT,
    RESEND_SMTP_STARTTLS_PORT,
    RESEND_SMTP_USER,
    mail_configured,
    mail_not_sent_hint,
    send_invite_email,
)
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


def _resend_settings() -> Settings:
    return _settings(
        mail_provider="resend",
        mail_api_key="re_test",
        mail_from="Open UX <hello@open-ux.dev>",
    )


def _part_content(msg: EmailMessage, content_type: str) -> str:
    for part in msg.walk():
        if part.get_content_type() == content_type:
            return part.get_content()
    return ""


class RecordingSMTP:
    def __init__(self, host="", port=0, local_hostname=None, timeout=None, **kwargs):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.context = kwargs.get("context")
        self.user = None
        self.password = None
        self.sent: list[EmailMessage] = []
        self.ehlo_count = 0
        self.starttls_called = False

    def __enter__(self):
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def ehlo(self, name: str = "") -> None:
        self.ehlo_count += 1

    def starttls(self, *, context=None) -> None:
        self.starttls_called = True
        self.context = context

    def login(self, user: str, password: str) -> None:
        self.user = user
        self.password = password

    def send_message(self, msg: EmailMessage) -> dict[str, tuple[int, bytes]]:
        self.sent.append(msg)
        return {}


def test_mail_configured_requires_all_fields() -> None:
    assert not mail_configured(_settings())
    assert mail_configured(_resend_settings())


def test_mail_not_sent_hint_splits_unconfigured_from_delivery() -> None:
    unconfigured = mail_not_sent_hint(configured=False)
    failed = mail_not_sent_hint(configured=True)
    assert "isn't configured" in unconfigured
    assert "delivery failed" not in unconfigured
    assert "delivery failed" in failed
    assert "isn't configured" not in failed
    assert "redeem_url" in unconfigured
    assert "redeem_url" in failed


def test_send_invite_email_skipped_when_unconfigured(tmp_env: Path) -> None:
    issued = approve_invite("ada@example.com", settings=Settings.load(hosted=True))
    assert send_invite_email(issued, settings=_settings()) is False


def test_send_invite_email_resend_success(
    tmp_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    issued = approve_invite("ada@example.com", settings=Settings.load(hosted=True))
    settings = _resend_settings()
    sessions: list[RecordingSMTP] = []

    def fake_ssl(*args, **kwargs):
        smtp = RecordingSMTP(*args, **kwargs)
        sessions.append(smtp)
        return smtp

    def fake_starttls(*args, **kwargs):
        raise AssertionError("STARTTLS must not run when SMTPS succeeds")

    monkeypatch.setattr("open_ux.mail.smtplib.SMTP_SSL", fake_ssl)
    monkeypatch.setattr("open_ux.mail.smtplib.SMTP", fake_starttls)
    assert send_invite_email(issued, settings=settings) is True
    assert len(sessions) == 1
    smtp = sessions[0]
    assert smtp.host == RESEND_SMTP_HOST
    assert smtp.port == RESEND_SMTP_PORT
    assert smtp.timeout == 30
    assert smtp.user == RESEND_SMTP_USER
    assert smtp.password == "re_test"
    assert len(smtp.sent) == 1
    msg = smtp.sent[0]
    assert msg["From"] == "Open UX <hello@open-ux.dev>"
    assert msg["To"] == "ada@example.com"
    assert msg["Subject"] == INVITE_SUBJECT
    html = _part_content(msg, "text/html")
    text = _part_content(msg, "text/plain")
    assert issued.redeem_url in html
    assert issued.redeem_url in text
    assert "#FF4B00" in html
    assert "Redeem invite" in html
    assert "If the button does not work" not in html
    assert "display:inline-block;padding:11px 18px" not in html
    assert "/pip.svg" in html
    assert "Pip, Open UX mascot" in html
    assert "icon.png" in html
    assert "MCP endpoint" not in html


def test_send_invite_email_resend_failure_is_best_effort(
    tmp_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    issued = approve_invite("ada@example.com", settings=Settings.load(hosted=True))
    settings = _resend_settings()

    def boom(*args, **kwargs):
        raise smtplib.SMTPResponseException(550, b"rejected")

    monkeypatch.setattr("open_ux.mail.smtplib.SMTP_SSL", boom)
    assert send_invite_email(issued, settings=settings) is False


def test_send_invite_email_resend_falls_back_to_starttls(
    tmp_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    issued = approve_invite("ada@example.com", settings=Settings.load(hosted=True))
    settings = _resend_settings()
    sessions: list[RecordingSMTP] = []

    def boom_ssl(*args, **kwargs):
        raise OSError("connection refused")

    def fake_smtp(*args, **kwargs):
        smtp = RecordingSMTP(*args, **kwargs)
        sessions.append(smtp)
        return smtp

    monkeypatch.setattr("open_ux.mail.smtplib.SMTP_SSL", boom_ssl)
    monkeypatch.setattr("open_ux.mail.smtplib.SMTP", fake_smtp)
    assert send_invite_email(issued, settings=settings) is True
    assert len(sessions) == 1
    smtp = sessions[0]
    assert smtp.host == RESEND_SMTP_HOST
    assert smtp.port == RESEND_SMTP_STARTTLS_PORT
    assert smtp.starttls_called is True
    assert smtp.ehlo_count >= 2
    assert smtp.user == RESEND_SMTP_USER
    assert smtp.password == "re_test"
    html = _part_content(smtp.sent[0], "text/html")
    assert issued.redeem_url in html


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

    def fake_ssl(*args, **kwargs):
        called["n"] += 1
        return RecordingSMTP(*args, **kwargs)

    monkeypatch.setattr("open_ux.mail.smtplib.SMTP_SSL", fake_ssl)
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
    body = approved.json()
    assert body["mail_sent"] is True
    assert body["mail_configured"] is False


def test_admin_approve_reports_delivery_failure(
    tmp_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPEN_UX_MAIL_PROVIDER", "resend")
    monkeypatch.setenv("OPEN_UX_MAIL_API_KEY", "re_test")
    monkeypatch.setenv("OPEN_UX_MAIL_FROM", "Open UX <hello@open-ux.dev>")

    def boom(*args, **kwargs):
        raise smtplib.SMTPResponseException(550, b"rejected")

    monkeypatch.setattr("open_ux.mail.smtplib.SMTP_SSL", boom)
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
    body = approved.json()
    assert body["mail_sent"] is False
    assert body["mail_configured"] is True
    assert body["redeem_url"]


def test_approve_invite_cli_reports_delivery_failure(
    tmp_env: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("OPEN_UX_MAIL_PROVIDER", "resend")
    monkeypatch.setenv("OPEN_UX_MAIL_API_KEY", "re_test")
    monkeypatch.setenv("OPEN_UX_MAIL_FROM", "Open UX <hello@open-ux.dev>")

    def boom(*args, **kwargs):
        raise smtplib.SMTPResponseException(550, b"rejected")

    monkeypatch.setattr("open_ux.mail.smtplib.SMTP_SSL", boom)
    assert main(["approve-invite", "ada@example.com"]) == 0
    captured = capsys.readouterr()
    out = json.loads(captured.out)
    assert out["mail_sent"] is False
    assert out["mail_configured"] is True
    assert "delivery failed" in captured.err
    assert "isn't configured" not in captured.err


def test_admin_copy_distinguishes_unconfigured_from_delivery_failure() -> None:
    admin = (
        Path(__file__).resolve().parents[3]
        / "packages"
        / "web"
        / "src"
        / "admin.js"
    ).read_text(encoding="utf-8")
    assert "mail isn’t configured" in admin
    assert "delivery failed" in admin
    assert "mail_configured === false" in admin
    assert "or delivery failed" not in admin
