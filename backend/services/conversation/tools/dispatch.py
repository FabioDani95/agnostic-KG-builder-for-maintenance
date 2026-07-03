"""Tool-name → implementation dispatch for the chat runtime.

Split out of the former tools.py god-file (stabilization P6); pure move.
"""

from __future__ import annotations

import logging

from typing import Any

from backend.services.conversation.tools.export import (
    _add_exported_relationship,
    _delete_exported_node,
    _delete_exported_relationship,
    _export_ontology,
    _inspect_exported_graph,
    _save_exported_graph,
    _update_exported_node,
)

from backend.services.conversation.tools.extraction import (
    _re_extract_pages,
    _run_extraction,
)

from backend.services.conversation.tools.inspect import (
    _explain_decision,
    _explain_entity,
    _explain_phase,
    _get_progress,
    _get_run_metrics,
    _list_extracted_nodes,
    _list_extracted_triplets,
)

from backend.services.conversation.tools.ontology import (
    _add_node_manual,
    _apply_suggested_relation,
    _confirm_node_manual,
    _draft_ontology,
    _fill_required_field,
)

from backend.services.conversation.tools.review import (
    _approve_triplet,
    _edit_triplet,
    _get_next_triplet,
    _skip_triplet,
)

from backend.services.conversation.tools.scoping import (
    _approve_cut_plan,
    _edit_cut_plan,
    _propose_cut_plan,
)

logger = logging.getLogger(__name__)

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
