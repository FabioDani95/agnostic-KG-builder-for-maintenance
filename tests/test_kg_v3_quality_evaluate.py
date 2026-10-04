"""Scorer acceptance: atomic matching, branch obligations and unknown precision."""

from __future__ import annotations

import copy

import pytest

from scripts.kg_v3_quality_evaluate import (
    maximum_matching,
    normal,
    paired_bootstrap,
    precision_sample,
    project_gold,
    score,
    weighted_support_precision,
)


def fixture(branches=("G1",)):
    claims = [
        {
            "claim_id": f"{b}.1",
            "branch_id": b,
            "indicator": "No power",
            "failure": "Blown fuse",
            "failure_stated": True,
            "code": "",
            "action": "Replace fuse",
            "action_kind": "repair",
            "conditions": "",
            "indicator_segments": ["p1.t1.r2"],
            "failure_segments": ["p1.t1.r2"],
            "action_segments": ["p1.t1.r2"],
        }
        for b in branches
    ]
    gold = project_gold({"claims": claims, "pages": [1]})
    predictions = [
        {
            **copy.deepcopy(g),
            "fact_id": f"P{n}",
            "occurrences": [{"branch_id": f"B{i}", "scope_status": "VERIFIED_REVIEW"} for i, _ in enumerate(branches)],
        }
        for n, g in enumerate(gold["facts"])
    ]
    alignment = [{"gold_branch_id": b, "branch_ids": [f"B{i}"], "status": "VERIFIED"} for i, b in enumerate(branches)]
    return gold, predictions, alignment


def test_t22_common_fact_satisfies_two_verified_applicabilities():
    gold, pred, alignment = fixture(("G1", "G2"))
    assert len(gold["facts"]) == 2 and len(gold["obligations"]) == 4
    metrics = score(gold, pred, alignment)
    assert metrics["tp"] == 2 and metrics["branch_complete"] == 2 and metrics["branch_recall"] == 1


def test_scope_cannot_borrow_a_fact_from_another_branch():
    gold, pred, alignment = fixture(("G1", "G2"))
    for p in pred:
        p["occurrences"] = p["occurrences"][:1]
    result = score(gold, pred, alignment)
    assert result["tp"] == 2 and result["branch_complete"] == 1
    assert len(result["satisfied_obligations"]) == 2


def test_matching_is_maximum_cardinality_then_maximum_obligations():
    assert maximum_matching([("G1", "P1", 3), ("G1", "P2", 1), ("G2", "P1", 1)]) == {"G1": "P2", "G2": "P1"}
    assert maximum_matching([("G1", "P1", 1), ("G1", "P2", 4), ("G2", "P1", 4), ("G2", "P2", 1)]) == {
        "G1": "P2",
        "G2": "P1",
    }
    assert maximum_matching([]) == {}


def test_t25_empty_predictions_recall_zero_precision_undefined():
    gold, _, alignment = fixture()
    result = score(gold, [], alignment)
    assert result["recall"] == 0 and result["fn"] == 2
    assert result["precision_judged"] is None and result["prediction_denominator"] == 0
    empty = score(project_gold({"claims": []}), [], [])
    assert empty["recall"] is None and empty["f1"] is None


def test_beyond_partial_gold_is_unjudged_not_false_positive():
    gold, pred, alignment = fixture()
    extra = copy.deepcopy(pred[0])
    extra["fact_id"] = "extra"
    extra["object"]["name"] = "Other source-supported fact"
    result = score(gold, pred + [extra], alignment)
    assert result["unjudged"] == 1 and result["fp"] == 0 and result["precision_global"] is None
    unsupported = score(gold, pred + [extra], alignment, {"precision": {"extra": "UNSUPPORTED"}})
    assert unsupported["fp"] == 1 and unsupported["unsupported"] == 1


@pytest.mark.parametrize(
    "left,right",
    [
        ("003", "3"),
        ("230 V", "230 kV"),
        ("No power", "Power"),
        ("A7AB", "7A7B"),
        ("input > 10", "input < 10"),
        ("up-stroke", "down-stroke"),
    ],
)
def test_normalization_preserves_semantic_differences(left, right):
    assert normal(left) != normal(right)


def test_typed_condition_missing_is_not_partial_credit():
    gold, pred, alignment = fixture()
    gold["facts"][0]["conditions"] = [{"kind": "if", "text": "at fault"}]
    result = score(gold, pred, alignment)
    assert result["tp"] == 1 and result["branch_complete"] == 0


def test_gold_ambiguity_is_explicit_and_input_unchanged():
    raw = {
        "claims": [
            {
                "claim_id": "G.1",
                "branch_id": "G",
                "indicator": "No power",
                "failure": "",
                "action": "Check voltage",
                "action_kind": "inspection",
                "conditions": "if fault persists",
                "indicator_segments": ["p1.b1"],
                "action_segments": ["p1.b1"],
                "component": "board",
                "component_segments": ["p1.b1"],
            }
        ]
    }
    prior = copy.deepcopy(raw)
    gold = project_gold(raw)
    assert raw == prior and gold["branches"][0]["adjudication_status"] == "NOT_ADJUDICATED"
    assert any(e["reason"] == "NOT_ADJUDICATED_AS_AFFECTS" for e in gold["excluded"])
    assert not any(f["object"]["type"] == "FailureMode" for f in gold["facts"])
    result = score(gold, [], [])
    assert result["excluded_gold_facts"] == 2 and result["excluded_gold_branches"] == 1


def test_stratified_precision_weights_and_unknown_bounds():
    sample = [
        {"inclusion_probability": 0.1, "judgment": "SUPPORTED"},
        {"inclusion_probability": 1, "judgment": "UNSUPPORTED"},
        {"inclusion_probability": 0.5, "judgment": "AMBIGUOUS"},
    ]
    result = weighted_support_precision(sample)
    assert result["estimate_judged"] == pytest.approx(10 / 11)
    assert result["lower_bound"] == pytest.approx(10 / 13) and result["upper_bound"] == pytest.approx(12 / 13)
    with pytest.raises(ValueError):
        weighted_support_precision([{"inclusion_probability": 0, "judgment": "SUPPORTED"}])


def test_sampling_is_deterministic_and_keeps_source_strata():
    _, pred, _ = fixture()
    population = [
        {
            **copy.deepcopy(pred[0]),
            "fact_id": str(i),
            "method": "GRAPH_REPAIR" if i % 2 else "PRIMARY",
            "modalities": ["VISUAL"] if i % 3 else ["TEXT"],
            "manual": "fixture",
        }
        for i in range(40)
    ]
    sample = precision_sample(population, per_stratum=2)
    assert sample == precision_sample(list(reversed(population)), per_stratum=2)
    assert all(0 < r["inclusion_probability"] <= 1 for r in sample)
    assert len({str(r["stratum"]) for r in sample}) == 4


def test_bootstrap_is_seeded_paired_and_inconclusive_without_clusters():
    assert paired_bootstrap({})["status"] == "INCONCLUSIVE"
    docs = {
        str(i): [
            {
                "baseline": "SUPPORTED",
                "candidate": "SUPPORTED",
                "inclusion_probability": 0.5,
                "stratum": ["PRIMARY", "TEXT"],
            }
        ]
        for i in range(8)
    }
    assert paired_bootstrap(docs, replicates=100) == paired_bootstrap(docs, replicates=100)
    assert paired_bootstrap(docs, replicates=100)["lower_one_sided_95"] == 0
