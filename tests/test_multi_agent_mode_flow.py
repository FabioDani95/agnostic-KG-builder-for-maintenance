import asyncio

from fastapi.testclient import TestClient

from backend import app_config
from backend.agents.ontology_draft_agent import run_ontology_draft_agent
from backend.agents.scoping_agent import run_scoping_agent
from backend.graph.store import seed_graph_state
from backend.main import app
from backend.models import (
    CutPlan,
    CutPlanRequest,
    ExtractionResult,
    ExtractRequest,
    OntologyDraftRequest,
    OntologyPipelineResponse,
)
from backend.routers.upload import pdf_store
from backend.services.extraction_pipeline import run_extraction_pipeline
from backend.services.run_metrics import ensure_run_metrics

client = TestClient(app)


def _sample_store(pdf_id: str) -> dict:
    store = {
        "pdf_id": pdf_id,
        "filename": "manual.pdf",
        "pages": [
            {"page_number": 1, "text": "Troubleshooting content."},
            {"page_number": 2, "text": "Corrective action content."},
        ],
        "page_count": 2,
        "source_type": "Service manual",
        "source_title": "Mock Robot",
        "selected_models": {
            "scoping": None,
            "ontology_draft": None,
            "extraction": None,
        },
    }
    ensure_run_metrics(store)
    seed_graph_state(store, pdf_id)
    return store


def _sample_triplet_payload() -> list[dict]:
    return [
        {
            "symptom": {
                "symptom_id": "SYM-001",
                "name": "Robot does not start",
                "description": "Startup failure",
                "severity": "High",
            },
            "failure_modes": [
                {
                    "failure_mode_id": "FM-001",
                    "name": "Power board fault",
                    "description": "Board failure",
                    "material_context": "Power board",
                    "linked_symptom_id": "SYM-001",
                },
            ],
            "corrective_actions": [
                {
                    "action_id": "CA-001",
                    "name": "Replace power board",
                    "description": "Replace faulty board",
                    "instruction_text": "Install a new board and reboot.",
                    "source_type": "Service manual",
                    "source_title": "Mock Robot",
                    "source_page": 1,
                    "linked_failure_mode_id": "FM-001",
                },
            ],
        },
    ]


def setup_function():
    pdf_store.clear()
    app_config._runtime_overrides.clear()


def teardown_function():
    pdf_store.clear()
    app_config._runtime_overrides.clear()


def test_scoping_agent_uses_workflow_and_keeps_cut_plan_shape(monkeypatch):
    store = _sample_store("pdf-cut")
    called = {"workflow": False}

    def fake_workflow(store, req):
        called["workflow"] = True
        return CutPlan.model_validate({
            "pdf_id": req.pdf_id,
            "total_pages": 2,
            "sections": [],
            "pages_to_keep": [1, 2],
            "page_offset": 0,
            "toc": None,
            "skipped": False,
            "product_info": None,
        })

    monkeypatch.setattr("backend.agents.scoping_agent.create_cut_plan_workflow", fake_workflow)

    result = run_scoping_agent(store, CutPlanRequest(pdf_id="pdf-cut", model_name="gpt-5.4-nano", page_offset=0))
    payload = result.model_dump()

    assert called["workflow"] is True
    assert payload["pages_to_keep"] == [1, 2]
    assert set(payload.keys()) == {
        "pdf_id",
        "total_pages",
        "sections",
        "pages_to_keep",
        "page_offset",
        "page_offset_detection",
        "toc",
        "skipped",
        "product_info",
    }
    assert store["graph_state"]["current_phase"] == "scoping"


