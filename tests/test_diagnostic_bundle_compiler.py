from __future__ import annotations

import pytest

from backend.domain.diagnostic_bundles import (
    DiagnosticBundleCandidate,
    DiagnosticChunkOutput,
)
from backend.services.diagnostic_bundle_compiler import (
    BundleDisposition,
    DiagnosticBundleEvidenceError,
    compile_diagnostic_bundles,
    validate_diagnostic_bundle,
)


def _span(anchor: str, quote: str, page: int = 7) -> dict:
    return {"source_anchor": anchor, "source_page": page, "quote": quote}


def _action(
    *,
    anchor: str,
    name: str,
    description: str,
    instruction: str,
    edge_quote: str,
    page: int = 7,
) -> dict:
    return {
        "name": name,
        "description": description,
        "instruction_text": instruction,
        "action_kind": "procedure",
        "claim_evidence": [_span(anchor, instruction, page)],
        "resolution_link_evidence": [_span(anchor, edge_quote, page)],
    }


def _dual_indicator_candidate() -> DiagnosticBundleCandidate:
    anchor = "ev_dualrecord0001"
    return DiagnosticBundleCandidate.model_validate(
        {
            "record_anchor": anchor,
            "branch_anchor": anchor,
            "indicators": [
                {
                    "kind": "symptom",
                    "name": "Machine stops",
                    "description": "The machine stops during operation.",
                    "severity": "High",
                    "claim_evidence": [_span(anchor, "Machine stops during operation")],
                    "failure_link_evidence": [
                        _span(anchor, "Machine stops during operation because the drive overheats")
                    ],
                },
                {
                    "kind": "error_code",
                    "code": "E42",
                    "name": "Drive temperature alarm",
                    "description": "E42 reports excessive drive temperature.",
                    "claim_evidence": [_span(anchor, "E42 drive temperature alarm")],
                    "failure_link_evidence": [
                        _span(anchor, "E42 drive temperature alarm indicates drive overheating")
                    ],
                },
            ],
            "failure": {
                "name": "Drive overheating",
                "description": "The drive temperature exceeds its operating range.",
                "material_context": "asset_level",
                "claim_evidence": [_span(anchor, "drive overheating")],
            },
            "actions": [
                _action(
                    anchor=anchor,
                    name="Clean ventilation path",
                    description="Restore airflow through the drive enclosure.",
                    instruction="Clean the drive ventilation path.",
                    edge_quote="To resolve drive overheating, clean the drive ventilation path",
                )
            ],
            "affected_component": None,
            "resolution_status": "action_stated",
        }
    )


DUAL_TEXT = """--- PAGE 7 ---

[[EVIDENCE_ID: ev_dualrecord0001]]
Machine stops during operation because the drive overheats. E42 drive temperature alarm
indicates drive overheating. The drive overheating occurs when the drive temperature exceeds
its operating range. To resolve drive overheating, clean the drive ventilation path.
Clean the drive ventilation path.
"""


def test_structured_output_contract_requires_nullable_and_list_fields() -> None:
    schema = DiagnosticChunkOutput.model_json_schema()
    assert set(schema["required"]) == {"schema_version", "source_language", "records"}

    candidate = schema["$defs"]["DiagnosticBundleCandidate"]
    assert set(candidate["required"]) == {
        "record_anchor",
        "branch_anchor",
        "indicators",
        "failure",
        "actions",
        "affected_component",
        "resolution_status",
    }
    failure = schema["$defs"]["FailureModeCandidate"]
    component = schema["$defs"]["AffectedComponentCandidate"]
    assert "material_context" in failure["required"]
    assert "category" in component["required"]


def test_not_diagnostic_marker_accounts_for_false_positive_without_graph_claims() -> None:
    marker = DiagnosticBundleCandidate.model_validate(
        {
            "record_anchor": "ev_generic0001",
            "branch_anchor": "ev_generic0001",
            "indicators": [],
            "failure": None,
            "actions": [],
            "affected_component": None,
            "resolution_status": "not_diagnostic",
        }
    )
    result = compile_diagnostic_bundles(
        [marker],
        source_type="manual",
        source_title="Generic service manual",
        text_with_pages=(
            "--- PAGE 4 ---\n\n[[EVIDENCE_ID: ev_generic0001]]\n"
            "Preventive maintenance schedule and general inspection notes."
        ),
    )

    assert result.report.entries[0].disposition is BundleDisposition.EXCLUDE
    assert result.report.entries[0].record_anchor == "ev_generic0001"
    assert result.report.entries[0].evidence_ids == ["ev_generic0001"]
    assert all(not nodes for nodes in result.ontology.nodes.values())

    invalid = marker.model_dump(mode="json")
    invalid["resolution_status"] = "action_stated"
    with pytest.raises(ValueError, match="indicators must not be empty"):
        DiagnosticBundleCandidate.model_validate(invalid)


