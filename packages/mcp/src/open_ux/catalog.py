from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypedDict

from jsonschema.validators import validator_for

from open_ux.bm25 import guideline_blob, rank_blobs
from open_ux.catalog_error import CatalogError
from open_ux.components import load_components, validate_component_refs
from open_ux.jobs import (
    CARD_IDS,
    CONTAINER_IDS,
    NeedScope,
    JobTree,
    load_job_tree,
    resolve_need_scope,
)
from open_ux.manifest import manifest_ids
from open_ux.rule_paths import iter_rule_files, rule_file_stem, rule_relpath
from open_ux.settings import HARD_CATALOG_BYTES, Settings

EMPTY_NOTE = (
    "Catalog is empty. Cited seed rules have not landed yet "
    "(Designer UNS-44 — Forms → field labels ×3). No guideline content is invented."
)

INDEX_KEYS = ("id", "title", "name", "jobs", "lane", "container", "card", "facet", "leaf")
BODY_KEYS = frozenset({"pass_when", "fail_when", "rule", "citation", "check", "severity"})
AGENT_KEYS = ("overview", "apply_when", "not_when", "agent_hint", "description")

GATE_LEAVES = frozenset(
    {
        "choose_control_for_choice",
        "pick_primary_action",
        "pick_modal_only_when_blocking",
        "disclose_instead_of_dump",
    }
)

_VENDOR_PATTERN = re.compile(
    r"\b(?:"
    r"Ant(?:\s+Design)?|MUI|Material(?:\s+UI)?|GOV\.?UK|Fluent|Polaris|Suomi(?:\.fi)?|"
    r"USWDS|NSW|Canada|Vercel|Spectrum|Gold(?:\s+Design)?|Tidwell|Lightning|NN/g|Polar"
    r")\b",
    re.IGNORECASE,
)
_ON_SURFACES_PATTERN = re.compile(r"\bon\s+\w+\s+surfaces\b", re.IGNORECASE)
_TASK_FRAME_PATTERN = re.compile(
    r"^(Choosing|Collecting|Ordering|Placing|Composing|Labeling|Adding|Naming|Arranging|"
    r"List-page|Scheduling|Hover|Input)\b",
    re.IGNORECASE,
)


class ApplyWhenFitViolation(TypedDict):
    id: str
    leaf: str
    apply_when: str
    reason: str


def _squish_fit(text: str) -> str:
    return " ".join((text or "").split()).casefold()


def _title_phrase(guideline: dict[str, Any]) -> str:
    name = str(guideline.get("name") or "")
    if "—" in name:
        name = name.split("—", 1)[0]
    elif " - " in name:
        name = name.split(" - ", 1)[0]
    title = str(guideline.get("title") or "")
    return name.strip() or title.replace("-", " ").strip()


def _apply_when_fit_reasons(guideline: dict[str, Any]) -> list[str]:
    apply_when = str(guideline.get("apply_when") or "").strip()
    if not apply_when:
        return ["apply_when is empty"]
    overview = str(guideline.get("overview") or "").strip()
    reasons: list[str] = []
    task_framed = bool(_TASK_FRAME_PATTERN.match(apply_when))
    if not task_framed and (
        _VENDOR_PATTERN.search(apply_when) or _ON_SURFACES_PATTERN.search(apply_when)
    ):
        reasons.append("apply_when names a house or surface")
    if _squish_fit(apply_when) == _squish_fit(overview):
        reasons.append("apply_when equals overview")
    title_phrase = _title_phrase(guideline)
    if title_phrase and _squish_fit(apply_when) == _squish_fit(title_phrase):
        reasons.append("apply_when only restates the cite title")
    return reasons


def validate_apply_when_fit(
    guidelines: list[dict[str, Any]],
) -> list[ApplyWhenFitViolation]:
    """Gate-Leaf apply_when sniff test. Report-only unless the caller exits non-zero."""
    out: list[ApplyWhenFitViolation] = []
    for guideline in guidelines:
        leaf = str(guideline.get("leaf") or "")
        if leaf not in GATE_LEAVES:
            continue
        apply_when = str(guideline.get("apply_when") or "").strip()
        for reason in _apply_when_fit_reasons(guideline):
            out.append(
                {
                    "id": str(guideline.get("id") or ""),
                    "leaf": leaf,
                    "apply_when": apply_when,
                    "reason": reason,
                }
            )
    out.sort(key=lambda row: (row["id"], row["reason"]))
    return out


def _rules_root(path: Path) -> Path | None:
    for parent in path.parents:
        if parent.name == "rules":
            return parent
    return None


