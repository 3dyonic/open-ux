"""Public `/health` HTML: F3 Health frame. JSON payload is the agent contract."""

from __future__ import annotations

from html import escape
from typing import Any

from starlette.requests import Request

from open_ux.catalog import Catalog
from open_ux.public_html import (
    FAVICON_HREF,
    MARK_CSS,
    NAV_BRAND_HTML,
    NAV_GITHUB_HTML,
    OSS_FOOTER_CSS,
    PAGE_SHELL_CSS,
    head_meta,
    public_oss_footer,
)

HEALTH_TITLE = "Health — Open UX"
HEALTH_DESCRIPTION = (
    "Live status of the Open UX hosted service and catalog. "
    "Same facts as GET /health JSON."
)

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
      --success-bg: #DAFBE1;
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
      font-size: 13px;
      font-weight: 500;
      color: var(--muted);
    }
    .nav-link:hover,
    .nav-link:focus { color: var(--ink); }
    .main {
      display: flex;
      flex-direction: column;
      gap: 28px;
      width: 100%;
      padding: 40px 48px 48px;
    }
    .kicker {
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
      font-family: var(--mono);
      font-size: 12px;
      font-weight: 500;
      color: var(--muted);
    }
    .pip {
      display: inline-block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--pip);
      flex-shrink: 0;
    }
    .status-banner {
      display: flex;
      align-items: center;
      gap: 12px;
      width: 100%;
      padding: 14px 16px;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: var(--radius);
    }
    .status-pip {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: var(--success);
      flex-shrink: 0;
    }
    .status-banner.is-degraded .status-pip { background: var(--danger); }
    .status-copy { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
    .status-title {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--ink);
    }
    .status-map {
      margin: 0;
      font-family: var(--mono);
      font-size: 12px;
      color: var(--muted);
    }
    .banner-spacer { flex: 1; }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border: 1px solid var(--success);
      border-radius: var(--radius);
      background: var(--success-bg);
      color: var(--success);
      font-family: var(--mono);
      font-size: 12px;
      font-weight: 500;
      white-space: nowrap;
    }
    .chip .pip {
      width: 7px;
      height: 7px;
      background: var(--success);
    }
    .chip--degraded {
      border-color: var(--danger);
      background: var(--danger-bg);
      color: var(--danger);
    }
    .chip--degraded .pip { background: var(--danger); }
    .header {
      display: flex;
      flex-wrap: wrap;
      align-items: flex-start;
      gap: 48px;
      width: 100%;
    }
    .header-copy {
      display: flex;
      flex-direction: column;
      gap: 12px;
      flex: 1 1 280px;
      min-width: 0;
    }
    h1 {
      margin: 0;
      font-size: 28px;
      font-weight: 600;
      line-height: normal;
      color: var(--ink);
    }
    .lede {
      margin: 0;
      font-size: 16px;
      color: var(--muted);
    }
    .browse {
      font-size: 14px;
      font-weight: 500;
      color: var(--pip);
    }
    .browse:hover,
    .browse:focus { text-decoration: underline; }
    .components { display: flex; flex-direction: column; gap: 12px; width: 100%; }
    .components-title {
      margin: 0;
      font-size: 14px;
      font-weight: 600;
      color: var(--ink);
    }
    .component-list {
      width: 100%;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      overflow: hidden;
    }
    .component-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      width: 100%;
      padding: 16px;
      border-bottom: 1px solid var(--line);
    }
    .component-row:last-child { border-bottom: none; }
    .row-left { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
    .component-name {
      margin: 0;
      font-size: 16px;
      font-weight: 500;
      color: var(--ink);
    }
    .component-meta {
      margin: 0;
      font-family: var(--mono);
      font-size: 13px;
      color: var(--muted);
    }
    .about {
      display: flex;
      flex-direction: column;
      gap: 8px;
      width: 100%;
      padding: 14px 16px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: var(--paper);
    }
    .about-title {
      margin: 0;
      font-size: 13px;
      font-weight: 600;
      color: var(--ink);
    }
    .about-body {
      margin: 0;
      font-size: 14px;
      color: var(--muted);
    }
    .browse-row {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      font-size: 14px;
    }
    .browse-note { margin: 0; color: var(--muted); }
    @media (max-width: 720px) {
      .nav, .main, .footer { padding-left: 20px; padding-right: 20px; }
    }
""" + MARK_CSS + OSS_FOOTER_CSS + PAGE_SHELL_CSS


def health_payload(catalog: Catalog, *, hosted: bool) -> dict[str, Any]:
    return {
        "ok": True,
        "name": "Open UX",
        "hosted": hosted,
        "catalog": {
            "status": "empty" if catalog.empty else "ok",
            "guideline_count": len(catalog.guidelines),
            "version": catalog.version,
        },
    }


def wants_health_html(request: Request) -> bool:
    fmt = (request.query_params.get("format") or "").strip().lower()
    if fmt == "json":
        return False
    accept = request.headers.get("accept") or ""
    for part in accept.split(","):
        media = part.split(";", 1)[0].strip().lower()
        if media == "text/html":
            return True
    return False


def _chip(label: str, *, degraded: bool = False) -> str:
    cls = "chip chip--degraded" if degraded else "chip"
    return (
        f'<span class="{cls}">'
        '<span class="pip" aria-hidden="true"></span>'
        f"{escape(label)}</span>"
    )


def render_health_page(payload: dict[str, Any]) -> str:
    catalog = payload["catalog"]
    systems_ok = bool(payload.get("ok")) and catalog.get("status") == "ok"
    hosted = bool(payload.get("hosted"))
    if systems_ok:
        status_title = "Success: host and catalog are up"
        status_body = "The hosted service is running. The catalog is loaded."
        chip = _chip("Operational")
    else:
        status_title = "Error: catalog is not loaded"
        status_body = (
            "The host is up. The catalog has no cited rules yet. "
            "Browse the catalog when rules land."
        )
        chip = _chip("Not loaded", degraded=True)
    banner_cls = "status-banner" if systems_ok else "status-banner is-degraded"
    count = catalog.get("guideline_count")
    version = catalog.get("version")
    hosted_line = (
        "Running on the hosted service."
        if hosted
        else "Running locally, not on the hosted service."
    )
    catalog_line = (
        f"{count} cited rules, version {version}"
        if systems_ok
        else "No cited rules loaded yet."
    )
    hosted_chip = _chip("Operational") if hosted else _chip("Local", degraded=True)
    catalog_chip = (
        _chip("Operational") if systems_ok else _chip("Not loaded", degraded=True)
    )

    main = f"""
    <p class="kicker"><span class="pip" aria-hidden="true"></span>Status</p>
    <div class="{banner_cls}" role="region" aria-label="Status">
      <span class="status-pip" aria-hidden="true"></span>
      <div class="status-copy">
        <p class="status-title">{escape(status_title)}</p>
        <p class="status-map">{escape(status_body)}</p>
      </div>
      <span class="banner-spacer"></span>
      {chip}
    </div>
    <div class="header">
      <div class="header-copy">
        <h1>Health</h1>
        <p class="lede">Whether the hosted service is up, and whether the catalog is loaded.</p>
        <a class="browse" href="/catalog">Browse catalog →</a>
      </div>
    </div>
    <section class="components">
      <h2 class="components-title">Components</h2>
      <div class="component-list">
        <div class="component-row">
          <div class="row-left">
            <p class="component-name">API</p>
            <p class="component-meta">The service answers requests.</p>
          </div>
          {_chip("Operational")}
        </div>
        <div class="component-row">
          <div class="row-left">
            <p class="component-name">Hosted service</p>
            <p class="component-meta">{escape(hosted_line)}</p>
          </div>
          {hosted_chip}
        </div>
        <div class="component-row">
          <div class="row-left">
            <p class="component-name">Catalog</p>
            <p class="component-meta">{escape(str(catalog_line))}</p>
          </div>
          {catalog_chip}
        </div>
      </div>
    </section>
    <section class="about">
      <h2 class="about-title">About</h2>
      <p class="about-body">This page shows whether Open UX is up. Agents that ask for JSON get the same facts.</p>
    </section>
    <p class="browse-row">
      <span class="browse-note">Need the rules?</span>
      <a class="browse" href="/catalog">Browse catalog →</a>
    </p>
"""

    return (
        """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
"""
        + head_meta(
            title=HEALTH_TITLE,
            description=HEALTH_DESCRIPTION,
            path="/health",
        )
        + f"""
  <link rel="icon" href="{FAVICON_HREF}" type="image/svg+xml">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
"""
        + _CSS
        + """
  </style>
</head>
<body>
  <header class="nav">
    """
        + NAV_BRAND_HTML
        + """
    <div class="nav-actions">
      <a class="nav-link" href="/catalog">Catalog</a>
      """
        + NAV_GITHUB_HTML
        + """
    </div>
  </header>
  <main class="main">
"""
        + main
        + """
  </main>
"""
        + public_oss_footer()
        + """
</body>
</html>
"""
    )
