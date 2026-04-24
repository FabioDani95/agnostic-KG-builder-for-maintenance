"""Deterministic phase gate.

Decides which tools are callable in the current pipeline phase and
validates their arguments against the live store. Returns (allowed, reason).
The chat orchestrator uses this BEFORE dispatching any tool call.
"""

from __future__ import annotations

from typing import Any

from backend.graph.state import GraphPhase

# --- Phase → allowed tool names -----------------------------------------

_PHASE_TOOLS: dict[str, set[str]] = {
    GraphPhase.LOADED.value: {
        "propose_cut_plan",
        "get_progress",
        "explain_phase",
    },
    GraphPhase.SCOPING.value: {
        "propose_cut_plan",
        "edit_cut_plan",
        "approve_cut_plan",
        "get_progress",
        "explain_phase",
        "explain_decision",
    },
    GraphPhase.ONTOLOGY_DRAFT.value: {
        "draft_ontology",
        "run_extraction",          # user can start extraction directly from the review widget
        "fill_required_field",
        "apply_suggested_relation",
        "get_progress",
        "explain_phase",
        "explain_decision",
        "explain_entity",
    },
    GraphPhase.EXTRACTION.value: {
        "fill_required_field",
        "apply_suggested_relation",
        "run_extraction",
        "re_extract_pages",
        "get_next_triplet",
        "approve_triplet",
        "skip_triplet",
        "edit_triplet",
        "add_node_manual",
        "confirm_node_manual",
        "get_progress",
        "explain_phase",
        "explain_decision",
        "explain_entity",
    },
    GraphPhase.VALIDATION.value: {
        "run_extraction",
        "re_extract_pages",
        "get_next_triplet",
        "approve_triplet",
        "skip_triplet",
        "edit_triplet",
        "get_progress",
        "explain_phase",
        "explain_decision",
        "explain_entity",
        "add_node_manual",
        "confirm_node_manual",
    },
    GraphPhase.EXPORT.value: {
        "export_ontology",
        "get_next_triplet",
        "get_progress",
        "explain_phase",
        "add_node_manual",
        "confirm_node_manual",
    },
    GraphPhase.COMPLETED.value: {
        "export_ontology",
        "inspect_exported_graph",
        "update_exported_node",
        "delete_exported_node",
        "add_exported_relationship",
        "delete_exported_relationship",
        "save_exported_graph",
        "get_progress",
    },
}

# Tools allowed in *any* phase when a run is active (after scoping starts)
_ALWAYS_ALLOWED: set[str] = {
    "get_progress",
    "get_run_metrics",
    "explain_phase",
    "explain_decision",
}

# Map of tool name → valid GraphPhase values (phases where the tool makes sense)
# Used for user-friendly error messages.
_TOOL_EARLIEST_PHASE: dict[str, str] = {
    "propose_cut_plan": GraphPhase.LOADED.value,
    "edit_cut_plan": GraphPhase.SCOPING.value,
    "approve_cut_plan": GraphPhase.SCOPING.value,
    "draft_ontology": GraphPhase.ONTOLOGY_DRAFT.value,
    "fill_required_field": GraphPhase.EXTRACTION.value,
    "apply_suggested_relation": GraphPhase.EXTRACTION.value,
    "run_extraction": GraphPhase.ONTOLOGY_DRAFT.value,
    "re_extract_pages": GraphPhase.EXTRACTION.value,
    "approve_triplet": GraphPhase.EXTRACTION.value,
    "skip_triplet": GraphPhase.EXTRACTION.value,
    "edit_triplet": GraphPhase.EXTRACTION.value,
    "add_node_manual": GraphPhase.EXTRACTION.value,
    "confirm_node_manual": GraphPhase.EXTRACTION.value,
    "get_next_triplet": GraphPhase.EXTRACTION.value,
    "export_ontology": GraphPhase.EXPORT.value,
    "inspect_exported_graph": GraphPhase.COMPLETED.value,
    "update_exported_node": GraphPhase.COMPLETED.value,
    "delete_exported_node": GraphPhase.COMPLETED.value,
    "add_exported_relationship": GraphPhase.COMPLETED.value,
    "delete_exported_relationship": GraphPhase.COMPLETED.value,
    "save_exported_graph": GraphPhase.COMPLETED.value,
}

_PHASE_LABELS: dict[str, str] = {
    GraphPhase.LOADED.value: "manual loaded (ready to scope)",
    GraphPhase.SCOPING.value: "scoping in progress",
    GraphPhase.ONTOLOGY_DRAFT.value: "ontology drafting",
    GraphPhase.EXTRACTION.value: "ontology review",
    GraphPhase.VALIDATION.value: "triplet review",
    GraphPhase.EXPORT.value: "ready to export",
    GraphPhase.COMPLETED.value: "completed",
}


