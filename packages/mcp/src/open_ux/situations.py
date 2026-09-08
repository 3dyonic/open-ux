from __future__ import annotations

from typing import Any

from open_ux.jobs import (
    CONTAINER_IDS,
    LEAF_IDS,
    JobTree,
    card_by_id,
    card_id_for_leaf,
    container_by_id_or_alias,
    load_job_tree,
)

EMPTY_SITUATIONS_NOTE = (
    "No Situation Cards are loaded. Cited seed rules have not landed yet."
)
UNKNOWN_SITUATION = "No Situation Card with id {id!r}."
LEAF_NOT_CARD = (
    "{id!r} is a Leaf, not a Card. Expand it from {card}. "
    "Do not pass a Leaf as the need."
)
LEAF_NOT_CARD_NO_PARENT = (
    "{id!r} is a Leaf, not a Card. Expand it from its Card. "
    "Do not pass a Leaf as the need."
)
CONTAINER_NOT_CARD = (
    "{id!r} is a container, not a Card. "
    "Call list_situations with that container, then pick a Card."
)
NO_SUGGEST_MATCH = (
    "No Situation Card matches this task. "
    "Pick from list_situations or name a compose job "
    "(form, actions, feedback, nav, overlay, steps)."
)
SUGGEST_MENU_NOTE = (
    "Catalog map. Pick a container with list_situations, or a Card with "
    "get_situation. Then audit with jobs=<card_id>."
)

MAP_ROW_KEYS = ("id", "title", "overview", "hints")
SPEC_ROW_KEYS = (
    "id",
    "title",
    "container",
    "overview",
    "when",
    "reject",
    "facet_count",
    "provisional",
)


def _index_row(card) -> dict[str, Any]:
    return {
        "id": card.id,
        "title": card.title,
        "container": card.container,
        "facet_count": len(card.facets),
        "provisional": card.provisional,
    }


def _reject_payload(card) -> list[dict[str, str]]:
    return [{"id": item.id, "why": item.why} for item in card.reject]


def _spec_row(card) -> dict[str, Any]:
    return {
        "id": card.id,
        "title": card.title,
        "container": card.container,
        "overview": card.overview,
        "when": list(card.when),
        "reject": _reject_payload(card),
        "facet_count": len(card.facets),
        "provisional": card.provisional,
    }


def _map_row(card) -> dict[str, Any]:
    return {
        "id": card.id,
        "title": card.title,
        "overview": card.overview,
        "hints": list(card.hints),
    }


def _facet_payload(facet) -> dict[str, Any]:
    leaf_ids = [leaf.id for leaf in facet.leaves]
    pointers: list[str] = []
    seen: set[str] = set()
    for gid in facet.guideline_ids:
        if gid not in seen:
            seen.add(gid)
            pointers.append(gid)
    for leaf in facet.leaves:
        for gid in leaf.guideline_ids:
            if gid not in seen:
                seen.add(gid)
                pointers.append(gid)
    return {
        "id": facet.id,
        "title": facet.title,
        "leaves": leaf_ids,
        "guideline_ids": pointers,
    }


def _card_payload(card) -> dict[str, Any]:
    return {
        "id": card.id,
        "title": card.title,
        "container": card.container,
        "overview": card.overview,
        "when": list(card.when),
        "reject": _reject_payload(card),
        "facets": [_facet_payload(facet) for facet in card.facets],
        "provisional": card.provisional,
    }


def list_situations(
    tree: JobTree | None = None,
    *,
    container: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    tree = tree or load_job_tree()
    if limit < 1:
        limit = 1
    if offset < 0:
        offset = 0
    cards = list(tree.cards)
    scoped = False
    if container and container.strip():
        wanted = container_by_id_or_alias(tree, container.strip())
        if wanted is None:
            return {
                "situations": [],
                "count": 0,
                "total": 0,
                "limit": limit,
                "offset": offset,
                "note": f"Unknown container {container.strip()!r}.",
            }
        cards = [card for card in cards if card.container == wanted.id]
        scoped = True
    total = len(cards)
    page = cards[offset : offset + limit]
    rows = [_spec_row(card) if scoped else _index_row(card) for card in page]
    payload: dict[str, Any] = {
        "situations": rows,
        "count": len(page),
        "total": total,
        "limit": limit,
        "offset": offset,
    }
    if tree.empty:
        payload["note"] = EMPTY_SITUATIONS_NOTE
    return payload


def get_situation(
    card_id: str,
    tree: JobTree | None = None,
) -> dict[str, Any]:
    tree = tree or load_job_tree()
    wanted = (card_id or "").strip()
    if not wanted:
        return {"found": False, "id": wanted, "error": UNKNOWN_SITUATION.format(id=wanted)}
    if wanted in LEAF_IDS:
        parent = card_id_for_leaf(tree, wanted)
        error = (
            LEAF_NOT_CARD.format(id=wanted, card=parent)
            if parent
            else LEAF_NOT_CARD_NO_PARENT.format(id=wanted)
        )
        return {"found": False, "id": wanted, "error": error}
    if container_by_id_or_alias(tree, wanted) is not None or wanted in {
        "forms",
        "actions",
        "feedback",
    }:
        return {
            "found": False,
            "id": wanted,
            "error": CONTAINER_NOT_CARD.format(id=wanted),
        }
    card = card_by_id(tree, wanted)
    if card is None:
        return {"found": False, "id": wanted, "error": UNKNOWN_SITUATION.format(id=wanted)}
    return {"found": True, "situation": _card_payload(card)}


def suggest_card_ids(result: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for container in result.get("containers") or []:
        for row in container.get("situations") or []:
            ids.append(row["id"])
    return ids


def suggest_situations(
    task_text: str,
    surface: str | None = None,
    tree: JobTree | None = None,
) -> dict[str, Any]:
    tree = tree or load_job_tree()
    text = (task_text or "").strip()
    if tree.empty:
        return {"containers": [], "note": EMPTY_SITUATIONS_NOTE}
    if not text:
        return {"containers": [], "note": NO_SUGGEST_MATCH}

    by_container: dict[str, list] = {cid: [] for cid in CONTAINER_IDS}
    for card in tree.cards:
        by_container.setdefault(card.container, []).append(card)

    containers = []
    title_by_id = {item.id: item.title for item in tree.containers}
    for cid in CONTAINER_IDS:
        cards = by_container.get(cid) or []
        if not cards:
            continue
        containers.append(
            {
                "id": cid,
                "title": title_by_id.get(cid, cid),
                "situations": [_map_row(card) for card in cards],
            }
        )
    _ = surface  # accepted for old callers; never an id; never an order key
    return {"containers": containers, "note": SUGGEST_MENU_NOTE}
