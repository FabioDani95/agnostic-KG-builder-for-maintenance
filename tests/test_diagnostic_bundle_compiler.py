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
from backend.services.graph_projection_service import project_graph_to_triplets
from backend.services.ontology_pipeline import (
    _bind_candidates_to_record_windows,
    _call_diagnostic_bundle_llm,
    _record_windows,
)
from backend.services.ontology_schema_service import load_ontology_schema


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
        "record_window_id",
        "allowed_source_anchors",
        "indicators",
        "failure",
        "actions",
        "inspection_steps",
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


def test_unlinked_optional_material_context_is_recovered_without_component() -> None:
    payload = _dual_indicator_candidate().model_dump(mode="json")
    payload["failure"]["material_context"] = "fluid"
    result = compile_diagnostic_bundles(
        [DiagnosticBundleCandidate.model_validate(payload)],
        source_type="manual",
        source_title="Generic drive manual",
        text_with_pages=DUAL_TEXT,
    )

    entry = result.report.entries[0]
    assert entry.disposition is BundleDisposition.PUBLISH
    assert entry.candidate["failure"]["material_context"] is None
    assert [item.code for item in entry.compiler_recoveries] == [
        "discarded_unlinked_material_context"
    ]
    assert result.report.recovered_items_by_reason == {
        "discarded_unlinked_material_context": 1
    }
    assert result.ontology.nodes["Component"] == []
    assert result.ontology.nodes["FailureMode"][0]["material_context"] == "asset_level"
    assert not any(relation.name == "AFFECTS" for relation in result.ontology.relations)


def test_explicit_remedy_can_coexist_with_a_separate_inspection_step() -> None:
    payload = _dual_indicator_candidate().model_dump(mode="json")
    payload["inspection_steps"] = [{
        "instruction_text": "Inspect the cooling fan.",
        "claim_evidence": [_span("ev_dualrecord0001", "Inspect the cooling fan.")],
    }]
    result = compile_diagnostic_bundles(
        [DiagnosticBundleCandidate.model_validate(payload)],
        source_type="manual",
        source_title="Generic drive manual",
        text_with_pages=DUAL_TEXT + "\nInspect the cooling fan.\n",
    )

    assert result.report.entries[0].disposition is BundleDisposition.PUBLISH
    assert len(result.ontology.nodes["CorrectiveAction"]) == 1
    assert result.ontology.nodes["CorrectiveAction"][0]["instruction_text"] == (
        "Clean the drive ventilation path."
    )


def test_compiler_rejects_literal_sibling_cell_outside_atomic_evidence_scope() -> None:
    payload = _dual_indicator_candidate().model_dump(mode="json")
    payload.update({
        "record_window_id": "diagwin_scopefixture000000000001",
        "allowed_source_anchors": ["ev_dualrecord0001"],
    })
    payload["actions"][0]["claim_evidence"] = [
        _span("ev_dualrecord0001", "Clean the sibling filter.")
    ]
    scope = [
        "Machine stops during operation because the drive overheats",
        "E42 drive temperature alarm indicates drive overheating",
        "drive overheating",
        "To resolve drive overheating, clean the drive ventilation path",
    ]
    result = compile_diagnostic_bundles(
        [DiagnosticBundleCandidate.model_validate(payload)],
        source_type="manual",
        source_title="Scoped table manual",
        text_with_pages=DUAL_TEXT + "\nClean the sibling filter.\n",
        record_windows=[{
            "window_id": "diagwin_scopefixture000000000001",
            "allowed_evidence_spans": {"ev_dualrecord0001": scope},
        }],
    )

    assert result.report.entries[0].disposition is BundleDisposition.REVIEW
    assert "quote_not_in_anchored_evidence" in {
        reason.code for reason in result.report.entries[0].drop_reasons
    }
    assert not result.ontology.relations


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


