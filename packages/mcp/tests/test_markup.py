from __future__ import annotations

from open_ux.markup import live_controls, parse_markup, visible_text, walk


def _fields(content: str, target_type: str) -> list[tuple[str, str]]:
    root = parse_markup(content, target_type)
    out = []
    for n in live_controls(root):
        out.append((n.tag, n.attrs.get("id") or n.attrs.get("placeholder") or ""))
    return out


def test_html_is_the_tree() -> None:
    html = '<form><label for="e">Email</label><input id="e"></form>'
    assert _fields(html, "html") == [("input", "e")]


def test_html_comment_is_not_a_node() -> None:
    html = '<!-- <input placeholder="x"> --><label for="e">Email</label><input id="e">'
    assert _fields(html, "html") == [("input", "e")]


def test_inert_parents_are_not_live_fields() -> None:
    html = (
        '<label for="e">Email</label><input id="e">'
        '<template><input placeholder="x"></template>'
        '<label for="t">Notes</label><textarea id="t"><input placeholder="x"></textarea>'
        '<script><input placeholder="x"></script>'
    )
    assert _fields(html, "html") == [("input", "e"), ("textarea", "t")]


def test_hidden_and_submit_are_not_fields() -> None:
    html = '<input type="hidden" name="csrf"><input type="submit" value="Go"><input id="e">'
    assert _fields(html, "html") == [("input", "e")]


def test_jsx_source_is_not_the_tree() -> None:
    jsx = (
        "export function Form() {\n"
        "  return (<form><label htmlFor='e'>Email</label><input id='e' /></form>);\n"
        "}\n"
    )
    assert _fields(jsx, "jsx") == [("input", "e")]


def test_jsx_comments_and_strings_are_not_live() -> None:
    jsx = (
        '// old: <input placeholder="Name" />\n'
        "const old = '<input placeholder=\"Name\" />';\n"
        "const also = `<input placeholder=\"Name\" />`;\n"
        "<form>\n"
        "  {/* leftover: <input placeholder='Name' /> */}\n"
        "  <label htmlFor='e'>Email</label><input id='e' />\n"
        "</form>\n"
    )
    assert _fields(jsx, "jsx") == [("input", "e")]


def test_jsx_expression_tags_are_live() -> None:
    jsx = (
        "<form>\n"
        "  {show && <input placeholder='Name' />}\n"
        "  <label htmlFor='e'>Email</label><input id='e' />\n"
        "</form>\n"
    )
    assert _fields(jsx, "jsx") == [("input", "Name"), ("input", "e")]


def test_jsx_keeps_urls_in_attrs_and_text() -> None:
    jsx = (
        "<form>\n"
        "  <p>See https://example.com/labels</p>\n"
        "  <label htmlFor='e'>Email</label>\n"
        "  <input id='e' data-hint='https://example.com/x' />\n"
        "</form>\n"
    )
    root = parse_markup(jsx, "jsx")
    assert _fields(jsx, "jsx") == [("input", "e")]
    paras = [n for n in walk(root) if n.tag == "p"]
    assert paras and "https://example.com/labels" in visible_text(paras[0])
    hint = live_controls(root)[0].attrs.get("data-hint")
    assert hint == "https://example.com/x"
