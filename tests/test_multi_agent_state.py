import asyncio

from backend.agents.conflict_resolution_agent import run_conflict_resolution_agent
from backend.agents.coverage_agent import run_coverage_agent
from backend.agents.extraction_agent import run_extraction_agent
from backend.agents.grounding_agent import run_grounding_agent
from backend.agents.ontology_draft_agent import run_ontology_draft_agent
from backend.agents.refiner_agent import run_refiner_agent
from backend.agents.scoping_agent import run_scoping_agent
from backend.agents.validation_agent import run_validation_agent
from backend.graph.supervisor import record_grounding_route, record_validation_route
from backend.graph.store import seed_graph_state
from backend.models import (
    CorrectiveAction,
    CutPlan,
    CutPlanRequest,
    ExtractRequest,
    ExtractionResult,
    FailureMode,
    OntologyDraftRequest,
    OntologyInstance,
    OntologyPipelineResponse,
    PageRange,
    PipelineIssue,
    ProductInfo,
    SectionInfo,
    Severity,
    SuggestedRelation,
    Symptom,
    Triplet,
)
from backend.services.run_metrics import ensure_run_metrics, record_stage_metrics


def _make_store() -> dict:
    store = {
        "pdf_id": "pdf-123",
        "filename": "manual.pdf",
        "pages": [
            {"page_number": 1, "text": "Power board error and recovery steps."},
            {"page_number": 2, "text": "Replace the board and reboot the robot."},
        ],
        "page_count": 2,
        "source_type": "",
        "source_title": "",
        "selected_models": {
            "scoping": None,
            "ontology_draft": None,
            "extraction": None,
        },
    }
    ensure_run_metrics(store)
    seed_graph_state(store, "pdf-123")
    return store


def _make_triplet() -> Triplet:
    return Triplet(
        symptom=Symptom(
            symptom_id="SYM-001",
            name="Robot does not start",
            description="Startup failure",
            severity=Severity.HIGH,
        ),
        failure_modes=[
            FailureMode(
                failure_mode_id="FM-001",
                name="Power board fault",
                description="The board is damaged.",
                material_context="Power board",
                linked_symptom_id="SYM-001",
            ),
        ],
        corrective_actions=[
            CorrectiveAction(
                action_id="CA-001",
                name="Replace power board",
                description="Install a replacement board.",
                instruction_text="Replace the power board and reboot the robot.",
                source_type="Service manual",
                source_title="Mock Robot",
                source_page=2,
                linked_failure_mode_id="FM-001",
            ),
        ],
    )


def _make_ontology_response() -> OntologyPipelineResponse:
    return OntologyPipelineResponse(
        status="needs_human",
        ontology=OntologyInstance(
            ontology_name="DiagnosticOntology",
            version="1.0",
            language="en",
            source_type="Service manual",
            source_title="Mock Robot",
            nodes={
                "Asset": [
                    {
                        "asset_id": "ASSET-001",
                        "name": "Mock Robot",
                        "description": "Robot controller",
                        "brand": "",
                        "model": "M-100",
                        "asset_type": "robot",
                    },
                ],
                "Component": [],
                "Symptom": [],
                "FailureMode": [],
                "CorrectiveAction": [],
                "ErrorCode": [],
            },
            relations=[],
        ),
        semantic_issues=[],
        schema_issues=[
            PipelineIssue(
                severity="warning",
                code="empty_draft_content",
                message="Missing diagnostic content",
                target_type="ontology",
            ),
        ],
        human_required_fields=[],
        is_schema_compliant=False,
        is_ready_for_human_review=False,
        retry_count=0,
        graph_issues=[],
        suggested_relations=[
            SuggestedRelation(
                relation_name="HAS_COMPONENT",
                from_type="Asset",
                from_id="ASSET-001",
                from_label="Mock Robot",
                to_type="Component",
                to_id="CMP-001",
                to_label="Power board",
                confidence=0.91,
                rationale="Mentioned in troubleshooting notes.",
            ),
        ],
    )


