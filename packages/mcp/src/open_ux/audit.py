from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from open_ux.catalog import EMPTY_NOTE, Catalog, get_by_id, select_by_jobs
from open_ux.markup import Node, find_by_id, live_controls, parse_markup, visible_text, walk

Verdict = Literal["pass", "fail", "incomplete"]
Checker = Callable[[str, str], Verdict]

INCOMPLETE_NO_CHECKER = (
    "No deterministic checker is registered for this rule. "
    "Client LLM may finish using pass_when / fail_when. No server LLM."
)
INCOMPLETE_DESCRIPTION = (
    "Target type is description; server does not grade prose. "
    "Client LLM may finish using pass_when / fail_when. No server LLM."
)

_CHECKERS: dict[str, Checker] = {}


def register_checker(guideline_id: str) -> Callable[[Checker], Checker]:
    """Register a fail-closed HTML/JSX grader. Missing id → incomplete."""

    def deco(fn: Checker) -> Checker:
        _CHECKERS[guideline_id] = fn
        return fn

    return deco


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


def _catalog_meta(catalog: Catalog) -> dict[str, Any]:
    return {
        "status": "empty" if catalog.empty else "ok",
        "guideline_count": len(catalog.guidelines),
        "version": catalog.version,
    }


def audit(
    catalog: Catalog,
    *,
    target_type: str,
    content: str,
    guideline_ids: list[str] | None = None,
    jobs: str | list[str] | None = None,
) -> dict[str, Any]:
    if target_type not in {"html", "jsx", "description"}:
        raise ValueError("target.type must be html, jsx, or description")

    requested = [gid for gid in (guideline_ids or []) if gid]
    job_scope = jobs if isinstance(jobs, list) else ([jobs] if jobs else [])
    job_scope = [j for j in job_scope if j]

    if not requested and not job_scope:
        payload: dict[str, Any] = {
            "error": "audit requires jobs or guideline_ids; the full catalog is never run.",
            "results": [],
            "summary": {"pass": 0, "fail": 0, "incomplete": 0},
            "catalog": _catalog_meta(catalog),
        }
        if catalog.empty:
            payload["note"] = EMPTY_NOTE
        return payload

    results: list[dict[str, Any]] = []

    if catalog.empty:
        for gid in requested:
            results.append(_unknown(gid))
        payload = {
            "results": results,
            "summary": _summary(results),
            "catalog": _catalog_meta(catalog),
            "note": EMPTY_NOTE,
        }
        return payload

    if requested:
        for gid in requested:
            g = get_by_id(catalog, gid)
            if g is None:
                results.append(_unknown(gid))
            else:
                results.append(_grade(g, target_type=target_type, content=content))
    else:
        for g in select_by_jobs(catalog, job_scope):
            results.append(_grade(g, target_type=target_type, content=content))

    return {
        "results": results,
        "summary": _summary(results),
        "catalog": _catalog_meta(catalog),
    }


def _result(guideline: dict[str, Any], verdict: Verdict, extra: str | None = None) -> dict[str, Any]:
    reasons = _reasons(guideline, kind=verdict)
    if extra:
        reasons = reasons + [f"{guideline['id']}: {extra}"]
    return {
        "guideline_id": guideline["id"],
        "verdict": verdict,
        "reasons": reasons,
        "rule": guideline.get("rule"),
        "pass_when": list(guideline.get("pass_when") or []),
        "fail_when": list(guideline.get("fail_when") or []),
    }


def _grade(guideline: dict[str, Any], *, target_type: str, content: str) -> dict[str, Any]:
    if target_type == "description":
        return _result(guideline, "incomplete", INCOMPLETE_DESCRIPTION)

    checker = _CHECKERS.get(guideline["id"])
    if checker is None:
        return _result(guideline, "incomplete", INCOMPLETE_NO_CHECKER)

    verdict = checker(content, target_type)
    if verdict == "incomplete":
        return _result(guideline, "incomplete", INCOMPLETE_NO_CHECKER)
    return _result(guideline, verdict)


def _summary(results: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"pass": 0, "fail": 0, "incomplete": 0}
    for row in results:
        v = row.get("verdict")
        if v in counts:
            counts[v] += 1
    return counts


def _has_outside_label(control: Node, root: Node) -> bool:
    cid = control.attrs.get("id") or ""
    if cid:
        for n in walk(root):
            if n.tag == "label" and n.attrs.get("for") == cid:
                if visible_text(n, skip_controls=True):
                    return True
    cur = control.parent
    while cur is not None:
        if cur.tag == "label" and visible_text(cur, skip_controls=True):
            return True
        cur = cur.parent
    for ref in (control.attrs.get("aria-labelledby") or "").split():
        target = find_by_id(root, ref)
        if target is not None and visible_text(target, skip_controls=True):
            return True
    return False


def _outside_labels_for_controls(content: str, target_type: str) -> Verdict:
    """Pass if every live field has a visible outside label; fail if any do not.

    No live fields → pass (vacuous). Placeholder / aria-label alone do not count.
    """
    root = parse_markup(content, target_type)
    found = live_controls(root)
    if not found:
        return "pass"
    if all(_has_outside_label(c, root) for c in found):
        return "pass"
    return "fail"


@register_checker("forms.field_labels.visible_label")
def _check_visible_label(content: str, target_type: str) -> Verdict:
    return _outside_labels_for_controls(content, target_type)


@register_checker("forms.field_labels.label_stays_visible")
def _check_label_stays_visible(content: str, target_type: str) -> Verdict:
    # Static markup: an outside <label> / labelledby text stays on screen while typing.
    # Placeholder-only names disappear → fail (same association test).
    return _outside_labels_for_controls(content, target_type)
