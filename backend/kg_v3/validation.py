"""Mandatory final checks after all recovery and gate mutations."""

from __future__ import annotations

from backend.kg_v3.contracts import Tier
from backend.kg_v3.navigation import diagnostic_paths
from backend.kg_v3.run_state import digest


def validate_quality(graph, relations, index, doc, coverage=None):
    issues, public = [], []
    nodes = graph.nodes_by_id
    known = {r.assertion.assertion_id for r in relations}
    for edge in graph.edges:
        if edge.source not in nodes or edge.target not in nodes:
            issues.append({"code": "DANGLING_ENDPOINT", "edge_id": edge.edge_id})
        for a in edge.assertions:
            if a.tier is not Tier.GREEN:
                continue
            problems = []
            if not a.branch_id or a.branch_id not in index.branches:
                problems.append("UNKNOWN_SCOPE")
            elif index.branches[a.branch_id].scope_status not in {"VERIFIED_STRUCTURE", "VERIFIED_REVIEW"}:
                problems.append("UNVERIFIED_SCOPE")
            if not a.certificate.evidence_ref_ids or not all(
                index.resolve(r, doc) for r in a.certificate.evidence_ref_ids
            ):
                problems.append("INVALID_EVIDENCE")
            if a.certificate.validation_issues:
                problems.extend(a.certificate.validation_issues)
            if not {b.role for b in a.certificate.verified_bindings if b.support_status == "SUPPORTED"} >= {
                "subject",
                "predicate",
                "object",
            }:
                problems.append("INVALID_BINDINGS")
            # A condition is verified with its statement: the verifier and the reviewer read it.
            judged = (a.certificate.verifier_verdict and a.certificate.verifier_verdict.value == "supported") or bool(
                a.certificate.confirmed_by and a.certificate.confirmed_by.kind.value in {"human", "agent"}
            )
            if (
                a.conditions
                and not judged
                and not any(
                    b.role == "condition" and b.support_status == "SUPPORTED" for b in a.certificate.verified_bindings
                )
            ):
                problems.append("UNSUPPORTED_CONDITION")
            if a.subject_mention_id not in index.mentions or a.object_mention_id not in index.mentions:
                problems.append("DANGLING_MENTION")
            for parent in a.parent_proposal_ids:
                if parent not in known and not parent.startswith("proposal_"):
                    problems.append("MISSING_LINEAGE_PARENT")
            for node_id in (edge.source, edge.target):
                node = nodes[node_id]
                if node.type in {"FailureMode", "CorrectiveAction"} and node.branch_id != a.branch_id:
                    problems.append("CROSS_BRANCH_CONTAMINATION")
            if problems:
                issues.append({"assertion_id": a.assertion_id, "codes": sorted(set(problems))})
            else:
                public.append(a.assertion_id)
    filtered = graph.model_copy(
        update={
            "edges": [
                e.model_copy(update={"assertions": [a for a in e.assertions if a.assertion_id in public]})
                for e in graph.edges
            ]
        }
    )
    paths = [diagnostic_paths(filtered, index, n.node_id) for n in nodes.values() if n.type in {"Symptom", "ErrorCode"}]
    counts = coverage.counts() if coverage else {}
    result = {
        "contract_version": index.contract_version,
        "status": "VALID" if not issues else "INVALID",
        "issues": issues,
        "public_assertion_ids": sorted(public),
        "supported_paths": sum(len(p["paths"]) for p in paths),
        "path_gaps": [g for p in paths for g in p["gaps"]],
        "coverage": counts,
        "quality_measured": False,
        "inventory_exhaustive": False,
    }
    result["validation_fingerprint"] = digest(result)
    return result
