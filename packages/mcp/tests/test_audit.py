from __future__ import annotations

from pathlib import Path

from open_ux.audit import NEED_ERROR, PACK_KEYS, audit
from open_ux.catalog import EMPTY_NOTE, load_catalog, select_by_jobs
from open_ux.jobs import DEFAULT_LIMIT, MISS_NOTE
from open_ux.settings import Settings

VISIBLE = "ant.checkbox-vs-switch"
ERROR = "govuk.error-summary-plus-per-field"
OVERLAY = "mui.non-modal-dialogs-allowed"
DENSE = "forms.labels.clickable"


def _catalog(_live_catalog: Path):
    return load_catalog(Settings.load())


def _assert_pack_row(row: dict) -> None:
    assert set(row) == set(PACK_KEYS)
    assert row["id"]
    assert row["title"]
    assert row["name"]
    assert row["rule"]
    assert row["pass_when"]
    assert row["fail_when"]
    assert "verdict" not in row
    assert "reasons" not in row


def test_jobs_card_returns_criteria_without_content(live_catalog: Path) -> None:
    result = audit(_catalog(live_catalog), jobs="design_a_form")
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


def test_query_reranks_but_never_narrows_within_job(live_catalog: Path) -> None:
    """query is a soft re-rank, never a filter (OUX-21, finding #4).

    A caller who narrows with `query` must never see fewer guidelines than
    the same `jobs` call with no query at all -- the content exists either
    way, only the order changes. Uses a job whose full guideline set fits
    under `limit` so the capped output is directly comparable; a job whose
    total exceeds `limit` legitimately has a different capped *window* once
    reranked (the match moves to the front and displaces the previous
    boundary item), which is expected and is not what this test checks.
    """
    target = "actions.action_panel"
    wide = audit(_catalog(live_catalog), jobs="design_actions_and_ctas", limit=50)
    narrow = audit(
        _catalog(live_catalog),
        jobs="design_actions_and_ctas",
        query="action panel",
        limit=50,
    )
    assert wide["total"] < 50  # sanity: nothing capped away in either call
    assert narrow["total"] == wide["total"]
    assert {row["id"] for row in narrow["guidelines"]} == {
        row["id"] for row in wide["guidelines"]
    }
    ids = [row["id"] for row in narrow["guidelines"]]
    assert target in ids
    assert ids.index(target) == 0


def test_query_that_matches_nothing_falls_open(live_catalog: Path) -> None:
    """A query with zero literal matches still returns the full job set.

    This is the direct fix for finding #4: narrowing a real, non-empty
    result down to zero via a query string is never acceptable -- a caller
    who tries to narrow with natural phrasing must never get a worse
    result than one who omits `query` entirely.
    """
    wide = audit(_catalog(live_catalog), jobs="handle_form_errors")
    narrowed = audit(
        _catalog(live_catalog),
        jobs="handle_form_errors",
        query="red border no message",
    )
    assert wide["total"] >= 1
    assert narrowed["total"] == wide["total"]
    assert narrowed["count"] == wide["count"]
    assert narrowed["note"] and "showing all" in narrowed["note"]


def test_limit_caps_pack(live_catalog: Path) -> None:
    result = audit(_catalog(live_catalog), jobs="forms", limit=3)
    assert result["count"] == 3
    assert result["total"] > 3


def test_leaf_id_is_not_a_need(live_catalog: Path) -> None:
    result = audit(_catalog(live_catalog), jobs="avoid_placeholder_as_label")
    assert result["guidelines"] == []
    assert result["count"] == 0
    assert result["total"] == 0
    assert result["note"] == MISS_NOTE


def test_live_seeds_resolve_through_their_cards(live_catalog: Path) -> None:
    form = audit(_catalog(live_catalog), jobs="design_a_form", limit=50)
    errors = audit(_catalog(live_catalog), jobs="handle_form_errors", limit=50)
    form_ids = {row["id"] for row in form["guidelines"]}
    error_ids = {row["id"] for row in errors["guidelines"]}
    assert VISIBLE in form_ids
    assert "forms.labels.clickable" in form_ids
    assert ERROR in error_ids
    assert VISIBLE not in error_ids


def test_cluster_only_cards_return_pointer_criteria(live_catalog: Path) -> None:
    display = audit(_catalog(live_catalog), jobs="compose_a_data_display", limit=50)
    overlay = audit(_catalog(live_catalog), jobs="choose_an_overlay", limit=50)
    steps = audit(_catalog(live_catalog), jobs="build_a_multi_step_flow", limit=50)
    display_ids = {row["id"] for row in display["guidelines"]}
    overlay_ids = {row["id"] for row in overlay["guidelines"]}
    step_ids = {row["id"] for row in steps["guidelines"]}
    assert "nsw.charts-start-with-story" in display_ids
    assert OVERLAY in overlay_ids
    assert "nl.step-n-of-m-in-title-and-above-form" in step_ids
    assert display["count"] >= 1
    assert "verdict" not in display
    for row in display["guidelines"]:
        _assert_pack_row(row)


def test_container_without_leaves_uses_card_pointers(live_catalog: Path) -> None:
    result = audit(_catalog(live_catalog), jobs="layout_and_data_display", limit=50)
    ids = {row["id"] for row in result["guidelines"]}
    assert "nsw.charts-start-with-story" in ids


def test_dense_card_includes_cluster_pointers(live_catalog: Path) -> None:
    selected = select_by_jobs(_catalog(live_catalog), "design_a_form")
    ids = {row["id"] for row in selected}
    assert VISIBLE in ids
    assert DENSE in ids


def test_empty_catalog_is_honest(tmp_env: Path) -> None:
    catalog = load_catalog(Settings.load())
    result = audit(catalog, jobs="forms")
    assert result["guidelines"] == []
    assert result["note"] == EMPTY_NOTE
    assert "verdict" not in result
