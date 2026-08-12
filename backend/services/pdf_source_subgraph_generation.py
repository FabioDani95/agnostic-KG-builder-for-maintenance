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
    get_diagnostic_escalation_config,
    get_ontology_config,
    get_pdf_generation_cost_guard_config,
    get_pdf_ingestion_config,
    get_resolution_completion_config,
    get_scoping_config,
    get_validation_config,
)
from backend.config import settings
from backend.domain.diagnostic_bundles import DiagnosticChunkOutput
from backend.domain.evidence import EvidenceUnit, QualityFlag
from backend.domain.ids import new_id, utc_now
from backend.domain.locators import PdfLocator
from backend.domain.subgraphs import (
    GraphEvidenceRef,
    KnowledgeGap,
    PdfExtractionScope,
    RelationEvidenceRef,
    SourceGenerationMetrics,
    SourceGenerationStageMetrics,
    SourceGraphNode,
    SourceGraphRelation,
    SourceSubgraphRevision,
    SourceSubgraphStatus,
    TokenCostMetrics,
)
from backend.models import CutPlanRequest, OntologyDraftRequest, OntologyPipelineResponse
from backend.services.cutplan_service import (
    evidence_has_diagnostic_candidate,
    is_diagnostic_section,
    page_has_diagnostic_candidate,
    page_has_diagnostic_record,
)
from backend.services.diagnostic_publication_service import build_publication_graph
from backend.services.llm_gateway import llm_mode
from backend.services.ontology_schema_service import load_ontology_schema, ontology_contract
from backend.services.ontology_workflow import draft_ontology_workflow
from backend.services.run_metrics import MODEL_PRICING, build_metrics_payload
from backend.services.scoping_workflow import create_cut_plan_workflow

PDF_SUBGRAPH_GENERATOR_VERSION = "pdf-g3-typed-diagnostic-publication-v7"

_ID_PROPERTIES = {
    "Asset": "asset_id",
    "Component": "component_id",
    "Symptom": "symptom_id",
    "FailureMode": "failure_mode_id",
    "CorrectiveAction": "action_id",
    "ErrorCode": "error_code_id",
}
_DERIVED_RELATIONS = {"HAS_COMPONENT", "GENERATES_ERROR"}
_EVIDENCE_TEXT_RE = re.compile(
    r"\[\[EVIDENCE_ID:\s*([^\]]+)\]\]\s*(.*?)(?=\n\s*\[\[EVIDENCE_ID:|\Z)",
    flags=re.DOTALL,
)


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
        "diagnostic_contract_sha256": _canonical_hash(
            DiagnosticChunkOutput.model_json_schema()
        ),
        "pricing_catalog": MODEL_PRICING,
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
        # Hash the normalized policy too: defaults applied by the runtime can
        # change model selection/call count even when the raw ontology section
        # omits those keys.
        "diagnostic_escalation": get_diagnostic_escalation_config(),
        "validation": get_validation_config(),
        "confidence": get_confidence_config(),
        "coverage_completion": get_coverage_completion_config(),
        "resolution_completion": get_resolution_completion_config(),
        "pdf_generation_cost_guard": get_pdf_generation_cost_guard_config(),
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


def _canonical_evidence_text(evidence: EvidenceUnit) -> str:
    """Return the complete canonical PDF span, never its display preview."""
    if not isinstance(evidence.locator, PdfLocator):
        return ""
    return str(evidence.content.observation or "").strip() or evidence.locator.quote


def _graph_evidence_locator(evidence: EvidenceUnit) -> dict[str, Any]:
    locator = evidence.locator.model_dump(mode="json")
    if isinstance(evidence.locator, PdfLocator):
        locator["canonical_text"] = _canonical_evidence_text(evidence)
    return locator


def _excerpt(evidence: EvidenceUnit) -> str:
    if isinstance(evidence.locator, PdfLocator):
        # Display preview only. Grounding uses the complete canonical span above.
        return evidence.locator.quote[:2000]
    values = (
        evidence.content.observation,
        evidence.content.cause,
        evidence.content.action,
        evidence.content.error_code,
        evidence.content.measurement,
    )
    return " · ".join(value for value in values if value)[:280]


def _evidence_label(evidence: EvidenceUnit) -> str:
    if isinstance(evidence.locator, PdfLocator):
        return f"Pagina {evidence.locator.page}"
    if evidence.locator.kind == "operator_input":
        return "Identità Asset confermata dall'operatore"
    return "Evidenza canonica"


