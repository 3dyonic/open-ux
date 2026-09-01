from __future__ import annotations

from typing import Any, Literal

from open_ux.catalog import EMPTY_NOTE, Catalog, get_by_id, select

Verdict = Literal["pass", "fail", "incomplete"]

INCOMPLETE_NO_CHECKER = (
    "No deterministic checker is registered for this rule. "
    "Client LLM may finish using pass_when / fail_when. No server LLM."
)
INCOMPLETE_DESCRIPTION = (
    "Target type is description; server does not grade prose. "
    "Client LLM may finish using pass_when / fail_when. No server LLM."
)


def _reasons(guideline: dict[str, Any], *, kind: Literal["pass", "fail", "incomplete"]) -> list[str]:
    """Reuse catalog wording + rule id. No house soft-copy."""
    gid = guideline["id"]
    if kind == "pass":
        body = list(guideline.get("pass_when") or [])
    elif kind == "fail":
        body = list(guideline.get("fail_when") or [])
    else:
        body = list(guideline.get("pass_when") or []) + list(guideline.get("fail_when") or [])
    return [f"{gid}: {line}" for line in body]


def _unknown(guideline_id: str) -> dict[str, Any]:
    return {
        "guideline_id": guideline_id,
        "verdict": "incomplete",
        "reasons": [
            f"{guideline_id}: Unknown guideline_id. Catalog has no matching rule."
        ],
    }


def audit(
    catalog: Catalog,
    *,
    target_type: str,
    content: str,
    guideline_ids: list[str] | None = None,
) -> dict[str, Any]:
    if target_type not in {"html", "jsx", "description"}:
        raise ValueError("target.type must be html, jsx, or description")

    requested = list(guideline_ids or [])
    results: list[dict[str, Any]] = []

    if catalog.empty:
        for gid in requested:
            results.append(_unknown(gid))
        summary = _summary(results)
        return {
            "results": results,
            "summary": summary,
            "catalog": {
                "status": "empty",
                "guideline_count": 0,
                "version": catalog.version,
            },
            "note": EMPTY_NOTE,
        }

    if requested:
        for gid in requested:
            g = get_by_id(catalog, gid)
            if g is None:
                results.append(_unknown(gid))
            else:
                results.append(_grade(g, target_type=target_type, content=content))
    else:
        for g in select(catalog, None):
            results.append(_grade(g, target_type=target_type, content=content))

    return {
        "results": results,
        "summary": _summary(results),
        "catalog": {
            "status": "ok",
            "guideline_count": len(catalog.guidelines),
            "version": catalog.version,
        },
    }


def _grade(guideline: dict[str, Any], *, target_type: str, content: str) -> dict[str, Any]:
    del content  # Hybrid C: no server LLM; no invented HTML/JSX checkers in this scaffold.
    check = guideline.get("check")
    if target_type == "description" or check in {"llm_judgment", "either"}:
        return {
            "guideline_id": guideline["id"],
            "verdict": "incomplete",
            "reasons": _reasons(guideline, kind="incomplete")
            + [f"{guideline['id']}: {INCOMPLETE_DESCRIPTION if target_type == 'description' else INCOMPLETE_NO_CHECKER}"],
            "rule": guideline.get("rule"),
            "pass_when": list(guideline.get("pass_when") or []),
            "fail_when": list(guideline.get("fail_when") or []),
        }
    # deterministic + html/jsx — checkers land with the rules, not before.
    return {
        "guideline_id": guideline["id"],
        "verdict": "incomplete",
        "reasons": _reasons(guideline, kind="incomplete")
        + [f"{guideline['id']}: {INCOMPLETE_NO_CHECKER}"],
        "rule": guideline.get("rule"),
        "pass_when": list(guideline.get("pass_when") or []),
        "fail_when": list(guideline.get("fail_when") or []),
    }


def _summary(results: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"pass": 0, "fail": 0, "incomplete": 0}
    for row in results:
        v = row.get("verdict")
        if v in counts:
            counts[v] += 1
    return counts
