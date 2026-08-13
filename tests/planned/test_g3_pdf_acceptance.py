from __future__ import annotations

import pytest

from backend.domain.evidence import QualityFlag
from backend.domain.subgraphs import PdfExtractionScope
from backend.models import (
    CutPlan,
    OntologyEvidence,
    OntologyInstance,
    OntologyPipelineResponse,
    OntologyRelationInstance,
    PageRange,
    SectionInfo,
)
from backend.services import pdf_source_subgraph_generation as pdf_generation
from backend.services.pdf_source_subgraph_generation import (
    PdfSourceSubgraphBuilder,
    pdf_input_config_hash,
    pdf_preparation_fingerprint,
)
from backend.storage.repositories.evidence import EvidenceRepository
from backend.storage.repositories.sources import SourceRepository
from backend.storage.repositories.workspaces import WorkspaceRepository
from tests.planned.source_fixtures import upload_pdf, upload_pdf_pages


def _workspace(client, machine_payload) -> dict:
    response = client.post("/api/workspace", json=machine_payload)
    assert response.status_code == 201, response.text
    return response.json()["workspace"]


def test_pdf_generation_cache_key_includes_reasoning_effort(monkeypatch):
    efforts = {"scoping": "low", "ontology_draft": "medium"}

    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.get_agent_config",
        lambda name: {"model": "gpt-5.6-luna", "reasoning_effort": efforts[name]},
    )
    medium_hash = pdf_input_config_hash()
    efforts["ontology_draft"] = "low"

    assert pdf_input_config_hash() != medium_hash


def test_pdf_generation_cache_key_includes_normalized_escalation_policy(monkeypatch):
    policy = {
        "enabled": False,
        "model": "gpt-5.6-terra",
        "reasoning_effort": "medium",
        "max_chunks_per_run": 0,
    }
    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.get_diagnostic_escalation_config",
        lambda: dict(policy),
    )
    disabled_hash = pdf_input_config_hash()
    policy["enabled"] = True
    policy["max_chunks_per_run"] = 1

    assert pdf_input_config_hash() != disabled_hash


def test_pdf_generation_cache_key_includes_pricing_catalog(monkeypatch):
    current_hash = pdf_input_config_hash()
    monkeypatch.setitem(
        pdf_generation.MODEL_PRICING["gpt-5.6-luna"],
        "output_per_million",
        1.21,
    )

    assert pdf_input_config_hash() != current_hash


def test_pdf_generation_cache_key_includes_diagnostic_contract(monkeypatch):
    current_hash = pdf_input_config_hash()

    class ChangedDiagnosticContract:
        @classmethod
        def model_json_schema(cls):
            return {"type": "object", "properties": {"changed": {"type": "boolean"}}}

    monkeypatch.setattr(
        pdf_generation,
        "DiagnosticChunkOutput",
        ChangedDiagnosticContract,
    )

    assert pdf_input_config_hash() != current_hash