def test_ontology_draft_agent_uses_workflow_and_keeps_shape(monkeypatch):
    store = _sample_store("pdf-ontology")
    called = {"workflow": False}

    async def fake_workflow(store, req):
        called["workflow"] = True
        return OntologyPipelineResponse.model_validate({
            "status": "ready",
            "ontology": {
                "ontology_name": "DiagnosticOntology",
                "version": "1.0",
                "language": "en",
                "source_type": req.source_type,
                "source_title": req.source_title,
                "nodes": {
                    "Asset": [],
                    "Component": [],
                    "Symptom": [],
                    "FailureMode": [],
                    "CorrectiveAction": [],
                    "ErrorCode": [],
                },
                "relations": [],
            },
            "semantic_issues": [],
            "schema_issues": [],
            "human_required_fields": [],
            "is_schema_compliant": True,
            "is_ready_for_human_review": True,
            "retry_count": 0,
            "graph_issues": [],
            "suggested_relations": [],
        })

    monkeypatch.setattr("backend.agents.ontology_draft_agent.draft_ontology_workflow", fake_workflow)

    result = asyncio.run(run_ontology_draft_agent(
        store,
        OntologyDraftRequest(
            pdf_id="pdf-ontology",
            source_type="Service manual",
            source_title="Mock Robot",
            model_name="gpt-5.4",
            target_language="en",
        ),
    ))
    payload = result.model_dump()

    assert called["workflow"] is True
    assert payload["status"] == "ready"
    assert set(payload.keys()) == {
        "status",
        "ontology",
        "semantic_issues",
        "schema_issues",
        "human_required_fields",
        "is_schema_compliant",
        "is_ready_for_human_review",
        "retry_count",
        "graph_issues",
        "suggested_relations",
        "confidence_report",
            "diagnostic_contract_report",
            "resolution_completion_report",
            "canonicalization_report",
            "review_queue",
        "review_summary",
    }
    assert store["graph_state"]["current_phase"] == "ontology_draft"


def test_extraction_pipeline_uses_extraction_agent_and_keeps_shape(monkeypatch):
    store = _sample_store("pdf-extract")
    called = {"agent": False}
    validation = {"called": False}
    advanced = {"coverage": False, "grounding": False, "conflict": False, "refiner": False}

    def fake_agent(store, req):
        called["agent"] = True
        return ExtractionResult.model_validate({
            "triplets": _sample_triplet_payload(),
            "raw_symptom_table": "",
            "raw_failure_mode_table": "",
            "raw_corrective_action_table": "",
        })

    monkeypatch.setattr("backend.services.extraction_pipeline.run_extraction_agent", fake_agent)
    monkeypatch.setattr(
        "backend.services.extraction_pipeline.run_validation_agent",
        lambda store: validation.update({"called": True}) or ([], {"total_entities": 0}),
    )
    monkeypatch.setattr("backend.services.extraction_pipeline.run_coverage_agent", lambda store: advanced.update({"coverage": True}) or {})
    monkeypatch.setattr("backend.services.extraction_pipeline.run_grounding_agent", lambda store: advanced.update({"grounding": True}) or ([], []))
    monkeypatch.setattr(
        "backend.services.extraction_pipeline.run_conflict_resolution_agent",
        lambda store: advanced.update({"conflict": True}) or [],
    )
    monkeypatch.setattr(
        "backend.services.extraction_pipeline.run_refiner_agent",
        lambda store: advanced.update({"refiner": True}) or ([], []),
    )

    result = run_extraction_pipeline(
        store,
        ExtractRequest(
            pdf_id="pdf-extract",
            source_type="Service manual",
            source_title="Mock Robot",
            model_name="gpt-5.4",
            pages_to_keep=[1, 2],
            target_language="en",
        ),
    )
    payload = result.model_dump()

    assert called["agent"] is True
    assert validation["called"] is True
    assert advanced == {"coverage": False, "grounding": False, "conflict": False, "refiner": False}
    assert len(payload["triplets"]) == 1
    assert set(payload.keys()) == {
        "triplets",
        "raw_symptom_table",
        "raw_failure_mode_table",
        "raw_corrective_action_table",
    }