def test_seed_graph_state_initializes_run_metadata():
    store = _make_store()

    graph_state = store["graph_state"]

    assert graph_state["pdf_id"] == "pdf-123"
    assert graph_state["run_id"].startswith("run_")
    assert graph_state["current_phase"] == "loaded"
    assert graph_state["filename"] == "manual.pdf"
    assert graph_state["config_snapshot"]["pipeline"]["mode"] in {"classic", "multi_agent"}
    assert graph_state["selected_models"] == {
        "scoping": None,
        "ontology_draft": None,
        "extraction": None,
    }


def test_scoping_agent_updates_graph_state(monkeypatch):
    store = _make_store()

    def fake_workflow(target_store, req):
        target_store["source_type"] = "Service manual"
        target_store["source_title"] = "Mock Robot"
        record_stage_metrics(
            target_store,
            "scoping",
            {
                "stage": "scoping",
                "duration_seconds": 1.2,
                "llm_calls": 2,
                "prompt_tokens": 100,
                "cached_prompt_tokens": 10,
                "non_cached_prompt_tokens": 90,
                "completion_tokens": 25,
                "total_tokens": 125,
                "estimated_cost_usd": 0.001,
                "models": ["gpt-5.4-nano"],
                "operations": ["scoping"],
                "by_model": {
                    "gpt-5.4-nano": {
                        "label": "GPT-5.4 Nano",
                        "llm_calls": 2,
                        "prompt_tokens": 100,
                        "cached_prompt_tokens": 10,
                        "non_cached_prompt_tokens": 90,
                        "completion_tokens": 25,
                        "total_tokens": 125,
                        "estimated_cost_usd": 0.001,
                    },
                },
                "details": {
                    "total_pages": 2,
                    "selected_pages": 2,
                    "selected_sections": 1,
                    "skipped": False,
                    "page_offset": 0,
                },
            },
        )
        return CutPlan(
            pdf_id=req.pdf_id,
            total_pages=2,
            sections=[
                SectionInfo(
                    name="Troubleshooting",
                    page_range=PageRange(start=1, end=2),
                    source="rule",
                ),
            ],
            pages_to_keep=[1, 2],
            page_offset=0,
            skipped=False,
            product_info=ProductInfo(
                product_name="Mock Robot",
                document_type="Service manual",
                language="en",
                page_count=2,
            ),
        )

    monkeypatch.setattr("backend.agents.scoping_agent.create_cut_plan_workflow", fake_workflow)

    result = run_scoping_agent(store, CutPlanRequest(pdf_id="pdf-123", model_name="gpt-5.4-nano"))

    graph_state = store["graph_state"]
    assert result.pages_to_keep == [1, 2]
    assert graph_state["current_phase"] == "scoping"
    assert graph_state["selected_pages"] == [1, 2]
    assert graph_state["source_title"] == "Mock Robot"
    assert graph_state["selected_models"]["scoping"] == "gpt-5.4-nano"
    assert graph_state["token_ledger"]["scoping_agent"]["total_tokens"] == 125
    assert graph_state["phase_history"][-1]["agent"] == "ScopingAgent"