def test_same_semantic_action_reuses_node_without_provenance_collision() -> None:
    alpha = _paired_candidate(
        anchor="ev_recordalpha001",
        alarm="Alarm A",
        failure="a cable is loose",
        action="Clear restriction",
        instruction="Clear the restriction",
    )
    bravo = _paired_candidate(
        anchor="ev_recordbravo001",
        alarm="Alarm B",
        failure="a filter is blocked",
        action="Clear restriction",
        instruction="Clear the restriction",
    )
    text = PAIR_TEXT.replace(
        "Reconnect the cable", "Clear the restriction",
    ).replace("Clean the filter", "Clear the restriction")

    result = compile_diagnostic_bundles(
        [alpha, bravo],
        source_type="manual",
        source_title="Repeated remedy manual",
        text_with_pages=text,
    )

    assert result.report.disposition_counts["publish"] == 2
    assert len(result.ontology.nodes["CorrectiveAction"]) == 1
    action_id = result.ontology.nodes["CorrectiveAction"][0]["action_id"]
    action_edges = [
        relation for relation in result.ontology.relations
        if relation.name == "RESOLVED_BY"
    ]
    assert len(action_edges) == 2
    assert {relation.to_id for relation in action_edges} == {action_id}
    assert len({relation.branch_lineage_id for relation in action_edges}) == 2


def test_shared_failure_keeps_branch_actions_out_of_cartesian_projection() -> None:
    alpha = _paired_candidate(
        anchor="ev_recordalpha001",
        alarm="Alarm A",
        failure="a shared restriction exists",
        action="Reconnect cable",
        instruction="Reconnect the cable",
    )
    bravo = _paired_candidate(
        anchor="ev_recordbravo001",
        alarm="Alarm B",
        failure="a shared restriction exists",
        action="Clean filter",
        instruction="Clean the filter",
    )
    text = (
        PAIR_TEXT
        .replace("a cable is loose", "a shared restriction exists")
        .replace("a filter is blocked", "a shared restriction exists")
    )
    result = compile_diagnostic_bundles(
        [alpha, bravo],
        source_type="manual",
        source_title="Shared cause manual",
        text_with_pages=text,
    )

    assert len(result.ontology.nodes["FailureMode"]) == 1
    projection = project_graph_to_triplets(result.ontology.model_dump(mode="json"))
    actions_by_symptom = {
        triplet.symptom.name: {action.name for action in triplet.corrective_actions}
        for triplet in projection.triplets
    }
    assert actions_by_symptom == {
        "Alarm A": {"Reconnect cable"},
        "Alarm B": {"Clean filter"},
    }


def test_system_owned_window_rejects_cross_row_anchor_pairing() -> None:
    payload = _paired_candidate(
        anchor="ev_recordalpha001",
        alarm="Alarm A",
        failure="a cable is loose",
        action="Reconnect cable",
        instruction="Reconnect the cable",
    ).model_dump(mode="json")
    payload["record_window_id"] = "diagwin_system_owned"
    payload["allowed_source_anchors"] = ["ev_recordalpha001"]
    payload["actions"][0]["claim_evidence"] = [
        _span("ev_recordbravo001", "Clean the filter", 9)
    ]
    candidate = DiagnosticBundleCandidate.model_validate(payload)

    result = compile_diagnostic_bundles(
        [candidate],
        source_type="manual",
        source_title="Cross row contamination manual",
        text_with_pages=PAIR_TEXT,
    )

    entry = result.report.entries[0]
    assert entry.disposition is BundleDisposition.REVIEW
    assert "source_anchor_outside_record_window" in {
        reason.code for reason in entry.drop_reasons
    }
    assert entry.candidate["actions"][0]["claim_evidence"][0]["source_anchor"] == (
        "ev_recordbravo001"
    )
    assert not result.ontology.relations


