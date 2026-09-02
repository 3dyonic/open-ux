from __future__ import annotations

import re
from collections.abc import Callable
from html.parser import HTMLParser
from typing import Any, Literal

from open_ux.catalog import EMPTY_NOTE, Catalog, get_by_id, select_by_jobs

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

_VOID = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)
_SKIP_INPUT_TYPES = frozenset({"hidden", "submit", "button", "reset", "image"})
_CONTROL_TAGS = frozenset({"input", "textarea", "select"})
# Markup inside these is not a live control (inert / not painted as a field).
_IGNORE_CONTROL_ANCESTORS = frozenset({"script", "style", "template", "textarea"})


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
        if not requested:
            # jobs-only on an empty catalog: nothing to grade.
            pass
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


# --- HTML / JSX parse (no extra deps) ---------------------------------------


class _Node:
    __slots__ = ("tag", "attrs", "parent", "children", "text")

    def __init__(self, tag: str, attrs: dict[str, str], parent: _Node | None) -> None:
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: list[_Node] = []
        self.text: list[str] = []


class _TreeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = _Node("document", {}, None)
        self._cur = self.root

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = _Node(tag.lower(), {k.lower(): (v or "") for k, v in attrs}, self._cur)
        self._cur.children.append(node)
        if tag.lower() not in _VOID:
            self._cur = node

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        cur = self._cur
        while cur.parent is not None:
            if cur.tag == tag:
                self._cur = cur.parent
                return
            cur = cur.parent

    def handle_data(self, data: str) -> None:
        if data:
            self._cur.text.append(data)


def _jsx_starts_tag(src: str, i: int) -> bool:
    if i >= len(src) or src[i] != "<":
        return False
    nxt = src[i + 1] if i + 1 < len(src) else ""
    return nxt.isalpha() or nxt in "/!"


def _skip_quoted(src: str, i: int) -> tuple[int, str]:
    quote = src[i]
    j = i + 1
    n = len(src)
    while j < n:
        if src[j] == "\\" and j + 1 < n:
            j += 2
            continue
        if src[j] == quote:
            return j + 1, src[i : j + 1]
        j += 1
    return n, src[i:]


def _skip_line_comment(src: str, i: int) -> int:
    j = i + 2
    n = len(src)
    while j < n and src[j] != "\n":
        j += 1
    return j


def _skip_block_comment(src: str, i: int) -> int:
    j = i + 2
    n = len(src)
    while j + 1 < n and not (src[j] == "*" and src[j + 1] == "/"):
        j += 1
    return min(n, j + 2)


def _copy_jsx_tag(src: str, i: int) -> tuple[int, str, str, bool, bool]:
    """Copy one JSX/HTML tag. Returns (next_i, raw, name, is_close, self_close)."""
    start = i
    n = len(src)
    i += 1
    is_close = False
    if i < n and src[i] == "/":
        is_close = True
        i += 1
    name_start = i
    while i < n and (src[i].isalnum() or src[i] in "-_:"):
        i += 1
    name = src[name_start:i].lower()
    self_close = False
    quote: str | None = None
    braces = 0
    while i < n:
        ch = src[i]
        if quote:
            if ch == "\\" and i + 1 < n:
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in {"'", '"'}:
            quote = ch
            i += 1
            continue
        if ch == "{":
            braces += 1
            i += 1
            continue
        if ch == "}" and braces:
            braces -= 1
            i += 1
            continue
        if braces:
            i += 1
            continue
        if ch == "/" and i + 1 < n and src[i + 1] == ">":
            self_close = True
            i += 2
            break
        if ch == ">":
            i += 1
            break
        i += 1
    return i, src[start:i], name, is_close, self_close


