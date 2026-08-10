"""Ontology-draft tools: draft, required fields, and candidate relations.

Split out of the former tools.py god-file (stabilization P6); pure move.
"""

from __future__ import annotations

from backend.services.conversation.tools.common import (
    _build_ontology_review_payload,
)


async def _draft_ontology(args, store, on_event):
    from backend.app_config import get_agent_config
    from backend.graph.store import update_ontology_state
    from backend.models import OntologyDraftRequest
    from backend.services.ontology_workflow import draft_ontology_workflow

    req = OntologyDraftRequest(
        pdf_id=store["pdf_id"],
        source_type=store.get("source_type", ""),
        source_title=store.get("source_title", ""),
        model_name=(store.get("selected_models") or {}).get("ontology_draft") or None,
        reasoning_effort=get_agent_config("ontology_draft").get("reasoning_effort"),
        pages_to_keep=(store.get("cut_plan") or {}).get("pages_to_keep"),
        target_language=store.get("target_language", "en"),
    )
    result = await draft_ontology_workflow(store, req, on_event)
    update_ontology_state(store, result, model_name=str(req.model_name or ""))
    store["ontology_pipeline"] = result.model_dump()

    # Proactive critic: emit critique events for draft issues
    if on_event:
        try:
            from backend.services.conversation.critic import critique_ontology_draft
            for critique in critique_ontology_draft(store):
                on_event(critique)
        except Exception:
            pass

    payload = _build_ontology_review_payload(result, store)

    from backend.graph.store import set_run_progress
    # The draft is done; nothing runs until the operator starts the extraction.
    set_run_progress(store, run_status="awaiting_operator", next_step="run_extraction")

    return {
        "status": result.status,
        **payload,
        "widget": "ontology_review",
    }

async def _fill_required_field(args, store, on_event):
    from backend.models import HumanBindingAnswer
    from backend.services.ontology_pipeline import apply_human_binding

    field_key = args["field_key"]
    value = args["value"]

    pipeline_state = store.get("ontology_pipeline")
    if not pipeline_state:
        return {"status": "error", "message": "No ontology pipeline state."}

    from backend.models import OntologyPipelineResponse
    existing = OntologyPipelineResponse.model_validate(pipeline_state)
    answers = [HumanBindingAnswer(field_key=field_key, value=value)]
    result = apply_human_binding(existing.ontology, answers)
    if existing.semantic_issues:
        result.semantic_issues = existing.semantic_issues
    store["ontology_pipeline"] = result.model_dump()

    from backend.graph.store import sync_ontology_pipeline_state
    sync_ontology_pipeline_state(store)
    payload = _build_ontology_review_payload(result, store)
    return {
        "status": "ok",
        "field_key": field_key,
        "remaining_fields": len(result.human_required_fields),
        "message": f"Field '{field_key}' set to '{value}'.",
        **payload,
        "widget": "ontology_review",
    }


async def _apply_suggested_relation(args, store, on_event):
    from backend.models import OntologyPipelineResponse
    from backend.services.pipeline_actions import apply_ontology_suggestions

    indices = args.get("indices") or []
    pipeline_state = store.get("ontology_pipeline")
    if not pipeline_state:
        return {"status": "error", "message": "No ontology pipeline state."}

    existing = OntologyPipelineResponse.model_validate(pipeline_state)
    suggested = existing.suggested_relations or []
    to_apply = []
    for idx in indices:
        if 0 <= idx < len(suggested):
            to_apply.append(suggested[idx])

    if not to_apply:
        return {"status": "ok", "message": "No valid indices provided."}

    result = apply_ontology_suggestions(store, to_apply)
    payload = _build_ontology_review_payload(result, store)
    return {
        "status": "ok",
        "applied_count": len(to_apply),
        "remaining_suggestions": len(result.suggested_relations),
        "message": (
            f"Applied {len(to_apply)} relation suggestion(s). "
            f"{len(result.graph_issues)} graph issue(s) and {len(result.suggested_relations)} suggestion(s) remain."
        ),
        **payload,
        "widget": "ontology_review",
    }
