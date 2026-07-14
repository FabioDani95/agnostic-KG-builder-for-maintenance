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
