from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from open_ux.catalog import load_catalog
from open_ux.health import health_payload
from open_ux.server import create_mcp
from open_ux.settings import Settings


def _client() -> TestClient:
    mcp = create_mcp(hosted=True)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    return TestClient(app)


def test_health_json_empty_catalog(tmp_env: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    expected = health_payload(catalog, hosted=True)
    assert expected["catalog"]["status"] == "empty"
    assert expected["catalog"]["guideline_count"] == 0
    assert "version" not in expected["catalog"]
    assert expected["version"]
    with _client() as client:
        response = client.get("/health.json")
        html_accept = client.get(
            "/health.json",
            headers={"Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8"},
        )
    assert response.status_code == 200
    assert response.json() == expected
    assert html_accept.json() == expected
