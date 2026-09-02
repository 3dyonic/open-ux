from __future__ import annotations

from pathlib import Path

from open_ux.audit import INCOMPLETE, audit
from open_ux.catalog import load_catalog
from open_ux.settings import Settings

VISIBLE = "forms.field_labels.visible_label"
ERROR = "forms.field_labels.error_identifies_and_fixes"
LABELED = '<form><label for="email">Email</label><input id="email" type="email"></form>'
UNLABELED = '<form><input type="email" placeholder="Email"></form>'


def _catalog(_live_catalog: Path):
    return load_catalog(Settings.load())


def _row(result: dict, guideline_id: str) -> dict:
    matches = [r for r in result["results"] if r["guideline_id"] == guideline_id]
    assert len(matches) == 1
    return matches[0]


def _is_criteria_pack(row: dict) -> None:
    assert row["verdict"] == "incomplete"
    assert row["pass_when"]
    assert row["fail_when"]
    assert row["rule"]
    assert INCOMPLETE in " ".join(row.get("reasons") or [])


def test_labeled_html_is_not_host_graded(live_catalog: Path) -> None:
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content=LABELED,
        guideline_ids=[VISIBLE],
    )
    _is_criteria_pack(_row(result, VISIBLE))
    assert result["summary"] == {"pass": 0, "fail": 0, "incomplete": 1}


def test_unlabeled_html_is_not_host_graded(live_catalog: Path) -> None:
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content=UNLABELED,
        guideline_ids=[VISIBLE],
    )
    _is_criteria_pack(_row(result, VISIBLE))


def test_jsx_is_not_host_graded(live_catalog: Path) -> None:
    result = audit(
        _catalog(live_catalog),
        target_type="jsx",
        content="<form><input placeholder='Name' /></form>",
        guideline_ids=[VISIBLE],
    )
    _is_criteria_pack(_row(result, VISIBLE))


def test_description_is_criteria_pack(live_catalog: Path) -> None:
    result = audit(
        _catalog(live_catalog),
        target_type="description",
        content="a login form with email and password",
        guideline_ids=[VISIBLE],
    )
    _is_criteria_pack(_row(result, VISIBLE))


def test_unknown_guideline_incomplete(live_catalog: Path) -> None:
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content="<form></form>",
        guideline_ids=["does.not.exist"],
    )
    row = _row(result, "does.not.exist")
    assert row["verdict"] == "incomplete"
    assert "Unknown guideline_id" in " ".join(row.get("reasons") or [])


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
    assert ERROR in ids
    _is_criteria_pack(_row(result, VISIBLE))
    _is_criteria_pack(_row(result, ERROR))
    assert result["summary"]["pass"] == 0
    assert result["summary"]["fail"] == 0
    assert result["summary"]["incomplete"] == len(result["results"])


def test_requires_scope(live_catalog: Path) -> None:
    result = audit(
        _catalog(live_catalog),
        target_type="html",
        content="<form></form>",
    )
    assert "requires jobs or guideline_ids" in result["error"]
    assert result["results"] == []
