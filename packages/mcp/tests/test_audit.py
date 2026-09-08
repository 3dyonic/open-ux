from __future__ import annotations

from pathlib import Path

from open_ux.audit import (
    HOST_CITATIONS_ONLY,
    NEED_ERROR,
    PACK_KEYS,
    _matches_query,
    _rerank_by_query,
    _stratify_by_facet,
    audit,
)
from open_ux.catalog import EMPTY_NOTE, get_by_id, load_catalog, select_by_jobs
from open_ux.jobs import (
    CARD_IDS,
    DEFAULT_LIMIT,
    MISS_NOTE,
    Card,
    Facet,
    JobTree,
    load_job_tree,
)
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
    assert row["overview"]
    assert row["rule"]
    assert "pass_when" not in row
    assert "fail_when" not in row
    assert "verdict" not in row
    assert "reasons" not in row


def _assert_contract(result: dict) -> None:
    assert result["host"] == HOST_CITATIONS_ONLY
    assert "verdict" not in result
    assert "summary" not in result


def test_jobs_card_returns_criteria_without_content(live_catalog: Path) -> None:
    result = audit(_catalog(live_catalog), jobs="design_a_form")
    assert "error" not in result
    _assert_contract(result)
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
        query="zxqv-not-a-guideline-token",
    )
    assert wide["total"] >= 1
    assert narrowed["total"] == wide["total"]
    assert narrowed["count"] == wide["count"]
    assert [row["id"] for row in narrowed["guidelines"]] == [
        row["id"] for row in wide["guidelines"]
    ]
    assert narrowed["note"] and "showing all" in narrowed["note"]
    assert narrowed["query_fallback"] is True


def test_limit_caps_pack(live_catalog: Path) -> None:
    result = audit(_catalog(live_catalog), jobs="forms", limit=3)
    assert result["count"] == 3
    assert result["total"] > 3
    assert result["omitted"] == result["total"] - 3
    assert result["next_offset"] == 3


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
    _assert_contract(display)
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


def _nonempty_facets(catalog, job: str) -> set[str]:
    return {
        str(row.get("facet") or "")
        for row in select_by_jobs(catalog, job)
        if row.get("facet")
    }


def test_design_a_form_default_covers_every_nonempty_facet(live_catalog: Path) -> None:
    catalog = _catalog(live_catalog)
    result = audit(catalog, jobs="design_a_form")
    ids = {row["id"] for row in result["guidelines"]}
    assert "fluent.helper-text-below" in ids
    assert "spectrum.asterisk-is-icon-not-label-text" in ids
    window = {row["facet"] for row in result["guidelines"]}
    assert _nonempty_facets(catalog, "design_a_form") <= window
    for row in result["guidelines"]:
        assert row["facet"]


def test_design_actions_default_covers_every_nonempty_facet(live_catalog: Path) -> None:
    catalog = _catalog(live_catalog)
    result = audit(catalog, jobs="design_actions_and_ctas")
    window = {row["facet"] for row in result["guidelines"]}
    assert _nonempty_facets(catalog, "design_actions_and_ctas") <= window


def test_query_phrase_token_any_does_not_fail_open(live_catalog: Path) -> None:
    catalog = _catalog(live_catalog)
    wide = audit(catalog, jobs="design_a_form")
    narrowed = audit(
        catalog,
        jobs="design_a_form",
        query="label required helper optional",
    )
    assert narrowed["total"] == wide["total"]
    assert not (narrowed.get("note") and "showing all" in narrowed["note"])


def test_query_helper_reorders_stratified_not_catalog(live_catalog: Path) -> None:
    catalog = _catalog(live_catalog)
    cap = DEFAULT_LIMIT
    scoped = select_by_jobs(catalog, "design_a_form")
    stratified = _stratify_by_facet(scoped, load_job_tree(), len(scoped) or 1)
    ranked, matched = _rerank_by_query(stratified, "helper")
    assert matched
    expected = [row["id"] for row in ranked][:cap]
    result = audit(catalog, jobs="design_a_form", query="helper")
    assert [row["id"] for row in result["guidelines"]] == expected


def test_token_any_required_false_positive_is_accepted(live_catalog: Path) -> None:
    """query='required' still matches ant.slider-intensity-grade ('precise number is required').

    OUX-24 accepted this as recall not precision. BM25 (OUX-26) does not
    promise to drop it either.
    """
    catalog = _catalog(live_catalog)
    slider = get_by_id(catalog, "ant.slider-intensity-grade")
    assert slider is not None
    assert _matches_query(slider, "required")
    result = audit(catalog, jobs="design_a_form", query="required")
    assert not (result.get("note") and "showing all" in result["note"])


def test_live_max_nonempty_facets_under_default_limit(live_catalog: Path) -> None:
    """Scaling limit: len(F) >= cap drops later facets. Today's Cards stay under cap."""
    catalog = _catalog(live_catalog)
    counts = [len(_nonempty_facets(catalog, cid)) for cid in CARD_IDS]
    assert max(counts) < DEFAULT_LIMIT


