from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from open_ux.catalog import Catalog, citations, load_catalog
from open_ux.catalog_page import (
    CONTAINER_CHIPS,
    _strip_source_suffix,
    render_catalog_list,
    render_catalog_not_found,
    render_catalog_rule,
)
from open_ux.jobs import load_job_tree
from open_ux.server import create_mcp
from open_ux.settings import Settings

LIVE_SEED = (
    "forms.field_labels.visible_label",
    "forms.field_labels.label_stays_visible",
    "forms.field_labels.error_identifies_and_fixes",
)
NNG_SEED = LIVE_SEED[0]
MULTI_CITE_ID = "forms.fields.distinguish_optional_required"
KNOWN_BODY = "Place a clear label outside the field so users always know what information belongs there."
FIELD_ORDER = (
    "name",
    "id",
    "rule",
    "overview",
    "apply_when",
    "not_when",
    "agent_hint",
    "description",
    "pass_when",
    "fail_when",
    "citation",
)


def _client(hosted: bool = True) -> TestClient:
    mcp = create_mcp(hosted=hosted)
    app = mcp.http_app(path="/mcp", stateless_http=True, transport="http")
    return TestClient(app)


def _public_page_guards(html: str) -> None:
    assert "fetch(" not in html
    assert "/mcp" not in html
    assert "Authorization" not in html
    assert "uxmcp_" not in html
    assert "test-pepper" not in html
    assert "test-admin-token" not in html
    assert "Bearer " not in html
    assert "OPEN_UX_PEPPER" not in html


def test_strip_source_suffix_drops_known_houses() -> None:
    assert _strip_source_suffix("Visible field label — NN/g") == "Visible field label"
    assert _strip_source_suffix("One toast at a time — Spectrum") == "One toast at a time"
    assert _strip_source_suffix("No suffix") == "No suffix"
    assert _strip_source_suffix("<script>alert(1)</script>") == "<script>alert(1)</script>"


def test_seven_container_chips() -> None:
    assert len(CONTAINER_CHIPS) == 7
    assert [cid for cid, _label in CONTAINER_CHIPS] == [
        "forms_and_input",
        "actions_and_decisions",
        "feedback_and_status",
        "navigation_and_wayfinding",
        "layout_and_data_display",
        "overlays_and_content_structure",
        "multi_step_flows",
    ]
    assert [label for _cid, label in CONTAINER_CHIPS] == [
        "Forms",
        "Actions",
        "Feedback",
        "Wayfinding",
        "Layout",
        "Overlays",
        "Multi-step",
    ]


def test_catalog_list_empty_is_200(tmp_env: Path) -> None:
    with _client() as client:
        response = client.get("/catalog")
        assert response.status_code == 200
        html = response.text
        assert "<h1>Catalog</h1>" in html
        assert "0 shown" in html
        assert "Forms" in html
        assert "Multi-step" in html
        _public_page_guards(html)
        denied = client.post("/mcp", json={})
        assert denied.status_code == 401