def test_ontology_draft_agent_updates_graph_state(monkeypatch):
    store = _make_store()

    async def fake_workflow(target_store, req):
        result = _make_ontology_response()
        target_store["ontology_pipeline"] = result.model_dump()
        record_stage_metrics(
            target_store,
            "ontology",
            {
                "stage": "ontology",
                "duration_seconds": 2.5,
                "llm_calls": 1,
                "prompt_tokens": 220,
                "cached_prompt_tokens": 20,
                "non_cached_prompt_tokens": 200,
                "completion_tokens": 90,
                "total_tokens": 310,
                "estimated_cost_usd": 0.004,
                "models": ["gpt-5.4"],
                "operations": ["ontology_draft"],
                "by_model": {
                    "gpt-5.4": {
                        "label": "GPT-5.4",
                        "llm_calls": 1,
                        "prompt_tokens": 220,
                        "cached_prompt_tokens": 20,
                        "non_cached_prompt_tokens": 200,
                        "completion_tokens": 90,
                        "total_tokens": 310,
                        "estimated_cost_usd": 0.004,
                    },
                },
                "details": {
                    "selected_pages": 2,
                    "selected_sections": 1,
                    "chunk_count": 1,
                    "retry_count": 0,
                    "status": result.status,
                    "schema_issue_count": len(result.schema_issues),
                    "semantic_issue_count": len(result.semantic_issues),
                    "graph_issue_count": len(result.graph_issues),
                    "suggested_relation_count": len(result.suggested_relations),
                },
            },
        )
        return result

    monkeypatch.setattr("backend.agents.ontology_draft_agent.draft_ontology_workflow", fake_workflow)

    result = asyncio.run(run_ontology_draft_agent(
        store,
        OntologyDraftRequest(
            pdf_id="pdf-123",
            source_type="Service manual",
            source_title="Mock Robot",
            model_name="gpt-5.4",
        ),
    ))

    graph_state = store["graph_state"]
    assert result.status == "needs_human"
    assert graph_state["current_phase"] == "ontology_draft"
    assert graph_state["selected_models"]["ontology_draft"] == "gpt-5.4"
    assert graph_state["ontology_pipeline"]["status"] == "needs_human"
    assert graph_state["suggested_relations"][0]["relation_name"] == "HAS_COMPONENT"
    assert graph_state["token_ledger"]["ontology_draft_agent"]["total_tokens"] == 310


def test_extraction_agent_updates_graph_state(monkeypatch):
    store = _make_store()
    store["cut_plan"] = {
        "pages_to_keep": [1, 2],
        "page_offset": 0,
        "sections": [{"name": "Troubleshooting", "start": 1, "end": 2, "source": "rule"}],
    }

    def fake_workflow(target_store, req):
        result = ExtractionResult(
            triplets=[_make_triplet()],
            raw_symptom_table="",
            raw_failure_mode_table="",
            raw_corrective_action_table="",
        )
        record_stage_metrics(
            target_store,
            "extraction",
            {
                "stage": "extraction",
                "duration_seconds": 1.7,
                "llm_calls": 1,
                "prompt_tokens": 180,
                "cached_prompt_tokens": 0,
                "non_cached_prompt_tokens": 180,
                "completion_tokens": 60,
                "total_tokens": 240,
                "estimated_cost_usd": 0.003,
                "models": ["gpt-5.4"],
                "operations": ["extraction"],
                "by_model": {
                    "gpt-5.4": {
                        "label": "GPT-5.4",
                        "llm_calls": 1,
                        "prompt_tokens": 180,
                        "cached_prompt_tokens": 0,
                        "non_cached_prompt_tokens": 180,
                        "completion_tokens": 60,
                        "total_tokens": 240,
                        "estimated_cost_usd": 0.003,
                    },
                },
                "details": {
                    "selected_pages": 2,
                    "triplet_count": 1,
                    "source_type": req.source_type,
                    "source_title": req.source_title,
                    "chunk_count": 1,
                },
            },
        )
        return result, [{"chunk_index": 1, "page_numbers": [1, 2], "page_start": 1, "page_end": 2, "page_count": 2}]

    monkeypatch.setattr("backend.agents.extraction_agent.extract_triplets_workflow", fake_workflow)

    result = run_extraction_agent(
        store,
        ExtractRequest(
            pdf_id="pdf-123",
            source_type="Service manual",
            source_title="Mock Robot",
            model_name="gpt-5.4",
            pages_to_keep=[1, 2],
        ),
    )

    graph_state = store["graph_state"]
    assert len(result.triplets) == 1
    assert graph_state["current_phase"] == "extraction"
    assert graph_state["selected_models"]["extraction"] == "gpt-5.4"
    assert len(graph_state["cleaned_triplets"]) == 1
    assert graph_state["extraction_chunks"][0]["page_numbers"] == [1, 2]
    assert graph_state["token_ledger"]["extraction_agent"]["total_tokens"] == 240


