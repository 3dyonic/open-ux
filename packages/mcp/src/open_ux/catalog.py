from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema

from open_ux.settings import HARD_CATALOG_BYTES, SOFT_CATALOG_BYTES, Settings

EMPTY_NOTE = (
    "Catalog is empty. Cited seed rules have not landed yet "
    "(Designer UNS-44 — Forms → field labels ×3). No guideline content is invented."
)


class CatalogError(ValueError):
    """Catalog failed schema or size checks."""


@dataclass(frozen=True)
class Catalog:
    version: str
    guidelines: list[dict[str, Any]]
    jobs: list[str]
    patterns: list[str]
    size_bytes: int
    path: Path

    @property
    def empty(self) -> bool:
        return len(self.guidelines) == 0


def _validate_size(raw: bytes) -> None:
    n = len(raw)
    if n > HARD_CATALOG_BYTES:
        raise CatalogError(
            f"Catalog is {n} bytes; hard ceiling is {HARD_CATALOG_BYTES} (~256 KB)."
        )


def load_catalog(settings: Settings | None = None) -> Catalog:
    settings = settings or Settings.load()
    raw = settings.catalog_path.read_bytes()
    _validate_size(raw)
    data = json.loads(raw.decode("utf-8"))
    schema = json.loads(settings.schema_path.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)
    guidelines = list(data.get("guidelines") or [])
    ids = [g.get("id") for g in guidelines]
    if len(ids) != len(set(ids)):
        raise CatalogError("Duplicate guideline ids in catalog.")
    return Catalog(
        version=str(data["version"]),
        guidelines=guidelines,
        jobs=list(data.get("jobs") or []),
        patterns=list(data.get("patterns") or []),
        size_bytes=len(raw),
        path=settings.catalog_path,
    )


def catalog_over_soft_budget(catalog: Catalog) -> bool:
    return catalog.size_bytes > SOFT_CATALOG_BYTES


def list_index(
    catalog: Catalog,
    *,
    category: str | None = None,
    segment: str | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for g in catalog.guidelines:
        if category and g.get("category") != category:
            continue
        if segment and g.get("segment") != segment:
            continue
        out.append(
            {
                "id": g["id"],
                "title": g.get("title") or g.get("rule", "")[:80],
                "category": g.get("category"),
                "segment": g.get("segment"),
                "severity": g.get("severity"),
            }
        )
    return out


def get_by_id(catalog: Catalog, guideline_id: str) -> dict[str, Any] | None:
    for g in catalog.guidelines:
        if g.get("id") == guideline_id:
            return g
    return None


def select(catalog: Catalog, guideline_ids: list[str] | None) -> list[dict[str, Any]]:
    if not guideline_ids:
        return list(catalog.guidelines)
    found: list[dict[str, Any]] = []
    for gid in guideline_ids:
        item = get_by_id(catalog, gid)
        if item is not None:
            found.append(item)
    return found


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
