from __future__ import annotations

from html import escape
from pathlib import Path

from starlette.testclient import TestClient

from open_ux.public_html import (
    CONSENT_BANNER_COPY,
    CONSENT_COOKIE,
    CONSENT_GRANTED,
    DEFAULT_GTM_ID,
    PRIVACY_DESCRIPTION,
    PRIVACY_H1,
    PRIVACY_LEDE,
    PRIVACY_SECTIONS,
    PRIVACY_TITLE,
    canonical_url,
    gtm_container_id,
)
from open_ux.server import create_mcp

ANT_SEED = "ant.checkbox-vs-switch"
PUBLIC_PATHS = ("/", "/catalog", f"/catalog/{ANT_SEED}", "/invite", "/privacy")
NEVER_GET = (
    "/mcp",
    "/admin/invite/waitlist",
    "/invite/redeem",
    "/account/delete",
    "/health",
    "/invite/requested",
)
GTM_HOST = "googletagmanager.com"


def _client() -> TestClient:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    return TestClient(app)


def test_public_pages_have_no_gtm_without_consent(live_catalog: Path) -> None:
    with _client() as client:
        for path in PUBLIC_PATHS:
            response = client.get(path)
            assert response.status_code == 200, path
            html = response.text
            assert GTM_HOST not in html, path
            assert CONSENT_BANNER_COPY in html, path
            assert ">Accept</button>" in html, path
            assert ">Decline</button>" in html, path
            assert 'href="/privacy"' in html, path
            assert "location.reload()" in html, path


def test_public_pages_have_gtm_when_consent_granted(live_catalog: Path) -> None:
    with _client() as client:
        client.cookies.set(CONSENT_COOKIE, CONSENT_GRANTED)
        for path in PUBLIC_PATHS:
            response = client.get(path)
            assert response.status_code == 200, path
            html = response.text
            assert GTM_HOST in html, path
            assert "gtm.js?id=" in html, path
            assert DEFAULT_GTM_ID in html, path
            assert CONSENT_BANNER_COPY in html, path


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


def test_privacy_page_is_po_html_not_eng_sot(tmp_env: Path) -> None:
    eng = (Path(__file__).resolve().parents[3] / "docs" / "PRIVACY.md").read_text(
        encoding="utf-8"
    )
    assert "Eng Done fails" in eng
    assert "OPEN_UX_DATA_DIR" in eng

    with _client() as client:
        response = client.get("/privacy")
    assert response.status_code == 200
    html = response.text
    head = html.split("</head>", 1)[0]
    title_e = escape(PRIVACY_TITLE, quote=True)
    desc_e = escape(PRIVACY_DESCRIPTION, quote=True)
    url_e = escape(canonical_url("/privacy"), quote=True)
    assert f"<title>{title_e}</title>" in head
    assert f'<meta name="description" content="{desc_e}">' in head
    assert f'<link rel="canonical" href="{url_e}">' in head
    assert f'<meta property="og:title" content="{title_e}">' in head
    assert f'<meta property="og:description" content="{desc_e}">' in head
    assert f'<meta property="og:url" content="{url_e}">' in head
    assert f'<meta name="twitter:title" content="{title_e}">' in head
    assert f'<meta name="twitter:description" content="{desc_e}">' in head
    assert f"<h1>{escape(PRIVACY_H1)}</h1>" in html
    assert escape(PRIVACY_LEDE) in html
    for heading, paragraph, bullets in PRIVACY_SECTIONS:
        assert f"<h2>{escape(heading)}</h2>" in html
        if paragraph:
            assert escape(paragraph) in html
        for item in bullets:
            assert escape(item) in html
    assert 'href="/privacy"' in html
    assert CONSENT_BANNER_COPY in html
    assert GTM_HOST not in html
    assert "Eng Done fails" not in html
    assert "OPEN_UX_DATA_DIR" not in html
    assert "Never persist" not in html


def test_gtm_id_from_env(live_catalog: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPEN_UX_GTM_ID", "GTM-TESTID1")
    assert gtm_container_id() == "GTM-TESTID1"
    with _client() as client:
        client.cookies.set(CONSENT_COOKIE, CONSENT_GRANTED)
        html = client.get("/").text
    assert "GTM-TESTID1" in html
    assert DEFAULT_GTM_ID not in html


def test_invalid_gtm_env_falls_back_to_default(live_catalog: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPEN_UX_GTM_ID", "not-a-container")
    assert gtm_container_id() == DEFAULT_GTM_ID
    with _client() as client:
        client.cookies.set(CONSENT_COOKIE, CONSENT_GRANTED)
        html = client.get("/").text
    assert "not-a-container" not in html
    assert DEFAULT_GTM_ID in html


def test_denied_consent_keeps_gtm_off(live_catalog: Path) -> None:
    with _client() as client:
        client.cookies.set(CONSENT_COOKIE, "denied")
        html = client.get("/").text
    assert GTM_HOST not in html
    assert CONSENT_BANNER_COPY in html
