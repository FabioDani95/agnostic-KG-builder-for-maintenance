"""Ontology-draft tools: draft, required fields, relations, manual nodes.

Split out of the former tools.py god-file (stabilization P6); pure move.
"""

from __future__ import annotations

from backend.services.conversation.tools.common import (
    _build_ontology_review_payload,
)

async def _draft_ontology(args, store, on_event):
    from backend.models import OntologyDraftRequest
    from backend.services.ontology_workflow import draft_ontology_workflow
    from backend.graph.store import update_ontology_state

    req = OntologyDraftRequest(
        pdf_id=store["pdf_id"],
        source_type=store.get("source_type", ""),
        source_title=store.get("source_title", ""),
        model_name=(store.get("selected_models") or {}).get("ontology_draft") or None,
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


async def _add_node_manual(args, store, on_event):
    import json
    from backend.app_config import get_chat_config
    from httpx import Timeout
    from backend.services.llm_gateway import get_async_client

    node_type = args["node_type"]
    raw_text = args["raw_text"]
    cfg = get_chat_config()

    client = get_async_client(timeout=Timeout(20.0))
    prompt = (
        f"Normalize an ontology node for a maintenance knowledge graph.\n"
        f"Node type: {node_type}\n"
        f"User description: {raw_text}\n\n"
        f"Extract a clean node with:\n"
        f"- name: concise 3-6 word identifier (title case)\n"
        f"- description: one clear sentence\n\n"
        f"Respond with JSON only: {{\"name\": \"...\", \"description\": \"...\"}}"
    )
    try:
        response = await client.chat.completions.create(
            model=cfg.get("model", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            max_completion_tokens=200,
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        # Strip markdown code fences if present
        if content.strip().startswith("```"):
            content = content.strip().strip("`").lstrip("json").strip()
        normalized = json.loads(content)
    except Exception:
        normalized = {"name": raw_text[:60].strip(), "description": ""}

    return {
        "status": "pending_confirmation",
        "node_type": node_type,
        "raw_text": raw_text,
        "normalized_name": normalized.get("name") or raw_text[:60],
        "normalized_description": normalized.get("description", ""),
        "widget": "node_draft",
        "message": (
            f"I've normalized your description into a **{node_type}** node. "
            "Review the proposal below and confirm to add it to the ontology."
        ),
    }


async def _confirm_node_manual(args, store, on_event):
    import re
    node_type = args["node_type"]
    node = args.get("node") or {}
    name = str(node.get("name") or "").strip()
    description = str(node.get("description") or "").strip()

    if not name:
        return {"status": "error", "message": "Node name is required."}

    # Build a candidate dict with the correct id field
    _id_fields = {
        "Asset": "asset_id",
        "Component": "component_id",
        "Symptom": "symptom_id",
        "FailureMode": "failure_mode_id",
        "CorrectiveAction": "action_id",
        "ErrorCode": "error_code_id",
    }
    id_field = _id_fields.get(node_type, "id")
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:40]
    node_id = f"{node_type[:3].lower()}_{slug}"

    candidate = {id_field: node_id, "name": name, "description": description}

    # Insert/merge via upsert
    pipeline_state = store.get("ontology_pipeline") or {}
    ontology = pipeline_state.get("ontology") or {}
    nodes = ontology.setdefault("nodes", {})

    from backend.services.ontology_merge_service import _upsert_node
    resulting_id = _upsert_node(nodes, node_type, candidate)

    ontology["nodes"] = nodes
    pipeline_state["ontology"] = ontology
    store["ontology_pipeline"] = pipeline_state

    from backend.graph.store import sync_ontology_pipeline_state
    sync_ontology_pipeline_state(store)

    return {
        "status": "ok",
        "node_type": node_type,
        "node_id": resulting_id or node_id,
        "name": name,
        "message": f"**{node_type}** node '{name}' added to the ontology.",
    }
