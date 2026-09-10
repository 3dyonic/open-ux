"""Where a cite lives on disk: catalog/rules/{category}/{source}/{file}.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from open_ux.catalog_error import CatalogError

# Id prefixes that are sources. `actions` and `forms` are categories, not sources.
SOURCES: dict[str, str] = {
    "ant": "Ant",
    "govuk": "GOV.UK",
    "fluent": "Fluent",
    "polar": "Polaris",
    "spectrum": "Spectrum",
    "uswds": "USWDS",
    "canada": "Canada.ca",
    "nsw": "NSW",
    "gold": "GOLD",
    "nl": "NL",
    "suomi": "Suomi.fi",
    "mui": "MUI",
    "vercel": "Vercel",
    "material": "Material",
    "tidwell": "Tidwell",
}
CATEGORY_LANES = frozenset({"actions", "forms"})
CITE_MARKERS: tuple[tuple[str, str], ...] = (
    ("ant.design", "ant"),
    ("ant design", "ant"),
    ("vercel", "vercel"),
    ("material.io", "material"),
    ("material 3", "material"),
    ("gov.uk", "govuk"),
    ("fluent 2", "fluent"),
    ("fluent", "fluent"),
    ("polaris", "polar"),
    ("shopify", "polar"),
    ("spectrum.adobe", "spectrum"),
    ("spectrum —", "spectrum"),
    ("spectrum -", "spectrum"),
    ("uswds", "uswds"),
    ("canada.ca", "canada"),
    ("nsw design", "nsw"),
    ("nsw —", "nsw"),
    ("nsw -", "nsw"),
    ("gold —", "gold"),
    ("gold -", "gold"),
    ("nldesignsystem", "nl"),
    ("nl design", "nl"),
    ("suomi.fi", "suomi"),
    ("suomi", "suomi"),
    ("mui —", "mui"),
    ("mui -", "mui"),
    ("tidwell", "tidwell"),
    ("designing interfaces", "tidwell"),
)


def category_folder(category: str) -> str:
    text = (category or "").strip().lower().replace("&", "and")
    slug = "".join(ch if ch.isalnum() else "_" for ch in text)
    while "__" in slug:
        slug = slug.replace("__", "_")
    slug = slug.strip("_")
    if not slug:
        raise CatalogError("category is required for the on-disk folder")
    return slug


def _cite_blob(guideline: dict[str, Any]) -> str:
    cites = guideline.get("citation") or []
    if not isinstance(cites, list) or not cites:
        return ""
    first = cites[0]
    if not isinstance(first, dict):
        return ""
    return f"{first.get('source') or ''} {first.get('url') or ''}"


def _source_from_cite(blob: str) -> str | None:
    text = blob.lower()
    best: tuple[int, str] | None = None
    for marker, slug in CITE_MARKERS:
        idx = text.find(marker)
        if idx < 0:
            continue
        if best is None or idx < best[0]:
            best = (idx, slug)
    return best[1] if best else None


def rule_source(guideline: dict[str, Any]) -> tuple[str, str]:
    """Return (folder slug, display label). Source, not category."""
    gid = str(guideline.get("id") or "")
    lane = gid.split(".", 1)[0]
    if lane in SOURCES and lane not in CATEGORY_LANES:
        return lane, SOURCES[lane]
    slug = _source_from_cite(_cite_blob(guideline))
    if slug and slug in SOURCES:
        return slug, SOURCES[slug]
    raise CatalogError(f"{gid}: cannot derive a source")


def rule_file_stem(gid: str) -> str:
    """Filename stem. Harvest prefix is already in the folder; id stays on the rule."""
    if "." in gid:
        return gid.split(".", 1)[1]
    return gid


def rule_relpath(guideline: dict[str, Any]) -> Path:
    slug, _label = rule_source(guideline)
    return (
        Path(category_folder(str(guideline.get("category") or "")))
        / slug
        / f"{rule_file_stem(str(guideline['id']))}.json"
    )


def rule_dest(rules_dir: Path, guideline: dict[str, Any]) -> Path:
    return rules_dir / rule_relpath(guideline)


def iter_rule_files(rules_dir: Path) -> list[Path]:
    if not rules_dir.is_dir():
        return []
    return sorted(p for p in rules_dir.rglob("*.json") if p.is_file())


def find_rule_file(rules_dir: Path, gid: str) -> Path | None:
    want = rule_file_stem(gid)
    hits = [path for path in iter_rule_files(rules_dir) if path.stem == want]
    if len(hits) > 1:
        hits = [
            path
            for path in hits
            if json.loads(path.read_text(encoding="utf-8")).get("id") == gid
        ]
    if len(hits) > 1:
        raise CatalogError(f"duplicate files for {gid}: {hits}")
    return hits[0] if hits else None
