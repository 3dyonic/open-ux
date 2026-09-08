"""OUX-21 completeness for suggest_situations.

The fixture asserts the expected Card is on the catalog map. It does not
assert #1: the tool is a lock-order map, not a ranker.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from open_ux.jobs import CARD_IDS, CONTAINER_IDS, load_job_tree
from open_ux.settings import Settings
from open_ux.situations import suggest_card_ids, suggest_situations

FIXTURE = Path(__file__).parent / "fixtures" / "situation_queries.json"
ROWS = json.loads(FIXTURE.read_text(encoding="utf-8"))


def _tree(live_catalog: Path):
    return load_job_tree(Settings.load())


def _row_by_id(result: dict, card_id: str) -> dict:
    for container in result["containers"]:
        for row in container["situations"]:
            if row["id"] == card_id:
                return row
    raise AssertionError(f"{card_id} missing from menu")


@pytest.mark.parametrize("row", ROWS, ids=[r["query"][:40] for r in ROWS])
def test_expected_card_present(live_catalog: Path, row: dict) -> None:
    tree = _tree(live_catalog)
    result = suggest_situations(row["query"], row.get("surface"), tree=tree)
    ids = suggest_card_ids(result)
    assert row["expected_card"] in ids, (
        f"{row['expected_card']!r} missing for {row['query']!r} "
        f"({row['note']}) -- got {ids}"
    )
    _row_by_id(result, row["expected_card"])


def test_menu_order_is_catalog_lock(live_catalog: Path) -> None:
    tree = _tree(live_catalog)
    a = suggest_situations("qwerty zxcvbn asdfgh", tree=tree)
    b = suggest_situations("can they go back and change an earlier answer", tree=tree)
    assert suggest_card_ids(a) == list(CARD_IDS)
    assert suggest_card_ids(b) == list(CARD_IDS)
    assert [c["id"] for c in a["containers"]] == list(CONTAINER_IDS)


def test_no_accept_reject_contradiction_is_possible(live_catalog: Path) -> None:
    tree = _tree(live_catalog)
    for row in ROWS:
        result = suggest_situations(row["query"], row.get("surface"), tree=tree)
        assert "rejected" not in result
        ids = suggest_card_ids(result)
        assert len(ids) == len(set(ids))
        assert set(ids) == set(CARD_IDS)
        dumped = str(result)
        assert "caution" not in dumped


def test_fixture_covers_every_card_at_least_once() -> None:
    covered = {row["expected_card"] for row in ROWS}
    assert covered
    assert covered <= set(CARD_IDS)
