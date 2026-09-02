from __future__ import annotations

from pathlib import Path

from open_ux.audit import INCOMPLETE_DESCRIPTION, INCOMPLETE_NO_CHECKER, audit
from open_ux.catalog import load_catalog
from open_ux.settings import Settings


VISIBLE = "forms.field_labels.visible_label"
STAYS = "forms.field_labels.label_stays_visible"
ERROR = "forms.field_labels.error_identifies_and_fixes"


def _catalog(_live_catalog: Path):
    return load_catalog(Settings.load())


def _row(result: dict, guideline_id: str) -> dict:
    matches = [r for r in result["results"] if r["guideline_id"] == guideline_id]
    assert len(matches) == 1
    return matches[0]


def _reasons_blob(row: dict) -> str:
    return " ".join(row.get("reasons") or [])


def test_visible_label_pass_html_for(live_catalog: Path) -> None:
    html = '<form><label for="email">Email</label><input id="email" type="email"></form>'
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content=html,
        guideline_ids=[VISIBLE],
    )
    row = _row(result, VISIBLE)
    assert row["verdict"] == "pass"
    assert row["reasons"]
    assert result["summary"]["pass"] == 1


def test_visible_label_pass_wrapping_label(live_catalog: Path) -> None:
    html = "<form><label>Name <input type='text'></label></form>"
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content=html,
        guideline_ids=[VISIBLE],
    )
    assert _row(result, VISIBLE)["verdict"] == "pass"


def test_visible_label_pass_aria_labelledby(live_catalog: Path) -> None:
    html = (
        '<form><span id="lbl">Phone</span>'
        '<input type="tel" aria-labelledby="lbl"></form>'
    )
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content=html,
        guideline_ids=[VISIBLE],
    )
    assert _row(result, VISIBLE)["verdict"] == "pass"


def test_visible_label_fail_placeholder_only(live_catalog: Path) -> None:
    html = '<form><input type="email" placeholder="Email"></form>'
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content=html,
        guideline_ids=[VISIBLE],
    )
    row = _row(result, VISIBLE)
    assert row["verdict"] == "fail"
    assert any("outside label" in r.lower() for r in row["reasons"])


def test_visible_label_fail_aria_label_only(live_catalog: Path) -> None:
    html = '<form><input type="text" aria-label="Search"></form>'
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content=html,
        guideline_ids=[VISIBLE],
    )
    assert _row(result, VISIBLE)["verdict"] == "fail"


def test_visible_label_empty_form_vacuous_pass(live_catalog: Path) -> None:
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content="<form></form>",
        guideline_ids=[VISIBLE],
    )
    assert _row(result, VISIBLE)["verdict"] == "pass"


def test_visible_label_jsx(live_catalog: Path) -> None:
    jsx = (
        "export function Form() {\n"
        "  return (<form><label htmlFor='email'>Email</label>"
        "<input id='email' type='email' /></form>);\n"
        "}\n"
    )
    result = audit(
        _catalog(live_catalog),
        target_type="jsx",
        content=jsx,
        guideline_ids=[VISIBLE],
    )
    assert _row(result, VISIBLE)["verdict"] == "pass"


def test_visible_label_jsx_unlabeled_fails(live_catalog: Path) -> None:
    jsx = "export default () => <form><input type='text' placeholder='Name' /></form>"
    result = audit(
        _catalog(live_catalog),
        target_type="jsx",
        content=jsx,
        guideline_ids=[VISIBLE],
    )
    assert _row(result, VISIBLE)["verdict"] == "fail"


def test_label_stays_visible_same_association(live_catalog: Path) -> None:
    html = '<form><label for="q">Query</label><input id="q"></form>'
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content=html,
        guideline_ids=[STAYS],
    )
    assert _row(result, STAYS)["verdict"] == "pass"


def test_llm_judgment_seed_stays_incomplete(live_catalog: Path) -> None:
    html = (
        '<form><label for="e">Email</label><input id="e">'
        "<p>Error: use a work address.</p></form>"
    )
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content=html,
        guideline_ids=[ERROR],
    )
    row = _row(result, ERROR)
    assert row["verdict"] == "incomplete"
    assert INCOMPLETE_NO_CHECKER in _reasons_blob(row)
    assert row["pass_when"]
    assert row["fail_when"]


def test_unknown_guideline_incomplete(live_catalog: Path) -> None:
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content="<form></form>",
        guideline_ids=["does.not.exist"],
    )
    row = _row(result, "does.not.exist")
    assert row["verdict"] == "incomplete"
    assert "Unknown guideline_id" in _reasons_blob(row)


def test_description_only_incomplete(live_catalog: Path) -> None:
    result = audit(
        _catalog(live_catalog),
        target_type="description",
        content="a login form with email and password",
        guideline_ids=[VISIBLE],
    )
    row = _row(result, VISIBLE)
    assert row["verdict"] == "incomplete"
    assert INCOMPLETE_DESCRIPTION in _reasons_blob(row)


def test_no_checker_deterministic_incomplete(live_catalog: Path) -> None:
    catalog = _catalog(live_catalog)
    other = next(
        g
        for g in catalog.guidelines
        if g.get("check") == "deterministic" and g["id"] not in {VISIBLE, STAYS}
    )
    result = audit(
        catalog,
        target_type="html",
        content="<form><input type='text'></form>",
        guideline_ids=[other["id"]],
    )
    row = _row(result, other["id"])
    assert row["verdict"] == "incomplete"
    assert row["pass_when"]
    assert row["fail_when"]
    assert INCOMPLETE_NO_CHECKER in _reasons_blob(row)


def test_jobs_scope_still_works(live_catalog: Path) -> None:
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content="<form></form>",
        jobs=["forms"],
    )
    ids = {row["guideline_id"] for row in result["results"]}
    assert ids
    assert all(i.startswith("forms.") for i in ids)
    assert VISIBLE in ids
    assert _row(result, VISIBLE)["verdict"] == "pass"
    assert _row(result, ERROR)["verdict"] == "incomplete"