_TOKEN_COST_FIELDS = (
    "llm_calls",
    "prompt_tokens",
    "cached_prompt_tokens",
    "cache_write_prompt_tokens",
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
        operator_evidence: list[EvidenceUnit] | None = None,
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
        canonical_evidence_ids = {item.evidence_id for item in evidence}
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

        # Scan the immutable all-page inventory, not only the cut-plan subset.
        # Candidate discovery is deliberately high recall; the typed compiler
        # later assigns publish/gap/review/exclude with exact evidence.
        all_candidate_pages = {
            page_number
            for page_number, page in evidence_by_page.items()
            if page_has_diagnostic_candidate(str(page.get("text", "")))
        }
        candidate_evidence_anchors: list[dict[str, Any]] = []
        for page_number, page in sorted(evidence_by_page.items()):
            for match in _EVIDENCE_TEXT_RE.finditer(str(page.get("text", ""))):
                evidence_id = match.group(1).strip()
                evidence_text = match.group(2).strip()
                if (
                    evidence_id in canonical_evidence_ids
                    and evidence_has_diagnostic_candidate(evidence_text)
                ):
                    candidate_evidence_anchors.append({
                        "evidence_id": evidence_id,
                        "page": page_number,
                    })
        # A cause/remedy may occupy its own block and therefore fail the
        # whole-page pair heuristic. Its page is still diagnostic input and
        # receives the same adjacent-page record window.
        all_candidate_pages.update(
            int(item["page"]) for item in candidate_evidence_anchors
        )
        candidate_windows = set(all_candidate_pages)
        for page_number in all_candidate_pages:
            candidate_windows.update({page_number - 1, page_number + 1})
        candidate_windows &= available_pages
        selected_pages = sorted(set(selected_pages) | candidate_windows)

        diagnostic_section_pages: set[int] = set()
        for section in cut_plan.sections:
            covered = set(range(section.page_range.start, section.page_range.end + 1))
            if is_diagnostic_section(section.name):
                diagnostic_section_pages.update(covered)
        content_diagnostic_pages = {
            page_number
            for page_number in selected_pages
            if page_has_diagnostic_record(
                str(evidence_by_page.get(page_number, {}).get("text", ""))
            )
        }
        # A small document with no section plan is kept whole, preserving the
        # legacy fail-safe. For scoped manuals, procedural pages remain useful
        # Component/retrieval context but cannot create diagnostic nodes merely
        # because they describe maintenance, inspection or installation.
        if cut_plan.skipped and not cut_plan.sections:
            diagnostic_pages = selected_pages
        else:
            diagnostic_pages = sorted(
                set(selected_pages)
                & (diagnostic_section_pages | content_diagnostic_pages | candidate_windows)
            )
        # Page roles are allowed to overlap. Adjacent/context pages and a
        # diagnostic section with no explicit record still feed the
        # Component-only structural pass, while explicit record roots stay
        # exclusively in the typed diagnostic contract to avoid duplication.
        diagnostic_record_roots = content_diagnostic_pages | all_candidate_pages
        structural_pages = sorted(set(selected_pages) - diagnostic_record_roots)
        if not diagnostic_pages and not structural_pages:
            diagnostic_pages = selected_pages

        # Scoping may infer document metadata from the manual, but never the
        # workspace-owned Asset used by graph generation.
        store["asset_identity"] = asset
        store["asset_identity_is_canonical"] = True
        store["source_type"] = "technical PDF"
        store["source_title"] = source_title
        store["pdf_extraction_roles"] = {
            "diagnostic_pages": diagnostic_pages,
            "structural_pages": structural_pages,
            "retrieval_pages": physical_pages,
        }
        unreadable_pages = sorted(
            page_number
            for page_number in physical_pages
            if not str(evidence_by_page.get(page_number, {}).get("text", "")).strip()
        )
        diagnostic_scan_report = {
            "physical_pages_scanned": len(physical_pages),
            "candidate_pages": sorted(all_candidate_pages),
            "candidate_context_pages": sorted(candidate_windows - all_candidate_pages),
            "candidate_page_count": len(all_candidate_pages),
            "candidate_evidence_anchors": candidate_evidence_anchors,
            "candidate_evidence_anchor_count": len(candidate_evidence_anchors),
            "unreadable_pages": unreadable_pages,
            "unreadable_page_count": len(unreadable_pages),
        }
        store["diagnostic_candidate_scan"] = diagnostic_scan_report
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
            diagnostic_pages=diagnostic_pages,
            structural_pages=structural_pages,
            retrieval_pages=physical_pages,
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
        result = result.model_copy(update={
            "diagnostic_contract_report": {
                **diagnostic_scan_report,
                **dict(result.diagnostic_contract_report or {}),
            },
        })
        revision = self._to_revision(
            workspace=workspace,
            source=source,
            result=result,
            evidence=[*evidence, *(operator_evidence or [])],
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
        gap_keys: set[tuple[str, str, str, tuple[str, ...]]] = set()

        def add_gap(
            code: str,
            message: str,
            evidence_ids: list[str] | None = None,
            *,
            blocking: bool = False,
            disposition: str = "gap",
            target_kind: str = "",
            target_id: str = "",
        ) -> None:
            ids = tuple(sorted(set(evidence_ids or [])))
            key = (code, target_kind, target_id, ids)
            if key in gap_keys:
                return
            gap_keys.add(key)
            gaps.append(KnowledgeGap(
                code=code[:120],
                message=message[:1000],
                evidence_ids=list(ids),
                stage="pdf_adapter",
                blocking=blocking,
                disposition=disposition,
                target_kind=target_kind,
                target_id=target_id,
            ))

        def resolve(
            page: int,
            quote: str,
            *,
            target: str,
            source_anchor: str = "",
        ) -> list[EvidenceUnit]:
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
                anchored_text = _normalized_text(_canonical_evidence_text(anchored))
                if normalized_quote and normalized_quote in anchored_text:
                    return [anchored]
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
                if normalized_quote in _normalized_text(_canonical_evidence_text(item))
            ]
            if len(exact) != 1:
                add_gap(
                    (
                        "pdf_evidence_quote_ambiguous"
                        if len(exact) > 1
                        else "pdf_evidence_quote_unresolved"
                    ),
                    (
                        f"{target}: la citazione a pagina {page} coincide con più evidenze e l'anchor non la disambigua."
                        if len(exact) > 1
                        else f"{target}: la citazione a pagina {page} non coincide con alcuna evidenza canonica."
                    ),
                )
                return []
            return exact

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
            resolved: dict[str, RelationEvidenceRef] = {}
            for provenance in relation.evidence:
                if provenance.source_page > 0:
                    matches = resolve(
                        provenance.source_page,
                        provenance.quote,
                        target=relation_key,
                        source_anchor=provenance.source_anchor,
                    )
                    for matched in matches:
                        resolved[matched.evidence_id] = RelationEvidenceRef(
                            evidence_id=matched.evidence_id,
                            quote=provenance.quote.strip(),
                            source_anchor=matched.evidence_id,
                            locator=matched.locator.model_dump(mode="json"),
                            support_role="direct",
                        )
                else:
                    add_gap(
                        "pdf_evidence_page_missing",
                        f"{relation_key}: la provenienza non indica una pagina PDF.",
                    )
            relation_drafts.append({
                "index": index,
                "relation": relation,
                "evidence_refs": resolved,
            })
            incident_evidence[relation.from_id].update(resolved)
            incident_evidence[relation.to_id].update(resolved)

        semantic_pages = (
            set(semantic_scope.selected_pages) if semantic_scope is not None else None
        )
        semantic_evidence = [
            item for item in evidence
            if isinstance(item.locator, PdfLocator)
            and (semantic_pages is None or item.locator.page in semantic_pages)
        ]
        all_ids = {item.evidence_id for item in semantic_evidence}
        operator_asset_ids = {
            item.evidence_id
            for item in evidence
            if item.locator.kind == "operator_input"
            and item.asset_id == workspace.asset.asset_id
        }

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
            matches: list[EvidenceUnit] = []
            for item in candidates:
                candidate_text = _normalized_text(_canonical_evidence_text(item))
                for value in query_values:
                    normalized_value = _normalized_text(value)
                    if len(normalized_value) >= 3 and normalized_value in candidate_text:
                        matches.append(item)
                        break
            return {item.evidence_id for item in matches}

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
                    add_gap(
                        "pdf_duplicate_node_id",
                        f"Identificatore di nodo duplicato: {node_id}.",
                        blocking=True,
                        disposition="review",
                        target_kind="node_id",
                        target_id=node_id,
                    )
                    continue
                if node_type == "Asset":
                    if node_id != workspace.asset.asset_id:
                        add_gap(
                            "pdf_asset_identity_mismatch",
                            "L'Asset prodotto dal PDF non coincide con l'identità canonica del workspace.",
                        )
                        continue
                    raw = workspace.asset.model_dump(mode="json")
                resolved = resolve_node_claim(raw)
                if node_type == "Asset":
                    resolved = set(operator_asset_ids)
                    if not resolved:
                        add_gap(
                            "pdf_asset_operator_evidence_missing",
                            "L'Asset canonico non dispone dell'asserzione operatore risolvibile.",
                        )
                if not resolved:
                    resolved.update(incident_evidence.get(node_id, set()))
                ontology_nodes[node_id] = {
                    "node_type": node_type,
                    "raw": raw,
                    "allowed": allowed,
                }
                node_types[node_id] = node_type
                node_evidence[node_id] = resolved

        # Structural root relations are ontology-derived, but their endpoint
        # assertion still supplies exact claim evidence.  Use the Component or
        # ErrorCode evidence—not an arbitrary union of both endpoints.
        for draft in relation_drafts:
            relation = draft["relation"]
            if not draft["evidence_refs"] and relation.name in _DERIVED_RELATIONS:
                for evidence_id in sorted(node_evidence.get(relation.to_id, set())):
                    item = by_id.get(evidence_id)
                    if item is None:
                        continue
                    quote = (
                        item.locator.quote
                        if isinstance(item.locator, PdfLocator)
                        else _excerpt(item)
                    )
                    if not quote.strip():
                        continue
                    draft["evidence_refs"][evidence_id] = RelationEvidenceRef(
                        evidence_id=evidence_id,
                        quote=quote.strip(),
                        source_anchor=evidence_id,
                        locator=item.locator.model_dump(mode="json"),
                        support_role="derived_structural",
                    )
                incident_evidence[relation.from_id].update(draft["evidence_refs"])
                incident_evidence[relation.to_id].update(draft["evidence_refs"])

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
            relation_evidence_refs = list(draft["evidence_refs"].values())
            if not relation_evidence_refs:
                add_gap(
                    "pdf_relation_provenance_unresolved",
                    f"{relation_key} non è collegabile a un'evidenza PDF canonica.",
                )
                continue
            resolved = sorted({item.evidence_id for item in relation_evidence_refs})
            relations.append(SourceGraphRelation(
                relation_id=(
                    "pdfrel_"
                    + _canonical_hash([
                        source.source_id,
                        relation.name,
                        relation.from_type,
                        relation.from_id,
                        relation.to_type,
                        relation.to_id,
                    ])[:20]
                ),
                relation_type=relation.name,
                from_id=relation.from_id,
                to_id=relation.to_id,
                evidence_ids=resolved,
                evidence_refs=relation_evidence_refs,
            ))

        used_ids = {
            evidence_id for node in nodes for evidence_id in node.evidence_ids
        } | {
            evidence_id for relation in relations for evidence_id in relation.evidence_ids
        }
        low_confidence_by_page: dict[int, list[str]] = defaultdict(list)
        for item in evidence:
            if (
                QualityFlag.OCR_LOW_CONFIDENCE in item.quality_flags
                and isinstance(item.locator, PdfLocator)
            ):
                low_confidence_by_page[item.locator.page].append(item.evidence_id)
        if low_confidence_by_page:
            low_confidence_pages = sorted(low_confidence_by_page)
            representative_ids = [
                sorted(low_confidence_by_page[page])[0]
                for page in low_confidence_pages
                if low_confidence_by_page[page]
            ]
            add_gap(
                "pdf_ocr_low_confidence",
                "OCR a bassa confidenza sulle pagine "
                + ", ".join(str(page) for page in low_confidence_pages)
                + "; la copertura non può essere dichiarata completa senza revisione.",
                representative_ids,
                blocking=True,
                disposition="review",
                target_kind="pdf_pages",
                target_id=",".join(str(page) for page in low_confidence_pages),
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
        if result.graph_issues:
            issue_counts: dict[str, int] = defaultdict(int)
            for issue in result.graph_issues:
                issue_counts[issue.issue_type] += 1
            add_gap(
                "pdf_prepublication_graph_issue_summary",
                "Problemi topologici pre-gate (aggregati): "
                + ", ".join(f"{key}={value}" for key, value in sorted(issue_counts.items())),
            )
        if result.suggested_relations:
            add_gap(
                "pdf_prepublication_suggestion_summary",
                f"{len(result.suggested_relations)} relazioni lessicalmente possibili restano escluse perché prive di evidenza diretta.",
            )
        contract_report = dict(result.diagnostic_contract_report or {})
        typed_contract = bool(contract_report.get("schema_version"))
        candidate_page_count = int(contract_report.get("candidate_page_count", 0) or 0)
        unreadable_pages = sorted({
            int(page)
            for page in (contract_report.get("unreadable_pages") or [])
            if int(page) > 0
        })
        if unreadable_pages:
            add_gap(
                "pdf_unreadable_pages",
                "Pagine fisiche senza testo canonico leggibile: "
                + ", ".join(str(page) for page in unreadable_pages),
                blocking=True,
                disposition="review",
                target_kind="pdf_pages",
                target_id=",".join(str(page) for page in unreadable_pages),
            )
        if candidate_page_count and not typed_contract:
            add_gap(
                "pdf_diagnostic_accounting_missing",
                "Sono state rilevate pagine diagnostiche candidate, ma la pipeline non ha "
                "prodotto il ledger record-level richiesto.",
                blocking=True,
                disposition="review",
            )
        if typed_contract:
            parsed = bool(contract_report.get("parsed", True))
            refusal = bool(contract_report.get("refusal", False))
            finish_reason = str(contract_report.get("finish_reason") or "stop")
            candidate_count = int(contract_report.get("candidate_count", 0) or 0)
            if not parsed or refusal or finish_reason not in {"", "stop"}:
                add_gap(
                    "pdf_diagnostic_contract_incomplete",
                    "L'estrazione tipizzata non ha prodotto una risposta completa e validabile "
                    f"(parsed={parsed}, refusal={refusal}, finish_reason={finish_reason or 'unknown'}).",
                    blocking=True,
                    disposition="review",
                )
            if candidate_page_count and candidate_count == 0:
                add_gap(
                    "pdf_diagnostic_candidates_unaccounted",
                    f"Lo scan ad alto recall ha trovato {candidate_page_count} pagina/e candidata/e, "
                    "ma nessun record ha ricevuto una disposizione.",
                    blocking=True,
                    disposition="review",
                )
            entries = contract_report.get("records", []) or []
            accounted_candidate_pages: set[int] = set()
            accounted_evidence_ids: set[str] = set()
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                entry_evidence_ids = {
                    str(value)
                    for value in (entry.get("evidence_ids") or [])
                    if str(value) in by_id
                }
                accounted_evidence_ids.update(entry_evidence_ids)
                for anchor_key in ("record_anchor", "branch_anchor"):
                    anchor = str(entry.get(anchor_key) or "")
                    if anchor in by_id:
                        entry_evidence_ids.add(anchor)
                for evidence_id in entry_evidence_ids:
                    locator = by_id[evidence_id].locator
                    if isinstance(locator, PdfLocator):
                        accounted_candidate_pages.add(locator.page)
                disposition = str(entry.get("disposition") or "")
                if disposition not in {"gap", "review"}:
                    continue
                reasons = [
                    str(reason.get("code") or "unknown")
                    for reason in (entry.get("drop_reasons") or [])
                    if isinstance(reason, dict)
                ]
                evidence_ids = sorted(entry_evidence_ids)
                branch_lineage_id = str(entry.get("branch_lineage_id") or "")
                add_gap(
                    f"pdf_diagnostic_record_{disposition}",
                    "Record diagnostico non pubblicabile senza decisione umana"
                    + (f" ({', '.join(sorted(set(reasons)))})" if reasons else "."),
                    evidence_ids,
                    blocking=True,
                    disposition="review",
                    target_kind="diagnostic_record",
                    target_id=branch_lineage_id,
                )
            candidate_pages = {
                int(page)
                for page in (contract_report.get("candidate_pages") or [])
                if int(page) > 0
            }
            unaccounted_candidate_pages = sorted(candidate_pages - accounted_candidate_pages)
            if unaccounted_candidate_pages:
                add_gap(
                    "pdf_diagnostic_candidate_pages_unaccounted",
                    "Pagine candidate senza record o disposizione esplicita: "
                    + ", ".join(str(page) for page in unaccounted_candidate_pages),
                    blocking=True,
                    disposition="review",
                    target_kind="diagnostic_candidate_pages",
                    target_id=",".join(str(page) for page in unaccounted_candidate_pages),
                )
            candidate_anchor_ids = {
                str(item.get("evidence_id") or "")
                for item in (contract_report.get("candidate_evidence_anchors") or [])
                if isinstance(item, dict) and str(item.get("evidence_id") or "") in by_id
            }
            unaccounted_candidate_anchors = sorted(
                candidate_anchor_ids - accounted_evidence_ids
            )
            if unaccounted_candidate_anchors:
                add_gap(
                    "pdf_diagnostic_candidate_evidence_unaccounted",
                    "Passaggi diagnostici candidati senza record o disposizione esplicita.",
                    unaccounted_candidate_anchors,
                    blocking=True,
                    disposition="review",
                    target_kind="diagnostic_candidate_evidence",
                    target_id=",".join(unaccounted_candidate_anchors),
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
                label=_evidence_label(by_id[evidence_id]),
                excerpt=_excerpt(by_id[evidence_id]),
                locator=_graph_evidence_locator(by_id[evidence_id]),
            )
            for evidence_id in sorted(used_ids)
        ]
        publication = build_publication_graph(
            candidate_nodes=nodes,
            candidate_relations=relations,
            evidence=evidence_refs,
            prior_gaps=gaps,
            canonicalization_report=result.canonicalization_report,
        )
        nodes = publication.nodes
        relations = publication.relations
        gaps = publication.knowledge_gaps
        graph_evidence_ids = {
            evidence_id for node in nodes for evidence_id in node.evidence_ids
        } | {
            evidence_id for relation in relations for evidence_id in relation.evidence_ids
        }
        # A review gap is itself a provenance-bearing assertion about missing
        # or unsafe extraction.  Keep its canonical evidence in the immutable
        # revision even when publication correctly omits the related graph
        # claim; otherwise the reviewer receives an unresolvable gap ID.
        gap_evidence_ids = {
            evidence_id
            for gap in gaps
            for evidence_id in gap.evidence_ids
            if evidence_id in by_id
        }
        used_ids = graph_evidence_ids | gap_evidence_ids
        evidence_refs = [
            GraphEvidenceRef(
                evidence_id=evidence_id,
                label=_evidence_label(by_id[evidence_id]),
                excerpt=_excerpt(by_id[evidence_id]),
                locator=_graph_evidence_locator(by_id[evidence_id]),
            )
            for evidence_id in sorted(used_ids)
        ]
        validation = _strict_validation(
            nodes=nodes,
            relations=relations,
            evidence=evidence_refs,
            require_relation_grounding=True,
        )
        blocking_gaps = [gap for gap in gaps if gap.blocking]
        publication_metrics = {
            **publication.metrics,
            "diagnostic_candidate_pages": candidate_page_count,
            "unreadable_pages": len(unreadable_pages),
            "low_confidence_ocr_pages": len(low_confidence_by_page),
            "diagnostic_candidate_records": int(contract_report.get("candidate_count", 0) or 0),
            "diagnostic_published_records": int(contract_report.get("publish_count", 0) or 0),
            "diagnostic_unresolved_records": int(contract_report.get("unresolved_count", 0) or 0),
            "diagnostic_unaccounted_candidate_pages": len(
                unaccounted_candidate_pages if typed_contract else []
            ),
            "diagnostic_candidate_evidence_anchors": int(
                contract_report.get("candidate_evidence_anchor_count", 0) or 0
            ),
            "diagnostic_unaccounted_candidate_evidence": len(
                unaccounted_candidate_anchors if typed_contract else []
            ),
            "diagnostic_accounting_complete": bool(
                typed_contract
                and bool(contract_report.get("parsed", False))
                and not bool(contract_report.get("refusal", False))
                and str(contract_report.get("finish_reason") or "stop") in {"", "stop"}
                and (not candidate_page_count or int(contract_report.get("candidate_count", 0) or 0) > 0)
                and not int(contract_report.get("unresolved_count", 0) or 0)
                and not (unaccounted_candidate_pages if typed_contract else [])
                and not (unaccounted_candidate_anchors if typed_contract else [])
                and not unreadable_pages
                and not low_confidence_by_page
            ),
        }
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
            pipeline_version=PDF_SUBGRAPH_GENERATOR_VERSION,
            projections=publication.projections,
            review_queue=publication.review_queue,
            review_summary=publication.review_summary,
            publication_metrics=publication_metrics,
            canonicalization_report=result.canonicalization_report,
            approval_eligible=(
                validation.passed
                and not blocking_gaps
                and result.is_schema_compliant
                and result.is_ready_for_human_review
            ),
            supersedes=supersedes,
            created_at=utc_now(),
        )
