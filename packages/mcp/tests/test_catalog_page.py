from __future__ import annotations

import re
from html.parser import HTMLParser
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
from open_ux.jobs import load_job_tree
from open_ux.server import create_mcp
from open_ux.settings import Settings

ANT_SEED = "ant.checkbox-vs-switch"
MULTI_CITE_ID = ANT_SEED
HOUSE_ID_FLUENT = "fluent.multistep-next-not-continue"
HOUSE_ID_ANT = ANT_SEED
FORMS_LANE_ID = "forms.labels.clickable"
KNOWN_BODY = "Place a clear label outside the field so users always know what information belongs there."
FIELD_ORDER = (
    "name",
    "id",
    "rule",
    "description",
    "apply_when",
    "not_when",
    "agent_hint",
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
        visible = _visible_row_tags(html)
        assert 1 <= len(visible) <= PAGE_SIZE
        assert len(visible) == min(PAGE_SIZE, len(catalog.index))
        for gid in (ANT_SEED, HOUSE_ID_FLUENT, FORMS_LANE_ID, "govuk.date-input-only-memorable"):
            assert gid in html
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
    guideline = next(g for g in catalog.guidelines if g["id"] == ANT_SEED)
    gid = guideline["id"]
    with _client() as client:
        response = client.get(f"/catalog/{gid}")
        assert response.status_code == 200
        html = response.text
        claim = guideline["name"]
        assert claim == "Checkbox vs switch — Ant"
        assert (
            '<h1 class="rule-name" data-field="name">Checkbox vs switch</h1>'
            in html
        )
        assert "— Ant" in claim
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
        assert 'data-field="overview"' not in html
        assert ">Overview</p>" not in html
        assert guideline["overview"] not in html
        assert 'data-field="description"' in html
        assert guideline["description"] in html
        assert 'class="crumb-path"' not in html
        assert f">/catalog/{gid}<" not in html
        assert html.count('data-field="id">checkbox-vs-switch</p>') == 1
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
    assert 'data-field="overview"' not in html
    assert "Overview text." not in html
    assert 'data-field="description"' in html


def test_catalog_rule_omits_overview_and_empty_description() -> None:
    guideline = {
        "id": "demo.no_description",
        "name": "No description",
        "title": "no description",
        "rule": "A rule.",
        "overview": "Overview must not appear.",
        "apply_when": "Apply.",
        "not_when": "Not.",
        "agent_hint": "Hint.",
        "pass_when": ["Pass this."],
        "fail_when": ["Fail this."],
        "citation": [{"source": "NN/g", "url": "https://www.nngroup.com/"}],
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
    assert 'data-field="overview"' not in html
    assert ">Overview</p>" not in html
    assert "Overview must not appear." not in html
    assert 'data-field="description"' not in html
    assert ">Description</p>" not in html


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


def _visible_row_tags(html: str) -> list[str]:
    return [
        tag
        for tag in re.findall(r"<a class=\"catalog-row\"[^>]*>", html)
        if not tag.endswith(" hidden>")
    ]


def _row_container_for(html: str, guideline_id: str) -> str:
    marker = f'data-id="{guideline_id}"'
    start = html.rfind("<a ", 0, html.index(marker))
    tag = html[start : html.index(">", start) + 1]
    match = re.search(r'data-container="([^"]*)"', tag)
    assert match is not None
    return match.group(1)


def _row_id_for(html: str, guideline_id: str) -> str:
    marker = f'data-id="{guideline_id}"'
    start = html.index(marker)
    chunk = html[start : html.index("</a>", start)]
    open_tag = chunk.index('class="row-id">') + len('class="row-id">')
    return chunk[open_tag : chunk.index("</span>", open_tag)]


def _row_name_for(html: str, guideline_id: str) -> str:
    marker = f'data-id="{guideline_id}"'
    start = html.index(marker)
    chunk = html[start : html.index("</a>", start)]
    open_tag = chunk.index('class="row-name">') + len('class="row-name">')
    return chunk[open_tag : chunk.index("</span>", open_tag)]


def test_catalog_list_row_title_strips_house_suffix(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    guideline = next(g for g in catalog.guidelines if g["id"] == ANT_SEED)
    assert guideline["name"].endswith(" — Ant")
    with _client() as client:
        html = client.get("/catalog").text
    title = _row_name_for(html, ANT_SEED)
    assert title == "Checkbox vs switch"
    assert "—" not in title
    assert "Ant" not in title
    assert 'class="row-name">Checkbox vs switch — Ant</span>' not in html


def test_catalog_human_titles_strip_house_suffix(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    guideline = next(g for g in catalog.guidelines if g["id"] == ANT_SEED)
    claim = guideline["name"]
    assert claim == "Checkbox vs switch — Ant"
    with _client() as client:
        listed = client.get("/catalog").text
        rule = client.get(f"/catalog/{ANT_SEED}").text
    assert _row_name_for(listed, ANT_SEED) == "Checkbox vs switch"
    h1 = rule.split('<h1 class="rule-name" data-field="name">', 1)[1].split("</h1>", 1)[0]
    assert h1 == "Checkbox vs switch"
    assert "—" not in h1
    assert "Ant" not in h1
    assert ">Checkbox vs switch — Ant</span>" not in listed
    assert ">Checkbox vs switch — Ant</span>" not in rule
    assert re.search(
        r'<a class="tree-item tree-item--rule is-active"[^>]*>'
        r'(?:<span class="tree-pip"[^>]*></span>)?'
        r"<span>Checkbox vs switch</span></a>",
        rule,
    )
    assert "Ant Design — Data entry" in rule
    assert 'data-field="citation"' in rule
    assert '<p class="cite-source">' in rule
    for name in re.findall(r'class="row-name">([^<]*)</span>', listed):
        assert "— Ant" not in name
        assert "— Fluent" not in name
    assert "— Fluent" not in _row_name_for(listed, HOUSE_ID_FLUENT)
    assert "— Ant" not in h1


def test_catalog_visible_ids_strip_house_prefix(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    by_id = {row["id"] for row in catalog.index}
    assert HOUSE_ID_FLUENT in by_id
    assert HOUSE_ID_ANT in by_id
    with _client() as client:
        listed = client.get("/catalog").text
        fluent = client.get(f"/catalog/{HOUSE_ID_FLUENT}").text
        ant = client.get(f"/catalog/{HOUSE_ID_ANT}").text
        lane_rule = client.get(f"/catalog/{FORMS_LANE_ID}").text
    assert _row_id_for(listed, HOUSE_ID_FLUENT) == "multistep-next-not-continue"
    assert _row_id_for(listed, HOUSE_ID_ANT) == "checkbox-vs-switch"
    assert 'class="row-id">fluent.multistep-next-not-continue</span>' not in listed
    assert 'class="row-id">ant.checkbox-vs-switch</span>' not in listed
    assert f'href="/catalog/{HOUSE_ID_FLUENT}"' in listed
    assert f'href="/catalog/{HOUSE_ID_ANT}"' in listed
    assert f'data-id="{HOUSE_ID_FLUENT}"' in listed
    assert f'data-id="{HOUSE_ID_ANT}"' in listed
    assert 'data-field="id">multistep-next-not-continue</p>' in fluent
    assert 'data-field="id">checkbox-vs-switch</p>' in ant
    assert f'data-field="id">{HOUSE_ID_FLUENT}</p>' not in fluent
    assert f'data-field="id">{HOUSE_ID_ANT}</p>' not in ant
    assert f'href="/catalog/{HOUSE_ID_FLUENT}"' in fluent
    assert f'href="/catalog/{HOUSE_ID_ANT}"' in ant
    fluent_h1 = fluent.split('<h1 class="rule-name" data-field="name">', 1)[1].split(
        "</h1>", 1
    )[0]
    assert "— Fluent" not in fluent_h1
    assert _row_id_for(listed, FORMS_LANE_ID) == FORMS_LANE_ID
    assert f'data-field="id">{FORMS_LANE_ID}</p>' in lane_rule


class _VisibleCatalogText(HTMLParser):
    """Text nodes outside script/style and citation blocks."""

    def __init__(self) -> None:
        super().__init__()
        self.skip = 0
        self.cite = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        cls = " ".join(str(v) for k, v in attrs if k == "class" and v)
        field = next((v for k, v in attrs if k == "data-field"), "")
        if tag in {"script", "style"}:
            self.skip += 1
        if "cite-row" in cls.split() or "cite-list" in cls.split() or field == "citation":
            self.cite += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self.skip:
            self.skip -= 1
        if tag in {"div", "section", "a", "p"} and self.cite:
            self.cite -= 1

    def handle_data(self, data: str) -> None:
        if self.skip or self.cite:
            return
        if data:
            self.parts.append(data)


def _visible_catalog_text(html: str) -> str:
    parser = _VisibleCatalogText()
    parser.feed(html)
    return "".join(parser.parts)


def test_catalog_house_absent_from_visible_text(live_catalog: Path) -> None:
    with _client() as client:
        listed = client.get("/catalog").text
        rule = client.get(f"/catalog/{ANT_SEED}").text
        fluent = client.get(f"/catalog/{HOUSE_ID_FLUENT}").text
    assert "Checkbox vs switch — Ant" not in listed
    assert "Checkbox vs switch — Ant" not in rule
    listed_text = _visible_catalog_text(listed)
    rule_text = _visible_catalog_text(rule)
    fluent_text = _visible_catalog_text(fluent)
    assert "Checkbox vs switch — Ant" not in listed_text
    assert "Checkbox vs switch — Ant" not in rule_text
    assert "— Ant" not in listed_text
    assert "— Fluent" not in listed_text
    assert "— Fluent" not in fluent_text
    assert "fluent." not in listed_text
    assert "fluent." not in fluent_text
    assert _row_id_for(listed, HOUSE_ID_FLUENT) == "multistep-next-not-continue"
    assert _row_name_for(listed, ANT_SEED) == "Checkbox vs switch"


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


def test_catalog_list_chip_forms_filters_container(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    chip_ids = {cid for cid, _label in CONTAINER_CHIPS}
    with _client() as client:
        html = client.get("/catalog").text
    assert 'data-chip="forms_and_input"' in html
    assert ">Forms</button>" in html
    assert 'data-chip="" aria-pressed="true">All</button>' in html
    assert 'aria-pressed="false">Forms</button>' in html
    assert "matchC && matchQ" in html
    forms = 0
    for row in catalog.index:
        cid = _row_container_for(html, row["id"])
        assert cid in chip_ids
        assert cid == row["container"]
        if cid == "forms_and_input":
            forms += 1
    assert forms >= 1
    assert html.count('data-container="forms_and_input"') == forms


def test_catalog_list_paginates_filtered_set(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    total = len(catalog.index)
    assert total > PAGE_SIZE
    with _client() as client:
        html = client.get("/catalog").text
    tags = re.findall(r"<a class=\"catalog-row\"[^>]*>", html)
    assert len(tags) == total
    visible = _visible_row_tags(html)
    assert len(visible) == PAGE_SIZE
    assert sum(tag.endswith(" hidden>") for tag in tags) == total - PAGE_SIZE
    assert 'id="catalog-pager"' in html
    assert ">Prev</button>" in html
    assert ">Next</button>" in html
    assert f"1–{PAGE_SIZE} of {total}" in html
    assert "btn--outline" in html
    assert f"const PAGE_SIZE = {PAGE_SIZE}" in html
    assert "page += 1" in html
    assert "page -= 1" in html
    second = None
    with _client() as client:
        second = client.get("/catalog?page=2").text
    visible2 = _visible_row_tags(second)
    assert len(visible2) == PAGE_SIZE
    assert _visible_row_tags(html) != visible2
    assert f"{PAGE_SIZE + 1}–{PAGE_SIZE * 2} of {total}" in second
    last_page = (total + PAGE_SIZE - 1) // PAGE_SIZE
    short = total - (last_page - 1) * PAGE_SIZE
    with _client() as client:
        last = client.get(f"/catalog?page={last_page}").text
    assert len(_visible_row_tags(last)) == short


def test_catalog_query_params_keep_filter_and_search(live_catalog: Path) -> None:
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
    visible = _visible_row_tags(html)
    assert len(visible) == PAGE_SIZE
    for tag in visible:
        assert 'data-container="forms_and_input"' in tag
    q = "visible"
    anded = [
        row
        for row in forms
        if q in f"{row.get('id') or ''} {row.get('title') or ''} {row.get('name') or ''}".lower()
    ]
    assert anded
    with _client() as client:
        searched = client.get("/catalog?container=forms_and_input&q=visible").text
    assert f"{len(anded)} shown" in searched
    assert 'value="visible"' in searched
    found = _visible_row_tags(searched)
    assert found
    assert len(found) <= PAGE_SIZE
    for tag in found:
        assert 'data-container="forms_and_input"' in tag
    assert "history.replaceState" in html
    assert 'params.set("container"' in html
    assert 'params.set("q"' in html
    assert 'params.set("page"' in html


def test_catalog_list_resolves_missing_container_from_tree(live_catalog: Path) -> None:
    row = {
        "id": "forms.labels.clickable",
        "name": "Clickable — Vercel",
        "title": "visible label",
        "card": "design_a_form",
    }
    catalog = Catalog(
        version="0.3.0",
        guidelines=[row],
        jobs=[],
        patterns=[],
        size_bytes=0,
        path=Path("."),
        index=[row],
    )
    tree = load_job_tree(Settings.load())
    html = render_catalog_list(catalog, tree)
    assert 'data-container="forms_and_input"' in html
    assert 'data-chip="forms_and_input"' in html


def test_catalog_nav_has_mark_wordmark(live_catalog: Path) -> None:
    with _client() as client:
        listed = client.get("/catalog").text
        rule = client.get(f"/catalog/{ANT_SEED}").text
    for html in (listed, rule):
        assert 'class="nav-brand" href="/"' in html
        assert '<img class="mark" src="/logo-mark.svg"' in html
        assert '<span class="wordmark">Open UX</span>' in html
        assert "class=\"nav-brand\" href=\"/\"><span class=\"pip\"" not in html
        assert "UNS-44" not in html
        assert "uns-44" not in html


def test_catalog_type_scale_matches_figma(live_catalog: Path) -> None:
    with _client() as client:
        listed = client.get("/catalog").text
        rule = client.get(f"/catalog/{ANT_SEED}").text
    css = listed.split("<style>", 1)[1].split("</style>", 1)[0]
    for selector, body in re.findall(r"([^{}]+)\{([^}]+)\}", css):
        sizes = [int(n) for n in re.findall(r"font-size:\s*(\d+)px", body)]
        if not sizes:
            continue
        decorative = any(
            token in selector for token in (".pip", ".tree-pip", ".tree-caret")
        )
        if decorative:
            continue
        for n in sizes:
            assert n >= 14, f"{selector.strip()} font-size {n}px is below floor 14"
    assert re.search(r"h1 \{[^}]*font-size: 28px", listed, re.S)
    assert re.search(r"\.row-name \{[^}]*font-size: 16px", listed, re.S)
    assert re.search(r"\.row-id \{[^}]*font-size: 14px", listed, re.S)
    assert re.search(r"\.row-dot, \.row-path \{[^}]*font-size: 14px", listed, re.S)
    assert re.search(r"\.chip \{[^}]*font-size: 14px", listed, re.S)
    assert re.search(r"\.lede \{[^}]*font-size: 16px", listed, re.S)
    assert re.search(r"\.rule-name \{[^}]*font-size: 28px", rule, re.S)
    assert re.search(r"\.rule-id \{[^}]*font-size: 14px", rule, re.S)
    assert re.search(r"\.block-body \{[^}]*font-size: 16px", rule, re.S)
    assert re.search(r"\.block-label \{[^}]*font-size: 16px", rule, re.S)
    assert re.search(r"\.block-label \{[^}]*font-weight: 600", rule, re.S)
    assert not re.search(r"\.block-label \{[^}]*font-size: 14px", rule, re.S)
    assert re.search(r"\.tree-item \{[^}]*font-size: 14px", rule, re.S)
    assert re.search(r"\.tree-item--rule \{[^}]*font-size: 14px", rule, re.S)
    assert not re.search(r"\.tree-item--rule \{[^}]*font-size: 16px", rule, re.S)



def test_catalog_tree_carets_toggle_and_rules_link(live_catalog: Path) -> None:
    catalog = load_catalog(Settings.load(hosted=True))
    other = next(
        g
        for g in catalog.guidelines
        if g.get("container") and g["container"] != "forms_and_input"
    )
    with _client() as client:
        html = client.get(f"/catalog/{ANT_SEED}").text
    assert 'id="catalog-tree"' in html
    assert 'aria-expanded="true"' in html
    assert 'aria-expanded="false"' in html
    assert 'class="tree-group is-open"' in html
    assert 'tree-item tree-item--container"' in html
    assert 'tree-item tree-item--card"' in html
    assert 'tree-item tree-item--facet"' in html
    assert html.count('class="tree-caret"') >= 3
    assert '<div class="tree-item tree-item--rule' not in html
    rule_links = re.findall(
        r'<a class="tree-item tree-item--rule[^"]*" href="/catalog/[^"]+"',
        html,
    )
    assert len(rule_links) == len(catalog.index)
    assert f'href="/catalog/{ANT_SEED}"' in html
    assert f'href="/catalog/{other["id"]}"' in html
    assert (
        f'<a class="tree-item tree-item--rule is-active" href="/catalog/{ANT_SEED}">'
        in html
    )
    assert re.search(
        r'<a class="tree-item tree-item--rule is-active"[^>]*>'
        r'(?:<span class="tree-pip"[^>]*></span>)?'
        r"<span>Checkbox vs switch</span></a>",
        html,
    )
    assert ">Checkbox vs switch — Ant</span>" not in html
    assert "Design a form" in html
    assert 'closest("button.tree-item[aria-expanded]")' in html
    assert 'classList.toggle("is-open"' in html
    assert 'caret.textContent = next ? "▾" : "▸"' in html
    _public_page_guards(html)


