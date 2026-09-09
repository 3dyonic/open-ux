from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from open_ux.catalog import load_catalog
from open_ux.public_html import (
    FAVICON_HREF,
    FAVICON_PATH,
    ROBOTS_TXT,
    guideline_display_id,
    guideline_display_name,
    rule_meta_description,
    rule_meta_title,
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
    assert "<loc>https://open-ux.dev/privacy</loc>" in body
    assert "<loc>https://open-ux.dev/sources</loc>" in body
    for gid in ids:
        assert f"<loc>https://open-ux.dev/catalog/{gid}</loc>" in body
    assert "nng." not in body
    assert "apple." not in body
    assert "/404" not in body
    assert "/500" not in body
    assert body.count("<url>") == 4 + len(ids)


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


def test_web_public_mark_symlinks_to_package_static() -> None:
    root = Path(__file__).resolve().parents[3]
    mark = (root / "packages" / "mcp" / "src" / "open_ux" / "static" / "logo-mark.svg").resolve()
    public = root / "packages" / "web" / "public"
    for name in ("logo-mark.svg", "favicon.svg"):
        path = public / name
        assert path.is_symlink(), name
        assert path.resolve() == mark
        assert path.read_bytes() == mark.read_bytes()


def test_dockerfile_overlays_web_public_mark() -> None:
    text = (Path(__file__).resolve().parents[3] / "Dockerfile").read_text()
    src = "COPY packages/mcp/src/open_ux/static/logo-mark.svg"
    assert f"{src} ./public/logo-mark.svg" in text
    assert f"{src} ./public/favicon.svg" in text
    assert "COPY catalog /catalog" in text
    assert "OPEN_UX_CATALOG=/catalog" in text


def test_guideline_display_strips_house_and_keeps_category_ids() -> None:
    assert guideline_display_name({"name": "Button groups — Tidwell"}) == "Button groups"
    assert guideline_display_name({"title": "button groups"}) == "button groups"
    assert guideline_display_id("actions.button_groups") == "actions.button_groups"
    assert guideline_display_id("ant.checkbox-vs-switch") == "checkbox-vs-switch"


def test_rule_meta_uses_rule_body_not_site_tagline() -> None:
    title = rule_meta_title("Button groups")
    desc = rule_meta_description(
        {"rule": "Present related actions as a small cluster of buttons."}
    )
    assert title == "Button groups — Open UX"
    assert desc.startswith("Present related actions")
    assert "Stop inventing UX rules" not in desc
