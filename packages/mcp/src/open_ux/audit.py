from __future__ import annotations

from typing import Any

from open_ux.catalog import EMPTY_NOTE, Catalog, get_by_id, select_by_jobs
from open_ux.jobs import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    MISS_NOTE,
    TEMPLATE_FALLBACK_ALIAS,
)

PACK_KEYS = ("id", "title", "rule", "pass_when", "fail_when")
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
        "rule": guideline.get("rule") or "",
        "pass_when": list(guideline.get("pass_when") or []),
        "fail_when": list(guideline.get("fail_when") or []),
    }


def _matches_query(guideline: dict[str, Any], query: str | None) -> bool:
    q = (query or "").strip().lower()
    if not q:
        return True
    blob = " ".join(
        [
            str(guideline.get("id") or ""),
            str(guideline.get("title") or ""),
            str(guideline.get("rule") or ""),
            " ".join(guideline.get("pass_when") or []),
            " ".join(guideline.get("fail_when") or []),
        ]
    ).lower()
    return q in blob


def _select_by_need(catalog: Catalog, jobs: str) -> list[dict[str, Any]]:
    matched = select_by_jobs(catalog, jobs)
    if matched:
        return matched
    alias = TEMPLATE_FALLBACK_ALIAS.get(jobs)
    if alias:
        return select_by_jobs(catalog, alias)
    return []


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
            if g is not None and _matches_query(g, query):
                found.append(g)
        selected = found
    else:
        assert job is not None
        selected = [g for g in _select_by_need(catalog, job) if _matches_query(g, query)]

    total = len(selected)
    capped = selected[:cap]
    note = None
    if total == 0:
        note = MISS_NOTE
    return _payload(capped, total=total, note=note)