def _synthetic_tree(facet_ids: list[str]) -> JobTree:
    facets = tuple(Facet(id=fid, title=fid) for fid in facet_ids)
    card = Card(
        id="design_a_form",
        title="Design a form",
        container="forms_and_input",
        overview="",
        when=(),
        reject=(),
        hints=(),
        facets=facets,
    )
    return JobTree(containers=(), cards=(card,))


def _synthetic_rows(facet_ids: list[str], per: int) -> list[dict]:
    rows = []
    for fid in facet_ids:
        for index in range(per):
            rows.append(
                {
                    "id": f"{fid}-{index}",
                    "card": "design_a_form",
                    "facet": fid,
                }
            )
    return rows


def test_stratify_even_five_facets_cap_ten() -> None:
    facets = [f"f{i}" for i in range(5)]
    ordered = _stratify_by_facet(_synthetic_rows(facets, 3), _synthetic_tree(facets), 10)
    head = ordered[:10]
    counts = {fid: 0 for fid in facets}
    for row in head:
        counts[row["facet"]] += 1
    assert counts == {fid: 2 for fid in facets}


def test_stratify_uneven_four_facets_cap_ten() -> None:
    facets = [f"f{i}" for i in range(4)]
    ordered = _stratify_by_facet(_synthetic_rows(facets, 3), _synthetic_tree(facets), 10)
    head = ordered[:10]
    counts = {fid: 0 for fid in facets}
    for row in head:
        counts[row["facet"]] += 1
    assert counts == {"f0": 3, "f1": 3, "f2": 2, "f3": 2}


def test_stratify_seven_facets_quota_then_fill() -> None:
    facets = [f"f{i}" for i in range(7)]
    ordered = _stratify_by_facet(_synthetic_rows(facets, 2), _synthetic_tree(facets), 10)
    head = ordered[:10]
    counts = {fid: 0 for fid in facets}
    for row in head:
        counts[row["facet"]] += 1
    assert counts == {
        "f0": 2,
        "f1": 2,
        "f2": 2,
        "f3": 1,
        "f4": 1,
        "f5": 1,
        "f6": 1,
    }


def test_stratify_facets_exceed_cap_drops_later_facets() -> None:
    """Known scaling limit (OUX-24): len(F) >= cap → 1 from each of the first cap only."""
    facets = [f"f{i}" for i in range(12)]
    ordered = _stratify_by_facet(_synthetic_rows(facets, 1), _synthetic_tree(facets), 10)
    head = ordered[:10]
    assert [row["facet"] for row in head] == [f"f{i}" for i in range(10)]
    assert "f10" not in {row["facet"] for row in head}
    assert "f11" not in {row["facet"] for row in head}


def test_compose_sign_in_returns_cited_show_password(live_catalog: Path) -> None:
    result = audit(_catalog(live_catalog), jobs="compose_sign_in")
    assert result["total"] >= 1
    assert result["count"] >= 1
    ids = {row["id"] for row in result["guidelines"]}
    assert "govuk.hide-password-by-default-show-toggle" in ids
    assert "forms.inputs.password_strength_meter" not in ids
    for row in result["guidelines"]:
        _assert_pack_row(row)
        assert row["facet"] == "credentials_are_hard_to_enter"


def test_data_display_lazy_loads_white_canvas(live_catalog: Path) -> None:
    catalog = _catalog(live_catalog)
    first = audit(catalog, jobs="compose_a_data_display")
    _assert_contract(first)
    assert first["count"] == 10
    assert first["total"] == 13
    assert first["omitted"] == 3
    assert first["next_offset"] == 10
    assert first["limit"] == 10
    assert first["offset"] == 0
    assert "3 more not shown" in first["omitted_hint"]
    assert "offset=10" in first["omitted_hint"]
    page1 = {row["id"] for row in first["guidelines"]}
    second = audit(catalog, jobs="compose_a_data_display", offset=10)
    _assert_contract(second)
    assert second["count"] == 3
    assert second["total"] == 13
    assert "omitted" not in second
    assert "next_offset" not in second
    page2 = {row["id"] for row in second["guidelines"]}
    assert page1.isdisjoint(page2)
    assert "nsw.white-canvas-single-colour-when-labelled" in page1 | page2


def test_design_a_form_walks_every_page(live_catalog: Path) -> None:
    catalog = _catalog(live_catalog)
    seen: list[str] = []
    offset = 0
    total = None
    pages = 0
    while True:
        result = audit(catalog, jobs="design_a_form", offset=offset)
        _assert_contract(result)
        if total is None:
            total = result["total"]
            assert total > DEFAULT_LIMIT
        assert result["total"] == total
        ids = [row["id"] for row in result["guidelines"]]
        assert not set(ids) & set(seen)
        seen.extend(ids)
        pages += 1
        nxt = result.get("next_offset")
        if nxt is None:
            break
        offset = nxt
    assert len(seen) == total
    assert pages >= 2
    assert offset >= DEFAULT_LIMIT


def test_query_fallback_stays_paged(live_catalog: Path) -> None:
    result = audit(
        _catalog(live_catalog),
        jobs="design_a_form",
        query="zxqv-not-a-guideline-token",
    )
    assert result["query_fallback"] is True
    assert result["count"] == DEFAULT_LIMIT
    assert result["omitted"] == result["total"] - DEFAULT_LIMIT
    assert result["next_offset"] == DEFAULT_LIMIT