def test_dual_indicators_compile_through_schema_relations() -> None:
    output = DiagnosticChunkOutput.model_validate(
        {
            "schema_version": "1.0",
            "source_language": "en",
            "records": [_dual_indicator_candidate().model_dump(mode="json")],
        }
    )
    result = compile_diagnostic_bundles(
        output,
        source_type="manual",
        source_title="Generic drive manual",
        text_with_pages=DUAL_TEXT,
    )

    assert result.report.disposition_counts["publish"] == 1
    assert len(result.ontology.nodes["Symptom"]) == 1
    assert len(result.ontology.nodes["ErrorCode"]) == 1
    assert len(result.ontology.nodes["FailureMode"]) == 1
    assert len(result.ontology.nodes["CorrectiveAction"]) == 1
    assert {relation.name for relation in result.ontology.relations} == {
        "MAY_INDICATE",
        "INDICATES",
        "RESOLVED_BY",
    }
    assert all(
        node[next(key for key in node if key.endswith("_id"))].startswith(
            {"Symptom": "sym_", "ErrorCode": "err_"}[node_type]
        )
        for node_type in ("Symptom", "ErrorCode")
        for node in result.ontology.nodes[node_type]
    )


def test_relation_evidence_is_edge_specific_not_endpoint_union() -> None:
    result = compile_diagnostic_bundles(
        [_dual_indicator_candidate()],
        source_type="manual",
        source_title="Generic drive manual",
        text_with_pages=DUAL_TEXT,
    )
    evidence_by_relation = {
        relation.name: [evidence.quote for evidence in relation.evidence]
        for relation in result.ontology.relations
    }

    assert evidence_by_relation["MAY_INDICATE"] == [
        "Machine stops during operation because the drive overheats"
    ]
    assert evidence_by_relation["INDICATES"] == [
        "E42 drive temperature alarm indicates drive overheating"
    ]
    assert evidence_by_relation["RESOLVED_BY"] == [
        "To resolve drive overheating, clean the drive ventilation path"
    ]
    assert "Clean the drive ventilation path." not in evidence_by_relation["RESOLVED_BY"]


def test_distributed_support_set_can_ground_edges_across_evidence_units() -> None:
    payload = _dual_indicator_candidate().model_dump(mode="json")
    payload["indicators"] = [payload["indicators"][0]]
    payload["record_anchor"] = "ev_distributed_problem"
    payload["branch_anchor"] = "ev_distributed_failure"
    payload["indicators"][0]["claim_evidence"] = [
        _span("ev_distributed_problem", "Problem: Machine stops", 8)
    ]
    payload["indicators"][0]["failure_link_evidence"] = [
        _span("ev_distributed_problem", "Problem: Machine stops", 8),
        _span("ev_distributed_failure", "Cause: drive overheating", 8),
    ]
    payload["failure"]["claim_evidence"] = [
        _span("ev_distributed_failure", "Cause: drive overheating", 8)
    ]
    payload["actions"][0]["claim_evidence"] = [
        _span("ev_distributed_action", "Remedy: clean the ventilation path", 9)
    ]
    payload["actions"][0]["resolution_link_evidence"] = [
        _span("ev_distributed_failure", "Cause: drive overheating", 8),
        _span("ev_distributed_action", "Remedy: clean the ventilation path", 9),
    ]
    text = """--- PAGE 8 ---

[[EVIDENCE_ID: ev_distributed_problem]]
Problem: Machine stops.

[[EVIDENCE_ID: ev_distributed_failure]]
Cause: drive overheating.

--- PAGE 9 ---

[[EVIDENCE_ID: ev_distributed_action]]
Remedy: clean the ventilation path.
"""

    result = compile_diagnostic_bundles(
        [DiagnosticBundleCandidate.model_validate(payload)],
        source_type="manual",
        source_title="Distributed record manual",
        text_with_pages=text,
    )

    assert result.report.disposition_counts["publish"] == 1
    evidence_by_relation = {
        relation.name: {(item.source_page, item.source_anchor, item.quote) for item in relation.evidence}
        for relation in result.ontology.relations
    }
    assert evidence_by_relation["MAY_INDICATE"] == {
        (8, "ev_distributed_problem", "Problem: Machine stops"),
        (8, "ev_distributed_failure", "Cause: drive overheating"),
    }
    assert evidence_by_relation["RESOLVED_BY"] == {
        (8, "ev_distributed_failure", "Cause: drive overheating"),
        (9, "ev_distributed_action", "Remedy: clean the ventilation path"),
    }


