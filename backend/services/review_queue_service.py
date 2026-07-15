"""Review queue + open-gap surfacing — Fase A2.

The architecture goal is "the graph builds itself as automatically as possible;
the human is the last gate, only on what genuinely stays open, inconsistent, or
flagged". This module turns the diagnostic signals the pipeline already produces
into one explicit, structured queue:

- open structural gaps (deterministic): symptoms with no failure mode, failure
  modes with no corrective action, error codes not wired to a failure, etc.
- ambiguous but valid diagnostic alternatives: one symptom pointing at multiple
  failure modes that the operator should confirm as parallel candidates
- low-confidence nodes (the confidence human_review / auto_reject band)
- advisory schema/graph issues (e.g. non-actionable instruction text)

The same open-gap list is embedded in the export bundle metadata so the export
is never silent about what is incomplete — the downstream troubleshooting agent
can see exactly which chains are not closed.

Everything here is read-only: it inspects an ontology and reports; it never
mutates the graph.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from backend.services.ontology_coverage import _NODE_ID_FIELDS, _iter_relations

_ACTIONABLE_CONFIDENCE_REASONS = {
    "missing required properties",
    "human binding required",
    "evidence quote not found on cited page",
}


def _rel_endpoints(rel: dict[str, Any]) -> tuple[str, str, str]:
    """Read (type, from_id, to_id) from either the contract or internal shape.

    The contract uses ``type``; the internal pipeline instance uses ``name``.
    """
    rel_type = str(rel.get("type") or rel.get("name") or "").strip()
    from_id = str(rel.get("from_id") or rel.get("from") or "").strip()
    to_id = str(rel.get("to_id") or rel.get("to") or "").strip()
    return rel_type, from_id, to_id


def _index(ontology: dict[str, Any]) -> tuple[dict[str, dict[str, dict]], dict[str, dict[str, set[str]]], dict[str, dict[str, set[str]]]]:
    """Return (nodes_by_type_id, out_edges, in_edges)."""
    nodes_by_type = ontology.get("nodes") or {}
    nodes: dict[str, dict[str, dict]] = {}
    id_to_type: dict[str, str] = {}
    for label, id_field in _NODE_ID_FIELDS.items():
        bucket: dict[str, dict] = {}
        for node in nodes_by_type.get(label) or []:
            if not isinstance(node, dict):
                continue
            node_id = str(node.get(id_field) or "").strip()
            if node_id:
                bucket[node_id] = node
                id_to_type[node_id] = label
        nodes[label] = bucket

    out_edges: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    in_edges: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for rel in _iter_relations(ontology):
        if not isinstance(rel, dict):
            continue
        rel_type, from_id, to_id = _rel_endpoints(rel)
        if not rel_type or not from_id or not to_id:
            continue
        out_edges[rel_type][from_id].add(to_id)
        in_edges[rel_type][to_id].add(from_id)
    return nodes, out_edges, in_edges


def _label(node: dict, fallback: str) -> str:
    return str(node.get("name") or fallback)


def compute_open_gaps(ontology: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministic structural gaps that break the diagnostic chain.

    Each gap names the specific node so the operator (or downstream agent) knows
    exactly what is unresolved — not just a count.
    """
    nodes, out_edges, in_edges = _index(ontology)
    gaps: list[dict[str, Any]] = []

    for sid, node in nodes.get("Symptom", {}).items():
        if not out_edges["MAY_INDICATE"].get(sid):
            gaps.append({
                "kind": "symptom_without_failure_mode",
                "severity": "open",
                "target_type": "Symptom",
                "target_id": sid,
                "label": _label(node, sid),
                "reason": "Symptom has no MAY_INDICATE link to a FailureMode.",
                "suggested_fix": "Link it to the failure mode it indicates, or confirm it is a standalone observation.",
            })

    for fid, node in nodes.get("FailureMode", {}).items():
        if not out_edges["RESOLVED_BY"].get(fid):
            gaps.append({
                "kind": "failure_mode_without_action",
                "severity": "open",
                "target_type": "FailureMode",
                "target_id": fid,
                "label": _label(node, fid),
                "reason": "FailureMode has no RESOLVED_BY link to a CorrectiveAction.",
                "suggested_fix": "Attach the remediation procedure from the manual, or mark as unresolved.",
            })

    for aid, node in nodes.get("CorrectiveAction", {}).items():
        if not in_edges["RESOLVED_BY"].get(aid):
            gaps.append({
                "kind": "orphan_corrective_action",
                "severity": "open",
                "target_type": "CorrectiveAction",
                "target_id": aid,
                "label": _label(node, aid),
                "reason": "CorrectiveAction is not used by any FailureMode.",
                "suggested_fix": "Link it to the failure mode it resolves, or remove it if redundant.",
            })

    for eid, node in nodes.get("ErrorCode", {}).items():
        if not out_edges["INDICATES"].get(eid):
            gaps.append({
                "kind": "error_code_without_failure_mode",
                "severity": "open",
                "target_type": "ErrorCode",
                "target_id": eid,
                "label": _label(node, eid),
                "reason": "ErrorCode has no INDICATES link to a FailureMode.",
                "suggested_fix": "Link the code to the failure condition it signals.",
            })

    return gaps