def _pipeline_result(
    store: dict,
    *,
    quote: str,
    source_page: int = 1,
    source_anchor: str = "",
) -> OntologyPipelineResponse:
    asset = store["asset_identity"]
    resolved_anchor = str(source_anchor or "").strip()
    if not resolved_anchor:
        source_page_payload = next(
            page for page in store["pages"]
            if int(page["page_number"]) == source_page
        )
        resolved_anchor = str(source_page_payload["evidence_anchors"][0])
    evidence = [OntologyEvidence(
        source_page=source_page,
        source_reference=f"PAGE {source_page}",
        quote=quote,
        source_anchor=resolved_anchor,
    )]
    return OntologyPipelineResponse(
        status="ready",
        ontology=OntologyInstance(
            ontology_name="Core_Ontology",
            version="2.0",
            language="en",
            source_type="technical PDF",
            source_title=store["source_title"],
            nodes={
                "Asset": [asset],
                "Symptom": [{
                    "symptom_id": "SYM-PDF-1",
                    "name": "Pump vibration",
                    "description": "The pump vibrates during operation.",
                    "severity": "Medium",
                }],
                "FailureMode": [{
                    "failure_mode_id": "FM-PDF-1",
                    "name": "Loose coupling",
                    "description": "The coupling is loose.",
                    "material_context": "COMP-PDF-1",
                }],
                "CorrectiveAction": [{
                    "action_id": "CA-PDF-1",
                    "name": "Tighten coupling",
                    "description": "Secure the pump coupling.",
                    "instruction_text": "Tighten the coupling to specification.",
                    "source_type": "technical PDF",
                    "source_title": store["source_title"],
                    "source_reference": f"PAGE {source_page}",
                }],
                "Component": [{
                    "component_id": "COMP-PDF-1",
                    "name": "Pump coupling",
                    "description": "Coupling in the pump drive train.",
                    "category": "Drive train",
                }],
                "ErrorCode": [],
            },
            relations=[
                OntologyRelationInstance(
                    name="HAS_COMPONENT",
                    from_type="Asset",
                    from_id=asset["asset_id"],
                    to_type="Component",
                    to_id="COMP-PDF-1",
                    evidence=evidence,
                ),
                OntologyRelationInstance(
                    name="MAY_INDICATE",
                    from_type="Symptom",
                    from_id="SYM-PDF-1",
                    to_type="FailureMode",
                    to_id="FM-PDF-1",
                    evidence=evidence,
                ),
                OntologyRelationInstance(
                    name="AFFECTS",
                    from_type="FailureMode",
                    from_id="FM-PDF-1",
                    to_type="Component",
                    to_id="COMP-PDF-1",
                    evidence=evidence,
                ),
                OntologyRelationInstance(
                    name="RESOLVED_BY",
                    from_type="FailureMode",
                    from_id="FM-PDF-1",
                    to_type="CorrectiveAction",
                    to_id="CA-PDF-1",
                    evidence=evidence,
                ),
            ],
        ),
        diagnostic_contract_report={
            "schema_version": "1.0",
            "parsed": True,
            "refusal": False,
            "finish_reason": "stop",
            "candidate_pages": [source_page],
            "candidate_page_count": 1,
            "candidate_count": 1,
            "publish_count": 1,
            "unresolved_count": 0,
            "records": [{
                "record_lineage_id": f"drec_fixture_page_{source_page}",
                "branch_lineage_id": f"dbranch_fixture_page_{source_page}",
                "record_anchor": resolved_anchor,
                "branch_anchor": resolved_anchor,
                "evidence_ids": [resolved_anchor],
                "disposition": "publish",
                "drop_reasons": [],
                "emitted_node_ids": ["SYM-PDF-1", "FM-PDF-1", "CA-PDF-1"],
                "emitted_relations": ["MAY_INDICATE", "RESOLVED_BY"],
            }],
        },
        is_schema_compliant=True,
        is_ready_for_human_review=True,
    )


def _cut_plan_for(store: dict, pdf_id: str, pages: list[int]) -> CutPlan:
    plan = CutPlan(
        pdf_id=pdf_id,
        total_pages=len(store["pages"]),
        sections=[],
        pages_to_keep=pages,
        page_offset=0,
        skipped=len(pages) == len(store["pages"]),
    )
    store["cut_plan"] = {
        "pdf_id": pdf_id,
        "total_pages": len(store["pages"]),
        "sections": [],
        "pages_to_keep": pages,
        "page_offset": 0,
        "skipped": plan.skipped,
    }
    return plan


