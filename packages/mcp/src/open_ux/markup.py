"""Live markup for Hybrid C graders. Stdlib only. No JS evaluation.

A checker sees a tree of what can appear on screen, not the source file.

HTML
    The source is the tree. ``<!-- -->`` is not a node.

JSX
    Live: JSX tags and their text children, including tags inside ``{…}``.
    Not live: JS comments, JS / template string bodies.
    Attribute values (including ``https://``) stay on the tag.
    Text children keep ``https://`` — that is not a comment.

Live control
    ``input`` / ``textarea`` / ``select`` that is a field on the page.
    Not: hidden / submit / button / reset / image.
    Not: descendants of ``script``, ``style``, ``template``, ``textarea``.

Out of scope: evaluating ``{cond}`` (inner JSX is treated as live),
regex literals that look like tags.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser

VOID = frozenset(
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
FIELD_TAGS = frozenset({"input", "textarea", "select"})
NON_FIELD_INPUT = frozenset({"hidden", "submit", "button", "reset", "image"})
INERT_PARENTS = frozenset({"script", "style", "template", "textarea"})


class Node:
    __slots__ = ("tag", "attrs", "parent", "children", "text")

    def __init__(self, tag: str, attrs: dict[str, str], parent: Node | None) -> None:
        self.tag = tag
        self.attrs = attrs
        self.parent = parent
        self.children: list[Node] = []
        self.text: list[str] = []


def parse_markup(content: str, target_type: str) -> Node:
    if target_type not in {"html", "jsx"}:
        raise ValueError("markup target must be html or jsx")
    html = content if target_type == "html" else _jsx_to_html(content)
    parser = _TreeParser()
    parser.feed(f"<div>{html}</div>")
    parser.close()
    return parser.root


def walk(node: Node) -> list[Node]:
    out = [node]
    for child in node.children:
        out.extend(walk(child))
    return out


def live_controls(root: Node) -> list[Node]:
    return [n for n in walk(root) if is_live_control(n)]


def is_live_control(node: Node) -> bool:
    if node.tag not in FIELD_TAGS:
        return False
    if node.tag == "input" and (node.attrs.get("type") or "text").lower() in NON_FIELD_INPUT:
        return False
    cur = node.parent
    while cur is not None:
        if cur.tag in INERT_PARENTS:
            return False
        cur = cur.parent
    return True


def visible_text(node: Node, *, skip_controls: bool = False) -> str:
    if skip_controls and node.tag in FIELD_TAGS:
        return ""
    parts = list(node.text)
    for child in node.children:
        parts.append(visible_text(child, skip_controls=skip_controls))
    return " ".join(p for p in parts if p and p.strip()).strip()


def find_by_id(root: Node, eid: str) -> Node | None:
    if not eid:
        return None
    for n in walk(root):
        if n.attrs.get("id") == eid:
            return n
    return None


# --- HTML tree --------------------------------------------------------------


class _TreeParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {}, None)
        self._cur = self.root

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag.lower(), {k.lower(): (v or "") for k, v in attrs}, self._cur)
        self._cur.children.append(node)
        if tag.lower() not in VOID:
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


# --- JSX → HTML (live elements only) ----------------------------------------


def _jsx_to_html(src: str) -> str:
    html = _JsxLive(src).html()
    html = re.sub(r"\bhtmlFor=", "for=", html)
    html = re.sub(r"\bclassName=", "class=", html)
    html = re.sub(r"/>", ">", html)
    return html


class _JsxLive:
    """One pass: script vs JSX tag vs JSX children.

    In script (module scope, or ``{…}`` inside JSX): comments and strings
    die; a ``<`` tag starts live markup.
    In a tag: copy the tag, including quoted attributes.
    In children: keep text; ``{`` re-enters script; a tag is live.
    """

    def __init__(self, src: str) -> None:
        self.src = src
        self.i = 0
        self.n = len(src)
        self.out: list[str] = []
        self.child_depth = 0
        self.expr_depth = 0

    def html(self) -> str:
        while self.i < self.n:
            if self._in_script() and self._skip_comment():
                continue
            if self._in_script() and self._skip_string():
                continue
            ch = self._ch()
            if self.child_depth > 0 and ch == "{":
                self.expr_depth += 1
                self.i += 1
                continue
            if self.expr_depth > 0 and ch == "}":
                self.expr_depth -= 1
                self.i += 1
                continue
            if self._at_tag():
                self._copy_tag()
                continue
            if self.child_depth > 0 and self.expr_depth == 0:
                self.out.append(ch)
            self.i += 1
        return "".join(self.out)

    def _ch(self, k: int = 0) -> str:
        j = self.i + k
        return self.src[j] if j < self.n else ""

    def _in_script(self) -> bool:
        return self.child_depth == 0 or self.expr_depth > 0

    def _at_tag(self) -> bool:
        if self._ch() != "<":
            return False
        nxt = self._ch(1)
        return nxt.isalpha() or nxt in "/!"

    def _skip_comment(self) -> bool:
        if self._ch() != "/" or self.i + 1 >= self.n:
            return False
        nxt = self._ch(1)
        if nxt == "/":
            self.i += 2
            while self.i < self.n and self.src[self.i] != "\n":
                self.i += 1
            return True
        if nxt == "*":
            self.i += 2
            while self.i + 1 < self.n and not (
                self.src[self.i] == "*" and self.src[self.i + 1] == "/"
            ):
                self.i += 1
            self.i = min(self.n, self.i + 2)
            return True
        return False

    def _skip_string(self) -> bool:
        quote = self._ch()
        if quote not in {"'", '"', "`"}:
            return False
        self.i += 1
        while self.i < self.n:
            ch = self.src[self.i]
            if ch == "\\" and self.i + 1 < self.n:
                self.i += 2
                continue
            if ch == quote:
                self.i += 1
                return True
            self.i += 1
        return True

    def _copy_tag(self) -> None:
        start = self.i
        self.i += 1
        close = self._ch() == "/"
        if close:
            self.i += 1
        name_at = self.i
        while self.i < self.n and (self.src[self.i].isalnum() or self.src[self.i] in "-_:"):
            self.i += 1
        name = self.src[name_at : self.i].lower()
        self_close = False
        quote: str | None = None
        braces = 0
        while self.i < self.n:
            ch = self.src[self.i]
            if quote:
                if ch == "\\" and self.i + 1 < self.n:
                    self.i += 2
                    continue
                if ch == quote:
                    quote = None
                self.i += 1
                continue
            if ch in {"'", '"'}:
                quote = ch
                self.i += 1
                continue
            if ch == "{":
                braces += 1
                self.i += 1
                continue
            if ch == "}" and braces:
                braces -= 1
                self.i += 1
                continue
            if braces:
                self.i += 1
                continue
            if ch == "/" and self._ch(1) == ">":
                self_close = True
                self.i += 2
                break
            if ch == ">":
                self.i += 1
                break
            self.i += 1
        self.out.append(self.src[start : self.i])
        if close:
            self.child_depth = max(0, self.child_depth - 1)
        elif not self_close and name not in VOID:
            self.child_depth += 1
