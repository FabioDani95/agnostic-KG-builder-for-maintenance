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
from backend.services.pdf_source_subgraph_generation import (
    PdfSourceSubgraphBuilder,
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


def _pipeline_result(
    store: dict,
    *,
    quote: str,
    source_page: int = 1,
) -> OntologyPipelineResponse:
    asset = store["asset_identity"]
    evidence = [OntologyEvidence(
        source_page=source_page,
        source_reference=f"PAGE {source_page}",
        quote=quote,
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
                    "material_context": "Drive train",
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
                "Component": [],
                "ErrorCode": [],
            },
            relations=[
                OntologyRelationInstance(
                    name="MAY_INDICATE",
                    from_type="Symptom",
                    from_id="SYM-PDF-1",
                    to_type="FailureMode",
                    to_id="FM-PDF-1",
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
        return _cut_plan_for(store, request.pdf_id, [1])

    async def fake_retained_pipeline(store, request, on_event=None):
        nonlocal calls
        calls += 1
        assert request.pdf_id == source["source_id"]
        assert store["asset_identity"]["asset_id"] == workspace["asset"]["asset_id"]
        return _pipeline_result(store, quote=store["pages"][0]["text"])

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
        "sections": [],
        "page_offset": 0,
        "skipped": True,
    }
    assert {node["node_type"] for node in graph["nodes"]} == {
        "Asset", "Symptom", "FailureMode", "CorrectiveAction",
    }
    assert {relation["relation_type"] for relation in graph["relations"]} == {
        "MAY_INDICATE", "RESOLVED_BY",
    }
    assert graph["evidence"]
    assert all(item["locator"]["kind"] == "pdf" for item in graph["evidence"])
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
        assert request.pages_to_keep == [2]
        assert store["cut_plan"]["pages_to_keep"] == [2]
        assert store["asset_identity"]["asset_id"] == workspace["asset"]["asset_id"]
        diagnostic_page = next(page for page in store["pages"] if page["page_number"] == 2)
        return _pipeline_result(
            store,
            quote=diagnostic_page["text"],
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
        "selected_pages": [2],
        "unselected_pages": [1, 3],
        "sections": [{
            "name": "Troubleshooting",
            "start_page": 2,
            "end_page": 2,
            "source": "rule",
        }],
        "page_offset": 0,
        "skipped": False,
    }
    assert {item["locator"]["page"] for item in graph["evidence"]} == {2}


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
    quote = low_confidence[0].locator.quote
    result = _pipeline_result(
        {
            "asset_identity": workspace.asset.model_dump(mode="json"),
            "source_title": source.file_name,
        },
        quote=quote,
    )

    revision = PdfSourceSubgraphBuilder()._to_revision(
        workspace=workspace,
        source=source,
        result=result,
        evidence=low_confidence,
        fingerprint="0" * 64,
        config_hash="1" * 64,
        supersedes=None,
    )
    assert revision.validation.passed is True
    assert revision.approval_eligible is False
    assert "pdf_ocr_low_confidence" in {item.code for item in revision.knowledge_gaps}
