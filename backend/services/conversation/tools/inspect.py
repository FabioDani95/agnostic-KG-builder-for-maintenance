"""Read-only inspection tools: progress, inventories, metrics, explanations.

Split out of the former tools.py god-file (stabilization P6); pure move.
"""

from __future__ import annotations

from typing import Any

from backend.graph.state import GraphPhase
from backend.services.conversation.tools.common import (
    _collect_extracted_nodes,
    _contains_triplet,
    _filter_inventory_items,
    _format_node_inventory_message,
    _node_type_counts,
    _triplet_summary,
)


async def _get_progress(args, store, on_event):
    from backend.graph.projections import build_status_payload
    payload = build_status_payload(store)
    gs = store.get("graph_state") or {}
    cut_plan = store.get("cut_plan") or {}
    triplets = gs.get("cleaned_triplets") or []
    validated = store.get("validated_triplets") or []
    selected_pages = cut_plan.get("pages_to_keep") or payload.get("selected_pages") or []
    return {
        "status": "ok",
        "phase": payload.get("current_phase", "loaded"),
        "run_status": payload.get("run_status", "loaded"),
        "progress_percent": payload.get("progress_percent", 0),
        "selected_pages": len(selected_pages),
        "total_pages": cut_plan.get("total_pages") or len(store.get("pages") or []),
        "section_count": len(cut_plan.get("sections") or []),
        "total_triplets": len(triplets),
        "validated_triplets": len(validated),
        "validation_summary": payload.get("validation_summary", {}),
    }


async def _list_extracted_nodes(args, store, on_event):
    node_type_filter = str(args.get("node_type") or "").strip().lower()
    query = str(args.get("query") or "").strip()
    limit = max(1, min(int(args.get("limit") or 40), 100))
    include_descriptions = bool(args.get("include_descriptions"))

    nodes = _collect_extracted_nodes(store)
    if node_type_filter:
        nodes = [
            node for node in nodes
            if str(node.get("type") or "").lower() == node_type_filter
        ]
    nodes = _filter_inventory_items(nodes, query=query)

    counts = _node_type_counts(nodes)
    selected = nodes[:limit]
    nodes_by_type: dict[str, list[dict[str, Any]]] = {}
    for node in selected:
        payload = {
            "id": node.get("id"),
            "name": node.get("name"),
            "type": node.get("type"),
            "source": node.get("source"),
        }
        if include_descriptions and node.get("description"):
            payload["description"] = str(node.get("description"))[:240]
        nodes_by_type.setdefault(str(node.get("type") or "Unknown"), []).append(payload)

    result = {
        "status": "ok",
        "query": query or None,
        "node_type": args.get("node_type") or None,
        "total_nodes": len(nodes),
        "returned_nodes": len(selected),
        "node_type_counts": counts,
        "nodes_by_type": nodes_by_type,
        "truncated": len(nodes) > len(selected),
    }
    result["message"] = _format_node_inventory_message(result)
    return result


async def _list_extracted_triplets(args, store, on_event):
    gs = store.get("graph_state") or {}
    triplets = list(gs.get("cleaned_triplets") or [])
    validated = list(store.get("validated_triplets") or [])
    review_index = int(store.get("review_index") or 0)
    status_filter = str(args.get("status") or "all").strip().lower()
    query = str(args.get("query") or "").strip()
    limit = max(1, min(int(args.get("limit") or 10), 50))

    rows: list[dict[str, Any]] = []
    for idx, triplet in enumerate(triplets):
        if _contains_triplet(validated, triplet):
            status = "validated"
        elif idx < review_index:
            status = "skipped"
        else:
            status = "pending"
        if status_filter != "all" and status != status_filter:
            continue
        rows.append(_triplet_summary(triplet, idx, status))

    if query:
        rows = _filter_inventory_items(rows, query=query)

    selected = rows[:limit]
    if not triplets:
        message = "I do not have extracted triplets yet in the current workflow."
    else:
        message = (
            f"I found {len(rows)} matching triplet(s) out of {len(triplets)} extracted. "
            f"Review progress: {review_index}/{len(triplets)}."
        )

    return {
        "status": "ok",
        "query": query or None,
        "filter": status_filter,
        "total_triplets": len(triplets),
        "matching_triplets": len(rows),
        "returned_triplets": len(selected),
        "review_index": review_index,
        "validated_triplets": len(validated),
        "triplets": selected,
        "truncated": len(rows) > len(selected),
        "message": message,
    }


async def _get_run_metrics(args, store, on_event):
    from backend.services.run_metrics import build_metrics_payload

    metrics = build_metrics_payload(store)
    totals = metrics.get("totals") or {}
    review = metrics.get("review") or {}
    return {
        "status": "ok",
        "metrics": metrics,
        "message": (
            f"Full extraction KPIs ready: {int(totals.get('llm_calls', 0) or 0)} LLM call(s), "
            f"{int(totals.get('total_tokens', 0) or 0)} token(s), "
            f"${float(totals.get('estimated_cost_usd', 0) or 0):.4f} estimated cost, "
            f"and {int(review.get('validated_triplets', 0) or 0)} validated triplet(s)."
        ),
        "widget": "run_metrics",
    }


