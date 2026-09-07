from __future__ import annotations

from html import escape

from starlette.testclient import TestClient

from open_ux.catalog import load_catalog
from open_ux.health_page import HEALTH_DESCRIPTION, HEALTH_TITLE, health_payload
from open_ux.public_html import FAVICON_HREF, canonical_url
from open_ux.server import create_mcp
from open_ux.settings import Settings


def _client() -> TestClient:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    return TestClient(app)


def _payload() -> dict:
    catalog = load_catalog(Settings.load(hosted=True))
    return health_payload(catalog, hosted=True)


def test_health_default_and_star_accept_are_json(live_catalog) -> None:
    expected = _payload()
    with _client() as client:
        default = client.get("/health")
        star = client.get("/health", headers={"Accept": "*/*"})
        missing = client.get("/health", headers={"Accept": ""})
        typed = client.get("/health", headers={"Accept": "application/json"})
    for response in (default, star, missing, typed):
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        assert response.json() == expected
        assert set(response.json()) == {"ok", "name", "hosted", "catalog"}
        assert set(response.json()["catalog"]) == {
            "status",
            "guideline_count",
            "version",
        }


def test_health_format_json_wins_over_html_accept(live_catalog) -> None:
    with _client() as client:
        response = client.get(
            "/health?format=json",
            headers={"Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"},
        )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json() == _payload()


def test_health_html_when_browser_accepts_html(live_catalog) -> None:
    payload = _payload()
    count = payload["catalog"]["guideline_count"]
    version = payload["catalog"]["version"]
    with _client() as client:
        response = client.get(
            "/health",
            headers={"Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"},
        )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    head = html.split("</head>", 1)[0]
    title_e = escape(HEALTH_TITLE, quote=True)
    desc_e = escape(HEALTH_DESCRIPTION, quote=True)
    url_e = escape(canonical_url("/health"), quote=True)
    assert f"<title>{title_e}</title>" in head
    assert f'<meta name="description" content="{desc_e}">' in head
    assert f'<link rel="canonical" href="{url_e}">' in head
    assert f'<link rel="icon" href="{FAVICON_HREF}" type="image/svg+xml">' in head
    assert "googletagmanager.com" not in html
    assert 'class="nav-brand" href="/"' in html
    assert f'<img class="mark" src="{FAVICON_HREF}"' in html
    assert 'class="nav-link" href="/catalog">Catalog</a>' in html
    assert 'class="nav-github"' in html
    assert ">Health</h1>" in html
    assert "Success: host and catalog are up" in html
    assert "The hosted service is running. The catalog is loaded." in html
    assert html.count(">Operational</span>") == 4
    assert f"{count} cited rules, version {version}" in html
    assert "What agents receive" not in html
    assert '"ok": true' not in html
    assert "pulse" not in html
    assert "Open UX · cited UX rules agents audit against" in html
    assert '<a href="/privacy">Privacy</a>' in html
    assert ">Get a key</a>" not in html


def test_health_html_has_no_gtm_even_with_consent(live_catalog) -> None:
    from open_ux.public_html import CONSENT_COOKIE, CONSENT_GRANTED

    with _client() as client:
        client.cookies.set(CONSENT_COOKIE, CONSENT_GRANTED)
        html = client.get("/health", headers={"Accept": "text/html"}).text
    assert "googletagmanager.com" not in html
    assert "We use cookies for analytics" not in html


def test_health_html_empty_catalog_marks_not_loaded(tmp_env) -> None:
    with _client() as client:
        html = client.get("/health", headers={"Accept": "text/html"}).text
        body = client.get("/health").json()
    assert body["catalog"]["status"] == "empty"
    assert body["catalog"]["guideline_count"] == 0
    assert "Error: catalog is not loaded" in html
    assert "Not loaded" in html
    assert "No cited rules loaded yet." in html
    assert "What agents receive" not in html
