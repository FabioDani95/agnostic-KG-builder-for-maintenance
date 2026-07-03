"""Shared payload builders and inventory/graph helpers for chat tools.

Split out of the former tools.py god-file (stabilization P6); pure move.
"""

from __future__ import annotations

from typing import Any

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