def test_exact_composite_quote_splits_only_across_contiguous_units() -> None:
    payload = _dual_indicator_candidate().model_dump(mode="json")
    payload["indicators"] = [payload["indicators"][0]]
    payload["record_anchor"] = "ev_split_problem001"
    payload["branch_anchor"] = "ev_split_cause0001"
    payload["indicators"][0]["claim_evidence"] = [
        _span("ev_split_problem001", "Problem: Machine stops", 8)
    ]
    payload["indicators"][0]["failure_link_evidence"] = [
        _span(
            "ev_split_problem001",
            "Problem: Machine stops Cause: drive overheating",
            8,
        )
    ]
    payload["failure"]["claim_evidence"] = [
        _span("ev_split_cause0001", "Cause: drive overheating", 8)
    ]
    payload["actions"][0]["claim_evidence"] = [
        _span("ev_split_action0001", "Clean the ventilation path", 8)
    ]
    payload["actions"][0]["resolution_link_evidence"] = [
        _span("ev_split_action0001", "Clean the ventilation path", 8)
    ]
    text = """--- PAGE 8 ---

[[EVIDENCE_ID: ev_split_problem001]]
Problem: Machine stops

[[EVIDENCE_ID: ev_split_cause0001]]
Cause: drive overheating

[[EVIDENCE_ID: ev_split_action0001]]
Clean the ventilation path
"""
    result = compile_diagnostic_bundles(
        [DiagnosticBundleCandidate.model_validate(payload)],
        source_type="manual",
        source_title="Split support manual",
        text_with_pages=text,
    )
    may = next(relation for relation in result.ontology.relations if relation.name == "MAY_INDICATE")
    assert [(item.source_anchor, item.quote) for item in may.evidence] == [
        ("ev_split_cause0001", "Cause: drive overheating"),
        ("ev_split_problem001", "Problem: Machine stops"),
    ]

    contaminated = text.replace(
        "[[EVIDENCE_ID: ev_split_cause0001]]",
        "[[EVIDENCE_ID: ev_unrelated000001]]\nUnrelated row\n\n"
        "[[EVIDENCE_ID: ev_split_cause0001]]",
    )
    rejected = compile_diagnostic_bundles(
        [DiagnosticBundleCandidate.model_validate(payload)],
        source_type="manual",
        source_title="Split support manual",
        text_with_pages=contaminated,
    )
    assert rejected.report.entries[0].disposition is BundleDisposition.REVIEW
    assert "quote_not_in_anchored_evidence" in {
        reason.code for reason in rejected.report.entries[0].drop_reasons
    }

def test_inspection_only_action_becomes_traceable_gap_not_corrective_action() -> None:
    payload = _dual_indicator_candidate().model_dump(mode="json")
    payload["indicators"] = [payload["indicators"][0]]
    payload["actions"][0].update({
        "name": "Inspect ventilation path",
        "description": "Inspect the airflow path.",
        "instruction_text": "Check the ventilation path for obstruction.",
        "claim_evidence": [
            _span("ev_dualrecord0001", "Check the ventilation path", 7)
        ],
        "resolution_link_evidence": [
            _span("ev_dualrecord0001", "Check the ventilation path", 7)
        ],
    })
    text = DUAL_TEXT.replace(
        "Clean the drive ventilation path.",
        "Check the ventilation path for obstruction.",
    )
    result = compile_diagnostic_bundles(
        [DiagnosticBundleCandidate.model_validate(payload)],
        source_type="manual",
        source_title="Inspection manual",
        text_with_pages=text,
    )

    entry = result.report.entries[0]
    assert entry.disposition is BundleDisposition.GAP
    assert "inspection_only_action" in {reason.code for reason in entry.drop_reasons}
    assert result.ontology.nodes["CorrectiveAction"] == []
    assert result.ontology.relations == []


def test_model_cannot_override_system_owned_continuation_branch_anchor() -> None:
    candidate = _dual_indicator_candidate().model_copy(update={
        "record_window_id": "diagwin_continuation",
        "record_anchor": "ev_rootrow0000001",
        "branch_anchor": "ev_rootrow0000001",
    })
    parsed = DiagnosticChunkOutput(
        schema_version="1.0",
        source_language="en",
        records=[candidate],
    )
    windows = _record_windows({
        "record_windows": [{
            "window_id": "diagwin_continuation",
            "record_anchor": "ev_rootrow0000001",
            "branch_anchor": "ev_currentrow00001",
            "allowed_source_anchors": [
                "ev_rootrow0000001",
                "ev_currentrow00001",
                "ev_dualrecord0001",
            ],
            "page_numbers": [7],
        }],
    })

    rebound = _bind_candidates_to_record_windows(parsed, windows)

    assert rebound.records[0].record_anchor == "ev_rootrow0000001"
    assert rebound.records[0].branch_anchor == "ev_currentrow00001"
    assert rebound.records[0].allowed_source_anchors == sorted({
        "ev_rootrow0000001",
        "ev_currentrow00001",
        "ev_dualrecord0001",
    })


