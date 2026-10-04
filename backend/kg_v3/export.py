"""Graph export for the downstream agent: every edge carries its evidence and certificate.

Red relations stay out of the graph and are listed separately. Yellow relations
are included with ``trusted: false`` so a consumer can choose its view. The
asset node and the relations leaving it are added by the code.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from backend.kg_v3.contracts import Tier
from backend.kg_v3.merger import GraphEdge, GraphNode, MergedGraph
from backend.kg_v3.ontology import OntologySpec, load_ontology
from backend.kg_v3.quality_contracts import QUALITY_VERSION
from backend.kg_v3.reader import DocumentText, render_segment
from backend.kg_v3.run import RunResult
from backend.kg_v3.run_state import atomic_bytes, atomic_json, digest, file_hash
from backend.kg_v3.source_index import SourceIndex

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


def _projection(result: RunResult, doc: DocumentText) -> MergedGraph:
    """The quality graph as the historical format can show it: public greens, non-red yellows,
    textual evidence only. Nothing is cited that the historical format cannot locate."""
    index = SourceIndex.model_validate(result.quality_bundle["source_index"])
    public = set(result.quality_bundle.get("validation", {}).get("public_assertion_ids", []))
    edges = []
    for edge in result.graph.edges:
        assertions = [a for a in edge.assertions if a.tier is not Tier.RED and representable(a, index)
                      and (a.tier is not Tier.GREEN or a.assertion_id in public)]
        if assertions:
            edges.append(edge.model_copy(update={"assertions": assertions}))
    nodes = {}
    for key, node in result.graph.nodes.items():
        segments = {index.evidence[r].segment_id for r in node.cites if r in index.evidence}
        cites = sorted((segments - {""}) | {r for r in node.cites if doc.segment(r)})
        nodes[key] = node.model_copy(update={"cites": cites})
    return result.graph.model_copy(update={"nodes": nodes, "edges": edges})


def graph_json(result: RunResult, doc: DocumentText, *, asset: dict[str, Any], source_title: str,
               spec: OntologySpec | None = None) -> dict[str, Any]:
    spec = spec or load_ontology()
    if getattr(result, "quality_bundle", None):  # a quality run; legacy results have none
        result = result.model_copy(update={"graph": _projection(result, doc)})
    kept = [edge for edge in result.graph.edges if edge.tier is not Tier.RED]
    used = {edge.source for edge in kept} | {edge.target for edge in kept}
    nodes = [node for node in result.graph.nodes.values() if node.node_id in used]
    asset_id = "v3n_asset_" + hashlib.sha256(str(asset.get("name", "")).encode("utf-8")).hexdigest()[:12]
    out_nodes = [{"id": asset_id, "type": spec.root, "name": asset.get("name", ""),
                  "properties": {**asset, f"{spec.root.lower()}_id": asset_id}, "evidence": []}]
    for node in sorted(nodes, key=lambda item: (item.type, item.name)):
        out_nodes.append({
            "id": node.node_id, "type": node.type, "name": node.name, "aliases": node.aliases,
            "stated_in_source": node.stated, 'branch_id': node.branch_id,
            'concept_id': node.concept_id, 'instance_id': node.instance_id,
            'denotation_status': node.denotation_status, "properties": _properties(node, spec, doc, source_title),
            "evidence": _evidence(doc, node.cites[:5]),
        })
    edges = []
    for edge in kept:
        edges.append({
            "id": edge.edge_id, "type": edge.relation_type, "from": edge.source, "to": edge.target,
            "tier": edge.tier.value, "trusted": edge.tier is Tier.GREEN,
            "conditions": [c.model_dump(mode='json') for c in edge.conditions],
            "occurrences": [{
                'assertion_id': item.assertion_id, 'branch_id': item.branch_id,
                'entry_id': item.entry_id, 'fact_fingerprint': item.fact_fingerprint,
                'epistemic_status': item.certificate.epistemic_status,
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


def representable(assertion, index) -> bool:
    """Every piece of evidence is a located text span (no image-only fact in the historical format)."""
    refs = [index.evidence.get(r) for r in assertion.certificate.evidence_ref_ids]
    return bool(refs) and all(ref is not None and ref.segment_id and ref.kind != "VISUAL_REGION" for ref in refs)


def _projection_status(public: set[str], projected: set[str]) -> tuple[str, str]:
    status = "EMPTY" if not projected else "FULL" if public == projected else "PARTIAL"
    reason = "NO_PUBLIC_FACTS" if not public else "NO_REPRESENTABLE_FACTS" if not projected else ""
    return status, reason


def write_exports(out, result, doc, *, asset, source_title):
    """Projection (graph.json) and quality sidecar from one result, with acyclic hashes.

    graph.json names the sidecar and the input manifest; the sidecar records the projection's hash;
    artifact_index.json records every file. No file holds a hash of itself.
    """
    projection = graph_json(result, doc, asset=asset, source_title=source_title)
    bundle = getattr(result, "quality_bundle", None)
    if bundle:
        projection = _bind_projection(projection, result, bundle)
    projection["report"] = result.report
    atomic_json(out / "graph.json", projection)
    if bundle:
        _write_sidecar(out, result, bundle, projection)
    atomic_json(out / "report.json", result.report)
    names = ("input_manifest.json", "graph.json", "ingestion_quality.json", "report.json", "source_index.json",
             "coverage.json", "review_requests.json", "quality_review.md")
    artifacts = [out / name for name in names if (out / name).exists()]
    artifacts += sorted((out / "crops").glob("*.png")) if (out / "crops").exists() else []
    atomic_json(out / "artifact_index.json", {"contract_version": QUALITY_VERSION,
                                              "artifacts": {str(p.relative_to(out)): file_hash(p) for p in artifacts}})
    return projection


def _bind_projection(projection, result, bundle):
    index = SourceIndex.model_validate(bundle["source_index"])
    public = set(bundle.get("validation", {}).get("public_assertion_ids", []))
    enabled = bundle.get("input_manifest", {}).get("config", {}).get("quality", {}).get("export_projection", True)
    if not enabled:
        projection["edges"] = []
        projection["nodes"] = projection["nodes"][:1]
    projected = {a.assertion_id for e in result.graph.edges for a in e.assertions
                 if enabled and a.assertion_id in public and representable(a, index)}
    status, reason = _projection_status(public, projected)
    projection["ingestion_quality"] = {"contract_version": QUALITY_VERSION, "file": "ingestion_quality.json",
                                       "input_manifest_sha256": digest(bundle["input_manifest"])}
    projection["projection_status"] = status
    if status == "EMPTY" and projection["status"] == "approved":
        projection["status"] = "incomplete"
    # Historical conditions cite their real parent segments, never region IDs.
    for edge in projection["edges"]:
        for occurrence in [edge, *edge.get("occurrences", [])]:
            for condition in occurrence.get("conditions", []):
                condition["cite"] = sorted({index.evidence[r].segment_id for r in condition.get("cite", [])
                                            if r in index.evidence and index.evidence[r].segment_id})
    missing = [{"assertion_id": a, "reason": "VISUAL_EVIDENCE_REQUIRES_QUALITY_READER"} for a in sorted(public - projected)]
    result.report.update(projection_status=status, projection_reason=reason, canonical_public_assertions=len(public),
                         projected_public_assertions=len(projected), not_projected=missing)
    return projection


def _write_sidecar(out, result, bundle, projection):
    index = SourceIndex.model_validate(bundle["source_index"])
    public = set(bundle.get("validation", {}).get("public_assertion_ids", []))
    rich = {"contract_version": QUALITY_VERSION, "document_identity": index.identity.model_dump(mode="json"),
            "input_manifest_sha256": digest(bundle["input_manifest"]),
            "projection_sha256": file_hash(out / "graph.json"),
            "nodes": [n.model_dump(mode="json") for n in sorted(result.graph.nodes.values(), key=lambda n: n.node_id)],
            "edges": [{**e.model_dump(mode="json"), "tier": e.tier.value,
                       "public_assertion_ids": sorted(a.assertion_id for a in e.assertions if a.assertion_id in public)}
                      for e in result.graph.edges],
            "concepts": result.graph.concepts, "instances": result.graph.instances,
            "merge_lineage": result.graph.merge_lineage,
            "source_index": index.model_dump(mode="json"), "coverage": bundle["coverage"],
            "public_assertion_ids": sorted(public), "not_projected": result.report["not_projected"],
            "projection_status": projection["projection_status"],
            "projection_reason": result.report["projection_reason"],
            "candidates": [r.model_dump(mode="json") for r in result.relations],
            "validation": bundle["validation"], "canonical_workflow_status": result.status}
    atomic_json(out / "ingestion_quality.json", rich)
    notes = ["# Quality review", "", "Observed inventory only; extraction quality has not been measured.", ""]
    for region in index.regions.values():
        notes.append(f"Page {region.page}: {region.region_id}, bbox={region.bbox}, "
                     f"render={region.render_fingerprint}, crop={region.image_path}")
    for request in bundle.get("coverage", {}).get("requests", []):
        notes.append(f"{request['request_id']}: {request['trigger']} {request['status']} {request['result_reason']}")
    atomic_bytes(out / "quality_review.md", "\n".join(notes).encode())


def load_quality(out):
    """Read-only loader. A projection edited after the run (STALE) never inherits sidecar certificates."""
    out = Path(out)
    projection = json.loads((out / "graph.json").read_text())
    sidecar = out / "ingestion_quality.json"
    if not sidecar.exists():
        return {"binding_status": "LEGACY_UNVERIFIED", "graph": projection, "scope_status": "LEGACY_UNKNOWN",
                "epistemic_status": "LEGACY_UNCLASSIFIED", "public_assertion_ids": []}
    rich = json.loads(sidecar.read_text())
    hashes = json.loads((out / "artifact_index.json").read_text())["artifacts"]
    if rich.get("contract_version") != QUALITY_VERSION:
        raise ValueError("unsupported ingestion quality version")
    if hashes.get("ingestion_quality.json") != file_hash(sidecar):
        raise ValueError("quality sidecar checksum mismatch")
    stale = {"binding_status": "STALE", "graph": projection, "public_assertion_ids": []}
    if rich.get("projection_sha256") != file_hash(out / "graph.json"):
        return stale
    if hashes.get("input_manifest.json") != file_hash(out / "input_manifest.json"):
        raise ValueError("manifest checksum mismatch")
    manifest = json.loads((out / "input_manifest.json").read_text())
    if rich["input_manifest_sha256"] != digest(manifest):
        raise ValueError("quality manifest binding mismatch")
    for name, sha in hashes.items():
        if name.startswith("crops/") and file_hash(out / name) != sha:
            raise ValueError("source image crop checksum mismatch")
    binding = projection.get("ingestion_quality", {})
    if binding.get("file") != "ingestion_quality.json" or binding.get("input_manifest_sha256") != digest(manifest):
        return stale
    SourceIndex.model_validate(rich["source_index"])
    return {"binding_status": "VERIFIED", "graph": projection, "quality": rich,
            "public_assertion_ids": rich["public_assertion_ids"]}


def load_certified_graph(out):
    """Only validated public occurrences, for quality diagnostic queries."""
    loaded = load_quality(out)
    if loaded["binding_status"] != "VERIFIED":
        raise ValueError("certified quality queries require a verified current sidecar")
    rich = loaded["quality"]
    public = set(rich["public_assertion_ids"])
    edges = []
    for raw in rich["edges"]:
        edge = GraphEdge.model_validate(raw)
        accepted = [a for a in edge.assertions if a.assertion_id in public]
        if accepted:
            edges.append(edge.model_copy(update={"assertions": accepted}))
    used = {e.source for e in edges} | {e.target for e in edges}
    nodes = {n["node_id"]: GraphNode.model_validate(n) for n in rich["nodes"] if n["node_id"] in used}
    return MergedGraph(nodes=nodes, edges=edges), SourceIndex.model_validate(rich["source_index"])