def compute_review_flags(ontology: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministic review-only flags for complete but ambiguous chains."""
    nodes, out_edges, _ = _index(ontology)
    flags: list[dict[str, Any]] = []

    for sid, node in nodes.get("Symptom", {}).items():
        failure_ids = sorted(out_edges["MAY_INDICATE"].get(sid) or [])
        if len(failure_ids) < 2:
            continue
        labels = [
            _label(nodes.get("FailureMode", {}).get(fid, {}), fid)
            for fid in failure_ids
        ]
        flags.append({
            "kind": "ambiguous_multi_cause_symptom",
            "severity": "review",
            "target_type": "Symptom",
            "target_id": sid,
            "label": _label(node, sid),
            "reason": "Symptom has multiple MAY_INDICATE links to possible FailureModes.",
            "suggested_fix": "Confirm that all listed failure modes are valid parallel causes, or remove the incorrect link.",
            "candidate_count": len(failure_ids),
            "candidate_failure_mode_ids": failure_ids,
            "candidate_failure_mode_labels": labels,
        })

    return flags


def _resolved_by_candidates_by_failure_mode(
    suggested_relations: list | None,
) -> dict[str, list[dict[str, Any]]]:
    """Index RESOLVED_BY suggestions (FailureMode -> CorrectiveAction) by FM id.

    Accepts either SuggestedRelation objects or plain dicts so the queue can be
    built from an already-serialized response.
    """
    by_fm: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for suggestion in suggested_relations or []:
        def _field(name: str) -> Any:
            if isinstance(suggestion, dict):
                return suggestion.get(name)
            return getattr(suggestion, name, None)

        if str(_field("relation_name") or "") != "RESOLVED_BY":
            continue
        from_id = str(_field("from_id") or "").strip()
        to_id = str(_field("to_id") or "").strip()
        if not from_id or not to_id:
            continue
        by_fm[from_id].append({
            "action_id": to_id,
            "action_label": str(_field("to_label") or to_id),
            "confidence": _field("confidence"),
        })
    for candidates in by_fm.values():
        candidates.sort(key=lambda c: (c.get("confidence") is None, -(c.get("confidence") or 0.0)))
    return by_fm


def build_review_queue(
    ontology: dict[str, Any],
    *,
    confidence_report: Any | None = None,
    schema_issues: list | None = None,
    suggested_relations: list | None = None,
) -> list[dict[str, Any]]:
    """Unified, de-duplicated, priority-ordered queue of what the human must touch.

    Priority: open structural gaps > low-confidence nodes > advisory issues.
    De-duplicated by (target_type, target_id, kind) so a node flagged by two
    signals appears once with the highest-priority framing.

    When ``suggested_relations`` is provided, each ``failure_mode_without_action``
    gap is enriched with the top RESOLVED_BY candidates the reasoner proposed, so
    the operator can confirm a link in one click instead of hunting for the
    action. RESOLVED_BY stays human-gated — these are proposals, never applied.
    """
    queue: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def _add(item: dict[str, Any]) -> None:
        key = (item.get("target_type", ""), item.get("target_id", ""), item.get("kind", ""))
        if key in seen:
            return
        seen.add(key)
        queue.append(item)

    candidates_by_fm = _resolved_by_candidates_by_failure_mode(suggested_relations)
    for gap in compute_open_gaps(ontology):
        if gap.get("kind") == "failure_mode_without_action":
            candidates = candidates_by_fm.get(gap.get("target_id", ""))
            if candidates:
                gap = {
                    **gap,
                    "candidate_actions": candidates[:3],
                    "suggested_fix": (
                        "Confirm one of the proposed corrective actions (candidate_actions), "
                        "attach the remediation procedure from the manual, or mark as unresolved."
                    ),
                }
        _add(gap)

    for flag in compute_review_flags(ontology):
        _add(flag)

    if confidence_report is not None:
        for entry in getattr(confidence_report, "entries", []) or []:
            classification = getattr(entry, "classification", "")
            if classification not in ("human_review", "auto_reject"):
                continue
            reasons = list(getattr(entry, "reasons", []) or [])
            score = getattr(entry, "score", None)
            theta_low = getattr(confidence_report, "theta_low", 0.0)
            try:
                below_low_threshold = float(score) < float(theta_low)
            except (TypeError, ValueError):
                below_low_threshold = False
            actionable_reason = any(reason in _ACTIONABLE_CONFIDENCE_REASONS for reason in reasons)
            if classification == "human_review" and not (below_low_threshold or actionable_reason):
                continue
            _add({
                "kind": "low_confidence",
                "severity": "review" if classification == "human_review" else "reject",
                "target_type": getattr(entry, "node_type", ""),
                "target_id": getattr(entry, "node_id", ""),
                "label": getattr(entry, "node_id", ""),
                "reason": "; ".join(reasons) or "Low confidence score.",
                "suggested_fix": "Verify this node against the manual before accepting.",
                "score": score,
            })

    for issue in schema_issues or []:
        severity = str(getattr(issue, "severity", "")).strip().lower()
        if severity == "error":
            sev = "blocking"
        elif severity == "warning":
            sev = "advisory"
        else:
            continue
        _add({
            "kind": str(getattr(issue, "code", "schema_issue")),
            "severity": sev,
            "target_type": str(getattr(issue, "target_type", "")),
            "target_id": str(getattr(issue, "target_id", "")),
            "label": str(getattr(issue, "target_id", "")),
            "reason": str(getattr(issue, "message", "")),
            "suggested_fix": str(getattr(issue, "fix_hint", "")),
        })

    priority = {"blocking": 0, "open": 1, "reject": 2, "review": 3, "advisory": 4}
    queue.sort(key=lambda item: priority.get(item.get("severity", ""), 9))
    return queue


def summarize_queue(queue: list[dict[str, Any]]) -> dict[str, Any]:
    by_kind: dict[str, int] = defaultdict(int)
    by_severity: dict[str, int] = defaultdict(int)
    for item in queue:
        by_kind[item.get("kind", "")] += 1
        by_severity[item.get("severity", "")] += 1
    return {
        "requires_human_review": bool(queue),
        "total": len(queue),
        "by_kind": dict(by_kind),
        "by_severity": dict(by_severity),
    }
