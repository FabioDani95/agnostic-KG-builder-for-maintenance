from scripts.kg_v3_contrastive import generate, score_contrasts


def test_contrastive_checks_distinct_identity_and_all_own_actions():
    data = generate([{"claim_id": "a", "failure": "pressure too high"},
                     {"claim_id": "b", "failure": "pressure too low"}], threshold=.6)
    assert len(data["pairs"]) == 1
    merged = {"a": {"FailureMode": ["f"]}, "b": {"FailureMode": ["f"]}}
    assert score_contrasts(data, merged)["contrastive_pairs_kept"] == [0, 1]
    separate = {"a": {"FailureMode": ["f"]}, "b": {"FailureMode": ["g"]}}
    assert score_contrasts(data, separate)["contrastive_pairs_kept"] == [1, 1]
    assert score_contrasts(data, {"a": separate["a"]})["contrastive_pairs_kept"] == [0, 1]
    assert score_contrasts(data, separate)["contrastive_reviewed_pairs_kept"] == [0, 0]
