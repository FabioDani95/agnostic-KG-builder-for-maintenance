"""Project the draft ontology graph into triplets — Fase A3 (unify the extractor).

Historically the pipeline ran two independent extractions: the ontology draft
(full graph) and a second LLM pass that re-extracted Symptom/FailureMode/
CorrectiveAction tables. The two used different ids and were reconciled by a
fuzzy merge that could drop draft nodes.

This module removes the second extraction: it derives the triplets the operator
validates directly from the draft graph's own chains
(Symptom -MAY_INDICATE-> FailureMode -RESOLVED_BY-> CorrectiveAction). The
triplets therefore carry the graph's own ids, so the downstream merge is an
identity (no fuzzy id reconciliation) and what the operator validates is exactly
what was extracted into the graph.

The output is a standard ExtractionResult so the existing validation UI, export
and tests keep working unchanged.
"""

from __future__ import annotations

import logging
from typing import Any

from backend.models import (
    CorrectiveAction,
    ExtractionResult,
    FailureMode,
    Severity,
    Symptom,
    Triplet,
)

logger = logging.getLogger(__name__)

_ID_FIELD = {
    "Symptom": "symptom_id",
    "FailureMode": "failure_mode_id",
    "CorrectiveAction": "action_id",
}


def _severity(value: Any) -> Severity:
    try:
        return Severity(str(value or "").strip().capitalize())
    except ValueError:
        return Severity.MEDIUM


def _first_evidence_page(relation: dict[str, Any]) -> int:
    for ev in relation.get("evidence") or []:
        if not isinstance(ev, dict):
            continue
        try:
            page = int(ev.get("source_page") or 0)
        except (TypeError, ValueError):
            continue
        if page > 0:
            return page
    return 0


def graph_has_validatable_chains(ontology: dict[str, Any]) -> bool:
    """True when the draft graph already contains Symptom→FailureMode chains."""
    nodes = (ontology or {}).get("nodes") or {}
    has_symptoms = bool(nodes.get("Symptom"))
    has_failure_modes = bool(nodes.get("FailureMode"))
    has_may_indicate = any(
        str(rel.get("name") or rel.get("type")) == "MAY_INDICATE"
        for rel in (ontology or {}).get("relations", []) or []
        if isinstance(rel, dict)
    )
    return has_symptoms and has_failure_modes and has_may_indicate


