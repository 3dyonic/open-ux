from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from open_ux.catalog_error import CatalogError
from open_ux.jobs import JobTree, JobTreeError
from open_ux.settings import Settings

EMPTY_COMPONENTS_NOTE = "No component records in the catalog."

_RECORD_KEYS = ("id", "title", "overview", "apply_when", "not_when", "keywords")


@dataclass(frozen=True)
class ComponentRef:
    id: str
    title: str
    path: str


@dataclass(frozen=True)
class ComponentRegistry:
    refs: tuple[ComponentRef, ...]
    records: dict[str, dict[str, Any]]

    @property
    def ids(self) -> frozenset[str]:
        return frozenset(ref.id for ref in self.refs)


def _registry_path(catalog_path: Path) -> Path:
    return catalog_path / "components.json"


def _parse_ref(raw: Any) -> ComponentRef:
    if not isinstance(raw, dict):
        raise CatalogError("Each component registry row must be an object.")
    cid = raw.get("id")
    title = raw.get("title")
    path = raw.get("path")
    if not isinstance(cid, str) or not cid.strip():
        raise CatalogError("Component registry rows need a non-empty id.")
    if not isinstance(title, str) or not title.strip():
        raise CatalogError(f"Component {cid!r} needs a non-empty title.")
    if not isinstance(path, str) or not path.strip():
        raise CatalogError(f"Component {cid!r} needs a non-empty path.")
    extra = set(raw) - {"id", "title", "path"}
    if extra:
        raise CatalogError(
            f"Component registry row {cid!r} has unknown keys: {sorted(extra)}."
        )
    return ComponentRef(id=cid, title=title, path=path)


def _load_record(path: Path, expected_id: str) -> dict[str, Any]:
    if not path.is_file():
        raise CatalogError(f"Component record missing: {path.as_posix()}.")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CatalogError(f"Component record {path.name!r} must be an object.")
    rid = data.get("id")
    if rid != expected_id:
        raise CatalogError(
            f"Component record {path.as_posix()} id {rid!r} "
            f"does not match registry id {expected_id!r}."
        )
    missing = [key for key in _RECORD_KEYS if key not in data]
    if missing:
        raise CatalogError(
            f"Component record {expected_id!r} missing keys: {missing}."
        )
    keywords = data.get("keywords")
    if not isinstance(keywords, list) or not keywords:
        raise CatalogError(f"Component record {expected_id!r} keywords must be a list.")
    if not all(isinstance(item, str) and item for item in keywords):
        raise CatalogError(
            f"Component record {expected_id!r} keywords must be non-empty strings."
        )
    return data


