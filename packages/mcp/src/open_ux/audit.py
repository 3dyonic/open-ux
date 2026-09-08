from __future__ import annotations

from collections import defaultdict
from typing import Any

from open_ux.bm25 import guideline_blob, rank_blobs
from open_ux.catalog import EMPTY_NOTE, Catalog, get_by_id, select_by_jobs
from open_ux.jobs import (
    CARD_IDS,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    MISS_NOTE,
    JobTree,
    card_by_id,
    load_job_tree,
)

PACK_KEYS = ("id", "title", "name", "overview", "rule", "facet")
NEED_ERROR = "audit requires jobs or guideline_ids; the full catalog is never run."
HOST_CITATIONS_ONLY = "citations_only"


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


def _pack(guideline: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": guideline["id"],
        "title": guideline.get("title") or "",
        "name": guideline.get("name") or guideline.get("title") or "",
        "overview": guideline.get("overview") or "",
        "rule": guideline.get("rule") or "",
        "facet": guideline.get("facet") or "",
    }


def _matches_query(guideline: dict[str, Any], query: str | None) -> bool:
    q = (query or "").strip()
    if not q:
        return True
    _order, matched = rank_blobs(q, [guideline_blob(guideline)])
    return matched


def _rerank_by_query(
    rows: list[dict[str, Any]], query: str | None
) -> tuple[list[dict[str, Any]], bool]:
    """Query orders the pack, never drops access: rank matches first.

    In-process BM25 over pack JSON. Phrase hits still lead via a
    substring bonus (OUX-24). Zero hits fail open (OUX-21).
    """
    q = (query or "").strip()
    if not q:
        return rows, True
    blobs = [guideline_blob(row) for row in rows]
    order, matched = rank_blobs(q, blobs)
    if not matched:
        return rows, False
    return [rows[i] for i in order], True


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


def _payload(
    rows: list[dict[str, Any]],
    *,
    total: int,
    limit: int,
    offset: int,
    note: str | None = None,
    error: str | None = None,
    query_fallback: bool = False,
) -> dict[str, Any]:
    packed = [_pack(g) for g in rows]
    count = len(packed)
    out: dict[str, Any] = {
        "guidelines": packed,
        "count": count,
        "total": total,
        "limit": limit,
        "offset": offset,
        "host": HOST_CITATIONS_ONLY,
    }
    omitted = max(0, total - offset - count)
    if omitted:
        next_offset = offset + count
        out["omitted"] = omitted
        out["next_offset"] = next_offset
        out["omitted_hint"] = (
            f"{omitted} more not shown; pass offset={next_offset}"
        )
    if query_fallback:
        out["query_fallback"] = True
    if note:
        out["note"] = note
    if error:
        out["error"] = error
    return out


def audit(
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
    """Need in, matching rule criteria out. Leftover target/content are ignored."""
    del target, content, target_type
    cap = _clamp_limit(limit)
    skip = _clamp_offset(offset)
    requested = [gid for gid in (guideline_ids or []) if gid]
    job = (jobs or "").strip() or None

    if not requested and not job:
        note = EMPTY_NOTE if catalog.empty else None
        return _payload(
            [], total=0, limit=cap, offset=skip, note=note, error=NEED_ERROR
        )

    if catalog.empty:
        return _payload([], total=0, limit=cap, offset=skip, note=EMPTY_NOTE)

    if requested:
        found: list[dict[str, Any]] = []
        for gid in requested:
            g = get_by_id(catalog, gid)
            if g is not None:
                found.append(g)
        rows = found
    else:
        assert job is not None
        scoped = _select_by_need(catalog, job)
        rows = _stratify_by_facet(scoped, load_job_tree(), len(scoped) or 1)

    selected, query_matched = _rerank_by_query(rows, query)

    total = len(selected)
    page = selected[skip : skip + cap]
    note = None
    query_fallback = False
    if total == 0:
        note = MISS_NOTE
    elif not query_matched:
        note = f"query too narrow — showing all {total} guidelines in scope"
        query_fallback = True
    return _payload(
        page,
        total=total,
        limit=cap,
        offset=skip,
        note=note,
        query_fallback=query_fallback,
    )
