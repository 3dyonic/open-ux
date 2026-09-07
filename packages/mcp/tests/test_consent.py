from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from open_ux.public_html import CONSENT_BANNER_COPY, CONSENT_COOKIE, CONSENT_GRANTED, DEFAULT_GTM_ID, gtm_container_id
from open_ux.server import create_mcp

GTM_HOST = "googletagmanager.com"
NEVER_GET = (
    "/mcp",
    "/admin/invite/waitlist",
    "/account/delete",
    "/health.json",
)


def _client() -> TestClient:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    return TestClient(app)


def test_gtm_id_from_env(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_UX_GTM_ID", "GTM-TESTID1")
    assert gtm_container_id() == "GTM-TESTID1"


def test_invalid_gtm_env_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv("OPEN_UX_GTM_ID", "not-a-container")
    assert gtm_container_id() == DEFAULT_GTM_ID


def test_never_pages_have_no_gtm_even_with_consent(tmp_env: Path) -> None:
    with _client() as client:
        client.cookies.set(CONSENT_COOKIE, CONSENT_GRANTED)
        for path in NEVER_GET:
            response = client.get(path)
            assert GTM_HOST not in response.text, path
            assert CONSENT_BANNER_COPY not in response.text, path
        admin = client.get(
            "/admin/invite/waitlist",
            headers={"Authorization": "Bearer test-admin-token"},
        )
        assert GTM_HOST not in admin.text
        account = client.post(
            "/account/delete",
            json={"email": "ada@example.com", "key": "uxmcp_nope"},
        )
        assert GTM_HOST not in account.text
