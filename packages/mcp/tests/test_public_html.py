from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from open_ux.catalog import load_catalog
from open_ux.public_html import (
    FAVICON_HREF,
    FAVICON_PATH,
    ICON_PNG_HREF,
    ICON_PNG_PATH,
    PIP_SVG_HREF,
    PIP_SVG_PATH,
    ROBOTS_TXT,
    guideline_display_id,
    guideline_display_name,
    render_sitemap,
)
from open_ux.server import create_mcp
from open_ux.settings import Settings


def _client() -> TestClient:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    return TestClient(app)


def test_robots_txt_is_exact(tmp_env: Path) -> None:
    with _client() as client:
        response = client.get("/robots.txt")
    assert response.status_code == 200
    assert response.text == ROBOTS_TXT
    assert "Disallow: /mcp" in response.text
    assert "Disallow: /health" in response.text
    assert "Disallow: /invite/requested" in response.text
    assert "Sitemap: https://open-ux.dev/sitemap.xml" in response.text


def test_sitemap_lists_landing_catalog_and_remaining_ids(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    ids = [str(row["id"]) for row in catalog.index]
    with _client() as client:
        response = client.get("/sitemap.xml")
    assert response.status_code == 200
    body = response.text
    assert 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"' in body
    assert 'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"' in body
    assert "<loc>https://open-ux.dev/</loc>" in body
    assert "<loc>https://open-ux.dev/catalog</loc>" in body
    assert "<loc>https://open-ux.dev/invite</loc>" in body
    assert "<loc>https://open-ux.dev/privacy</loc>" in body
    assert "<loc>https://open-ux.dev/sources</loc>" in body
    assert "<image:loc>https://open-ux.dev/icon.png</image:loc>" in body
    assert "<lastmod>" in body
    assert "<changefreq>" not in body
    assert "<priority>" not in body
    for gid in ids:
        assert f"<loc>https://open-ux.dev/catalog/{gid}</loc>" in body
    assert "nng." not in body
    assert "apple." not in body
    assert "/404" not in body
    assert "/500" not in body
    assert "https://open-ux.dev/health" not in body
    assert body.count("<url>") == 5 + len(ids)


def test_sitemap_house_block_uses_protocol_fields() -> None:
    xml = render_sitemap(
        ["actions.button_groups"],
        lastmods={
            "/": "2026-09-10",
            "/catalog": "2026-09-09",
            "/catalog/actions.button_groups": "2026-09-08",
        },
    )
    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')
    home = """  <url>
    <loc>https://open-ux.dev/</loc>
    <lastmod>2026-09-10</lastmod>
    <image:image>
      <image:loc>https://open-ux.dev/icon.png</image:loc>
      <image:title>Open UX</image:title>
    </image:image>
  </url>"""
    assert home in xml
    assert """  <url>
    <loc>https://open-ux.dev/catalog/actions.button_groups</loc>
    <lastmod>2026-09-08</lastmod>
  </url>""" in xml


def test_favicon_svg_is_served(tmp_env: Path) -> None:
    assert FAVICON_PATH.is_file()
    assert FAVICON_PATH.name == "logo-mark.svg"
    assert FAVICON_HREF == "/logo-mark.svg"
    mark = FAVICON_PATH.read_bytes()
    assert b'viewBox="0 0 32 32"' in mark
    assert b'fill="#FF4B00"' in mark
    assert b'fill="#FFECE0"' in mark
    with _client() as client:
        preferred = client.get("/logo-mark.svg")
        alias = client.get("/favicon.svg")
    for response in (preferred, alias):
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("image/svg+xml")
        assert response.content == mark
    assert b"#FF4B00" in preferred.content


def test_icon_png_is_served(tmp_env: Path) -> None:
    assert ICON_PNG_PATH.is_file()
    assert ICON_PNG_HREF == "/icon.png"
    png = ICON_PNG_PATH.read_bytes()
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    assert png[16:24] == b"\x00\x00\x02\x00\x00\x00\x02\x00"  # 512x512
    with _client() as client:
        response = client.get("/icon.png")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert response.content == png


def test_pip_svg_is_served(tmp_env: Path) -> None:
    assert PIP_SVG_PATH.is_file()
    assert PIP_SVG_HREF == "/pip.svg"
    svg = PIP_SVG_PATH.read_bytes()
    assert svg.startswith(b"<svg")
    assert b"Pip, Open UX mascot" in svg
    with _client() as client:
        response = client.get("/pip.svg")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
    assert response.content == svg


def test_web_public_mark_symlinks_to_package_static() -> None:
    root = Path(__file__).resolve().parents[3]
    mark = (root / "packages" / "mcp" / "src" / "open_ux" / "static" / "logo-mark.svg").resolve()
    public = root / "packages" / "web" / "public"
    for name in ("logo-mark.svg", "favicon.svg"):
        path = public / name
        assert path.is_symlink(), name
        assert path.resolve() == mark
        assert path.read_bytes() == mark.read_bytes()
    icon = public / "icon.png"
    assert icon.is_symlink()
    assert icon.resolve() == ICON_PNG_PATH.resolve()
    assert icon.read_bytes() == ICON_PNG_PATH.read_bytes()


def test_dockerfile_overlays_web_public_mark() -> None:
    text = (Path(__file__).resolve().parents[3] / "Dockerfile").read_text()
    src = "COPY packages/mcp/src/open_ux/static/logo-mark.svg"
    assert f"{src} ./public/logo-mark.svg" in text
    assert f"{src} ./public/favicon.svg" in text
    assert "COPY packages/mcp/src/open_ux/static/icon.png ./public/icon.png" in text
    assert "COPY catalog /catalog" in text
    assert "OPEN_UX_CATALOG=/catalog" in text


def test_guideline_display_strips_house_and_keeps_category_ids() -> None:
    assert guideline_display_name({"name": "Button groups — Tidwell"}) == "Button groups"
    assert guideline_display_name({"title": "button groups"}) == "button groups"
    assert guideline_display_id("actions.button_groups") == "actions.button_groups"
    assert guideline_display_id("ant.checkbox-vs-switch") == "checkbox-vs-switch"