def load_components(settings: Settings | None = None) -> ComponentRegistry:
    settings = settings or Settings.load()
    registry_file = _registry_path(settings.catalog_path)
    if not registry_file.is_file():
        return ComponentRegistry(refs=(), records={})
    data = json.loads(registry_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CatalogError("catalog/components.json must be an object.")
    rows = data.get("components")
    if not isinstance(rows, list):
        raise CatalogError("catalog/components.json must be {components: [...]}.")
    refs: list[ComponentRef] = []
    records: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    catalog_path = settings.catalog_path
    for raw in rows:
        ref = _parse_ref(raw)
        if ref.id in seen:
            raise CatalogError(f"Duplicate component id {ref.id!r} in components.json.")
        seen.add(ref.id)
        record_path = catalog_path / ref.path
        records[ref.id] = _load_record(record_path, ref.id)
        refs.append(ref)
    return ComponentRegistry(refs=tuple(refs), records=records)


def validate_component_refs(
    tree: JobTree,
    guidelines: list[dict[str, Any]],
    registry: ComponentRegistry,
) -> None:
    known = registry.ids
    for card in tree.cards:
        for cid in card.component:
            if cid not in known:
                raise JobTreeError(
                    f"Card {card.id!r} component {cid!r} is not in components.json."
                )
    for guideline in guidelines:
        gid = str(guideline.get("id") or "")
        raw = guideline.get("component")
        if raw is None:
            continue
        if not isinstance(raw, list):
            raise CatalogError(f"{gid}: component must be an array.")
        for cid in raw:
            if not isinstance(cid, str) or not cid:
                raise CatalogError(f"{gid}: component entries must be non-empty strings.")
            if cid not in known:
                raise CatalogError(
                    f"{gid}: component {cid!r} is not in components.json."
                )


def _terms(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if item]
    return []


def _placement_orders(tree: JobTree) -> tuple[
    dict[str, int],
    dict[tuple[str, str], int],
    dict[tuple[str, str, str], int],
]:
    card_order = {card.id: index for index, card in enumerate(tree.cards)}
    facet_order: dict[tuple[str, str], int] = {}
    leaf_order: dict[tuple[str, str, str], int] = {}
    for card in tree.cards:
        for facet_index, facet in enumerate(card.facets):
            facet_order[(card.id, facet.id)] = facet_index
            for leaf_index, leaf in enumerate(facet.leaves):
                leaf_order[(card.id, facet.id, leaf.id)] = leaf_index
    return card_order, facet_order, leaf_order


def build_component_usage(
    tree: JobTree,
    guidelines: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    card_order, facet_order, leaf_order = _placement_orders(tree)
    cards_by_component: dict[str, list[dict[str, str]]] = defaultdict(list)
    cites_by_component: dict[str, list[dict[str, str]]] = defaultdict(list)

    for card in tree.cards:
        for component_id in card.component:
            cards_by_component[component_id].append(
                {
                    "id": card.id,
                    "title": card.title,
                    "container": card.container,
                }
            )

    for guideline in guidelines:
        for component_id in _terms(guideline.get("component")):
            cites_by_component[component_id].append(
                {
                    "id": guideline["id"],
                    "overview": guideline.get("overview") or "",
                    "card": guideline.get("card") or "",
                    "facet": guideline.get("facet") or "",
                    "leaf": guideline.get("leaf") or "",
                }
            )

    usage: dict[str, dict[str, Any]] = {}
    for component_id in set(cards_by_component) | set(cites_by_component):
        cards = cards_by_component.get(component_id, [])
        cites = cites_by_component.get(component_id, [])
        cites.sort(
            key=lambda row: (
                card_order.get(row["card"], 999),
                facet_order.get((row["card"], row["facet"]), 999),
                leaf_order.get((row["card"], row["facet"], row["leaf"]), 999),
                row["id"],
            )
        )
        usage[component_id] = {
            "cards": cards,
            "cites": cites,
            "cards_total": len(cards),
            "cites_total": len(cites),
        }
    return usage


def list_components(registry: ComponentRegistry) -> dict[str, Any]:
    if not registry.refs:
        return {
            "components": [],
            "count": 0,
            "total": 0,
            "note": EMPTY_COMPONENTS_NOTE,
        }
    items = [
        {
            "id": ref.id,
            "title": ref.title,
            "overview": registry.records[ref.id]["overview"],
        }
        for ref in registry.refs
    ]
    return {"components": items, "count": len(items), "total": len(items)}


def _optional_section(
    record: dict[str, Any],
    key: str,
    *,
    include: bool,
) -> dict[str, Any]:
    if not include:
        return {}
    value = record.get(key)
    if value:
        return {key: value}
    return {}


def get_component(
    registry: ComponentRegistry,
    usage: dict[str, dict[str, Any]],
    component_id: str,
    *,
    include_vs: bool = True,
    include_variants: bool = True,
    include_accessibility: bool = True,
    include_keyboard: bool = True,
    include_keywords: bool = False,
    include_used_on: bool = False,
) -> dict[str, Any]:
    record = registry.records.get(component_id)
    if record is None:
        return {
            "found": False,
            "error": f"Unknown component {component_id!r}.",
        }
    component: dict[str, Any] = {
        "id": record["id"],
        "title": record["title"],
        "overview": record["overview"],
        "apply_when": record["apply_when"],
        "not_when": record["not_when"],
        **_optional_section(record, "vs", include=include_vs),
        **_optional_section(record, "variants", include=include_variants),
        **_optional_section(record, "accessibility", include=include_accessibility),
        **_optional_section(record, "keyboard", include=include_keyboard),
        **_optional_section(record, "keywords", include=include_keywords),
    }
    if include_used_on:
        row = usage.get(component_id, {})
        component["used_on"] = {
            "cards": row.get("cards", []),
            "cites": row.get("cites", []),
            "cards_total": row.get("cards_total", 0),
            "cites_total": row.get("cites_total", 0),
        }
    return {"found": True, "component": component}
