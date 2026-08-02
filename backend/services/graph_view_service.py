"""Read-only helpers for graph visualization and published-graph inspection."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ViewNode:
    id: str
    label: str
    node_type: str


@dataclass(frozen=True)
class ViewEdge:
    id: str
    source: str
    target: str
    edge_type: str


def find_node_id_key(obj: dict[str, Any]) -> str | None:
    return next((key for key in obj if key.endswith("_id")), None)


def node_id(obj: dict[str, Any]) -> str | None:
    key = find_node_id_key(obj)
    return str(obj[key]) if key else None


def node_label(obj: dict[str, Any], fallback: str = "") -> str:
    return str(
        obj.get(
            "name",
            obj.get("code", obj.get("locator", obj.get("version", fallback))),
        )
    )


def build_graph(data: dict[str, Any]) -> dict[str, Any]:
    """Build the graph payload consumed by read-only frontend visualizations."""
    raw_nodes = data.get("nodes", {})
    raw_relationships = data.get("relations", data.get("relationships", []))

    nodes: list[ViewNode] = []
    for node_type, items in raw_nodes.items():
        for obj in items:
            obj_id = node_id(obj)
            if not obj_id:
                continue
            nodes.append(
                ViewNode(
                    id=obj_id,
                    label=node_label(obj, obj_id),
                    node_type=str(node_type),
                )
            )

    edges: list[ViewEdge] = []
    for index, relationship in enumerate(raw_relationships):
        edge_type = str(
            relationship.get("name", relationship.get("type", "REL"))
        )
        from_id = str(relationship.get("from_id", ""))
        to_id = str(relationship.get("to_id", ""))
        if not from_id or not to_id:
            continue
        edges.append(
            ViewEdge(
                id=f"e{index}",
                source=from_id,
                target=to_id,
                edge_type=edge_type,
            )
        )

    return {
        "nodes": [
            {
                "id": item.id,
                "label": item.label,
                "group": item.node_type,
                "title": (
                    f"{item.node_type}: {item.label}"
                    f"<br><code>{item.id}</code>"
                ),
            }
            for item in nodes
        ],
        "edges": [
            {
                "id": item.id,
                "from": item.source,
                "to": item.target,
                "label": item.edge_type,
                "title": item.edge_type,
                "arrows": "to",
            }
            for item in edges
        ],
        "node_types": sorted({item.node_type for item in nodes}),
        "edge_types": sorted({item.edge_type for item in edges}),
    }


def resolve_published_graph_path(store: dict[str, Any]) -> Path:
    """Resolve the immutable export associated with a run, or the latest one."""
    explicit = str(store.get("ontology_path") or "").strip()
    if explicit:
        path = Path(explicit)
    else:
        from backend.services.ontology_export_store import ontology_path_for_pdf

        path = ontology_path_for_pdf(str(store.get("pdf_id") or "latest"))
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"Published graph not found: {path}")
    return path


def load_published_graph(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Published graph must be a JSON object.")
    return payload


def published_graph_status(
    path: Path,
    graph: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = graph if graph is not None else load_published_graph(path)
    metadata = payload.get("metadata") or {}
    return {
        "graph_path": str(path),
        "version": str(
            metadata.get("version") or metadata.get("file_version") or ""
        ),
        "read_only": True,
    }


def published_node_detail(
    graph: dict[str, Any],
    requested_node_id: str,
) -> dict[str, Any]:
    for node_type, items in (graph.get("nodes") or {}).items():
        for attributes in items or []:
            current_id = node_id(attributes)
            if current_id != requested_node_id:
                continue
            relationships = graph.get("relationships") or graph.get("relations") or []
            return {
                "id": current_id,
                "type": str(node_type),
                "label": node_label(attributes, current_id),
                "attributes": dict(attributes),
                "relationships_out": [
                    dict(item)
                    for item in relationships
                    if str(item.get("from_id") or "") == current_id
                ],
                "relationships_in": [
                    dict(item)
                    for item in relationships
                    if str(item.get("to_id") or "") == current_id
                ],
                "read_only": True,
            }
    raise KeyError(requested_node_id)
