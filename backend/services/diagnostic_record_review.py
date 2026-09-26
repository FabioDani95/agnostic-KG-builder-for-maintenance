"""Source-backed single-record correction, without model calls or gate overrides."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy

from backend.domain.diagnostic_bundles import DiagnosticChunkOutput
from backend.domain.ids import new_id, utc_now
from backend.domain.subgraphs import (
    DiagnosticKnowledgeRecord,
    GraphEvidenceRef,
    KnowledgeGap,
    RelationEvidenceRef,
    SourceGraphNode,
    SourceGraphRelation,
    SourceSubgraphRevision,
)
from backend.services.diagnostic_bundle_compiler import compile_diagnostic_bundles
from backend.services.diagnostic_publication_service import build_publication_graph
from backend.services.diagnostic_record_windowing import build_diagnostic_record_windows
from backend.services.ontology_pipeline import _bind_candidates_to_record_windows, _record_windows
from backend.services.source_subgraph_generation import _strict_validation

ID_FIELDS = {"Asset": "asset_id", "Component": "component_id", "Symptom": "symptom_id",
             "ErrorCode": "error_code_id", "FailureMode": "failure_mode_id", "CorrectiveAction": "action_id"}


def correct_record(revision, branch_id, request, evidence):
    """Return a new immutable revision; callers persist with compare-and-swap.

    This validates the changed branch and the complete graph. Existing gaps and
    all untouched branches survive. Corrections do not certify semantic completeness.
    """
    if revision.source_kind.value != "pdf":
        raise ValueError("La correzione diagnostica richiede una fonte PDF")
    if not request.reviewer.strip() or not request.reason.strip():
        raise ValueError("Indica revisore e motivazione")
    ledger = deepcopy(revision.diagnostic_compilation_ledger)
    records = ledger.get("records", [])
    matches = [r for r in records if r.get("branch_lineage_id") == branch_id]
    if len(matches) != 1:
        raise ValueError("Seleziona un solo record presente nella revisione")
    old = matches[0]
    units = [e for e in evidence if e.source_id == revision.source_id and e.eligible_for_semantic_processing]
    windows = _record_windows({"record_windows": [w.model_dump(mode="json") for w in build_diagnostic_record_windows(units)]})
    envelope = DiagnosticChunkOutput(schema_version="1.1", source_language="en", records=[request.candidate])
    # Human edits cannot manufacture an atomic window or its allow-list.
    payload = request.candidate.model_dump(mode="json")
    payload["record_window_id"] = ""
    payload["allowed_source_anchors"] = []
    envelope = DiagnosticChunkOutput.model_validate({**envelope.model_dump(), "records": [payload]})
    envelope = _bind_candidates_to_record_windows(envelope, windows, strict=False)
    compiled = compile_diagnostic_bundles(envelope, source_type="technical PDF", source_title=revision.source_name,
                                          evidence_units=units, record_windows=windows)
    entry = compiled.report.entries[0].model_dump(mode="json")
    if entry["branch_lineage_id"] != branch_id and any(r.get("branch_lineage_id") == entry["branch_lineage_id"] for r in records):
        raise ValueError("La correzione duplica un record esistente; conserva i due casi per il confronto")
    entry["human_correction_of"] = branch_id
    ledger["records"] = [entry if r is old else r for r in records]
    ledger["candidate_count"] = len(ledger["records"])
    ledger["publish_count"] = sum(r.get("disposition") == "publish" for r in ledger["records"])
    ledger["unresolved_count"] = sum(r.get("disposition") in {"gap", "review"} and not r.get("source_gap_verified") for r in ledger["records"])
    ledger["pending_diagnostic_records"] = ledger["unresolved_count"]
    ledger["disposition_counts"] = dict(Counter(r.get("disposition") for r in ledger["records"]))
    ledger["drop_reasons"] = dict(Counter(reason["code"] for r in ledger["records"] for reason in r.get("drop_reasons", [])))
    ledger["diagnostic_extraction_complete"] = False
    ledger["semantic_completeness_validated"] = False
    now = utc_now()
    event = {"parent_revision_id": revision.source_subgraph_revision_id, "branch_id": branch_id,
             "reviewer": request.reviewer.strip(), "reason": request.reason.strip(), "created_at": now,
             "before": old, "after": entry, "submitted_candidate": request.candidate.model_dump(mode="json"),
             "automatic_approval": False}
    history = [*revision.diagnostic_review_history, event]
    by_id = {e.evidence_id: e for e in units}
    refs = {r.evidence_id: r for r in revision.evidence}
    for evidence_id in entry["evidence_ids"]:
        if evidence_id in by_id:
            e = by_id[evidence_id]
            refs[evidence_id] = GraphEvidenceRef(evidence_id=evidence_id, label=f"Pagina {e.locator.page}",
                                               excerpt=e.locator.quote[:280], locator=e.locator.model_dump(mode="json"))
    relations = [r for r in revision.relations if r.branch_lineage_id != branch_id]
    used = {x for r in relations for x in (r.from_id, r.to_id)}
    removable = set(old.get("emitted_node_ids", [])) - used
    nodes = {n.node_id: n for n in revision.nodes if n.node_id not in removable}
    renames = {}
    for kind, values in compiled.ontology.nodes.items():
        for value in values:
            node_id = value[ID_FIELDS[kind]]
            if node_id in nodes and nodes[node_id].attributes != value:
                # Preserve the shared original and make the correction local
                # to this branch; never rewrite a sibling's attributes.
                renames[node_id] = node_id + "_review_" + hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()[:12]
    evidence_for_node = {}
    for rel in compiled.ontology.relations:
        rel = rel.model_copy(update={"from_id": renames.get(rel.from_id, rel.from_id), "to_id": renames.get(rel.to_id, rel.to_id)})
        ev_refs = [RelationEvidenceRef(evidence_id=e.source_anchor, source_anchor=e.source_anchor, quote=e.quote,
                                      locator=by_id[e.source_anchor].locator.model_dump(mode="json")) for e in rel.evidence]
        ids = sorted({r.evidence_id for r in ev_refs})
        for endpoint in (rel.from_id, rel.to_id):
            evidence_for_node.setdefault(endpoint, set()).update(ids)
        identity = json.dumps([rel.name, rel.from_id, rel.to_id, rel.branch_lineage_id])
        relations.append(SourceGraphRelation(relation_id="rel_" + hashlib.sha256(identity.encode()).hexdigest()[:24],
                                            relation_type=rel.name, from_id=rel.from_id, to_id=rel.to_id,
                                            branch_lineage_id=rel.branch_lineage_id, evidence_ids=ids, evidence_refs=ev_refs))
    for kind, values in compiled.ontology.nodes.items():
        for value in values:
            value = dict(value)
            node_id = renames.get(value[ID_FIELDS[kind]], value[ID_FIELDS[kind]])
            value[ID_FIELDS[kind]] = node_id
            if value.get("material_context") in renames:
                value["material_context"] = renames[value["material_context"]]
            if node_id not in evidence_for_node:
                continue
            node = SourceGraphNode(node_id=node_id, node_type=kind, label=value.get("name") or value.get("code") or node_id,
                                   description=value.get("description", ""), attributes=value,
                                   evidence_ids=sorted(evidence_for_node[node_id]))
            nodes[node_id] = node
    entry["emitted_node_ids"] = sorted({endpoint for rel in relations if rel.branch_lineage_id == entry["branch_lineage_id"] for endpoint in (rel.from_id, rel.to_id)})
    entry["emitted_relations"] = sorted(f"{rel.relation_type}:{rel.from_id}->{rel.to_id}" for rel in relations if rel.branch_lineage_id == entry["branch_lineage_id"])
    # Window-level notifications may also concern untouched sibling records.
    target = old.get("record_window_id") or branch_id
    siblings = [r for r in ledger["records"] if r is not entry and (r.get("record_window_id") or r.get("branch_lineage_id")) == target
                and r.get("disposition") in {"gap", "review"} and not r.get("source_gap_verified")]
    gaps = [g for g in revision.knowledge_gaps if not (g.target_kind == "diagnostic_record" and g.target_id in {branch_id, target} and not siblings)]
    if entry["disposition"] in {"gap", "review"} and not entry["source_gap_verified"]:
        gaps.append(KnowledgeGap(code="pdf_diagnostic_record_review", message="; ".join(r["message"] for r in entry["drop_reasons"]),
                                 target_kind="diagnostic_record", target_id=entry["branch_lineage_id"],
                                 evidence_ids=entry["evidence_ids"], blocking=True, disposition="review"))
    publication = build_publication_graph(candidate_nodes=list(nodes.values()), candidate_relations=relations,
                                          evidence=list(refs.values()), prior_gaps=gaps, canonicalization_report=revision.canonicalization_report)
    validation = _strict_validation(nodes=publication.nodes, relations=publication.relations, evidence=list(refs.values()), require_relation_grounding=True)
    diagnostic_records = [r for r in revision.diagnostic_records if r.record.branch_lineage_id != branch_id]
    if entry.get("validated_record") and entry["disposition"] != "exclude":
        diagnostic_records.append(DiagnosticKnowledgeRecord(record=entry["validated_record"], disposition=entry["disposition"],
                                  review_required=entry["disposition"] in {"gap", "review"} and not entry["source_gap_verified"],
                                  node_ids=entry["emitted_node_ids"]))
    data = revision.model_dump(mode="json")
    data.update(source_subgraph_revision_id=new_id("source_subgraph"), created_at=now, supersedes=revision.source_subgraph_revision_id,
                status="reviewing", approval_decision_id=None, decision_note=None, nodes=publication.nodes, relations=publication.relations,
                evidence=list(refs.values()), evidence_ids=sorted(refs), knowledge_gaps=publication.knowledge_gaps,
                review_queue=publication.review_queue, review_summary=publication.review_summary, projections=publication.projections,
                validation=validation, diagnostic_compilation_ledger=ledger, diagnostic_records=diagnostic_records,
                diagnostic_review_history=history, review_base_config_hash=revision.review_base_config_hash or revision.input_config_hash,
                input_config_hash=hashlib.sha256(json.dumps(history, sort_keys=True).encode()).hexdigest(),
                publication_metrics={**revision.publication_metrics, **publication.metrics,
                    "diagnostic_published_records": ledger["publish_count"], "diagnostic_unresolved_records": ledger["unresolved_count"]},
                approval_eligible=validation.passed and not any(g.blocking or g.review_required for g in publication.knowledge_gaps)
                    and ledger["unresolved_count"] == 0 and bool(ledger.get("diagnostic_contract_processing_complete")))
    return SourceSubgraphRevision.model_validate(data)
