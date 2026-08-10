"""Source-scoped graph generation for structured and PDF evidence."""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from typing import Any

from backend.domain.evidence import EvidenceUnit
from backend.domain.ids import new_id, utc_now
from backend.domain.sources import SourceKind, SourceState
from backend.domain.subgraphs import (
    CrossSourceMatch,
    G3SourceView,
    G3WorkspaceView,
    GraphEvidenceRef,
    GraphValidationIssue,
    GraphValidationReport,
    KnowledgeGap,
    MergeBarrierView,
    SourceGraphNode,
    SourceGraphRelation,
    SourceSubgraphRevision,
    SourceSubgraphStatus,
)
from backend.services.ontology_schema_service import load_ontology_schema, ontology_contract
from backend.services.pdf_source_subgraph_generation import (
    PdfSourceSubgraphBuilder,
    pdf_input_config_hash,
    pdf_preparation_fingerprint,
)
from backend.services.structured_preparation import CONFIRMED_PROFILES_SQL, mapping_fingerprint
from backend.storage.database import get_database
from backend.storage.repositories.evidence import EvidenceRepository
from backend.storage.repositories.sources import SourceNotFoundError, SourceRepository
from backend.storage.repositories.structured import StructuredPreparationRepository
from backend.storage.repositories.subgraphs import SourceSubgraphRepository
from backend.storage.repositories.workspaces import WorkspaceRepository

# v4: a mapped cell is one claim; the generator no longer splits on "|".
# The version is part of input_config_hash, so subgraphs built under v3 no
# longer match and are rebuilt instead of silently reused.
GENERATOR_VERSION = "structured-direct-graph-v4-cell-per-claim"
STRUCTURED_GRAPH_KINDS = {SourceKind.CSV, SourceKind.XLSX, SourceKind.JSON, SourceKind.JSONL}
GRAPH_KINDS = STRUCTURED_GRAPH_KINDS | {SourceKind.PDF}
_PDF_GENERATION_LOCKS: dict[str, asyncio.Lock] = {}


