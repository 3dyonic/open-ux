"""Public `/catalog` HTML: F3 list (36:22) and rule (78:26). HTTP-only."""

from __future__ import annotations

from html import escape
from urllib.parse import quote
from typing import Any

from open_ux.catalog import SOURCE_HOUSES, Catalog, citations, get_by_id, list_index
from open_ux.jobs import JobTree, card_by_id, empty_job_tree
from open_ux.public_html import (
    CATALOG_TITLE,
    CONSENT_CSS,
    LANDING_DESCRIPTION,
    MARK_CSS,
    NAV_BRAND_HTML,
    NAV_GITHUB_HTML,
    OSS_FOOTER_CSS,
    PAGE_SHELL_CSS,
    head_meta,
    public_consent_footer,
    public_gtm_head,
    public_gtm_noscript,
    public_oss_footer,
    rule_meta_description,
    rule_meta_title,
)

# Longest house label first so "Suomi.fi" wins over a shorter tail.
_SOURCE_SUFFIXES = tuple(
    f" — {label}"
    for label in sorted(SOURCE_HOUSES.values(), key=len, reverse=True)
)

# Figma 36:22 chip labels for the locked seven containers.
CONTAINER_CHIPS: tuple[tuple[str, str], ...] = (
    ("forms_and_input", "Forms"),
    ("actions_and_decisions", "Actions"),
    ("feedback_and_status", "Feedback"),
    ("navigation_and_wayfinding", "Wayfinding"),
    ("layout_and_data_display", "Layout"),
    ("overlays_and_content_structure", "Overlays"),
    ("multi_step_flows", "Multi-step"),
)

PAGE_SIZE = 25
_CHIP_IDS = frozenset(cid for cid, _label in CONTAINER_CHIPS)

