"""Fail-closed validation and deterministic ontology compilation for PDF diagnostics."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Iterable, Mapping, Sequence

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.diagnostic_bundles import (
    DiagnosticBundleCandidate,
    DiagnosticChunkOutput,
    DiagnosticEvidenceSpan,
    ResolutionStatus,
    ValidatedAffectedComponent,
    ValidatedCorrectiveAction,
    ValidatedDiagnosticBundle,
    ValidatedDiagnosticEvidenceSpan,
    ValidatedErrorCodeIndicator,
    ValidatedFailureMode,
    ValidatedSymptomIndicator,
)
from backend.domain.evidence import EvidenceUnit
from backend.domain.locators import PdfLocator
from backend.models import (
    OntologyEvidence,
    OntologyInstance,
    OntologyRelationInstance,
    OntologySchemaDefinition,
)
from backend.services.ontology_schema_service import load_ontology_schema

_ANCHOR_RE = re.compile(r"\[\[EVIDENCE_ID:\s*([^\]]+?)\s*\]\]")
_PAGE_RE = re.compile(r"(?m)^--- PAGE\s+(\d+)\s+---\s*$")
_GENERAL_MATERIAL_CONTEXTS = {
    "asset",
    "asset level",
    "asset_level",
    "general",
    "machine",
    "system",
    "whole asset",
    "whole_asset",
}
_TYPE_PREFIX = {
    "Component": "comp",
    "Symptom": "sym",
    "FailureMode": "fm",
    "CorrectiveAction": "ca",
    "ErrorCode": "err",
}


class BundleDisposition(StrEnum):
    PUBLISH = "publish"
    GAP = "gap"
    REVIEW = "review"
    EXCLUDE = "exclude"


class BundleDropReason(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(min_length=1)
    path: str = ""
    message: str = Field(min_length=1)


class BundleCompilationEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_lineage_id: str
    branch_lineage_id: str
    record_anchor: str
    branch_anchor: str
    evidence_ids: list[str] = Field(default_factory=list)
    disposition: BundleDisposition
    drop_reasons: list[BundleDropReason] = Field(default_factory=list)
    emitted_node_ids: list[str] = Field(default_factory=list)
    emitted_relations: list[str] = Field(default_factory=list)


class DiagnosticBundleCompilationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    input_candidates: int = Field(ge=0)
    unique_candidates: int = Field(ge=0)
    duplicate_candidates: int = Field(ge=0)
    disposition_counts: dict[str, int]
    dropped_items_by_reason: dict[str, int]
    entries: list[BundleCompilationEntry]


class DiagnosticBundleCompilationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    ontology: OntologyInstance
    validated_bundles: list[ValidatedDiagnosticBundle]
    report: DiagnosticBundleCompilationReport


class EvidenceValidationProblem(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    path: str
    message: str


class DiagnosticBundleEvidenceError(ValueError):
    """Raised when at least one model-provided evidence span cannot be grounded."""

    def __init__(self, problems: Sequence[EvidenceValidationProblem]) -> None:
        self.problems = tuple(problems)
        super().__init__("; ".join(problem.message for problem in self.problems))


@dataclass(frozen=True)
class _EvidenceRecord:
    evidence_id: str
    page: int
    text: str
    locator: dict[str, Any]
    priority: int


def _display_text(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or ""))).strip()


def _identity_text(value: str) -> str:
    return _display_text(value).casefold()


def _canonical_value(value: Any) -> Any:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_value(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [_canonical_value(item) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
    if isinstance(value, str):
        return _identity_text(value)
    return value


def _canonical_json(value: Any) -> str:
    return json.dumps(
        _canonical_value(value),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _record_payload(
    candidate: DiagnosticBundleCandidate,
    *,
    source_type: str,
    source_title: str,
) -> dict[str, Any]:
    indicators: list[dict[str, Any]] = []
    for indicator in candidate.indicators:
        payload = indicator.model_dump(mode="json", exclude={"failure_link_evidence"})
        indicators.append(payload)
    return {
        "source_type": source_type,
        "source_title": source_title,
        "record_anchor": candidate.record_anchor,
        "indicators": indicators,
    }


def diagnostic_record_lineage_id(
    candidate: DiagnosticBundleCandidate,
    *,
    source_type: str,
    source_title: str,
) -> str:
    """Return the source-record identity, independent of branch/action ordering."""

    return f"drec_{_digest(_record_payload(candidate, source_type=source_type, source_title=source_title))}"


def diagnostic_branch_lineage_id(
    candidate: DiagnosticBundleCandidate,
    *,
    source_type: str,
    source_title: str,
) -> str:
    """Return a stable identity for one exact diagnostic branch.

    Resolution status is review state, not branch identity, and is deliberately
    excluded.  All claims and claim-specific edge evidence remain in the hash.
    """

    payload = candidate.model_dump(mode="json", exclude={"resolution_status"})
    return f"dbranch_{_digest({'source_type': source_type, 'source_title': source_title, 'bundle': payload})}"


def _legacy_page(mapping: Mapping[str, Any]) -> int | None:
    for key in ("source_page", "page_number", "page"):
        value = mapping.get(key)
        if isinstance(value, int) and value >= 1:
            return value
        if isinstance(value, str) and value.strip().isdigit() and int(value) >= 1:
            return int(value)
    return None


def _legacy_records(chunk: Mapping[str, Any]) -> list[_EvidenceRecord]:
    page = _legacy_page(chunk)
    if page is None:
        return []
    text = str(chunk.get("text") or chunk.get("quote") or "")
    direct_anchor = str(chunk.get("source_anchor") or chunk.get("evidence_id") or "").strip()
    if direct_anchor:
        return [
            _EvidenceRecord(
                evidence_id=direct_anchor,
                page=page,
                text=text,
                locator={
                    "kind": "pdf",
                    "page": page,
                    "quote": text,
                    "extraction_method": str(chunk.get("text_source") or "native_text"),
                },
                priority=1,
            )
        ]

    matches = list(_ANCHOR_RE.finditer(text))
    records: list[_EvidenceRecord] = []
    for index, match in enumerate(matches):
        anchor = match.group(1).strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        anchored_text = text[match.end() : end].strip()
        records.append(
            _EvidenceRecord(
                evidence_id=anchor,
                page=page,
                text=anchored_text,
                locator={
                    "kind": "pdf",
                    "page": page,
                    "quote": anchored_text,
                    "extraction_method": str(chunk.get("text_source") or "native_text"),
                },
                priority=1,
            )
        )
    return records


def _chunks_from_text_with_pages(text_with_pages: str) -> list[dict[str, Any]]:
    """Parse the exact ``format_text_with_pages`` representation used by G3."""

    matches = list(_PAGE_RE.finditer(str(text_with_pages or "")))
    chunks: list[dict[str, Any]] = []
    for position, match in enumerate(matches):
        end = matches[position + 1].start() if position + 1 < len(matches) else len(text_with_pages)
        chunks.append(
            {
                "page_number": int(match.group(1)),
                "text": text_with_pages[match.end() : end].strip(),
                "text_source": "native_text",
            }
        )
    return chunks


def _evidence_index(
    evidence_units: Sequence[EvidenceUnit],
    legacy_chunks: Sequence[Mapping[str, Any]],
    text_with_pages: str | None = None,
) -> dict[str, tuple[_EvidenceRecord, ...]]:
    records: list[_EvidenceRecord] = []
    for unit in evidence_units:
        if not isinstance(unit.locator, PdfLocator):
            raise ValueError("Diagnostic PDF bundles require PdfLocator evidence units")
        records.append(
            _EvidenceRecord(
                evidence_id=str(unit.evidence_id),
                page=unit.locator.page,
                text=unit.locator.quote,
                locator=unit.locator.model_dump(mode="json"),
                priority=0,
            )
        )
    for chunk in legacy_chunks:
        records.extend(_legacy_records(chunk))
    if text_with_pages:
        for chunk in _chunks_from_text_with_pages(text_with_pages):
            records.extend(_legacy_records(chunk))

    unique: dict[tuple[str, int, str], _EvidenceRecord] = {}
    for record in records:
        key = (record.evidence_id, record.page, _display_text(record.text))
        current = unique.get(key)
        if current is None or record.priority < current.priority:
            unique[key] = record

    by_anchor: dict[str, list[_EvidenceRecord]] = {}
    for record in unique.values():
        by_anchor.setdefault(record.evidence_id, []).append(record)
    return {
        anchor: tuple(
            sorted(
                items,
                key=lambda item: (
                    item.priority,
                    item.page,
                    _display_text(item.text),
                    json.dumps(item.locator, sort_keys=True, ensure_ascii=False),
                ),
            )
        )
        for anchor, items in by_anchor.items()
    }


def _resolve_span(
    span: DiagnosticEvidenceSpan,
    *,
    path: str,
    index: Mapping[str, tuple[_EvidenceRecord, ...]],
) -> tuple[ValidatedDiagnosticEvidenceSpan | None, EvidenceValidationProblem | None]:
    anchor = span.source_anchor.strip()
    records = index.get(anchor)
    if not records:
        return None, EvidenceValidationProblem(
            code="unknown_source_anchor",
            path=path,
            message=f"{path}: source anchor {anchor!r} does not resolve",
        )

    page_records = [record for record in records if record.page == span.source_page]
    if not page_records:
        pages = sorted({record.page for record in records})
        return None, EvidenceValidationProblem(
            code="source_page_mismatch",
            path=path,
            message=(
                f"{path}: anchor {anchor!r} is on page(s) {pages}, not page {span.source_page}"
            ),
        )

    quote = _display_text(span.quote)
    matching = [record for record in page_records if quote and quote in _display_text(record.text)]
    if not matching:
        return None, EvidenceValidationProblem(
            code="quote_not_in_anchored_evidence",
            path=path,
            message=f"{path}: quote is not an exact lexical span of anchor {anchor!r}",
        )

    best_priority = min(record.priority for record in matching)
    preferred = [record for record in matching if record.priority == best_priority]
    canonical_texts = {_display_text(record.text) for record in preferred}
    if len(canonical_texts) > 1:
        return None, EvidenceValidationProblem(
            code="ambiguous_source_anchor",
            path=path,
            message=f"{path}: anchor {anchor!r} resolves to conflicting source evidence",
        )

    record = preferred[0]
    return (
        ValidatedDiagnosticEvidenceSpan(
            source_anchor=anchor,
            source_page=span.source_page,
            quote=_display_text(span.quote),
            evidence_id=record.evidence_id,
            locator=record.locator,
        ),
        None,
    )


def _resolve_spans(
    spans: Sequence[DiagnosticEvidenceSpan],
    *,
    path: str,
    index: Mapping[str, tuple[_EvidenceRecord, ...]],
    problems: list[EvidenceValidationProblem],
) -> list[ValidatedDiagnosticEvidenceSpan]:
    resolved: dict[tuple[str, int, str], ValidatedDiagnosticEvidenceSpan] = {}
    for position, span in enumerate(spans):
        item, problem = _resolve_span(span, path=f"{path}[{position}]", index=index)
        if problem is not None:
            problems.append(problem)
        elif item is not None:
            resolved[(item.source_anchor, item.source_page, item.quote)] = item
    return [resolved[key] for key in sorted(resolved)]


def _validate_lineage_anchor(
    anchor: str,
    *,
    path: str,
    index: Mapping[str, tuple[_EvidenceRecord, ...]],
    problems: list[EvidenceValidationProblem],
) -> str:
    """Require a model-produced record/branch anchor to be source-owned."""

    normalized = str(anchor or "").strip()
    if normalized not in index:
        problems.append(
            EvidenceValidationProblem(
                code="unknown_lineage_anchor",
                path=path,
                message=f"{path}: anchor {normalized!r} was not present in the supplied source text",
            )
        )
    return normalized


def _validated_bundle(
    candidate: DiagnosticBundleCandidate,
    *,
    index: Mapping[str, tuple[_EvidenceRecord, ...]],
    source_type: str,
    source_title: str,
) -> ValidatedDiagnosticBundle:
    problems: list[EvidenceValidationProblem] = []
    record_anchor = _validate_lineage_anchor(
        candidate.record_anchor,
        path="record_anchor",
        index=index,
        problems=problems,
    )
    branch_anchor = _validate_lineage_anchor(
        candidate.branch_anchor,
        path="branch_anchor",
        index=index,
        problems=problems,
    )
    indicators: list[ValidatedSymptomIndicator | ValidatedErrorCodeIndicator] = []
    for position, indicator in enumerate(candidate.indicators):
        prefix = f"indicators[{position}]"
        claims = _resolve_spans(
            indicator.claim_evidence,
            path=f"{prefix}.claim_evidence",
            index=index,
            problems=problems,
        )
        links = _resolve_spans(
            indicator.failure_link_evidence,
            path=f"{prefix}.failure_link_evidence",
            index=index,
            problems=problems,
        )
        if not claims:
            # Candidate claim evidence is non-empty by contract; an empty
            # resolved set therefore means grounding failed and ``problems``
            # already contains the exact reason.  Avoid constructing a
            # misleading partially validated claim.
            continue
        if indicator.kind == "symptom":
            indicators.append(
                ValidatedSymptomIndicator(
                    name=_display_text(indicator.name),
                    description=_display_text(indicator.description),
                    severity=indicator.severity,
                    claim_evidence=claims,
                    failure_link_evidence=links,
                )
            )
        else:
            indicators.append(
                ValidatedErrorCodeIndicator(
                    code=_display_text(indicator.code or ""),
                    name=_display_text(indicator.name),
                    description=_display_text(indicator.description),
                    claim_evidence=claims,
                    failure_link_evidence=links,
                )
            )

    failure: ValidatedFailureMode | None = None
    if candidate.failure is not None:
        failure_claims = _resolve_spans(
            candidate.failure.claim_evidence,
            path="failure.claim_evidence",
            index=index,
            problems=problems,
        )
        if failure_claims:
            failure = ValidatedFailureMode(
                name=_display_text(candidate.failure.name),
                description=_display_text(candidate.failure.description),
                material_context=(
                    _display_text(candidate.failure.material_context)
                    if candidate.failure.material_context is not None
                    else None
                ),
                claim_evidence=failure_claims,
            )

    actions: list[ValidatedCorrectiveAction] = []
    for position, action in enumerate(candidate.actions):
        action_claims = _resolve_spans(
            action.claim_evidence,
            path=f"actions[{position}].claim_evidence",
            index=index,
            problems=problems,
        )
        action_links = _resolve_spans(
            action.resolution_link_evidence,
            path=f"actions[{position}].resolution_link_evidence",
            index=index,
            problems=problems,
        )
        if not action_claims:
            continue
        actions.append(
            ValidatedCorrectiveAction(
                name=_display_text(action.name),
                description=_display_text(action.description),
                instruction_text=_display_text(action.instruction_text),
                action_kind=_display_text(action.action_kind) if action.action_kind else None,
                claim_evidence=action_claims,
                resolution_link_evidence=action_links,
            )
        )

    component: ValidatedAffectedComponent | None = None
    if candidate.affected_component is not None:
        component_claims = _resolve_spans(
            candidate.affected_component.claim_evidence,
            path="affected_component.claim_evidence",
            index=index,
            problems=problems,
        )
        component_links = _resolve_spans(
            candidate.affected_component.affects_link_evidence,
            path="affected_component.affects_link_evidence",
            index=index,
            problems=problems,
        )
        if component_claims:
            component = ValidatedAffectedComponent(
                name=_display_text(candidate.affected_component.name),
                description=_display_text(candidate.affected_component.description),
                category=(
                    _display_text(candidate.affected_component.category)
                    if candidate.affected_component.category is not None
                    else None
                ),
                claim_evidence=component_claims,
                affects_link_evidence=component_links,
            )

    claim_anchors = {
        span.source_anchor
        for indicator in indicators
        for span in indicator.claim_evidence
    }
    edge_anchors = {
        span.source_anchor
        for indicator in indicators
        for span in indicator.failure_link_evidence
    }
    if failure is not None:
        claim_anchors.update(span.source_anchor for span in failure.claim_evidence)
    for action in actions:
        claim_anchors.update(span.source_anchor for span in action.claim_evidence)
        edge_anchors.update(span.source_anchor for span in action.resolution_link_evidence)
    if component is not None:
        claim_anchors.update(span.source_anchor for span in component.claim_evidence)
        edge_anchors.update(span.source_anchor for span in component.affects_link_evidence)

    if record_anchor not in claim_anchors:
        problems.append(
            EvidenceValidationProblem(
                code="lineage_anchor_outside_bundle",
                path="record_anchor",
                message=(
                    f"record_anchor {record_anchor!r} does not support any claim in this record"
                ),
            )
        )
    branch_support_anchors = edge_anchors if failure is not None and edge_anchors else claim_anchors
    if branch_anchor not in branch_support_anchors:
        support_kind = "edge" if failure is not None and edge_anchors else "claim"
        problems.append(
            EvidenceValidationProblem(
                code="lineage_anchor_outside_bundle",
                path="branch_anchor",
                message=(
                    f"branch_anchor {branch_anchor!r} does not support any {support_kind} "
                    "evidence in this branch"
                ),
            )
        )

    if problems:
        raise DiagnosticBundleEvidenceError(problems)

    indicators.sort(key=_canonical_json)
    actions.sort(key=_canonical_json)
    return ValidatedDiagnosticBundle(
        record_lineage_id=diagnostic_record_lineage_id(
            candidate,
            source_type=source_type,
            source_title=source_title,
        ),
        branch_lineage_id=diagnostic_branch_lineage_id(
            candidate,
            source_type=source_type,
            source_title=source_title,
        ),
        record_anchor=record_anchor,
        branch_anchor=branch_anchor,
        indicators=indicators,
        failure=failure,
        actions=actions,
        affected_component=component,
        resolution_status=candidate.resolution_status,
    )


def validate_diagnostic_bundle(
    candidate: DiagnosticBundleCandidate | Mapping[str, Any],
    *,
    source_type: str,
    source_title: str,
    evidence_units: Sequence[EvidenceUnit] = (),
    legacy_chunks: Sequence[Mapping[str, Any]] = (),
    text_with_pages: str | None = None,
) -> ValidatedDiagnosticBundle:
    """Resolve every candidate span exactly or raise ``DiagnosticBundleEvidenceError``."""

    typed = (
        candidate
        if isinstance(candidate, DiagnosticBundleCandidate)
        else DiagnosticBundleCandidate.model_validate(candidate)
    )
    return _validated_bundle(
        typed,
        index=_evidence_index(evidence_units, legacy_chunks, text_with_pages),
        source_type=_required_source_value(source_type, "source_type"),
        source_title=_required_source_value(source_title, "source_title"),
    )


def _reason(code: str, message: str, path: str = "") -> BundleDropReason:
    return BundleDropReason(code=code, path=path, message=message)


def _classify_candidate(
    candidate: DiagnosticBundleCandidate,
    evidence_problems: Sequence[EvidenceValidationProblem],
) -> tuple[BundleDisposition, list[BundleDropReason]]:
    if candidate.resolution_status is ResolutionStatus.NOT_DIAGNOSTIC:
        if evidence_problems:
            return BundleDisposition.REVIEW, _sorted_reasons(
                _reason(problem.code, problem.message, problem.path)
                for problem in evidence_problems
            )
        return BundleDisposition.EXCLUDE, [
            _reason("declared_not_diagnostic", "The extractor explicitly classified this record as non-diagnostic.")
        ]

    reasons = [
        _reason(problem.code, problem.message, problem.path)
        for problem in evidence_problems
    ]
    contradictions = False
    missing = False

    if candidate.failure is None:
        missing = True
        reasons.append(_reason("missing_failure", "No FailureMode claim was supplied.", "failure"))
        if candidate.actions:
            contradictions = True
            reasons.append(
                _reason("action_without_failure", "CorrectiveAction claims cannot be linked without a FailureMode.", "actions")
            )
        if candidate.affected_component is not None:
            contradictions = True
            reasons.append(
                _reason(
                    "component_without_failure",
                    "An affected Component cannot be linked without a FailureMode.",
                    "affected_component",
                )
            )
        if any(indicator.failure_link_evidence for indicator in candidate.indicators):
            contradictions = True
            reasons.append(
                _reason(
                    "failure_edge_without_failure",
                    "Indicator-to-failure evidence was supplied without a FailureMode.",
                    "indicators",
                )
            )
    else:
        for position, indicator in enumerate(candidate.indicators):
            if not indicator.failure_link_evidence:
                missing = True
                reasons.append(
                    _reason(
                        "missing_indicator_failure_evidence",
                        "The indicator-to-failure edge has no direct evidence.",
                        f"indicators[{position}].failure_link_evidence",
                    )
                )
        if not candidate.actions:
            missing = True
            reasons.append(_reason("missing_actions", "No CorrectiveAction claim was supplied.", "actions"))
        for position, action in enumerate(candidate.actions):
            if not action.resolution_link_evidence:
                missing = True
                reasons.append(
                    _reason(
                        "missing_resolution_evidence",
                        "The FailureMode-to-CorrectiveAction edge has no direct evidence.",
                        f"actions[{position}].resolution_link_evidence",
                    )
                )
        if (
            candidate.affected_component is not None
            and not candidate.affected_component.affects_link_evidence
        ):
            missing = True
            reasons.append(
                _reason(
                    "missing_affects_evidence",
                    "The FailureMode-to-Component edge has no direct evidence.",
                    "affected_component.affects_link_evidence",
                )
            )
        if (
            candidate.affected_component is None
            and candidate.failure.material_context is not None
            and not _is_asset_level(candidate.failure.material_context)
        ):
            missing = True
            reasons.append(
                _reason(
                    "unresolved_material_context",
                    "A non-asset material context requires an explicit affected Component.",
                    "failure.material_context",
                )
            )

    if candidate.resolution_status is ResolutionStatus.AMBIGUOUS:
        reasons.append(_reason("declared_ambiguous", "The extractor marked this branch as ambiguous."))
        return BundleDisposition.REVIEW, _sorted_reasons(reasons)
    if evidence_problems or contradictions:
        return BundleDisposition.REVIEW, _sorted_reasons(reasons)
    if candidate.resolution_status is ResolutionStatus.NO_ACTION_STATED:
        if candidate.actions:
            reasons.append(
                _reason(
                    "status_action_conflict",
                    "Actions were supplied although resolution_status says no action was stated.",
                    "resolution_status",
                )
            )
            return BundleDisposition.REVIEW, _sorted_reasons(reasons)
        reasons.append(
            _reason(
                "no_action_stated",
                "The source states no restorative action for this diagnostic branch.",
                "resolution_status",
            )
        )
        return BundleDisposition.GAP, _sorted_reasons(reasons)
    if candidate.resolution_status is ResolutionStatus.CHECK_ONLY:
        if candidate.actions:
            reasons.append(
                _reason(
                    "check_action_conflict",
                    "Check-only content was supplied as a restorative CorrectiveAction.",
                    "actions",
                )
            )
            return BundleDisposition.REVIEW, _sorted_reasons(reasons)
        reasons.append(
            _reason(
                "check_only",
                "The source provides a diagnostic check but no restorative action.",
                "resolution_status",
            )
        )
        return BundleDisposition.GAP, _sorted_reasons(reasons)
    if missing:
        return BundleDisposition.GAP, _sorted_reasons(reasons)
    return BundleDisposition.PUBLISH, []


def _sorted_reasons(reasons: Iterable[BundleDropReason]) -> list[BundleDropReason]:
    unique = {
        (reason.code, reason.path, reason.message): reason
        for reason in reasons
    }
    return [unique[key] for key in sorted(unique)]


def _is_asset_level(value: str | None) -> bool:
    return _identity_text(value).replace("-", "_") in {
        item.replace(" ", "_") for item in _GENERAL_MATERIAL_CONTEXTS
    }


def _required_source_value(value: str, field: str) -> str:
    normalized = _display_text(value)
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


def _slug(value: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_text.casefold()).strip("_")
    return (slug or "node")[:48]


def _graph_id(node_type: str, label: str, semantic_payload: Any) -> str:
    try:
        prefix = _TYPE_PREFIX[node_type]
    except KeyError as exc:
        raise ValueError(f"Unsupported diagnostic node type: {node_type}") from exc
    # The full digest makes the ID globally collision-resistant while the fixed
    # type prefix prevents accidental cross-type references.
    return f"{prefix}_{_slug(label)}_{_digest({'type': node_type, 'claim': semantic_payload})}"


def _node_definitions(schema: OntologySchemaDefinition) -> dict[str, Any]:
    definitions = {node.name: node for node in schema.nodes}
    missing = sorted(set(_TYPE_PREFIX) - set(definitions))
    if missing:
        raise ValueError(f"Ontology schema is missing diagnostic node types: {missing}")
    return definitions


def _id_property(node_definition: Any) -> str:
    for prop in node_definition.properties:
        if prop.unique:
            return prop.name
    raise ValueError(f"Ontology node {node_definition.name} has no unique identifier property")


def _validated_node(node_definition: Any, values: dict[str, Any]) -> dict[str, Any]:
    properties = {prop.name: prop for prop in node_definition.properties}
    extras = sorted(set(values) - set(properties))
    if extras:
        raise ValueError(f"Compiler emitted unknown {node_definition.name} properties: {extras}")
    missing = [
        prop.name
        for prop in node_definition.properties
        if prop.required and (prop.name not in values or values[prop.name] in (None, ""))
    ]
    if missing:
        raise ValueError(f"Compiler omitted required {node_definition.name} properties: {missing}")
    return {prop.name: values[prop.name] for prop in node_definition.properties if prop.name in values}


def _relation_names(schema: OntologySchemaDefinition) -> dict[tuple[str, str], str]:
    expected = {
        ("Symptom", "FailureMode"): "MAY_INDICATE",
        ("ErrorCode", "FailureMode"): "INDICATES",
        ("FailureMode", "CorrectiveAction"): "RESOLVED_BY",
        ("FailureMode", "Component"): "AFFECTS",
    }
    by_pair: dict[tuple[str, str], list[str]] = {}
    for relation in schema.relations:
        by_pair.setdefault((relation.domain, relation.range), []).append(relation.name)
    resolved: dict[tuple[str, str], str] = {}
    for pair, required_name in expected.items():
        names = by_pair.get(pair, [])
        if required_name not in names:
            raise ValueError(
                f"Ontology schema is missing {required_name} for {pair[0]} -> {pair[1]}"
            )
        resolved[pair] = required_name
    return resolved


def _relation_evidence(
    spans: Sequence[ValidatedDiagnosticEvidenceSpan],
) -> list[OntologyEvidence]:
    return [
        OntologyEvidence(
            source_page=span.source_page,
            source_reference=span.evidence_id,
            quote=span.quote,
            source_anchor=span.source_anchor,
        )
        for span in sorted(
            spans,
            key=lambda item: (item.source_anchor, item.source_page, item.quote),
        )
    ]


def _compile_published(
    bundles: Sequence[ValidatedDiagnosticBundle],
    *,
    schema: OntologySchemaDefinition,
    source_type: str,
    source_title: str,
    language: str,
) -> tuple[OntologyInstance, dict[str, tuple[list[str], list[str]]]]:
    definitions = _node_definitions(schema)
    relation_names = _relation_names(schema)
    nodes_by_type: dict[str, dict[str, dict[str, Any]]] = {
        node.name: {} for node in schema.nodes
    }
    relations: dict[
        tuple[str, str, str, str, str],
        dict[tuple[int, str, str, str], OntologyEvidence],
    ] = {}
    emissions: dict[str, tuple[set[str], set[str]]] = {}

    def add_node(node_type: str, node_id: str, values: dict[str, Any]) -> None:
        node = _validated_node(definitions[node_type], values)
        current = nodes_by_type[node_type].get(node_id)
        if current is not None and current != node:
            raise RuntimeError(f"Deterministic ID collision for {node_id}")
        nodes_by_type[node_type][node_id] = node

    def add_relation(
        *,
        from_type: str,
        from_id: str,
        to_type: str,
        to_id: str,
        spans: Sequence[ValidatedDiagnosticEvidenceSpan],
        branch_id: str,
    ) -> None:
        name = relation_names[(from_type, to_type)]
        key = (name, from_type, from_id, to_type, to_id)
        evidence = relations.setdefault(key, {})
        for item in _relation_evidence(spans):
            evidence[(item.source_page, item.source_reference, item.source_anchor, item.quote)] = item
        branch_nodes, branch_relations = emissions.setdefault(branch_id, (set(), set()))
        branch_nodes.update((from_id, to_id))
        branch_relations.add(f"{name}:{from_id}->{to_id}")

    source_scope = {"source_type": source_type, "source_title": source_title}
    for bundle in sorted(bundles, key=lambda item: item.branch_lineage_id):
        if bundle.failure is None or not bundle.actions:
            raise RuntimeError("Only complete bundles may reach ontology compilation")

        component_id: str | None = None
        if bundle.affected_component is not None:
            component = bundle.affected_component
            # Component.category is ontology-required, while the source may
            # name a concrete part without stating its functional taxonomy.
            # Derive the neutral schema value from claim kind; never ask the
            # model to invent a category or reject an otherwise grounded edge.
            component_category = component.category or "source_named_component"
            component_claim = {
                **source_scope,
                "name": component.name,
                "description": component.description,
                "category": component_category,
            }
            component_id = _graph_id("Component", component.name, component_claim)
            add_node(
                "Component",
                component_id,
                {
                    _id_property(definitions["Component"]): component_id,
                    "name": component.name,
                    "description": component.description,
                    "category": component_category,
                },
            )

        failure = bundle.failure
        material_context = component_id or "asset_level"
        failure_claim = {
            **source_scope,
            "name": failure.name,
            "description": failure.description,
            "material_context": material_context,
        }
        failure_id = _graph_id("FailureMode", failure.name, failure_claim)
        add_node(
            "FailureMode",
            failure_id,
            {
                _id_property(definitions["FailureMode"]): failure_id,
                "name": failure.name,
                "description": failure.description,
                "material_context": material_context,
            },
        )

        if bundle.affected_component is not None and component_id is not None:
            add_relation(
                from_type="FailureMode",
                from_id=failure_id,
                to_type="Component",
                to_id=component_id,
                spans=bundle.affected_component.affects_link_evidence,
                branch_id=bundle.branch_lineage_id,
            )

        for indicator in bundle.indicators:
            if isinstance(indicator, ValidatedSymptomIndicator):
                node_type = "Symptom"
                label = indicator.name
                claim = {
                    **source_scope,
                    "name": indicator.name,
                    "description": indicator.description,
                    "severity": indicator.severity,
                }
                values = {
                    "name": indicator.name,
                    "description": indicator.description,
                    "severity": indicator.severity,
                }
            else:
                node_type = "ErrorCode"
                label = indicator.code
                claim = {
                    **source_scope,
                    "code": indicator.code,
                    "name": indicator.name,
                    "description": indicator.description,
                }
                values = {
                    "code": indicator.code,
                    "name": indicator.name,
                    "description": indicator.description,
                }
            indicator_id = _graph_id(node_type, label, claim)
            values[_id_property(definitions[node_type])] = indicator_id
            add_node(node_type, indicator_id, values)
            add_relation(
                from_type=node_type,
                from_id=indicator_id,
                to_type="FailureMode",
                to_id=failure_id,
                spans=indicator.failure_link_evidence,
                branch_id=bundle.branch_lineage_id,
            )

        for action in bundle.actions:
            action_claim = {
                **source_scope,
                "name": action.name,
                "description": action.description,
                "instruction_text": action.instruction_text,
                "action_kind": action.action_kind,
            }
            action_id = _graph_id("CorrectiveAction", action.name, action_claim)
            values = {
                _id_property(definitions["CorrectiveAction"]): action_id,
                "name": action.name,
                "description": action.description,
                "instruction_text": action.instruction_text,
                "source_type": source_type,
                "source_title": source_title,
                "source_reference": action.claim_evidence[0].evidence_id,
            }
            if action.action_kind:
                values["action_kind"] = action.action_kind
            add_node("CorrectiveAction", action_id, values)
            add_relation(
                from_type="FailureMode",
                from_id=failure_id,
                to_type="CorrectiveAction",
                to_id=action_id,
                spans=action.resolution_link_evidence,
                branch_id=bundle.branch_lineage_id,
            )

    relation_instances = [
        OntologyRelationInstance(
            name=key[0],
            from_type=key[1],
            from_id=key[2],
            to_type=key[3],
            to_id=key[4],
            evidence=[evidence[evidence_key] for evidence_key in sorted(evidence)],
        )
        for key, evidence in sorted(relations.items())
    ]
    ontology = OntologyInstance(
        ontology_name=schema.ontology_name,
        version=schema.version,
        language=language,
        source_type=source_type,
        source_title=source_title,
        nodes={
            node.name: [
                nodes_by_type[node.name][node_id]
                for node_id in sorted(nodes_by_type[node.name])
            ]
            for node in schema.nodes
        },
        relations=relation_instances,
    )
    rendered_emissions = {
        branch_id: (sorted(node_ids), sorted(relation_ids))
        for branch_id, (node_ids, relation_ids) in emissions.items()
    }
    return ontology, rendered_emissions


def _bundle_evidence_ids(bundle: ValidatedDiagnosticBundle | None) -> list[str]:
    if bundle is None:
        return []
    ids: set[str] = set()

    def add(spans: Sequence[ValidatedDiagnosticEvidenceSpan]) -> None:
        ids.update(span.evidence_id for span in spans)

    for indicator in bundle.indicators:
        add(indicator.claim_evidence)
        add(indicator.failure_link_evidence)
    if bundle.failure is not None:
        add(bundle.failure.claim_evidence)
    for action in bundle.actions:
        add(action.claim_evidence)
        add(action.resolution_link_evidence)
    if bundle.affected_component is not None:
        add(bundle.affected_component.claim_evidence)
        add(bundle.affected_component.affects_link_evidence)
    return sorted(ids)


def compile_diagnostic_bundles(
    candidates: (
        DiagnosticChunkOutput
        | Mapping[str, Any]
        | Sequence[DiagnosticBundleCandidate | Mapping[str, Any]]
    ),
    *,
    source_type: str,
    source_title: str,
    evidence_units: Sequence[EvidenceUnit] = (),
    legacy_chunks: Sequence[Mapping[str, Any]] = (),
    text_with_pages: str | None = None,
    schema: OntologySchemaDefinition | None = None,
    language: str | None = None,
) -> DiagnosticBundleCompilationResult:
    """Validate, disposition and compile only complete grounded bundles.

    The returned ontology is publication-safe: gap/review/exclude branches do
    not leak partial nodes into it.  Their evidence-resolved forms and explicit
    reasons remain available in ``validated_bundles`` and ``report``.
    """

    source_type = _required_source_value(source_type, "source_type")
    source_title = _required_source_value(source_title, "source_title")
    schema = schema or load_ontology_schema()
    chunk_output: DiagnosticChunkOutput | None = None
    if isinstance(candidates, DiagnosticChunkOutput):
        chunk_output = candidates
    elif isinstance(candidates, Mapping) and "records" in candidates:
        chunk_output = DiagnosticChunkOutput.model_validate(candidates)

    raw_candidates: Sequence[DiagnosticBundleCandidate | Mapping[str, Any]]
    if chunk_output is not None:
        raw_candidates = chunk_output.records
    elif isinstance(candidates, Mapping):
        raw_candidates = [candidates]
    else:
        raw_candidates = candidates

    language = _display_text(
        language
        or (chunk_output.source_language if chunk_output is not None else "")
        or schema.language
    )
    if not language:
        raise ValueError("language must not be empty")

    typed_candidates = [
        item
        if isinstance(item, DiagnosticBundleCandidate)
        else DiagnosticBundleCandidate.model_validate(item)
        for item in raw_candidates
    ]
    by_branch: dict[str, DiagnosticBundleCandidate] = {}
    for candidate in typed_candidates:
        branch_id = diagnostic_branch_lineage_id(
            candidate,
            source_type=source_type,
            source_title=source_title,
        )
        current = by_branch.get(branch_id)
        if current is not None and _canonical_json(current) != _canonical_json(candidate):
            raise ValueError(f"Conflicting candidates share branch lineage {branch_id}")
        by_branch[branch_id] = candidate

    index = _evidence_index(evidence_units, legacy_chunks, text_with_pages)
    validated: list[ValidatedDiagnosticBundle] = []
    staged: list[
        tuple[
            DiagnosticBundleCandidate,
            str,
            str,
            BundleDisposition,
            list[BundleDropReason],
            ValidatedDiagnosticBundle | None,
        ]
    ] = []
    for branch_id, candidate in sorted(by_branch.items()):
        record_id = diagnostic_record_lineage_id(
            candidate,
            source_type=source_type,
            source_title=source_title,
        )
        evidence_problems: Sequence[EvidenceValidationProblem] = ()
        resolved: ValidatedDiagnosticBundle | None = None
        if candidate.resolution_status is ResolutionStatus.NOT_DIAGNOSTIC:
            exclusion_problems: list[EvidenceValidationProblem] = []
            _validate_lineage_anchor(
                candidate.record_anchor,
                path="record_anchor",
                index=index,
                problems=exclusion_problems,
            )
            _validate_lineage_anchor(
                candidate.branch_anchor,
                path="branch_anchor",
                index=index,
                problems=exclusion_problems,
            )
            evidence_problems = exclusion_problems
        else:
            try:
                resolved = _validated_bundle(
                    candidate,
                    index=index,
                    source_type=source_type,
                    source_title=source_title,
                )
                validated.append(resolved)
            except DiagnosticBundleEvidenceError as exc:
                evidence_problems = exc.problems
        disposition, reasons = _classify_candidate(candidate, evidence_problems)
        staged.append((candidate, record_id, branch_id, disposition, reasons, resolved))

    published = [
        resolved
        for _, _, _, disposition, _, resolved in staged
        if disposition is BundleDisposition.PUBLISH and resolved is not None
    ]
    ontology, emissions = _compile_published(
        published,
        schema=schema,
        source_type=source_type,
        source_title=source_title,
        language=language,
    )

    entries: list[BundleCompilationEntry] = []
    drop_counts: Counter[str] = Counter()
    disposition_counts: Counter[str] = Counter()
    for candidate, record_id, branch_id, disposition, reasons, resolved in staged:
        disposition_counts[disposition.value] += 1
        if disposition is not BundleDisposition.PUBLISH:
            drop_counts.update(reason.code for reason in reasons)
        node_ids, relation_ids = emissions.get(branch_id, ([], []))
        entries.append(
            BundleCompilationEntry(
                record_lineage_id=record_id,
                branch_lineage_id=branch_id,
                record_anchor=candidate.record_anchor,
                branch_anchor=candidate.branch_anchor,
                evidence_ids=(
                    _bundle_evidence_ids(resolved)
                    or sorted({
                        anchor
                        for anchor in (candidate.record_anchor, candidate.branch_anchor)
                        if anchor in index
                    })
                ),
                disposition=disposition,
                drop_reasons=reasons,
                emitted_node_ids=node_ids,
                emitted_relations=relation_ids,
            )
        )

    all_dispositions = {item.value: disposition_counts[item.value] for item in BundleDisposition}
    report = DiagnosticBundleCompilationReport(
        input_candidates=len(typed_candidates),
        unique_candidates=len(by_branch),
        duplicate_candidates=len(typed_candidates) - len(by_branch),
        disposition_counts=all_dispositions,
        dropped_items_by_reason=dict(sorted(drop_counts.items())),
        entries=entries,
    )
    return DiagnosticBundleCompilationResult(
        ontology=ontology,
        validated_bundles=sorted(validated, key=lambda item: item.branch_lineage_id),
        report=report,
    )
