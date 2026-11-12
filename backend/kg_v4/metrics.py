"""Offline measures of an exported graph (``graph.json``), for any pipeline version.

Connectivity is counted on grounded edges only: the asset node and the links the code derives
from it are left out, because a graph hung on one artificial hub is connected only on paper.
Node quality counts what a technician would read: descriptions that say more than the name,
required attributes that are filled, generic or noisy names, and candidates for residual
duplicates and for wrongly merged false friends. The last two are lexical screens that select
pairs for a person to judge; they are not a semantic verdict.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

from backend.kg_v4.names import canonical, distinguishing_difference, name_defects, similarity

ONTOLOGY_PATH = Path(__file__).resolve().parents[2] / "ontology_schema.JSON"
ENTRY_TYPES = {"Symptom", "ErrorCode"}
CAUSE_LINKS = {"MAY_INDICATE", "INDICATES"}
DIRECT_LINKS = {"ADDRESSED_BY", "CLEARED_BY"}
# Edge occurrences the code derives from names or from the survey's hierarchy rather than reads
# from a diagnostic passage; reported both in and out so that nobody has to trust them.
DERIVED_ORIGINS = {"name_mention", "catalogue"}
PLACEHOLDER = re.compile(r"^\s*(not[_ ]stated|unknown|unspecified|n/?a|none|null|-|tbd|)\s*$", re.I)
MIN_DESCRIPTION_CHARS = 25
DUPLICATE_SIMILARITY = 0.85


def _grounded(graph: dict[str, Any], *, extracted_only: bool = False, drop_escalations: bool = False):
    nodes = {node["id"]: node for node in graph["nodes"] if node["type"] != "Asset"}
    if drop_escalations:
        nodes = {key: node for key, node in nodes.items()
                 if not (node["type"] == "CorrectiveAction"
                         and node.get("properties", {}).get("action_kind") == "escalation")}
    edges = []
    for edge in graph["edges"]:
        if edge.get("derived") or edge["from"] not in nodes or edge["to"] not in nodes:
            continue
        if extracted_only:
            origins = {item.get("origin", "extract") for item in edge.get("occurrences", [])}
            if origins and origins <= DERIVED_ORIGINS:
                continue
        edges.append(edge)
    return nodes, edges


def _components(nodes: dict[str, Any], edges: list[dict[str, Any]]) -> list[int]:
    adjacent: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        adjacent[edge["from"]].add(edge["to"])
        adjacent[edge["to"]].add(edge["from"])
    seen: set[str] = set()
    sizes = []
    for start in nodes:
        if start in seen:
            continue
        stack, size = [start], 0
        seen.add(start)
        while stack:
            current = stack.pop()
            size += 1
            for other in adjacent[current] - seen:
                seen.add(other)
                stack.append(other)
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _share(part: int, whole: int) -> float | None:
    return round(part / whole, 4) if whole else None


def connectivity(graph: dict[str, Any]) -> dict[str, Any]:
    """Components, chains and declared absences, without the asset hub and derived links."""

    nodes, edges = _grounded(graph)
    sizes = _components(nodes, edges)
    out: dict[str, set[tuple[str, str]]] = defaultdict(set)
    incoming: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for edge in edges:
        out[edge["from"]].add((edge["type"], edge["to"]))
        incoming[edge["to"]].add((edge["type"], edge["from"]))

    def has(node_id: str, relations: set[str], table=out) -> bool:
        return any(relation in relations for relation, _ in table[node_id])

    causes = [key for key, node in nodes.items() if node["type"] == "FailureMode"]
    entries = [key for key, node in nodes.items() if node["type"] in ENTRY_TYPES]
    properties = {key: node.get("properties", {}) for key, node in nodes.items()}
    with_action = [key for key in causes if has(key, {"RESOLVED_BY"})]
    declared_no_remedy = [key for key in causes if key not in with_action
                          and properties[key].get("remedy_status") in {"not_stated", "not_in_entry"}]
    reachable = [key for key in causes if has(key, CAUSE_LINKS, incoming)]
    declared_no_entry = [key for key in causes if key not in reachable
                         and properties[key].get("entry_status") == "none_in_manual"]

    def complete(entry: str) -> bool:
        return has(entry, DIRECT_LINKS) or any(
            relation in CAUSE_LINKS and has(target, {"RESOLVED_BY"}) for relation, target in out[entry])

    diagnosed = [key for key in entries if has(key, CAUSE_LINKS | DIRECT_LINKS)]
    declared_undiagnosed = [key for key in entries if key not in diagnosed
                            and properties[key].get("diagnosis_status") == "not_stated"]
    chains = [key for key in entries if complete(key)]
    variants = {}
    for name, options in (("extracted_only", {"extracted_only": True}),
                          ("without_escalation_actions", {"drop_escalations": True})):
        other_nodes, other_edges = _grounded(graph, **options)
        other = _components(other_nodes, other_edges)
        variants[name] = {"nodes": len(other_nodes), "components": len(other),
                          "largest_component_share": _share(other[0], len(other_nodes)) if other else None}
    origins = Counter(item.get("origin", "extract") for edge in edges for item in edge.get("occurrences", []))
    degree = Counter()
    for edge in edges:
        degree[edge["from"]] += 1
        degree[edge["to"]] += 1
    hubs = [{"name": nodes[key]["name"], "type": nodes[key]["type"], "degree": count}
            for key, count in degree.most_common(5)]
    return {
        "nodes": len(nodes), "edges": len(edges), "nodes_by_type": dict(Counter(n["type"] for n in nodes.values())),
        "edges_by_type": dict(Counter(edge["type"] for edge in edges)),
        "components": len(sizes), "largest_component_share": _share(sizes[0], len(nodes)) if sizes else None,
        "component_sizes_top5": sizes[:5], "isolated_nodes": sum(size == 1 for size in sizes),
        "causes": len(causes),
        "causes_with_action": len(with_action), "causes_with_action_share": _share(len(with_action), len(causes)),
        "causes_declared_without_remedy": len(declared_no_remedy),
        "causes_with_action_or_declared_share": _share(len(with_action) + len(declared_no_remedy), len(causes)),
        "causes_reachable_from_entry": len(reachable),
        "causes_reachable_share": _share(len(reachable), len(causes)),
        "causes_declared_without_entry": len(declared_no_entry),
        "causes_reachable_where_manual_gives_entry_share": _share(len(reachable), len(causes) - len(declared_no_entry)),
        "entries": len(entries), "entries_with_diagnosis": len(diagnosed),
        "entries_declared_without_diagnosis": len(declared_undiagnosed),
        "entries_with_complete_chain": len(chains),
        "entries_with_complete_chain_share": _share(len(chains), len(entries)),
        "excluded_relations": len(graph.get("excluded_relations", [])),
        "excluded_share": _share(len(graph.get("excluded_relations", [])),
                                 len(graph.get("excluded_relations", [])) + len(edges)),
        "occurrences_by_origin": dict(origins), "variants": variants, "highest_degree_nodes": hubs,
    }


def required_properties(ontology: dict[str, Any] | None = None) -> dict[str, list[str]]:
    ontology = ontology or json.loads(ONTOLOGY_PATH.read_text(encoding="utf-8"))
    return {item["name"]: [prop["name"] for prop in item["properties"]
                           if prop.get("required") and not prop["name"].endswith("_id")
                           and prop["name"] not in {"name", "description"}]
            for item in ontology["nodes"]}


def node_quality(graph: dict[str, Any], ontology: dict[str, Any] | None = None) -> dict[str, Any]:
    required = required_properties(ontology)
    nodes = [node for node in graph["nodes"] if node["type"] != "Asset"]
    degree = Counter()
    for edge in graph["edges"]:
        if not edge.get("derived"):
            degree[edge["from"]] += 1
            degree[edge["to"]] += 1
    real = from_manual = total_required = placeholders = inferred = from_name = 0
    placeholder_by_property: Counter = Counter()
    defects: Counter = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    bridges = []
    for node in nodes:
        properties = node.get("properties", {})
        description = " ".join(str(properties.get("description") or "").split())
        is_real = len(description) >= MIN_DESCRIPTION_CHARS and canonical(description) != canonical(node["name"])
        real += is_real
        # Graphs of the previous pipeline carry no source mark: a real description there would be the manual's.
        from_manual += is_real and node.get("description_source", "manual") == "manual"
        for key in required.get(node["type"], []):
            total_required += 1
            value = properties.get(key)
            if value is None or (isinstance(value, str) and PLACEHOLDER.match(value)):
                placeholders += 1
                placeholder_by_property[f"{node['type']}.{key}"] += 1
        inferred += len(node.get("inferred_properties", []))
        from_name += len(node.get("name_derived_properties", []))
        # In graphs of the previous pipeline the instruction of every action is its name.
        if node["type"] == "CorrectiveAction" and "name_derived_properties" not in node and canonical(
                str(properties.get("instruction_text") or "")) == canonical(node["name"]):
            from_name += 1
        for defect in name_defects(node["name"]):
            defects[defect] += 1
            if len(examples[defect]) < 5:
                examples[defect].append(node["name"])
            if defect == "generic" and degree[node["id"]] >= 2:
                bridges.append(node["name"])
    by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        by_type[node["type"]].append(node)
    exact = 0
    candidates: list[dict[str, Any]] = []
    for kind, group in by_type.items():
        keys = Counter(canonical(node["name"]) + "|" + str(node.get("properties", {}).get("code") or "")
                       for node in group)
        exact += sum(count - 1 for count in keys.values() if count > 1)
        names = sorted({node["name"] for node in group})
        for left, right in combinations(names, 2):
            if canonical(left) == canonical(right) or distinguishing_difference(left, right):
                continue
            score = similarity(left, right)
            if score >= DUPLICATE_SIMILARITY:
                candidates.append({"type": kind, "left": left, "right": right, "similarity": score})
    suspect = []
    for node in nodes:
        names = [node["name"], *node.get("aliases", [])]
        for left, right in combinations(names, 2):
            reason = distinguishing_difference(left, right)
            if reason:
                suspect.append({"type": node["type"], "node": node["name"], "left": left, "right": right,
                                "reason": reason})
    candidates.sort(key=lambda item: (-item["similarity"], item["left"]))
    return {
        "nodes": len(nodes),
        "real_descriptions": real, "real_description_share": _share(real, len(nodes)),
        "descriptions_from_manual": from_manual, "descriptions_from_manual_share": _share(from_manual, len(nodes)),
        "required_attributes": total_required, "placeholder_attributes": placeholders,
        "filled_required_attribute_share": _share(total_required - placeholders, total_required),
        "attributes_repeating_the_name": from_name,
        "required_attributes_from_manual_share": _share(total_required - placeholders - from_name, total_required),
        "placeholder_by_property": dict(placeholder_by_property.most_common()),
        "inferred_attributes": inferred,
        "name_defects": dict(defects), "name_defect_examples": dict(examples),
        "generic_nodes_used_as_bridge": len(bridges), "generic_bridge_examples": bridges[:5],
        "exact_duplicates": exact,
        "duplicate_candidates": len(candidates), "duplicate_candidate_share": _share(len(candidates), len(nodes)),
        "duplicate_candidate_examples": candidates[:8],
        "suspect_merges": len(suspect), "suspect_merge_examples": suspect[:8],
        "nodes_with_aliases": sum(bool(node.get("aliases")) for node in nodes),
    }


def provenance(graph: dict[str, Any]) -> dict[str, Any]:
    """How precisely facts point to the manual: every occurrence needs a page; sections and segments add to it."""

    occurrences = [item for edge in graph["edges"] if not edge.get("derived") for item in edge.get("occurrences", [])]
    with_page = sum(any(e.get("page") for e in item.get("evidence", [])) for item in occurrences)
    with_section = sum(any(e.get("section") for e in item.get("evidence", [])) for item in occurrences)
    anchors = Counter(item.get("anchor", "cited") for item in occurrences)
    confidence = Counter(item.get("confidence") or ("high" if item.get("tier") == "green" else "low")
                         for item in occurrences)
    return {"occurrences": len(occurrences), "with_page_share": _share(with_page, len(occurrences)),
            "with_section_share": _share(with_section, len(occurrences)),
            "by_anchor": dict(anchors), "by_confidence": dict(confidence)}


def cost(report: dict[str, Any]) -> dict[str, Any]:
    usage = report.get("usage_total") or report.get("usage") or {}
    agent = report.get("agent_usage") or {}
    total = float(usage.get("estimated_cost_usd") or 0)
    if not report.get("usage_total"):
        total += float(agent.get("estimated_cost_usd") or 0)
    seconds = report.get("seconds") or {}
    return {"estimated_cost_usd": round(total, 6), "calls": usage.get("calls"),
            "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
            "seconds": seconds.get("end_to_end") or seconds.get("total"), "pages": report.get("pages")}


def scorecard(graph: dict[str, Any], ontology: dict[str, Any] | None = None) -> dict[str, Any]:
    """Every offline measure of one graph; recall and precision need a gold and judges and are added apart."""

    return {"format": graph.get("version"), "pipeline": graph.get("pipeline", "kg-v3"),
            "connectivity": connectivity(graph), "node_quality": node_quality(graph, ontology),
            "provenance": provenance(graph), "cost": cost(graph.get("report") or {})}