def test_extraction_pipeline_runs_phase3_agents_when_enabled_and_preserves_shape(monkeypatch):
    store = _sample_store("pdf-phase3")
    call_order: list[str] = []

    def fake_extraction(store, req):
        store["graph_state"]["selected_pages"] = [1, 2]
        store["graph_state"]["cleaned_triplets"] = _sample_triplet_payload()
        return ExtractionResult.model_validate({
            "triplets": _sample_triplet_payload(),
            "raw_symptom_table": "",
            "raw_failure_mode_table": "",
            "raw_corrective_action_table": "",
        })

    def fake_validation(store):
        call_order.append("validation")
        store["graph_state"]["entity_verdicts"] = [
            {
                "entity_id": "CA-001",
                "entity_type": "CorrectiveAction",
                "verdict": "needs_refinement",
                "reasons": ["weak support"],
                "source_page": 1,
                "source_pages": [1],
                "grounding_score": 0.6,
                "agent": "ValidationAgent",
                "advisory_only": True,
            },
        ]
        store["graph_state"]["validation_summary"] = {
            "total_entities": 1,
            "accepted": 0,
            "needs_refinement": 1,
            "needs_human": 0,
            "flagged_entities": 1,
            "flagged_entity_ids": ["CA-001"],
            "advisory_only": True,
        }
        return store["graph_state"]["entity_verdicts"], store["graph_state"]["validation_summary"]

    def fake_coverage(store):
        call_order.append("coverage")
        store["graph_state"]["coverage_map"] = {
            1: {
                "has_content": True,
                "extracted_entities": ["Robot does not start"],
                "gap_type": "partially_covered",
                "recommendation": "Review flagged entities.",
            },
        }
        return store["graph_state"]["coverage_map"]

    def fake_grounding(store):
        call_order.append("grounding")
        return [], store["graph_state"].get("entity_verdicts", [])

    def fake_conflict(store):
        call_order.append("conflict")
        return []

    def fake_refiner(store):
        call_order.append("refiner")
        store["graph_state"]["cleaned_triplets"][0]["corrective_actions"][0]["instruction_text"] = "Refined action text."
        store["graph_state"]["refinement_log"] = [
            {"entity_id": "CA-001", "attempt": 1, "result": "updated", "reasoning": "Refined deterministically."},
        ]
        return {
            "attempted_entity_ids": ["CA-001"],
            "changed_entity_ids": ["CA-001"],
            "exhausted_entity_ids": [],
            "refinement_log": store["graph_state"]["refinement_log"],
        }

    monkeypatch.setattr("backend.services.extraction_pipeline.run_extraction_agent", fake_extraction)
    monkeypatch.setattr("backend.services.extraction_pipeline.run_validation_agent", fake_validation)
    monkeypatch.setattr("backend.services.extraction_pipeline.run_coverage_agent", fake_coverage)
    monkeypatch.setattr("backend.services.extraction_pipeline.run_grounding_agent", fake_grounding)
    monkeypatch.setattr("backend.services.extraction_pipeline.run_conflict_resolution_agent", fake_conflict)
    monkeypatch.setattr("backend.services.extraction_pipeline.run_refiner_agent", fake_refiner)
    monkeypatch.setattr(
        "backend.services.extraction_pipeline.get_agents_config",
        lambda: {
            "validation": {"enabled": True},
            "coverage": {"enabled": True},
            "grounding": {"enabled": True},
            "conflict_resolution": {"enabled": True},
            "refiner": {"enabled": True},
        },
    )

    result = run_extraction_pipeline(
        store,
        ExtractRequest(
            pdf_id="pdf-phase3",
            source_type="Service manual",
            source_title="Mock Robot",
            model_name="gpt-5.4",
            pages_to_keep=[1, 2],
            target_language="en",
        ),
    )
    payload = result.model_dump()

    assert call_order == [
        "validation",
        "coverage",
        "grounding",
        "refiner",
        "validation",
        "grounding",
        "conflict",
    ]
    assert payload["triplets"][0]["corrective_actions"][0]["instruction_text"] == "Refined action text."
    assert set(payload.keys()) == {
        "triplets",
        "raw_symptom_table",
        "raw_failure_mode_table",
        "raw_corrective_action_table",
    }


