"""Graph export for the downstream agent: every edge carries its evidence and certificate.

Red relations stay out of the graph and are listed separately. Yellow relations
are included with ``trusted: false`` so a consumer can choose its view. The
asset node and the relations leaving it are added by the code.
"""

from __future__ import annotations

import hashlib
from typing import Any

from backend.kg_v3.contracts import Tier
from backend.kg_v3.merger import GraphNode
from backend.kg_v3.ontology import OntologySpec, load_ontology
from backend.kg_v3.reader import DocumentText, render_segment
from backend.kg_v3.run import RunResult

EXPORT_VERSION = "kg-v3-graph-2"


def _evidence(doc: DocumentText, segment_ids: list[str]) -> list[dict[str, Any]]:
    items = []
    for segment in doc.segments(segment_ids):
        items.append({
            "segment_id": segment.segment_id, "page": segment.page, "evidence_id": segment.evidence_id,
            "bbox": list(segment.bbox) if segment.bbox else None,
            "text": render_segment(segment).split("] ", 1)[-1],
        })
    return items


def _properties(node: GraphNode, spec: OntologySpec, doc: DocumentText, source_title: str) -> dict[str, Any]:
    """Required ontology properties are filled from the source or marked not_stated."""

    first_page = next((segment.page for segment in doc.segments(node.cites)), None)
    values: dict[str, Any] = {"name": node.name, "description": node.name}
    if node.code:
        values["code"] = node.code
    if node.kind:
        values["action_kind"] = node.kind
    if node.type == "CorrectiveAction":
        values.update(instruction_text=node.name, source_type="technical PDF", source_title=source_title,
                      source_reference=f"page {first_page}" if first_page else "not_stated")
    properties = {}
    for name, required in spec.properties.get(node.type, ()):
        if name.endswith("_id"):
            properties[name] = node.node_id
        elif name in values:
            properties[name] = values[name]
        elif required:
            properties[name] = "Unknown" if name == "severity" else "not_stated"
    return properties


def graph_json(result: RunResult, doc: DocumentText, *, asset: dict[str, Any], source_title: str,
               spec: OntologySpec | None = None) -> dict[str, Any]:
    spec = spec or load_ontology()
    kept = [edge for edge in result.graph.edges if edge.tier is not Tier.RED]
    used = {edge.source for edge in kept} | {edge.target for edge in kept}
    nodes = [node for node in result.graph.nodes.values() if node.node_id in used]
    asset_id = "v3n_asset_" + hashlib.sha256(str(asset.get("name", "")).encode("utf-8")).hexdigest()[:12]
    out_nodes = [{"id": asset_id, "type": spec.root, "name": asset.get("name", ""),
                  "properties": {**asset, f"{spec.root.lower()}_id": asset_id}, "evidence": []}]
    for node in sorted(nodes, key=lambda item: (item.type, item.name)):
        out_nodes.append({
            "id": node.node_id, "type": node.type, "name": node.name, "aliases": node.aliases,
            "stated_in_source": node.stated, "properties": _properties(node, spec, doc, source_title),
            "evidence": _evidence(doc, node.cites[:5]),
        })
    edges = []
    for edge in kept:
        edges.append({
            "id": edge.edge_id, "type": edge.relation_type, "from": edge.source, "to": edge.target,
            "tier": edge.tier.value, "trusted": edge.tier is Tier.GREEN,
            "conditions": [c.model_dump(mode='json') for c in edge.conditions],
            "occurrences": [{
                "record": item.record_key,
                "tier": item.tier.value,
                "conditions": [c.model_dump(mode='json') for c in item.conditions],
                "certificate": item.certificate.model_dump(mode="json"),
                "evidence": _evidence(doc, item.certificate.segment_ids),
            } for item in edge.assertions],
        })
    by_type = {node.node_id: node.type for node in nodes}
    for relation in spec.root_relations:
        for node in nodes:
            if by_type[node.node_id] != relation.range:
                continue
            best = min((edge.tier for edge in kept if node.node_id in (edge.source, edge.target)),
                       key=[Tier.GREEN, Tier.YELLOW].index)
            edges.append({
                "id": "v3e_" + hashlib.sha256(f"{relation.name}|{node.node_id}".encode()).hexdigest()[:20],
                "type": relation.name, "from": asset_id, "to": node.node_id, "tier": best.value,
                "trusted": best is Tier.GREEN, "conditions": [], "derived": True,
                "occurrences": [{"record": "asset", "evidence": _evidence(doc, node.cites[:3])}],
            })
    red = [{
        "relation": item.assertion.relation_type, "source": item.assertion.source_key,
        "target": item.assertion.target_key, "certificate": item.assertion.certificate.model_dump(mode="json"),
    } for item in result.relations if item.assertion.tier is Tier.RED]
    return {
        "version": EXPORT_VERSION, "status": result.status, "source_title": source_title,
        "nodes": out_nodes, "edges": edges, "excluded_relations": red, "report": result.report,
    }