def test_atomic_table_binding_replaces_nonliteral_edge_text_with_endpoint_spans() -> None:
    candidate = _dual_indicator_candidate().model_copy(update={
        "record_window_id": "diagwin_atomic_table",
    })
    parsed = DiagnosticChunkOutput(
        schema_version="1.0",
        source_language="en",
        records=[candidate],
    )
    windows = _record_windows({
        "record_windows": [{
            "window_id": "diagwin_atomic_table",
            "window_kind": "table_row",
            "structure_status": "atomic",
            "record_anchor": "ev_dualrecord0001",
            "branch_anchor": "ev_dualrecord0001",
            "allowed_source_anchors": ["ev_dualrecord0001"],
            "allowed_evidence_spans": {"ev_dualrecord0001": ["drive overheating"]},
            "page_numbers": [7],
        }],
    })

    rebound = _bind_candidates_to_record_windows(parsed, windows).records[0]

    assert {span.quote for span in rebound.indicators[0].failure_link_evidence} == {
        "Machine stops during operation",
        "drive overheating",
    }
    assert {span.quote for span in rebound.actions[0].resolution_link_evidence} == {
        "drive overheating",
        "Clean the drive ventilation path.",
    }


def test_layout_only_prose_branch_is_forced_to_review_with_endpoint_spans() -> None:
    candidate = _dual_indicator_candidate().model_copy(update={
        "record_window_id": "diagwin_layout_prose",
    })
    parsed = DiagnosticChunkOutput(
        schema_version="1.0",
        source_language="en",
        records=[candidate],
    )
    windows = _record_windows({
        "record_windows": [{
            "window_id": "diagwin_layout_prose",
            "window_kind": "contiguous_blocks",
            "structure_status": "atomic",
            "edge_policy": "prose_layout_endpoint_union",
            "record_anchor": "ev_dualrecord0001",
            "branch_anchor": "ev_dualrecord0001",
            "allowed_source_anchors": ["ev_dualrecord0001"],
            "allowed_evidence_spans": {
                "ev_dualrecord0001": [
                    "Machine stops during operation",
                    "drive overheating",
                    "Clean the drive ventilation path.",
                ]
            },
            "page_numbers": [7],
        }],
    })

    rebound = _bind_candidates_to_record_windows(parsed, windows).records[0]

    assert rebound.resolution_status.value == "ambiguous"
    assert {span.quote for span in rebound.actions[0].resolution_link_evidence} == {
        "drive overheating",
        "Clean the drive ventilation path.",
    }


def test_structurally_ambiguous_table_window_is_accounted_without_model_call() -> None:
    result = _call_diagnostic_bundle_llm({
        "source_type": "technical PDF",
        "source_title": "Ambiguous table fixture",
        "target_language": "en",
        "text_with_pages": (
            "--- PAGE 14 ---\n\n[[EVIDENCE_ID: ev_ambiguousrow001]]\n"
            "Output low | two causes | three remedies"
        ),
        "model_name": "must-not-be-called",
        "reasoning_effort": "medium",
        "schema": load_ontology_schema(),
        "diagnostic_call_options": {
            "record_windows": [{
                "window_id": "diagwin_ambiguous_fixture",
                "window_kind": "table_row",
                "structure_status": "ambiguous_pairing",
                "record_anchor": "ev_ambiguousrow001",
                "branch_anchor": "ev_ambiguousrow001",
                "allowed_source_anchors": ["ev_ambiguousrow001"],
                "allowed_evidence_spans": {
                    "ev_ambiguousrow001": ["Output low", "two causes", "three remedies"]
                },
                "page_numbers": [14],
            }],
        },
        "diagnostic_evidence_units": [],
        "llm_usage": [],
    })

    report = result["diagnostic_contract_report"]
    assert report["provider_model"] == "deterministic_structural_inventory"
    assert report["records"][0]["accounting_state"] == (
        "observed_structurally_incomplete"
    )
    assert report["records"][0]["disposition"] == "review"
    assert result["llm_usage"] == []