class SourceSubgraphGenerationError(RuntimeError):
    pass


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalized_label(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"[^\w\s-]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def _values(value: str) -> list[str]:
    """One filled cell of a mapped column is one claim.

    The generator used to split on ``|``, treating it as a multi-value
    separator.  That was an assumption about a character, not a reading of the
    data: a pipe written inside a free-text cell was silently turned into two
    graph elements, and nothing said so.  A cell is now taken whole — if its
    text needs cleaning, that is a data problem, and it stays visible as one.

    A role is held by at most one column (see
    ``StructuredProfileRepository.set_column_role``), so the joined evidence
    field this reads carries a single cell.
    """
    text = str(value or "").strip()
    return [text] if text else []


def _stable_id(prefix: str, *parts: str) -> str:
    return f"{prefix}_{_canonical_hash([*parts])[:20]}"


def _locator_label(locator: dict[str, Any]) -> str:
    kind = locator.get("kind")
    if kind == "table_row":
        start = locator.get("line_start") or locator.get("row") or locator.get("row_index")
        end = locator.get("line_end") or start
        return f"Righe {start}–{end}" if start and end and start != end else f"Riga {start or '?'}"
    if kind == "pdf_page":
        return f"Pagina {locator.get('page') or locator.get('page_number') or '?'}"
    if kind == "json_path":
        return str(locator.get("json_path") or "Elemento JSON")
    return "Posizione originale"


def _excerpt(evidence: EvidenceUnit) -> str:
    values = [
        evidence.content.observation,
        evidence.content.cause,
        evidence.content.action,
        evidence.content.error_code,
        evidence.content.measurement,
    ]
    return " · ".join(value for value in values if value)[:280]


_ID_PROPERTIES = {
    "Asset": "asset_id",
    "Component": "component_id",
    "Symptom": "symptom_id",
    "FailureMode": "failure_mode_id",
    "CorrectiveAction": "action_id",
    "ErrorCode": "error_code_id",
}


def _is_populated(value: Any) -> bool:
    if value is None:
        return False
    return bool(value.strip()) if isinstance(value, str) else True


def _strict_validation(
    *,
    nodes: list[SourceGraphNode],
    relations: list[SourceGraphRelation],
    evidence: list[GraphEvidenceRef],
    unresolved_mapping_diagnostics: int = 0,
) -> GraphValidationReport:
    """Validate the exact source-subgraph payload, not a parallel export draft."""
    schema = load_ontology_schema()
    node_defs = {item.name: item for item in schema.nodes}
    relation_defs = {item.name: item for item in schema.relations}
    issues: list[GraphValidationIssue] = []
    required_total = required_present = extra_properties = duplicate_ids = 0
    ids_by_type: dict[str, set[str]] = defaultdict(set)
    node_type_by_id = {node.node_id: node.node_type for node in nodes}

    for node in nodes:
        definition = node_defs[node.node_type]
        allowed = {property_def.name for property_def in definition.properties}
        for property_name in sorted(set(node.attributes) - allowed):
            extra_properties += 1
            issues.append(GraphValidationIssue(
                code="extra_property",
                message=f"{node.node_type} contains undeclared property {property_name}.",
                node_type=node.node_type,
                node_id=node.node_id,
                property_name=property_name,
            ))
        for property_def in definition.properties:
            value = node.attributes.get(property_def.name)
            if property_def.required:
                required_total += 1
                if _is_populated(value):
                    required_present += 1
                else:
                    issues.append(GraphValidationIssue(
                        code="missing_required_property",
                        message=f"{node.node_type} is missing required property {property_def.name}.",
                        node_type=node.node_type,
                        node_id=node.node_id,
                        property_name=property_def.name,
                    ))
            if property_def.unique and _is_populated(value):
                identifier = str(value).strip()
                if identifier in ids_by_type[node.node_type]:
                    duplicate_ids += 1
                    issues.append(GraphValidationIssue(
                        code="duplicate_id",
                        message=f"Duplicate {node.node_type} identifier {identifier}.",
                        node_type=node.node_type,
                        node_id=node.node_id,
                        property_name=property_def.name,
                    ))
                ids_by_type[node.node_type].add(identifier)

    domain_range_errors = endpoint_errors = 0
    for relation in relations:
        definition = relation_defs.get(relation.relation_type)
        from_type = node_type_by_id.get(relation.from_id)
        to_type = node_type_by_id.get(relation.to_id)
        if definition is None or from_type != definition.domain or to_type != definition.range:
            domain_range_errors += 1
            issues.append(GraphValidationIssue(
                code="relation_domain_range_mismatch",
                message=f"{relation.relation_type} does not match its ontology domain and range.",
                node_type="relation",
            ))
        if relation.from_id not in node_type_by_id:
            endpoint_errors += 1
            issues.append(GraphValidationIssue(
                code="relation_missing_source",
                message=f"{relation.relation_type} references a missing source node.",
                node_type="relation",
            ))
        if relation.to_id not in node_type_by_id:
            endpoint_errors += 1
            issues.append(GraphValidationIssue(
                code="relation_missing_target",
                message=f"{relation.relation_type} references a missing target node.",
                node_type="relation",
            ))

    graph_invariant_errors = 0
    asset_ids = sorted(
        node.node_id for node in nodes if node.node_type == "Asset"
    )
    if len(asset_ids) != 1:
        graph_invariant_errors += 1
        issues.append(GraphValidationIssue(
            code="asset_cardinality",
            message=f"The source graph must contain exactly one Asset; found {len(asset_ids)}.",
            node_type="Asset",
        ))

    has_component_pairs = {
        (relation.from_id, relation.to_id)
        for relation in relations
        if relation.relation_type == "HAS_COMPONENT"
    }
    canonical_asset_id = asset_ids[0] if len(asset_ids) == 1 else None
    for component in (node for node in nodes if node.node_type == "Component"):
        if canonical_asset_id is None or (
            canonical_asset_id,
            component.node_id,
        ) not in has_component_pairs:
            graph_invariant_errors += 1
            issues.append(GraphValidationIssue(
                code="component_not_owned_by_asset",
                message=(
                    f"Component {component.node_id} must be connected to the canonical "
                    "Asset by HAS_COMPONENT."
                ),
                node_type="Component",
                node_id=component.node_id,
            ))

    evidence_ids = {item.evidence_id for item in evidence}
    referenced_evidence_ids = {
        evidence_id for node in nodes for evidence_id in node.evidence_ids
    } | {
        evidence_id for relation in relations for evidence_id in relation.evidence_ids
    }
    provenance_total = len(referenced_evidence_ids)
    provenance_resolvable = sum(evidence_id in evidence_ids for evidence_id in referenced_evidence_ids)
    for evidence_id in sorted(referenced_evidence_ids - evidence_ids):
        issues.append(GraphValidationIssue(
            code="unresolvable_provenance",
            message=f"Graph claim references unavailable evidence {evidence_id}.",
            node_type="provenance",
        ))
    for evidence_ref in evidence:
        if not evidence_ref.locator:
            issues.append(GraphValidationIssue(
                code="missing_provenance_locator",
                message=f"Evidence {evidence_ref.evidence_id} has no source locator.",
                node_type="provenance",
            ))
    if unresolved_mapping_diagnostics:
        issues.append(GraphValidationIssue(
            code="unresolved_mapping_diagnostics",
            message="Diagnostic columns still require an explicit mapping decision.",
            node_type="mapping",
        ))
    passed = (
        required_total == required_present
        and extra_properties == 0
        and domain_range_errors == 0
        and endpoint_errors == 0
        and graph_invariant_errors == 0
        and duplicate_ids == 0
        and provenance_total == provenance_resolvable
        and all(item.locator for item in evidence)
        and unresolved_mapping_diagnostics == 0
    )
    return GraphValidationReport(
        required_properties_total=required_total,
        required_properties_present=required_present,
        extra_properties=extra_properties,
        domain_range_errors=domain_range_errors,
        endpoint_errors=endpoint_errors,
        graph_invariant_errors=graph_invariant_errors,
        duplicate_ids=duplicate_ids,
        provenance_total=provenance_total,
        provenance_resolvable=provenance_resolvable,
        unresolved_mapping_diagnostics=unresolved_mapping_diagnostics,
        passed=passed,
        issues=issues,
    )


class SourceSubgraphGenerationService:
    def __init__(self) -> None:
        self.workspaces = WorkspaceRepository()
        self.sources = SourceRepository()
        self.profiles = StructuredPreparationRepository()
        self.evidence = EvidenceRepository()
        self.subgraphs = SourceSubgraphRepository()

    def snapshot(self, workspace_id: str) -> G3WorkspaceView:
        workspace = self.workspaces.get_by_id(workspace_id)
        if workspace is None:
            raise LookupError(workspace_id)
        sources = [
            item for item in self.sources.list_for_workspace(workspace_id)
            if item.source_kind is not SourceKind.OPERATOR_INPUT and item.status is not SourceState.EXCLUDED
        ]
        profiles = {item.source_id: item for item in self.profiles.profiles_for_workspace(workspace_id)}
        confirmed = self._confirmed_profiles(workspace_id)
        revisions = self.subgraphs.current_for_workspace(workspace_id)
        views: list[G3SourceView] = []
        eligible_ids: list[str] = []

        for source in sources:
            name = source.file_name or "Fonte"
            if source.source_kind is SourceKind.PDF:
                eligible_ids.append(source.source_id)
                scope = self.evidence.current_scope(source.source_id)
                source_evidence = [
                    item for item in self.evidence.list_evidence(
                        workspace_id=workspace_id, source_id=source.source_id,
                    )
                    if item.eligible_for_semantic_processing
                ]
                if scope is None or not source_evidence:
                    views.append(G3SourceView(
                        source_id=source.source_id,
                        source_name=name,
                        source_kind=source.source_kind,
                        state="waiting",
                        message="Attendi che la preparazione del PDF produca evidenze utilizzabili.",
                    ))
                    continue
                revision = revisions.get(source.source_id)
                expected_config_hash = pdf_input_config_hash()
                expected_fingerprint = pdf_preparation_fingerprint(
                    source=source, scope=scope, evidence=source_evidence,
                )
                if revision is not None and (
                    revision.preparation_fingerprint != expected_fingerprint
                    or revision.input_config_hash != expected_config_hash
                ):
                    revision = None
                if revision is None:
                    views.append(G3SourceView(
                        source_id=source.source_id,
                        source_name=name,
                        source_kind=source.source_kind,
                        state="ready",
                        message="Il PDF è pronto per generare il proprio sottografo.",
                    ))
                    continue
                views.append(G3SourceView(
                    source_id=source.source_id,
                    source_name=name,
                    source_kind=source.source_kind,
                    state=revision.status.value,
                    message={
                        SourceSubgraphStatus.REVIEWING: "Controlla il grafo e approvalo fonte per fonte.",
                        SourceSubgraphStatus.APPROVED: "Sottografo controllato e approvato.",
                        SourceSubgraphStatus.REJECTED: "Sottografo segnalato per correzione.",
                    }[revision.status],
                    subgraph=revision,
                ))
                continue
            if source.source_kind not in STRUCTURED_GRAPH_KINDS:
                views.append(G3SourceView(
                    source_id=source.source_id,
                    source_name=name,
                    source_kind=source.source_kind,
                    state="deferred",
                    message="Formato predisposto per una fase successiva.",
                ))
                continue
            eligible_ids.append(source.source_id)
            profile = profiles.get(source.source_id)
            if profile is None or profile.state != "prepared" or profile.profile_id not in confirmed:
                views.append(G3SourceView(
                    source_id=source.source_id,
                    source_name=name,
                    source_kind=source.source_kind,
                    state="waiting",
                    message="Conferma prima la struttura di questa fonte.",
                ))
                continue
            revision = revisions.get(source.source_id)
            expected_config_hash = self._input_config_hash(source.source_kind)
            expected_mapping_fingerprint = mapping_fingerprint(profile)
            if revision is not None and (
                revision.preparation_fingerprint != expected_mapping_fingerprint
                or revision.input_config_hash != expected_config_hash
            ):
                revision = None
            if revision is None:
                views.append(G3SourceView(
                    source_id=source.source_id,
                    source_name=name,
                    source_kind=source.source_kind,
                    state="ready",
                    message="La fonte è pronta per generare il proprio sottografo.",
                ))
                continue
            views.append(G3SourceView(
                source_id=source.source_id,
                source_name=name,
                source_kind=source.source_kind,
                state=revision.status.value,
                message={
                    SourceSubgraphStatus.REVIEWING: "Controlla il grafo e approvalo fonte per fonte.",
                    SourceSubgraphStatus.APPROVED: "Sottografo controllato e approvato.",
                    SourceSubgraphStatus.REJECTED: "Sottografo segnalato per correzione.",
                }[revision.status],
                subgraph=revision,
            ))

        eligible = [item for item in views if item.source_id in eligible_ids]
        missing_generation = [item.source_id for item in eligible if item.subgraph is None]
        missing_approval = [
            item.source_id for item in eligible
            if item.subgraph is not None and item.subgraph.status is not SourceSubgraphStatus.APPROVED
        ]
        if missing_generation:
            barrier_state = "waiting_for_generation"
            pending = missing_generation + missing_approval
        elif missing_approval:
            barrier_state = "waiting_for_approval"
            pending = missing_approval
        else:
            barrier_state = "ready"
            pending = []
        approved = [
            item.subgraph for item in eligible
            if item.subgraph and item.subgraph.status is SourceSubgraphStatus.APPROVED
        ]
        exact_matches = self._exact_matches(approved) if barrier_state == "ready" else []
        return G3WorkspaceView(
            workspace_id=workspace_id,
            sources=views,
            counts={
                "eligible_sources": len(eligible),
                "generated_sources": sum(item.subgraph is not None for item in eligible),
                "approved_sources": sum(
                    item.subgraph is not None and item.subgraph.status is SourceSubgraphStatus.APPROVED
                    for item in eligible
                ),
                "deferred_sources": sum(item.state == "deferred" for item in views),
                "exact_cross_source_matches": len(exact_matches),
            },
            merge_barrier=MergeBarrierView(
                state=barrier_state,
                pending_source_ids=list(dict.fromkeys(pending)),
                exact_matches=exact_matches,
            ),
        )

    async def generate(self, workspace_id: str, source_id: str) -> G3WorkspaceView:
        workspace = self.workspaces.get_by_id(workspace_id)
        if workspace is None:
            raise LookupError(workspace_id)
        try:
            source = self.sources.get(source_id)
        except SourceNotFoundError as exc:
            raise LookupError(source_id) from exc
        if source.workspace_id != workspace_id:
            raise LookupError(source_id)
        if source.source_kind not in GRAPH_KINDS:
            raise SourceSubgraphGenerationError(
                "La generazione del grafo non è disponibile per questo formato."
            )
        if source.source_kind is SourceKind.PDF:
            scope = self.evidence.current_scope(source_id)
            evidence = [
                item for item in self.evidence.list_evidence(
                    workspace_id=workspace_id, source_id=source_id,
                )
                if item.eligible_for_semantic_processing
            ]
            if scope is None or not evidence:
                raise SourceSubgraphGenerationError(
                    "Attendi che la preparazione del PDF produca evidenze utilizzabili"
                )
            fingerprint = pdf_preparation_fingerprint(
                source=source, scope=scope, evidence=evidence,
            )
            config_hash = pdf_input_config_hash()
            lock = _PDF_GENERATION_LOCKS.setdefault(source_id, asyncio.Lock())
            async with lock:
                existing = self.subgraphs.find_matching(
                    source_id=source_id,
                    preparation_fingerprint=fingerprint,
                    input_config_hash=config_hash,
                )
                if existing is None:
                    previous = self.subgraphs.current_for_workspace(workspace_id).get(source_id)
                    try:
                        revision = await PdfSourceSubgraphBuilder().build_revision(
                            workspace=workspace,
                            source=source,
                            scope=scope,
                            evidence=evidence,
                            fingerprint=fingerprint,
                            config_hash=config_hash,
                            supersedes=(previous.source_subgraph_revision_id if previous else None),
                        )
                    except ValueError as exc:
                        raise SourceSubgraphGenerationError(str(exc)) from exc
                    self.subgraphs.create(revision)
            return self.snapshot(workspace_id)
        profile = self.profiles.current_profile(source_id)
        if profile is None or profile.state != "prepared":
            raise SourceSubgraphGenerationError("Completa prima la struttura dei dati di questa fonte")
        if profile.profile_id not in self._confirmed_profiles(workspace_id):
            raise SourceSubgraphGenerationError("Conferma prima la struttura dei dati di questa fonte")
        effective_mapping_fingerprint = mapping_fingerprint(profile)
        evidence = [
            item for item in self.evidence.list_evidence(workspace_id=workspace_id, source_id=source_id)
            if item.eligible_for_semantic_processing
        ]
        if not evidence:
            raise SourceSubgraphGenerationError("La fonte non contiene evidenze utilizzabili per generare il grafo")
        config_hash = self._input_config_hash(source.source_kind)
        existing = self.subgraphs.find_matching(
            source_id=source_id,
            preparation_fingerprint=effective_mapping_fingerprint,
            input_config_hash=config_hash,
        )
        if existing is None:
            previous = self.subgraphs.current_for_workspace(workspace_id).get(source_id)
            self.subgraphs.create(self._build_revision(
                workspace=workspace,
                source=source,
                fingerprint=effective_mapping_fingerprint,
                config_hash=config_hash,
                evidence=evidence,
                supersedes=(previous.source_subgraph_revision_id if previous else None),
            ))
        return self.snapshot(workspace_id)

    def decide(self, revision_id: str, *, action: str, note: str | None) -> G3WorkspaceView:
        revision = self.subgraphs.decide(revision_id, action=action, note=note)
        return self.snapshot(revision.workspace_id)

    def _build_revision(
        self,
        *,
        workspace,
        source,
        fingerprint: str,
        config_hash: str,
        evidence: list[EvidenceUnit],
        supersedes: str | None,
    ) -> SourceSubgraphRevision:
        node_claims: dict[tuple[str, str], dict[str, Any]] = {}
        relation_claims: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        knowledge_gaps: list[KnowledgeGap] = []
        raw_node_claims = 0
        raw_relation_claims = 0

        def add_gap(code: str, message: str, evidence_id: str) -> None:
            if any((item.code, tuple(item.evidence_ids)) == (code, (evidence_id,)) for item in knowledge_gaps):
                return
            knowledge_gaps.append(KnowledgeGap(code=code, message=message, evidence_ids=[evidence_id]))

        def add_node(
            node_type: str,
            label: str,
            evidence_id: str,
            *,
            attributes: dict[str, Any],
            node_id: str | None = None,
        ) -> str | None:
            nonlocal raw_node_claims
            normalized = _normalized_label(label)
            if not normalized:
                return None
            raw_node_claims += 1
            key = (node_type, normalized)
            node = node_claims.setdefault(key, {
                "node_id": node_id or _stable_id("gnode", source.source_id, node_type, normalized),
                "node_type": node_type,
                "label": str(label).strip(),
                "description": str(label).strip(),
                "evidence_ids": set(),
                "attributes": {},
            })
            node["evidence_ids"].add(evidence_id)
            canonical_attributes = {
                key: value for key, value in attributes.items() if value not in (None, "")
            }
            canonical_attributes[_ID_PROPERTIES[node_type]] = node["node_id"]
            canonical_attributes.setdefault("name", node["label"])
            canonical_attributes.setdefault("description", node["description"])
            for attribute, value in canonical_attributes.items():
                current = node["attributes"].get(attribute)
                if attribute == "related_measurements":
                    node["attributes"][attribute] = list(dict.fromkeys([*(current or []), *value]))
                elif current in (None, ""):
                    node["attributes"][attribute] = value
                elif attribute == "material_context" and current != value:
                    # A globally deduplicated failure mode spanning multiple
                    # components must not claim an arbitrary one as its sole
                    # material context.
                    node["attributes"][attribute] = "asset_level"
            return node["node_id"]

        def add_relation(relation_type: str, from_id: str | None, to_id: str | None, evidence_id: str) -> None:
            nonlocal raw_relation_claims
            if not from_id or not to_id:
                return
            raw_relation_claims += 1
            relation_claims[(relation_type, from_id, to_id)].add(evidence_id)

        def add_unambiguous_pairs(
            relation_type: str,
            left: list[str | None],
            right: list[str | None],
            *,
            evidence_id: str,
            gap_code: str,
            gap_message: str,
        ) -> None:
            left_ids = [item for item in left if item]
            right_ids = [item for item in right if item]
            if not left_ids or not right_ids:
                return
            if len(left_ids) > 1 and len(right_ids) > 1:
                add_gap(gap_code, gap_message, evidence_id)
                return
            for from_id in left_ids:
                for to_id in right_ids:
                    add_relation(relation_type, from_id, to_id, evidence_id)

        all_evidence_ids = [item.evidence_id for item in evidence]
        asset_id = add_node(
            "Asset",
            workspace.asset.name,
            all_evidence_ids[0],
            node_id=workspace.asset.asset_id,
            attributes={
                "description": workspace.asset.description,
                "brand": workspace.asset.brand,
                "model": workspace.asset.model,
                "asset_type": workspace.asset.asset_type,
            },
        )
        node_claims[("Asset", _normalized_label(workspace.asset.name))]["evidence_ids"].update(all_evidence_ids)

        for unit in evidence:
            semantic = unit.content.semantic_texts
            components = _values(semantic.get("component", ""))
            symptoms = _values(unit.content.observation or semantic.get("symptom", ""))
            causes = _values(unit.content.cause or semantic.get("failure_mode", ""))
            actions = _values(unit.content.action or semantic.get("corrective_action", ""))
            error_codes = _values(unit.content.error_code or semantic.get("error_code_context", ""))
            component_ids = [
                add_node("Component", value, unit.evidence_id, attributes={"category": "source_record"})
                for value in components
            ]
            symptom_ids = [
                add_node("Symptom", value, unit.evidence_id, attributes={"severity": "unspecified"})
                for value in symptoms
            ]
            material_context = component_ids[0] if len(component_ids) == 1 else "asset_level"
            cause_ids = [
                add_node(
                    "FailureMode",
                    value,
                    unit.evidence_id,
                    attributes={
                        "material_context": material_context,
                        "related_measurements": [unit.content.measurement] if unit.content.measurement else [],
                    },
                )
                for value in causes
            ]
            action_ids = [
                add_node(
                    "CorrectiveAction",
                    value,
                    unit.evidence_id,
                    attributes={
                        "instruction_text": value,
                        "source_type": source.source_kind.value,
                        "source_title": source.file_name or "Structured source",
                        "source_reference": f"source:{source.source_id}",
                    },
                )
                for value in actions
            ]
            error_ids = [
                add_node("ErrorCode", value, unit.evidence_id, attributes={"code": value})
                for value in error_codes
            ]
            if not causes:
                add_gap(
                    "missing_failure_mode",
                    "La riga contiene segnali diagnostici ma non dichiara una causa o modalità di guasto.",
                    unit.evidence_id,
                )
            if causes and not (symptoms or error_codes):
                add_gap(
                    "missing_diagnostic_indicator",
                    "La causa non è collegabile a un sintomo o a un codice errore nella riga originale.",
                    unit.evidence_id,
                )
            if causes and not actions:
                add_gap(
                    "missing_corrective_action",
                    "La causa non ha un'azione correttiva dichiarata nella riga originale.",
                    unit.evidence_id,
                )
            for component_id in component_ids:
                add_relation("HAS_COMPONENT", asset_id, component_id, unit.evidence_id)
            add_unambiguous_pairs(
                "MAY_INDICATE", symptom_ids, cause_ids,
                evidence_id=unit.evidence_id,
                gap_code="ambiguous_symptom_cause_pairing",
                gap_message="Più sintomi e più cause nella stessa riga non stabiliscono le coppie corrette.",
            )
            add_unambiguous_pairs(
                "AFFECTS", cause_ids, component_ids,
                evidence_id=unit.evidence_id,
                gap_code="ambiguous_cause_component_pairing",
                gap_message="Più cause e più componenti nella stessa riga non stabiliscono le coppie corrette.",
            )
            add_unambiguous_pairs(
                "RESOLVED_BY", cause_ids, action_ids,
                evidence_id=unit.evidence_id,
                gap_code="ambiguous_cause_action_pairing",
                gap_message="Più cause e più azioni nella stessa riga non stabiliscono le coppie corrette.",
            )
            for error_id in error_ids:
                add_relation("GENERATES_ERROR", asset_id, error_id, unit.evidence_id)
            add_unambiguous_pairs(
                "INDICATES", error_ids, cause_ids,
                evidence_id=unit.evidence_id,
                gap_code="ambiguous_error_cause_pairing",
                gap_message="Più codici errore e più cause nella stessa riga non stabiliscono le coppie corrette.",
            )

        nodes = [
            SourceGraphNode.model_validate({**node, "evidence_ids": sorted(node["evidence_ids"])})
            for _, node in sorted(node_claims.items())
        ]
        relations = [
            SourceGraphRelation(
                relation_id=_stable_id("grel", source.source_id, relation_type, from_id, to_id),
                relation_type=relation_type,
                from_id=from_id,
                to_id=to_id,
                evidence_ids=sorted(evidence_ids),
            )
            for (relation_type, from_id, to_id), evidence_ids in sorted(relation_claims.items())
        ]
        evidence_refs = [
            GraphEvidenceRef(
                evidence_id=item.evidence_id,
                label=_locator_label(item.locator.model_dump(mode="json")),
                excerpt=_excerpt(item),
                locator=item.locator.model_dump(mode="json"),
            )
            for item in evidence
        ]
        validation = _strict_validation(nodes=nodes, relations=relations, evidence=evidence_refs)
        return SourceSubgraphRevision(
            source_subgraph_revision_id=new_id("source_subgraph"),
            workspace_id=workspace.workspace_id,
            source_id=source.source_id,
            source_name=source.file_name or "Fonte",
            source_kind=source.source_kind,
            preparation_fingerprint=fingerprint,
            input_config_hash=config_hash,
            evidence_ids=sorted(all_evidence_ids),
            nodes=nodes,
            relations=relations,
            evidence=evidence_refs,
            status=SourceSubgraphStatus.REVIEWING,
            duplicate_nodes_consolidated=max(0, raw_node_claims - len(nodes)),
            duplicate_relations_consolidated=max(0, raw_relation_claims - len(relations)),
            validation=validation,
            knowledge_gaps=knowledge_gaps,
            approval_eligible=validation.passed and not knowledge_gaps,
            supersedes=supersedes,
            created_at=utc_now(),
        )

    @staticmethod
    def _input_config_hash(source_kind: SourceKind) -> str:
        return _canonical_hash({
            "generator_version": GENERATOR_VERSION,
            "ontology_sha256": ontology_contract().sha256,
            "source_kind": source_kind.value,
        })

    @staticmethod
    def _exact_matches(revisions: list[SourceSubgraphRevision]) -> list[CrossSourceMatch]:
        grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
        labels: dict[tuple[str, str], str] = {}
        for revision in revisions:
            for node in revision.nodes:
                if node.node_type == "Asset":
                    continue
                key = (node.node_type, _normalized_label(node.label))
                labels[key] = node.label
                grouped[key].append({
                    "source_id": revision.source_id,
                    "source_name": revision.source_name,
                    "node_id": node.node_id,
                })
        return [
            CrossSourceMatch(
                node_type=node_type,
                normalized_label=normalized,
                label=labels[(node_type, normalized)],
                occurrences=occurrences,
            )
            for (node_type, normalized), occurrences in sorted(grouped.items())
            if len({item["source_id"] for item in occurrences}) > 1
        ]

    @staticmethod
    def _confirmed_profiles(workspace_id: str) -> set[str]:
        with get_database().read() as connection:
            rows = connection.execute(CONFIRMED_PROFILES_SQL, (workspace_id,)).fetchall()
        return {row["subject_id"] for row in rows}
