from open_ux.bm25 import blob_scores, rank_blobs


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