def test_system_owned_lineage_need_not_be_echoed_in_claim_evidence() -> None:
    payload = _dual_indicator_candidate().model_dump(mode="json")
    payload.update({
        "record_window_id": "diagwin_system_lineage",
        "allowed_source_anchors": [
            "ev_systemrecord001",
            "ev_systembranch001",
            "ev_dualrecord0001",
        ],
        "record_anchor": "ev_systemrecord001",
        "branch_anchor": "ev_systembranch001",
    })
    text = DUAL_TEXT.replace(
        "[[EVIDENCE_ID: ev_dualrecord0001]]",
        "[[EVIDENCE_ID: ev_systemrecord001]]\nSystem-owned record root.\n\n"
        "[[EVIDENCE_ID: ev_systembranch001]]\nSystem-owned branch row.\n\n"
        "[[EVIDENCE_ID: ev_dualrecord0001]]",
    )

    windowed = compile_diagnostic_bundles(
        [DiagnosticBundleCandidate.model_validate(payload)],
        source_type="manual",
        source_title="System lineage manual",
        text_with_pages=text,
    )
    assert windowed.report.entries[0].disposition is BundleDisposition.PUBLISH

    legacy = dict(payload)
    legacy["record_window_id"] = ""
    legacy["allowed_source_anchors"] = []
    rejected = compile_diagnostic_bundles(
        [DiagnosticBundleCandidate.model_validate(legacy)],
        source_type="manual",
        source_title="System lineage manual",
        text_with_pages=text,
    )
    assert rejected.report.entries[0].disposition is BundleDisposition.REVIEW
    assert "lineage_anchor_outside_bundle" in {
        reason.code for reason in rejected.report.entries[0].drop_reasons
    }


def test_system_owned_lineage_must_exist_inside_its_allowed_window() -> None:
    marker = DiagnosticBundleCandidate.model_validate({
        "record_window_id": "diagwin_exclusion_lineage",
        "allowed_source_anchors": ["ev_allowedmarker001"],
        "record_anchor": "ev_outsidemarker001",
        "branch_anchor": "ev_outsidemarker001",
        "indicators": [],
        "failure": None,
        "actions": [],
        "inspection_steps": [],
        "affected_component": None,
        "resolution_status": "not_diagnostic",
    })
    text = """--- PAGE 4 ---

[[EVIDENCE_ID: ev_allowedmarker001]]
Preventive maintenance schedule.

[[EVIDENCE_ID: ev_outsidemarker001]]
Unrelated source row.
"""

    result = compile_diagnostic_bundles(
        [marker],
        source_type="manual",
        source_title="Window membership manual",
        text_with_pages=text,
    )
    assert result.report.entries[0].disposition is BundleDisposition.REVIEW
    assert "lineage_anchor_outside_record_window" in {
        reason.code for reason in result.report.entries[0].drop_reasons
    }


def _misanchored_window_candidate(*, allowed: list[str]) -> DiagnosticBundleCandidate:
    payload = _dual_indicator_candidate().model_dump(mode="json")
    wrong_anchor = "ev_windowrouting001"
    payload.update({
        "record_window_id": "diagwin_exact_relocation",
        "allowed_source_anchors": allowed,
        "record_anchor": wrong_anchor,
        "branch_anchor": wrong_anchor,
    })
    for indicator in payload["indicators"]:
        for field in ("claim_evidence", "failure_link_evidence"):
            for span in indicator[field]:
                span["source_anchor"] = wrong_anchor
    for span in payload["failure"]["claim_evidence"]:
        span["source_anchor"] = wrong_anchor
    for action in payload["actions"]:
        for field in ("claim_evidence", "resolution_link_evidence"):
            for span in action[field]:
                span["source_anchor"] = wrong_anchor
    return DiagnosticBundleCandidate.model_validate(payload)


