from __future__ import annotations

from collections import defaultdict
from typing import Any

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

PACK_KEYS = ("id", "title", "name", "rule", "pass_when", "fail_when", "facet")
NEED_ERROR = "audit requires jobs or guideline_ids; the full catalog is never run."


def _clamp_limit(limit: int) -> int:
    if limit < 1:
        return 1
    if limit > MAX_LIMIT:
        return MAX_LIMIT
    return limit


def _pack(guideline: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": guideline["id"],
        "title": guideline.get("title") or "",
        "name": guideline.get("name") or guideline.get("title") or "",
        "rule": guideline.get("rule") or "",
        "pass_when": list(guideline.get("pass_when") or []),
        "fail_when": list(guideline.get("fail_when") or []),
        "facet": guideline.get("facet") or "",
    }


def _query_blob(guideline: dict[str, Any]) -> str:
    return " ".join(
        [
            str(guideline.get("id") or ""),
            str(guideline.get("title") or ""),
            str(guideline.get("name") or ""),
            str(guideline.get("rule") or ""),
            " ".join(guideline.get("pass_when") or []),
            " ".join(guideline.get("fail_when") or []),
        ]
    ).lower()


def _query_tokens(query: str) -> list[str]:
    return [part for part in query.strip().lower().split() if len(part) > 1]


def _matches_query(guideline: dict[str, Any], query: str | None) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return True
    blob = _query_blob(guideline)
    if q in blob:
        return True
    tokens = _query_tokens(q)
    return bool(tokens) and any(token in blob for token in tokens)


def _rerank_by_query(
    rows: list[dict[str, Any]], query: str | None
) -> tuple[list[dict[str, Any]], bool]:
    """Query narrows attention, never access: rank matches first, drop nothing.

    Phrase hits (full query in the blob) stay ahead of token-any hits so a
    two-word query like "action panel" still surfaces that rule first.
    Token-any is recall for multi-word queries that have no phrase hit
    (OUX-24). Zero hits fail open (OUX-21).
    """
    q = (query or "").strip()
    if not q:
        return rows, True
    needle = q.lower()
    phrase: list[dict[str, Any]] = []
    token_only: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []
    for row in rows:
        blob = _query_blob(row)
        if needle in blob:
            phrase.append(row)
        elif _matches_query(row, q):
            token_only.append(row)
        else:
            unmatched.append(row)
    if not phrase and not token_only:
        return rows, False
    return phrase + token_only + unmatched, True


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
    """Reorder a Card/container pack so the first `cap` rows cover facets.

    Round-robin: quota pass, then fill in Card facet order (not catalog-file
    order). Known scaling limit: when len(F) >= cap, take 1 from each of the
    first `cap` facets; later facets get zero rows in that window (OUX-24).
    Returns the full set: stratified sample first, leftover in facet order.
    """
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

    facet_count = len(ordered)
    if facet_count == 0:
        return list(rows)

    taken: set[int] = set()
    head: list[dict[str, Any]] = []

    if facet_count >= cap:
        for key in ordered[:cap]:
            row = by_key[key][0]
            head.append(row)
            taken.add(id(row))
    else:
        quota = max(1, cap // facet_count)
        for key in ordered:
            take = 0
            for row in by_key[key]:
                if take >= quota or len(head) >= cap:
                    break
                head.append(row)
                taken.add(id(row))
                take += 1
            if len(head) >= cap:
                break
        for key in ordered:
            if len(head) >= cap:
                break
            for row in by_key[key]:
                if id(row) in taken:
                    continue
                head.append(row)
                taken.add(id(row))
                if len(head) >= cap:
                    break

    tail: list[dict[str, Any]] = []
    for key in ordered:
        for row in by_key[key]:
            if id(row) not in taken:
                tail.append(row)
    return head + tail


def _select_by_need(catalog: Catalog, jobs: str) -> list[dict[str, Any]]:
    return select_by_jobs(catalog, jobs)


def _payload(
    rows: list[dict[str, Any]],
    *,
    total: int,
    note: str | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    packed = [_pack(g) for g in rows]
    out: dict[str, Any] = {
        "guidelines": packed,
        "count": len(packed),
        "total": total,
    }
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
    target: Any = None,
    content: Any = None,
    target_type: str | None = None,
) -> dict[str, Any]:
    """Need in, matching rule criteria out. Leftover target/content are ignored."""
    del target, content, target_type
    cap = _clamp_limit(limit)
    requested = [gid for gid in (guideline_ids or []) if gid]
    job = (jobs or "").strip() or None

    if not requested and not job:
        note = EMPTY_NOTE if catalog.empty else None
        return _payload([], total=0, note=note, error=NEED_ERROR)

    if catalog.empty:
        return _payload([], total=0, note=EMPTY_NOTE)

    if requested:
        found: list[dict[str, Any]] = []
        for gid in requested:
            g = get_by_id(catalog, gid)
            if g is not None:
                found.append(g)
        rows = found
    else:
        assert job is not None
        rows = _stratify_by_facet(_select_by_need(catalog, job), load_job_tree(), cap)

    selected, query_matched = _rerank_by_query(rows, query)

    total = len(selected)
    capped = selected[:cap]
    note = None
    if total == 0:
        note = MISS_NOTE
    elif not query_matched:
        note = f"query too narrow — showing all {total} guidelines in scope"
    return _payload(capped, total=total, note=note)
