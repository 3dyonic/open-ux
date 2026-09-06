from __future__ import annotations

from pathlib import Path

from open_ux.audit import NEED_ERROR, PACK_KEYS, audit
from open_ux.catalog import EMPTY_NOTE, load_catalog
from open_ux.jobs import DEFAULT_LIMIT, MISS_NOTE
from open_ux.settings import Settings

VISIBLE = "forms.field_labels.visible_label"
ERROR = "forms.field_labels.error_identifies_and_fixes"


def _catalog(_live_catalog: Path):
    return load_catalog(Settings.load())


def _assert_pack_row(row: dict) -> None:
    assert set(row) == set(PACK_KEYS)
    assert row["id"]
    assert row["title"]
    assert row["rule"]
    assert row["pass_when"]
    assert row["fail_when"]
    assert "verdict" not in row
    assert "reasons" not in row


def test_jobs_template_returns_criteria_without_content(live_catalog: Path) -> None:
    result = audit(_catalog(live_catalog), jobs="avoid_placeholder_as_label")
    assert "error" not in result
    assert "verdict" not in result
    assert "summary" not in result
    assert result["count"] == len(result["guidelines"])
    assert result["total"] >= result["count"]
    assert result["count"] >= 1
    assert result["count"] <= DEFAULT_LIMIT
    for row in result["guidelines"]:
        _assert_pack_row(row)


def test_jobs_forms_alias_includes_live_seeds(live_catalog: Path) -> None:
    result = audit(_catalog(live_catalog), jobs="forms", limit=50)
    ids = {row["id"] for row in result["guidelines"]}
    assert VISIBLE in ids
    assert ERROR in ids
    assert all(not row["id"].startswith("actions.") for row in result["guidelines"])
    _assert_pack_row(next(r for r in result["guidelines"] if r["id"] == VISIBLE))


def test_guideline_ids_return_those_rules(live_catalog: Path) -> None:
    result = audit(
        _catalog(live_catalog),
        guideline_ids=[VISIBLE, "actions.button_groups"],
    )
    assert [row["id"] for row in result["guidelines"]] == [
        VISIBLE,
        "actions.button_groups",
    ]
    assert result["count"] == 2
    assert result["total"] == 2
    for row in result["guidelines"]:
        _assert_pack_row(row)


def test_unknown_id_is_empty_not_invented(live_catalog: Path) -> None:
    result = audit(_catalog(live_catalog), guideline_ids=["does.not.exist"])
    assert result["guidelines"] == []
    assert result["count"] == 0
    assert result["total"] == 0
    assert result["note"] == MISS_NOTE
    assert "verdict" not in result


def test_requires_need(live_catalog: Path) -> None:
    result = audit(_catalog(live_catalog))
    assert NEED_ERROR in result["error"]
    assert result["guidelines"] == []
    assert result["count"] == 0


def test_leftover_target_is_ignored(live_catalog: Path) -> None:
    result = audit(
        _catalog(live_catalog),
        jobs="forms",
        target={"type": "html", "content": "<input placeholder='Email'>"},
        content="<form></form>",
        target_type="html",
        limit=5,
    )
    assert result["count"] >= 1
    assert "verdict" not in result
    for row in result["guidelines"]:
        _assert_pack_row(row)


def test_query_narrows_within_job(live_catalog: Path) -> None:
    wide = audit(_catalog(live_catalog), jobs="forms", limit=50)
    narrow = audit(
        _catalog(live_catalog),
        jobs="forms",
        query="visible label",
        limit=50,
    )
    assert narrow["total"] < wide["total"]
    assert narrow["total"] >= 1
    assert any(row["id"] == VISIBLE for row in narrow["guidelines"])


def test_limit_caps_pack(live_catalog: Path) -> None:
    result = audit(_catalog(live_catalog), jobs="forms", limit=3)
    assert result["count"] == 3
    assert result["total"] > 3


def test_empty_catalog_is_honest(tmp_env: Path) -> None:
    catalog = load_catalog(Settings.load())
    result = audit(catalog, jobs="forms")
    assert result["guidelines"] == []
    assert result["note"] == EMPTY_NOTE
    assert "verdict" not in result