def test_generate_json_reads_ontology_from_graph_state_in_multi_agent(monkeypatch):
    store = _sample_store("pdf-generate")
    store["graph_state"]["selected_models"]["extraction"] = "gpt-5.4-mini"
    store["graph_state"]["ontology_pipeline"] = {
        "ontology": {
            "ontology_name": "DiagnosticOntology",
            "version": "1.0",
            "language": "en",
            "source_type": "Service manual",
            "source_title": "Graph State Robot",
            "nodes": {
                "Asset": [],
                "Component": [],
                "Symptom": [],
                "FailureMode": [],
                "CorrectiveAction": [],
                "ErrorCode": [],
            },
            "relations": [],
        },
        "schema_issues": [],
        "human_required_fields": [],
    }
    pdf_store["pdf-generate"] = store

    captured = {}

    def fake_merge(base_ontology, validated_triplets):
        captured["base_ontology"] = base_ontology
        return {
            "ontology_name": "DiagnosticOntology",
            "version": "1.0",
            "language": "en",
            "source_type": "Service manual",
            "source_title": "Graph State Robot",
            "nodes": {
                "Asset": [],
                "Component": [],
                "Symptom": [],
                "FailureMode": [],
                "CorrectiveAction": [],
                "ErrorCode": [],
            },
            "relations": [],
        }

    monkeypatch.setattr("backend.routers.generate.merge_validated_triplets", fake_merge)
    monkeypatch.setattr("backend.routers.generate.validate_ontology_instance", lambda ontology: ([], []))
    monkeypatch.setattr(
        "backend.routers.generate.cleanup_export_ontology",
        lambda ontology, target_language, model_name: (
            captured.update({"cleanup_model_name": model_name}) or ontology,
            {},
            {},
        ),
    )
    monkeypatch.setattr(
        "backend.routers.generate.prepare_exported_ontology",
        lambda ontology: {"metadata": {"version": "1.0"}, "nodes": {}, "relationships": []},
    )
    monkeypatch.setattr(
        "backend.routers.generate.persist_exported_ontology",
        lambda payload, pdf_id, manual_filename=None: {
            "target_path": "/tmp/mock_export.json",
            "filename": "ontology.json",
            "download_filename": "mock_export.json",
            "metrics_path": "/tmp/metrics.json",
            "directory_name": "manual",
        },
    )
    monkeypatch.setattr(
        "backend.routers.generate.persist_export_metrics",
        lambda metrics_payload, ontology_payload, export_info, manual_filename=None: {
            "target_path": "/tmp/metrics.json",
            "filename": "metrics.json",
        },
    )

    response = client.post("/generate-json", json={
        "pdf_id": "pdf-generate",
        "validated_triplets": _sample_triplet_payload(),
        "target_language": "en",
    })

    assert response.status_code == 200
    assert captured["base_ontology"]["source_title"] == "Graph State Robot"
    assert captured["cleanup_model_name"] == "gpt-5.4-mini"
    assert store["graph_state"]["export_base"] == "ontology_draft"
    assert store["metrics_path"] == "/tmp/metrics.json"
    assert response.headers["content-disposition"].endswith('filename=mock_export.json')


def test_generate_json_minimal_fallback_autofills_asset_identity(monkeypatch):
    store = _sample_store("pdf-generate-fallback")
    store["filename"] = "eagle_s3l_laser_cutting_system_service_manual.pdf"
    store["source_title"] = "Eagle Automatic Laser Cutting System Model: Eagle S3L."
    pdf_store["pdf-generate-fallback"] = store

    captured = {}

    def fake_merge(base_ontology, validated_triplets):
        captured["base_ontology"] = base_ontology
        return base_ontology

    monkeypatch.setattr("backend.routers.generate.merge_validated_triplets", fake_merge)
    monkeypatch.setattr("backend.routers.generate.validate_ontology_instance", lambda ontology: ([], []))
    monkeypatch.setattr(
        "backend.routers.generate.cleanup_export_ontology",
        lambda ontology, target_language, model_name: (ontology, {}, {}),
    )
    monkeypatch.setattr(
        "backend.routers.generate.prepare_exported_ontology",
        lambda ontology: {"metadata": {"version": "1.0"}, "nodes": ontology.get("nodes", {}), "relationships": []},
    )
    monkeypatch.setattr(
        "backend.routers.generate.persist_exported_ontology",
        lambda payload, pdf_id, manual_filename=None: {
            "target_path": "/tmp/mock_export.json",
            "filename": "ontology.json",
            "download_filename": "mock_export.json",
            "metrics_path": "/tmp/metrics.json",
            "directory_name": "manual",
        },
    )
    monkeypatch.setattr(
        "backend.routers.generate.persist_export_metrics",
        lambda metrics_payload, ontology_payload, export_info, manual_filename=None: {
            "target_path": "/tmp/metrics.json",
            "filename": "metrics.json",
        },
    )

    response = client.post("/generate-json", json={
        "pdf_id": "pdf-generate-fallback",
        "validated_triplets": _sample_triplet_payload(),
        "target_language": "en",
    })

    assert response.status_code == 200
    asset = captured["base_ontology"]["nodes"]["Asset"][0]
    assert asset["brand"] == "Eagle"
    assert asset["model"] == "Eagle S3L"
    assert asset["name"] == "Eagle Automatic Laser Cutting System Model: Eagle S3L"
    assert store["metrics_path"] == "/tmp/metrics.json"


