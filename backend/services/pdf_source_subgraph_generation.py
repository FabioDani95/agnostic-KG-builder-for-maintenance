"""Bridge the retained PDF ontology pipeline into source-scoped graph revisions.

The retained ontology workflow is the only semantic PDF engine.  This module
adapts its result to the workspace contract and resolves every graph claim back
to the canonical EvidenceUnit inventory produced during PDF preparation.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
import unicodedata
from collections import defaultdict
from typing import Any

from backend.adapters.pdf import ADAPTER_VERSION, evidence_units_to_legacy_pages, pdf_evidence_sort_key
from backend.app_config import (
    get_agent_config,
    get_confidence_config,
    get_coverage_completion_config,
    get_ontology_config,
    get_pdf_ingestion_config,
    get_resolution_completion_config,
    get_scoping_config,
    get_validation_config,
)
from backend.config import settings
from backend.domain.evidence import EvidenceUnit, QualityFlag
from backend.domain.ids import new_id, utc_now
from backend.domain.locators import PdfLocator
from backend.domain.subgraphs import (
    GraphEvidenceRef,
    KnowledgeGap,
    PdfExtractionScope,
    SourceGenerationMetrics,
    SourceGenerationStageMetrics,
    SourceGraphNode,
    SourceGraphRelation,
    SourceSubgraphRevision,
    SourceSubgraphStatus,
    TokenCostMetrics,
)
from backend.models import CutPlanRequest, OntologyDraftRequest, OntologyPipelineResponse
from backend.services.llm_gateway import llm_mode
from backend.services.ontology_schema_service import load_ontology_schema, ontology_contract
from backend.services.ontology_workflow import draft_ontology_workflow
from backend.services.run_metrics import build_metrics_payload
from backend.services.scoping_workflow import create_cut_plan_workflow

PDF_SUBGRAPH_GENERATOR_VERSION = "retained-pdf-ontology-adapter-v4-canonical-asset"

_ID_PROPERTIES = {
    "Asset": "asset_id",
    "Component": "component_id",
    "Symptom": "symptom_id",
    "FailureMode": "failure_mode_id",
    "CorrectiveAction": "action_id",
    "ErrorCode": "error_code_id",
}
_DERIVED_RELATIONS = {"HAS_COMPONENT", "GENERATES_ERROR"}


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def pdf_preparation_fingerprint(*, source, scope: dict, evidence: list[EvidenceUnit]) -> str:
    """Fingerprint the exact immutable PDF reading used by the semantic core."""
    return _canonical_hash({
        "source_sha256": source.sha256,
        "scope": {
            "scope_id": scope.get("scope_id"),
            "version": scope.get("version"),
            "included_pages": sorted(scope.get("included_pages") or []),
            "excluded_pages": dict(sorted((scope.get("excluded_pages") or {}).items())),
        },
        "evidence": [
            {
                "evidence_id": item.evidence_id,
                "raw_hash": item.provenance_refs[0].raw_hash,
                "locator_hash": item.raw_ref.locator_hash,
                "adapter_version": item.ingestion.adapter_version,
            }
            for item in sorted(evidence, key=lambda value: value.evidence_id)
        ],
    })


def pdf_input_config_hash() -> str:
    """Hash every runtime choice that can alter the retained PDF graph."""
    return _canonical_hash({
        "generator_version": PDF_SUBGRAPH_GENERATOR_VERSION,
        "pdf_adapter_version": ADAPTER_VERSION,
        "ontology_sha256": ontology_contract().sha256,
        "models": {
            "fallback": settings.MODEL_NAME,
            "scoping": {
                "model": _agent_model("scoping"),
                "reasoning_effort": _agent_reasoning_effort("scoping"),
            },
            "ontology": {
                "model": _agent_model("ontology_draft"),
                "reasoning_effort": _agent_reasoning_effort("ontology_draft"),
            },
        },
        "llm_mode": llm_mode(),
        "pdf_ingestion": get_pdf_ingestion_config(),
        "scoping": get_scoping_config(),
        "ontology": get_ontology_config(),
        "validation": get_validation_config(),
        "confidence": get_confidence_config(),
        "coverage_completion": get_coverage_completion_config(),
        "resolution_completion": get_resolution_completion_config(),
    })


def _agent_model(agent_name: str) -> str:
    return str(get_agent_config(agent_name).get("model") or settings.MODEL_NAME).strip()


def _agent_reasoning_effort(agent_name: str) -> str | None:
    value = str(get_agent_config(agent_name).get("reasoning_effort") or "").strip().lower()
    return value or None


def _normalized_text(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[^\w\s.-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(value: str) -> set[str]:
    return {token for token in _normalized_text(value).split() if len(token) > 1}


def _excerpt(evidence: EvidenceUnit) -> str:
    values = (
        evidence.content.observation,
        evidence.content.cause,
        evidence.content.action,
        evidence.content.error_code,
        evidence.content.measurement,
    )
    return " · ".join(value for value in values if value)[:280]


_TOKEN_COST_FIELDS = (
    "llm_calls",
    "prompt_tokens",
    "cached_prompt_tokens",
    "non_cached_prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "estimated_cost_usd",
)


def _token_cost_payload(raw: dict[str, Any] | None) -> dict[str, Any]:
    source = raw or {}
    return {field: source.get(field, 0) or 0 for field in _TOKEN_COST_FIELDS}


def _generation_metrics(store: dict[str, Any], *, duration_seconds: float) -> SourceGenerationMetrics:
    payload = build_metrics_payload(store)
    totals = payload.get("totals") or {}
    stages = {
        name: SourceGenerationStageMetrics(
            **_token_cost_payload(stage),
            duration_seconds=float(stage.get("duration_seconds", 0) or 0),
            models=list(stage.get("models") or []),
            operations=list(stage.get("operations") or []),
            details=dict(stage.get("details") or {}),
        )
        for name, stage in (payload.get("stages") or {}).items()
    }
    by_model = {
        name: TokenCostMetrics(**_token_cost_payload(model_metrics))
        for name, model_metrics in (totals.get("by_model") or {}).items()
    }
    models = sorted({
        model
        for stage in stages.values()
        for model in stage.models
        if model
    })
    return SourceGenerationMetrics(
        **_token_cost_payload(totals),
        duration_seconds=round(max(0.0, duration_seconds), 3),
        models=models,
        by_model=by_model,
        stages=stages,
        execution_mode=llm_mode(),
    )


class PdfSourceSubgraphBuilder:
    """Run the local PDF core and produce one immutable target revision."""

    async def build_revision(
        self,
        *,
        workspace,
        source,
        scope: dict,
        evidence: list[EvidenceUnit],
        fingerprint: str,
        config_hash: str,
        supersedes: str | None,
    ) -> SourceSubgraphRevision:
        build_started_at = time.perf_counter()
        evidence_pages = evidence_units_to_legacy_pages(evidence)
        included_pages = sorted({int(page) for page in scope.get("included_pages") or []})
        if not evidence_pages:
            raise ValueError("La preparazione PDF non contiene testo utilizzabile")

        # The retained scoping workflow reasons in physical PDF page numbers.
        # Preserve empty physical pages in that projection so page offsets and
        # section ranges cannot collapse when a page has no semantic evidence.
        evidence_by_page = {int(page["page_number"]): page for page in evidence_pages}
        physical_pages = included_pages or sorted(evidence_by_page)
        pages = [
            evidence_by_page.get(page_number, {
                "page_number": page_number,
                "text": "",
                "text_source": "empty",
            })
            for page_number in physical_pages
        ]

        asset = workspace.asset.model_dump(mode="json")
        source_title = source.file_name or "Documento PDF"
        store = {
            "pages": pages,
            "filename": source_title,
            "source_type": "technical PDF",
            "source_title": source_title,
            "asset_identity": asset,
            "asset_identity_is_canonical": True,
        }

        try:
            cut_plan = await asyncio.to_thread(
                create_cut_plan_workflow,
                store,
                CutPlanRequest(
                    pdf_id=source.source_id,
                    model_name=_agent_model("scoping"),
                    reasoning_effort=_agent_reasoning_effort("scoping"),
                    discover_asset_identity=False,
                ),
            )
        except Exception as exc:
            raise ValueError(
                "La segmentazione diagnostica del PDF non è riuscita"
            ) from exc

        available_pages = {int(page["page_number"]) for page in pages}
        selected_pages = sorted({
            int(page) for page in cut_plan.pages_to_keep
            if int(page) in available_pages
        })
        if not selected_pages:
            raise ValueError(
                "La segmentazione diagnostica non ha selezionato pagine elaborabili"
            )

        # Scoping may infer document metadata from the manual, but never the
        # workspace-owned Asset used by graph generation.
        store["asset_identity"] = asset
        store["asset_identity_is_canonical"] = True
        store["source_type"] = "technical PDF"
        store["source_title"] = source_title
        semantic_scope = PdfExtractionScope(
            total_pages=len(physical_pages),
            selected_pages=selected_pages,
            unselected_pages=sorted(set(physical_pages) - set(selected_pages)),
            sections=[
                {
                    "name": section.name,
                    "start_page": section.page_range.start,
                    "end_page": section.page_range.end,
                    "source": section.source,
                }
                for section in cut_plan.sections
            ],
            page_offset=cut_plan.page_offset,
            skipped=cut_plan.skipped,
        )
        try:
            result = await draft_ontology_workflow(
                store,
                OntologyDraftRequest(
                    pdf_id=source.source_id,
                    source_type="technical PDF",
                    source_title=source_title,
                    model_name=_agent_model("ontology_draft"),
                    reasoning_effort=_agent_reasoning_effort("ontology_draft"),
                    pages_to_keep=selected_pages,
                    target_language="en",
                ),
            )
        except Exception as exc:
            detail = str(getattr(exc, "detail", "") or str(exc)).strip()
            suffix = f": {detail}" if detail else ""
            raise ValueError(
                f"La costruzione semantica del PDF non è riuscita{suffix}"
            ) from exc
        revision = self._to_revision(
            workspace=workspace,
            source=source,
            result=result,
            evidence=evidence,
            fingerprint=fingerprint,
            config_hash=config_hash,
            supersedes=supersedes,
            semantic_scope=semantic_scope,
        )
        generation_metrics = _generation_metrics(
            store,
            duration_seconds=time.perf_counter() - build_started_at,
        )
        return revision.model_copy(update={"generation_metrics": generation_metrics})

    def _to_revision(
        self,
        *,
        workspace,
        source,
        result: OntologyPipelineResponse,
        evidence: list[EvidenceUnit],
        fingerprint: str,
        config_hash: str,
        supersedes: str | None,
        semantic_scope: PdfExtractionScope | None = None,
        generation_metrics: SourceGenerationMetrics | None = None,
    ) -> SourceSubgraphRevision:
        # Imported lazily to keep this adapter independent from orchestration
        # while sharing the exact strict validator used by structured sources.
        from backend.services.source_subgraph_generation import _strict_validation

        schema = load_ontology_schema()
        node_defs = {item.name: item for item in schema.nodes}
        relation_defs = {item.name: item for item in schema.relations}
        by_id = {item.evidence_id: item for item in evidence}
        by_anchor = dict(by_id)
        by_page: dict[int, list[EvidenceUnit]] = defaultdict(list)
        for item in evidence:
            if isinstance(item.locator, PdfLocator):
                by_page[item.locator.page].append(item)
        for page_items in by_page.values():
            page_items.sort(key=pdf_evidence_sort_key)

        gaps: list[KnowledgeGap] = []
        gap_keys: set[tuple[str, tuple[str, ...]]] = set()

        def add_gap(code: str, message: str, evidence_ids: list[str] | None = None) -> None:
            ids = tuple(sorted(set(evidence_ids or [])))
            key = (code, ids)
            if key in gap_keys:
                return
            gap_keys.add(key)
            gaps.append(KnowledgeGap(code=code[:120], message=message[:1000], evidence_ids=list(ids)))

        def resolve(
            page: int,
            quote: str,
            *,
            target: str,
            source_anchor: str = "",
        ) -> list[str]:
            candidates = by_page.get(page, [])
            if not candidates:
                add_gap(
                    "pdf_evidence_page_unavailable",
                    f"{target}: pagina {page} non presente nello scope PDF attivo.",
                )
                return []
            anchor = str(source_anchor or "").strip()
            anchored = by_anchor.get(anchor) if anchor else None
            normalized_quote = _normalized_text(quote)
            if anchored is not None and (
                isinstance(anchored.locator, PdfLocator)
                and anchored.locator.page == page
            ):
                anchored_text = _normalized_text(anchored.locator.quote)
                anchor_tokens = _tokens(quote)
                anchor_score = (
                    len(anchor_tokens & _tokens(anchored.locator.quote))
                    / max(1, len(anchor_tokens))
                )
                if normalized_quote and (
                    normalized_quote in anchored_text
                    or anchored_text in normalized_quote
                    or anchor_score >= 0.8
                ):
                    return [anchored.evidence_id]
            if not normalized_quote:
                add_gap(
                    "pdf_evidence_anchor_unresolved" if anchor else "pdf_evidence_quote_missing",
                    (
                        f"{target}: l'anchor {anchor} non identifica un'evidenza della pagina {page}."
                        if anchor
                        else f"{target}: la pipeline ha indicato pagina {page} senza una citazione verificabile."
                    ),
                )
                return []

            exact = [
                item for item in candidates
                if normalized_quote in _normalized_text(item.locator.quote)
                or _normalized_text(item.locator.quote) in normalized_quote
            ]
            matches = exact
            if not matches:
                quote_tokens = _tokens(quote)
                scored: list[tuple[float, EvidenceUnit]] = []
                for item in candidates:
                    candidate_tokens = _tokens(item.locator.quote)
                    denominator = max(1, len(quote_tokens))
                    score = len(quote_tokens & candidate_tokens) / denominator
                    if score >= 0.8:
                        scored.append((score, item))
                if scored:
                    best = max(score for score, _ in scored)
                    matches = [item for score, item in scored if score == best]
            if not matches:
                add_gap(
                    "pdf_evidence_quote_unresolved",
                    f"{target}: la citazione a pagina {page} non coincide con alcuna evidenza canonica.",
                )
                return []
            return sorted({item.evidence_id for item in matches})

        relation_drafts: list[dict[str, Any]] = []
        incident_evidence: dict[str, set[str]] = defaultdict(set)
        for index, relation in enumerate(result.ontology.relations, start=1):
            relation_key = (
                f"{relation.name} {relation.from_type}:{relation.from_id}"
                f" → {relation.to_type}:{relation.to_id}"
            )
            if relation.name not in relation_defs:
                add_gap(
                    "pdf_unknown_relation_type",
                    f"Relazione non prevista dall'ontologia: {relation_key}.",
                )
                continue
            resolved: set[str] = set()
            for provenance in relation.evidence:
                if provenance.source_page > 0:
                    resolved.update(resolve(
                        provenance.source_page,
                        provenance.quote,
                        target=relation_key,
                        source_anchor=provenance.source_anchor,
                    ))
                else:
                    add_gap(
                        "pdf_evidence_page_missing",
                        f"{relation_key}: la provenienza non indica una pagina PDF.",
                    )
            relation_drafts.append({
                "index": index,
                "relation": relation,
                "evidence_ids": resolved,
            })
            incident_evidence[relation.from_id].update(resolved)
            incident_evidence[relation.to_id].update(resolved)

        semantic_pages = (
            set(semantic_scope.selected_pages) if semantic_scope is not None else None
        )
        semantic_evidence = [
            item for item in evidence
            if semantic_pages is None
            or (
                isinstance(item.locator, PdfLocator)
                and item.locator.page in semantic_pages
            )
        ]
        clean_ids = {
            item.evidence_id for item in semantic_evidence
            if QualityFlag.OCR_LOW_CONFIDENCE not in item.quality_flags
        }
        all_ids = {item.evidence_id for item in semantic_evidence}

        def resolve_node_claim(raw: dict[str, Any]) -> set[str]:
            """Ground standalone nodes by label/content, never by page alone."""
            page = 0
            for key in ("evidence_page", "source_page"):
                try:
                    page = int(raw.get(key) or 0)
                except (TypeError, ValueError):
                    page = 0
                if page > 0:
                    break
            if page <= 0:
                match = re.search(
                    r"\b(?:page|pagina|p\.?)\s*[:#-]*\s*(\d+)\b",
                    str(raw.get("source_reference") or ""),
                    re.I,
                )
                page = int(match.group(1)) if match else 0

            candidates = by_page.get(page, []) if page > 0 else semantic_evidence
            candidates = [item for item in candidates if item.evidence_id in all_ids]
            query_values = [
                str(raw.get(key) or "").strip()
                for key in ("name", "code", "instruction_text", "description")
                if str(raw.get(key) or "").strip()
            ]
            scored: list[tuple[float, EvidenceUnit]] = []
            for item in candidates:
                candidate_text = _normalized_text(item.locator.quote)
                candidate_tokens = _tokens(item.locator.quote)
                best_score = 0.0
                for value in query_values:
                    normalized_value = _normalized_text(value)
                    if len(normalized_value) >= 3 and normalized_value in candidate_text:
                        best_score = 1.0
                        break
                    value_tokens = _tokens(value)
                    if value_tokens:
                        best_score = max(
                            best_score,
                            len(value_tokens & candidate_tokens) / len(value_tokens),
                        )
                if best_score >= 0.75:
                    scored.append((best_score, item))
            if not scored:
                return set()
            best = max(score for score, _ in scored)
            return {item.evidence_id for score, item in scored if score == best}

        ontology_nodes: dict[str, dict[str, Any]] = {}
        node_types: dict[str, str] = {}
        node_evidence: dict[str, set[str]] = {}
        asset_items = result.ontology.nodes.get("Asset", []) or []
        if len(asset_items) != 1:
            add_gap(
                "pdf_asset_cardinality",
                "La pipeline PDF deve produrre esattamente l'Asset canonico del workspace.",
            )

        for node_type, items in result.ontology.nodes.items():
            if node_type not in node_defs:
                add_gap("pdf_unknown_node_type", f"Tipo di nodo non previsto: {node_type}.")
                continue
            allowed = {item.name for item in node_defs[node_type].properties}
            id_property = _ID_PROPERTIES[node_type]
            for raw in items:
                node_id = str(raw.get(id_property) or raw.get("id") or "").strip()
                if not node_id:
                    add_gap("pdf_node_id_missing", f"Un nodo {node_type} non ha un identificatore.")
                    continue
                if node_id in ontology_nodes:
                    add_gap("pdf_duplicate_node_id", f"Identificatore di nodo duplicato: {node_id}.")
                    continue
                if node_type == "Asset":
                    if node_id != workspace.asset.asset_id:
                        add_gap(
                            "pdf_asset_identity_mismatch",
                            "L'Asset prodotto dal PDF non coincide con l'identità canonica del workspace.",
                        )
                        continue
                    raw = workspace.asset.model_dump(mode="json")
                resolved = set(incident_evidence.get(node_id, set()))
                if not resolved:
                    resolved.update(resolve_node_claim(raw))
                if node_type == "Asset" and not resolved:
                    ordered_semantic = sorted(semantic_evidence, key=pdf_evidence_sort_key)
                    fallback = next(
                        (item for item in ordered_semantic if item.evidence_id in clean_ids),
                        ordered_semantic[0] if ordered_semantic else None,
                    )
                    if fallback is not None:
                        resolved.add(fallback.evidence_id)
                ontology_nodes[node_id] = {
                    "node_type": node_type,
                    "raw": raw,
                    "allowed": allowed,
                }
                node_types[node_id] = node_type
                node_evidence[node_id] = resolved

        # Structural relations are deterministically added by the retained
        # core. They inherit endpoint provenance, never a fabricated quote.
        for draft in relation_drafts:
            relation = draft["relation"]
            if not draft["evidence_ids"] and relation.name in _DERIVED_RELATIONS:
                draft["evidence_ids"].update(node_evidence.get(relation.from_id, set()))
                draft["evidence_ids"].update(node_evidence.get(relation.to_id, set()))
                incident_evidence[relation.from_id].update(draft["evidence_ids"])
                incident_evidence[relation.to_id].update(draft["evidence_ids"])

        # A node may only enter the target graph when at least one canonical
        # EvidenceUnit can be shown to the reviewer.
        nodes: list[SourceGraphNode] = []
        included_node_ids: set[str] = set()
        for node_id in sorted(ontology_nodes, key=lambda value: (node_types[value], value)):
            details = ontology_nodes[node_id]
            resolved = node_evidence[node_id] | incident_evidence.get(node_id, set())
            if not resolved:
                add_gap(
                    "pdf_node_provenance_unresolved",
                    f"{details['node_type']}:{node_id} non è collegabile a un'evidenza PDF canonica.",
                )
                continue
            raw = details["raw"]
            attributes = {
                key: value for key, value in raw.items()
                if key in details["allowed"]
            }
            nodes.append(SourceGraphNode(
                node_id=node_id,
                node_type=details["node_type"],
                label=str(raw.get("name") or raw.get("code") or node_id),
                description=str(raw.get("description") or ""),
                evidence_ids=sorted(resolved),
                attributes=attributes,
            ))
            included_node_ids.add(node_id)

        relations: list[SourceGraphRelation] = []
        for draft in relation_drafts:
            relation = draft["relation"]
            relation_key = f"{relation.name}:{relation.from_id}:{relation.to_id}"
            if relation.from_id not in included_node_ids or relation.to_id not in included_node_ids:
                add_gap(
                    "pdf_relation_endpoint_omitted",
                    f"{relation_key} esclusa perché almeno un estremo non ha provenienza risolvibile.",
                )
                continue
            resolved = sorted(draft["evidence_ids"])
            if not resolved:
                add_gap(
                    "pdf_relation_provenance_unresolved",
                    f"{relation_key} non è collegabile a un'evidenza PDF canonica.",
                )
                continue
            relations.append(SourceGraphRelation(
                relation_id=(
                    f"pdfrel_{_canonical_hash([source.source_id, relation_key, draft['index']])[:20]}"
                ),
                relation_type=relation.name,
                from_id=relation.from_id,
                to_id=relation.to_id,
                evidence_ids=resolved,
            ))

        used_ids = {
            evidence_id for node in nodes for evidence_id in node.evidence_ids
        } | {
            evidence_id for relation in relations for evidence_id in relation.evidence_ids
        }
        for evidence_id in sorted(used_ids):
            item = by_id[evidence_id]
            if QualityFlag.OCR_LOW_CONFIDENCE in item.quality_flags:
                add_gap(
                    "pdf_ocr_low_confidence",
                    "Una o più asserzioni dipendono da OCR a bassa confidenza "
                    "e richiedono una fonte verificabile.",
                    [evidence_id],
                )

        for issue in result.schema_issues:
            add_gap(f"pdf_schema_{issue.code}", issue.message)
        for field in result.human_required_fields:
            add_gap(
                "pdf_human_field_required",
                f"{field.target_type}:{field.target_id} richiede {field.property_name}: {field.prompt}",
            )
        for issue in result.semantic_issues:
            code = str(issue.code or "semantic_issue")
            if any(token in code.casefold() for token in ("ground", "evidence", "unresolved")):
                add_gap(f"pdf_semantic_{code}", issue.message)
        for issue in result.graph_issues:
            add_gap(f"pdf_graph_{issue.issue_type}", issue.description)
        for suggestion in result.suggested_relations:
            add_gap(
                "pdf_suggested_relation",
                f"Relazione da verificare: {suggestion.relation_name} "
                f"{suggestion.from_type}:{suggestion.from_id} → "
                f"{suggestion.to_type}:{suggestion.to_id}.",
            )
        if (
            not result.is_schema_compliant
            and not result.schema_issues
            and not result.human_required_fields
        ):
            add_gap(
                "pdf_pipeline_schema_noncompliant",
                "La pipeline PDF ha dichiarato il payload non conforme allo schema.",
            )
        if not result.is_ready_for_human_review:
            add_gap(
                "pdf_pipeline_not_reviewable",
                "La pipeline PDF non considera ancora il risultato pronto per la revisione umana.",
            )
        if str(result.status).strip().lower() == "blocked":
            add_gap("pdf_pipeline_blocked", "La pipeline PDF ha restituito uno stato bloccato.")
        if not nodes:
            add_gap("pdf_empty_graph", "La pipeline PDF non ha prodotto nodi con provenienza verificabile.")

        evidence_refs = [
            GraphEvidenceRef(
                evidence_id=evidence_id,
                label=f"Pagina {by_id[evidence_id].locator.page}",
                excerpt=_excerpt(by_id[evidence_id]),
                locator=by_id[evidence_id].locator.model_dump(mode="json"),
            )
            for evidence_id in sorted(used_ids)
        ]
        validation = _strict_validation(nodes=nodes, relations=relations, evidence=evidence_refs)
        return SourceSubgraphRevision(
            source_subgraph_revision_id=new_id("source_subgraph"),
            workspace_id=workspace.workspace_id,
            source_id=source.source_id,
            source_name=source.file_name or "Documento PDF",
            source_kind=source.source_kind,
            preparation_fingerprint=fingerprint,
            input_config_hash=config_hash,
            evidence_ids=sorted(used_ids),
            nodes=nodes,
            relations=relations,
            evidence=evidence_refs,
            status=SourceSubgraphStatus.REVIEWING,
            validation=validation,
            knowledge_gaps=gaps,
            pdf_extraction_scope=semantic_scope,
            generation_metrics=generation_metrics,
            approval_eligible=(
                validation.passed
                and not gaps
                and result.is_schema_compliant
                and result.is_ready_for_human_review
            ),
            supersedes=supersedes,
            created_at=utc_now(),
        )