async def _explain_phase(args, store, on_event):
    from backend.graph.state import GraphPhase
    gs = store.get("graph_state") or {}
    phase = gs.get("current_phase", GraphPhase.LOADED.value)
    explanations = {
        GraphPhase.LOADED.value: "The manual is loaded. I'm ready to scope it — I'll identify the relevant diagnostic sections.",
        GraphPhase.SCOPING.value: "I'm scoping the document: finding the table of contents, identifying diagnostic sections, and selecting pages for extraction.",
        GraphPhase.ONTOLOGY_DRAFT.value: "I'm drafting the ontology: extracting Assets, Components, Symptoms, Failure Modes, and Corrective Actions from the scoped pages.",
        GraphPhase.EXTRACTION.value: "Ontology is drafted. Review the required fields and suggested relations before extraction.",
        GraphPhase.VALIDATION.value: "Triplet extraction is done. Review each Symptom → FailureMode → CorrectiveAction chain. Validate the ones you want to keep.",
        GraphPhase.EXPORT.value: "All triplets reviewed. Ready to export the ontology JSON.",
        GraphPhase.COMPLETED.value: (
            "Export complete. The ontology JSON is available in output/, "
            "and you can inspect the published graph in read-only mode."
        ),
    }
    return {"status": "ok", "phase": phase, "explanation": explanations.get(phase, f"Current phase: {phase}.")}


async def _explain_decision(args, store, on_event):
    import re

    topic = args.get("topic", "")
    gs = store.get("graph_state") or {}
    phase_history = gs.get("phase_history") or []
    supervisor_log = gs.get("supervisor_log") or []
    cut_plan = store.get("cut_plan") or {}
    sections = list(cut_plan.get("sections") or [])
    selected_pages = sorted(cut_plan.get("pages_to_keep") or gs.get("selected_pages") or [])
    selected_page_set = set(selected_pages)
    total_pages = cut_plan.get("total_pages") or len(store.get("pages") or [])

    context_parts = [f"Topic: {topic}"]
    context_parts.append(
        f"Current phase: {gs.get('current_phase', GraphPhase.LOADED.value)}. "
        f"Selected pages: {len(selected_pages)}/{total_pages}."
    )
    if sections:
        context_parts.append(
            "Sections selected: "
            + "; ".join(
                f"{s.get('name', 'Section')} (pages {s.get('start', '?')}-{s.get('end', '?')})"
                for s in sections
            )
        )

    page_numbers = sorted({int(match) for match in re.findall(r"\b\d+\b", topic)})
    for page_number in page_numbers[:6]:
        matching_sections = [
            s for s in sections
            if int(s.get("start") or 0) <= page_number <= int(s.get("end") or 0)
        ]
        if page_number in selected_page_set:
            if matching_sections:
                context_parts.append(
                    f"Page {page_number} is currently selected and falls in: "
                    + ", ".join(
                        f"{s.get('name', 'Section')} ({s.get('start')}-{s.get('end')})"
                        for s in matching_sections
                    )
                )
            else:
                context_parts.append(
                    f"Page {page_number} is currently selected but is not mapped to a named section in the cut plan."
                )
        else:
            context_parts.append(f"Page {page_number} is not currently selected.")

    topic_lower = topic.lower()
    matched_sections = [
        s for s in sections
        if str(s.get("name") or "").strip() and str(s.get("name")).lower() in topic_lower
    ]
    for section in matched_sections[:6]:
        context_parts.append(
            f"Section '{section.get('name', 'Section')}' is currently selected "
            f"from page {section.get('start', '?')} to {section.get('end', '?')}."
        )

    if phase_history:
        context_parts.append(f"Last phase decision: {phase_history[-1]}")
    if supervisor_log:
        context_parts.append(f"Supervisor log (last): {supervisor_log[-1]}")

    return {
        "status": "ok",
        "topic": topic,
        "context": "\n".join(context_parts),
    }


async def _explain_entity(args, store, on_event):
    entity_id = args.get("entity_id", "")
    gs = store.get("graph_state") or {}
    verdicts = gs.get("entity_verdicts") or []
    match = next((v for v in verdicts if str(v.get("entity_id")) == entity_id), None)
    pipeline = store.get("ontology_pipeline") or {}
    ontology = pipeline.get("ontology") or {}
    nodes = ontology.get("nodes") or {}

    entity_data = None
    for node_list in nodes.values():
        for node in (node_list or []):
            if isinstance(node, dict) and node.get("asset_id") == entity_id or \
               node.get("symptom_id") == entity_id or \
               node.get("failure_mode_id") == entity_id or \
               node.get("action_id") == entity_id or \
               node.get("component_id") == entity_id or \
               node.get("error_code_id") == entity_id:
                entity_data = node
                break

    return {
        "status": "ok",
        "entity_id": entity_id,
        "entity_data": entity_data,
        "verdict": match,
    }