_CSS = """
    :root {
      --paper: #F9F6F2;
      --card: #ffffff;
      --ink: #1F1B16;
      --muted: #6A6056;
      --line: #DED4C8;
      --pip: #FF4B00;
      --pip-soft: #FFECE0;
      --danger: #B82A2A;
      --danger-bg: #fdecec;
      --success: #1A7F37;
      --success-bg: #e7f6ec;
      --radius: 6px;
      --sans: "IBM Plex Sans", ui-sans-serif, system-ui, sans-serif;
      --mono: "IBM Plex Mono", ui-monospace, monospace;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: var(--sans);
      font-size: 16px;
      line-height: 1.5;
      color: var(--ink);
      background: var(--paper);
    }
    a { color: inherit; text-decoration: none; }
    .nav {
      display: flex;
      align-items: center;
      justify-content: space-between;
      width: 100%;
      padding: 16px 48px;
      background: var(--paper);
      border-bottom: 1px solid var(--line);
    }
    .nav-actions {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .nav-link {
      font-size: 14px;
      font-weight: 400;
      color: var(--muted);
    }
    .nav-catalog {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 14px;
      font-weight: 500;
      color: var(--pip);
    }
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 10px 16px;
      border-radius: var(--radius);
      font-family: inherit;
      font-size: 14px;
      font-weight: 600;
      line-height: normal;
      cursor: pointer;
      text-decoration: none;
      border: none;
    }
    .btn--primary {
      background: var(--pip);
      color: #FFECDC;
    }
    .btn--outline {
      background: var(--card);
      color: var(--ink);
      border: 1px solid var(--line);
    }
    .btn:disabled {
      opacity: 0.4;
      cursor: default;
    }
    .main {
      display: flex;
      flex-direction: column;
      gap: 28px;
      width: 100%;
      padding: 40px 48px 48px;
    }
    .header { display: flex; flex-direction: column; gap: 8px; }
    .title-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }
    h1 {
      margin: 0;
      font-size: 28px;
      font-weight: 700;
      line-height: normal;
      color: var(--ink);
    }
    .shown {
      margin: 0;
      font-family: var(--mono);
      font-size: 14px;
      color: var(--muted);
    }
    .lede {
      margin: 0;
      font-size: 16px;
      color: var(--muted);
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 8px;
      width: 100%;
    }
    .field label {
      font-size: 14px;
      font-weight: 500;
      color: var(--ink);
    }
    .field__input {
      width: 100%;
      padding: 12px 14px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--card);
      color: var(--ink);
      font-family: inherit;
      font-size: 14px;
    }
    .field__input::placeholder { color: var(--muted); }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .chip {
      padding: 6px 12px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: var(--card);
      color: var(--ink);
      font-family: inherit;
      font-size: 14px;
      font-weight: 500;
      cursor: pointer;
    }
    .chip.is-selected {
      background: var(--pip-soft);
      border-color: var(--pip);
      color: var(--pip);
    }
    .list {
      width: 100%;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      overflow: hidden;
    }
    .catalog-row {
      display: flex;
      align-items: center;
      gap: 10px;
      width: 100%;
      padding: 12px 20px;
      border-bottom: 1px solid var(--line);
      color: inherit;
    }
    .catalog-row:last-child { border-bottom: none; }
    .catalog-row[hidden] { display: none; }
    .pager {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      width: 100%;
    }
    .pager-meta {
      margin: 0;
      font-family: var(--mono);
      font-size: 14px;
      color: var(--muted);
    }
    .row-id {
      font-family: var(--mono);
      font-size: 14px;
      font-weight: 500;
      color: var(--pip);
      text-decoration: underline;
      flex-shrink: 0;
    }
    .row-dot, .row-path {
      font-size: 14px;
      color: var(--muted);
      flex-shrink: 0;
    }
    .row-name {
      flex: 1 1 auto;
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-size: 16px;
      color: var(--ink);
    }
    .row-chevron {
      font-size: 16px;
      font-weight: 500;
      color: var(--muted);
      flex-shrink: 0;
    }
    .rule-shell {
      display: flex;
      align-items: flex-start;
      width: 100%;
    }
    .sidebar {
      width: 260px;
      flex-shrink: 0;
      padding: 40px 12px 48px 20px;
      border-right: 1px solid var(--line);
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .tree-group, .tree-children {
      display: flex;
      flex-direction: column;
      gap: 2px;
      width: 100%;
    }
    .tree-group:not(.is-open) > .tree-children { display: none; }
    .tree-item {
      display: flex;
      align-items: center;
      gap: 6px;
      min-height: 28px;
      padding: 6px 8px;
      border-radius: var(--radius);
      font-family: inherit;
      font-size: 14px;
      color: var(--ink);
      background: none;
      border: none;
      width: 100%;
      text-align: left;
      cursor: pointer;
    }
    .tree-item--card { padding-left: 20px; }
    .tree-item--facet { padding-left: 32px; color: var(--muted); font-weight: 500; }
    .tree-item--rule { padding-left: 44px; font-size: 14px; cursor: pointer; }
    .tree-item--container { font-weight: 600; }
    .tree-item.is-active {
      background: var(--pip-soft);
      color: var(--ink);
      font-weight: 500;
    }
    .tree-caret {
      width: 10px;
      font-size: 10px;
      color: var(--muted);
      flex-shrink: 0;
    }
    .tree-pip {
      width: 5px;
      height: 5px;
      border-radius: 50%;
      background: var(--pip);
      flex-shrink: 0;
    }
    .content {
      flex: 1 1 auto;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 28px;
      padding: 40px 48px 48px 40px;
    }
    .back {
      font-size: 14px;
      font-weight: 500;
      color: var(--pip);
      text-decoration: underline;
    }
    .eyebrow {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .eyebrow-path {
      margin: 0;
      font-size: 14px;
      font-weight: 500;
      color: var(--muted);
    }
    .severity {
      padding: 3px 8px;
      border: 1px solid var(--line);
      border-radius: 999px;
      font-size: 14px;
      font-weight: 500;
      color: var(--muted);
    }
    .rule-name {
      margin: 0;
      font-size: 28px;
      font-weight: 600;
      color: var(--ink);
    }
    .rule-id {
      margin: 0;
      font-family: var(--mono);
      font-size: 14px;
      color: var(--muted);
    }
    .rule-text {
      margin: 0;
      font-size: 16px;
      color: var(--ink);
    }
    .block { display: flex; flex-direction: column; gap: 8px; }
    .block-label {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--muted);
    }
    .block-label--use { color: var(--success); }
    .block-label--not { color: var(--danger); }
    .block-body {
      margin: 0;
      font-size: 16px;
      line-height: 24px;
      color: var(--ink);
    }
    .when-stack { display: flex; flex-direction: column; gap: 20px; }
    .examples { display: flex; flex-direction: column; gap: 16px; }
    .example {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
    }
    .example--pass { background: var(--success-bg); }
    .example--fail { background: var(--danger-bg); }
    .badge {
      display: inline-flex;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 14px;
      font-weight: 500;
      color: #fff;
    }
    .badge--pass { background: var(--success); }
    .badge--fail { background: var(--danger); }
    .cite-list { display: flex; flex-direction: column; gap: 10px; }
    .cite-row { display: flex; flex-direction: column; gap: 2px; }
    .cite-source { margin: 0; font-size: 16px; color: var(--ink); }
    .cite-url {
      margin: 0;
      font-family: var(--mono);
      font-size: 14px;
      color: var(--pip);
      word-break: break-all;
    }
    .empty, .not-found {
      margin: 0;
      font-size: 16px;
      color: var(--muted);
    }
""" + MARK_CSS + CONSENT_CSS + OSS_FOOTER_CSS + PAGE_SHELL_CSS


