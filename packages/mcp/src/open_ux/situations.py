from __future__ import annotations

import re
from typing import Any

from open_ux.jobs import (
    CARD_IDS,
    LEAF_IDS,
    JobTree,
    card_by_id,
    container_by_id_or_alias,
    load_job_tree,
)

EMPTY_SITUATIONS_NOTE = (
    "No Situation Cards are loaded. Cited seed rules have not landed yet."
)
UNKNOWN_SITUATION = "No Situation Card with id {id!r}."
LEAF_NOT_CARD = (
    "{id!r} is a Leaf, not a Card. Expand it from a Card "
    "(for example design_a_form). Do not pass a Leaf as the need."
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

# Surface is ranking bias only. Never returned as an id.
SURFACE_HINTS: dict[str, tuple[str, ...]] = {
    "checkout": (
        "build_a_multi_step_flow",
        "design_a_form",
        "protect_destructive_and_leave",
    ),
    "home": (
        "orient_in_the_place",
        "compose_a_data_display",
        "compose_feedback",
    ),
    "cart": (
        "design_actions_and_ctas",
        "protect_destructive_and_leave",
        "compose_feedback",
    ),
}

_STOP = frozenset(
    {
        "a",
        "an",
        "the",
        "to",
        "for",
        "of",
        "and",
        "or",
        "in",
        "on",
        "this",
        "that",
        "these",
        "those",
        "is",
        "are",
        "be",
        "with",
        "from",
        "as",
        "at",
        "vs",
        "it",
        "its",
        "into",
        "am",
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "they",
        "their",
    }
)
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return [
        token
        for token in _TOKEN_RE.findall(text.lower())
        if token not in _STOP and len(token) > 1
    ]


def _index_row(card) -> dict[str, Any]:
    return {
        "id": card.id,
        "title": card.title,
        "container": card.container,
        "facet_count": len(card.facets),
        "provisional": card.provisional,
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
        "problem": card.problem,
        "when": list(card.when),
        "reject": [{"id": item.id, "why": item.why} for item in card.reject],
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
    total = len(cards)
    page = cards[offset : offset + limit]
    payload: dict[str, Any] = {
        "situations": [_index_row(card) for card in page],
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
        return {"found": False, "id": wanted, "error": LEAF_NOT_CARD.format(id=wanted)}
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


def _score_card(card, task_text: str, task_tokens: list[str]) -> tuple[int, str]:
    title_tokens = set(_tokens(f"{card.title} {card.id.replace('_', ' ')}"))
    when_tokens = set(_tokens(" ".join(card.when)))
    hint_tokens = set(_tokens(" ".join(card.hints)))
    problem_tokens = set(_tokens(card.problem))
    score = 0
    hits: list[str] = []
    lowered = task_text.lower()
    for phrase in card.when:
        if phrase.lower() in lowered:
            score += 4
            hits.append(phrase)
    for token in task_tokens:
        if token in title_tokens:
            score += 3
            hits.append(token)
        elif token in when_tokens:
            score += 2
            hits.append(token)
        elif token in hint_tokens or token in problem_tokens:
            score += 1
            hits.append(token)
    why = hits[0] if hits else card.problem
    return score, why


def suggest_situations(
    task_text: str,
    surface: str | None = None,
    tree: JobTree | None = None,
) -> dict[str, Any]:
    tree = tree or load_job_tree()
    text = (task_text or "").strip()
    if tree.empty:
        return {"situations": [], "rejected": None, "note": EMPTY_SITUATIONS_NOTE}
    if not text:
        return {"situations": [], "rejected": None, "note": NO_SUGGEST_MATCH}

    task_tokens = _tokens(text)
    ranked: list[tuple[int, str, Any, str]] = []
    hint_cards = SURFACE_HINTS.get((surface or "").strip().lower(), ())
    for card in tree.cards:
        score, why = _score_card(card, text, task_tokens)
        if card.id in hint_cards:
            score += 2
        if score > 0:
            ranked.append((score, card.id, card, why))
    ranked.sort(key=lambda row: (-row[0], CARD_IDS.index(row[1])))
    keep = [row for row in ranked if row[0] >= 2]
    if not keep:
        return {"situations": [], "rejected": None, "note": NO_SUGGEST_MATCH}

    winner = keep[0][2]
    rejected = None
    reject_ids = {item.id: item.why for item in winner.reject}
    for _score, card_id, card, _why in keep[1:]:
        if card_id in reject_ids:
            rejected = {"id": card.id, "why": reject_ids[card_id]}
            break
    if rejected is None and winner.reject:
        first = winner.reject[0]
        rejected = {"id": first.id, "why": first.why}

    return {
        "situations": [
            {"id": card.id, "title": card.title, "why": why}
            for _score, _cid, card, why in keep[:5]
        ],
        "rejected": rejected,
    }
