from __future__ import annotations

from collections import defaultdict
from typing import Any

from open_ux.catalog import EMPTY_NOTE, Catalog, get_by_id, select_by_jobs
from open_ux.jobs import (
    CARD_IDS,
    DEFAULT_LIMIT,
    LEAF_IDS,
    MAX_LIMIT,
    MISS_NOTE,
    JobTree,
    card_by_id,
    card_id_for_leaf,
    load_job_tree,
)

PACK_ROW_KEYS = (
    "id",
    "title",
    "name",
    "overview",
    "apply_when",
    "not_when",
    "rule",
    "component",
    "leaf",
    "card",
    "facet",
)
OPTIONAL_PACK_ROW_KEYS = ("hints",)
PACK_KEYS = PACK_ROW_KEYS + OPTIONAL_PACK_ROW_KEYS
NEED_ERROR = "pack requires jobs or guideline_ids; the full catalog is never run."
HOST_CITATIONS_ONLY = "citations_only"
CITE_VIA = "get_guideline"


def _clamp_limit(limit: int) -> int:
    if limit < 1:
        return 1
    if limit > MAX_LIMIT:
        return MAX_LIMIT
    return limit


def _clamp_offset(offset: int) -> int:
    if offset < 0:
        return 0
    return offset


def _terms(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if item]
    return []


def _hints_extra(guideline: dict[str, Any]) -> dict[str, list[str]]:
    hints = _terms(guideline.get("hints"))
    if hints:
        return {"hints": hints}
    return {}


def _pack_row(guideline: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": guideline["id"],
        "title": guideline.get("title") or "",
        "name": guideline.get("name") or guideline.get("title") or "",
        "overview": guideline.get("overview") or "",
        "apply_when": guideline.get("apply_when") or "",
        "not_when": guideline.get("not_when") or "",
        "rule": guideline.get("rule") or "",
        "component": _terms(guideline.get("component")),
        "leaf": guideline.get("leaf") or "",
        "card": guideline.get("card") or "",
        "facet": guideline.get("facet") or "",
        **_hints_extra(guideline),
    }


def _facet_keys(tree: JobTree) -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    for card_id in CARD_IDS:
        card = card_by_id(tree, card_id)
        if card is None:
            continue
        for facet in card.facets:
            keys.append((card.id, facet.id))
    return keys


def _stratify_by_facet(
    rows: list[dict[str, Any]],
    tree: JobTree,
    cap: int,
) -> list[dict[str, Any]]:
    """Full-set facet round-robin (OUX-32). `cap` is unused; callers slice.

    One row per facet per pass, Card facet order, then leftover keys.
    Page windows stay facet-balanced without reshuffling later offsets.
    """
    del cap
    if not rows:
        return []
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[(str(row.get("card") or ""), str(row.get("facet") or ""))].append(row)

    ordered: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for key in _facet_keys(tree):
        if by_key.get(key) and key not in seen:
            ordered.append(key)
            seen.add(key)
    for key in by_key:
        if key not in seen:
            ordered.append(key)
            seen.add(key)

    if not ordered:
        return list(rows)

    queues = {key: list(by_key[key]) for key in ordered}
    out: list[dict[str, Any]] = []
    while True:
        progressed = False
        for key in ordered:
            bucket = queues[key]
            if bucket:
                out.append(bucket.pop(0))
                progressed = True
        if not progressed:
            break
    return out


def _select_by_need(catalog: Catalog, jobs: str) -> list[dict[str, Any]]:
    return select_by_jobs(catalog, jobs)


def _situation_envelope(job: str, tree: JobTree) -> dict[str, Any] | None:
    """Card when/reject for Card or Leaf pack. Omit for container aliases."""
    need = (job or "").strip()
    if not need:
        return None
    leaf_id: str | None = None
    card_id: str | None = None
    if need in LEAF_IDS:
        leaf_id = need
        card_id = card_id_for_leaf(tree, need)
    elif card_by_id(tree, need) is not None:
        card_id = need
    else:
        return None
    card = card_by_id(tree, card_id or "")
    if card is None:
        return None
    out: dict[str, Any] = {
        "card": card.id,
        "when": list(card.when),
        "reject": [{"id": item.id, "why": item.why} for item in card.reject],
    }
    if leaf_id:
        out["leaf"] = leaf_id
    return out


def _payload(
    rows: list[dict[str, Any]],
    *,
    total: int,
    offset: int,
    note: str | None = None,
    error: str | None = None,
    situation: dict[str, Any] | None = None,
    cite_via: str | None = None,
) -> dict[str, Any]:
    packed = [_pack_row(g) for g in rows]
    count = len(packed)
    out: dict[str, Any] = {
        "guidelines": packed,
        "count": count,
        "total": total,
        "offset": offset,
        "host": HOST_CITATIONS_ONLY,
    }
    if situation is not None:
        out["situation"] = situation
    if cite_via is not None:
        out["cite_via"] = cite_via
    omitted = max(0, total - offset - count)
    if omitted:
        next_offset = offset + count
        out["omitted"] = omitted
        out["next_offset"] = next_offset
        out["omitted_hint"] = (
            f"{omitted} more not shown; pass offset={next_offset}"
        )
    if note:
        out["note"] = note
    if error:
        out["error"] = error
    return out


def pack(
    catalog: Catalog,
    *,
    jobs: str | None = None,
    query: str | None = None,
    guideline_ids: list[str] | None = None,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
    target: Any = None,
    content: Any = None,
    target_type: str | None = None,
) -> dict[str, Any]:
    """Need in, matching rule criteria out. Leftover target/content are ignored.

    ``query`` is accepted for wire compatibility and is not ranked. Catalog /
    facet order only. Optional local BM25: helpers/rank_pack.py.
    """
    del target, content, target_type, query
    cap = _clamp_limit(limit)
    skip = _clamp_offset(offset)
    requested = [gid for gid in (guideline_ids or []) if gid]
    job = (jobs or "").strip() or None

    if not requested and not job:
        note = EMPTY_NOTE if catalog.empty else None
        return _payload(
            [], total=0, offset=skip, note=note, error=NEED_ERROR
        )

    if catalog.empty:
        return _payload([], total=0, offset=skip, note=EMPTY_NOTE)

    tree = load_job_tree()
    situation: dict[str, Any] | None = None
    cite_via: str | None = None

    if requested:
        found: list[dict[str, Any]] = []
        for gid in requested:
            g = get_by_id(catalog, gid)
            if g is not None:
                found.append(g)
        rows = found
        if found:
            cite_via = CITE_VIA
    else:
        assert job is not None
        situation = _situation_envelope(job, tree)
        cite_via = CITE_VIA
        scoped = _select_by_need(catalog, job)
        rows = _stratify_by_facet(scoped, tree, len(scoped) or 1)

    total = len(rows)
    page = rows[skip : skip + cap]
    note = MISS_NOTE if total == 0 else None
    return _payload(
        page,
        total=total,
        offset=skip,
        note=note,
        situation=situation,
        cite_via=cite_via,
    )