def _get_phase(store: dict) -> str:
    gs = store.get("graph_state") or {}
    return str(gs.get("current_phase") or GraphPhase.LOADED.value)


def is_allowed(tool_name: str, store: dict) -> tuple[bool, str]:
    """Return (True, "") if tool_name is callable in current phase, else (False, reason)."""
    if tool_name in _ALWAYS_ALLOWED:
        return True, ""

    phase = _get_phase(store)
    allowed = _PHASE_TOOLS.get(phase, set())

    if tool_name in allowed:
        return True, ""

    phase_label = _PHASE_LABELS.get(phase, phase)
    earliest = _TOOL_EARLIEST_PHASE.get(tool_name)
    if earliest:
        earliest_label = _PHASE_LABELS.get(earliest, earliest)
        reason = (
            f"'{tool_name}' is not available during the {phase_label} phase. "
            f"It becomes available once we reach: {earliest_label}."
        )
    else:
        reason = f"'{tool_name}' is not a recognized action."
    return False, reason


def validate_args(tool_name: str, args: dict[str, Any], store: dict) -> tuple[bool, str]:
    """Validate tool arguments against current store state. Returns (ok, reason)."""
    pages = store.get("pages") or []
    total_pages = len(pages)

    if tool_name == "re_extract_pages":
        start = args.get("start_page")
        end = args.get("end_page")
        if start is None or end is None:
            return False, "re_extract_pages requires start_page and end_page."
        if not isinstance(start, int) or not isinstance(end, int):
            return False, "start_page and end_page must be integers."
        if start < 1 or end < start:
            return False, f"Invalid page range: {start}–{end}. Start must be ≥ 1 and end ≥ start."
        page_numbers = {p["page_number"] for p in pages}
        if start not in page_numbers or end not in page_numbers:
            return False, (
                f"Pages {start}–{end} are outside this document "
                f"(valid range: 1–{total_pages})."
            )

    if tool_name in ("approve_triplet", "skip_triplet", "edit_triplet"):
        idx = args.get("index")
        gs = store.get("graph_state") or {}
        triplets = gs.get("cleaned_triplets") or []
        if idx is None:
            return False, f"{tool_name} requires an index."
        if not isinstance(idx, int) or idx < 0 or idx >= len(triplets):
            return False, (
                f"Triplet index {idx} is out of range "
                f"(0–{len(triplets) - 1 if triplets else 0})."
            )

    if tool_name == "fill_required_field":
        field_key = args.get("field_key")
        value = args.get("value")
        if not field_key or value is None:
            return False, "fill_required_field requires field_key and value."
        pipeline_state = store.get("ontology_pipeline") or {}
        required = pipeline_state.get("human_required_fields") or []
        valid_keys = {f.get("field_key") for f in required if isinstance(f, dict)}
        if valid_keys and field_key not in valid_keys:
            return False, (
                f"Unknown field_key '{field_key}'. "
                f"Valid keys: {', '.join(sorted(valid_keys))}."
            )

    if tool_name == "add_node_manual":
        node_type = args.get("node_type")
        valid_types = {"Asset", "Component", "Symptom", "FailureMode", "CorrectiveAction", "ErrorCode"}
        if not node_type:
            return False, "add_node_manual requires node_type."
        if node_type not in valid_types:
            return False, (
                f"'{node_type}' is not a valid node type. "
                f"Valid types: {', '.join(sorted(valid_types))}."
            )
        if not args.get("raw_text"):
            return False, "add_node_manual requires raw_text describing the node."

    if tool_name == "inspect_exported_graph":
        limit = args.get("limit")
        if limit is not None and (not isinstance(limit, int) or limit < 1 or limit > 20):
            return False, "inspect_exported_graph limit must be an integer between 1 and 20."

    if tool_name == "update_exported_node":
        if not args.get("node_id"):
            return False, "update_exported_node requires node_id."
        attributes = args.get("attributes")
        if not isinstance(attributes, dict) or not attributes:
            return False, "update_exported_node requires a non-empty attributes object."

    if tool_name == "delete_exported_node":
        if not args.get("node_id"):
            return False, "delete_exported_node requires node_id."

    if tool_name == "add_exported_relationship":
        if not args.get("relation_type") or not args.get("from_id") or not args.get("to_id"):
            return False, "add_exported_relationship requires relation_type, from_id, and to_id."

    if tool_name == "delete_exported_relationship":
        index = args.get("index")
        if not isinstance(index, int) or index < 0:
            return False, "delete_exported_relationship requires a non-negative integer index."

    return True, ""


def check(tool_name: str, args: dict[str, Any], store: dict) -> tuple[bool, str]:
    """Combined phase + argument check. Returns (ok, reason)."""
    ok, reason = is_allowed(tool_name, store)
    if not ok:
        return False, reason
    return validate_args(tool_name, args, store)
