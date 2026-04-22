"""Chat tool catalog.

Defines OpenAI function-calling schemas and dispatch bindings.
Each tool corresponds to one deterministic pipeline action.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from backend.graph.state import GraphPhase

logger = logging.getLogger(__name__)

# --- OpenAI tool schemas ------------------------------------------------

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "propose_cut_plan",
            "description": "Run document scoping to propose a cut plan (page selection). Call this automatically at the start of a session or when the user asks to re-scope.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_cut_plan",
            "description": "Modify the proposed section selection before approval. Use when the user adds, removes, or renames a section.",
            "parameters": {
                "type": "object",
                "properties": {
                    "add_sections": {
                        "type": "array",
                        "description": "Sections to add.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "start_page": {"type": "integer"},
                                "end_page": {"type": "integer"},
                            },
                            "required": ["name", "start_page", "end_page"],
                        },
                    },
                    "remove_section_names": {
                        "type": "array",
                        "description": "Names of sections to remove.",
                        "items": {"type": "string"},
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "approve_cut_plan",
            "description": "Approve the current section selection and proceed to ontology drafting.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "draft_ontology",
            "description": "Run the ontology drafting pipeline on the approved pages.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fill_required_field",
            "description": "Fill a schema-required field that the automatic extraction left empty.",
            "parameters": {
                "type": "object",
                "properties": {
                    "field_key": {"type": "string", "description": "The field_key from the human_required_fields list."},
                    "value": {"type": "string", "description": "The value to set."},
                },
                "required": ["field_key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_suggested_relation",
            "description": "Accept one or more graph-reasoning suggested relations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "indices": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Indices into the suggested_relations list (0-based).",
                    },
                },
                "required": ["indices"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_extraction",
            "description": "Run triplet extraction on the approved pages.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "re_extract_pages",
            "description": "Re-run extraction on a specific page range, optionally with a hint about what the user expects to find.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_page": {"type": "integer"},
                    "end_page": {"type": "integer"},
                    "hint": {"type": "string", "description": "Optional hint about what to look for."},
                },
                "required": ["start_page", "end_page"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "approve_triplet",
            "description": "Validate (add to graph) the triplet at the given index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "0-based index in the triplet list."},
                },
                "required": ["index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "skip_triplet",
            "description": "Discard (skip) the triplet at the given index.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "0-based index in the triplet list."},
                },
                "required": ["index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "edit_triplet",
            "description": "Apply a patch to an existing triplet (e.g., rewrite a description).",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "description": "0-based index in the triplet list."},
                    "patch": {
                        "type": "object",
                        "description": "Partial update: keys are field paths, values are new values.",
                        "additionalProperties": True,
                    },
                },
                "required": ["index", "patch"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_node_manual",
            "description": "Add a new ontology node entered by the user. The chatbot will normalize the text and check for duplicates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_type": {
                        "type": "string",
                        "enum": ["Asset", "Component", "Symptom", "FailureMode", "CorrectiveAction", "ErrorCode"],
                    },
                    "raw_text": {"type": "string", "description": "Free-form text describing the node."},
                },
                "required": ["node_type", "raw_text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_next_triplet",
            "description": "Present the next triplet in the review queue. Call this after approving/skipping a triplet, or when the user asks to start triplet review.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "confirm_node_manual",
            "description": "Confirm and insert a manually-proposed ontology node after the user approves the normalized draft.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_type": {
                        "type": "string",
                        "enum": ["Asset", "Component", "Symptom", "FailureMode", "CorrectiveAction", "ErrorCode"],
                    },
                    "node": {
                        "type": "object",
                        "description": "The confirmed node data (name, description, …).",
                        "additionalProperties": True,
                    },
                },
                "required": ["node_type", "node"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "export_ontology",
            "description": "Export the final ontology JSON bundle to disk.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_progress",
            "description": "Return the current pipeline phase, counts, and a human-readable status summary.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_phase",
            "description": "Explain what happens in the current pipeline phase and what the user needs to do.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_decision",
            "description": "Explain a specific pipeline decision or why a page/section/entity was handled a certain way.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "What to explain (e.g. 'why was page 12 excluded', 'why is this a FailureMode')."},
                },
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "explain_entity",
            "description": "Explain an ontology node: why it was classified as it was, its evidence, validation verdict.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entity_id": {"type": "string"},
                },
                "required": ["entity_id"],
            },
        },
    },
]

TOOL_SCHEMA_MAP: dict[str, dict] = {t["function"]["name"]: t for t in TOOL_SCHEMAS}


def tools_for_phase(phase: str) -> list[dict[str, Any]]:
    """Return the subset of tool schemas relevant to the current phase."""
    from backend.services.conversation.gate import _PHASE_TOOLS, _ALWAYS_ALLOWED
    allowed = _PHASE_TOOLS.get(phase, set()) | _ALWAYS_ALLOWED
    return [t for t in TOOL_SCHEMAS if t["function"]["name"] in allowed]


def _build_ontology_review_payload(result, store: dict[str, Any]) -> dict[str, Any]:
    ontology_nodes = (getattr(result.ontology, "nodes", None) or {})
    node_type_counts = {
        node_type: len(items or [])
        for node_type, items in ontology_nodes.items()
        if len(items or []) > 0
    }

    graph_issue_types: dict[str, int] = {}
    top_graph_issues: list[dict[str, Any]] = []
    for issue in list(getattr(result, "graph_issues", []) or []):
        issue_type = str(getattr(issue, "issue_type", "") or "issue")
        graph_issue_types[issue_type] = graph_issue_types.get(issue_type, 0) + 1
        if len(top_graph_issues) < 3:
            top_graph_issues.append({
                "issue_type": issue_type,
                "description": str(getattr(issue, "description", "") or ""),
                "affected_nodes": list(getattr(issue, "affected_nodes", []) or []),
            })

    preview_relations: list[dict[str, Any]] = []
    for suggestion in list(getattr(result, "suggested_relations", []) or [])[:4]:
        preview_relations.append({
            "relation_name": suggestion.relation_name,
            "from_label": suggestion.from_label or suggestion.from_id,
            "to_label": suggestion.to_label or suggestion.to_id,
            "confidence": suggestion.confidence,
            "rationale": suggestion.rationale,
        })

    cut_plan = store.get("cut_plan") or {}
    graph_state = store.get("graph_state") or {}
    selected_pages = list(cut_plan.get("pages_to_keep") or graph_state.get("selected_pages") or [])
    selected_sections = list(cut_plan.get("sections") or [])
    confidence_report = getattr(result, "confidence_report", None)

    return {
        "status": getattr(result, "status", "ready"),
        "node_count": sum(node_type_counts.values()),
        "node_type_counts": node_type_counts,
        "selected_pages_count": len(selected_pages),
        "selected_sections_count": len(selected_sections),
        "graph_issues_count": len(getattr(result, "graph_issues", []) or []),
        "graph_issue_types": graph_issue_types,
        "top_graph_issues": top_graph_issues,
        "human_fields_count": len(getattr(result, "human_required_fields", []) or []),
        "schema_issues_count": len(getattr(result, "schema_issues", []) or []),
        "suggested_relations_count": len(getattr(result, "suggested_relations", []) or []),
        "preview_relations": preview_relations,
        "confidence_counts": getattr(confidence_report, "counts", {}) if confidence_report else {},
        "human_required_fields": [
            field.model_dump() for field in (getattr(result, "human_required_fields", []) or [])
        ],
    }


def _as_plain_dict(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if isinstance(value, dict):
        return value
    return {}


def _triplet_entity_id(entity: dict[str, Any], id_key: str) -> str:
    return str(entity.get(id_key) or "").strip()


def _upsert_graph_node(
    nodes_by_type: dict[str, list[dict[str, Any]]],
    seen: set[str],
    node_type: str,
    id_key: str,
    entity: dict[str, Any],
) -> str:
    entity_id = _triplet_entity_id(entity, id_key)
    if not entity_id:
        return ""
    if entity_id in seen:
        return entity_id
    nodes_by_type.setdefault(node_type, []).append({
        id_key: entity_id,
        "name": str(entity.get("name") or entity_id),
        "description": str(entity.get("description") or ""),
    })
    seen.add(entity_id)
    return entity_id


def _build_triplet_graph_payload(
    triplets: list[Any],
    *,
    focus_index: int | None = None,
) -> dict[str, Any]:
    """Build the same graph data shape used by modify.graph, with review focus metadata."""
    from modify.graph import build_graph

    nodes_by_type: dict[str, list[dict[str, Any]]] = {
        "Symptom": [],
        "FailureMode": [],
        "CorrectiveAction": [],
    }
    relations: list[dict[str, Any]] = []
    seen_nodes: set[str] = set()
    seen_edges: set[tuple[str, str, str]] = set()
    focus_node_ids: set[str] = set()

    for idx, raw_triplet in enumerate(triplets or []):
        triplet = _as_plain_dict(raw_triplet)
        symptom = _as_plain_dict(triplet.get("symptom"))
        symptom_id = _upsert_graph_node(nodes_by_type, seen_nodes, "Symptom", "symptom_id", symptom)
        if focus_index == idx and symptom_id:
            focus_node_ids.add(symptom_id)

        for raw_fm in triplet.get("failure_modes") or []:
            fm = _as_plain_dict(raw_fm)
            fm_id = _upsert_graph_node(nodes_by_type, seen_nodes, "FailureMode", "failure_mode_id", fm)
            if focus_index == idx and fm_id:
                focus_node_ids.add(fm_id)
            if symptom_id and fm_id:
                edge = ("MAY_INDICATE", symptom_id, fm_id)
                if edge not in seen_edges:
                    relations.append({
                        "name": edge[0],
                        "from_type": "Symptom",
                        "from_id": edge[1],
                        "to_type": "FailureMode",
                        "to_id": edge[2],
                    })
                    seen_edges.add(edge)

        for raw_ca in triplet.get("corrective_actions") or []:
            ca = _as_plain_dict(raw_ca)
            ca_id = _upsert_graph_node(nodes_by_type, seen_nodes, "CorrectiveAction", "action_id", ca)
            if focus_index == idx and ca_id:
                focus_node_ids.add(ca_id)
            linked_fm_id = str(ca.get("linked_failure_mode_id") or "").strip()
            if linked_fm_id and ca_id:
                edge = ("HAS_CORRECTIVE_ACTION", linked_fm_id, ca_id)
                if edge not in seen_edges:
                    relations.append({
                        "name": edge[0],
                        "from_type": "FailureMode",
                        "from_id": edge[1],
                        "to_type": "CorrectiveAction",
                        "to_id": edge[2],
                    })
                    seen_edges.add(edge)

    graph = build_graph({"nodes": nodes_by_type, "relations": relations})
    focus_edge_ids = [
        edge["id"]
        for edge in graph.get("edges", [])
        if edge.get("from") in focus_node_ids and edge.get("to") in focus_node_ids
    ]
    return {
        **graph,
        "triplet_count": len(triplets or []),
        "focus_index": focus_index,
        "focus_node_ids": sorted(focus_node_ids),
        "focus_edge_ids": focus_edge_ids,
    }


# --- Dispatch implementations -------------------------------------------

async def dispatch(
    tool_name: str,
    args: dict[str, Any],
    store: dict[str, Any],
    on_event=None,
) -> dict[str, Any]:
    """Execute a validated tool call and return a result dict."""
    try:
        fn = _DISPATCH_MAP.get(tool_name)
        if fn is None:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}
        return await fn(args, store, on_event)
    except Exception as exc:
        logger.exception("Tool '%s' raised an exception", tool_name)
        return {"status": "error", "message": str(exc)}


async def _propose_cut_plan(args, store, on_event):
    from backend.models import CutPlanRequest
    from backend.services.scoping_workflow import create_cut_plan_workflow

    page_offset = store.get("page_offset")
    if page_offset is None:
        page_offset = 0
    req = CutPlanRequest(
        pdf_id=store["pdf_id"],
        page_offset=page_offset,
        model_name=(store.get("selected_models") or {}).get("scoping") or None,
    )
    result = await asyncio.to_thread(create_cut_plan_workflow, store, req, on_event)
    # Persist cut plan in store
    from backend.graph.store import update_scoping_state
    update_scoping_state(store, result, model_name=str(req.model_name or ""))
    return {
        "status": "ok",
        "sections": [
            {
                "name": s.name,
                "start": s.page_range.start,
                "end": s.page_range.end,
            }
            for s in result.sections
        ],
        "pages_to_keep": result.pages_to_keep,
        "total_pages": result.total_pages,
        "skipped": result.skipped,
        "product_info": result.product_info.model_dump() if result.product_info else None,
        "widget": "sections",
    }


async def _edit_cut_plan(args, store, on_event):
    cut_plan = store.get("cut_plan") or {}
    sections = list(cut_plan.get("sections") or [])

    remove_names = {n.lower() for n in (args.get("remove_section_names") or [])}
    if remove_names:
        sections = [s for s in sections if s.get("name", "").lower() not in remove_names]

    for new_sec in (args.get("add_sections") or []):
        sections.append({
            "name": new_sec["name"],
            "start": new_sec["start_page"],
            "end": new_sec["end_page"],
            "source": "human",
        })

    cut_plan["sections"] = sections
    # Recompute pages_to_keep from sections
    pages_to_keep = set()
    for sec in sections:
        pages_to_keep.update(range(sec["start"], sec["end"] + 1))
    cut_plan["pages_to_keep"] = sorted(pages_to_keep)
    store["cut_plan"] = cut_plan

    return {
        "status": "ok",
        "sections": sections,
        "pages_to_keep": cut_plan["pages_to_keep"],
        "widget": "sections",
    }


async def _approve_cut_plan(args, store, on_event):
    from backend.models import CutPlanApproval
    from backend.services.scoping_workflow import approve_cut_plan_workflow
    from backend.graph.store import update_cut_plan_approval

    cut_plan = store.get("cut_plan") or {}
    pages_to_keep = cut_plan.get("pages_to_keep") or [p["page_number"] for p in store.get("pages", [])]
    page_offset = cut_plan.get("page_offset")
    if page_offset is None:
        page_offset = store.get("page_offset", 0)

    sections_raw = cut_plan.get("sections") or []
    from backend.models import CutPlanApprovalSection, PageRange
    sections = []
    for s in sections_raw:
        try:
            sections.append(CutPlanApprovalSection(
                name=s.get("name", "Section"),
                page_range=PageRange(start=s.get("start", 1), end=s.get("end", 1)),
                source=s.get("source", "human"),
            ))
        except Exception:
            pass

    req = CutPlanApproval(
        pdf_id=store["pdf_id"],
        pages_to_keep=pages_to_keep,
        page_offset=page_offset,
        sections=sections,
    )
    approve_cut_plan_workflow(store, req)
    update_cut_plan_approval(
        store,
        pages_to_keep=pages_to_keep,
        page_offset=page_offset,
        sections=sections_raw,
    )
    return {
        "status": "ok",
        "pages_approved": len(pages_to_keep),
        "message": f"Section selection approved — {len(pages_to_keep)} pages will be processed.",
    }


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


async def _run_extraction(args, store, on_event):
    from backend.models import ExtractRequest
    from backend.services.extraction_workflow import extract_triplets_workflow
    from backend.graph.store import update_extraction_state

    req = ExtractRequest(
        pdf_id=store["pdf_id"],
        source_type=store.get("source_type", ""),
        source_title=store.get("source_title", ""),
        model_name=(store.get("selected_models") or {}).get("extraction") or None,
        pages_to_keep=(store.get("cut_plan") or {}).get("pages_to_keep"),
        target_language=store.get("target_language", "en"),
    )
    result, chunk_metadata = await asyncio.to_thread(
        extract_triplets_workflow, store, req, on_event
    )
    pages_to_keep = req.pages_to_keep or [p["page_number"] for p in store.get("pages", [])]
    update_extraction_state(
        store,
        result,
        model_name=str(req.model_name or ""),
        chunk_metadata=chunk_metadata,
        pages_to_keep=pages_to_keep,
    )
    triplets = [triplet.model_dump() for triplet in result.triplets]
    return {
        "status": "ok",
        "triplet_count": len(result.triplets),
        "message": f"Extraction complete — {len(result.triplets)} triplet(s) ready for review.",
        "graph": _build_triplet_graph_payload(triplets),
        "widget": "extraction_graph",
    }


async def _re_extract_pages(args, store, on_event):
    from backend.models import ExtractRequest
    from backend.services.extraction_workflow import extract_triplets_workflow
    from backend.services.llm_service import _merge_extraction_results
    from backend.graph.state import GraphPhase

    start = args["start_page"]
    end = args["end_page"]
    hint = args.get("hint", "")

    pages = store.get("pages") or []
    target_pages = [p for p in pages if start <= p["page_number"] <= end]
    if not target_pages:
        return {"status": "error", "message": f"No pages found in range {start}–{end}."}

    # Temporarily override pages_to_keep for this sub-extraction
    fake_store = dict(store)
    fake_store["pages"] = target_pages
    fake_store["cut_plan"] = {**(store.get("cut_plan") or {}), "pages_to_keep": [p["page_number"] for p in target_pages]}

    req = ExtractRequest(
        pdf_id=store["pdf_id"],
        source_type=store.get("source_type", ""),
        source_title=store.get("source_title", ""),
        model_name=(store.get("selected_models") or {}).get("extraction") or None,
        target_language=store.get("target_language", "en"),
    )
    new_result, _ = await asyncio.to_thread(extract_triplets_workflow, fake_store, req, on_event)

    # Merge new triplets with existing ones
    gs = store.get("graph_state") or {}
    existing_triplets = gs.get("cleaned_triplets") or []

    # Filter out triplets from the re-extracted page range in the existing set
    from backend.models import Triplet
    kept = [
        t for t in existing_triplets
        if not (start <= int((t.get("symptom") or {}).get("evidence_page", 0) or 0) <= end)
    ]
    added = [t.model_dump() for t in new_result.triplets]
    merged_triplets = kept + added

    gs["cleaned_triplets"] = merged_triplets
    store["graph_state"] = gs

    return {
        "status": "ok",
        "new_triplets": len(added),
        "total_triplets": len(merged_triplets),
        "message": f"Re-extracted pages {start}–{end}: found {len(added)} triplet(s).",
    }


async def _approve_triplet(args, store, on_event):
    idx = args["index"]
    gs = store.get("graph_state") or {}
    triplets = gs.get("cleaned_triplets") or []
    triplet = triplets[idx]
    validated = store.setdefault("validated_triplets", [])
    if triplet not in validated:
        validated.append(triplet)
    store["review_index"] = idx + 1
    return {"status": "ok", "action": "validated", "index": idx}


async def _skip_triplet(args, store, on_event):
    idx = args["index"]
    store["review_index"] = idx + 1
    return {"status": "ok", "action": "skipped", "index": idx}


async def _edit_triplet(args, store, on_event):
    idx = args["index"]
    patch = args.get("patch") or {}
    gs = store.get("graph_state") or {}
    triplets = gs.get("cleaned_triplets") or []
    if not triplets or idx >= len(triplets):
        return {"status": "error", "message": f"No triplet at index {idx}."}

    import copy
    triplet = copy.deepcopy(triplets[idx])
    # Apply simple dot-notation patch (e.g. "symptom.description": "new val")
    for key, value in patch.items():
        parts = key.split(".")
        target = triplet
        for part in parts[:-1]:
            if isinstance(target, dict):
                target = target.setdefault(part, {})
        if isinstance(target, dict):
            target[parts[-1]] = value

    triplets[idx] = triplet
    gs["cleaned_triplets"] = triplets
    store["graph_state"] = gs
    return {"status": "ok", "action": "edited", "index": idx, "triplet": triplet}


async def _get_next_triplet(args, store, on_event):
    gs = store.get("graph_state") or {}
    triplets = gs.get("cleaned_triplets") or []
    review_index = store.get("review_index", 0)

    if review_index >= len(triplets):
        # All done — update phase to EXPORT
        from backend.graph.store import _record_phase
        from backend.graph.state import GraphPhase
        _record_phase(
            store, phase=GraphPhase.EXPORT,
            agent="TripletReviewAgent", decision="all_reviewed",
        )
        validated = store.get("validated_triplets") or []
        return {
            "status": "done",
            "total": len(triplets),
            "validated": len(validated),
            "message": (
                f"All {len(triplets)} triplet(s) reviewed — "
                f"{len(validated)} validated, {len(triplets) - len(validated)} skipped. "
                "Ready to export!"
            ),
            "widget": "export",
        }

    triplet = triplets[review_index]

    # Proactive critic
    if on_event:
        try:
            from backend.services.conversation.critic import critique_triplet
            for critique in critique_triplet(triplet, store):
                on_event(critique)
        except Exception:
            pass

    return {
        "status": "ok",
        "index": review_index,
        "total": len(triplets),
        "triplet": triplet,
        "graph": _build_triplet_graph_payload(triplets, focus_index=review_index),
        "widget": "triplet",
    }


async def _add_node_manual(args, store, on_event):
    import json
    from backend.app_config import get_chat_config
    from backend.config import settings
    from openai import AsyncOpenAI
    from httpx import Timeout

    node_type = args["node_type"]
    raw_text = args["raw_text"]
    cfg = get_chat_config()

    client = AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=Timeout(20.0),
    )
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


async def _export_ontology(args, store, on_event):
    import json
    import os
    from backend.services.pipeline_actions import get_current_ontology
    from backend.services.ontology_pipeline import ontology_export_payload
    from backend.services.style_cleanup_service import cleanup_export_ontology
    from backend.services.conversation import events as evt_bus

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
        cleaned, _, cleanup_report = await asyncio.to_thread(
            cleanup_export_ontology,
            ontology_dict,
            target_language=store.get("target_language", "en"),
        )
    except Exception:
        cleaned = ontology_dict
        cleanup_report = {}

    from backend.models import OntologyInstance
    cleaned_ontology = OntologyInstance.model_validate(cleaned)
    payload_json = ontology_export_payload(cleaned_ontology)

    manual_name = (
        (store.get("source_title") or store.get("pdf_id") or "export")
        .replace(" ", "_")
        .replace("/", "_")
    )
    output_dir = os.path.join("output", manual_name)
    os.makedirs(output_dir, exist_ok=True)

    ontology_path = os.path.join(output_dir, "ontology.json")
    with open(ontology_path, "w", encoding="utf-8") as f:
        f.write(payload_json)

    conversation = store.get("conversation") or {}
    conversation_path = os.path.join(output_dir, "conversation.json")
    with open(conversation_path, "w", encoding="utf-8") as f:
        json.dump(conversation, f, indent=2, ensure_ascii=False, default=str)

    # Update phase to COMPLETED
    from backend.graph.store import _record_phase
    from backend.graph.state import GraphPhase
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
        "triplets_total": len(triplets),
        "triplets_validated": len(validated),
        "cleanup_fields_changed": cleanup_report.get("deterministic_fields_changed", 0),
        "message": (
            f"Export complete — {len(validated)} validated triplet(s). "
            f"Ontology saved to `{ontology_path}`."
        ),
        "widget": "export",
    }


async def _get_progress(args, store, on_event):
    from backend.graph.store import build_status_payload
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
        GraphPhase.COMPLETED.value: "Export complete. The ontology JSON is available in output/.",
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


_DISPATCH_MAP = {
    "propose_cut_plan": _propose_cut_plan,
    "edit_cut_plan": _edit_cut_plan,
    "approve_cut_plan": _approve_cut_plan,
    "draft_ontology": _draft_ontology,
    "fill_required_field": _fill_required_field,
    "apply_suggested_relation": _apply_suggested_relation,
    "run_extraction": _run_extraction,
    "re_extract_pages": _re_extract_pages,
    "get_next_triplet": _get_next_triplet,
    "approve_triplet": _approve_triplet,
    "skip_triplet": _skip_triplet,
    "edit_triplet": _edit_triplet,
    "add_node_manual": _add_node_manual,
    "confirm_node_manual": _confirm_node_manual,
    "export_ontology": _export_ontology,
    "get_progress": _get_progress,
    "explain_phase": _explain_phase,
    "explain_decision": _explain_decision,
    "explain_entity": _explain_entity,
}