def _strip_jsx_js_noise(src: str) -> str:
    """Keep JSX tags and text; drop JS comments and JS string bodies.

    html.parser has no JS lexer. Leftover `// <input …>` or a string of
    markup must not become gradeable controls. `//` in JSX text or in an
    attribute URL is kept. `{/* … */}` in children is dropped.
    """
    out: list[str] = []
    i = 0
    n = len(src)
    depth = 0
    expr = 0
    while i < n:
        in_js = depth == 0 or expr > 0
        if in_js and i + 1 < n and src[i] == "/" and src[i + 1] == "/":
            i = _skip_line_comment(src, i)
            continue
        if in_js and i + 1 < n and src[i] == "/" and src[i + 1] == "*":
            i = _skip_block_comment(src, i)
            continue
        if in_js and src[i] in {"'", '"', "`"}:
            i, _raw = _skip_quoted(src, i)
            continue
        if src[i] == "{" and depth > 0:
            expr += 1
            i += 1
            continue
        if src[i] == "}" and expr > 0:
            expr -= 1
            i += 1
            continue
        if _jsx_starts_tag(src, i):
            i, raw, name, is_close, self_close = _copy_jsx_tag(src, i)
            out.append(raw)
            if is_close:
                depth = max(0, depth - 1)
            elif not self_close and name not in _VOID:
                depth += 1
            continue
        if depth > 0 and expr == 0:
            out.append(src[i])
        i += 1
    return "".join(out)


def _normalize_markup(content: str, target_type: str) -> str:
    text = content
    if target_type == "jsx":
        text = _strip_jsx_js_noise(text)
        text = re.sub(r"\bhtmlFor=", "for=", text)
        text = re.sub(r"\bclassName=", "class=", text)
        text = re.sub(r"/>", ">", text)
    return f"<div>{text}</div>"


def _parse(content: str, target_type: str) -> _Node:
    parser = _TreeParser()
    parser.feed(_normalize_markup(content, target_type))
    parser.close()
    return parser.root


def _walk(node: _Node) -> list[_Node]:
    out = [node]
    for child in node.children:
        out.extend(_walk(child))
    return out


def _visible_text(node: _Node, *, skip_controls: bool = False) -> str:
    if skip_controls and node.tag in _CONTROL_TAGS:
        return ""
    parts = list(node.text)
    for child in node.children:
        parts.append(_visible_text(child, skip_controls=skip_controls))
    return " ".join(p for p in parts if p and p.strip()).strip()


def _is_control(node: _Node) -> bool:
    if node.tag not in _CONTROL_TAGS:
        return False
    if node.tag == "input" and (node.attrs.get("type") or "text").lower() in _SKIP_INPUT_TYPES:
        return False
    cur = node.parent
    while cur is not None:
        if cur.tag in _IGNORE_CONTROL_ANCESTORS:
            return False
        cur = cur.parent
    return True


def _controls(root: _Node) -> list[_Node]:
    return [n for n in _walk(root) if _is_control(n)]


def _by_id(root: _Node, eid: str) -> _Node | None:
    if not eid:
        return None
    for n in _walk(root):
        if n.attrs.get("id") == eid:
            return n
    return None


def _has_outside_label(control: _Node, root: _Node) -> bool:
    cid = control.attrs.get("id") or ""
    if cid:
        for n in _walk(root):
            if n.tag == "label" and n.attrs.get("for") == cid:
                if _visible_text(n, skip_controls=True):
                    return True
    cur = control.parent
    while cur is not None:
        if cur.tag == "label" and _visible_text(cur, skip_controls=True):
            return True
        cur = cur.parent
    labelledby = (control.attrs.get("aria-labelledby") or "").split()
    for ref in labelledby:
        target = _by_id(root, ref)
        if target is not None and _visible_text(target, skip_controls=True):
            return True
    return False


def _outside_labels_for_controls(content: str, target_type: str) -> Verdict:
    """Pass if every gradeable control has a visible outside label; fail if any do not.

    No controls → pass (vacuous). Placeholder / aria-label alone do not count.
    """
    root = _parse(content, target_type)
    found = _controls(root)
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
