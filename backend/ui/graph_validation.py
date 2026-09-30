"""Structural and documentary diagnostics, with pre-existing defects distinguished."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher

from backend.ui.graph_document import digest


def value_state(properties: dict, field: str) -> str:
    if field not in properties:
        return "missing"
    value = properties[field]
    if value is None or value == "" or value == [] or (isinstance(value, str) and not value.strip()):
        return "empty"
    if isinstance(value, str) and value.lower() in ("not_stated", "unknown"):
        return "not_stated"
    return "filled"


def validate(graph: dict, base: dict, ontology: dict) -> list[dict]:
    issues = []
    nodes = {n["id"]: n for n in graph["nodes"]}
    old_nodes = {n["id"]: n for n in base["nodes"]}
    old_edges = {e["id"]: e for e in base["edges"]}
    specs = {n["name"]: n for n in ontology["nodes"]}
    relations = {r["name"]: r for r in ontology["relations"]}

    def issue(code, kind="graph", id=None, field=None, error=False, introduced=True, **params):
        target = {"kind": kind}
        if id is not None:
            target["id"] = id
        if field is not None:
            target["field"] = field
        issues.append(
            {
                "id": "issue_" + digest([code, target, params])[:24],
                "code": code,
                "severity": "error" if error else "warning",
                "target": target,
                "introduced": introduced,
                "message_key": code,
                "message_params": params,
            }
        )

    for group in ("nodes", "edges"):
        for id, count in Counter(n["id"] for n in graph[group]).items():
            if count > 1 or not id:
                issue("DUPLICATE_ID", "node" if group == "nodes" else "edge", id, error=True)
    if sum(n["type"] == ontology["root"] for n in graph["nodes"]) != 1:
        issue("ROOT_COUNT", error=True)

    def active(edge):
        return any(o.get("review", {}).get("status") != "rejected" for o in edge.get("occurrences", []))

    diagnostic = [e for e in graph["edges"] if not e.get("derived") and active(e)]
    adjacency = defaultdict(list)
    outgoing_by_node = defaultdict(list)
    old_outgoing = defaultdict(list)
    for edge in diagnostic:
        adjacency[edge["from"]].append(edge)
        adjacency[edge["to"]].append(edge)
        outgoing_by_node[edge["from"]].append(edge)
    for edge in base["edges"]:
        if not edge.get("derived") and active(edge):
            old_outgoing[edge["from"]].append(edge)

    def compatible_path(node_id, outgoing):
        causes = [e for e in outgoing[node_id] if e["type"] in ("MAY_INDICATE", "INDICATES")]
        return any(
            e["type"] == "RESOLVED_BY"
            and any(
                not a.get("conditions") or not b.get("conditions") or a["conditions"] == b["conditions"]
                for a in c.get("occurrences", [])
                if a.get("review", {}).get("status") != "rejected"
                for b in e.get("occurrences", [])
                if b.get("review", {}).get("status") != "rejected"
            )
            for c in causes
            for e in outgoing[c["to"]]
        )

    old_incident = {
        endpoint for e in base["edges"] if not e.get("derived") and active(e) for endpoint in (e["from"], e["to"])
    }
    names = defaultdict(list)
    for node in graph["nodes"]:
        normalized = re.sub(r"[^\w]+", " ", node["name"].casefold()).strip()
        bucket = names[(node["type"], normalized[:3])]
        for other, other_name in bucket:
            if SequenceMatcher(None, normalized, other_name).ratio() >= 0.9:
                issue(
                    "SIMILAR_NAME",
                    "node",
                    node["id"],
                    introduced=node != old_nodes.get(node["id"]),
                    other_id=other["id"],
                )
        bucket.append((node, normalized))
    triples = Counter((e["type"], e["from"], e["to"]) for e in graph["edges"])
    for node in graph["nodes"]:
        old = old_nodes.get(node["id"])
        spec = specs.get(node["type"])
        if spec is None:
            issue("NODE_TYPE", "node", node["id"], error=True)
            continue
        if not isinstance(node.get("name"), str) or not node["name"].strip():
            issue("REQUIRED_FIELD", "node", node["id"], "name", error=True)
        props = node.get("properties", {})
        for field in spec["properties"]:
            key = field["name"]
            state = value_state(props, key)
            introduced = (
                old is None
                or props.get(key) != old.get("properties", {}).get(key)
                or (key in props) != (key in old.get("properties", {}))
            )
            if key.endswith("_id") and props.get(key) != node["id"]:
                issue("CANONICAL_ID", "node", node["id"], key, error=True, introduced=introduced)
            if key == "name" and key in props and props[key] != node["name"]:
                issue("CANONICAL_NAME", "node", node["id"], key, error=True, introduced=introduced)
            if field.get("required") and state != "filled":
                # Export uses explicit unknowns; they remain visible warnings, never completeness.
                issue(
                    "REQUIRED_FIELD" if state != "not_stated" else "NOT_STATED",
                    "node",
                    node["id"],
                    key,
                    error=introduced and state != "not_stated",
                    introduced=introduced,
                )
            if key in props and props[key] is not None:
                value = props[key]
                ok = {
                    "string": isinstance(value, str),
                    "number": isinstance(value, (int, float)) and not isinstance(value, bool),
                    "integer": isinstance(value, int) and not isinstance(value, bool),
                    "boolean": isinstance(value, bool),
                    "array": isinstance(value, list),
                }.get(field.get("type", "string"), False)
                if field.get("type") == "array" and isinstance(value, list):
                    item_type = field.get("items", "string")
                    if isinstance(item_type, dict):
                        item_type = item_type.get("type")
                    ok = all(isinstance(v, str) for v in value) if item_type == "string" else ok
                if not ok:
                    issue("VALUE_TYPE", "node", node["id"], key, error=True, introduced=introduced)
        incident = adjacency[node["id"]]
        if node["type"] != ontology["root"] and not incident:
            issue("ISOLATED_NODE", "node", node["id"], introduced=old is None or node["id"] in old_incident)
        outgoing = outgoing_by_node[node["id"]]
        if node["type"] == "FailureMode" and not any(e["type"] == "RESOLVED_BY" for e in outgoing):
            issue(
                "CAUSE_WITHOUT_ACTION",
                "node",
                node["id"],
                introduced=old is None or any(e["type"] == "RESOLVED_BY" for e in old_outgoing[node["id"]]),
            )
        if node["type"] in ("Symptom", "ErrorCode"):
            causes = [e for e in outgoing if e["type"] in ("MAY_INDICATE", "INDICATES")]
            if not causes:
                issue(
                    "PROBLEM_WITHOUT_CAUSE",
                    "node",
                    node["id"],
                    introduced=old is None
                    or any(e["type"] in ("MAY_INDICATE", "INDICATES") for e in old_outgoing[node["id"]]),
                )
            elif not compatible_path(node["id"], outgoing_by_node):
                issue(
                    "NO_COMPATIBLE_ACTION_PATH",
                    "node",
                    node["id"],
                    introduced=old is None or compatible_path(node["id"], old_outgoing),
                )
    for edge in graph["edges"]:
        old = old_edges.get(edge["id"])
        spec = relations.get(edge["type"])
        if edge["from"] not in nodes or edge["to"] not in nodes:
            issue("ORPHAN_EDGE", "edge", edge["id"], error=True)
        elif spec is None or (nodes[edge["from"]]["type"], nodes[edge["to"]]["type"]) != (
            spec["domain"],
            spec["range"],
        ):
            issue("ENDPOINT_TYPE", "edge", edge["id"], error=True)
        elif spec["domain"] == ontology["root"] and not edge.get("derived"):
            issue("DERIVED_READ_ONLY", "edge", edge["id"], error=True)
        if triples[(edge["type"], edge["from"], edge["to"])] > 1:
            issue("DUPLICATE_EDGE", "edge", edge["id"], error=True)
        if edge.get("derived"):
            continue
        if not edge.get("occurrences"):
            issue("NO_OCCURRENCES", "edge", edge["id"], error=True)
        ids = Counter(o["id"] for o in edge.get("occurrences", []))
        for occ in edge.get("occurrences", []):
            if ids[occ["id"]] > 1:
                issue("DUPLICATE_ID", "edge", edge["id"], error=True, occurrence_id=occ["id"])
            if occ.get("review", {}).get("status") == "rejected":
                continue
            if not occ.get("trusted"):
                issue("UNVERIFIED_CONTENT", "edge", edge["id"], introduced=old != edge, occurrence_id=occ["id"])
            if not occ.get("evidence"):
                issue("NO_EVIDENCE", "edge", edge["id"], introduced=old != edge, occurrence_id=occ["id"])
    return issues


def metrics(graph: dict, ontology: dict) -> dict:
    """Separate documentary completeness, links and provenance; never a correctness score."""
    specs = {n["name"]: n for n in ontology["nodes"]}
    fields = {group: Counter(total=0, filled=0, missing=0, empty=0, not_stated=0) for group in ("required", "optional")}
    for node in graph["nodes"]:
        for field in specs.get(node["type"], {}).get("properties", []):
            group = fields["required" if field.get("required") else "optional"]
            group["total"] += 1
            group[value_state(node.get("properties", {}), field["name"])] += 1
    occurrences = [o for e in graph["edges"] if not e.get("derived") for o in e.get("occurrences", [])]
    return {
        "fields": fields,
        "diagnostic_edges": sum(not e.get("derived") for e in graph["edges"]),
        "system_edges": sum(bool(e.get("derived")) for e in graph["edges"]),
        "occurrences_with_evidence": sum(bool(o.get("evidence")) for o in occurrences),
        "human_without_evidence": sum(o.get("record") == "human" and not o.get("evidence") for o in occurrences),
        "pending_occurrences": sum(
            not o.get("trusted") and o.get("review", {}).get("status") != "rejected" for o in occurrences
        ),
    }