def test_pdf_builds_the_same_reviewable_source_subgraph_contract(
    foundation_client,
    machine_payload,
    monkeypatch,
):
    workspace = _workspace(foundation_client, machine_payload)
    uploaded = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "pump-manual.pdf",
        "SERIAL: HP7-000042\nPump vibration indicates a loose coupling. Tighten the coupling.",
    )
    assert uploaded.status_code == 200, uploaded.text
    source = uploaded.json()["source"]
    calls = 0

    def fake_cut_plan(store, request, on_event=None):
        assert request.discover_asset_identity is False
        return _cut_plan_for(store, request.pdf_id, [1])

    async def fake_retained_pipeline(store, request, on_event=None):
        nonlocal calls
        calls += 1
        assert request.pdf_id == source["source_id"]
        assert store["asset_identity"]["asset_id"] == workspace["asset"]["asset_id"]
        return _pipeline_result(
            store,
            quote="Pump vibration indicates a loose coupling. Tighten the coupling.",
        )

    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.create_cut_plan_workflow",
        fake_cut_plan,
    )
    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.draft_ontology_workflow",
        fake_retained_pipeline,
    )

    initial = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/g3/subgraphs"
    )
    assert initial.status_code == 200, initial.text
    assert initial.json()["sources"][0]["state"] == "ready"

    generated = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/g3/sources/{source['source_id']}/generate"
    )
    assert generated.status_code == 200, generated.text
    view = generated.json()
    graph = view["sources"][0]["subgraph"]
    assert graph["source_kind"] == "pdf"
    assert graph["validation"]["passed"] is True
    assert graph["approval_eligible"] is True
    assert graph["knowledge_gaps"] == []
    assert graph["pdf_extraction_scope"] == {
        "method": "retained_cut_plan",
        "total_pages": 1,
        "selected_pages": [1],
        "unselected_pages": [],
        "diagnostic_pages": [1],
        "structural_pages": [],
        "retrieval_pages": [1],
        "sections": [],
        "page_offset": 0,
        "skipped": True,
    }
    assert {node["node_type"] for node in graph["nodes"]} == {
        "Asset", "Component", "Symptom", "FailureMode", "CorrectiveAction",
    }
    assert {relation["relation_type"] for relation in graph["relations"]} == {
        "HAS_COMPONENT", "MAY_INDICATE", "AFFECTS", "RESOLVED_BY",
    }
    assert graph["evidence"]
    assert {item["locator"]["kind"] for item in graph["evidence"]} == {"pdf", "operator_input"}
    assert all(node["evidence_ids"] for node in graph["nodes"])
    assert all(relation["evidence_ids"] for relation in graph["relations"])

    repeated = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/g3/sources/{source['source_id']}/generate"
    )
    assert repeated.status_code == 200, repeated.text
    assert calls == 1
    assert (
        repeated.json()["sources"][0]["subgraph"]["source_subgraph_revision_id"]
        == graph["source_subgraph_revision_id"]
    )

    approved = foundation_client.post(
        f"/api/g3/subgraphs/{graph['source_subgraph_revision_id']}/decision",
        json={"action": "approve"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["sources"][0]["state"] == "approved"
    assert approved.json()["merge_barrier"]["state"] == "ready"


def test_pdf_unresolvable_quote_is_visible_and_fails_closed(
    foundation_client,
    machine_payload,
    monkeypatch,
):
    workspace = _workspace(foundation_client, machine_payload)
    source = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "pump-manual.pdf",
        "SERIAL: HP7-000042\nPump vibration indicates a loose coupling.",
    ).json()["source"]

    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.create_cut_plan_workflow",
        lambda store, request, on_event=None: _cut_plan_for(store, request.pdf_id, [1]),
    )

    async def fake_retained_pipeline(store, request, on_event=None):
        return _pipeline_result(store, quote="A sentence that does not occur in the PDF.")

    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.draft_ontology_workflow",
        fake_retained_pipeline,
    )
    generated = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/g3/sources/{source['source_id']}/generate"
    )
    assert generated.status_code == 200, generated.text
    graph = generated.json()["sources"][0]["subgraph"]
    assert graph["approval_eligible"] is False
    codes = {item["code"] for item in graph["knowledge_gaps"]}
    assert "pdf_evidence_quote_unresolved" in codes
    assert "pdf_node_provenance_unresolved" in codes

    approval = foundation_client.post(
        f"/api/g3/subgraphs/{graph['source_subgraph_revision_id']}/decision",
        json={"action": "approve"},
    )
    assert approval.status_code == 409


def test_pdf_high_recall_candidates_without_typed_records_fail_closed(
    foundation_client,
    machine_payload,
    monkeypatch,
):
    monkeypatch.setenv("KG_LLM_MODE", "mock")
    monkeypatch.delenv("KG_LLM_FIXTURE", raising=False)
    monkeypatch.delenv("KG_LLM_MOCK_DIR", raising=False)
    workspace = _workspace(foundation_client, machine_payload)
    source = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "empty-typed-candidates.pdf",
        (
            "Problem: Pump vibration.\n"
            "Cause: The coupling is loose.\n"
            "Remedy: Tighten the coupling to specification."
        ),
    ).json()["source"]

    generated = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/g3/sources/{source['source_id']}/generate"
    )
    assert generated.status_code == 200, generated.text
    graph = generated.json()["sources"][0]["subgraph"]

    assert graph["publication_metrics"]["diagnostic_candidate_pages"] >= 1
    assert graph["publication_metrics"]["diagnostic_candidate_records"] == 1
    assert graph["publication_metrics"]["diagnostic_unresolved_records"] == 1
    # The source window is now durably disposed to review even when the mock
    # provider omits it. Accounting completeness is distinct from approval.
    assert graph["publication_metrics"]["diagnostic_accounting_complete"] is True
    gap = next(
        item for item in graph["knowledge_gaps"]
        if item["code"] == "pdf_diagnostic_record_review"
    )
    assert gap["blocking"] is True
    assert graph["approval_eligible"] is False

    approval = foundation_client.post(
        f"/api/g3/subgraphs/{graph['source_subgraph_revision_id']}/decision",
        json={"action": "approve"},
    )
    assert approval.status_code == 409


