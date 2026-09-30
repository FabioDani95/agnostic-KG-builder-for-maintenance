"""Lossless graph editing. Only allowlisted domain operations can change a snapshot."""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.kg_v3.contracts import ContextItem
from backend.kg_v3.ontology import ONTOLOGY_PATH, load_ontology


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def schema() -> dict:
    data = json.loads(ONTOLOGY_PATH.read_text())
    return {
        "root": load_ontology().root,
        "nodes": data["nodes"],
        "relations": [{**r, "added_by_code": r["domain"] == load_ontology().root} for r in data["relations"]],
    }


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class NodeAdd(Strict):
    op: Literal["node.add"]
    temp_id: str = Field(pattern=r"^tmp_node_[a-zA-Z0-9_-]+$")
    node_type: str
    name: str
    properties: dict[str, Any] = Field(default_factory=dict)


class NodeName(Strict):
    op: Literal["node.set_name"]
    node_id: str
    value: str


class NodeProperty(Strict):
    op: Literal["node.set_property"]
    node_id: str
    field: str
    value: Any


class NodeRemoveProperty(Strict):
    op: Literal["node.remove_property"]
    node_id: str
    field: str


class NodeAliases(Strict):
    op: Literal["node.set_aliases"]
    node_id: str
    values: list[str]


class NodeDelete(Strict):
    op: Literal["node.delete"]
    node_id: str


class OccurrenceData(Strict):
    conditions: list[ContextItem] = Field(default_factory=list)
    segment_ids: list[str] = Field(default_factory=list)
    annotation: str = ""


class EdgeAdd(Strict):
    op: Literal["edge.add"]
    temp_id: str = Field(pattern=r"^tmp_edge_[a-zA-Z0-9_-]+$")
    relation_type: str
    source: str = Field(alias="from")
    to: str
    occurrences: list[OccurrenceData] = Field(min_length=1)


class EdgeReplace(Strict):
    op: Literal["edge.replace_endpoints"]
    edge_id: str
    replacement_temp_id: str = Field(pattern=r"^tmp_edge_[a-zA-Z0-9_-]+$")
    relation_type: str
    source: str = Field(alias="from")
    to: str


class EdgeDelete(Strict):
    op: Literal["edge.delete"]
    edge_id: str


class OccurrenceEdit(OccurrenceData):
    op: Literal["occurrence.add", "occurrence.update"]
    edge_id: str
    occurrence_id: str


class OccurrenceDelete(Strict):
    op: Literal["occurrence.delete"]
    edge_id: str
    occurrence_id: str


class OccurrenceDecision(Strict):
    op: Literal["occurrence.confirm", "occurrence.reject"]
    edge_id: str
    occurrence_id: str
    content_hash: str
    reason: str = ""


EditOperation = Annotated[
    NodeAdd
    | NodeName
    | NodeProperty
    | NodeRemoveProperty
    | NodeAliases
    | NodeDelete
    | EdgeAdd
    | EdgeReplace
    | EdgeDelete
    | OccurrenceEdit
    | OccurrenceDelete
    | OccurrenceDecision,
    Field(discriminator="op"),
]


class Preconditions(Strict):
    base_hash: str
    ontology_hash: str
    source_token: str
    source_review_hash: str


class EditInput(Strict):
    preconditions: Preconditions
    operations: list[EditOperation] = Field(max_length=10000)
    draft_generation: int = Field(ge=0)


class Acceptance(Strict):
    decision: Literal["accept_changes"]
    acknowledged_issue_ids: list[str]


class AcceptRevision(EditInput):
    request_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{8,100}$")
    preview_hash: str
    note: str = Field(default="", max_length=10000)
    acceptance: Acceptance


class EditError(ValueError):
    def __init__(self, code: str, target: dict | None = None):
        super().__init__(code)
        self.code, self.target = code, target or {"kind": "graph"}


