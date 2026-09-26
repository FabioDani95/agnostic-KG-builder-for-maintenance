"""V3 inside the application: same revision contract as the v22 builder.

The workspace's canonical evidence is read, the pipeline runs with the gates
configured under ``kg_v3`` in config.yaml, and the result becomes a
SourceSubgraphRevision. Questions still open for a person are listed in the
review queue as questions; system warnings go to the run report only.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from backend.domain.evidence import EvidenceUnit
from backend.domain.locators import PdfLocator
from backend.domain.subgraphs import (
    GraphEvidenceRef,
    RelationEvidenceRef,
    SourceGenerationMetrics,
    SourceGraphNode,
    SourceGraphRelation,
    SourceSubgraphRevision,
    SourceSubgraphStatus,
)
from backend.kg_v3.contracts import Tier
from backend.kg_v3.export import graph_json
from backend.kg_v3.llm import ModelClient
from backend.kg_v3.reader import read_document
from backend.kg_v3.reviewers import InMemoryQuestionStore, render_question
from backend.kg_v3.run import Pipeline, RunConfig

GENERATOR_VERSION = "kg-v3-cite-check-ask-1"
_CODE_FILES = ("contracts.py", "reader.py", "mapper.py", "extractor.py", "checker.py", "merger.py",
               "questions.py", "run.py", "export.py", "prompts.py", "ontology.py", "reviewers.py", "llm.py")


def kg_v3_config() -> dict[str, Any]:
    from backend.app_config import load_config

    return dict(load_config().get("kg_v3") or {})


def kg_v3_enabled() -> bool:
    """KG_PDF_GENERATOR overrides config.yaml (the retained v22 tests pin legacy_v22)."""

    import os

    choice = os.environ.get("KG_PDF_GENERATOR") or kg_v3_config().get("pdf_generator", "legacy_v22")
    return str(choice) == "v3"


def run_config() -> RunConfig:
    raw = kg_v3_config()
    fields = {key: raw[key] for key in RunConfig.model_fields if key in raw}
    return RunConfig(**fields)


def kg_v3_config_hash() -> str:
    from backend.services.ontology_schema_service import ontology_contract

    package = Path(__file__).parent
    code = {name: hashlib.sha256((package / name).read_bytes()).hexdigest() for name in _CODE_FILES}
    payload = {"generator": GENERATOR_VERSION, "config": run_config().model_dump(mode="json"), "code": code,
               "ontology": ontology_contract().sha256}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _evidence_ref(evidence: EvidenceUnit) -> GraphEvidenceRef:
    locator = evidence.locator
    excerpt = locator.quote if isinstance(locator, PdfLocator) else str(evidence.content or "")
    label = f"p. {locator.page}" if isinstance(locator, PdfLocator) else evidence.evidence_id
    return GraphEvidenceRef(evidence_id=evidence.evidence_id, label=label, excerpt=excerpt[:500],
                            locator=locator.model_dump(mode="json"))


class V3PdfSubgraphBuilder:
    async def build_revision(self, *, workspace, source, scope: dict, evidence: list[EvidenceUnit],
                             fingerprint: str, config_hash: str, supersedes: str | None,
                             operator_evidence: list[EvidenceUnit] | None = None) -> SourceSubgraphRevision:
        from backend.domain.ids import new_id, utc_now
        from backend.kg_v3.ontology import load_ontology
        from backend.services.source_subgraph_generation import _strict_validation

        started = time.perf_counter()
        included = {int(page) for page in scope.get("included_pages") or []}
        pdf_evidence = [item for item in evidence if isinstance(item.locator, PdfLocator)
                        and (not included or item.locator.page in included)]
        page_count = max([*included, *(item.locator.page for item in pdf_evidence)] or [1])
        doc = read_document(pdf_evidence, page_count=page_count)
        if not doc.pages:
            raise ValueError("La preparazione PDF non contiene testo utilizzabile")
        config = run_config()
        llm = ModelClient(model=config.model, reasoning_effort=config.reasoning_effort)
        agent_llm = ModelClient(model=config.agent_model, reasoning_effort=config.agent_reasoning_effort)
        store = InMemoryQuestionStore()
        asset = workspace.asset.model_dump(mode="json")
        result = await Pipeline(doc=doc, asset_name=asset.get("name", ""), llm=llm, config=config,
                                agent_llm=agent_llm, human_store=store).run()
        exported = graph_json(result, doc, asset=asset, source_title=source.file_name or "PDF")

        by_id = {item.evidence_id: item for item in [*evidence, *(operator_evidence or [])]}
        asset_evidence = [item.evidence_id for item in operator_evidence or []
                          if item.asset_id == workspace.asset.asset_id]
        root_id = exported["nodes"][0]["id"]
        nodes: list[SourceGraphNode] = []
        for node in exported["nodes"]:
            is_root = node["id"] == root_id
            evidence_ids = asset_evidence if is_root else sorted({item["evidence_id"] for item in node["evidence"]})
            if not evidence_ids:
                continue
            node_id = workspace.asset.asset_id if is_root else node["id"]
            properties = dict(node["properties"])
            if is_root:
                allowed = {name for name, _ in load_ontology().properties.get(node["type"], ())}
                properties = {key: value for key, value in {**asset, "asset_id": node_id}.items()
                              if key in allowed and value not in (None, "")}
            nodes.append(SourceGraphNode(node_id=node_id, node_type=node["type"], label=node["name"] or node_id,
                                         description=str(properties.get("description") or ""),
                                         evidence_ids=evidence_ids, attributes=properties))
        kept = {node.node_id for node in nodes}
        relations: list[SourceGraphRelation] = []
        for edge in exported["edges"]:
            from_id = workspace.asset.asset_id if edge["from"] == root_id else edge["from"]
            if from_id not in kept or edge["to"] not in kept:
                continue
            refs: dict[str, RelationEvidenceRef] = {}
            for occurrence in edge["occurrences"]:
                for item in occurrence["evidence"]:
                    unit = by_id.get(item["evidence_id"])
                    if unit is None or not isinstance(unit.locator, PdfLocator):
                        continue
                    refs[unit.evidence_id] = RelationEvidenceRef(
                        evidence_id=unit.evidence_id, quote=unit.locator.quote, source_anchor=unit.evidence_id,
                        locator=unit.locator.model_dump(mode="json"),
                        support_role="derived_structural" if edge.get("derived") else "direct")
            if not refs:
                continue
            relations.append(SourceGraphRelation(
                relation_id=edge["id"], relation_type=edge["type"], from_id=from_id, to_id=edge["to"],
                evidence_ids=sorted(refs), evidence_refs=list(refs.values()),
                branch_lineage_id=(edge["occurrences"][0].get("record") or "")[:200],
                attributes={"tier": edge["tier"], "trusted": edge["trusted"], "conditions": edge["conditions"],
                            "certificates": [item.get("certificate") for item in edge["occurrences"]
                                             if item.get("certificate")]},
            ))
        used = {evidence_id for item in [*nodes, *relations] for evidence_id in item.evidence_ids}
        evidence_refs = [_evidence_ref(by_id[item]) for item in sorted(used) if item in by_id]
        validation = _strict_validation(nodes=nodes, relations=relations, evidence=evidence_refs,
                                        require_relation_grounding=True)
        open_questions = store.open_questions()
        review_queue = [{
            "item_id": question.question_id, "priority": "question", "code": f"v3_{question.kind.value}",
            "target_kind": "question", "target_id": question.question_id, "message": question.title,
            "question": question.model_dump(mode="json"), "text": render_question(question),
            "evidence_ids": [], "disposition": "review",
        } for question in open_questions]
        tiers = {tier.value: sum(1 for item in relations if item.attributes.get("tier") == tier.value) for tier in Tier}
        return SourceSubgraphRevision(
            source_subgraph_revision_id=new_id("source_subgraph"), workspace_id=workspace.workspace_id,
            source_id=source.source_id, source_name=source.file_name, source_kind=source.source_kind,
            preparation_fingerprint=fingerprint, input_config_hash=config_hash,
            evidence_ids=sorted(used), nodes=nodes, relations=relations, evidence=evidence_refs,
            status=SourceSubgraphStatus.REVIEWING, validation=validation, knowledge_gaps=[],
            pipeline_version=GENERATOR_VERSION, review_queue=review_queue,
            review_summary={"total": len(review_queue), "questions": len(review_queue), "relations_by_tier": tiers},
            publication_metrics={"v3_report": result.report},
            generation_metrics=SourceGenerationMetrics(
                llm_calls=llm.usage.calls + agent_llm.usage.calls,
                prompt_tokens=llm.usage.prompt_tokens + agent_llm.usage.prompt_tokens,
                completion_tokens=llm.usage.completion_tokens + agent_llm.usage.completion_tokens,
                total_tokens=llm.usage.prompt_tokens + llm.usage.completion_tokens
                + agent_llm.usage.prompt_tokens + agent_llm.usage.completion_tokens,
                estimated_cost_usd=round(llm.usage.estimated_cost_usd + agent_llm.usage.estimated_cost_usd, 6),
                duration_seconds=round(time.perf_counter() - started, 3), models=[config.model, config.agent_model],
                execution_mode=GENERATOR_VERSION,
            ),
            approval_eligible=validation.passed,
            supersedes=supersedes, created_at=utc_now(),
        )