def test_pdf_exact_evidence_anchor_resolves_without_fuzzy_page_fallback(
    foundation_client,
    machine_payload,
    monkeypatch,
):
    workspace = _workspace(foundation_client, machine_payload)
    source = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "anchored-manual.pdf",
        "SERIAL: HP7-000042\nPump vibration indicates a loose coupling. Tighten the coupling.",
    ).json()["source"]

    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.create_cut_plan_workflow",
        lambda store, request, on_event=None: _cut_plan_for(store, request.pdf_id, [1]),
    )

    async def fake_retained_pipeline(store, request, on_event=None):
        anchor = store["pages"][0]["evidence_anchors"][0]
        return _pipeline_result(
            store,
            quote="Pump vibration indicates a loose coupling.",
            source_anchor=anchor,
        )

    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.draft_ontology_workflow",
        fake_retained_pipeline,
    )
    graph = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/g3/sources/{source['source_id']}/generate"
    ).json()["sources"][0]["subgraph"]

    assert graph["approval_eligible"] is True
    assert graph["knowledge_gaps"] == []
    assert len(graph["evidence"]) == 2


def test_pdf_heading_inside_a_longer_generated_quote_does_not_ground_relations(
    foundation_client,
    machine_payload,
    monkeypatch,
):
    workspace = _workspace(foundation_client, machine_payload)
    source = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "heading-only-manual.pdf",
        "SERIAL: HP7-000042\nTroubleshooting",
    ).json()["source"]

    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.create_cut_plan_workflow",
        lambda store, request, on_event=None: _cut_plan_for(store, request.pdf_id, [1]),
    )

    async def fake_retained_pipeline(store, request, on_event=None):
        anchor = store["pages"][0]["evidence_anchors"][0]
        return _pipeline_result(
            store,
            quote=(
                "SERIAL: HP7-000042 Troubleshooting explains that pump vibration "
                "indicates a loose coupling and requires tightening the coupling."
            ),
            source_anchor=anchor,
        )

    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.draft_ontology_workflow",
        fake_retained_pipeline,
    )
    graph = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/g3/sources/{source['source_id']}/generate"
    ).json()["sources"][0]["subgraph"]

    assert graph["relations"] == []
    assert "pdf_evidence_quote_unresolved" in {
        item["code"] for item in graph["knowledge_gaps"]
    }


def test_pdf_grounding_uses_full_canonical_span_beyond_display_excerpt(
    foundation_client,
    machine_payload,
):
    workspace_payload = _workspace(foundation_client, machine_payload)
    source_payload = upload_pdf(
        foundation_client,
        workspace_payload["workspace_id"],
        "long-span-manual.pdf",
        "SERIAL: HP7-000042\nPlaceholder diagnostic content.",
    ).json()["source"]
    workspace = WorkspaceRepository().get_by_id(workspace_payload["workspace_id"])
    source = SourceRepository().get(source_payload["source_id"])
    pdf_evidence = next(
        item
        for item in EvidenceRepository().list_evidence(
            workspace_id=workspace.workspace_id,
            source_id=source.source_id,
        )
        if item.locator.kind == "pdf"
    )
    operator_evidence = [
        item
        for item in EvidenceRepository().list_evidence(workspace_id=workspace.workspace_id)
        if item.locator.kind == "operator_input"
    ]

    support_quote = (
        "Pump vibration indicates a loose coupling. Tighten the coupling to specification."
    )
    prefix = "Introductory safety material without diagnostic support. " * 50
    canonical_text = prefix + support_quote
    assert len(prefix) > 2000
    preview_locator = pdf_evidence.locator.model_copy(
        update={"quote": canonical_text[:2000]}
    )
    expanded_evidence = pdf_evidence.model_copy(update={
        "locator": preview_locator,
        "provenance_refs": [
            item.model_copy(update={"locator": preview_locator})
            for item in pdf_evidence.provenance_refs
        ],
        "content": pdf_evidence.content.model_copy(update={
            "observation": canonical_text,
            "semantic_texts": {"observation": canonical_text},
        }),
    })
    assert support_quote not in expanded_evidence.locator.quote

    result = _pipeline_result(
        {
            "asset_identity": workspace.asset.model_dump(mode="json"),
            "source_title": source.file_name,
        },
        quote=support_quote,
        source_anchor=expanded_evidence.evidence_id,
    )
    revision = PdfSourceSubgraphBuilder()._to_revision(
        workspace=workspace,
        source=source,
        result=result,
        evidence=[expanded_evidence, *operator_evidence],
        fingerprint="2" * 64,
        config_hash="3" * 64,
        supersedes=None,
    )

    published_evidence = next(
        item for item in revision.evidence
        if item.evidence_id == expanded_evidence.evidence_id
    )
    assert support_quote not in published_evidence.excerpt
    assert support_quote in published_evidence.locator["canonical_text"]
    assert revision.validation.passed is True
    assert (
        revision.validation.relation_grounding_total
        == revision.validation.relation_grounding_passed
        == 4
    )


