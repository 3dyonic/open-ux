"""Robots, sitemap, favicon, and display-name helpers. Python does not write pages."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from open_ux.rule_paths import SOURCES

CANONICAL_ORIGIN = "https://open-ux.dev"
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_MARK_PATH = _STATIC_DIR / "logo-mark.svg"
_FAVICON_FALLBACK = _STATIC_DIR / "favicon.svg"
FAVICON_PATH = _MARK_PATH if _MARK_PATH.is_file() else _FAVICON_FALLBACK
FAVICON_HREF = "/logo-mark.svg" if FAVICON_PATH == _MARK_PATH else "/favicon.svg"
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

_HOUSE_SUFFIXES = tuple(
    sorted((f" — {label}" for label in SOURCES.values()), key=len, reverse=True)
)


def canonical_url(path: str) -> str:
    text = path if path.startswith("/") else f"/{path}"
    if text != "/" and text.endswith("/"):
        text = text.rstrip("/")
    return f"{CANONICAL_ORIGIN}{text}"


def guideline_display_name(guideline: dict[str, Any]) -> str:
    raw = str(
        guideline.get("name") or guideline.get("title") or guideline.get("id") or ""
    ).strip()
    for suffix in _HOUSE_SUFFIXES:
        if raw.endswith(suffix):
            return raw[: -len(suffix)].rstrip()
    return raw


def guideline_display_id(guideline_id: str) -> str:
    text = (guideline_id or "").strip()
    if "." not in text:
        return text
    lane, rest = text.split(".", 1)
    if rest and lane in SOURCES:
        return rest
    return text


def render_sitemap(guideline_ids: list[str]) -> str:
    locs = [
        canonical_url("/"),
        canonical_url("/catalog"),
        canonical_url("/privacy"),
        canonical_url("/sources"),
    ]
    locs.extend(canonical_url(f"/catalog/{gid}") for gid in guideline_ids)
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for loc in locs:
        lines.append(f"  <url><loc>{escape(loc)}</loc></url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"
