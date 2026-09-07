"""Shared public HTML head, robots, sitemap, and favicon helpers."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

CANONICAL_ORIGIN = "https://open-ux.dev"
LANDING_TITLE = "Open UX — Cited UX rules agents audit against"
LANDING_DESCRIPTION = (
    "Stop inventing UX rules from memory. Open UX is a shared, cited catalog "
    "agents list, fetch, and audit against."
)
CATALOG_TITLE = "Catalog — Open UX"
FAVICON_HREF = "/favicon.svg"
FAVICON_PATH = Path(__file__).resolve().parent / "static" / "favicon.svg"
ROBOTS_TXT = """User-agent: *
Allow: /
Allow: /catalog
Allow: /catalog/
Disallow: /mcp
Disallow: /admin
Disallow: /invite/redeem
Disallow: /account

Sitemap: https://open-ux.dev/sitemap.xml
"""


def canonical_url(path: str) -> str:
    text = path if path.startswith("/") else f"/{path}"
    if text != "/" and text.endswith("/"):
        text = text.rstrip("/")
    return f"{CANONICAL_ORIGIN}{text}"


def _short_description(text: str, limit: int = 155) -> str:
    raw = " ".join(text.split()).strip()
    if not raw:
        return ""
    for sep in (". ", ".\n"):
        if sep in raw:
            raw = raw.split(sep, 1)[0].strip()
            break
    if raw and raw[-1] not in ".!?":
        raw += "."
    if len(raw) <= limit:
        return raw
    cut = raw[: limit - 1].rsplit(" ", 1)[0].rstrip(".,;:")
    return f"{cut}…"


def rule_meta_description(guideline: dict[str, Any]) -> str:
    for key in ("rule", "description"):
        text = _short_description(str(guideline.get(key) or ""))
        if text:
            return text
    return LANDING_DESCRIPTION


def rule_meta_title(display_name: str) -> str:
    name = (display_name or "").strip() or "Catalog"
    return f"{name} — Open UX"


def head_meta(*, title: str, description: str, path: str) -> str:
    url = canonical_url(path)
    title_e = escape(title, quote=True)
    desc_e = escape(description, quote=True)
    url_e = escape(url, quote=True)
    return (
        f"  <title>{title_e}</title>\n"
        f'  <meta name="description" content="{desc_e}">\n'
        f'  <link rel="canonical" href="{url_e}">\n'
        f'  <meta property="og:site_name" content="Open UX">\n'
        f'  <meta property="og:title" content="{title_e}">\n'
        f'  <meta property="og:description" content="{desc_e}">\n'
        f'  <meta property="og:url" content="{url_e}">\n'
        f'  <meta property="og:type" content="website">\n'
        '  <meta name="twitter:card" content="summary">\n'
        f'  <meta name="twitter:title" content="{title_e}">\n'
        f'  <meta name="twitter:description" content="{desc_e}">\n'
        f'  <link rel="icon" href="{FAVICON_HREF}" type="image/svg+xml">'
    )


def render_sitemap(guideline_ids: list[str]) -> str:
    locs = [canonical_url("/"), canonical_url("/catalog")]
    locs.extend(canonical_url(f"/catalog/{gid}") for gid in guideline_ids)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc in locs:
        lines.append(f"  <url><loc>{escape(loc)}</loc></url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"
