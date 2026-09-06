from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

from open_ux.jobs import (
    CARD_IDS,
    CONTAINER_IDS,
    NeedScope,
    JobTree,
    load_job_tree,
    resolve_need_scope,
)
from open_ux.settings import HARD_CATALOG_BYTES, SOFT_CATALOG_BYTES, Settings

EMPTY_NOTE = (
    "Catalog is empty. Cited seed rules have not landed yet "
    "(Designer UNS-44 — Forms → field labels ×3). No guideline content is invented."
)

INDEX_KEYS = ("id", "title", "name", "jobs", "lane", "container", "card", "facet", "leaf")
ROOT_SKIP = frozenset({"schema.json", "index.json", "guidelines.json", "jobs.json"})
BODY_KEYS = frozenset({"pass_when", "fail_when", "rule", "citation", "check", "severity"})
AGENT_KEYS = ("overview", "apply_when", "not_when", "agent_hint", "description")
CATALOG_VERSION = "0.3.0"


class CatalogError(ValueError):
    """Catalog failed schema, placement, or size checks."""


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
            f"Catalog is {n} bytes; hard ceiling is {HARD_CATALOG_BYTES} (~768 KB)."
        )


def _rule_files(catalog_path: Path) -> list[Path]:
    if catalog_path.is_file():
        return [catalog_path]
    if not catalog_path.is_dir():
        raise CatalogError(f"Catalog path does not exist: {catalog_path}")
    rules_dir = catalog_path / "rules"
    if rules_dir.is_dir():
        return sorted(p for p in rules_dir.glob("*.json") if p.is_file())
    legacy = catalog_path / "guidelines.json"
    if legacy.is_file():
        return [legacy]
    return []


def _index_entry(row: dict[str, Any]) -> dict[str, Any]:
    extra = set(row) - set(INDEX_KEYS)
    if extra & BODY_KEYS:
        raise CatalogError(
            f"Index entry {row.get('id')!r} contains rule bodies: {sorted(extra & BODY_KEYS)}"
        )
    out = {k: row.get(k) for k in INDEX_KEYS if k in row or k != "leaf"}
    if row.get("leaf"):
        out["leaf"] = row["leaf"]
    elif "leaf" in out:
        out.pop("leaf", None)
    return out


def _index_from_guidelines(guidelines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for g in guidelines:
        leaf = g.get("leaf")
        jobs = [leaf] if leaf else list(g.get("jobs") or [])
        lane = str(g.get("id") or "").split(".", 1)[0] or None
        row: dict[str, Any] = {
            "id": g["id"],
            "title": g.get("title") or g.get("rule", "")[:80],
            "name": g.get("name") or g.get("title") or g.get("rule", "")[:80],
            "jobs": jobs,
            "lane": lane,
            "container": g.get("container"),
            "card": g.get("card"),
            "facet": g.get("facet"),
        }
        if leaf:
            row["leaf"] = leaf
        out.append(row)
    return out


def _load_on_disk_index(index_path: Path) -> tuple[str, list[dict[str, Any]]]:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        version = str(data.get("version") or CATALOG_VERSION)
        rows = data.get("guidelines")
    else:
        version = CATALOG_VERSION
        rows = data
    if not isinstance(rows, list):
        raise CatalogError("catalog/index.json must be a list or {guidelines: [...]}.")
    return version, [_index_entry(row) for row in rows]


def _load_one(path: Path, schema: dict[str, Any]) -> dict[str, Any]:
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    if path.name == "guidelines.json" or (
        isinstance(data, dict) and "guidelines" in data and "id" not in data
    ):
        jsonschema.validate(instance=data, schema=_empty_wrapper_schema())
        rows = data.get("guidelines") or []
        if rows:
            raise CatalogError("Legacy guidelines.json must be empty; use catalog/rules/{id}.json.")
        return {"_empty_wrapper": True, "_bytes": len(raw)}
    jsonschema.validate(instance=data, schema=schema)
    if path.stem != data.get("id"):
        raise CatalogError(f"Filename {path.name!r} does not match id {data.get('id')!r}.")
    data["_bytes"] = len(raw)
    return data


def _empty_wrapper_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["version", "guidelines"],
        "properties": {
            "version": {"type": "string"},
            "guidelines": {"type": "array", "maxItems": 0},
            "jobs": {"type": "array"},
            "patterns": {"type": "array"},
        },
    }


def _tree_homes(tree: JobTree) -> tuple[dict[str, dict[str, Any]], set[str], dict[str, str]]:
    facet: dict[str, dict[str, Any]] = {}
    cluster_ids: set[str] = set()
    pointer_files: dict[str, str] = {}
    for card in tree.cards:
        for item in card.facets:
            facet[item.id] = {
                "container": card.container,
                "card": card.id,
                "has_leaves": bool(item.leaves),
                "leaf_ids": {leaf.id for leaf in item.leaves},
            }
            if not item.leaves:
                for gid in item.guideline_ids:
                    cluster_ids.add(gid)
                    pointer_files[gid] = item.id
            for leaf in item.leaves:
                for gid in leaf.guideline_ids:
                    pointer_files[gid] = leaf.id
    return facet, cluster_ids, pointer_files