def read_graph(graph: dict) -> dict:
    if not isinstance(graph, dict) or graph.get("version") not in ("kg-v3-graph-2", "kg-v3-graph-3"):
        raise EditError("UNSUPPORTED_GRAPH")
    if (
        not isinstance(graph, dict)
        or not isinstance(graph.get("nodes"), list)
        or not isinstance(graph.get("edges"), list)
    ):
        raise EditError("UNSUPPORTED_GRAPH")
    for node in graph["nodes"]:
        if (
            not isinstance(node, dict)
            or any(not isinstance(node.get(k), str) for k in ("id", "type", "name"))
            or not isinstance(node.get("properties"), dict)
        ):
            raise EditError("UNSUPPORTED_GRAPH")
    for edge in graph["edges"]:
        if (
            not isinstance(edge, dict)
            or any(not isinstance(edge.get(k), str) for k in ("id", "type", "from", "to"))
            or not isinstance(edge.get("occurrences"), list)
            or any(not isinstance(o, dict) for o in edge["occurrences"])
        ):
            raise EditError("UNSUPPORTED_GRAPH")
    return copy.deepcopy(graph)


def occurrence_hash(edge: dict, occurrence: dict, nodes: list[dict]) -> str:
    return digest(
        {
            "type": edge["type"],
            "from": edge["from"],
            "to": edge["to"],
            "nodes": [
                {k: n.get(k) for k in ("id", "type", "name", "properties", "aliases", "evidence")}
                for n in nodes
                if n["id"] in (edge["from"], edge["to"])
            ],
            "conditions": occurrence.get("conditions", []),
            "evidence": occurrence.get("evidence", []),
            "annotation": occurrence.get("annotation", ""),
        }
    )


def with_occurrence_ids(graph: dict) -> dict:
    graph = read_graph(graph)
    for edge in graph["edges"]:
        for i, occ in enumerate(edge.get("occurrences", [])):
            occ.setdefault("id", "occ_" + digest([edge["id"], i, occ])[:24])
            occ["content_hash"] = occurrence_hash(edge, occ, graph["nodes"])
    return graph


def _invalidate(occ: dict) -> None:
    occ["tier"] = None
    occ.pop("certificate", None)
    occ["review"] = {"status": "pending"}
    occ["trusted"] = False


def _human_occ(data: dict, occurrence_id: str, segments: dict) -> dict:
    ids = data.get("segment_ids", [])
    if any(s not in segments for s in ids):
        raise EditError("SOURCE_SEGMENT_UNAVAILABLE")
    conditions = copy.deepcopy(data.get("conditions", []))
    if any(s not in segments for c in conditions for s in c.get("cite", [])):
        raise EditError("SOURCE_SEGMENT_UNAVAILABLE")
    return {
        "id": occurrence_id,
        "record": "human",
        "conditions": conditions,
        "evidence": [copy.deepcopy(segments[s]) for s in ids],
        "annotation": data.get("annotation", ""),
        "tier": None,
        "trusted": False,
        "review": {"status": "pending"},
        "provenance": {"origin": "human"},
    }


