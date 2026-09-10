"""Robots, sitemap, icons, and display-name helpers. Python does not write pages."""

from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from open_ux.catalog_error import CatalogError
from open_ux.rule_paths import SOURCES, rule_relpath

CANONICAL_ORIGIN = "https://open-ux.dev"
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_MARK_PATH = _STATIC_DIR / "logo-mark.svg"
_FAVICON_FALLBACK = _STATIC_DIR / "favicon.svg"
FAVICON_PATH = _MARK_PATH if _MARK_PATH.is_file() else _FAVICON_FALLBACK
FAVICON_HREF = "/logo-mark.svg" if FAVICON_PATH == _MARK_PATH else "/favicon.svg"
ICON_PNG_PATH = _STATIC_DIR / "icon.png"
ICON_PNG_HREF = "/icon.png"
PIP_SVG_PATH = _STATIC_DIR / "pip.svg"
PIP_SVG_HREF = "/pip.svg"
ROBOTS_TXT = """User-agent: *
Allow: /
Allow: /catalog
Allow: /catalog/
Disallow: /mcp
Disallow: /admin
Disallow: /health
Disallow: /invite/redeem
Disallow: /invite/requested
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


_HOUSE_PAGES: tuple[str, ...] = (
    "/",
    "/catalog",
    "/invite",
    "/privacy",
    "/sources",
)
_DIST_FILES = {
    "/": "index.html",
    "/catalog": "catalog/index.html",
    "/invite": "invite/index.html",
    "/privacy": "privacy/index.html",
    "/sources": "sources/index.html",
}


def _iso_day(path: Path) -> str | None:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).date().isoformat()
    except OSError:
        return None


def sitemap_lastmods(
    *,
    catalog_path: Path,
    guidelines: list[dict[str, Any]],
    dist: Path | None = None,
) -> dict[str, str]:
    """Real file dates only. Do not invent lastmod — Google drops it when it is fake."""
    lastmods: dict[str, str] = {}
    rule_days: list[str] = []
    rules_root = catalog_path / "rules"
    for guideline in guidelines:
        gid = str(guideline.get("id") or "")
        if not gid:
            continue
        try:
            path = rules_root / rule_relpath(guideline)
        except CatalogError:
            continue
        day = _iso_day(path)
        if not day:
            continue
        lastmods[f"/catalog/{gid}"] = day
        rule_days.append(day)
    if rule_days:
        lastmods["/catalog"] = max(rule_days)
    if dist is not None:
        for path, rel in _DIST_FILES.items():
            if path == "/catalog" and path in lastmods:
                continue
            day = _iso_day(dist / rel)
            if day:
                lastmods[path] = day
    return lastmods


def _url_block(
    path: str,
    *,
    lastmod: str | None,
    images: list[tuple[str, str]] | None = None,
) -> list[str]:
    loc = canonical_url(path)
    lines = ["  <url>", f"    <loc>{escape(loc)}</loc>"]
    if lastmod:
        lines.append(f"    <lastmod>{escape(lastmod)}</lastmod>")
    for image_loc, title in images or []:
        lines.append("    <image:image>")
        lines.append(f"      <image:loc>{escape(image_loc)}</image:loc>")
        lines.append(f"      <image:title>{escape(title)}</image:title>")
        lines.append("    </image:image>")
    lines.append("  </url>")
    return lines


def render_sitemap(
    guideline_ids: list[str],
    *,
    lastmods: dict[str, str] | None = None,
) -> str:
    dates = lastmods or {}
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
        '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
    ]
    for path in _HOUSE_PAGES:
        images = None
        if path == "/":
            images = [(canonical_url(ICON_PNG_HREF), "Open UX")]
        lines.extend(
            _url_block(
                path,
                lastmod=dates.get(path),
                images=images,
            )
        )
    for gid in guideline_ids:
        path = f"/catalog/{gid}"
        lines.extend(
            _url_block(
                path,
                lastmod=dates.get(path),
            )
        )
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"
