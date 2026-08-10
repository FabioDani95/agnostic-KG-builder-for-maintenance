from __future__ import annotations

from backend.domain.subgraphs import (
    GraphEvidenceRef,
    RelationEvidenceRef,
    SourceGraphNode,
    SourceGraphRelation,
)
from backend.models import OntologyInstance, OntologyRelationInstance
from backend.services.cutplan_service import is_diagnostic_section, page_has_diagnostic_record
from backend.services.diagnostic_publication_service import build_publication_graph
from backend.services.ontology_canonicalization_service import canonicalize_ontology_instance
from backend.services.pdf_cost_guard import estimate_pdf_generation_envelope
from backend.services.source_subgraph_generation import _strict_validation


def _evidence(evidence_id: str, page: int, quote: str) -> GraphEvidenceRef:
    return GraphEvidenceRef(
        evidence_id=evidence_id,
        label=f"Page {page}",
        excerpt=quote,
        locator={
            "kind": "pdf",
            "page": page,
            "quote": quote,
            "extraction_method": "native_text",
            "section": None,
            "printed_page": None,
            "block_index": 0,
            "table_index": None,
            "row_index": None,
            "ocr_region_index": None,
        },
    )


def _node(node_id: str, node_type: str, evidence_id: str, **attributes) -> SourceGraphNode:
    return SourceGraphNode(
        node_id=node_id,
        node_type=node_type,
        label=str(attributes.get("name") or node_id),
        evidence_ids=[evidence_id],
        attributes=attributes,
    )


def _relation(
    relation_id: str,
    relation_type: str,
    from_id: str,
    to_id: str,
    evidence_id: str,
    quote: str,
    page: int,
    *,
    support_role: str = "direct",
) -> SourceGraphRelation:
    return SourceGraphRelation(
        relation_id=relation_id,
        relation_type=relation_type,
        from_id=from_id,
        to_id=to_id,
        evidence_ids=[evidence_id],
        evidence_refs=[RelationEvidenceRef(
            evidence_id=evidence_id,
            quote=quote,
            source_anchor=evidence_id,
            locator={"kind": "pdf", "page": page},
            support_role=support_role,
        )],
    )


def test_publication_gate_separates_structural_view_and_excludes_incomplete_diagnostics():
    quotes = {
        "ev_asset_0000000001": "Operator confirmed the canonical industrial asset.",
        "ev_component_000001": "The drive motor is part of the machine assembly.",
        "ev_chain_0000000001": "Motor stalls because the drive bearing is seized; replace the bearing.",
        "ev_orphan_000000001": "Inspect the guard every shift as preventive maintenance.",
    }
    evidence = [
        _evidence(evidence_id, index, quote)
        for index, (evidence_id, quote) in enumerate(quotes.items(), start=1)
    ]
    nodes = [
        _node(
            "asset_demo", "Asset", "ev_asset_0000000001", asset_id="asset_demo", name="Demo machine",
            description="Canonical asset", brand="Generic", model="M", asset_type="industrial machine",
        ),
        _node(
            "comp_motor", "Component", "ev_component_000001", component_id="comp_motor", name="Drive motor",
            description="Motor subsystem", category="drive",
        ),
        _node(
            "sym_stall", "Symptom", "ev_chain_0000000001", symptom_id="sym_stall", name="Motor stalls",
            description="Motor stops during operation", severity="High",
        ),
        _node(
            "fm_bearing", "FailureMode", "ev_chain_0000000001", failure_mode_id="fm_bearing", name="Bearing seized",
            description="Drive bearing is seized", material_context="comp_motor",
        ),
        _node(
            "ca_replace", "CorrectiveAction", "ev_chain_0000000001", action_id="ca_replace", name="Replace bearing",
            description="Replace the seized bearing", instruction_text="Replace the drive bearing.",
            source_type="manual", source_title="Generic", source_reference="PAGE 3",
        ),
        _node(
            "ca_inspect_guard", "CorrectiveAction", "ev_orphan_000000001", action_id="ca_inspect_guard",
            name="Inspect guard", description="Preventive inspection", instruction_text="Inspect every shift.",
            source_type="manual", source_title="Generic", source_reference="PAGE 4",
        ),
    ]
    relations = [
        _relation(
            "rel_component", "HAS_COMPONENT", "asset_demo", "comp_motor",
            "ev_component_000001", quotes["ev_component_000001"], 2, support_role="derived_structural",
        ),
        _relation("rel_symptom", "MAY_INDICATE", "sym_stall", "fm_bearing", "ev_chain_0000000001", quotes["ev_chain_0000000001"], 3),
        _relation("rel_action", "RESOLVED_BY", "fm_bearing", "ca_replace", "ev_chain_0000000001", quotes["ev_chain_0000000001"], 3),
        _relation("rel_affects", "AFFECTS", "fm_bearing", "comp_motor", "ev_chain_0000000001", quotes["ev_chain_0000000001"], 3),
    ]

    result = build_publication_graph(
        candidate_nodes=nodes,
        candidate_relations=relations,
        evidence=evidence,
    )

    published_ids = {node.node_id for node in result.nodes}
    assert "ca_inspect_guard" not in published_ids
    assert {"asset_demo", "comp_motor", "sym_stall", "fm_bearing", "ca_replace"} <= published_ids
    assert set(result.projections) == {"canonical", "diagnostic", "structural"}
    assert "comp_motor" in result.projections["structural"].node_ids
    assert "sym_stall" not in result.projections["structural"].node_ids
    assert result.metrics["isolated_nodes"] == 0
    assert result.metrics["published_corrective_actions_without_failure"] == 0
    assert any(
        gap.code == "diagnostic_unlinked_or_noncorrective_action"
        and gap.target_id == "ca_inspect_guard"
        for gap in result.knowledge_gaps
    )

    validation = _strict_validation(
        nodes=result.nodes,
        relations=result.relations,
        evidence=evidence,
        require_relation_grounding=True,
    )
    assert validation.passed
    assert validation.relation_grounding_total == validation.relation_grounding_passed == 4