def _e(value: Any) -> str:
    return escape("" if value is None else str(value), quote=True)


def _href_id(guideline_id: str) -> str:
    return "/catalog/" + quote(guideline_id, safe="._-")


def _full_index(catalog: Catalog) -> list[dict[str, Any]]:
    items, _total = list_index(catalog, limit=max(len(catalog.index), 1))
    return items


def _container_title(tree: JobTree, container_id: str | None) -> str:
    if not container_id:
        return ""
    for container in tree.containers:
        if container.id == container_id:
            return container.title
    return container_id


def _card_title(tree: JobTree, card_id: str | None) -> str:
    if not card_id:
        return ""
    card = card_by_id(tree, card_id)
    return card.title if card is not None else card_id


def _facet_title(tree: JobTree, card_id: str | None, facet_id: str | None) -> str:
    if not facet_id:
        return ""
    card = card_by_id(tree, card_id or "")
    if card is not None:
        for facet in card.facets:
            if facet.id == facet_id:
                return facet.title
    return facet_id


def _row_path(row: dict[str, Any], tree: JobTree) -> str:
    left = _container_title(tree, _row_container(row, tree) or row.get("container"))
    right = _card_title(tree, row.get("card"))
    if left and right:
        return f"{left} / {right}"
    return left or right


def _raw_name(row: dict[str, Any]) -> str:
    return str(row.get("name") or row.get("title") or row.get("id") or "")


def _strip_house_suffix(name: str) -> str:
    """Drop a trailing ` — {house}` from human-facing rule titles."""
    text = name.strip()
    for suffix in _SOURCE_SUFFIXES:
        if text.endswith(suffix):
            return text[: -len(suffix)].rstrip()
    return text


def _display_name(row: dict[str, Any]) -> str:
    """Human-facing title: master `name` without ` — {house}` (fallback title → id)."""
    return _strip_house_suffix(_raw_name(row))


def _display_id(guideline_id: str) -> str:
    """Visible id only: drop a leading `{house}.` prefix. Href keeps the master id."""
    text = str(guideline_id or "").strip()
    if "." not in text:
        return text
    lane, rest = text.split(".", 1)
    if rest and lane in SOURCE_HOUSES:
        return rest
    return text


def _search_blob(row: dict[str, Any]) -> str:
    gid = str(row.get("id") or "")
    return f"{_display_id(gid)} {row.get('title') or ''} {_display_name(row)}".lower()


def _row_container(row: dict[str, Any], tree: JobTree) -> str:
    raw = str(row.get("container") or "").strip()
    if raw:
        return raw
    card = card_by_id(tree, str(row.get("card") or ""))
    if card is not None and card.container:
        return str(card.container)
    facet_id = str(row.get("facet") or "")
    if facet_id:
        for card in tree.cards:
            for facet in card.facets:
                if facet.id == facet_id:
                    return str(card.container)
    return ""


def _nav() -> str:
    return f"""
  <header class="nav">
    {NAV_BRAND_HTML}
    <div class="nav-actions">
      <a class="nav-catalog" href="/catalog">Catalog</a>
      {NAV_GITHUB_HTML}
      <a class="btn btn--primary" href="/invite">Get a key</a>
    </div>
  </header>
"""


