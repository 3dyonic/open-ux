from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from open_ux.server import create_mcp
from open_ux.settings import DEFAULT_GTM_ID, gtm_container_id

GTM_HOST = "googletagmanager.com"
CONSENT_COOKIE = "open_ux_gtm_consent"
NEVER_GET = (
    "/mcp",
    "/admin/invite/waitlist",
    "/account/delete",
    "/health.json",
    "/api/site",
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


def test_site_config_returns_gtm_id(tmp_env: Path) -> None:
    with _client() as client:
        response = client.get("/api/site")
    assert response.status_code == 200
    assert response.json() == {"gtm_id": DEFAULT_GTM_ID}


def test_site_config_uses_env(tmp_env: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPEN_UX_GTM_ID", "GTM-TESTID1")
    with _client() as client:
        response = client.get("/api/site")
    assert response.json() == {"gtm_id": "GTM-TESTID1"}


def test_never_pages_have_no_gtm_even_with_consent(tmp_env: Path) -> None:
    with _client() as client:
        client.cookies.set(CONSENT_COOKIE, "granted")
        for path in NEVER_GET:
            response = client.get(path)
            assert GTM_HOST not in response.text, path
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