def test_pdf_generation_metrics_are_persisted_with_revision(
    foundation_client,
    machine_payload,
    monkeypatch,
):
    workspace = _workspace(foundation_client, machine_payload)
    source = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "metered-manual.pdf",
        "SERIAL: HP7-000042\nPump vibration indicates a loose coupling. Tighten the coupling.",
    ).json()["source"]

    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.create_cut_plan_workflow",
        lambda store, request, on_event=None: _cut_plan_for(store, request.pdf_id, [1]),
    )

    async def fake_retained_pipeline(store, request, on_event=None):
        model_metrics = {
            "label": "GPT-5.6 Terra",
            "llm_calls": 2,
            "prompt_tokens": 1_000,
            "cached_prompt_tokens": 200,
            "non_cached_prompt_tokens": 800,
            "completion_tokens": 100,
            "total_tokens": 1_100,
            "estimated_cost_usd": 0.0028,
        }
        store["run_metrics"] = {
            "stages": {
                "ontology": {
                    "stage": "ontology",
                    "duration_seconds": 1.25,
                    **{key: value for key, value in model_metrics.items() if key != "label"},
                    "models": ["gpt-5.6-terra"],
                    "operations": ["ontology_extract"],
                    "by_model": {"gpt-5.6-terra": model_metrics},
                    "details": {"selected_pages": 1, "chunk_count": 1},
                },
            },
        }
        return _pipeline_result(store, quote="Pump vibration indicates a loose coupling.")

    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.draft_ontology_workflow",
        fake_retained_pipeline,
    )
    generated = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/g3/sources/{source['source_id']}/generate"
    ).json()
    metrics = generated["sources"][0]["subgraph"]["generation_metrics"]

    assert metrics["llm_calls"] == 2
    assert metrics["total_tokens"] == 1_100
    assert metrics["estimated_cost_usd"] == 0.0028
    assert metrics["stages"]["ontology"]["details"]["chunk_count"] == 1
    assert metrics["by_model"]["gpt-5.6-terra"]["prompt_tokens"] == 1_000

    persisted = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/g3/subgraphs"
    ).json()["sources"][0]["subgraph"]["generation_metrics"]
    assert persisted == metrics


def test_pdf_cut_plan_segments_diagnostics_before_ontology(
    foundation_client,
    machine_payload,
    monkeypatch,
):
    workspace = _workspace(foundation_client, machine_payload)
    source = upload_pdf_pages(
        foundation_client,
        workspace["workspace_id"],
        "segmented-manual.pdf",
        [
            "SERIAL: HP7-000042\nGeneral safety and intended use.",
            "Troubleshooting: pump vibration indicates a loose coupling. Tighten the coupling.",
            "Cleaning and storage instructions.",
        ],
    ).json()["source"]

    def fake_cut_plan(store, request, on_event=None):
        assert [page["page_number"] for page in store["pages"]] == [1, 2, 3]
        section = SectionInfo(
            name="Troubleshooting",
            page_range=PageRange(start=2, end=2),
            source="rule",
            reasoning="Diagnostic chapter",
        )
        store["asset_identity"] = {"asset_id": "manual_inference_must_not_win"}
        store["cut_plan"] = {
            "pdf_id": request.pdf_id,
            "total_pages": 3,
            "sections": [{"name": "Troubleshooting", "start": 2, "end": 2, "source": "rule"}],
            "pages_to_keep": [2],
            "page_offset": 0,
            "skipped": False,
        }
        return CutPlan(
            pdf_id=request.pdf_id,
            total_pages=3,
            sections=[section],
            pages_to_keep=[2],
            page_offset=0,
            skipped=False,
        )

    async def fake_retained_pipeline(store, request, on_event=None):
        assert request.pages_to_keep == [1, 2, 3]
        assert store["cut_plan"]["pages_to_keep"] == [2]
        assert store["asset_identity"]["asset_id"] == workspace["asset"]["asset_id"]
        return _pipeline_result(
            store,
            quote=(
                "Troubleshooting: pump vibration indicates a loose coupling. "
                "Tighten the coupling."
            ),
            source_page=2,
        )

    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.create_cut_plan_workflow",
        fake_cut_plan,
    )
    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.draft_ontology_workflow",
        fake_retained_pipeline,
    )

    generated = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/g3/sources/{source['source_id']}/generate"
    )
    assert generated.status_code == 200, generated.text
    graph = generated.json()["sources"][0]["subgraph"]
    assert graph["pdf_extraction_scope"] == {
        "method": "retained_cut_plan",
        "total_pages": 3,
        "selected_pages": [1, 2, 3],
        "unselected_pages": [],
        "diagnostic_pages": [1, 2, 3],
        "structural_pages": [1, 3],
        "retrieval_pages": [1, 2, 3],
        "sections": [{
            "name": "Troubleshooting",
            "start_page": 2,
            "end_page": 2,
            "source": "rule",
        }],
        "page_offset": 0,
        "skipped": False,
    }
    published_evidence_ids = {
        evidence_id
        for claim in [*graph["nodes"], *graph["relations"]]
        for evidence_id in claim["evidence_ids"]
    }
    assert {
        item["locator"]["page"]
        for item in graph["evidence"]
        if item["locator"]["kind"] == "pdf"
        and item["evidence_id"] in published_evidence_ids
    } == {2}