def _page(
    title: str,
    body: str,
    script: str = "",
    *,
    description: str = LANDING_DESCRIPTION,
    path: str = "/catalog",
    consent: str | None = None,
) -> str:
    return (
        """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
"""
        + public_gtm_head(consent)
        + head_meta(title=title, description=description, path=path)
        + """
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
"""
        + _CSS
        + """
  </style>
</head>
<body>
"""
        + public_gtm_noscript(consent)
        + _nav()
        + body
        + (
            """
  <script>
"""
            + script
            + """
  </script>
"""
            if script
            else ""
        )
        + public_oss_footer()
        + public_consent_footer(consent)
        + """
</body>
</html>
"""
    )


def _chips_html(selected: str = "") -> str:
    wanted = selected if selected in _CHIP_IDS else ""
    parts = []
    for cid, label in (("", "All"),) + CONTAINER_CHIPS:
        on = cid == wanted
        cls = "chip is-selected" if on else "chip"
        pressed = "true" if on else "false"
        parts.append(
            f'<button type="button" class="{cls}" data-chip="{_e(cid)}" '
            f'aria-pressed="{pressed}">{_e(label)}</button>'
        )
    return '<div class="chips" id="catalog-chips">' + "".join(parts) + "</div>"


def _pager_meta(total: int, page: int = 1, size: int = PAGE_SIZE) -> str:
    if total <= 0:
        return "0 of 0"
    pages = max(1, (total + size - 1) // size)
    page = min(max(page, 1), pages)
    start = (page - 1) * size + 1
    end = min(page * size, total)
    return f"{start}–{end} of {total}"


def _pager_html(total: int, page: int = 1) -> str:
    if total < 0:
        return ""
    pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE) if total else 1
    page = min(max(page, 1), pages)
    prev_disabled = " disabled" if page <= 1 or total == 0 else ""
    next_disabled = " disabled" if page >= pages or total == 0 else ""
    return (
        f'<div class="pager" id="catalog-pager" data-page="{page}">'
        f'<button type="button" class="btn btn--outline" id="page-prev"{prev_disabled}>Prev</button>'
        f'<p class="pager-meta" id="page-meta">{_e(_pager_meta(total, page))}</p>'
        f'<button type="button" class="btn btn--outline" id="page-next"{next_disabled}>Next</button>'
        "</div>"
    )


