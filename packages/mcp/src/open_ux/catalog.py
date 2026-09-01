from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

from open_ux.settings import HARD_CATALOG_BYTES, SOFT_CATALOG_BYTES, Settings

EMPTY_NOTE = (
    "Catalog is empty. Cited seed rules have not landed yet "
    "(Designer UNS-44 — Forms → field labels ×3). No guideline content is invented."
)

INDEX_KEYS = ("id", "title", "jobs", "lane")
LANE_SKIP = frozenset({"schema.json", "index.json", "guidelines.json"})
BODY_KEYS = frozenset({"pass_when", "fail_when", "rule", "citation", "check", "severity"})


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
    index: list[dict[str, Any]] = field(default_factory=list)

    @property
    def empty(self) -> bool:
        return len(self.guidelines) == 0


def _validate_size(n: int) -> None:
    if n > HARD_CATALOG_BYTES:
        raise CatalogError(
            f"Catalog is {n} bytes; hard ceiling is {HARD_CATALOG_BYTES} (~256 KB)."
        )


def _lane_files(catalog_path: Path) -> list[Path]:
    if catalog_path.is_file():
        return [catalog_path]
    if not catalog_path.is_dir():
        raise CatalogError(f"Catalog path does not exist: {catalog_path}")
    files = sorted(
        p for p in catalog_path.glob("*.json") if p.name not in LANE_SKIP
    )
    if files:
        return files
    legacy = catalog_path / "guidelines.json"
    if legacy.is_file():
        return [legacy]
    raise CatalogError(f"No lane JSON files in {catalog_path}")


def _index_entry(row: dict[str, Any]) -> dict[str, Any]:
    extra = set(row) - set(INDEX_KEYS)
    if extra & BODY_KEYS:
        raise CatalogError(
            f"Index entry {row.get('id')!r} contains rule bodies: {sorted(extra & BODY_KEYS)}"
        )
    return {k: row.get(k) for k in INDEX_KEYS}


def _index_from_guidelines(guidelines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for g in guidelines:
        jobs = list(g.get("jobs") or [])
        lane = jobs[0] if jobs else (str(g.get("id") or "").split(".", 1)[0] or None)
        out.append(
            {
                "id": g["id"],
                "title": g.get("title") or g.get("rule", "")[:80],
                "jobs": jobs,
                "lane": lane,
            }
        )
    return out


def _load_on_disk_index(index_path: Path) -> list[dict[str, Any]]:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    rows = data.get("guidelines") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise CatalogError("catalog/index.json must be a list or {guidelines: [...]}.")
    return [_index_entry(row) for row in rows]


def _strip_lane(guideline: dict[str, Any]) -> dict[str, Any]:
    if "lane" not in guideline:
        return guideline
    cleaned = dict(guideline)
    cleaned.pop("lane", None)
    return cleaned


def load_catalog(settings: Settings | None = None) -> Catalog:
    settings = settings or Settings.load()
    catalog_path = settings.catalog_path
    schema = json.loads(settings.schema_path.read_text(encoding="utf-8"))
    lane_files = _lane_files(catalog_path)

    guidelines: list[dict[str, Any]] = []
    jobs: list[str] = []
    patterns: list[str] = []
    version = "0.0.0"
    size_bytes = 0

    for path in lane_files:
        raw = path.read_bytes()
        size_bytes += len(raw)
        data = json.loads(raw.decode("utf-8"))
        jsonschema.validate(instance=data, schema=schema)
        version = str(data.get("version") or version)
        for g in data.get("guidelines") or []:
            guidelines.append(_strip_lane(g))
        for job in data.get("jobs") or []:
            if job not in jobs:
                jobs.append(job)
        for pattern in data.get("patterns") or []:
            if pattern not in patterns:
                patterns.append(pattern)

    _validate_size(size_bytes)
    ids = [g.get("id") for g in guidelines]
    if len(ids) != len(set(ids)):
        raise CatalogError("Duplicate guideline ids in catalog.")

    index_path = (
        catalog_path / "index.json"
        if catalog_path.is_dir()
        else catalog_path.parent / "index.json"
    )
    if catalog_path.is_dir() and index_path.is_file():
        index = _load_on_disk_index(index_path)
        catalog_ids = [g["id"] for g in guidelines]
        index_ids = [row["id"] for row in index]
        if catalog_ids != index_ids:
            raise CatalogError("catalog/index.json ids do not match merged lane files.")
    else:
        index = _index_from_guidelines(guidelines)

    return Catalog(
        version=version,
        guidelines=guidelines,
        jobs=jobs,
        patterns=patterns,
        size_bytes=size_bytes,
        path=catalog_path,
        index=index,
    )


def catalog_over_soft_budget(catalog: Catalog) -> bool:
    return catalog.size_bytes > SOFT_CATALOG_BYTES


def list_index(
    catalog: Catalog,
    *,
    query: str | None = None,
    jobs: str | list[str] | None = None,
    lane: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    wanted_jobs = _as_job_list(jobs)
    q = (query or "").strip().lower()
    out: list[dict[str, Any]] = []
    for row in catalog.index:
        entry = {k: row.get(k) for k in INDEX_KEYS}
        row_jobs = entry.get("jobs") or []
        if wanted_jobs and not any(j in row_jobs for j in wanted_jobs):
            continue
        if lane and entry.get("lane") != lane:
            continue
        if q:
            blob = f"{entry.get('id') or ''} {entry.get('title') or ''}".lower()
            if q not in blob:
                continue
        out.append(entry)
    if limit < 1:
        raise CatalogError("limit must be >= 1")
    if offset < 0:
        raise CatalogError("offset must be >= 0")
    return out[offset : offset + limit], len(out)


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


def select_by_jobs(catalog: Catalog, jobs: str | list[str]) -> list[dict[str, Any]]:
    wanted = set(_as_job_list(jobs))
    return [g for g in catalog.guidelines if wanted.intersection(g.get("jobs") or [])]


def _as_job_list(jobs: str | list[str] | None) -> list[str]:
    if jobs is None:
        return []
    if isinstance(jobs, str):
        return [jobs] if jobs.strip() else []
    return [j for j in jobs if j]


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