def test_actionless_record_is_an_explicit_gap_and_publishes_no_partial_graph() -> None:
    payload = _dual_indicator_candidate().model_dump(mode="json")
    payload.update(actions=[], resolution_status="no_action_stated")
    candidate = DiagnosticBundleCandidate.model_validate(payload)
    result = compile_diagnostic_bundles(
        [candidate],
        source_type="manual",
        source_title="Generic drive manual",
        text_with_pages=DUAL_TEXT,
    )

    entry = result.report.entries[0]
    assert entry.disposition is BundleDisposition.GAP
    assert {reason.code for reason in entry.drop_reasons} >= {"missing_actions", "no_action_stated"}
    assert all(not nodes for nodes in result.ontology.nodes.values())
    assert not any(relation.name == "RESOLVED_BY" for relation in result.ontology.relations)
    assert result.validated_bundles[0].failure is not None
    assert result.validated_bundles[0].actions == []


def test_unspecified_material_context_is_safely_compiled_as_asset_level() -> None:
    payload = _dual_indicator_candidate().model_dump(mode="json")
    payload["failure"]["material_context"] = None
    result = compile_diagnostic_bundles(
        [DiagnosticBundleCandidate.model_validate(payload)],
        source_type="manual",
        source_title="Generic drive manual",
        text_with_pages=DUAL_TEXT,
    )

    assert result.report.entries[0].disposition is BundleDisposition.PUBLISH
    assert result.ontology.nodes["FailureMode"][0]["material_context"] == "asset_level"


def test_explicit_component_without_source_category_gets_neutral_schema_value() -> None:
    payload = _dual_indicator_candidate().model_dump(mode="json")
    payload["affected_component"] = {
        "name": "Drive enclosure",
        "description": "The enclosure around the drive.",
        "category": None,
        "claim_evidence": [_span("ev_dualrecord0001", "drive enclosure")],
        "affects_link_evidence": [_span("ev_dualrecord0001", "drive overheats")],
    }
    text = DUAL_TEXT.replace(
        "the drive overheats.",
        "the drive overheats in the drive enclosure.",
    )
    result = compile_diagnostic_bundles(
        [DiagnosticBundleCandidate.model_validate(payload)],
        source_type="manual",
        source_title="Generic drive manual",
        text_with_pages=text,
    )

    assert result.report.entries[0].disposition is BundleDisposition.PUBLISH
    assert result.ontology.nodes["Component"][0]["category"] == "source_named_component"
    assert {relation.name for relation in result.ontology.relations} >= {"AFFECTS"}


def test_invalid_anchor_is_reviewed_and_direct_validation_fails_closed() -> None:
    payload = _dual_indicator_candidate().model_dump(mode="json")
    payload["indicators"][0]["claim_evidence"][0]["source_anchor"] = "ev_unknownanchor01"
    candidate = DiagnosticBundleCandidate.model_validate(payload)

    with pytest.raises(DiagnosticBundleEvidenceError) as exc_info:
        validate_diagnostic_bundle(
            candidate,
            source_type="manual",
            source_title="Generic drive manual",
            text_with_pages=DUAL_TEXT,
        )
    assert {problem.code for problem in exc_info.value.problems} == {"unknown_source_anchor"}

    result = compile_diagnostic_bundles(
        [candidate],
        source_type="manual",
        source_title="Generic drive manual",
        text_with_pages=DUAL_TEXT,
    )
    assert result.report.entries[0].disposition is BundleDisposition.REVIEW
    assert result.report.dropped_items_by_reason["unknown_source_anchor"] == 1
    assert result.validated_bundles == []
    assert result.ontology.relations == []