def _rows_html(
    rows: list[dict[str, Any]],
    tree: JobTree,
    *,
    container: str = "",
    query: str = "",
    page: int = 1,
) -> str:
    if not rows:
        return '<p class="empty">No guidelines in the catalog.</p>'
    q = query.strip().lower()
    matching: list[dict[str, Any]] = []
    for row in rows:
        cid = _row_container(row, tree)
        if container and cid != container:
            continue
        if q and q not in _search_blob(row):
            continue
        matching.append(row)
    pages = max(1, (len(matching) + PAGE_SIZE - 1) // PAGE_SIZE) if matching else 1
    page = min(max(page, 1), pages)
    start = (page - 1) * PAGE_SIZE
    visible_ids = {
        str(row.get("id") or "") for row in matching[start : start + PAGE_SIZE]
    }
    parts = ['<div class="list" id="catalog-list">']
    for row in rows:
        gid = str(row.get("id") or "")
        name = _display_name(row)
        path = _row_path(row, tree)
        search = _search_blob(row)
        cid = _row_container(row, tree)
        path_html = ""
        if path:
            path_html = (
                f'<span class="row-dot" aria-hidden="true">·</span>'
                f'<span class="row-path">{_e(path)}</span>'
                f'<span class="row-dot" aria-hidden="true">·</span>'
            )
        hidden = "" if gid in visible_ids else " hidden"
        # Figma 36:22: id · category · one-liner · chevron. No severity chip.
        parts.append(
            f'<a class="catalog-row" href="{_e(_href_id(gid))}" '
            f'data-id="{_e(gid)}" data-container="{_e(cid)}" '
            f'data-search="{_e(search)}"{hidden}>'
            f'<span class="row-id">{_e(_display_id(gid))}</span>'
            f"{path_html}"
            f'<span class="row-name">{_e(name)}</span>'
            f'<span class="row-chevron" aria-hidden="true">›</span>'
            f"</a>"
        )
    parts.append("</div>")
    parts.append(_pager_html(len(matching), page))
    return "".join(parts)


def render_catalog_list(
    catalog: Catalog,
    tree: JobTree | None = None,
    *,
    container: str = "",
    query: str = "",
    page: int = 1,
    consent: str | None = None,
) -> str:
    tree = tree or empty_job_tree()
    rows = _full_index(catalog)
    wanted = container if container in _CHIP_IDS else ""
    q = query.strip()
    matching_n = 0
    q_low = q.lower()
    for row in rows:
        cid = _row_container(row, tree)
        if wanted and cid != wanted:
            continue
        if q_low and q_low not in _search_blob(row):
            continue
        matching_n += 1
    value_attr = f' value="{_e(q)}"' if q else ""
    body = f"""
  <main class="main">
    <div class="header">
      <div class="title-row">
        <h1>Catalog</h1>
        <p class="shown" id="shown-count">{matching_n} shown</p>
      </div>
      <p class="lede">Cited UX rules agents audit against</p>
    </div>
    <div class="field">
      <label for="catalog-search">Search</label>
      <input class="field__input" id="catalog-search" type="search" autocomplete="off" spellcheck="false"{value_attr}>
    </div>
    {_chips_html(wanted)}
    {_rows_html(rows, tree, container=wanted, query=q, page=page)}
  </main>
"""
    script = f"""
    const PAGE_SIZE = {PAGE_SIZE};
    const search = document.getElementById("catalog-search");
    const chips = document.getElementById("catalog-chips");
    const rows = Array.from(document.querySelectorAll(".catalog-row"));
    const shown = document.getElementById("shown-count");
    const pager = document.getElementById("catalog-pager");
    const prev = document.getElementById("page-prev");
    const next = document.getElementById("page-next");
    const pageMeta = document.getElementById("page-meta");
    let container = "";
    if (chips) {{
      const on = chips.querySelector("[data-chip].is-selected");
      if (on) container = on.getAttribute("data-chip") || "";
    }}
    let page = pager
      ? Math.max(1, parseInt(pager.getAttribute("data-page") || "1", 10) || 1)
      : 1;

    function syncUrl() {{
      const params = new URLSearchParams();
      if (container) params.set("container", container);
      const raw = (search && search.value || "").trim();
      if (raw) params.set("q", raw);
      if (page > 1) params.set("page", String(page));
      const qs = params.toString();
      const nextUrl = location.pathname + (qs ? "?" + qs : "");
      if (nextUrl !== location.pathname + location.search) {{
        history.replaceState(null, "", nextUrl);
      }}
    }}

    function apply() {{
      const q = (search && search.value || "").trim().toLowerCase();
      const matched = [];
      for (const row of rows) {{
        const matchC = !container || row.getAttribute("data-container") === container;
        const blob = row.getAttribute("data-search") || "";
        const matchQ = !q || blob.indexOf(q) !== -1;
        if (matchC && matchQ) matched.push(row);
        else row.hidden = true;
      }}
      const total = matched.length;
      const pages = Math.max(1, Math.ceil(total / PAGE_SIZE) || 1);
      if (page > pages) page = pages;
      if (page < 1) page = 1;
      const start = (page - 1) * PAGE_SIZE;
      const end = Math.min(start + PAGE_SIZE, total);
      matched.forEach((row, i) => {{
        row.hidden = i < start || i >= end;
      }});
      if (shown) shown.textContent = total + " shown";
      if (pageMeta) {{
        pageMeta.textContent = total === 0
          ? "0 of 0"
          : (start + 1) + "–" + end + " of " + total;
      }}
      if (pager) pager.setAttribute("data-page", String(page));
      if (prev) prev.disabled = page <= 1 || total === 0;
      if (next) next.disabled = page >= pages || total === 0;
      syncUrl();
    }}

    if (search) search.addEventListener("input", () => {{ page = 1; apply(); }});
    if (chips) chips.addEventListener("click", (event) => {{
      const btn = event.target.closest("[data-chip]");
      if (!btn) return;
      container = btn.getAttribute("data-chip") || "";
      for (const chip of chips.querySelectorAll("[data-chip]")) {{
        const on = chip === btn;
        chip.classList.toggle("is-selected", on);
        chip.setAttribute("aria-pressed", on ? "true" : "false");
      }}
      page = 1;
      apply();
    }});
    if (prev) prev.addEventListener("click", () => {{ page -= 1; apply(); }});
    if (next) next.addEventListener("click", () => {{ page += 1; apply(); }});
"""
    return _page(
        CATALOG_TITLE,
        body,
        script,
        description=LANDING_DESCRIPTION,
        path="/catalog",
        consent=consent,
    )


def _lines(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if item]
    text = str(value).strip()
    return [text] if text else []


def _block(field: str, label: str, value: Any, *, label_class: str = "") -> str:
    lines = _lines(value)
    if not lines:
        return ""
    cls = f"block-label {label_class}".strip()
    bodies = "".join(f'<p class="block-body">{_e(line)}</p>' for line in lines)
    return (
        f'<section class="block" data-field="{_e(field)}">'
        f'<p class="{cls}">{_e(label)}</p>'
        f"{bodies}"
        f"</section>"
    )


def _example(field: str, kind: str, label: str, value: Any) -> str:
    lines = _lines(value)
    if not lines:
        return ""
    bodies = "".join(f'<p class="block-body">{_e(line)}</p>' for line in lines)
    return (
        f'<div class="example example--{kind}" data-field="{_e(field)}">'
        f'<span class="badge badge--{kind}">{_e(label)}</span>'
        f"{bodies}"
        f"</div>"
    )


def _citations_html(guideline: dict[str, Any]) -> str:
    rows = citations(guideline)
    if not rows:
        return ""
    items: list[str] = []
    for row in rows:
        source = str(row.get("source") or "").strip()
        url = str(row.get("url") or "").strip()
        if not source and not url:
            continue
        source_html = f'<p class="cite-source">{_e(source)}</p>' if source else ""
        url_html = ""
        if url:
            href = url if url.startswith("https://") else ""
            if href:
                url_html = (
                    f'<a class="cite-url" href="{_e(href)}">{_e(url)}</a>'
                )
            else:
                url_html = f'<p class="cite-url">{_e(url)}</p>'
        items.append(f'<div class="cite-row">{source_html}{url_html}</div>')
    if not items:
        return ""
    return (
        '<section class="block" data-field="citation">'
        '<p class="block-label">Citations</p>'
        f'<div class="cite-list">{"".join(items)}</div>'
        "</section>"
    )


def _tree_toggle(kind: str, title: str, open_: bool) -> str:
    caret = "▾" if open_ else "▸"
    expanded = "true" if open_ else "false"
    open_cls = " is-open" if open_ else ""
    return (
        f'<div class="tree-group{open_cls}">'
        f'<button type="button" class="tree-item tree-item--{kind}" '
        f'aria-expanded="{expanded}">'
        f'<span class="tree-caret" aria-hidden="true">{caret}</span>'
        f"<span>{_e(title)}</span></button>"
        f'<div class="tree-children">'
    )


def _tree_script() -> str:
    return r"""
    const tree = document.getElementById("catalog-tree");
    if (tree) tree.addEventListener("click", (event) => {
      const btn = event.target.closest("button.tree-item[aria-expanded]");
      if (!btn || !tree.contains(btn)) return;
      const group = btn.parentElement;
      if (!group || !group.classList.contains("tree-group")) return;
      const next = btn.getAttribute("aria-expanded") !== "true";
      btn.setAttribute("aria-expanded", next ? "true" : "false");
      group.classList.toggle("is-open", next);
      const caret = btn.querySelector(".tree-caret");
      if (caret) caret.textContent = next ? "▾" : "▸";
    });
"""


def _tree_html(
    tree: JobTree,
    index: list[dict[str, Any]],
    current: dict[str, Any],
) -> str:
    if not tree.containers:
        return ""
    current_id = str(current.get("id") or "")
    current_container = str(current.get("container") or "")
    current_card = str(current.get("card") or "")
    current_facet = str(current.get("facet") or "")

    by_facet: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
    for row in index:
        key = (
            str(row.get("container") or ""),
            str(row.get("card") or ""),
            str(row.get("facet") or ""),
        )
        by_facet.setdefault(key, []).append(row)

    parts = ['<nav class="sidebar" id="catalog-tree" aria-label="Catalog tree">']
    for container in tree.containers:
        open_c = container.id == current_container
        parts.append(_tree_toggle("container", container.title, open_c))
        for card in tree.cards:
            if card.container != container.id:
                continue
            open_card = open_c and card.id == current_card
            parts.append(_tree_toggle("card", card.title, open_card))
            for facet in card.facets:
                open_f = open_card and facet.id == current_facet
                parts.append(_tree_toggle("facet", facet.title, open_f))
                for row in by_facet.get((container.id, card.id, facet.id), []):
                    gid = str(row.get("id") or "")
                    if not gid:
                        continue
                    active = gid == current_id
                    cls = "tree-item tree-item--rule" + (" is-active" if active else "")
                    pip = (
                        '<span class="tree-pip" aria-hidden="true"></span>'
                        if active
                        else ""
                    )
                    label = _display_name(row)
                    parts.append(
                        f'<a class="{cls}" href="{_e(_href_id(gid))}">{pip}'
                        f"<span>{_e(label)}</span></a>"
                    )
                parts.append("</div></div>")
            parts.append("</div></div>")
        parts.append("</div></div>")
    parts.append("</nav>")
    return "".join(parts)


def _severity_chip(guideline: dict[str, Any]) -> str:
    """Rule-page chip only (Figma 78:26). List rows (36:22) never call this."""
    severity = guideline.get("severity")
    if not severity:
        return ""
    label = str(severity).strip()
    if not label:
        return ""
    return (
        f'<span class="severity" data-field="severity">'
        f"{_e(label[:1].upper() + label[1:])}</span>"
    )


def _eyebrow(guideline: dict[str, Any], tree: JobTree) -> str:
    category = str(guideline.get("category") or "").strip()
    segment = str(guideline.get("segment") or "").strip()
    if category and segment:
        path = f"{category} / {segment}"
    elif category:
        path = category
    else:
        path = _row_path(guideline, tree)
    chip = _severity_chip(guideline)
    path_html = f'<p class="eyebrow-path">{_e(path)}</p>' if path else ""
    if not path_html and not chip:
        return ""
    return f'<div class="eyebrow">{path_html}{chip}</div>'


def render_catalog_rule(
    catalog: Catalog,
    guideline_id: str,
    tree: JobTree | None = None,
    *,
    consent: str | None = None,
) -> str | None:
    found = get_by_id(catalog, guideline_id)
    if found is None:
        return None
    tree = tree or empty_job_tree()
    index = _full_index(catalog)
    name = _display_name(found)
    gid = str(found.get("id") or guideline_id)
    fields: list[str] = []
    fields.append(
        f'<h1 class="rule-name" data-field="name">{_e(name)}</h1>'
    )
    fields.append(
        f'<p class="rule-id" data-field="id">{_e(_display_id(gid))}</p>'
    )
    if found.get("rule"):
        fields.append(
            f'<p class="rule-text" data-field="rule">{_e(found.get("rule"))}</p>'
        )
    header = (
        '<div class="header" data-field="header">'
        + _eyebrow(found, tree)
        + "".join(fields[:3])
        + "</div>"
    )
    stack = [header]
    stack.append(_block("description", "Description", found.get("description")))
    when = _block("apply_when", "When to use", found.get("apply_when"), label_class="block-label--use")
    not_when = _block("not_when", "Not when", found.get("not_when"), label_class="block-label--not")
    if when or not_when:
        stack.append(f'<div class="when-stack">{when}{not_when}</div>')
    stack.append(_block("agent_hint", "Agent hint", found.get("agent_hint")))
    examples = _example("pass_when", "pass", "Pass", found.get("pass_when")) + _example(
        "fail_when", "fail", "Fail", found.get("fail_when")
    )
    if examples:
        stack.append(f'<div class="examples">{examples}</div>')
    stack.append(_citations_html(found))
    body = f"""
  <div class="rule-shell">
    {_tree_html(tree, index, found)}
    <main class="content">
      <a class="back" href="/catalog">← Back to Catalog</a>
      {"".join(stack)}
    </main>
  </div>
"""
    return _page(
        rule_meta_title(name),
        body,
        _tree_script(),
        description=rule_meta_description(found),
        path=f"/catalog/{gid}",
        consent=consent,
    )


def render_catalog_not_found(guideline_id: str, *, consent: str | None = None) -> str:
    body = f"""
  <main class="main">
    <a class="back" href="/catalog">← Back to Catalog</a>
    <h1>Not found</h1>
    <p class="not-found">No guideline with id “{_e(guideline_id)}”.</p>
  </main>
"""
    return _page(
        "Not found — Open UX",
        body,
        description=LANDING_DESCRIPTION,
        path=f"/catalog/{guideline_id}",
        consent=consent,
    )
