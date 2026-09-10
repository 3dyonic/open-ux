from open_ux.bm25 import blob_scores, pack_blob, rank_blobs, rank_pack


def test_phrase_hit_outranks_token_only() -> None:
    blobs = [
        "unrelated token soup about buttons",
        "the action panel pattern for commands",
        "panel only in passing",
    ]
    order, matched = rank_blobs("action panel", blobs)
    assert matched
    assert blobs[order[0]] == "the action panel pattern for commands"


def test_zero_hits_keep_input_order() -> None:
    blobs = ["alpha", "beta", "gamma"]
    order, matched = rank_blobs("zxqv-not-a-token", blobs)
    assert matched is False
    assert order == [0, 1, 2]


def test_blob_scores_are_positive_only_on_hits() -> None:
    blobs = ["delete a teammate from the workspace", "breadcrumb navigation"]
    scores = blob_scores("removing a teammate", blobs)
    assert scores[0] > 0
    assert scores[1] == 0 or scores[0] > scores[1]


def test_pack_blob_uses_overview_hints_not_pass_when() -> None:
    blob = pack_blob(
        {
            "id": "ant.one-cta-per-screen",
            "overview": "Landing and welcome screens carry one command-like Call to Action.",
            "hints": ["landing", "welcome", "cta"],
            "component": ["button"],
            "pass_when": ["this must not be in the pack blob"],
        }
    )
    assert "landing" in blob
    assert "button" in blob
    assert "this must not be in the pack blob" not in blob


def test_rank_pack_fail_open_no_scores() -> None:
    payload = {
        "guidelines": [
            {"id": "a", "overview": "alpha"},
            {"id": "b", "overview": "beta"},
        ],
        "count": 2,
        "total": 2,
        "host": "citations_only",
    }
    ranked = rank_pack(payload, "zxqv-not-a-token")
    assert [row["id"] for row in ranked["guidelines"]] == ["a", "b"]
    assert ranked["query_fallback"] is True
    assert "score" not in ranked["guidelines"][0]


def test_rank_pack_orders_by_overview() -> None:
    payload = {
        "guidelines": [
            {"id": "nav", "overview": "Sidebar and breadcrumbs."},
            {"id": "cta", "overview": "Landing welcome command CTA."},
        ]
    }
    ranked = rank_pack(payload, "landing cta")
    assert ranked["guidelines"][0]["id"] == "cta"
    assert "query_fallback" not in ranked