def validate_placement(guidelines: list[dict[str, Any]], tree: JobTree) -> None:
    facet, cluster_ids, pointer_files = _tree_homes(tree)
    seen: set[str] = set()
    for g in guidelines:
        gid = str(g.get("id") or "")
        if gid in seen:
            raise CatalogError(f"Duplicate guideline id {gid!r}.")
        seen.add(gid)
        container = g.get("container")
        card = g.get("card")
        facet_id = g.get("facet")
        leaf = g.get("leaf")
        if container not in CONTAINER_IDS:
            raise CatalogError(f"{gid}: container {container!r} is not locked.")
        if card not in CARD_IDS:
            raise CatalogError(f"{gid}: card {card!r} is not locked.")
        home = facet.get(str(facet_id or ""))
        if home is None:
            raise CatalogError(f"{gid}: facet {facet_id!r} is not in jobs.json.")
        if home["container"] != container or home["card"] != card:
            raise CatalogError(f"{gid}: placement disagrees with jobs.json.")
        if home["has_leaves"]:
            if leaf not in home["leaf_ids"]:
                raise CatalogError(
                    f"{gid}: leaf {leaf!r} is required and must sit on facet {facet_id!r}."
                )
        elif leaf:
            raise CatalogError(f"{gid}: cluster facet {facet_id!r} cannot have a leaf.")
        elif gid not in cluster_ids:
            raise CatalogError(
                f"{gid}: cluster home must appear in facet guideline_ids[]."
            )
        agent = [key for key in AGENT_KEYS if g.get(key)]
        waived = bool(g.get("waive_reason"))
        if agent and len(agent) != len(AGENT_KEYS):
            raise CatalogError(f"{gid}: agent-facing fields must be complete or waived.")
        if not agent and not waived:
            raise CatalogError(f"{gid}: missing agent-facing fields and waive_reason.")
        if agent and waived:
            raise CatalogError(f"{gid}: waive_reason is only for rows without agent fields.")
    for gid, target in pointer_files.items():
        if gid not in seen:
            raise CatalogError(f"jobs.json points at missing rule file {gid!r} ({target}).")


def load_catalog(settings: Settings | None = None) -> Catalog:
    settings = settings or Settings.load()
    catalog_path = settings.catalog_path
    schema = json.loads(settings.schema_path.read_text(encoding="utf-8"))
    files = _rule_files(catalog_path)

    guidelines: list[dict[str, Any]] = []
    jobs: list[str] = []
    patterns: list[str] = []
    version = CATALOG_VERSION
    size_bytes = 0

    for path in files:
        loaded = _load_one(path, schema)
        size_bytes += int(loaded.pop("_bytes", 0))
        if loaded.pop("_empty_wrapper", False):
            continue
        guidelines.append(loaded)
        for job in loaded.get("jobs") or []:
            if job not in jobs:
                jobs.append(job)
        for pattern in loaded.get("patterns") or []:
            if pattern not in patterns:
                patterns.append(pattern)

    _validate_size(size_bytes)
    ids = [g.get("id") for g in guidelines]
    if len(ids) != len(set(ids)):
        raise CatalogError("Duplicate guideline ids in catalog.")

    if guidelines:
        tree = load_job_tree(settings)
        if not tree.empty:
            validate_placement(guidelines, tree)

    index_path = (
        catalog_path / "index.json"
        if catalog_path.is_dir()
        else catalog_path.parent / "index.json"
    )
    if catalog_path.is_dir() and index_path.is_file() and guidelines:
        version, index = _load_on_disk_index(index_path)
        catalog_ids = [g["id"] for g in guidelines]
        index_ids = [row["id"] for row in index]
        if sorted(catalog_ids) != sorted(index_ids):
            raise CatalogError("catalog/index.json ids do not match catalog/rules.")
        by_id = {g["id"]: g for g in guidelines}
        guidelines = [by_id[gid] for gid in index_ids]
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
    scope = resolve_need_scope(jobs)
    if jobs is not None and scope is not None and scope.empty:
        return [], 0
    q = (query or "").strip().lower()
    out: list[dict[str, Any]] = []
    for row in catalog.index:
        entry = {k: row.get(k) for k in INDEX_KEYS if k in row}
        if scope is not None and not _in_scope(
            entry.get("id"),
            entry.get("jobs") or [],
            scope,
            leaf=entry.get("leaf"),
        ):
            continue
        if lane and entry.get("lane") != lane:
            continue
        if q:
            blob = (
                f"{entry.get('id') or ''} {entry.get('title') or ''} "
                f"{entry.get('name') or ''}"
            ).lower()
            if q not in blob:
                continue
        out.append(entry)
    if limit < 1:
        raise CatalogError("limit must be >= 1")
    if offset < 0:
        raise CatalogError("offset must be >= 0")
    return out[offset : offset + limit], len(out)


def citations(guideline: dict[str, Any]) -> list[dict[str, Any]]:
    """Return citation as a list of {source, url}. Catalog stores an array."""
    raw = guideline.get("citation")
    if raw is None:
        return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        return [raw]
    return []


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


def _in_scope(
    guideline_id: Any,
    jobs: list[Any],
    scope: NeedScope,
    *,
    leaf: Any = None,
) -> bool:
    if scope.guideline_ids and guideline_id in scope.guideline_ids:
        return True
    tags = set(scope.tags)
    if tags and leaf in tags:
        return True
    if tags and any(tag in jobs for tag in tags):
        return True
    return False


def select_by_jobs(catalog: Catalog, jobs: str | list[str]) -> list[dict[str, Any]]:
    scope = resolve_need_scope(jobs)
    if scope is None or scope.empty:
        return []
    return [
        g
        for g in catalog.guidelines
        if _in_scope(g.get("id"), g.get("jobs") or [], scope, leaf=g.get("leaf"))
    ]


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
