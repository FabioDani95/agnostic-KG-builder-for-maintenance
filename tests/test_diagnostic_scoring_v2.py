from copy import deepcopy

from paper.evaluation.diagnostic_scoring import score_branches


def branch(ident):
    return {"branch_id": ident, "source_occurrence_id": "synthetic-page10-row2-branch1", "pages": [10], "symptoms": ["no output"], "codes": ["02"], "failure": "valve stuck open", "component": "valve", "conditions": [{"text": "pressure is not low", "polarity": "negative", "applies_to": "action", "step_index": 0}], "inspections": ["check voltage"], "actions": ["replace valve"], "resolution_status": "action_stated", "disposition": "publish"}


def gold():
    return {"validation_status": "technician_validated", "adjudication": {"reviewer_id": "synthetic-test-reviewer"}, "scope_pages": [10, 11], "scope_exhaustive": True, "branches": [branch("g1")], "equivalences": {}}


def test_duplicate_prediction_cannot_earn_twice_the_credit():
    result = score_branches(gold(), [branch("p1"), branch("p2")])
    assert result["matched_branches"] == 1
    assert len(result["unmatched_predictions_requiring_adjudication"]) == 1
    assert result["semantic_precision"] is None


def test_negation_code_branch_and_inspection_action_swaps_do_not_match():
    changes = [{"codes": ["20"]}, {"failure": "valve stuck closed"}, {"inspections": ["replace valve"], "actions": ["check voltage"]}, {"conditions": [{"text": "pressure is low", "polarity": "positive", "applies_to": "action", "step_index": 0}]}]
    for change in changes:
        pred = {**branch("p1"), **change}
        assert score_branches(gold(), [pred])["matched_branches"] == 0


def test_proposed_gold_cannot_produce_validation_scores():
    proposed = {**gold(), "validation_status": "agent_proposed"}
    assert score_branches(proposed, [branch("p")])["status"] == "pending_technician_validation"


def test_multipage_reference_does_not_require_identical_page_sets():
    ref = gold()
    ref["branches"][0]["pages"] = [10, 11]
    assert score_branches(ref, [branch("p")])["matched_branches"] == 1
    pred = deepcopy(branch("p"))
    pred["pages"] = [9, 10]
    assert score_branches(ref, [pred])["boundary_or_missing_scope_unscored"] == 1


def test_explicit_independent_equivalence_can_match_without_lexical_threshold():
    ref = gold()
    ref["equivalences"] = {"renew valve": "replace valve"}
    pred = branch("p")
    pred["actions"] = ["renew valve"]
    assert score_branches(ref, [pred])["matched_branches"] == 1


def test_identical_words_in_a_different_source_occurrence_do_not_match():
    pred = branch("p")
    pred["source_occurrence_id"] = "synthetic-page10-row9-branch1"
    assert score_branches(gold(), [pred])["matched_branches"] == 0


def test_context_page_outside_scope_is_allowed_when_root_scope_is_explicit():
    pred = branch("p")
    pred.update(root_pages=[10], pages=[10, 12])
    assert score_branches(gold(), [pred])["matched_branches"] == 1