def test_pdf_generation_fails_closed_when_cut_plan_fails(
    foundation_client,
    machine_payload,
    monkeypatch,
):
    workspace = _workspace(foundation_client, machine_payload)
    source = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "unscopable-manual.pdf",
        "SERIAL: HP7-000042\nPump troubleshooting.",
    ).json()["source"]

    def failed_cut_plan(store, request, on_event=None):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.create_cut_plan_workflow",
        failed_cut_plan,
    )

    generated = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/g3/sources/{source['source_id']}/generate"
    )
    assert generated.status_code == 409
    assert generated.json()["detail"] == "La segmentazione diagnostica del PDF non è riuscita"

    snapshot = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/g3/subgraphs"
    ).json()
    source_view = next(item for item in snapshot["sources"] if item["source_id"] == source["source_id"])
    assert source_view["state"] == "ready"
    assert source_view["subgraph"] is None


def test_pdf_generation_returns_a_reviewable_error_when_semantic_build_fails(
    foundation_client,
    machine_payload,
    monkeypatch,
):
    workspace = _workspace(foundation_client, machine_payload)
    source = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "semantic-failure-manual.pdf",
        "SERIAL: HP7-000042\nPump troubleshooting.",
    ).json()["source"]

    async def failed_pipeline(store, request, on_event=None):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(
        "backend.services.pdf_source_subgraph_generation.draft_ontology_workflow",
        failed_pipeline,
    )

    generated = foundation_client.post(
        f"/api/workspaces/{workspace['workspace_id']}/g3/sources/{source['source_id']}/generate"
    )
    assert generated.status_code == 409
    assert generated.json()["detail"] == (
        "La costruzione semantica del PDF non è riuscita: provider unavailable"
    )

    snapshot = foundation_client.get(
        f"/api/workspaces/{workspace['workspace_id']}/g3/subgraphs"
    ).json()
    source_view = next(item for item in snapshot["sources"] if item["source_id"] == source["source_id"])
    assert source_view["state"] == "ready"
    assert source_view["subgraph"] is None


def test_pdf_extraction_scope_must_be_a_complete_disjoint_page_partition():
    with pytest.raises(ValueError, match="must be disjoint"):
        PdfExtractionScope(
            total_pages=2,
            selected_pages=[1],
            unselected_pages=[1],
        )

    with pytest.raises(ValueError, match="partition total_pages"):
        PdfExtractionScope(
            total_pages=3,
            selected_pages=[2],
            unselected_pages=[1],
        )


def test_pdf_preparation_fingerprint_is_stable_and_invalidates_on_scope_change(
    foundation_client,
    machine_payload,
):
    workspace = _workspace(foundation_client, machine_payload)
    source_payload = upload_pdf(
        foundation_client,
        workspace["workspace_id"],
        "fingerprint-manual.pdf",
        "SERIAL: HP7-000042\nInspect the pump coupling.",
    ).json()["source"]
    source = SourceRepository().get(source_payload["source_id"])
    repository = EvidenceRepository()
    scope = repository.current_scope(source.source_id)
    evidence = repository.list_evidence(
        workspace_id=workspace["workspace_id"], source_id=source.source_id,
    )

    first = pdf_preparation_fingerprint(source=source, scope=scope, evidence=evidence)
    reordered = pdf_preparation_fingerprint(
        source=source, scope=scope, evidence=list(reversed(evidence)),
    )
    changed_scope = {**scope, "version": scope["version"] + 1}
    changed = pdf_preparation_fingerprint(
        source=source, scope=changed_scope, evidence=evidence,
    )
    assert first == reordered
    assert first != changed