def project_graph_to_triplets(
    ontology: dict[str, Any],
    *,
    source_type: str = "",
    source_title: str = "",
) -> ExtractionResult:
    """Build an ExtractionResult from the draft graph's diagnostic chains.

    Every Symptom that participates in a MAY_INDICATE edge becomes a triplet with
    its linked FailureModes and, through RESOLVED_BY, their CorrectiveActions.
    Node ids are preserved verbatim so the export merge is an identity.
    """
    nodes = (ontology or {}).get("nodes") or {}
    relations = [rel for rel in (ontology or {}).get("relations", []) or [] if isinstance(rel, dict)]

    symptoms = {
        str(n.get("symptom_id", "")).strip(): n
        for n in nodes.get("Symptom", []) or []
        if isinstance(n, dict) and str(n.get("symptom_id", "")).strip()
    }
    error_codes = {
        str(n.get("error_code_id", "")).strip(): str(n.get("code") or n.get("name") or "").strip()
        for n in nodes.get("ErrorCode", []) or []
        if isinstance(n, dict) and str(n.get("error_code_id", "")).strip()
    }
    failure_modes = {
        str(n.get("failure_mode_id", "")).strip(): n
        for n in nodes.get("FailureMode", []) or []
        if isinstance(n, dict) and str(n.get("failure_mode_id", "")).strip()
    }
    actions = {
        str(n.get("action_id", "")).strip(): n
        for n in nodes.get("CorrectiveAction", []) or []
        if isinstance(n, dict) and str(n.get("action_id", "")).strip()
    }

    # symptom -> [failure_mode_id], failure_mode -> [action_id], with evidence pages
    may_indicate: dict[str, list[str]] = {}
    resolved_by: dict[str, list[str]] = {}
    fm_evidence: dict[str, int] = {}
    ca_link_page: dict[str, int] = {}
    # failure_mode -> [error code text], via ErrorCode -INDICATES-> FailureMode.
    # Alarm-code chains are first-class diagnostic knowledge (the user reports
    # the displayed code, not the symptom), so the projection must not drop them.
    fm_error_codes: dict[str, list[str]] = {}
    for rel in relations:
        name = str(rel.get("name") or rel.get("type") or "").strip()
        from_id = str(rel.get("from_id") or "").strip()
        to_id = str(rel.get("to_id") or "").strip()
        if name == "MAY_INDICATE" and from_id in symptoms and to_id in failure_modes:
            may_indicate.setdefault(from_id, [])
            if to_id not in may_indicate[from_id]:
                may_indicate[from_id].append(to_id)
            fm_evidence.setdefault(to_id, _first_evidence_page(rel))
        elif name == "RESOLVED_BY" and from_id in failure_modes and to_id in actions:
            resolved_by.setdefault(from_id, [])
            if to_id not in resolved_by[from_id]:
                resolved_by[from_id].append(to_id)
            ca_link_page.setdefault(to_id, _first_evidence_page(rel))
        elif name == "INDICATES" and from_id in error_codes and to_id in failure_modes:
            code = error_codes[from_id]
            if code:
                fm_error_codes.setdefault(to_id, [])
                if code not in fm_error_codes[to_id]:
                    fm_error_codes[to_id].append(code)

    triplets: list[Triplet] = []
    for symptom_id, sym_node in symptoms.items():
        linked_fm_ids = may_indicate.get(symptom_id, [])
        if not linked_fm_ids:
            continue  # orphan symptoms surface via the review queue, not as triplets
        symptom = Symptom(
            symptom_id=symptom_id,
            name=str(sym_node.get("name", "")),
            description=str(sym_node.get("description", "")),
            severity=_severity(sym_node.get("severity")),
        )
        fm_models: list[FailureMode] = []
        ca_models: list[CorrectiveAction] = []
        for fm_id in linked_fm_ids:
            fm_node = failure_modes[fm_id]
            fm_models.append(FailureMode(
                failure_mode_id=fm_id,
                name=str(fm_node.get("name", "")),
                description=str(fm_node.get("description", "")),
                material_context=str(fm_node.get("material_context", "")),
                linked_symptom_id=symptom_id,
                evidence_page=fm_evidence.get(fm_id, 0),
                error_codes=list(fm_error_codes.get(fm_id, [])),
            ))
            for action_id in resolved_by.get(fm_id, []):
                ca_node = actions[action_id]
                try:
                    source_page = int(ca_node.get("source_page") or 0)
                except (TypeError, ValueError):
                    source_page = 0
                ca_models.append(CorrectiveAction(
                    action_id=action_id,
                    name=str(ca_node.get("name", "")),
                    description=str(ca_node.get("description", "")),
                    instruction_text=str(ca_node.get("instruction_text", "")),
                    source_type=str(ca_node.get("source_type", "") or source_type),
                    source_title=str(ca_node.get("source_title", "") or source_title),
                    source_page=source_page or ca_link_page.get(action_id, 0),
                    linked_failure_mode_id=fm_id,
                ))
        triplet_codes: list[str] = []
        for fm_model in fm_models:
            for code in fm_model.error_codes:
                if code not in triplet_codes:
                    triplet_codes.append(code)
        triplets.append(Triplet(
            symptom=symptom,
            failure_modes=fm_models,
            corrective_actions=ca_models,
            error_codes=triplet_codes,
        ))

    logger.info(
        "[projection] Projected %d triplet(s) from draft graph (%d symptoms, %d FMs, %d actions)",
        len(triplets),
        len(symptoms),
        len(failure_modes),
        len(actions),
    )
    return ExtractionResult(
        triplets=triplets,
        raw_symptom_table="",
        raw_failure_mode_table="",
        raw_corrective_action_table="",
    )
