"""Graph export for agents, the interface and the scorers.

The file keeps the ``kg-v3-graph-2`` shape the interface and the editor read, and adds optional
fields: a section on every piece of evidence, a confidence and an origin on every occurrence,
real descriptions and declared placeholders on nodes. Facts rejected for their meaning are listed
in ``excluded_relations`` with the reason. The asset node and its links are added by the code and
marked ``derived``.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from backend.kg_v3.contracts import ContextItem
from backend.kg_v3.ontology import OntologySpec, load_ontology
from backend.kg_v3.reader import DocumentText, render_segment
from backend.kg_v4 import PIPELINE_VERSION
from backend.kg_v4.enrich import real_description
from backend.kg_v4.model import Edge, Evidence, Graph, Node
from backend.kg_v4.names import display_name

EXPORT_VERSION = "kg-v3-graph-2"
TIER = {"supported": "green", "unchecked": "yellow", "unclear": "yellow"}
_TIER_RANK = {"green": 0, "yellow": 1}
PLACEHOLDERS = {"severity": "Unknown"}


def reference(evidence: Evidence) -> str:
    return f"p. {evidence.page}" + (f", {evidence.section}" if evidence.section else "")


def evidence_items(doc: DocumentText, evidence: Evidence) -> list[dict[str, Any]]:
    """Evidence as the interface reads it; a fact known by page points to where that page starts."""

    segment_ids = evidence.segment_ids
    anchor = evidence.anchor
    if not segment_ids:
        first = (doc.pages.get(evidence.page) or [None])[0]
        segment_ids, anchor = ([first.segment_id] if first else []), "page"
    items = []
    for segment in doc.segments(segment_ids):
        items.append({
            "segment_id": segment.segment_id, "page": segment.page, "evidence_id": segment.evidence_id,
            "bbox": list(segment.bbox) if segment.bbox else None,
            "text": render_segment(segment).split("] ", 1)[-1],
            "section": evidence.section, "anchor": anchor,
        })
    return items


def instruction_from_name(node: Node, graph: Graph) -> str:
    """An action the manual gives in one phrase: that phrase with the conditions printed with it."""

    conditions = {(item.kind, item.text) for edge in graph.in_edges(node.node_id)
                  for fact in edge.facts for item in fact.conditions}
    order = {"prerequisite": 0, "if": 1, "order": 2, "warning": 3, "expected": 4}
    notes = [f"{kind}: {text}" for kind, text in sorted(conditions, key=lambda item: (order.get(item[0], 9), item[1]))]
    return node.name + (" (" + "; ".join(notes) + ")" if notes else "")


def node_properties(node: Node, graph: Graph, spec: OntologySpec,
                    source_title: str) -> tuple[dict[str, Any], str, list[str], list[str]]:
    """Ontology properties, the source of the description, the placeholders that remain and the
    properties filled from the name because the manual says nothing more."""

    fallbacks: list[str] = []
    # A description the manual does not support is left as the name and counted as missing.
    source = "manual" if real_description(node) else "name"
    name = display_name(node.name)
    values: dict[str, Any] = {**node.properties, "name": name,
                              "description": node.description if source == "manual" else name}
    if node.code:
        values["code"] = node.code
    if node.kind:
        values["action_kind"] = node.kind
    if node.evidence:
        values["source_reference"] = "; ".join(dict.fromkeys(reference(item) for item in node.evidence[:3]))
    if node.type == "CorrectiveAction":
        values.setdefault("source_type", "technical PDF")
        values.setdefault("source_title", source_title)
        if not values.get("instruction_text"):
            values["instruction_text"] = instruction_from_name(node, graph)
            fallbacks.append("instruction_text")
    properties: dict[str, Any] = {}
    placeholders: list[str] = []
    for name, required in spec.properties.get(node.type, ()):
        if name.endswith("_id"):
            properties[name] = node.node_id
        elif values.get(name) not in (None, ""):
            properties[name] = values[name]
        elif required:
            properties[name] = PLACEHOLDERS.get(name, "not_stated")
            placeholders.append(name)
    return properties, source, placeholders, fallbacks


def _conditions(items: list[ContextItem]) -> list[dict[str, Any]]:
    return [item.model_dump(mode="json") for item in items]


def _edge(edge: Edge, doc: DocumentText) -> dict[str, Any]:
    occurrences = []
    for fact in edge.facts:
        tier = TIER[fact.verdict]
        occurrences.append({
            "assertion_id": fact.fact_id, "record": fact.record, "tier": tier, "trusted": tier == "green",
            "confidence": fact.confidence, "verdict": fact.verdict, "origin": fact.origin,
            "anchor": fact.evidence.anchor, "note": fact.reason,
            "conditions": _conditions(fact.conditions), "evidence": evidence_items(doc, fact.evidence),
        })
    tier = min((item["tier"] for item in occurrences), key=_TIER_RANK.__getitem__)
    shared = set.intersection(*(set(fact.conditions) for fact in edge.facts)) if edge.facts else set()
    return {"id": edge.edge_id, "type": edge.relation, "from": edge.source, "to": edge.target, "tier": tier,
            "trusted": tier == "green",
            "confidence": min((item["confidence"] for item in occurrences), key=["high", "medium", "low"].index),
            "conditions": _conditions(sorted(shared)), "occurrences": occurrences}


def with_survey(asset: dict[str, Any], read: dict[str, str]) -> dict[str, Any]:
    """The machine identity given by the operator, completed with what the manual says of it."""

    merged = dict(asset)
    empty = {"", "not_stated", None}
    for key, source in (("description", "description"), ("brand", "brand"), ("model", "model"), ("asset_type", "type")):
        value = read.get(source)
        if value and (merged.get(key) in empty or (key == "description" and merged.get(key) == merged.get("name"))):
            merged[key] = value
    return merged


def graph_json(graph: Graph, doc: DocumentText, *, asset: dict[str, Any], source_title: str, status: str,
               report: dict[str, Any], spec: OntologySpec | None = None,
               survey_asset: dict[str, str] | None = None) -> dict[str, Any]:
    spec = spec or load_ontology(full=True)
    asset_id = "kg4n_asset_" + hashlib.sha256(str(asset.get("name", "")).encode("utf-8")).hexdigest()[:12]
    asset = with_survey(asset, survey_asset or {})
    nodes = [{"id": asset_id, "type": spec.root, "name": asset.get("name", ""), "aliases": [],
              "properties": {**asset, f"{spec.root.lower()}_id": asset_id}, "evidence": []}]
    for node in sorted(graph.nodes.values(), key=lambda item: (item.type, item.name.casefold(), item.node_id)):
        properties, source, placeholders, fallbacks = node_properties(node, graph, spec, source_title)
        evidence = [item for part in node.evidence[:5] for item in evidence_items(doc, part)]
        nodes.append({
            "id": node.node_id, "type": node.type, "name": display_name(node.name),
            "aliases": [alias for alias in node.aliases if alias.casefold() != node.name.casefold()],
            "stated_in_source": node.stated, "properties": properties, "description_source": source,
            "inferred_properties": node.inferred, "placeholder_properties": placeholders,
            "name_derived_properties": fallbacks,
            "evidence": list({item["segment_id"]: item for item in evidence}.values()),
        })
    edges = [_edge(edge, doc) for edge in graph.edges]
    best: dict[str, str] = {}
    for edge in edges:
        for end in (edge["from"], edge["to"]):
            best[end] = min(best.get(end, "yellow"), edge["tier"], key=_TIER_RANK.__getitem__)
    for relation in spec.root_relations:
        for node in graph.nodes.values():
            if node.type != relation.range:
                continue
            tier = best.get(node.node_id, "yellow")
            evidence = [item for part in node.evidence[:3] for item in evidence_items(doc, part)]
            edges.append({
                "id": "kg4e_" + hashlib.sha256(f"{relation.name}|{node.node_id}".encode()).hexdigest()[:20],
                "type": relation.name, "from": asset_id, "to": node.node_id, "tier": tier, "trusted": tier == "green",
                "conditions": [], "derived": True, "occurrences": [{"record": "asset", "evidence": evidence}]})
    excluded = [{
        "relation": item["relation"], "source": item["source"], "target": item["target"], "reason": item["reason"],
        "origin": item.get("origin", "extract"), "record": item.get("record", ""),
        "certificate": {"notes": [item["reason"]], "verifier_verdict": "not_supported", "witnesses": [],
                        "segment_ids": item["evidence"].get("segment_ids", []), "page": item["evidence"].get("page"),
                        "section": item["evidence"].get("section", "")},
    } for item in graph.rejected]
    return {"version": EXPORT_VERSION, "pipeline": PIPELINE_VERSION, "status": status, "source_title": source_title,
            "nodes": nodes, "edges": edges, "excluded_relations": excluded, "report": report}


def graph_counts(document: dict[str, Any]) -> dict[str, Any]:
    edges = [edge for edge in document["edges"] if not edge.get("derived")]
    return {"nodes": len(document["nodes"]) - 1,
            "nodes_by_type": dict(Counter(node["type"] for node in document["nodes"][1:])),
            "edges": len(edges), "edges_by_tier": dict(Counter(edge["tier"] for edge in edges)),
            "edges_by_type": dict(Counter(edge["type"] for edge in edges))}