def test_validation_agent_updates_graph_state_with_advisory_verdicts():
    store = _make_store()
    store["pages"] = [
        {"page_number": 1, "text": "Robot does not start. Startup failure caused by power board fault."},
        {"page_number": 2, "text": "Replace power board. Install a replacement board. Replace the power board and reboot the robot."},
    ]
    graph_state = store["graph_state"]
    graph_state["selected_pages"] = [1, 2]
    graph_state["cleaned_triplets"] = [_make_triplet().model_dump()]
    graph_state["ontology_draft"] = {
        "nodes": {
            "Asset": [],
            "Component": [],
            "Symptom": [],
            "FailureMode": [],
            "CorrectiveAction": [],
            "ErrorCode": [],
        },
    }

    verdicts, summary = run_validation_agent(store)

    updated_state = store["graph_state"]
    assert len(verdicts) == 3
    assert summary["total_entities"] == 3
    assert summary["accepted"] >= 1
    assert summary["flagged_entities"] >= 0
    assert updated_state["current_phase"] == "validation"
    assert updated_state["validation_summary"]["advisory_only"] is True
    assert updated_state["token_ledger"]["validation_agent"]["total_tokens"] == 0


def test_supervisor_records_validation_route_without_bypassing_triplet_review():
    store = _make_store()
    graph_state = store["graph_state"]
    graph_state["current_phase"] = "validation"
    graph_state["validation_summary"] = {
        "total_entities": 3,
        "accepted": 2,
        "needs_refinement": 1,
        "needs_human": 0,
        "flagged_entities": 1,
        "flagged_entity_ids": ["CA-001"],
        "advisory_only": True,
    }

    entry = record_validation_route(store)

    updated_state = store["graph_state"]
    assert entry["phase_to"] == "triplet_review"
    assert updated_state["next_step"] == "triplet_review"
    assert updated_state["run_status"] == "awaiting_operator"
    assert updated_state["supervisor_log"][-1]["condition_met"] == "phase2_validation_is_advisory_only"


def test_coverage_agent_updates_graph_state_with_page_gap_analysis():
    store = _make_store()
    store["pages"] = [
        {"page_number": 1, "text": "Troubleshooting: robot does not start due to a power board fault."},
        {"page_number": 2, "text": "Replace the power board and reboot the robot."},
        {"page_number": 3, "text": "Safety notes and general warranty information."},
    ]
    store["page_count"] = 3
    graph_state = store["graph_state"]
    graph_state["selected_pages"] = [1, 2, 3]
    graph_state["cleaned_triplets"] = [_make_triplet().model_dump()]
    graph_state["entity_verdicts"] = [
        {
            "entity_id": "CA-001",
            "entity_type": "CorrectiveAction",
            "verdict": "accepted",
            "source_page": 2,
            "source_pages": [2],
            "reasons": [],
            "grounding_score": 1.0,
        },
    ]

    coverage_map = run_coverage_agent(store)

    updated_state = store["graph_state"]
    assert coverage_map[1]["gap_type"] == "missing_extraction"
    assert coverage_map[2]["gap_type"] == "fully_covered"
    assert coverage_map[3]["gap_type"] == "no_diagnostic_content"
    assert updated_state["current_phase"] == "coverage"
    assert updated_state["coverage_map"][1]["recommendation"].startswith("Consider targeted")


def test_grounding_agent_updates_verdicts_with_deeper_support_checks():
    store = _make_store()
    store["pages"] = [
        {"page_number": 1, "text": "Robot does not start. Startup failure caused by power board fault."},
        {"page_number": 2, "text": "Replace the power board. Install a replacement board. Reboot the robot."},
    ]
    graph_state = store["graph_state"]
    graph_state["selected_pages"] = [1, 2]
    triplet = _make_triplet().model_dump()
    triplet["corrective_actions"][0]["name"] = "Calibrate sensor harness"
    triplet["corrective_actions"][0]["description"] = "Tune the cooling manifold."
    triplet["corrective_actions"][0]["instruction_text"] = "Calibrate the cooling manifold and validate the harness."
    graph_state["cleaned_triplets"] = [triplet]
    graph_state["ontology_draft"] = {"nodes": {}}

    run_validation_agent(store)
    grounding_results, updated_verdicts = run_grounding_agent(store)

    action_verdict = next(item for item in updated_verdicts if item["entity_id"] == "CA-001")
    updated_state = store["graph_state"]
    assert len(grounding_results) == 3
    assert action_verdict["verdict"] == "needs_human"
    assert updated_state["current_phase"] == "grounding"
    assert updated_state["validation_summary"]["needs_human"] >= 1
    assert updated_state["grounding_results"][2]["entity_type"] == "CorrectiveAction"