def _check_rule_path(path: Path, data: dict[str, Any]) -> None:
    rules_root = _rules_root(path)
    if rules_root is None or not data.get("category"):
        return
    expected = rule_relpath(data)
    rel = path.relative_to(rules_root)
    if rel != expected:
        raise CatalogError(
            f"{data['id']}: path catalog/rules/{rel.as_posix()} "
            f"must be catalog/rules/{expected.as_posix()}"
        )


@dataclass(frozen=True)
class Catalog:
    guidelines: list[dict[str, Any]]
    size_bytes: int
    path: Path
    index: list[dict[str, Any]] = field(default_factory=list)
    by_id: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def empty(self) -> bool:
        return len(self.guidelines) == 0


def catalog_status(catalog: Catalog) -> dict[str, Any]:
    return {
        "status": "empty" if catalog.empty else "ok",
        "guideline_count": len(catalog.guidelines),
    }


def _validate_size(n: int) -> None:
    if n > HARD_CATALOG_BYTES:
        raise CatalogError(
            f"Catalog is {n} bytes; hard ceiling is {HARD_CATALOG_BYTES} (~768 KB)."
        )


def _rule_files(catalog_path: Path) -> list[Path]:
    if not catalog_path.is_dir():
        raise CatalogError(f"Catalog path does not exist: {catalog_path}")
    rules_dir = catalog_path / "rules"
    if not rules_dir.is_dir():
        return []
    return iter_rule_files(rules_dir)


def _index_entry(row: dict[str, Any]) -> dict[str, Any]:
    extra = set(row) - set(INDEX_KEYS)
    if extra & BODY_KEYS:
        raise CatalogError(
            f"Index entry {row.get('id')!r} contains rule bodies: {sorted(extra & BODY_KEYS)}"
        )
    out = {k: row[k] for k in INDEX_KEYS if k in row}
    if not out.get("leaf"):
        out.pop("leaf", None)
    return out


def _load_on_disk_index(index_path: Path) -> list[dict[str, Any]]:
    data = json.loads(index_path.read_text(encoding="utf-8"))
    rows = data.get("guidelines") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise CatalogError("catalog/index.json must be {guidelines: [...]}.")
    return [_index_entry(row) for row in rows]


def _load_one(path: Path, validator: Any) -> tuple[dict[str, Any], int]:
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    validator.validate(data)
    gid = str(data.get("id") or "")
    if path.stem not in {gid, rule_file_stem(gid)}:
        raise CatalogError(f"Filename {path.name!r} does not match id {gid!r}.")
    _check_rule_path(path, data)
    return data, len(raw)


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
    Validator = validator_for(schema)
    validator = Validator(schema)
    files = _rule_files(catalog_path)

    guidelines: list[dict[str, Any]] = []
    seen: set[str] = set()
    size_bytes = 0

    for path in files:
        loaded, nbytes = _load_one(path, validator)
        size_bytes += nbytes
        gid = loaded["id"]
        if gid in seen:
            raise CatalogError("Duplicate guideline ids in catalog.")
        seen.add(gid)
        guidelines.append(loaded)

    _validate_size(size_bytes)

    if guidelines:
        tree = load_job_tree(settings)
        registry = load_components(settings)
        if not tree.empty:
            validate_placement(guidelines, tree)
            validate_component_refs(tree, guidelines, registry)

    lookup = {g["id"]: g for g in guidelines}
    if not guidelines:
        index: list[dict[str, Any]] = []
    else:
        index_path = catalog_path / "index.json"
        if not index_path.is_file():
            raise CatalogError("catalog/index.json is required.")
        index = _load_on_disk_index(index_path)
        index_ids = [row["id"] for row in index]
        if sorted(lookup) != sorted(index_ids):
            raise CatalogError("catalog/index.json ids do not match catalog/rules.")
        guidelines = [lookup[gid] for gid in index_ids]
        manifest_path = catalog_path / "manifest.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if sorted(manifest_ids(manifest)) != sorted(lookup):
                raise CatalogError("catalog/manifest.json ids do not match catalog/rules.")

    return Catalog(
        guidelines=guidelines,
        size_bytes=size_bytes,
        path=catalog_path,
        index=index,
        by_id=lookup,
    )


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
    q = (query or "").strip()
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
        out.append(entry)
    if q:
        bodies = {g.get("id"): g for g in catalog.guidelines}
        blobs = [guideline_blob(bodies.get(entry.get("id")) or entry) for entry in out]
        order, matched = rank_blobs(q, blobs)
        if matched:
            out = [out[i] for i in order]
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
    return catalog.by_id.get(guideline_id)


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
