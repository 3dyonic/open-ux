from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from open_ux.catalog import get_by_id, load_catalog
from open_ux.health import health_payload
from open_ux.server import create_mcp, web_dist
from open_ux.settings import Settings

ANT_SEED = "ant.checkbox-vs-switch"


def _client() -> TestClient:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    return TestClient(app)


def _write_dist(tmp_path: Path) -> Path:
    dist = tmp_path / "web-dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text(
        "<!DOCTYPE html><html><body>open-ux-shell</body></html>",
        encoding="utf-8",
    )
    (assets / "app.js").write_text("window.__openUx = true;", encoding="utf-8")
    return dist


def test_health_json_is_always_json(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    expected = health_payload(catalog, hosted=True)
    with _client() as client:
        response = client.get("/health.json")
        html_accept = client.get(
            "/health.json",
            headers={"Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"},
        )
    for body in (response, html_accept):
        assert body.status_code == 200
        assert body.headers["content-type"].startswith("application/json")
        assert body.json() == expected
        assert set(body.json()) == {"ok", "name", "hosted", "version", "catalog"}
        assert set(body.json()["catalog"]) == {"status", "guideline_count"}


def test_catalog_api_index_includes_rule_and_jobs(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    with _client() as client:
        response = client.get("/api/catalog")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"guidelines", "total", "catalog", "jobs"}
    assert body["total"] == len(catalog.index)
    assert len(body["guidelines"]) == len(catalog.index)
    assert body["catalog"]["status"] == "ok"
    assert body["catalog"]["guideline_count"] == len(catalog.guidelines)
    assert "version" not in body["catalog"]
    assert "version" not in body["jobs"]
    assert {row["id"] for row in body["jobs"]["containers"]} == {
        "forms_and_input",
        "actions_and_decisions",
        "feedback_and_status",
        "navigation_and_wayfinding",
        "layout_and_data_display",
        "overlays_and_content_structure",
        "multi_step_flows",
    }
    sample = next(row for row in body["guidelines"] if row["id"] == ANT_SEED)
    found = get_by_id(catalog, ANT_SEED)
    assert found is not None
    assert sample["rule"] == str(found["rule"]).strip()
    assert "pass_when" not in sample


def test_catalog_api_get_returns_guideline_or_404(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    found = get_by_id(catalog, ANT_SEED)
    with _client() as client:
        ok = client.get(f"/api/catalog/{ANT_SEED}")
        missing = client.get("/api/catalog/does.not.exist")
    assert ok.status_code == 200
    assert ok.json()["id"] == ANT_SEED
    assert ok.json()["rule"] == found["rule"]
    assert missing.status_code == 404
    assert missing.json() == {"found": False, "id": "does.not.exist"}


def test_no_dist_is_json_only_no_shell(tmp_env: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPEN_UX_WEB_DIST", raising=False)
    monkeypatch.setenv("OPEN_UX_WEB_DIST", str(tmp_env / "missing-dist"))
    assert web_dist() is None
    with _client() as client:
        for path in (
            "/",
            "/catalog",
            f"/catalog/{ANT_SEED}",
            "/health",
            "/privacy",
            "/sources",
            "/invite",
            "/invite/requested",
            "/invite/redeem",
        ):
            response = client.get(path)
            assert response.status_code == 404, path
            assert response.headers["content-type"].startswith("application/json")
            assert "open-ux-shell" not in response.text


def test_dist_serves_shell_on_page_routes_only(
    tmp_env: Path, monkeypatch, live_catalog: Path
) -> None:
    dist = _write_dist(tmp_env)
    monkeypatch.setenv("OPEN_UX_WEB_DIST", str(dist))
    with _client() as client:
        for path in (
            "/",
            "/catalog",
            f"/catalog/{ANT_SEED}",
            "/health",
            "/privacy",
            "/sources",
            "/invite",
            "/invite/requested",
            "/invite/redeem",
        ):
            response = client.get(path)
            assert response.status_code == 200, path
            assert response.headers["content-type"].startswith("text/html")
            assert "open-ux-shell" in response.text
        asset = client.get("/assets/app.js")
        assert asset.status_code == 200
        assert "window.__openUx" in asset.text
        health = client.get("/health.json")
        assert health.headers["content-type"].startswith("application/json")
        catalog = client.get("/api/catalog")
        assert catalog.headers["content-type"].startswith("application/json")
        assert "open-ux-shell" not in catalog.text
        admin = client.get("/admin/invite/waitlist")
        assert admin.status_code == 401
        assert "open-ux-shell" not in admin.text
        invite_post = client.post("/invite/request", json={"email": "ada@example.com"})
        assert invite_post.status_code == 200
        assert invite_post.json()["ok"] is True


def test_mcp_and_account_are_not_swallowed(tmp_env: Path, monkeypatch) -> None:
    dist = _write_dist(tmp_env)
    monkeypatch.setenv("OPEN_UX_WEB_DIST", str(dist))
    with _client() as client:
        mcp = client.get("/mcp")
        assert "open-ux-shell" not in mcp.text
        deleted = client.post(
            "/account/delete", json={"email": "ada@example.com", "key": "uxmcp_nope"}
        )
        assert deleted.status_code in {400, 401}
        assert "open-ux-shell" not in deleted.text


def test_sources_is_a_vite_tailwind_page() -> None:
    root = Path(__file__).resolve().parents[3]
    main = (root / "packages" / "web" / "src" / "main.js").read_text(encoding="utf-8")
    sources = (root / "packages" / "web" / "src" / "sources.js").read_text(
        encoding="utf-8"
    )
    chrome = (root / "packages" / "web" / "src" / "chrome.js").read_text(
        encoding="utf-8"
    )
    assert 'from "./sources.js"' in main
    assert 'path === "/sources"' in main
    assert "return renderSources(root)" in main
    assert 'class="page page-sources"' in sources
    assert "flex flex-col gap-3" in sources
    assert "text-[15px] leading-[22px] text-ink" in sources
    assert "contact@open-ux.dev" in sources
    assert "Nielsen" not in sources
    assert "NN/g" not in sources
    assert 'href="/sources"' in chrome


def test_catalog_rule_page_embeds_rule_for_fetchers(
    tmp_env: Path, monkeypatch, live_catalog: Path
) -> None:
    root = Path(__file__).resolve().parents[3]
    dist = tmp_env / "web-dist"
    dist.mkdir()
    (dist / "index.html").write_text(
        (root / "packages" / "web" / "index.html").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPEN_UX_WEB_DIST", str(dist))
    catalog = load_catalog(Settings.load(hosted=True))
    found = get_by_id(catalog, "actions.button_groups")
    assert found is not None
    with _client() as client:
        response = client.get("/catalog/actions.button_groups")
        home = client.get("/")
        missing = client.get("/catalog/does.not.exist")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "<title>Button groups — Open UX</title>" in body
    assert found["rule"] in body
    assert "Stop inventing UX rules from memory" not in body
    assert home.status_code == 200
    assert "<title>Open UX</title>" in home.text
    assert found["rule"] not in home.text
    assert missing.status_code == 200
    assert found["rule"] not in missing.text
    assert "<title>Open UX</title>" in missing.text
    catalog_js = (root / "packages" / "web" / "src" / "catalog.js").read_text(
        encoding="utf-8"
    )
    assert "data-ssr-rule" in catalog_js
    assert "hasSsr" in catalog_js


def test_register_still_redirects_to_invite(tmp_env: Path) -> None:
    with _client() as client:
        response = client.get("/register", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "/invite"
