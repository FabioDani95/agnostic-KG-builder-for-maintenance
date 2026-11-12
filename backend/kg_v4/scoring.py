"""A connected-pipeline graph as the historical branch scorer reads graphs.

The scorer (scripts/kg_v3_evaluate.py) compares gold claims "problem -> cause" and
"cause -> action" with trusted edges. This pipeline links a remedy the manual gives without a
cause directly to the symptom or code, where the previous one wrote a placeholder cause. For
scoring only, each such direct link is shown the old way: an unnamed cause, marked as not
written in the manual, between the problem and the action of the same source record. Nothing is
added to the graph, and no fact is shown that the graph does not hold.
"""

from __future__ import annotations

from typing import Any

DIRECT = {"ADDRESSED_BY": "MAY_INDICATE", "CLEARED_BY": "INDICATES"}
SCORED = {"MAY_INDICATE", "INDICATES", "RESOLVED_BY"}


def historical_edges(document: dict[str, Any]) -> list[dict[str, Any]]:
    names = {node["id"]: node["name"] for node in document["nodes"]}
    stated = {node["id"]: node.get("stated_in_source", True) for node in document["nodes"]}
    edges: list[dict[str, Any]] = []
    for edge in document["edges"]:
        if edge.get("derived") or edge["type"] not in SCORED | set(DIRECT):
            continue
        for occurrence in edge["occurrences"]:
            base = {"conditions": occurrence.get("conditions", edge.get("conditions", [])),
                    "record": occurrence.get("record", ""),
                    "segments": {item["segment_id"] for item in occurrence.get("evidence", [])},
                    "trusted": occurrence.get("tier", edge.get("tier")) == "green"}
            if edge["type"] in SCORED:
                edges.append({**base, "type": edge["type"], "source": edge["from"], "target": edge["to"],
                              "source_name": names[edge["from"]], "target_name": names[edge["to"]],
                              "source_stated": stated[edge["from"]], "target_stated": stated[edge["to"]]})
                continue
            # One unnamed cause per problem and source record, as the manual's entry has it.
            unnamed = f"unnamed:{edge['from']}:{base['record']}"
            label = f"Unspecified cause of {names[edge['from']]}"
            link = {**base, "type": DIRECT[edge["type"]], "source": edge["from"], "target": unnamed,
                    "source_name": names[edge["from"]], "target_name": label, "source_stated": stated[edge["from"]],
                    "target_stated": False, "conditions": []}
            if not any(item["type"] == link["type"] and item["source"] == link["source"]
                       and item["target"] == unnamed for item in edges):
                edges.append(link)
            edges.append({**base, "type": "RESOLVED_BY", "source": unnamed, "target": edge["to"], "source_name": label,
                          "target_name": names[edge["to"]], "source_stated": False, "target_stated": stated[edge["to"]]})
    return edges


def run_facts(document: dict[str, Any]) -> dict[str, Any]:
    """The run columns of the KPI table, from a report of this pipeline."""

    report = document.get("report") or {}
    return {"diagnostic_pages": report.get("read_pages", []), "person_questions": 0, "unresolved_questions": 0,
            "agent_answers": 0, "failed_reads": report.get("failed_reads", 0),
            "seconds": (report.get("seconds") or {}).get("total"),
            "cost_usd": round(float((report.get("usage") or {}).get("estimated_cost_usd") or 0), 5),
            "green": (report.get("graph") or {}).get("edges_by_tier", {}).get("green", 0), "derived_causes": 0}