def test_catalog_list_is_full_live_index(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    with _client() as client:
        response = client.get("/catalog")
        assert response.status_code == 200
        html = response.text
        assert html.count('class="catalog-row"') == len(catalog.index)
        assert f"{len(catalog.index)} shown" in html
        for gid in LIVE_SEED:
            assert gid in html
        assert "govuk.date-input-only-memorable" in html
        assert KNOWN_BODY not in html
        assert "Each input has a clear label outside the field" not in html
        assert "pass_when" not in html
        assert "fail_when" not in html
        assert "agent_hint" not in html
        assert "--paper: #F9F6F2" in html
        assert "--ink: #1F1B16" in html
        assert "--pip: #FF4B00" in html
        assert "IBM Plex Sans" in html
        assert "IBM Plex Mono" in html
        assert 'href="/catalog"' in html
        assert 'href="/invite"' in html
        _public_page_guards(html)


def test_catalog_rule_known_id_ordered_fields(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    tree = load_job_tree(Settings.load())
    guideline = catalog.guidelines[0]
    gid = guideline["id"]
    assert gid == LIVE_SEED[0]
    with _client() as client:
        response = client.get(f"/catalog/{gid}")
        assert response.status_code == 200
        html = response.text
        claim = _strip_source_suffix(guideline["name"])
        assert f'<h1 class="rule-name" data-field="name">{claim}</h1>' in html
        assert guideline["name"] != claim
        assert gid in html
        assert guideline["rule"] in html
        positions = [html.index(f'data-field="{field}"') for field in FIELD_ORDER]
        assert positions == sorted(positions)
        assert 'data-field="severity"' in html
        assert ">Major</span>" in html
        assert "Forms &amp; input" in html or "Forms & input" in html
        assert "Design a form" in html
        assert "← Back to Catalog" in html
        assert 'href="/catalog"' in html
        assert "cited style" not in html
        assert "invented anti-pattern" not in html
        _public_page_guards(html)
    rendered = render_catalog_rule(catalog, gid, tree)
    assert rendered is not None
    assert 'data-field="severity"' in rendered


def test_catalog_rule_severity_chip_only_when_present() -> None:
    guideline = {
        "id": "demo.no_severity",
        "name": "No severity",
        "title": "no severity",
        "rule": "A rule.",
        "overview": "Overview text.",
        "apply_when": "Apply.",
        "not_when": "Not.",
        "agent_hint": "Hint.",
        "description": "Desc.",
        "pass_when": ["Pass this."],
        "fail_when": ["Fail this."],
        "citation": [{"source": "NN/g", "url": "https://www.nngroup.com/"}],
        "container": "forms_and_input",
        "card": "design_a_form",
        "facet": "field_has_no_lasting_name",
    }
    catalog = Catalog(
        version="0.3.0",
        guidelines=[guideline],
        jobs=[],
        patterns=[],
        size_bytes=0,
        path=Path("."),
        index=[{"id": guideline["id"], "name": guideline["name"], "title": guideline["title"]}],
    )
    html = render_catalog_rule(catalog, guideline["id"])
    assert html is not None
    assert 'data-field="severity"' not in html
    assert "Major" not in html


def test_catalog_pages_escape_text() -> None:
    nasty = {
        "id": "evil.alert",
        "name": "<script>alert(1)</script>",
        "title": "a&b",
        "rule": "<img src=x onerror=alert(1)>",
        "overview": "O<script>",
        "container": "forms_and_input",
        "card": "design_a_form",
        "facet": "x",
        "citation": [{"source": "<b>src</b>", "url": "javascript:alert(1)"}],
    }
    catalog = Catalog(
        version="0.3.0",
        guidelines=[nasty],
        jobs=[],
        patterns=[],
        size_bytes=0,
        path=Path("."),
        index=[
            {
                "id": nasty["id"],
                "name": nasty["name"],
                "title": nasty["title"],
                "container": "forms_and_input",
                "card": "design_a_form",
            }
        ],
    )
    listed = render_catalog_list(catalog)
    assert "<script>alert(1)</script>" not in listed
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in listed
    detail = render_catalog_rule(catalog, nasty["id"])
    assert detail is not None
    assert "<script>alert(1)</script>" not in detail
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in detail
    assert "<img src=x" not in detail
    assert 'href="javascript:alert(1)"' not in detail
    missing = render_catalog_not_found("<em>nope</em>")
    assert "<em>nope</em>" not in missing
    assert "&lt;em&gt;nope&lt;/em&gt;" in missing


def test_catalog_unknown_id_is_404(live_catalog: Path) -> None:
    with _client() as client:
        response = client.get("/catalog/not.a.real.rule")
        assert response.status_code == 404
        html = response.text
        assert "not.a.real.rule" in html
        assert "No guideline with id" in html
        _public_page_guards(html)


def test_catalog_stdio_http_surface_still_public(tmp_env: Path) -> None:
    with _client(hosted=False) as client:
        response = client.get("/catalog")
        assert response.status_code == 200
        assert "<h1>Catalog</h1>" in response.text


def test_landing_catalog_link(tmp_env: Path) -> None:
    with _client() as client:
        html = client.get("/").text
        assert 'href="/catalog"' in html
        assert ">Catalog</a>" in html


def _row_name_for(html: str, guideline_id: str) -> str:
    marker = f'data-id="{guideline_id}"'
    start = html.index(marker)
    chunk = html[start : html.index("</a>", start)]
    open_tag = chunk.index('class="row-name">') + len('class="row-name">')
    return chunk[open_tag : chunk.index("</span>", open_tag)]


def test_catalog_list_row_title_is_name_without_source(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    guideline = next(g for g in catalog.guidelines if g["id"] == NNG_SEED)
    assert guideline["name"].endswith(" — NN/g")
    with _client() as client:
        html = client.get("/catalog").text
    title = _row_name_for(html, NNG_SEED)
    assert title == _strip_source_suffix(guideline["name"])
    assert title == "Visible field label"
    assert "— NN/g" not in title
    assert "— Spectrum" not in title
    assert title != guideline["name"]


def test_catalog_rule_h1_is_name_field_without_source(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    guideline = next(g for g in catalog.guidelines if g["id"] == NNG_SEED)
    claim = _strip_source_suffix(guideline["name"])
    assert claim == "Visible field label"
    with _client() as client:
        html = client.get(f"/catalog/{NNG_SEED}").text
    h1 = html.split('<h1 class="rule-name" data-field="name">', 1)[1].split("</h1>", 1)[0]
    assert h1 == claim
    assert "— NN/g" not in h1
    assert h1 != guideline["name"]


def test_catalog_rule_one_cite_row_per_citation(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    guideline = next(g for g in catalog.guidelines if g["id"] == MULTI_CITE_ID)
    cites = citations(guideline)
    assert len(cites) >= 2
    with _client() as client:
        html = client.get(f"/catalog/{MULTI_CITE_ID}").text
    assert html.count('class="cite-row"') == len(cites)
    joined = "; ".join(str(row["source"]) for row in cites)
    assert joined not in html
    for row in cites:
        source = str(row["source"])
        url = str(row["url"])
        assert f'<div class="cite-row">' in html
        assert f'<p class="cite-source">{source}</p>' in html
        assert f'<a class="cite-url" href="{url}">{url}</a>' in html
