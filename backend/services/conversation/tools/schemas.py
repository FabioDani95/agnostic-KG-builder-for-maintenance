"""OpenAI function-calling schemas and per-phase tool availability.

Split out of the former tools.py god-file (stabilization P6); pure move.
"""

from __future__ import annotations

from typing import Any

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


def tools_for_phase(phase: str) -> list[dict[str, Any]]:
    """Return the subset of tool schemas relevant to the current phase."""
    from backend.services.conversation.gate import _ALWAYS_ALLOWED, _PHASE_TOOLS
    allowed = _PHASE_TOOLS.get(phase, set()) | _ALWAYS_ALLOWED
    return [t for t in TOOL_SCHEMAS if t["function"]["name"] in allowed]
