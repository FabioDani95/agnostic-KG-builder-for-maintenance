from backend.services.ontology_coverage import compute_graph_coverage


def _nodes():
    return {
        "Asset": [{"asset_id": "asset"}],
        "Component": [],
        "Symptom": [{"symptom_id": "sym"}],
        "FailureMode": [
            {"failure_mode_id": "fm_symptom"},
            {"failure_mode_id": "fm_error"},
        ],
        "CorrectiveAction": [
            {"action_id": "ca_symptom"},
            {"action_id": "ca_error"},
        ],
        "ErrorCode": [{"error_code_id": "err"}],
    }


def test_internal_relation_name_is_counted():
    coverage = compute_graph_coverage({
        "nodes": _nodes(),
        "relations": [
            {"name": "MAY_INDICATE", "from_id": "sym", "to_id": "fm_symptom"},
            {"name": "RESOLVED_BY", "from_id": "fm_symptom", "to_id": "ca_symptom"},
        ],
    })

    assert coverage["relationship_totals"] == {"MAY_INDICATE": 1, "RESOLVED_BY": 1}
    assert coverage["diagnostic_chain"]["symptoms_end_to_end_resolved"] == 1


def test_error_code_is_a_valid_diagnostic_root_for_failure_mode():
    coverage = compute_graph_coverage({
        "nodes": _nodes(),
        "relations": [
            {"name": "MAY_INDICATE", "from_id": "sym", "to_id": "fm_symptom"},
            {"name": "RESOLVED_BY", "from_id": "fm_symptom", "to_id": "ca_symptom"},
            {"name": "INDICATES", "from_id": "err", "to_id": "fm_error"},
            {
                "name": "RESOLVED_BY",
                "from_id": "fm_error",
                "to_id": "ca_error",
                "evidence": [{"quote": "Replace the failed part."}],
            },
        ],
    })

    fm = coverage["failure_mode_coverage"]
    assert fm["reachable_from_symptom"] == 1
    assert fm["reachable_from_error_code"] == 1
    assert fm["reachable_from_diagnostic_root"] == 2
    assert fm["orphan_upstream"] == 0
    assert coverage["error_code_coverage"]["end_to_end_resolved"] == 1
    assert coverage["evidence_coverage"] == {
        "causal_relations_total": 4,
        "causal_relations_with_evidence_quote": 1,
        "causal_relations_with_evidence_quote_ratio": 0.25,
    }


def test_operational_state_failure_modes_are_excluded_from_actionable_denominator():
    coverage = compute_graph_coverage({
        "nodes": {
            "Asset": [{"asset_id": "asset"}],
            "Component": [],
            "Symptom": [],
            "FailureMode": [
                {
                    "failure_mode_id": "fm_worn_belt",
                    "name": "Drive belt worn",
                    "description": "The drive belt is worn.",
                    "material_context": "comp_belt",
                },
                {
                    "failure_mode_id": "fm_door_open",
                    "name": "Door in open state",
                    "description": "The safety door is in the open state.",
                    "material_context": "asset_level",
                },
            ],
            "CorrectiveAction": [
                {"action_id": "ca_replace_belt", "name": "Replace belt",
                 "instruction_text": "1. Replace the drive belt."},
            ],
            "ErrorCode": [],
        },
        "relations": [
            {"name": "RESOLVED_BY", "from_id": "fm_worn_belt", "to_id": "ca_replace_belt"},
        ],
    })

    fm = coverage["failure_mode_coverage"]
    # Gross denominator still reports both FMs...
    assert fm["failure_modes_total"] == 2
    assert fm["with_corrective_action"] == 1
    # ...but the operational-state door is out of the actionable denominator,
    # so actionable coverage reads 1/1 instead of 1/2.
    assert fm["operational_state_count"] == 1
    assert fm["actionable_failure_modes_total"] == 1
    assert fm["actionable_with_corrective_action_ratio"] == 1.0


def test_resolution_outcome_splits_procedure_and_escalation():
    coverage = compute_graph_coverage({
        "nodes": {
            "Asset": [{"asset_id": "asset"}],
            "Component": [],
            "Symptom": [],
            "FailureMode": [
                {"failure_mode_id": "fm_a", "name": "Fault A", "description": "d", "material_context": "asset_level"},
                {"failure_mode_id": "fm_b", "name": "Fault B", "description": "d", "material_context": "asset_level"},
            ],
            "CorrectiveAction": [
                {"action_id": "ca_fix", "name": "Replace part",
                 "instruction_text": "1. Replace the part.", "action_kind": "procedure"},
                {"action_id": "ca_call", "name": "Contact dealer",
                 "instruction_text": "1. Contact your dealer.", "action_kind": "escalation"},
            ],
            "ErrorCode": [],
        },
        "relations": [
            {"name": "RESOLVED_BY", "from_id": "fm_a", "to_id": "ca_fix"},
            {"name": "RESOLVED_BY", "from_id": "fm_b", "to_id": "ca_call"},
        ],
    })

    outcome = coverage["resolution_outcome"]
    assert outcome["resolved_or_escalated"] == 2
    assert outcome["resolved_or_escalated_ratio"] == 1.0
    assert outcome["fm_resolved_by_procedure"] == 1
    assert outcome["fm_resolved_by_escalation_only"] == 1
    assert outcome["escalation_actions_total"] == 1
    assert outcome["procedure_actions_total"] == 1