def apply_operations(base: dict, operations: list[EditOperation], ontology: dict, segments: dict) -> dict:
    graph = with_occurrence_ids(base)
    baseline = copy.deepcopy(graph)
    descriptors = {n["name"]: {p["name"]: p for p in n["properties"]} for n in ontology["nodes"]}
    decisions = []
    for operation in operations:
        op = operation.model_dump(mode="json", by_alias=True)
        kind = op["op"]
        if kind.startswith("node."):
            node = next((n for n in graph["nodes"] if n["id"] == op.get("node_id")), None)
            if kind == "node.add":
                if op["node_type"] not in descriptors or op["node_type"] == ontology["root"]:
                    raise EditError("NODE_TYPE")
                if any(n["id"] == op["temp_id"] for n in graph["nodes"]):
                    raise EditError("DUPLICATE_ID")
                fields = descriptors[op["node_type"]]
                if any(f not in fields or f == "name" or f.endswith("_id") for f in op["properties"]):
                    raise EditError("RESERVED_FIELD")
                props = {**op["properties"], "name": op["name"]}
                props.update({f: op["temp_id"] for f in fields if f.endswith("_id")})
                graph["nodes"].append(
                    {
                        "id": op["temp_id"],
                        "type": op["node_type"],
                        "name": op["name"],
                        "properties": props,
                        "evidence": [],
                        "provenance": {"origin": "human"},
                    }
                )
                continue
            if node is None:
                raise EditError("NODE_NOT_FOUND", {"kind": "node", "id": op["node_id"]})
            fields = descriptors.get(node["type"], {})
            if kind == "node.delete":
                if node["type"] == ontology["root"]:
                    raise EditError("ROOT_PROTECTED")
                graph["nodes"].remove(node)
                graph["edges"] = [e for e in graph["edges"] if node["id"] not in (e["from"], e["to"])]
            elif kind == "node.set_name":
                node["name"] = node["properties"]["name"] = op["value"]
            elif kind == "node.set_aliases":
                node["aliases"] = op["values"]
            else:
                field = op["field"]
                if field not in fields or field == "name" or field.endswith("_id"):
                    raise EditError("RESERVED_FIELD")
                if kind == "node.remove_property":
                    if fields[field].get("required"):
                        raise EditError("REQUIRED_FIELD")
                    node["properties"].pop(field, None)
                else:
                    node["properties"][field] = op["value"]
        else:
            edge = next((e for e in graph["edges"] if e["id"] == op.get("edge_id")), None)
            if kind == "edge.add":
                if any(e["id"] == op["temp_id"] for e in graph["edges"]):
                    raise EditError("DUPLICATE_ID")
                graph["edges"].append(
                    {
                        "id": op["temp_id"],
                        "type": op["relation_type"],
                        "from": op["from"],
                        "to": op["to"],
                        "conditions": [],
                        "tier": None,
                        "trusted": False,
                        "provenance": {"origin": "human"},
                        "occurrences": [
                            _human_occ(d, f"{op['temp_id']}_{i}", segments) for i, d in enumerate(op["occurrences"])
                        ],
                    }
                )
                continue
            if edge is None:
                raise EditError("EDGE_NOT_FOUND")
            if edge.get("derived"):
                raise EditError("DERIVED_READ_ONLY")
            if kind == "edge.delete":
                graph["edges"].remove(edge)
            elif kind == "edge.replace_endpoints":
                if any(e["id"] == op["replacement_temp_id"] for e in graph["edges"]):
                    raise EditError("DUPLICATE_ID")
                edge.update(
                    id=op["replacement_temp_id"],
                    type=op["relation_type"],
                    **{"from": op["from"], "to": op["to"]},
                    provenance={"origin": "human", "replaces": op["edge_id"]},
                )
                for occ in edge["occurrences"]:
                    _invalidate(occ)
            else:
                occ = next((o for o in edge["occurrences"] if o["id"] == op["occurrence_id"]), None)
                if kind == "occurrence.add":
                    if occ is not None:
                        raise EditError("DUPLICATE_ID")
                    edge["occurrences"].append(_human_occ(op, op["occurrence_id"], segments))
                elif occ is None:
                    raise EditError("OCCURRENCE_NOT_FOUND")
                elif kind == "occurrence.delete":
                    edge["occurrences"].remove(occ)
                    if not edge["occurrences"]:
                        graph["edges"].remove(edge)
                elif kind == "occurrence.update":
                    replacement = _human_occ(op, occ["id"], segments)
                    if any(
                        occ.get(f, default) != replacement[f]
                        for f, default in [("conditions", []), ("evidence", []), ("annotation", "")]
                    ):
                        replacement["provenance"].update(
                            previous_origin=occ.get("provenance", {}).get("origin", "extraction"),
                            previous_record=occ.get("record"),
                        )
                        occ.update(replacement)
                        occ.pop("certificate", None)
                else:
                    if op["content_hash"] != occurrence_hash(edge, occ, graph["nodes"]):
                        raise EditError("STALE_OCCURRENCE")
                    decisions.append((edge, occ, op))
    # Invalidate only net changes, including all incident diagnostic assertions.
    old_nodes = {n["id"]: n for n in baseline["nodes"]}
    changed = {n["id"] for n in graph["nodes"] if n != old_nodes.get(n["id"])}
    for node in graph["nodes"]:
        if node["id"] in changed:
            node["provenance"] = {
                **node.get("provenance", {}),
                "origin": "human",
                "previous_origin": node.get("provenance", {}).get("origin", "extraction"),
            }
    for edge in graph["edges"]:
        if not edge.get("derived") and changed.intersection((edge["from"], edge["to"])):
            for occ in edge["occurrences"]:
                _invalidate(occ)
    for edge, occ, op in decisions:
        h = occurrence_hash(edge, occ, graph["nodes"])
        if op["content_hash"] != h:
            continue
        occ["review"] = {
            "status": "confirmed" if op["op"] == "occurrence.confirm" else "rejected",
            "author": "human:operator",
            "reason": op["reason"],
            "content_hash": h,
        }
    recompute(graph, ontology)
    return graph


