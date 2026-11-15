"""A connected-pipeline graph as the historical branch scorer reads graphs.

The scorer (scripts/kg_v3_evaluate.py) compares gold claims "problem -> cause" and
"cause -> action" with trusted edges, and its judge sees node names. This pipeline stores
knowledge in other places too, so it is shown to the scorer in one of two views:

``names``
    Exactly what the graph links, by node name. A remedy the manual gives without a cause
    (ADDRESSED_BY, CLEARED_BY) is shown the old way: an unnamed cause, marked as not written
    in the manual, between the problem and the action of the same source record.

``full``
    As ``names``, plus what a consumer of the graph reads: an action is shown with its
    instruction (the manual's steps and values), and a check that is linked only to the part
    it tests (ACTS_ON, no problem, no cause) is shown as a test of that part, one per source
    record. This is how an agent reaches a component test: from the component.

Neither view adds a fact to the graph; both only change how its facts are put to the judge.
Results must say which view was used.
"""

from __future__ import annotations

from typing import Any

from backend.kg_v4.names import canonical

DIRECT = {"ADDRESSED_BY": "MAY_INDICATE", "CLEARED_BY": "INDICATES"}
SCORED = {"MAY_INDICATE", "INDICATES", "RESOLVED_BY"}
REMEDY_LINKS = {"RESOLVED_BY", "ADDRESSED_BY", "CLEARED_BY"}
VIEWS = ("names", "full")


def _action_text(node: dict[str, Any]) -> str:
    """Name and instruction of an action, when the instruction says more than the name."""

    instruction = str(node.get("properties", {}).get("instruction_text") or "")
    if (not instruction or "instruction_text" in node.get("name_derived_properties", [])
            or canonical(instruction) == canonical(node["name"])):
        return node["name"]
    return f"{node['name']} ({instruction})"


def _base(occurrence: dict[str, Any], edge: dict[str, Any]) -> dict[str, Any]:
    return {"conditions": occurrence.get("conditions", edge.get("conditions", [])),
            "record": occurrence.get("record", ""),
            "segments": {item["segment_id"] for item in occurrence.get("evidence", [])},
            "trusted": occurrence.get("tier", edge.get("tier")) == "green"}


def _unnamed(edges: list[dict[str, Any]], relation: str, source: str, source_name: str, source_stated: bool,
             key: str, base: dict[str, Any]) -> tuple[str, str]:
    """An unnamed cause between a problem and its actions; added once per problem and record."""

    label = f"Unspecified cause of {source_name}"
    if not any(item["type"] == relation and item["source"] == source and item["target"] == key for item in edges):
        edges.append({**base, "type": relation, "source": source, "target": key, "source_name": source_name,
                      "target_name": label, "source_stated": source_stated, "target_stated": False, "conditions": []})
    return key, label


def historical_edges(document: dict[str, Any], view: str = "names") -> list[dict[str, Any]]:
    if view not in VIEWS:
        raise ValueError(f"unknown view {view!r}; use one of {VIEWS}")
    nodes = {node["id"]: node for node in document["nodes"]}
    names = {key: node["name"] for key, node in nodes.items()}
    if view == "full":
        names.update({key: _action_text(node) for key, node in nodes.items() if node["type"] == "CorrectiveAction"})
    stated = {key: node.get("stated_in_source", True) for key, node in nodes.items()}
    edges: list[dict[str, Any]] = []
    for edge in document["edges"]:
        if edge.get("derived") or edge["type"] not in SCORED | set(DIRECT):
            continue
        for occurrence in edge["occurrences"]:
            base = _base(occurrence, edge)
            if edge["type"] in SCORED:
                edges.append({**base, "type": edge["type"], "source": edge["from"], "target": edge["to"],
                              "source_name": names[edge["from"]], "target_name": names[edge["to"]],
                              "source_stated": stated[edge["from"]], "target_stated": stated[edge["to"]]})
                continue
            key, label = _unnamed(edges, DIRECT[edge["type"]], edge["from"], names[edge["from"]],
                                  stated[edge["from"]], f"unnamed:{edge['from']}:{base['record']}", base)
            edges.append({**base, "type": "RESOLVED_BY", "source": key, "target": edge["to"], "source_name": label,
                          "target_name": names[edge["to"]], "source_stated": False, "target_stated": stated[edge["to"]]})
    if view == "full":
        edges.extend(_component_tests(document, nodes, names, edges))
    return edges


def _component_tests(document: dict[str, Any], nodes: dict[str, dict], names: dict[str, str],
                     known: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Checks reachable only from the part they test, shown as "<part> test" -> unnamed cause -> check."""

    remedied = {edge["to"] for edge in document["edges"] if edge["type"] in REMEDY_LINKS and not edge.get("derived")}
    out: list[dict[str, Any]] = []
    for edge in document["edges"]:
        if (edge["type"] != "ACTS_ON" or edge.get("derived") or edge["from"] in remedied
                or nodes.get(edge["from"], {}).get("type") != "CorrectiveAction"):
            continue
        part = f"test:{edge['to']}"
        test_name = f"{names[edge['to']]} test"
        for occurrence in edge["occurrences"]:
            base = _base(occurrence, edge)
            key, label = _unnamed(out, "MAY_INDICATE", part, test_name, False,
                                  f"unnamed:{part}:{base['record']}", base)
            out.append({**base, "type": "RESOLVED_BY", "source": key, "target": edge["from"], "source_name": label,
                        "target_name": names[edge["from"]], "source_stated": False, "target_stated": True})
    return out


def run_facts(document: dict[str, Any]) -> dict[str, Any]:
    """The run columns of the KPI table, from a report of this pipeline."""

    report = document.get("report") or {}
    return {"diagnostic_pages": report.get("read_pages", []), "person_questions": 0, "unresolved_questions": 0,
            "agent_answers": 0, "failed_reads": report.get("failed_reads", 0),
            "seconds": (report.get("seconds") or {}).get("total"),
            "cost_usd": round(float((report.get("usage") or {}).get("estimated_cost_usd") or 0), 5),
            "green": (report.get("graph") or {}).get("edges_by_tier", {}).get("green", 0), "derived_causes": 0}