def test_publication_gate_rejects_relation_when_anchor_is_not_resolvable():
    quote = "Pressure drops because the filter is blocked; replace the filter."
    evidence = [_evidence("ev_chain_0000000001", 1, quote)]
    nodes = [
        _node("sym_pressure", "Symptom", "ev_chain_0000000001", symptom_id="sym_pressure", name="Pressure drops", description="Low pressure", severity="High"),
        _node("fm_filter", "FailureMode", "ev_chain_0000000001", failure_mode_id="fm_filter", name="Filter blocked", description="Filter is blocked", material_context="asset_level"),
        _node("ca_filter", "CorrectiveAction", "ev_chain_0000000001", action_id="ca_filter", name="Replace filter", description="Replace it", instruction_text="Replace the filter", source_type="manual", source_title="Generic", source_reference="PAGE 1"),
    ]
    bad_relation = _relation("rel_bad", "MAY_INDICATE", "sym_pressure", "fm_filter", "ev_chain_0000000001", quote, 1).model_copy(
        update={
            "evidence_refs": [RelationEvidenceRef(
                evidence_id="ev_chain_0000000001", quote=quote, source_anchor="unknown_anchor",
                locator={"kind": "pdf", "page": 1}, support_role="direct",
            )]
        }
    )
    action_relation = _relation("rel_action", "RESOLVED_BY", "fm_filter", "ca_filter", "ev_chain_0000000001", quote, 1)

    result = build_publication_graph(
        candidate_nodes=nodes,
        candidate_relations=[bad_relation, action_relation],
        evidence=evidence,
    )
    assert not result.nodes
    assert not result.relations
    assert result.metrics["excluded_ungrounded_relations"] == 1
    assert any(gap.code == "publication_relation_ungrounded" for gap in result.knowledge_gaps)


