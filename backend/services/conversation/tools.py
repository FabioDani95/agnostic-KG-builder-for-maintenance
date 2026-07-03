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
            "description": (
                "Modify the proposed section selection before approval. Use when the user adds, removes, or renames a section. "
                "IMPORTANT: to add a section you MUST know both start_page and end_page (absolute PDF page numbers, 1-indexed, >=1 and <= total_pages). "
                "If the user gives only a section name without a page range, DO NOT call this tool — ask the user for the page range first."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "add_sections": {
                        "type": "array",
                        "description": "Sections to add. Each entry requires a real page range; do not use 0 or placeholder values.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "start_page": {"type": "integer", "minimum": 1},
                                "end_page": {"type": "integer", "minimum": 1},
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
                    "patch": {
                        "type": "object",
                        "description": "Optional dot-notation field patch to save before validating.",
                        "additionalProperties": True,
                    },
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
            "name": "inspect_exported_graph",
            "description": "Inspect the exported graph after JSON generation. Use this to answer questions about node counts, node types, matching nodes, or a specific exported node.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Optional free-text search across node ids, names, types, and attributes.",
                    },
                    "node_id": {
                        "type": "string",
                        "description": "Optional exact node id to inspect in detail.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of matching nodes to return.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_exported_node",
            "description": "Modify one exported graph node by applying a partial attribute update in the shared modify workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_id": {"type": "string"},
                    "attributes": {
                        "type": "object",
                        "description": "Partial node attributes to replace.",
                        "additionalProperties": True,
                    },
                },
                "required": ["node_id", "attributes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_exported_node",
            "description": "Delete an exported graph node and all of its connected relationships from the shared modify workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_id": {"type": "string"},
                },
                "required": ["node_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_exported_relationship",
            "description": "Add a relationship between two exported graph nodes in the shared modify workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "relation_type": {"type": "string"},
                    "from_id": {"type": "string"},
                    "to_id": {"type": "string"},
                },
                "required": ["relation_type", "from_id", "to_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_exported_relationship",
            "description": "Delete one exported graph relationship by its index from the shared modify workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                },
                "required": ["index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_exported_graph",
            "description": "Save the current shared modify workspace as the next ontology file version.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_extracted_nodes",
            "description": "List ontology nodes already extracted in the current workflow, grouped by type. Use when the user asks which nodes, node types, assets, symptoms, failure modes, actions, or entities have been found.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_type": {
                        "type": "string",
                        "description": "Optional node type filter, e.g. Asset, Component, Symptom, FailureMode, CorrectiveAction, ErrorCode.",
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional text filter across node id, name, description, and type.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum nodes to return overall.",
                    },
                    "include_descriptions": {
                        "type": "boolean",
                        "description": "Whether to include short node descriptions.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_extracted_triplets",
            "description": "List triplets already extracted in the current workflow, including review status and the Symptom → FailureMode → CorrectiveAction chain.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["all", "pending", "validated", "skipped"],
                        "description": "Optional review-status filter.",
                    },
                    "query": {
                        "type": "string",
                        "description": "Optional text filter across symptom, failure modes, corrective actions, ids, and descriptions.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum triplets to return.",
                    },
                },
                "required": [],
            },
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
            "name": "get_run_metrics",
            "description": "Show the extraction KPIs: total duration, estimated cost, token usage, stage breakdown, model cost breakdown, node counts, and derived metrics.",
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
    resolution_report = getattr(result, "resolution_completion_report", {}) or {}
    resolution_attempts = list(resolution_report.get("attempts") or [])

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
        "resolution_completion": {
            "target_count": int(resolution_report.get("target_count", 0) or 0),
            "attempted": int(resolution_report.get("attempted", 0) or 0),
            "completed": int(resolution_report.get("completed", 0) or 0),
            "attempts": resolution_attempts[:5],
        },
        "preview_relations": preview_relations,
        "confidence_counts": getattr(confidence_report, "counts", {}) if confidence_report else {},
        "review_summary": getattr(result, "review_summary", {}) or {},
        "review_queue": (getattr(result, "review_queue", []) or [])[:20],
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


_NODE_ID_FIELDS = {
    "Asset": "asset_id",
    "Component": "component_id",
    "Symptom": "symptom_id",
    "FailureMode": "failure_mode_id",
    "CorrectiveAction": "action_id",
    "ErrorCode": "error_code_id",
}


def _node_identity(node_type: str, node: dict[str, Any]) -> tuple[str, str, str]:
    id_field = _NODE_ID_FIELDS.get(str(node_type), "id")
    node_id = str(node.get(id_field) or node.get("id") or "").strip()
    name = str(node.get("name") or node.get("label") or node_id).strip()
    description = str(node.get("description") or node.get("instruction_text") or "").strip()
    return node_id, name, description


def _collect_extracted_nodes(store: dict[str, Any]) -> list[dict[str, Any]]:
    pipeline_state = store.get("ontology_pipeline") or (store.get("graph_state") or {}).get("ontology_pipeline") or {}
    ontology = pipeline_state.get("ontology") if isinstance(pipeline_state, dict) else {}
    nodes_by_type = ontology.get("nodes") if isinstance(ontology, dict) else {}

    collected: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    if isinstance(nodes_by_type, dict):
        for node_type, items in nodes_by_type.items():
            for raw_node in items or []:
                node = _as_plain_dict(raw_node)
                node_id, name, description = _node_identity(str(node_type), node)
                if not node_id and not name:
                    continue
                key = (str(node_type), node_id or name.lower())
                if key in seen:
                    continue
                seen.add(key)
                collected.append({
                    "id": node_id,
                    "name": name or node_id,
                    "type": str(node_type),
                    "description": description,
                    "source": "ontology",
                })

    gs = store.get("graph_state") or {}
    triplets = gs.get("cleaned_triplets") or []
    for raw_triplet in triplets:
        triplet = _as_plain_dict(raw_triplet)
        symptom = _as_plain_dict(triplet.get("symptom"))
        triplet_nodes = [("Symptom", symptom)]
        triplet_nodes.extend(("FailureMode", _as_plain_dict(item)) for item in (triplet.get("failure_modes") or []))
        triplet_nodes.extend(("CorrectiveAction", _as_plain_dict(item)) for item in (triplet.get("corrective_actions") or []))
        for node_type, node in triplet_nodes:
            node_id, name, description = _node_identity(node_type, node)
            if not node_id and not name:
                continue
            key = (node_type, node_id or name.lower())
            if key in seen:
                continue
            seen.add(key)
            collected.append({
                "id": node_id,
                "name": name or node_id,
                "type": node_type,
                "description": description,
                "source": "triplet_extraction",
            })

    return collected


def _node_type_counts(nodes: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in nodes:
        node_type = str(node.get("type") or "Unknown")
        counts[node_type] = counts.get(node_type, 0) + 1
    return counts


def _filter_inventory_items(
    items: list[dict[str, Any]],
    *,
    query: str = "",
) -> list[dict[str, Any]]:
    terms = [term for term in str(query or "").lower().split() if term]
    if not terms:
        return items
    matches = []
    for item in items:
        haystack = " ".join(str(value) for value in item.values() if value is not None).lower()
        if all(term in haystack for term in terms):
            matches.append(item)
    return matches


def build_extraction_memory_snapshot(store: dict[str, Any], *, limit_per_type: int = 5) -> dict[str, Any]:
    """Compact facts the chatbot may safely remember across turns."""
    nodes = _collect_extracted_nodes(store)
    counts = _node_type_counts(nodes)
    preview_by_type: dict[str, list[str]] = {}
    for node in nodes:
        node_type = str(node.get("type") or "Unknown")
        bucket = preview_by_type.setdefault(node_type, [])
        if len(bucket) < limit_per_type:
            label = str(node.get("name") or node.get("id") or "").strip()
            if node.get("id") and node.get("id") != label:
                label = f"{label} ({node['id']})"
            if label:
                bucket.append(label)

    gs = store.get("graph_state") or {}
    triplets = list(gs.get("cleaned_triplets") or [])
    validated = list(store.get("validated_triplets") or [])
    return {
        "node_count": len(nodes),
        "node_type_counts": counts,
        "node_preview_by_type": preview_by_type,
        "triplet_count": len(triplets),
        "validated_triplet_count": len(validated),
        "review_index": int(store.get("review_index") or 0),
    }


def _format_node_inventory_message(result: dict[str, Any]) -> str:
    total = int(result.get("total_nodes") or 0)
    counts = result.get("node_type_counts") or {}
    nodes_by_type = result.get("nodes_by_type") or {}
    if not total:
        return "I do not have extracted nodes yet in the current workflow."

    count_text = ", ".join(f"{node_type}: {count}" for node_type, count in sorted(counts.items()))
    lines = [f"I found {total} extracted node(s). Types: {count_text}."]
    for node_type in sorted(nodes_by_type):
        labels = []
        for node in nodes_by_type[node_type]:
            label = str(node.get("name") or node.get("id") or "").strip()
            if node.get("id") and node.get("id") != label:
                label = f"{label} ({node['id']})"
            if node.get("description"):
                label = f"{label}: {node['description']}"
            if label:
                labels.append(label)
        if labels:
            lines.append(f"{node_type}: " + "; ".join(labels))
    if result.get("truncated"):
        lines.append("This is a compact list; ask for a specific type or search term to narrow it.")
    return "\n".join(lines)


def _triplet_summary(raw_triplet: Any, index: int, status: str) -> dict[str, Any]:
    triplet = _as_plain_dict(raw_triplet)
    symptom = _as_plain_dict(triplet.get("symptom"))
    failure_modes = [_as_plain_dict(item) for item in (triplet.get("failure_modes") or [])]
    corrective_actions = [_as_plain_dict(item) for item in (triplet.get("corrective_actions") or [])]
    return {
        "index": index,
        "status": status,
        "symptom": {
            "id": str(symptom.get("symptom_id") or ""),
            "name": str(symptom.get("name") or symptom.get("symptom_id") or ""),
            "description": str(symptom.get("description") or ""),
            "page": symptom.get("evidence_page"),
        },
        "failure_modes": [
            {
                "id": str(item.get("failure_mode_id") or ""),
                "name": str(item.get("name") or item.get("failure_mode_id") or ""),
                "description": str(item.get("description") or ""),
                "page": item.get("evidence_page"),
            }
            for item in failure_modes
        ],
        "corrective_actions": [
            {
                "id": str(item.get("action_id") or ""),
                "name": str(item.get("name") or item.get("action_id") or ""),
                "description": str(item.get("description") or ""),
                "instruction_text": str(item.get("instruction_text") or ""),
                "page": item.get("source_page"),
                "linked_failure_mode_id": str(item.get("linked_failure_mode_id") or ""),
            }
            for item in corrective_actions
        ],
    }


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


def _triplet_identity(triplet: Any) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    plain = _as_plain_dict(triplet)
    symptom = _as_plain_dict(plain.get("symptom"))
    failure_modes = tuple(
        str(_as_plain_dict(fm).get("failure_mode_id") or "")
        for fm in (plain.get("failure_modes") or [])
    )
    corrective_actions = tuple(
        str(_as_plain_dict(ca).get("action_id") or "")
        for ca in (plain.get("corrective_actions") or [])
    )
    return (
        str(symptom.get("symptom_id") or ""),
        failure_modes,
        corrective_actions,
    )


def _contains_triplet(triplets: list[Any], triplet: Any) -> bool:
    identity = _triplet_identity(triplet)
    return any(_triplet_identity(item) == identity for item in triplets or [])


def _build_review_graph_payload(
    store: dict[str, Any],
    *,
    focus_index: int | None = None,
) -> dict[str, Any]:
    """Graph shown during HITL review: approved triplets plus current preview."""
    gs = store.get("graph_state") or {}
    all_triplets = list(gs.get("cleaned_triplets") or [])
    approved_triplets = list(store.get("validated_triplets") or [])
    visible_triplets = list(approved_triplets)
    focus_payload_index: int | None = None
    current_is_preview = False

    if focus_index is not None and 0 <= focus_index < len(all_triplets):
        current = all_triplets[focus_index]
        for idx, item in enumerate(visible_triplets):
            if _triplet_identity(item) == _triplet_identity(current):
                focus_payload_index = idx
                break
        if focus_payload_index is None:
            visible_triplets.append(current)
            focus_payload_index = len(visible_triplets) - 1
            current_is_preview = True

    graph = _build_triplet_graph_payload(visible_triplets, focus_index=focus_payload_index)
    graph.update({
        "review_graph": True,
        "approved_triplet_count": len(approved_triplets),
        "total_triplets": len(all_triplets),
        "current_triplet_index": focus_index,
        "current_is_preview": current_is_preview,
    })
    return graph


def _triplet_logic_assessment(triplet: dict[str, Any]) -> list[str]:
    def _safe_int(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    symptom = _as_plain_dict(triplet.get("symptom"))
    failure_modes = [_as_plain_dict(item) for item in (triplet.get("failure_modes") or [])]
    corrective_actions = [_as_plain_dict(item) for item in (triplet.get("corrective_actions") or [])]

    symptom_name = str(symptom.get("name") or symptom.get("symptom_id") or "this symptom")
    linked_actions = [
        action for action in corrective_actions
        if str(action.get("linked_failure_mode_id") or "").strip()
    ]
    if failure_modes and corrective_actions and linked_actions:
        line_one = (
            f"Logic: '{symptom_name}' forms a reviewable chain with "
            f"{len(failure_modes)} failure mode(s) and {len(corrective_actions)} corrective action(s)."
        )
    else:
        missing = []
        if not failure_modes:
            missing.append("failure mode")
        if not corrective_actions:
            missing.append("corrective action")
        if corrective_actions and not linked_actions:
            missing.append("failure-to-action link")
        line_one = (
            f"Logic: '{symptom_name}' is incomplete; missing "
            f"{', '.join(missing) or 'a clear chain'}."
        )

    pages = [
        _safe_int(symptom.get("evidence_page")),
        *[_safe_int(item.get("evidence_page")) for item in failure_modes],
        *[_safe_int(item.get("source_page")) for item in corrective_actions],
    ]
    pages = [page for page in pages if page > 0]
    action_with_instruction = any(str(action.get("instruction_text") or "").strip() for action in corrective_actions)
    if pages and action_with_instruction:
        line_two = (
            f"Sense check: source page(s) {', '.join(map(str, sorted(set(pages))))} are traceable, "
            "and at least one action has concrete instructions."
        )
    elif pages:
        line_two = (
            f"Sense check: source page(s) {', '.join(map(str, sorted(set(pages))))} are traceable, "
            "but the corrective instruction is weak or empty."
        )
    else:
        line_two = "Sense check: no source page is attached, so verify this against the manual before approving."
    return [line_one, line_two]


def _apply_triplet_patch(triplet: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Apply dot-notation patches, including list indices such as failure_modes.0.name."""
    for key, value in (patch or {}).items():
        parts = [part for part in str(key).split(".") if part]
        if not parts:
            continue
        target: Any = triplet
        for part in parts[:-1]:
            if isinstance(target, list):
                try:
                    target = target[int(part)]
                except (ValueError, IndexError):
                    target = None
            elif isinstance(target, dict):
                target = target.setdefault(part, {})
            else:
                target = None
            if target is None:
                break
        if target is None:
            continue
        leaf = parts[-1]
        if isinstance(target, list):
            try:
                target[int(leaf)] = value
            except (ValueError, IndexError):
                continue
        elif isinstance(target, dict):
            target[leaf] = value
    return triplet


def _modify_workspace_payload(store: dict[str, Any], *, refresh: bool = False) -> dict[str, Any]:
    pdf_id = str(store.get("pdf_id") or "latest")
    return {
        "editor_url": f"/modify/{pdf_id}" if pdf_id and pdf_id != "latest" else "/modify",
        "pdf_id": pdf_id,
        "refresh": refresh,
    }


def _resolve_exported_graph_path(store: dict[str, Any]):
    from backend.services import graph_editor_session

    return graph_editor_session.resolve_ontology_path(
        str(store.get("pdf_id") or "latest"),
        store=store,
    )


def _graph_type_counts(ontology: dict[str, Any]) -> tuple[dict[str, int], dict[str, int]]:
    node_type_counts = {
        str(node_type): len(items or [])
        for node_type, items in (ontology.get("nodes") or {}).items()
        if items
    }

    edge_type_counts: dict[str, int] = {}
    for rel in ontology.get("relations") or ontology.get("relationships") or []:
        rel_type = str(rel.get("name") or rel.get("type") or "").strip()
        if not rel_type:
            continue
        edge_type_counts[rel_type] = edge_type_counts.get(rel_type, 0) + 1
    return node_type_counts, edge_type_counts


def _search_exported_nodes(ontology: dict[str, Any], query: str, *, limit: int = 8) -> list[dict[str, Any]]:
    from modify.graph import _node_id, _node_label

    terms = [term for term in str(query or "").lower().split() if term]
    if not terms:
        return []

    matches: list[dict[str, Any]] = []
    for node_type, items in (ontology.get("nodes") or {}).items():
        for obj in items or []:
            node_id = _node_id(obj)
            if not node_id:
                continue
            label = _node_label(obj, node_id)
            haystack = " ".join(
                [
                    str(node_type),
                    str(node_id),
                    str(label),
                    *(str(value) for value in obj.values()),
                ]
            ).lower()
            if not all(term in haystack for term in terms):
                continue
            matches.append({
                "id": node_id,
                "label": label,
                "type": str(node_type),
            })
            if len(matches) >= limit:
                return matches
    return matches


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


def _visible_sections_for_widget(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sections shown in the UI widget: drop keyword-fallback entries.

    Keyword-match sections are still kept in pages_to_keep so the pipeline
    does not lose recall, but they are opaque to the operator (e.g. "Keyword
    match (pp. 1-5)") and confuse the selection UI.
    """
    visible: list[dict[str, Any]] = []
    for sec in sections or []:
        if not isinstance(sec, dict):
            continue
        source = str(sec.get("source") or "").lower()
        name = str(sec.get("name") or "")
        if source == "keyword":
            continue
        if name.lower().startswith("keyword match"):
            continue
        visible.append(sec)
    return visible


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

    all_sections = [
        {
            "name": s.name,
            "start": s.page_range.start,
            "end": s.page_range.end,
            "source": s.source,
        }
        for s in result.sections
    ]
    visible_sections = _visible_sections_for_widget(all_sections)
    keyword_section_count = len(all_sections) - len(visible_sections)
    return {
        "status": "ok",
        "sections": visible_sections,
        "pages_to_keep": result.pages_to_keep,
        "total_pages": result.total_pages,
        "keyword_fallback_sections": keyword_section_count,
        "skipped": result.skipped,
        "product_info": result.product_info.model_dump() if result.product_info else None,
        "widget": "sections",
    }


async def _edit_cut_plan(args, store, on_event):
    cut_plan = store.get("cut_plan") or {}
    sections = list(cut_plan.get("sections") or [])

    total_pages = int(
        cut_plan.get("total_pages")
        or (store.get("graph_state") or {}).get("total_pages")
        or len(store.get("pages") or [])
        or 0
    )

    remove_names = {n.lower() for n in (args.get("remove_section_names") or [])}
    if remove_names:
        sections = [s for s in sections if s.get("name", "").lower() not in remove_names]

    rejected_adds: list[dict[str, Any]] = []
    accepted_adds: list[dict[str, Any]] = []
    for new_sec in (args.get("add_sections") or []):
        name = str(new_sec.get("name") or "").strip()
        try:
            start = int(new_sec.get("start_page"))
            end = int(new_sec.get("end_page"))
        except (TypeError, ValueError):
            start = end = 0
        reason = None
        if not name:
            reason = "missing section name"
        elif start <= 0 or end <= 0:
            reason = "missing or invalid page range (start_page and end_page must be >= 1)"
        elif end < start:
            reason = f"end_page ({end}) is smaller than start_page ({start})"
        elif total_pages and (start > total_pages or end > total_pages):
            reason = f"page range {start}-{end} exceeds total_pages ({total_pages})"

        if reason:
            rejected_adds.append({"name": name or "(unnamed)", "start": start, "end": end, "reason": reason})
            continue

        accepted_adds.append({
            "name": name,
            "start": start,
            "end": end,
            "source": "human",
        })

    sections.extend(accepted_adds)

    if rejected_adds and not accepted_adds and not remove_names:
        details = "; ".join(f"{r['name']} ({r['reason']})" for r in rejected_adds)
        return {
            "status": "refused",
            "widget": "sections",
            "sections": _visible_sections_for_widget(sections),
            "pages_to_keep": cut_plan.get("pages_to_keep") or [],
            "total_pages": total_pages,
            "keyword_fallback_sections": len(sections) - len(_visible_sections_for_widget(sections)),
            "product_info": cut_plan.get("product_info"),
            "rejected_adds": rejected_adds,
            "message": (
                f"I couldn't add the section(s) because: {details}. "
                "Please tell me the absolute PDF page range (e.g. \"Errors, pages 42 to 58\") and I'll retry."
            ),
        }

    cut_plan["sections"] = sections
    pages_to_keep = set()
    for sec in sections:
        pages_to_keep.update(range(int(sec["start"]), int(sec["end"]) + 1))
    cut_plan["pages_to_keep"] = sorted(pages_to_keep)
    store["cut_plan"] = cut_plan

    visible_sections = _visible_sections_for_widget(sections)
    payload: dict[str, Any] = {
        "status": "ok",
        "sections": visible_sections,
        "pages_to_keep": cut_plan["pages_to_keep"],
        "total_pages": total_pages,
        "keyword_fallback_sections": len(sections) - len(visible_sections),
        "product_info": cut_plan.get("product_info"),
        "widget": "sections",
    }
    if rejected_adds:
        details = "; ".join(f"{r['name']} ({r['reason']})" for r in rejected_adds)
        payload["rejected_adds"] = rejected_adds
        payload["message"] = (
            f"Applied {len(accepted_adds)} addition(s). Skipped: {details}. "
            "Give me the page range for the skipped section(s) to retry."
        )
    return payload


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
        "graph": _build_review_graph_payload(store, focus_index=0 if triplets else None),
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
    patch = args.get("patch") or {}
    gs = store.get("graph_state") or {}
    triplets = gs.get("cleaned_triplets") or []
    triplet = triplets[idx]
    if patch:
        import copy
        triplet = _apply_triplet_patch(copy.deepcopy(triplet), patch)
        triplets[idx] = triplet
        gs["cleaned_triplets"] = triplets
        store["graph_state"] = gs
    validated = store.setdefault("validated_triplets", [])
    if not _contains_triplet(validated, triplet):
        validated.append(triplet)
    store["review_index"] = idx + 1
    return {
        "status": "ok",
        "action": "validated",
        "index": idx,
        "graph": _build_review_graph_payload(store),
        "widget": "extraction_graph",
    }


async def _skip_triplet(args, store, on_event):
    idx = args["index"]
    store["review_index"] = idx + 1
    return {
        "status": "ok",
        "action": "skipped",
        "index": idx,
        "graph": _build_review_graph_payload(store),
        "widget": "extraction_graph",
    }


async def _edit_triplet(args, store, on_event):
    idx = args["index"]
    patch = args.get("patch") or {}
    gs = store.get("graph_state") or {}
    triplets = gs.get("cleaned_triplets") or []
    if not triplets or idx >= len(triplets):
        return {"status": "error", "message": f"No triplet at index {idx}."}

    import copy
    triplet = _apply_triplet_patch(copy.deepcopy(triplets[idx]), patch)

    triplets[idx] = triplet
    gs["cleaned_triplets"] = triplets
    store["graph_state"] = gs
    return {
        "status": "ok",
        "action": "edited",
        "index": idx,
        "total": len(triplets),
        "triplet": triplet,
        "graph": _build_review_graph_payload(store, focus_index=idx),
        "widget": "triplet",
        "logic_assessment": _triplet_logic_assessment(triplet),
        "message": "Triplet edits saved. Review the updated card before approving or skipping.",
    }


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
            "exported": False,
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
        "logic_assessment": _triplet_logic_assessment(triplet),
        "graph": _build_review_graph_payload(store, focus_index=review_index),
        "widget": "triplet",
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


async def _export_ontology(args, store, on_event):
    import json
    import time
    from backend.services.pipeline_actions import get_current_ontology
    from backend.services.ontology_export_store import (
        persist_export_metrics,
        persist_exported_ontology,
        prepare_exported_ontology,
    )
    from backend.services.run_metrics import aggregate_usage, build_metrics_payload, record_stage_metrics
    from backend.services.style_cleanup_service import cleanup_export_ontology
    from backend.services.conversation import events as evt_bus

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
        "download_filename": export_info.get("download_filename") or export_info["filename"],
        "triplets_total": len(triplets),
        "triplets_validated": len(validated),
        "cleanup_fields_changed": cleanup_report.get("deterministic_fields_changed", 0),
        "exported": True,
        "metrics": metrics_payload,
        **_modify_workspace_payload(store, refresh=False),
        "message": (
            f"Export complete — {len(validated)} validated triplet(s). "
            f"Ontology saved to `{ontology_path}`. "
            "The full extraction KPIs are shown below. Would you like to inspect and modify the graph now?"
        ),
        "widget": "export",
    }

async def _inspect_exported_graph(args, store, on_event):
    from backend.services import graph_editor_session

    path = _resolve_exported_graph_path(store)
    ontology = graph_editor_session.current_ontology(path)
    status = graph_editor_session.status_payload(path)
    node_type_counts, edge_type_counts = _graph_type_counts(ontology)
    total_nodes = sum(node_type_counts.values())
    total_relationships = sum(edge_type_counts.values())

    node_id = str(args.get("node_id") or "").strip()
    query = str(args.get("query") or "").strip()
    limit = max(1, min(int(args.get("limit") or 8), 20))

    if node_id:
        try:
            node = graph_editor_session.node_detail_payload(path, node_id)
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


async def _update_exported_node(args, store, on_event):
    from backend.services import graph_editor_session

    path = _resolve_exported_graph_path(store)
    node_id = str(args.get("node_id") or "").strip()
    attributes = args.get("attributes") or {}
    try:
        result = graph_editor_session.update_node(path, node_id, attributes)
    except ValueError as exc:
        return {"status": "refused", "message": str(exc)}
    except KeyError:
        return {"status": "refused", "message": f"Node `{node_id}` was not found in the exported graph."}

    return {
        "status": "ok",
        "node_id": node_id,
        "vis_node": result.get("vis_node"),
        "message": f"Node `{node_id}` updated in the modify workspace. Save a new version when you are ready.",
        **_modify_workspace_payload(store, refresh=True),
        "widget": "modify_workspace_sync",
    }


async def _delete_exported_node(args, store, on_event):
    from backend.services import graph_editor_session

    path = _resolve_exported_graph_path(store)
    node_id = str(args.get("node_id") or "").strip()
    try:
        result = graph_editor_session.delete_node(path, node_id)
    except KeyError:
        return {"status": "refused", "message": f"Node `{node_id}` was not found in the exported graph."}

    return {
        "status": "ok",
        "node_id": node_id,
        "removed_relationships": result.get("removed_relationships", 0),
        "message": (
            f"Node `{node_id}` deleted from the modify workspace. "
            f"{result.get('removed_relationships', 0)} relationship(s) were removed with it."
        ),
        **_modify_workspace_payload(store, refresh=True),
        "widget": "modify_workspace_sync",
    }


async def _add_exported_relationship(args, store, on_event):
    from backend.services import graph_editor_session

    path = _resolve_exported_graph_path(store)
    relation_type = str(args.get("relation_type") or "").strip()
    from_id = str(args.get("from_id") or "").strip()
    to_id = str(args.get("to_id") or "").strip()
    try:
        result = graph_editor_session.add_relationship(path, relation_type, from_id, to_id)
    except ValueError as exc:
        return {"status": "refused", "message": str(exc)}

    return {
        "status": "ok",
        "edge": result.get("edge"),
        "message": (
            f"Relationship `{relation_type}` added from `{from_id}` to `{to_id}` in the modify workspace. "
            "Save a new version when you are ready."
        ),
        **_modify_workspace_payload(store, refresh=True),
        "widget": "modify_workspace_sync",
    }


async def _delete_exported_relationship(args, store, on_event):
    from backend.services import graph_editor_session

    path = _resolve_exported_graph_path(store)
    index = int(args.get("index"))
    try:
        result = graph_editor_session.delete_relationship(path, index)
    except IndexError as exc:
        return {"status": "refused", "message": str(exc)}

    removed = result.get("removed") or {}
    rel_type = removed.get("name") or removed.get("type") or "relationship"
    return {
        "status": "ok",
        "index": index,
        "removed": removed,
        "message": f"Relationship {index} (`{rel_type}`) was removed from the modify workspace.",
        **_modify_workspace_payload(store, refresh=True),
        "widget": "modify_workspace_sync",
    }


async def _save_exported_graph(args, store, on_event):
    from backend.services import graph_editor_session

    path = _resolve_exported_graph_path(store)
    try:
        result = graph_editor_session.save_session(path, store=store)
    except ValueError as exc:
        return {"status": "refused", "message": str(exc)}

    return {
        "status": "ok",
        "version": result.get("version"),
        "saved_as": result.get("saved_as"),
        "message": f"Modify workspace saved as `{result.get('saved_as')}` (version {result.get('version')}).",
        **_modify_workspace_payload(store, refresh=True),
        "widget": "modify_workspace_sync",
    }


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
        GraphPhase.COMPLETED.value: "Export complete. The ontology JSON is available in output/, and you can now inspect or modify the exported graph.",
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
    "inspect_exported_graph": _inspect_exported_graph,
    "update_exported_node": _update_exported_node,
    "delete_exported_node": _delete_exported_node,
    "add_exported_relationship": _add_exported_relationship,
    "delete_exported_relationship": _delete_exported_relationship,
    "save_exported_graph": _save_exported_graph,
    "list_extracted_nodes": _list_extracted_nodes,
    "list_extracted_triplets": _list_extracted_triplets,
    "get_progress": _get_progress,
    "get_run_metrics": _get_run_metrics,
    "explain_phase": _explain_phase,
    "explain_decision": _explain_decision,
    "explain_entity": _explain_entity,
}