def test_pdf_claims_backed_only_by_low_confidence_ocr_cannot_be_approved(
    foundation_client,
    machine_payload,
):
    workspace_payload = _workspace(foundation_client, machine_payload)
    source_payload = upload_pdf(
        foundation_client,
        workspace_payload["workspace_id"],
        "ocr-manual.pdf",
        "SERIAL: HP7-000042\nPump vibration indicates a loose coupling.",
    ).json()["source"]
    workspace = WorkspaceRepository().get_by_id(workspace_payload["workspace_id"])
    source = SourceRepository().get(source_payload["source_id"])
    evidence = EvidenceRepository().list_evidence(
        workspace_id=workspace.workspace_id, source_id=source.source_id,
    )
    low_confidence = [
        item.model_copy(update={
            "quality_flags": list(dict.fromkeys([
                *item.quality_flags, QualityFlag.OCR_LOW_CONFIDENCE,
            ])),
        })
        for item in evidence
    ]
    operator_evidence = [
        item
        for item in EvidenceRepository().list_evidence(workspace_id=workspace.workspace_id)
        if item.locator.kind == "operator_input"
    ]
    quote = low_confidence[0].locator.quote
    result = _pipeline_result(
        {
            "asset_identity": workspace.asset.model_dump(mode="json"),
            "source_title": source.file_name,
        },
        quote=quote,
        source_anchor=low_confidence[0].evidence_id,
    )

    revision = PdfSourceSubgraphBuilder()._to_revision(
        workspace=workspace,
        source=source,
        result=result,
        evidence=[*low_confidence, *operator_evidence],
        fingerprint="0" * 64,
        config_hash="1" * 64,
        supersedes=None,
    )
    assert revision.validation.passed is True
    assert revision.approval_eligible is False
    low_confidence_gap = next(
        item
        for item in revision.knowledge_gaps
        if item.code == "pdf_ocr_low_confidence"
    )
    assert set(low_confidence_gap.evidence_ids).issubset(revision.evidence_ids)
    assert set(low_confidence_gap.evidence_ids).issubset({
        item.evidence_id for item in revision.evidence
    })


def test_pdf_relation_ids_are_invariant_to_pipeline_relation_order(
    foundation_client,
    machine_payload,
):
    workspace_payload = _workspace(foundation_client, machine_payload)
    source_payload = upload_pdf(
        foundation_client,
        workspace_payload["workspace_id"],
        "stable-relation-ids.pdf",
        (
            "SERIAL: HP7-000042\nPump vibration indicates a loose coupling. "
            "Tighten the coupling to specification."
        ),
    ).json()["source"]
    workspace = WorkspaceRepository().get_by_id(workspace_payload["workspace_id"])
    source = SourceRepository().get(source_payload["source_id"])
    all_evidence = EvidenceRepository().list_evidence(workspace_id=workspace.workspace_id)
    pdf_evidence = next(item for item in all_evidence if item.source_id == source.source_id)
    result = _pipeline_result(
        {
            "asset_identity": workspace.asset.model_dump(mode="json"),
            "source_title": source.file_name,
        },
        quote=pdf_evidence.locator.quote,
        source_anchor=pdf_evidence.evidence_id,
    )
    reversed_result = result.model_copy(update={
        "ontology": result.ontology.model_copy(update={
            "relations": list(reversed(result.ontology.relations)),
        }),
    })

    builder = PdfSourceSubgraphBuilder()
    forward = builder._to_revision(
        workspace=workspace,
        source=source,
        result=result,
        evidence=all_evidence,
        fingerprint="4" * 64,
        config_hash="5" * 64,
        supersedes=None,
    )
    reversed_revision = builder._to_revision(
        workspace=workspace,
        source=source,
        result=reversed_result,
        evidence=all_evidence,
        fingerprint="4" * 64,
        config_hash="5" * 64,
        supersedes=None,
    )

    def relation_ids(revision):
        return {
            (item.relation_type, item.from_id, item.to_id): item.relation_id
            for item in revision.relations
        }

    assert relation_ids(forward)
    assert relation_ids(forward) == relation_ids(reversed_revision)