def recompute(graph: dict, ontology: dict) -> None:
    for edge in graph["edges"]:
        if edge.get("derived"):
            continue
        active = []
        for occ in edge.get("occurrences", []):
            occ["content_hash"] = occurrence_hash(edge, occ, graph["nodes"])
            review = occ.get("review", {})
            occ["trusted"] = review.get("status") != "rejected" and (
                occ.get("tier") == "green"
                or (review.get("status") == "confirmed" and review.get("content_hash") == occ["content_hash"])
            )
            if review.get("status") != "rejected":
                active.append(occ)
        edge["trusted"] = any(o["trusted"] for o in active)
        edge["tier"] = next((t for t in ("green", "yellow") if any(o.get("tier") == t for o in active)), None)
        common = copy.deepcopy(active[0].get("conditions", [])) if active else []
        edge["conditions"] = [c for c in common if all(c in o.get("conditions", []) for o in active)]
    roots = [n for n in graph["nodes"] if n["type"] == ontology["root"]]
    old = {(e["type"], e["from"], e["to"]): e for e in graph["edges"] if e.get("derived")}
    diagnostic = [e for e in graph["edges"] if not e.get("derived")]
    derived = []
    if len(roots) == 1:
        for rel in ontology["relations"]:
            if rel["domain"] != ontology["root"]:
                continue
            for node in graph["nodes"]:
                if node["type"] != rel["range"]:
                    continue
                key = (rel["name"], roots[0]["id"], node["id"])
                edge = copy.deepcopy(old.get(key)) or {
                    "id": "v3e_" + digest(key)[:20],
                    "type": key[0],
                    "from": key[1],
                    "to": key[2],
                    "derived": True,
                    "conditions": [],
                    "occurrences": [
                        {"id": "occ_" + digest(key)[:24], "record": "asset", "evidence": node.get("evidence", [])}
                    ],
                }
                incident = [e for e in diagnostic if node["id"] in (e["from"], e["to"])]
                edge["trusted"] = any(e["trusted"] for e in incident)
                edge["tier"] = next((t for t in ("green", "yellow") if any(e["tier"] == t for e in incident)), None)
                derived.append(edge)
    # Preserve existing array order; append genuinely new system links.
    by_key = {(e["type"], e["from"], e["to"]): e for e in derived}
    result = []
    for edge in graph["edges"]:
        if not edge.get("derived"):
            result.append(edge)
        else:
            replacement = by_key.pop((edge["type"], edge["from"], edge["to"]), None)
            if replacement:
                result.append(replacement)
    graph["edges"] = result + list(by_key.values())


def graph_diff(base: dict, graph: dict) -> dict:
    result = {}
    for group in ("nodes", "edges"):
        before = {n["id"]: n for n in base[group]}
        after = {n["id"]: n for n in graph[group]}
        result[group] = {
            "added": [n for n in graph[group] if n["id"] not in before],
            "removed": [n for n in base[group] if n["id"] not in after],
            "updated": [
                {
                    "id": n["id"],
                    "before": before[n["id"]],
                    "after": n,
                    "fields": [f for f in sorted(set(before[n["id"]]) | set(n)) if before[n["id"]].get(f) != n.get(f)],
                }
                for n in graph[group]
                if n["id"] in before and n != before[n["id"]]
            ],
        }
    return result
