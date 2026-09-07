from __future__ import annotations

import re
from pathlib import Path

from starlette.testclient import TestClient

from open_ux.catalog import Catalog, citations, load_catalog
from open_ux.catalog_page import (
    CONTAINER_CHIPS,
    PAGE_SIZE,
    render_catalog_list,
    render_catalog_not_found,
    render_catalog_rule,
)
from open_ux.jobs import CONTAINER_IDS, load_job_tree
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
        claim = guideline["name"]
        assert f'<h1 class="rule-name" data-field="name">{claim}</h1>' in html
        assert "— NN/g" in claim
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


_ROW_TAG = re.compile(
    r'<a class="catalog-row"(?P<hidden> hidden)? href="[^"]*" '
    r'data-id="(?P<id>[^"]*)" data-container="(?P<container>[^"]*)"'
)


def _parse_list_rows(html: str) -> list[dict[str, str | bool]]:
    return [
        {
            "id": m.group("id"),
            "container": m.group("container"),
            "hidden": bool(m.group("hidden")),
        }
        for m in _ROW_TAG.finditer(html)
    ]


def _visible_list_rows(html: str) -> list[dict[str, str | bool]]:
    return [row for row in _parse_list_rows(html) if not row["hidden"]]


def _assert_nav_wordmark(html: str) -> None:
    assert 'class="nav-brand"' in html
    assert 'class="pip"' in html
    assert 'class="wordmark">Open UX</span>' in html


def test_catalog_list_row_title_keeps_source_suffix(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    guideline = next(g for g in catalog.guidelines if g["id"] == NNG_SEED)
    assert guideline["name"].endswith(" — NN/g")
    with _client() as client:
        html = client.get("/catalog").text
    title = _row_name_for(html, NNG_SEED)
    assert title == guideline["name"]
    assert "— NN/g" in title
    assert title != "Visible field label"


def test_catalog_rule_h1_keeps_source_suffix(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    guideline = next(g for g in catalog.guidelines if g["id"] == NNG_SEED)
    assert guideline["name"] == "Visible field label — NN/g"
    with _client() as client:
        html = client.get(f"/catalog/{NNG_SEED}").text
    h1 = html.split('<h1 class="rule-name" data-field="name">', 1)[1].split("</h1>", 1)[0]
    assert h1 == guideline["name"]
    assert "— NN/g" in h1


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


def test_catalog_nav_has_pip_wordmark(live_catalog: Path) -> None:
    with _client() as client:
        listed = client.get("/catalog").text
        rule = client.get(f"/catalog/{NNG_SEED}").text
    _assert_nav_wordmark(listed)
    _assert_nav_wordmark(rule)


def test_catalog_list_meta_type_is_figma_12px(live_catalog: Path) -> None:
    with _client() as client:
        css = client.get("/catalog").text.split("<style>", 1)[1].split("</style>", 1)[0]
    assert re.search(r"\.row-id \{[^}]*font-size: 12px", css)
    assert re.search(r"\.row-path \{[^}]*font-size: 12px", css)
    assert ".catalog-row[hidden] { display: none; }" in css


def test_every_live_row_has_container_chip_id(live_catalog: Path) -> None:
    chip_ids = {cid for cid, _label in CONTAINER_CHIPS}
    assert chip_ids == set(CONTAINER_IDS)
    with _client() as client:
        html = client.get("/catalog").text
    rows = _parse_list_rows(html)
    assert rows
    for row in rows:
        assert row["container"] in chip_ids


def test_forms_chip_filters_rows_and_updates_count(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    forms = [row for row in catalog.index if row.get("container") == "forms_and_input"]
    assert len(forms) > PAGE_SIZE
    with _client() as client:
        html = client.get("/catalog?container=forms_and_input").text
    assert f"{len(forms)} shown" in html
    assert (
        'class="chip is-selected" data-chip="forms_and_input" aria-pressed="true">Forms</button>'
        in html
    )
    assert 'data-chip="" aria-pressed="false">All</button>' in html
    visible = _visible_list_rows(html)
    assert len(visible) == PAGE_SIZE
    assert all(row["container"] == "forms_and_input" for row in visible)
    hidden_other = [
        row
        for row in _parse_list_rows(html)
        if row["hidden"] and row["container"] != "forms_and_input"
    ]
    assert hidden_other
    assert "matchC && matchQ" in html


def test_search_ands_with_chip(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    q = "visible"
    forms = [
        row
        for row in catalog.index
        if row.get("container") == "forms_and_input"
        and q in f"{row.get('id') or ''} {row.get('title') or ''} {row.get('name') or ''}".lower()
    ]
    assert forms
    with _client() as client:
        html = client.get("/catalog?container=forms_and_input&q=visible").text
    assert f"{len(forms)} shown" in html
    assert 'id="catalog-search"' in html
    assert 'value="visible"' in html
    visible = _visible_list_rows(html)
    assert visible
    assert len(visible) <= PAGE_SIZE
    assert all(row["container"] == "forms_and_input" for row in visible)
    for row in visible:
        assert q in row["id"] or q in _row_name_for(html, str(row["id"])).lower()


def test_catalog_list_paginates_filtered_set(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    total = len(catalog.index)
    assert total > PAGE_SIZE
    last_page = (total + PAGE_SIZE - 1) // PAGE_SIZE
    short = total - (last_page - 1) * PAGE_SIZE
    assert 1 <= short <= PAGE_SIZE
    with _client() as client:
        first = client.get("/catalog").text
        second = client.get("/catalog?page=2").text
        last = client.get(f"/catalog?page={last_page}").text
    v1 = _visible_list_rows(first)
    v2 = _visible_list_rows(second)
    vlast = _visible_list_rows(last)
    assert len(v1) == PAGE_SIZE
    assert len(v2) == PAGE_SIZE
    assert [row["id"] for row in v1] != [row["id"] for row in v2]
    assert len(vlast) == short
    assert f"1–{PAGE_SIZE} of {total}" in first
    assert f"{PAGE_SIZE + 1}–{PAGE_SIZE * 2} of {total}" in second
    assert 'id="pager-prev"' in first
    assert 'id="pager-next"' in first
    assert "btn--outline" in first
    assert "const PAGE_SIZE = 25;" in first
    assert 'id="pager-prev" disabled' in first
    assert 'id="pager-next"' in first
    assert f"{(last_page - 1) * PAGE_SIZE + 1}–{total} of {total}" in last


def test_missing_index_container_resolved_from_jobs_card(live_catalog: Path) -> None:
    tree = load_job_tree(Settings.load())
    guideline = {
        "id": "demo.missing_container",
        "name": "Missing container — NN/g",
        "title": "missing container",
        "rule": "A rule.",
        "card": "design_a_form",
        "citation": [{"source": "NN/g", "url": "https://www.nngroup.com/"}],
    }
    catalog = Catalog(
        version="0.3.0",
        guidelines=[guideline],
        jobs=[],
        patterns=[],
        size_bytes=0,
        path=Path("."),
        index=[
            {
                "id": guideline["id"],
                "name": guideline["name"],
                "title": guideline["title"],
                "card": "design_a_form",
            }
        ],
    )
    html = render_catalog_list(catalog, tree)
    rows = _parse_list_rows(html)
    assert rows == [
        {
            "id": "demo.missing_container",
            "container": "forms_and_input",
            "hidden": False,
        }
    ]
    assert "— NN/g" in _row_name_for(html, guideline["id"])