def test_pdf_incomplete_diagnostic_contract_cannot_report_complete_accounting(
    foundation_client,
    machine_payload,
):
    workspace_payload = _workspace(foundation_client, machine_payload)
    source_payload = upload_pdf(
        foundation_client,
        workspace_payload["workspace_id"],
        "incomplete-contract.pdf",
        "Pump vibration indicates a loose coupling. Tighten the coupling.",
    ).json()["source"]
    workspace = WorkspaceRepository().get_by_id(workspace_payload["workspace_id"])
    source = SourceRepository().get(source_payload["source_id"])
    all_evidence = EvidenceRepository().list_evidence(workspace_id=workspace.workspace_id)
    pdf_evidence = next(item for item in all_evidence if item.source_id == source.source_id)
    result = _pipeline_result(
        {
            "asset_identity": workspace.asset.model_dump(mode="json"),
            "source_title": source.file_name,
        },
        quote=pdf_evidence.locator.quote,
        source_anchor=pdf_evidence.evidence_id,
    )
    result = result.model_copy(update={
        "status": "blocked",
        "is_schema_compliant": False,
        "is_ready_for_human_review": False,
        "diagnostic_contract_report": {
            **result.diagnostic_contract_report,
            "parsed": False,
            "finish_reason": "incomplete",
            "contract_failure_count": 1,
            "escalation_recommended": True,
        },
    })

    revision = PdfSourceSubgraphBuilder()._to_revision(
        workspace=workspace,
        source=source,
        result=result,
        evidence=all_evidence,
        fingerprint="6" * 64,
        config_hash="7" * 64,
        supersedes=None,
    )

    assert revision.publication_metrics["diagnostic_accounting_complete"] is False
    assert revision.approval_eligible is False
    assert "pdf_diagnostic_contract_incomplete" in {
        item.code for item in revision.knowledge_gaps
    }


def test_pdf_review_disposition_is_persisted_and_accounted_but_not_approvable(
    foundation_client,
    machine_payload,
):
    workspace_payload = _workspace(foundation_client, machine_payload)
    source_payload = upload_pdf(
        foundation_client,
        workspace_payload["workspace_id"],
        "reviewed-candidate.pdf",
        "Pump vibration indicates a loose coupling. Tighten the coupling.",
    ).json()["source"]
    workspace = WorkspaceRepository().get_by_id(workspace_payload["workspace_id"])
    source = SourceRepository().get(source_payload["source_id"])
    all_evidence = EvidenceRepository().list_evidence(workspace_id=workspace.workspace_id)
    pdf_evidence = next(item for item in all_evidence if item.source_id == source.source_id)
    result = _pipeline_result(
        {
            "asset_identity": workspace.asset.model_dump(mode="json"),
            "source_title": source.file_name,
        },
        quote=pdf_evidence.locator.quote,
        source_anchor=pdf_evidence.evidence_id,
    )
    raw_candidate = {
        "record_lineage_id": "record-review",
        "record_anchor": pdf_evidence.evidence_id,
        "resolution_status": "action_stated",
        "symptom": {"label": "Pump vibration"},
    }
    attempt = {
        "attempt": 2,
        "model": "gpt-5.6-terra",
        "reasoning_effort": "medium",
        "recovery": True,
    }
    review_record = {
        **result.diagnostic_contract_report["records"][0],
        "disposition": "review",
        "drop_reasons": [{
            "code": "ambiguous_branch",
            "path": "failure_modes.0",
            "message": "The row pairing needs review.",
        }],
        "candidate": raw_candidate,
        "attempt": attempt,
        "resolved_evidence_ids": [pdf_evidence.evidence_id],
    }
    contract_report = {
        **result.diagnostic_contract_report,
        "publish_count": 0,
        "unresolved_count": 1,
        "records": [review_record],
        "chunks": [{"chunk_index": 0, "attempts": [attempt]}],
    }
    result = result.model_copy(update={"diagnostic_contract_report": contract_report})

    revision = PdfSourceSubgraphBuilder()._to_revision(
        workspace=workspace,
        source=source,
        result=result,
        evidence=all_evidence,
        fingerprint="8" * 64,
        config_hash="9" * 64,
        supersedes=None,
    )

    assert revision.publication_metrics["diagnostic_accounting_complete"] is True
    assert revision.approval_eligible is False
    assert revision.diagnostic_compilation_ledger == contract_report
    assert revision.diagnostic_compilation_ledger["records"][0]["candidate"] == raw_candidate
    assert revision.diagnostic_compilation_ledger["chunks"][0]["attempts"] == [attempt]
    serialized = revision.model_dump(mode="json")
    assert serialized["diagnostic_compilation_ledger"]["records"][0]["attempt"] == attempt
    review_gap = next(
        item
        for item in revision.knowledge_gaps
        if item.code == "pdf_diagnostic_record_review"
    )
    assert review_gap.blocking is True
    assert review_gap.disposition == "review"