def test_global_canonicalization_merges_safe_plural_variant_but_not_distinct_procedures():
    ontology = OntologyInstance(
        ontology_name="Core_Ontology",
        version="2.0",
        language="en",
        source_type="manual",
        source_title="Generic industrial machine",
        nodes={
            "Asset": [],
            "Component": [
                {"component_id": "comp_filters", "name": "Filters", "description": "Air filters", "category": "pneumatic"},
                {"component_id": "comp_filter", "name": "Filter", "description": "Air filter", "category": "pneumatic"},
            ],
            "Symptom": [],
            "FailureMode": [],
            "CorrectiveAction": [
                {"action_id": "ca_reset_a", "name": "Reset controller", "description": "Warm reset", "instruction_text": "Press reset once.", "source_type": "manual", "source_title": "Generic", "source_reference": "PAGE 1"},
                {"action_id": "ca_reset_b", "name": "Reset controller", "description": "Cold reset", "instruction_text": "Isolate power for thirty seconds.", "source_type": "manual", "source_title": "Generic", "source_reference": "PAGE 2"},
            ],
            "ErrorCode": [],
        },
        relations=[
            OntologyRelationInstance(name="AFFECTS", from_type="FailureMode", from_id="fm_demo", to_type="Component", to_id="comp_filter", evidence=[]),
        ],
    )

    canonical, report = canonicalize_ontology_instance(ontology)
    assert len(canonical.nodes["Component"]) == 1
    assert len(canonical.nodes["CorrectiveAction"]) == 2
    assert report["auto_merged_count"] == 1
    assert canonical.relations[0].to_id == "comp_filter"


def test_page_role_detection_uses_diagnostic_semantics_not_procedural_sections():
    assert is_diagnostic_section("Alarm diagnosis and fault finding")
    assert is_diagnostic_section("Ricerca guasti")
    assert is_diagnostic_section("Fehlersuche")
    assert not is_diagnostic_section("Preventive maintenance and calibration")
    assert not is_diagnostic_section("Installation and inspection procedures")

    assert page_has_diagnostic_record(
        "Problem: actuator speed is unstable\nTroubleshooting:\nCause: feedback cable is loose"
    )
    assert page_has_diagnostic_record(
        "Problema: pressione insufficiente\nCausa: filtro ostruito\nRimedio: sostituire il filtro"
    )
    assert page_has_diagnostic_record(
        "Problemstellung: Antrieb stoppt\nUrsache: Versorgung fehlt\nAbhilfe: Sicherung ersetzen"
    )
    assert not page_has_diagnostic_record(
        "Preventive maintenance: inspect guards every shift and record the result."
    )


def test_canonicalization_remaps_material_context_and_clusters_review_candidates():
    ontology = OntologyInstance(
        ontology_name="Core_Ontology",
        version="2.0",
        language="en",
        source_type="manual",
        source_title="Generic machine",
        nodes={
            "Asset": [],
            "Component": [
                {"component_id": "comp_cables", "name": "Cables", "description": "Cables", "category": "electrical"},
                {"component_id": "comp_cable", "name": "Cable", "description": "Cable", "category": "electrical"},
                {"component_id": "comp_signal_cable", "name": "Signal cable", "description": "Signal cable", "category": "electrical"},
            ],
            "Symptom": [],
            "FailureMode": [
                {"failure_mode_id": "fm_open", "name": "Cable open", "description": "Cable is open", "material_context": "comp_cables"},
            ],
            "CorrectiveAction": [],
            "ErrorCode": [],
        },
        relations=[],
    )

    canonical, report = canonicalize_ontology_instance(ontology)
    assert canonical.nodes["FailureMode"][0]["material_context"] == "comp_cable"
    assert report["ambiguous_candidate_pair_count"] >= report["ambiguous_group_count"]


def test_cost_guard_is_bounded_by_chunk_and_completion_caps():
    envelope = estimate_pdf_generation_envelope(
        model_name="gpt-5.6-luna",
        chunk_input_characters=[12000, 14000, 9000, 8000, 5000],
        extraction_max_output_tokens=16000,
        coverage_enabled=True,
        coverage_max_input_tokens=30000,
        coverage_max_output_tokens=4500,
        resolution_enabled=True,
        resolution_max_targets=6,
        resolution_max_input_tokens=12500,
        resolution_max_output_tokens=2500,
        scoping_actual_cost_usd=0.005,
    )
    assert envelope["maximum_call_count"] == 12
    assert envelope["maximum_post_scoping_call_count"] == 12
    assert envelope["assumptions"]["sdk_retries"] == 0
    assert envelope["conservative_max_cost_usd"] < 0.50
    assert envelope["central_estimated_cost_usd"] < envelope["conservative_max_cost_usd"]