def test_multi_agent_status_and_audit_endpoints_are_read_only(monkeypatch):
    store = _sample_store("pdf-status")
    run_id = store["graph_state"]["run_id"]
    store["graph_state"]["current_phase"] = "validation"
    store["graph_state"]["run_status"] = "awaiting_operator"
    store["graph_state"]["next_step"] = "triplet_review"
    store["graph_state"]["validation_summary"] = {
        "total_entities": 3,
        "accepted": 2,
        "needs_refinement": 1,
        "needs_human": 0,
        "flagged_entities": 1,
        "flagged_entity_ids": ["CA-001"],
        "advisory_only": True,
    }
    store["graph_state"]["phase_history"] = [
        {"phase": "scoping", "agent": "ScopingAgent", "timestamp": "2026-04-09T12:00:00Z", "decision": "selected 2 pages", "tokens_used": 10, "llm_calls": 1, "details": {}},
        {"phase": "validation", "agent": "ValidationAgent", "timestamp": "2026-04-09T12:01:00Z", "decision": "accepted=2 needs_refinement=1 needs_human=0", "tokens_used": 0, "llm_calls": 0, "details": {}},
    ]
    store["graph_state"]["coverage_map"] = {
        1: {
            "has_content": True,
            "extracted_entities": ["Robot does not start"],
            "gap_type": "partially_covered",
            "recommendation": "Review flagged entities.",
            "review_required": True,
        },
    }
    store["graph_state"]["grounding_results"] = [
        {
            "entity_id": "CA-001",
            "entity_type": "CorrectiveAction",
            "source_page": 1,
            "grounding_score": 0.42,
            "supporting_text": "",
            "issues": ["weak support"],
        },
    ]
    store["graph_state"]["conflicts"] = [
        {
            "entity_ids": ["CA-001", "CA-002"],
            "conflict_type": "duplicate_corrective_action",
            "resolution": "merge",
            "resolved_entity": {"action_id": "CA-001"},
        },
    ]
    store["graph_state"]["refinement_attempts"] = {"CA-001": 1}
    store["graph_state"]["refinement_log"] = [
        {"entity_id": "CA-001", "attempt": 1, "result": "updated", "reasoning": "Refined deterministically."},
    ]
    store["graph_state"]["supervisor_log"] = [
        {
            "timestamp": "2026-04-09T12:01:05Z",
            "run_id": run_id,
            "phase_from": "validation",
            "phase_to": "triplet_review",
            "decision_type": "deterministic",
            "condition_met": "phase2_validation_is_advisory_only",
            "entities_affected": ["CA-001"],
            "reasoning": "Validation remains advisory.",
            "state_snapshot_hash": "abc123",
            "next_agent": "triplet_review",
            "token_budget_used_this_phase": 0,
            "validation_summary": store["graph_state"]["validation_summary"],
        },
    ]
    pdf_store["pdf-status"] = store

    status_response = client.get("/multi-agent/status", params={"run_id": run_id})
    audit_response = client.get(f"/multi-agent/audit/{run_id}")

    assert status_response.status_code == 200
    assert status_response.json()["run_id"] == run_id
    assert status_response.json()["next_step"] == "triplet_review"
    assert status_response.json()["validation_summary"]["flagged_entities"] == 1
    assert status_response.json()["coverage_summary"]["gap_counts"]["partially_covered"] == 1
    assert status_response.json()["grounding_summary"]["weak_grounding_entities"] == 1
    assert status_response.json()["conflict_summary"]["resolved_conflicts"] == 1
    assert status_response.json()["refinement_summary"]["updated_entities"] == 1

    assert audit_response.status_code == 200
    assert audit_response.json()["run_id"] == run_id
    assert audit_response.json()["supervisor_log"][0]["condition_met"] == "phase2_validation_is_advisory_only"
    assert audit_response.json()["phase_history"][1]["agent"] == "ValidationAgent"
    assert audit_response.json()["grounding_results"][0]["entity_id"] == "CA-001"
    assert audit_response.json()["conflicts"][0]["resolution"] == "merge"
    assert audit_response.json()["refinement_log"][0]["result"] == "updated"
