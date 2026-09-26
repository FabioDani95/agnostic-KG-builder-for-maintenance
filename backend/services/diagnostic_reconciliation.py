"""Conservative reconciliation of repeated, already validated source branches.

No fuzzy name matching: occurrence, codes, polarity-bearing labels, ordered
instructions, conditions and components must agree. Original attempts remain in
the chunk reports; an excluded duplicate never supplies extra graph edges.
"""
from __future__ import annotations

import json
import re
import unicodedata
from copy import deepcopy


def _literal(value):
    value = unicodedata.normalize("NFKC", str(value or ""))
    value = re.sub(r"(?<=\w)-\s+(?=\w)", "", value)
    return re.sub(r"\s+", " ", value).strip().casefold().rstrip(".")


def _instruction(value):
    # A printed step number is provenance, not part of the instruction's
    # meaning. List order is retained by the surrounding ordered array.
    return re.sub(r"^\d+[.)]\s+", "", _literal(value))


def verified_occurrence_key(entry):
    candidate = entry.get("candidate") or {}
    window = entry.get("record_window_id")
    if entry.get("disposition") != "publish" or not window or not entry.get("validated_record"):
        return None
    payload = {
        "window": window,
        "indicators": sorted((i["kind"], i.get("code") or "", _literal(i["name"]), i.get("severity")) for i in candidate["indicators"]),
        "failure": _literal(candidate["failure"]["name"]),
        "material_context": _literal(candidate["failure"].get("material_context")),
        "actions": [_instruction(a["instruction_text"]) for a in candidate["actions"]],
        "inspections": [_instruction(s["instruction_text"]) for s in candidate.get("inspection_steps", [])],
        "conditions": [(c["applies_to"], c.get("step_index"), _literal(c["text"])) for c in candidate.get("conditions", [])],
    }
    return json.dumps(payload, sort_keys=True)


def reconcile_verified_duplicates(results):
    """Remove only repeat assertions about the same immutable source occurrence."""
    groups = {}
    for result in results:
        report = result.diagnostic_contract_report or {}
        for entry in report.get("records", []):
            key = verified_occurrence_key(entry)
            if key:
                groups.setdefault(key, {})[entry["branch_lineage_id"]] = entry
    aliases = {}
    for entries in groups.values():
        components = {branch: _literal((entry["candidate"].get("affected_component") or {}).get("name")) for branch, entry in entries.items()}
        explicit = {value for value in components.values() if value}
        if len(explicit) > 1:
            continue  # Conflicting component identities require adjudication.
        richest = [branch for branch, value in components.items() if value] or list(entries)
        winner = min(richest)
        aliases.update({branch: winner for branch in entries if branch != winner})
    if not aliases:
        return results
    reconciled = []
    for result in results:
        report = deepcopy(result.diagnostic_contract_report or {})
        removed_nodes = set()
        for entry in report.get("records", []):
            branch = entry.get("branch_lineage_id")
            if branch not in aliases:
                continue
            removed_nodes.update(entry.get("emitted_node_ids", []))
            entry["reconciled_from"] = deepcopy(entry)
            entry.update(disposition="exclude", accounting_state="duplicate_verified_occurrence", duplicate_of=aliases[branch])
            entry["drop_reasons"] = [{"code": "duplicate_verified_occurrence", "path": "record_window_id", "message": "Same source occurrence and exact normalized assertions; original attempt retained in chunk history."}]
            entry["emitted_node_ids"] = []
            entry["emitted_relations"] = []
        ontology = result.ontology.model_copy(deep=True)
        ontology.relations = [r for r in ontology.relations if r.branch_lineage_id not in aliases]
        used = {endpoint for r in ontology.relations for endpoint in (r.from_id, r.to_id)}
        for kind, nodes in ontology.nodes.items():
            ontology.nodes[kind] = [n for n in nodes if not any(str(n.get(field, "")) in removed_nodes - used for field in ("symptom_id", "error_code_id", "failure_mode_id", "action_id", "component_id"))]
        reconciled.append(result.model_copy(update={"ontology": ontology, "diagnostic_contract_report": report}))
    return reconciled