def test_conflict_resolution_agent_records_duplicate_triplets():
    store = _make_store()
    graph_state = store["graph_state"]
    graph_state["selected_pages"] = [1, 2]
    graph_state["cleaned_triplets"] = [_make_triplet().model_dump(), _make_triplet().model_dump()]
    graph_state["cleaned_triplets"][1]["symptom"]["symptom_id"] = "SYM-002"
    graph_state["cleaned_triplets"][1]["failure_modes"][0]["failure_mode_id"] = "FM-002"
    graph_state["cleaned_triplets"][1]["failure_modes"][0]["linked_symptom_id"] = "SYM-002"
    graph_state["cleaned_triplets"][1]["corrective_actions"][0]["action_id"] = "CA-002"
    graph_state["cleaned_triplets"][1]["corrective_actions"][0]["linked_failure_mode_id"] = "FM-002"

    conflicts = run_conflict_resolution_agent(store)

    updated_state = store["graph_state"]
    assert len(conflicts) >= 1
    assert conflicts[0]["conflict_type"] in {"duplicate_symptom", "duplicate_failure_mode", "overlapping_corrective_action"}
    assert conflicts[0]["resolution"] in {"merge", "prefer_higher_confidence"}
    assert len(updated_state["cleaned_triplets"]) == 2
    assert updated_state["current_phase"] == "conflict_resolution"


def test_refiner_agent_updates_targeted_entities_and_logs_attempts():
    store = _make_store()
    store["pages"] = [
        {"page_number": 1, "text": "Robot does not start. Startup failure caused by power board fault."},
        {"page_number": 2, "text": "Replace the power board and reboot the robot."},
    ]
    graph_state = store["graph_state"]
    graph_state["selected_pages"] = [1, 2]
    triplet = _make_triplet().model_dump()
    triplet["corrective_actions"][0]["instruction_text"] = "1. Replace the power board.\n2. Confirm the fault is resolved."
    triplet["corrective_actions"][0]["description"] = "Board replacement procedure."
    graph_state["cleaned_triplets"] = [triplet]
    graph_state["entity_verdicts"] = [
        {
            "entity_id": "CA-001",
            "entity_type": "CorrectiveAction",
            "entity_name": "Replace power board",
            "verdict": "needs_refinement",
            "reasons": ["procedural steps are weakly grounded"],
            "source_page": 2,
            "source_pages": [2],
            "grounding_score": 0.62,
            "agent": "ValidationAgent",
            "advisory_only": True,
        },
    ]

    refinement_result = run_refiner_agent(store)

    updated_state = store["graph_state"]
    updated_action = updated_state["cleaned_triplets"][0]["corrective_actions"][0]
    assert refinement_result["changed_entity_ids"] == ["CA-001"]
    assert "Replace the power board" in updated_action["instruction_text"]
    assert updated_state["refinement_attempts"]["CA-001"] == 1
    assert updated_state["refinement_log"][-1]["result"] == "updated"


def test_supervisor_routes_grounding_to_triplet_review_when_no_other_agents_are_enabled():
    store = _make_store()
    graph_state = store["graph_state"]
    graph_state["current_phase"] = "grounding"
    graph_state["validation_summary"] = {
        "total_entities": 3,
        "accepted": 2,
        "needs_refinement": 0,
        "needs_human": 1,
        "flagged_entities": 1,
        "flagged_entity_ids": ["CA-001"],
        "advisory_only": True,
    }

    entry = record_grounding_route(store, conflict_enabled=False, refiner_enabled=False)

    updated_state = store["graph_state"]
    assert entry["phase_to"] == "triplet_review"
    assert updated_state["next_step"] == "triplet_review"
    assert updated_state["run_status"] == "awaiting_operator"
