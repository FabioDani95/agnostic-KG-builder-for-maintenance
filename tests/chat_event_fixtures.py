from __future__ import annotations

from typing import Any

from backend.services.conversation import events as evt_bus

KNOWN_EVENT_TYPES = {
    evt_bus.EVT_PROGRESS,
    evt_bus.EVT_CHAT_DELTA,
    evt_bus.EVT_WIDGET,
    evt_bus.EVT_CRITIQUE,
    evt_bus.EVT_NEEDS_INPUT,
    evt_bus.EVT_DONE,
    evt_bus.EVT_ERROR,
    evt_bus.EVT_THINKING,
}

KNOWN_WIDGET_TYPES = {
    "sections",
    "ontology_review",
    "triplet",
    "triplet_review_start",
    "required_fields",
    "node_draft",
    "extraction_graph",
    "modify_workspace_sync",
    "export",
    "run_metrics",
}


def sample_chat_events() -> list[dict[str, Any]]:
    return [
        evt_bus.progress_event("scoping", "Running scoping..."),
        evt_bus.chat_delta_event("Section selection is ready."),
        evt_bus.widget_event("sections", sample_widget_payloads()["sections"]),
        evt_bus.critique_event(
            "Symptom has no linked failure mode.",
            entity_id="SYM-001",
            suggestion="Link it to a failure mode.",
        ),
        {
            "type": evt_bus.EVT_NEEDS_INPUT,
            "message": "Fill the required field.",
            "field_key": "Asset:ASSET-001:brand",
        },
        evt_bus.done_event(),
        evt_bus.error_event("The action is not available in this phase."),
        {"type": evt_bus.EVT_THINKING},
    ]


def sample_widget_payloads() -> dict[str, dict[str, Any]]:
    return {
        "sections": {
            "status": "ok",
            "sections": [{"name": "Troubleshooting", "start": 2, "end": 4, "source": "llm"}],
            "pages_to_keep": [2, 3, 4],
            "total_pages": 5,
        },
        "ontology_review": {
            "status": "ready",
            "node_count": 3,
            "node_type_counts": {"Asset": 1, "Symptom": 1, "FailureMode": 1},
            "selected_pages_count": 3,
            "selected_sections_count": 1,
            "graph_issues_count": 0,
            "human_fields_count": 0,
            "schema_issues_count": 0,
            "suggested_relations_count": 0,
            "human_required_fields": [],
            "review_queue": [],
        },
        "triplet": {
            "status": "ok",
            "index": 0,
            "total": 1,
            "triplet": sample_triplet(),
            "logic_assessment": {"status": "ok", "issues": []},
            "graph": sample_extraction_graph(),
        },
        "triplet_review_start": {
            "status": "ok",
            "total": 1,
            "message": "Triplet review started.",
        },
        "required_fields": {
            "status": "needs_input",
            "fields": [
                {
                    "field_key": "Asset:ASSET-001:brand",
                    "prompt": "What brand is the asset?",
                    "target_type": "Asset",
                    "target_id": "ASSET-001",
                    "property_name": "brand",
                }
            ],
        },
        "node_draft": {
            "status": "pending_confirmation",
            "node_type": "Symptom",
            "raw_text": "pump vibrates",
            "normalized_name": "Pump Vibration",
            "normalized_description": "The pump vibrates during operation.",
        },
        "extraction_graph": {
            "status": "ok",
            "graph": sample_extraction_graph(),
            "action": "validated",
            "index": 0,
        },
        "modify_workspace_sync": {
            "status": "ok",
            "editor_url": "/modify/pdf-characterization",
            "workspace": {"nodes": [], "edges": []},
        },
        "export": {
            "status": "done",
            "total": 1,
            "validated": 1,
            "exported": False,
        },
        "run_metrics": {
            "status": "ok",
            "metrics": {
                "totals": {"duration_seconds": 1.0, "llm_calls": 0, "total_tokens": 0},
                "review": {"validated_triplets": 1, "discarded_triplets": 0},
            },
        },
    }


def sample_triplet() -> dict[str, Any]:
    return {
        "symptom": {
            "symptom_id": "SYM-001",
            "name": "Low Flow",
            "description": "Pump flow is below target.",
            "severity": "Medium",
            "evidence_page": 3,
        },
        "failure_modes": [
            {
                "failure_mode_id": "FM-001",
                "name": "Clogged Filter",
                "description": "The inlet filter is clogged.",
                "material_context": "Hydraulic circuit",
                "linked_symptom_id": "SYM-001",
                "evidence_page": 3,
            }
        ],
        "corrective_actions": [
            {
                "action_id": "CA-001",
                "name": "Clean Filter",
                "description": "Clean or replace the inlet filter.",
                "instruction_text": "Stop the pump and clean the filter.",
                "source_type": "manual",
                "source_title": "Characterization Manual",
                "source_page": 4,
                "linked_failure_mode_id": "FM-001",
            }
        ],
    }


def sample_extraction_graph() -> dict[str, Any]:
    return {
        "nodes": [
            {"id": "SYM-001", "label": "Low Flow", "type": "Symptom"},
            {"id": "FM-001", "label": "Clogged Filter", "type": "FailureMode"},
            {"id": "CA-001", "label": "Clean Filter", "type": "CorrectiveAction"},
        ],
        "edges": [
            {"id": "SYM-001->FM-001", "from": "SYM-001", "to": "FM-001", "label": "MAY_INDICATE"},
            {"id": "FM-001->CA-001", "from": "FM-001", "to": "CA-001", "label": "HAS_REMEDY"},
        ],
        "triplet_count": 1,
        "focus_index": 0,
        "focus_node_ids": ["SYM-001", "FM-001", "CA-001"],
        "focus_edge_ids": ["SYM-001->FM-001", "FM-001->CA-001"],
    }