def _relocation_text(*, duplicate: bool = False) -> str:
    diagnostic_text = DUAL_TEXT.split("[[EVIDENCE_ID: ev_dualrecord0001]]", 1)[1].strip()
    duplicate_block = (
        "\n\n[[EVIDENCE_ID: ev_windowexact0002]]\n" + diagnostic_text
        if duplicate
        else ""
    )
    return (
        "--- PAGE 7 ---\n\n"
        "[[EVIDENCE_ID: ev_windowrouting001]]\nWindow routing context only.\n\n"
        "[[EVIDENCE_ID: ev_windowexact00001]]\n"
        + diagnostic_text
        + duplicate_block
    )


def test_exact_quote_is_relocated_to_one_unique_anchor_inside_window() -> None:
    candidate = _misanchored_window_candidate(
        allowed=["ev_windowrouting001", "ev_windowexact00001"]
    )
    result = compile_diagnostic_bundles(
        [candidate],
        source_type="manual",
        source_title="Exact relocation manual",
        text_with_pages=_relocation_text(),
    )

    entry = result.report.entries[0]
    assert entry.disposition is BundleDisposition.PUBLISH
    assert entry.candidate["indicators"][0]["claim_evidence"][0]["source_anchor"] == (
        "ev_windowrouting001"
    )
    assert entry.resolved_evidence_ids == ["ev_windowexact00001"]
    assert {
        evidence.source_anchor
        for relation in result.ontology.relations
        for evidence in relation.evidence
    } == {"ev_windowexact00001"}

    outside_hint_payload = candidate.model_dump(mode="json")
    for indicator in outside_hint_payload["indicators"]:
        for field in ("claim_evidence", "failure_link_evidence"):
            for span in indicator[field]:
                span["source_anchor"] = "ev_outsidewindowhint1"
    for span in outside_hint_payload["failure"]["claim_evidence"]:
        span["source_anchor"] = "ev_outsidewindowhint1"
    for action in outside_hint_payload["actions"]:
        for field in ("claim_evidence", "resolution_link_evidence"):
            for span in action[field]:
                span["source_anchor"] = "ev_outsidewindowhint1"
    outside_hint = compile_diagnostic_bundles(
        [DiagnosticBundleCandidate.model_validate(outside_hint_payload)],
        source_type="manual",
        source_title="Exact relocation manual",
        text_with_pages=_relocation_text(),
    )
    assert outside_hint.report.entries[0].disposition is BundleDisposition.PUBLISH
    assert outside_hint.report.entries[0].resolved_evidence_ids == [
        "ev_windowexact00001"
    ]


def test_exact_quote_relocation_rejects_ambiguous_or_cross_window_match() -> None:
    ambiguous = _misanchored_window_candidate(
        allowed=[
            "ev_windowrouting001",
            "ev_windowexact00001",
            "ev_windowexact0002",
        ]
    )
    ambiguous_result = compile_diagnostic_bundles(
        [ambiguous],
        source_type="manual",
        source_title="Ambiguous relocation manual",
        text_with_pages=_relocation_text(duplicate=True),
    )
    assert ambiguous_result.report.entries[0].disposition is BundleDisposition.REVIEW
    assert "quote_not_in_anchored_evidence" in {
        reason.code for reason in ambiguous_result.report.entries[0].drop_reasons
    }

    cross_window = _misanchored_window_candidate(allowed=["ev_windowrouting001"])
    cross_window_result = compile_diagnostic_bundles(
        [cross_window],
        source_type="manual",
        source_title="Cross-window relocation manual",
        text_with_pages=_relocation_text(),
    )
    assert cross_window_result.report.entries[0].disposition is BundleDisposition.REVIEW
    assert not cross_window_result.ontology.relations