def test_lineage_anchor_cannot_point_to_another_record_in_the_same_chunk() -> None:
    payload = _dual_indicator_candidate().model_dump(mode="json")

    def move_evidence_to_other_record(value: object) -> None:
        if isinstance(value, dict):
            if "source_anchor" in value:
                value["source_anchor"] = "ev_otherrecord001"
            for child in value.values():
                move_evidence_to_other_record(child)
        elif isinstance(value, list):
            for child in value:
                move_evidence_to_other_record(child)

    move_evidence_to_other_record(payload)
    candidate = DiagnosticBundleCandidate.model_validate(payload)
    text = DUAL_TEXT.replace(
        "[[EVIDENCE_ID: ev_dualrecord0001]]",
        "[[EVIDENCE_ID: ev_dualrecord0001]]\nUnrelated record.\n\n"
        "[[EVIDENCE_ID: ev_otherrecord001]]",
    )
    result = compile_diagnostic_bundles(
        [candidate],
        source_type="manual",
        source_title="Generic drive manual",
        text_with_pages=text,
    )

    assert result.report.entries[0].disposition is BundleDisposition.REVIEW
    reasons = result.report.entries[0].drop_reasons
    assert [reason.path for reason in reasons if reason.code == "lineage_anchor_outside_bundle"] == [
        "branch_anchor",
        "record_anchor",
    ]
    assert all(not nodes for nodes in result.ontology.nodes.values())
    assert result.ontology.relations == []


PAIR_TEXT = """--- PAGE 9 ---

[[EVIDENCE_ID: ev_recordalpha001]]
Alarm A occurs because a cable is loose. Reconnect the cable to resolve Alarm A.

[[EVIDENCE_ID: ev_recordbravo001]]
Alarm B occurs because a filter is blocked. Clean the filter to resolve Alarm B.
"""


def _paired_candidate(
    *,
    anchor: str,
    alarm: str,
    failure: str,
    action: str,
    instruction: str,
) -> DiagnosticBundleCandidate:
    return DiagnosticBundleCandidate.model_validate(
        {
            "record_anchor": anchor,
            "branch_anchor": anchor,
            "indicators": [
                {
                    "kind": "symptom",
                    "name": alarm,
                    "description": f"{alarm} is displayed.",
                    "severity": "Medium",
                    "claim_evidence": [_span(anchor, alarm, 9)],
                    "failure_link_evidence": [
                        _span(anchor, f"{alarm} occurs because {failure}", 9)
                    ],
                }
            ],
            "failure": {
                "name": failure.capitalize(),
                "description": f"The condition is that {failure}.",
                "material_context": "asset_level",
                "claim_evidence": [_span(anchor, failure, 9)],
            },
            "actions": [
                _action(
                    anchor=anchor,
                    name=action,
                    description=f"Resolve the condition by {action.lower()}.",
                    instruction=instruction,
                    edge_quote=f"{instruction} to resolve {alarm}",
                    page=9,
                )
            ],
            "affected_component": None,
            "resolution_status": "action_stated",
        }
    )


def test_ids_and_output_are_order_invariant_without_cross_pairing() -> None:
    alpha = _paired_candidate(
        anchor="ev_recordalpha001",
        alarm="Alarm A",
        failure="a cable is loose",
        action="Reconnect cable",
        instruction="Reconnect the cable",
    )
    bravo = _paired_candidate(
        anchor="ev_recordbravo001",
        alarm="Alarm B",
        failure="a filter is blocked",
        action="Clean filter",
        instruction="Clean the filter",
    )
    forward = compile_diagnostic_bundles(
        [alpha, bravo],
        source_type="manual",
        source_title="Generic controller manual",
        text_with_pages=PAIR_TEXT,
    )
    reversed_result = compile_diagnostic_bundles(
        [bravo, alpha],
        source_type="manual",
        source_title="Generic controller manual",
        text_with_pages=PAIR_TEXT,
    )

    assert forward.model_dump(mode="json") == reversed_result.model_dump(mode="json")
    failure_ids = {
        node["name"]: node["failure_mode_id"]
        for node in forward.ontology.nodes["FailureMode"]
    }
    action_ids = {
        node["name"]: node["action_id"]
        for node in forward.ontology.nodes["CorrectiveAction"]
    }
    resolved_pairs = {
        (relation.from_id, relation.to_id)
        for relation in forward.ontology.relations
        if relation.name == "RESOLVED_BY"
    }
    assert resolved_pairs == {
        (failure_ids["A cable is loose"], action_ids["Reconnect cable"]),
        (failure_ids["A filter is blocked"], action_ids["Clean filter"]),
    }
    assert len({entry.record_lineage_id for entry in forward.report.entries}) == 2
    assert len({entry.branch_lineage_id for entry in forward.report.entries}) == 2
