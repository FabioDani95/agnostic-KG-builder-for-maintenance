"""Export and read-only graph inspection tools.

Split out of the former tools.py god-file (stabilization P6); pure move.
"""

from __future__ import annotations

import asyncio

from backend.graph.state import GraphPhase
from backend.services.conversation.tools.common import (
    _graph_type_counts,
    _resolve_exported_graph_path,
    _search_exported_nodes,
)


async def _export_ontology(args, store, on_event):
    import json
    import time

    from backend.services.conversation import events as evt_bus
    from backend.services.ontology_export_store import (
        persist_export_metrics,
        persist_exported_ontology,
        prepare_exported_ontology,
    )
    from backend.services.pipeline_actions import get_current_ontology
    from backend.services.run_metrics import aggregate_usage, build_metrics_payload, record_stage_metrics
    from backend.services.style_cleanup_service import cleanup_export_ontology

    t0 = time.perf_counter()
    result = get_current_ontology(store)
    if not result:
        return {"status": "error", "message": "No ontology available to export."}

    blocking = [
        i for i in (result.schema_issues or [])
        if getattr(i, "severity", "") in ("critical", "Critical")
    ]
    if blocking:
        return {
            "status": "refused",
            "reason": f"The ontology has {len(blocking)} critical schema issue(s). Resolve them before exporting.",
            "suggested_next": "Review schema issues listed in the ontology review widget.",
        }
    if result.human_required_fields:
        return {
            "status": "refused",
            "reason": f"{len(result.human_required_fields)} required field(s) are still empty.",
            "suggested_next": "Fill the required fields first.",
        }

    if on_event:
        on_event(evt_bus.progress_event("export", "Running style cleanup…"))

    ontology_dict = result.ontology.model_dump()
    try:
        cleaned, style_cleanup_usage, cleanup_report = await asyncio.to_thread(
            cleanup_export_ontology,
            ontology_dict,
            target_language=store.get("target_language", "en"),
        )
    except Exception:
        cleaned = ontology_dict
        style_cleanup_usage = {}
        cleanup_report = {}

    from backend.models import OntologyInstance
    cleaned_ontology = OntologyInstance.model_validate(cleaned)
    ontology_payload = prepare_exported_ontology(cleaned_ontology.model_dump())
    export_info = persist_exported_ontology(
        ontology_payload,
        store.get("pdf_id"),
        manual_filename=store.get("filename"),
    )
    ontology_path = export_info["target_path"]
    store["ontology_path"] = ontology_path

    conversation = store.get("conversation") or {}
    from pathlib import Path
    conversation_path = str(Path(ontology_path).with_name("conversation.json"))
    with open(conversation_path, "w", encoding="utf-8") as f:
        json.dump(conversation, f, indent=2, ensure_ascii=False, default=str)

    export_usage = aggregate_usage([style_cleanup_usage] if style_cleanup_usage else [])
    record_stage_metrics(
        store,
        "export",
        {
            "stage": "export",
            "duration_seconds": round(max(0.0, time.perf_counter() - t0), 3),
            **export_usage,
            "details": {
                "validated_triplets": len(store.get("validated_triplets") or []),
                "filename": export_info.get("download_filename") or export_info["filename"],
                "style_cleanup_fields_seen": int(cleanup_report.get("llm_fields_seen", 0) or 0),
                "style_cleanup_fields_changed": int(cleanup_report.get("llm_fields_changed", 0) or 0),
                "style_cleanup_fields_rejected": int(cleanup_report.get("llm_fields_rejected", 0) or 0),
                "style_cleanup_deterministic_fields_changed": int(
                    cleanup_report.get("deterministic_fields_changed", 0) or 0
                ),
                "style_cleanup_model": cleanup_report.get("model"),
            },
        },
    )
    metrics_payload = build_metrics_payload(store)
    correct_coverage = (ontology_payload.get("metadata") or {}).get("graph_coverage")
    if correct_coverage:
        metrics_payload["graph_coverage"] = correct_coverage
    metrics_info = persist_export_metrics(
        metrics_payload,
        ontology_payload,
        export_info,
        manual_filename=store.get("filename"),
    )
    store["metrics_path"] = metrics_info["target_path"]
    try:
        from backend.runstore import copy_export_artifacts
        copy_export_artifacts(store)
    except Exception:
        pass

    # Update phase to COMPLETED
    from backend.graph.store import _record_phase
    _record_phase(
        store, phase=GraphPhase.COMPLETED,
        agent="ExportAgent", decision="exported",
    )

    gs = store.get("graph_state") or {}
    triplets = gs.get("cleaned_triplets") or []
    validated = store.get("validated_triplets") or []

    return {
        "status": "ok",
        "output_path": ontology_path,
        "download_filename": export_info.get("download_filename") or export_info["filename"],
        "triplets_total": len(triplets),
        "triplets_validated": len(validated),
        "cleanup_fields_changed": cleanup_report.get("deterministic_fields_changed", 0),
        "exported": True,
        "metrics": metrics_payload,
        "message": (
            f"Export complete — {len(validated)} validated triplet(s). "
            f"Ontology saved to `{ontology_path}`. "
            "The full extraction KPIs are shown below. "
            "You can now inspect the published graph in read-only mode."
        ),
        "widget": "export",
    }


async def _inspect_exported_graph(args, store, on_event):
    from backend.services.graph_view_service import (
        load_published_graph,
        published_graph_status,
        published_node_detail,
    )

    path = _resolve_exported_graph_path(store)
    ontology = load_published_graph(path)
    status = published_graph_status(path, ontology)
    node_type_counts, edge_type_counts = _graph_type_counts(ontology)
    total_nodes = sum(node_type_counts.values())
    total_relationships = sum(edge_type_counts.values())

    node_id = str(args.get("node_id") or "").strip()
    query = str(args.get("query") or "").strip()
    limit = max(1, min(int(args.get("limit") or 8), 20))

    if node_id:
        try:
            node = published_node_detail(ontology, node_id)
        except KeyError:
            return {
                "status": "refused",
                "node_id": node_id,
                "message": f"I could not find node `{node_id}` in the exported graph.",
                "total_nodes": total_nodes,
                "total_relationships": total_relationships,
                "node_type_counts": node_type_counts,
                "relationship_type_counts": edge_type_counts,
                **status,
            }
        return {
            "status": "ok",
            "node": node,
            "total_nodes": total_nodes,
            "total_relationships": total_relationships,
            "node_type_counts": node_type_counts,
            "relationship_type_counts": edge_type_counts,
            **status,
            "message": (
                f"Found node `{node['id']}` ({node['type']}) with "
                f"{len(node['relationships_out'])} outgoing and {len(node['relationships_in'])} incoming relationship(s)."
            ),
        }

    matches = _search_exported_nodes(ontology, query, limit=limit) if query else []
    if query:
        summary = (
            f"Found {len(matches)} matching node(s) for '{query}'."
            if matches
            else f"No exported nodes matched '{query}'."
        )
    else:
        summary = f"The exported graph contains {total_nodes} node(s) and {total_relationships} relationship(s)."

    return {
        "status": "ok",
        "query": query or None,
        "matches": matches,
        "total_nodes": total_nodes,
        "total_relationships": total_relationships,
        "node_type_counts": node_type_counts,
        "relationship_type_counts": edge_type_counts,
        **status,
        "message": summary,
    }
