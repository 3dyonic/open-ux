from __future__ import annotations

from pathlib import Path

from starlette.middleware import Middleware
from starlette.testclient import TestClient

from open_ux.catalog import load_catalog
from open_ux.health import HealthErrorMiddleware, HealthState, health_payload
from open_ux.server import create_mcp, server_error_response
from open_ux.settings import Settings


def _client(*, middleware: list[Middleware] | None = None) -> TestClient:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(
        path="/mcp",
        stateless_http=True,
        transport="http",
        middleware=middleware or [],
    )
    return TestClient(app), mcp


def test_health_json_empty_catalog(tmp_env: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    expected = health_payload(catalog, hosted=True)
    assert expected["ok"] is False
    assert expected["error"] is None
    assert expected["title"] == "Error: catalog is not loaded"
    assert expected["catalog"]["status"] == "empty"
    assert expected["catalog"]["guideline_count"] == 0
    assert "version" not in expected["catalog"]
    assert expected["version"]
    client, _mcp = _client()
    with client:
        response = client.get("/health.json")
        html_accept = client.get(
            "/health.json",
            headers={"Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"},
        )
    assert response.status_code == 200
    assert response.json() == expected
    assert html_accept.json() == expected


def test_health_payload_records_server_error(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    state = HealthState()
    state.note_server_error(status=500, path="/catalog/actions.button_groups?x=1")
    state.note_server_error(status=404, path="/missing")
    payload = health_payload(catalog, hosted=True, state=state)
    assert payload["ok"] is False
    assert payload["catalog"]["status"] == "ok"
    assert payload["title"] == "Error: a request failed"
    assert payload["body"] == "A page could not be loaded. Try that page again."
    assert payload["error"]["status"] == 500
    assert payload["error"]["path"] == "/catalog/actions.button_groups"
    assert payload["error"]["at"]


def test_health_skips_own_routes() -> None:
    state = HealthState()
    state.note_server_error(status=500, path="/health")
    state.note_server_error(status=500, path="/health.json")
    assert state.snapshot() is None


def test_health_json_records_unhandled_500(live_catalog: Path, monkeypatch) -> None:
    def boom() -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr("open_ux.server.render_landing_article", boom)
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(
        path="/mcp",
        stateless_http=True,
        transport="http",
        middleware=[
            Middleware(
                HealthErrorMiddleware,
                state=mcp.health_state,
                render_500=server_error_response,
            )
        ],
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        failed = client.get("/")
        health = client.get("/health.json")
        page = client.get("/health")
    assert failed.status_code == 500
    if failed.headers["content-type"].startswith("application/json"):
        assert failed.json()["error"] == "This page could not be loaded."
    else:
        assert "This page could not be loaded" in failed.text
    body = health.json()
    assert health.status_code == 200
    assert body["ok"] is False
    assert body["error"]["status"] == 500
    assert body["error"]["path"] == "/"
    assert "Error: a request failed" in page.text
    assert "A request returned 500. /" in page.text


def test_server_error_page_embeds_copy_for_fetchers(
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

    def boom() -> str:
        raise RuntimeError("boom")

    monkeypatch.setattr("open_ux.server.render_landing_article", boom)
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(
        path="/mcp",
        stateless_http=True,
        transport="http",
        middleware=[
            Middleware(
                HealthErrorMiddleware,
                state=mcp.health_state,
                render_500=server_error_response,
            )
        ],
    )
    with TestClient(app, raise_server_exceptions=False) as client:
        failed = client.get("/")
    assert failed.status_code == 500
    assert failed.headers["content-type"].startswith("text/html")
    assert "<title>This page could not be loaded — Open UX</title>" in failed.text
    assert "Try again in a moment." in failed.text
    assert 'data-ssr-page="server-error"' in failed.text
    assert 'href="/">Try again</a>' in failed.text
