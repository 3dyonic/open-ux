from __future__ import annotations

from html import escape
from pathlib import Path

from starlette.testclient import TestClient

from open_ux.catalog import load_catalog
from open_ux.public_html import (
    CATALOG_TITLE,
    FAVICON_PATH,
    LANDING_DESCRIPTION,
    LANDING_TITLE,
    ROBOTS_TXT,
    canonical_url,
    rule_meta_description,
    rule_meta_title,
)
from open_ux.server import create_mcp
from open_ux.settings import Settings

ANT_SEED = "ant.checkbox-vs-switch"


def _client() -> TestClient:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    return TestClient(app)


def _head(html: str) -> str:
    return html.split("</head>", 1)[0]


def test_robots_txt_is_exact(tmp_env: Path) -> None:
    with _client() as client:
        response = client.get("/robots.txt")
    assert response.status_code == 200
    assert response.text == ROBOTS_TXT
    assert "Disallow: /mcp" in response.text
    assert "Sitemap: https://open-ux.dev/sitemap.xml" in response.text


def test_sitemap_lists_landing_catalog_and_remaining_ids(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    ids = [str(row["id"]) for row in catalog.index]
    with _client() as client:
        response = client.get("/sitemap.xml")
    assert response.status_code == 200
    body = response.text
    assert 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"' in body
    assert "<loc>https://open-ux.dev/</loc>" in body
    assert "<loc>https://open-ux.dev/catalog</loc>" in body
    for gid in ids:
        assert f"<loc>https://open-ux.dev/catalog/{gid}</loc>" in body
    assert "nng." not in body
    assert "apple." not in body
    assert body.count("<url>") == 2 + len(ids)


def test_favicon_svg_is_served(tmp_env: Path) -> None:
    assert FAVICON_PATH.is_file()
    with _client() as client:
        response = client.get("/favicon.svg")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.content == FAVICON_PATH.read_bytes()
    assert b"#FF4B00" in response.content


def test_public_pages_have_pack_head_and_no_mcp_or_og_image(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    guideline = next(g for g in catalog.guidelines if g["id"] == ANT_SEED)
    display = "Checkbox vs switch"
    rule_title = rule_meta_title(display)
    rule_desc = rule_meta_description(guideline)
    with _client() as client:
        landing = client.get("/").text
        listed = client.get("/catalog").text
        rule = client.get(f"/catalog/{ANT_SEED}").text
    for html, title, description, path in (
        (landing, LANDING_TITLE, LANDING_DESCRIPTION, "/"),
        (listed, CATALOG_TITLE, LANDING_DESCRIPTION, "/catalog"),
        (rule, rule_title, rule_desc, f"/catalog/{ANT_SEED}"),
    ):
        head = _head(html)
        title_e = escape(title, quote=True)
        desc_e = escape(description, quote=True)
        url_e = escape(canonical_url(path), quote=True)
        assert f"<title>{title_e}</title>" in head
        assert f'<meta name="description" content="{desc_e}">' in head
        assert f'<link rel="canonical" href="{url_e}">' in head
        assert f'<meta property="og:title" content="{title_e}">' in head
        assert f'<meta property="og:description" content="{desc_e}">' in head
        assert f'<meta property="og:url" content="{url_e}">' in head
        assert '<meta property="og:type" content="website">' in head
        assert '<meta name="twitter:card" content="summary">' in head
        assert f'<meta name="twitter:title" content="{title_e}">' in head
        assert f'<meta name="twitter:description" content="{desc_e}">' in head
        assert '<link rel="icon" href="/favicon.svg" type="image/svg+xml">' in head
        assert "og:image" not in head.lower()
        assert "twitter:image" not in head.lower()
        assert "MCP" not in head
    assert 'class="nav-brand" href="/catalog"' in listed
    assert 'class="nav-brand" href="/catalog"' in rule
    assert ">Get a key</a>" in listed
    assert 'href="/invite"' in listed
    assert ">Browse catalog</a>" in landing
    assert 'class="btn btn--primary" href="/catalog">Browse catalog</a>' in landing
    assert 'class="btn btn--primary btn--nav" href="/invite">Get a key</a>' in landing
