"""Schema-driven publication gate and projections for source subgraphs."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any

from backend.domain.subgraphs import (
    GraphEvidenceRef,
    GraphProjection,
    KnowledgeGap,
    SourceGraphNode,
    SourceGraphRelation,
)
from backend.services.ontology_schema_service import load_ontology_schema
from backend.services.ontology_semantics import normalize_semantic_text


@dataclass(frozen=True)
class PublicationGateResult:
    nodes: list[SourceGraphNode]
    relations: list[SourceGraphRelation]
    projections: dict[str, GraphProjection]
    knowledge_gaps: list[KnowledgeGap]
    review_queue: list[dict[str, Any]]
    review_summary: dict[str, Any]
    metrics: dict[str, Any]


def _relation_for(domain: str, range_: str) -> str:
    schema = load_ontology_schema()
    match = next((item.name for item in schema.relations if item.domain == domain and item.range == range_), "")
    if not match:
        raise RuntimeError(f"Configured ontology has no {domain} -> {range_} relation")
    return match


def _anchor_resolves(anchor: str, evidence: GraphEvidenceRef) -> bool:
    normalized_anchor = normalize_semantic_text(anchor)
    if not normalized_anchor:
        return False
    locator = evidence.locator
    locator_anchor = str(locator.get("source_anchor") or locator.get("anchor") or "")
    if locator_anchor and normalized_anchor == normalize_semantic_text(locator_anchor):
        return True
    page = locator.get("page")
    return page is not None and normalized_anchor in {
        normalize_semantic_text(f"page:{page}"),
        normalize_semantic_text(f"page {page}"),
        normalize_semantic_text(str(evidence.evidence_id)),
    }


def _canonical_evidence_text(evidence: GraphEvidenceRef) -> str:
    """Return the complete claim span; ``excerpt`` is display-only for PDFs."""
    if evidence.locator.get("kind") == "pdf":
        return str(
            evidence.locator.get("canonical_text")
            or evidence.locator.get("quote")
            or ""
        )
    return evidence.excerpt


def _grounded_copy(
    relation: SourceGraphRelation,
    evidence_by_id: dict[str, GraphEvidenceRef],
) -> SourceGraphRelation | None:
    valid_refs = []
    for ref in relation.evidence_refs:
        evidence = evidence_by_id.get(str(ref.evidence_id))
        if evidence is None:
            continue
        quote = normalize_semantic_text(ref.quote)
        canonical_text = normalize_semantic_text(_canonical_evidence_text(evidence))
        if not quote or not canonical_text or quote not in canonical_text:
            continue
        if not _anchor_resolves(ref.source_anchor, evidence):
            continue
        valid_refs.append(ref)
    if not valid_refs:
        return None
    return relation.model_copy(
        update={
            "evidence_ids": sorted({ref.evidence_id for ref in valid_refs}),
            "evidence_refs": valid_refs,
        }
    )


def _ids_by_type(nodes: list[SourceGraphNode]) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    for node in nodes:
        result[node.node_type].add(node.node_id)
    return result


def _relation_ids(relations: list[SourceGraphRelation]) -> list[str]:
    return sorted(relation.relation_id for relation in relations)


def _weak_component_sizes(
    node_ids: set[str],
    relations: list[SourceGraphRelation],
) -> list[int]:
    """Return deterministic undirected component sizes for observability.

    The ontology does not define an Asset-to-Symptom root edge, so literal
    single-component connectivity is a policy decision rather than a safe
    publication invariant. Persisting the exact count keeps that distinction
    visible instead of overloading the existing zero-isolate check.
    """
    adjacency = {node_id: set() for node_id in node_ids}
    for relation in relations:
        if relation.from_id not in adjacency or relation.to_id not in adjacency:
            continue
        adjacency[relation.from_id].add(relation.to_id)
        adjacency[relation.to_id].add(relation.from_id)
    sizes: list[int] = []
    remaining = set(node_ids)
    while remaining:
        frontier = [min(remaining)]
        visited: set[str] = set()
        while frontier:
            node_id = frontier.pop()
            if node_id in visited:
                continue
            visited.add(node_id)
            frontier.extend(sorted(adjacency[node_id] - visited, reverse=True))
        remaining -= visited
        sizes.append(len(visited))
    return sorted(sizes, reverse=True)


def build_publication_graph(
    *,
    candidate_nodes: list[SourceGraphNode],
    candidate_relations: list[SourceGraphRelation],
    evidence: list[GraphEvidenceRef],
    prior_gaps: list[KnowledgeGap] | None = None,
    canonicalization_report: dict[str, Any] | None = None,
) -> PublicationGateResult:
    """Build canonical, diagnostic and structural views from grounded claims.

    Completeness is expressed only through relation domain/range pairs supplied
    by the configured ontology.  Gold labels, page numbers, vendors and machine
    terminology never participate in the decision.
    """
    asset_component = _relation_for("Asset", "Component")
    symptom_failure = _relation_for("Symptom", "FailureMode")
    failure_component = _relation_for("FailureMode", "Component")
    failure_action = _relation_for("FailureMode", "CorrectiveAction")
    asset_error = _relation_for("Asset", "ErrorCode")
    error_failure = _relation_for("ErrorCode", "FailureMode")

    evidence_by_id = {str(item.evidence_id): item for item in evidence}
    node_by_id = {item.node_id: item for item in candidate_nodes}
    node_ids_by_type = _ids_by_type(candidate_nodes)
    relation_definitions = {item.name: item for item in load_ontology_schema().relations}

    grounded_relations: list[SourceGraphRelation] = []
    ungrounded_relations: list[SourceGraphRelation] = []
    for relation in candidate_relations:
        definition = relation_definitions.get(relation.relation_type)
        from_node = node_by_id.get(relation.from_id)
        to_node = node_by_id.get(relation.to_id)
        if (
            definition is None
            or from_node is None
            or to_node is None
            or from_node.node_type != definition.domain
            or to_node.node_type != definition.range
        ):
            ungrounded_relations.append(relation)
            continue
        grounded = _grounded_copy(relation, evidence_by_id)
        if grounded is None:
            ungrounded_relations.append(relation)
        else:
            grounded_relations.append(grounded)

    by_type: dict[str, list[SourceGraphRelation]] = defaultdict(list)
    for relation in grounded_relations:
        by_type[relation.relation_type].append(relation)

    failures_with_action = {relation.from_id for relation in by_type[failure_action]}
    complete_symptom_relations = [
        relation for relation in by_type[symptom_failure] if relation.to_id in failures_with_action
    ]
    complete_error_relations = [
        relation for relation in by_type[error_failure] if relation.to_id in failures_with_action
    ]
    complete_failures = {
        relation.to_id for relation in [*complete_symptom_relations, *complete_error_relations]
    }

    diagnostic_relation_candidates: list[SourceGraphRelation] = [
        *complete_symptom_relations,
        *complete_error_relations,
        *(relation for relation in by_type[failure_action] if relation.from_id in complete_failures),
        *(relation for relation in by_type[failure_component] if relation.from_id in complete_failures),
    ]
    complete_error_ids = {relation.from_id for relation in complete_error_relations}
    diagnostic_relation_candidates.extend(
        relation for relation in by_type[asset_error] if relation.to_id in complete_error_ids
    )

    diagnostic_node_ids: set[str] = set()
    for relation in diagnostic_relation_candidates:
        diagnostic_node_ids.update((relation.from_id, relation.to_id))

    structural_relations = [
        relation for relation in by_type[asset_component]
        if relation.to_id in node_ids_by_type.get("Component", set())
    ]
    structural_node_ids: set[str] = set()
    for relation in structural_relations:
        structural_node_ids.update((relation.from_id, relation.to_id))

    canonical_relation_by_id = {
        relation.relation_id: relation
        for relation in [*diagnostic_relation_candidates, *structural_relations]
    }
    canonical_node_ids = diagnostic_node_ids | structural_node_ids

    # No isolated assertion is publishable.  This also prevents an Asset from
    # being retained merely because it is workspace-canonical; it remains the
    # mandatory endpoint of grounded structural/error assertions.
    canonical_relations = sorted(canonical_relation_by_id.values(), key=lambda item: item.relation_id)
    incident_ids = {
        endpoint
        for relation in canonical_relations
        for endpoint in (relation.from_id, relation.to_id)
    }
    canonical_node_ids &= incident_ids
    canonical_nodes = sorted(
        (node_by_id[node_id] for node_id in canonical_node_ids if node_id in node_by_id),
        key=lambda item: (item.node_type, item.node_id),
    )
    canonical_node_ids = {node.node_id for node in canonical_nodes}

    gaps = list(prior_gaps or [])
    gap_keys = {(gap.code, gap.target_kind, gap.target_id) for gap in gaps}

    def add_gap(
        code: str,
        target_kind: str,
        target_id: str,
        message: str,
        *,
        disposition: str = "gap",
        blocking: bool = False,
        evidence_ids: list[str] | None = None,
    ) -> None:
        key = (code, target_kind, target_id)
        if key in gap_keys:
            return
        gap_keys.add(key)
        gaps.append(
            KnowledgeGap(
                code=code,
                message=message,
                evidence_ids=sorted(set(evidence_ids or [])),
                target_kind=target_kind,
                target_id=target_id,
                stage="publication_gate",
                blocking=blocking,
                disposition=disposition,
            )
        )

    symptom_to_failures: dict[str, set[str]] = defaultdict(set)
    error_to_failures: dict[str, set[str]] = defaultdict(set)
    actions_by_failure: dict[str, set[str]] = defaultdict(set)
    affected_by_failure: dict[str, set[str]] = defaultdict(set)
    for relation in by_type[symptom_failure]:
        symptom_to_failures[relation.from_id].add(relation.to_id)
    for relation in by_type[error_failure]:
        error_to_failures[relation.from_id].add(relation.to_id)
    for relation in by_type[failure_action]:
        actions_by_failure[relation.from_id].add(relation.to_id)
    for relation in by_type[failure_component]:
        affected_by_failure[relation.from_id].add(relation.to_id)

    for symptom_id in sorted(node_ids_by_type.get("Symptom", set())):
        failures = symptom_to_failures.get(symptom_id, set())
        if not failures:
            add_gap(
                "diagnostic_missing_failure_mode", "Symptom", symptom_id,
                "Observed symptom has no grounded relation to an explicit failure mode.",
            )
        elif not any(actions_by_failure.get(failure_id) for failure_id in failures):
            add_gap(
                "diagnostic_missing_corrective_action", "Symptom", symptom_id,
                "Observed symptom reaches no grounded corrective action through a failure mode.",
            )

    indicator_failure_ids = {
        failure_id for values in [*symptom_to_failures.values(), *error_to_failures.values()] for failure_id in values
    }
    for failure_id in sorted(node_ids_by_type.get("FailureMode", set())):
        if failure_id not in indicator_failure_ids:
            add_gap(
                "diagnostic_failure_without_indicator", "FailureMode", failure_id,
                "Failure mode has no grounded incoming Symptom or ErrorCode relation.",
                disposition="exclude",
            )
        if not actions_by_failure.get(failure_id):
            add_gap(
                "diagnostic_failure_without_action", "FailureMode", failure_id,
                "Failure mode has no grounded corrective action.",
            )
        if not affected_by_failure.get(failure_id):
            add_gap(
                "diagnostic_failure_without_component", "FailureMode", failure_id,
                "No explicitly grounded affected component was found; AFFECTS remains optional.",
                disposition="review",
            )

    linked_action_ids = {target for targets in actions_by_failure.values() for target in targets}
    for action_id in sorted(node_ids_by_type.get("CorrectiveAction", set()) - linked_action_ids):
        add_gap(
            "diagnostic_unlinked_or_noncorrective_action", "CorrectiveAction", action_id,
            "Action is not grounded as resolving an explicit failure mode and is excluded from publication.",
            disposition="exclude",
        )

    for error_id in sorted(node_ids_by_type.get("ErrorCode", set())):
        failures = error_to_failures.get(error_id, set())
        if not failures or not any(actions_by_failure.get(failure_id) for failure_id in failures):
            add_gap(
                "diagnostic_incomplete_error_chain", "ErrorCode", error_id,
                "Error code does not reach a grounded corrective action through a failure mode.",
            )

    for relation in ungrounded_relations:
        add_gap(
            "publication_relation_ungrounded", "relation", relation.relation_id,
            "Relation has no quote and anchor resolvable to canonical evidence and is excluded.",
            disposition="review",
            evidence_ids=[str(value) for value in relation.evidence_ids],
        )

    auto_merged = int((canonicalization_report or {}).get("auto_merged_count", 0))
    ambiguous = list((canonicalization_report or {}).get("ambiguous_groups", []))
    for index, group in enumerate(ambiguous):
        add_gap(
            "canonicalization_ambiguous", str(group.get("node_type") or "node"), f"candidate:{index + 1}",
            "Potential near-duplicate was not auto-merged because identity was not certain.",
            disposition="review",
        )

    review_queue = [
        {
            "item_id": f"publication:{index + 1}",
            "priority": "blocking" if gap.blocking else "review",
            "code": gap.code,
            "target_kind": gap.target_kind,
            "target_id": gap.target_id,
            "message": gap.message,
            "evidence_ids": [str(value) for value in gap.evidence_ids],
            "disposition": gap.disposition,
        }
        for index, gap in enumerate(gaps)
        if gap.blocking or gap.disposition in {"gap", "review"}
    ]

    relation_counts = Counter(relation.relation_type for relation in canonical_relations)
    node_counts = Counter(node.node_type for node in canonical_nodes)
    complete_symptom_ids = {relation.from_id for relation in complete_symptom_relations}
    action_ids = node_ids_by_type.get("CorrectiveAction", set())
    published_action_ids = {node.node_id for node in canonical_nodes if node.node_type == "CorrectiveAction"}
    structural_component_ids = {
        node_id for node_id in structural_node_ids if node_id in node_ids_by_type.get("Component", set())
    }
    diagnostic_component_ids = {
        node_id for node_id in diagnostic_node_ids if node_id in node_ids_by_type.get("Component", set())
    }
    canonical_component_sizes = _weak_component_sizes(
        canonical_node_ids,
        canonical_relations,
    )
    published_diagnostic_node_ids = diagnostic_node_ids & canonical_node_ids
    diagnostic_relation_ids = {
        relation.relation_id for relation in diagnostic_relation_candidates
    }
    published_diagnostic_relations = [
        relation
        for relation in canonical_relations
        if relation.relation_id in diagnostic_relation_ids
    ]
    diagnostic_component_sizes = _weak_component_sizes(
        published_diagnostic_node_ids,
        published_diagnostic_relations,
    )
    metrics = {
        "candidate_nodes": len(candidate_nodes),
        "candidate_relations": len(candidate_relations),
        "published_nodes": len(canonical_nodes),
        "published_relations": len(canonical_relations),
        "nodes_by_type": dict(sorted(node_counts.items())),
        "relations_by_type": dict(sorted(relation_counts.items())),
        "isolated_nodes": 0,
        "weakly_connected_components": len(canonical_component_sizes),
        "weak_component_sizes": canonical_component_sizes,
        "diagnostic_weakly_connected_components": len(diagnostic_component_sizes),
        "diagnostic_weak_component_sizes": diagnostic_component_sizes,
        "published_symptoms": len(complete_symptom_ids),
        "published_symptoms_with_complete_path": len(complete_symptom_ids),
        "published_failure_modes": len(complete_failures),
        "published_failure_modes_without_indicator": 0,
        "published_failure_modes_without_action": 0,
        "published_failure_modes_without_component": len(complete_failures - set(affected_by_failure)),
        "candidate_corrective_actions": len(action_ids),
        "published_corrective_actions": len(published_action_ids),
        "published_corrective_actions_without_failure": 0,
        "structural_components": len(structural_component_ids),
        "diagnostic_components": len(diagnostic_component_ids),
        "grounded_relations": len(canonical_relations),
        "ungrounded_relations": 0,
        "excluded_ungrounded_relations": len(ungrounded_relations),
        "auto_merged_duplicates": auto_merged,
        "ambiguous_near_duplicates": len(ambiguous),
        "knowledge_gaps": len(gaps),
        "review_queue_items": len(review_queue),
    }

    projections = {
        "canonical": GraphProjection(
            node_ids=sorted(canonical_node_ids),
            relation_ids=_relation_ids(canonical_relations),
        ),
        "diagnostic": GraphProjection(
            node_ids=sorted(diagnostic_node_ids & canonical_node_ids),
            relation_ids=_relation_ids(diagnostic_relation_candidates),
        ),
        "structural": GraphProjection(
            node_ids=sorted(structural_node_ids & canonical_node_ids),
            relation_ids=_relation_ids(structural_relations),
        ),
    }
    review_summary = {
        "total": len(review_queue),
        "blocking": sum(item["priority"] == "blocking" for item in review_queue),
        "by_code": dict(sorted(Counter(item["code"] for item in review_queue).items())),
    }
    return PublicationGateResult(
        nodes=canonical_nodes,
        relations=canonical_relations,
        projections=projections,
        knowledge_gaps=gaps,
        review_queue=review_queue,
        review_summary=review_summary,
        metrics=metrics,
    )