def test_composite_quote_relocation_is_unique_contiguous_and_window_bounded() -> None:
    payload = _dual_indicator_candidate().model_dump(mode="json")
    payload["indicators"] = [payload["indicators"][0]]
    payload.update({
        "record_window_id": "diagwin_composite_relocation",
        "allowed_source_anchors": [
            "ev_compositeproblem1",
            "ev_compositecause001",
            "ev_compositeaction01",
        ],
        "record_anchor": "ev_compositeproblem1",
        "branch_anchor": "ev_compositecause001",
    })
    payload["indicators"][0]["claim_evidence"] = [
        _span("ev_compositeproblem1", "Problem: Machine stops", 8)
    ]
    payload["indicators"][0]["failure_link_evidence"] = [
        _span(
            "ev_compositeaction01",
            "Problem: Machine stops Cause: drive overheating",
            8,
        )
    ]
    payload["failure"]["claim_evidence"] = [
        _span("ev_compositecause001", "Cause: drive overheating", 8)
    ]
    payload["actions"][0]["claim_evidence"] = [
        _span("ev_compositeaction01", "Clean the ventilation path", 8)
    ]
    payload["actions"][0]["resolution_link_evidence"] = [
        _span("ev_compositeaction01", "Clean the ventilation path", 8)
    ]
    candidate = DiagnosticBundleCandidate.model_validate(payload)
    text = """--- PAGE 8 ---

[[EVIDENCE_ID: ev_compositeproblem1]]
Problem: Machine stops

[[EVIDENCE_ID: ev_compositecause001]]
Cause: drive overheating

[[EVIDENCE_ID: ev_compositeaction01]]
Clean the ventilation path
"""
    result = compile_diagnostic_bundles(
        [candidate],
        source_type="manual",
        source_title="Composite relocation manual",
        text_with_pages=text,
    )
    assert result.report.entries[0].disposition is BundleDisposition.PUBLISH
    may_indicate = next(
        relation for relation in result.ontology.relations if relation.name == "MAY_INDICATE"
    )
    assert [(item.source_anchor, item.quote) for item in may_indicate.evidence] == [
        ("ev_compositecause001", "Cause: drive overheating"),
        ("ev_compositeproblem1", "Problem: Machine stops"),
    ]

    contaminated = text.replace(
        "[[EVIDENCE_ID: ev_compositecause001]]",
        "[[EVIDENCE_ID: ev_outsidewindow001]]\nUnrelated row\n\n"
        "[[EVIDENCE_ID: ev_compositecause001]]",
    )
    rejected = compile_diagnostic_bundles(
        [candidate],
        source_type="manual",
        source_title="Composite relocation manual",
        text_with_pages=contaminated,
    )
    assert rejected.report.entries[0].disposition is BundleDisposition.REVIEW
    assert "quote_not_in_anchored_evidence" in {
        reason.code for reason in rejected.report.entries[0].drop_reasons
    }

    ambiguous_payload = candidate.model_dump(mode="json")
    ambiguous_payload["allowed_source_anchors"].extend([
        "ev_compositeproblem2",
        "ev_compositecause002",
    ])
    ambiguous_text = text.replace(
        "[[EVIDENCE_ID: ev_compositeaction01]]",
        "[[EVIDENCE_ID: ev_compositeproblem2]]\nProblem: Machine stops\n\n"
        "[[EVIDENCE_ID: ev_compositecause002]]\nCause: drive overheating\n\n"
        "[[EVIDENCE_ID: ev_compositeaction01]]",
    )
    ambiguous_result = compile_diagnostic_bundles(
        [DiagnosticBundleCandidate.model_validate(ambiguous_payload)],
        source_type="manual",
        source_title="Composite relocation manual",
        text_with_pages=ambiguous_text,
    )
    assert ambiguous_result.report.entries[0].disposition is BundleDisposition.REVIEW
    assert "quote_not_in_anchored_evidence" in {
        reason.code for reason in ambiguous_result.report.entries[0].drop_reasons
    }
