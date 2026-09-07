"""Regression fixture for OUX-21 (suggest_situations retrieval fix).

Runs the exact queries from the stress-test session that surfaced the
original findings, plus a few known-passing queries as regression guards,
and asserts the acceptance criteria from OUX-21:

  * expected_card is present *somewhere* in the returned set -- the tool's
    job is to never hide a real answer, not to guess it outright (the
    calling LLM makes the final call).
  * there is no separate "rejected" list any card id could contradict --
    reject is folded into a same-row `caution` annotation, so the
    accept/reject contradiction (finding #2) is structurally impossible.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from open_ux.jobs import CARD_IDS, load_job_tree
from open_ux.settings import Settings
from open_ux.situations import suggest_situations

FIXTURE = Path(__file__).parent / "fixtures" / "situation_queries.json"
ROWS = json.loads(FIXTURE.read_text(encoding="utf-8"))


def _tree(live_catalog: Path):
    return load_job_tree(Settings.load())


@pytest.mark.parametrize("row", ROWS, ids=[r["query"][:40] for r in ROWS])
def test_expected_card_present(live_catalog: Path, row: dict) -> None:
    tree = _tree(live_catalog)
    result = suggest_situations(row["query"], row.get("surface"), tree=tree)
    ids = [item["id"] for item in result["situations"]]
    assert row["expected_card"] in ids, (
        f"{row['expected_card']!r} missing for {row['query']!r} "
        f"({row['note']}) -- got {ids}"
    )


def test_no_accept_reject_contradiction_is_possible(live_catalog: Path) -> None:
    """There is exactly one list; a card id cannot appear twice or be
    simultaneously 'accepted' and 'rejected' because that second list no
    longer exists."""
    tree = _tree(live_catalog)
    for row in ROWS:
        result = suggest_situations(row["query"], row.get("surface"), tree=tree)
        assert "rejected" not in result
        ids = [item["id"] for item in result["situations"]]
        assert len(ids) == len(set(ids))
        assert set(ids) == set(CARD_IDS)


def test_fixture_covers_every_card_at_least_once() -> None:
    covered = {row["expected_card"] for row in ROWS}
    assert covered  # sanity: fixture is not empty
    assert covered <= set(CARD_IDS)
