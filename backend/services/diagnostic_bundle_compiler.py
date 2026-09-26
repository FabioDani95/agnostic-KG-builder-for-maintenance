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
    ValidatedDiagnosticCondition,
    ValidatedDiagnosticEvidenceSpan,
    ValidatedDiagnosticInspectionStep,
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
    record_window_id: str = ""
    record_anchor: str
    branch_anchor: str
    evidence_ids: list[str] = Field(default_factory=list)
    resolved_evidence_ids: list[str] = Field(default_factory=list)
    candidate: dict[str, Any]
    validated_record: ValidatedDiagnosticBundle | None = None
    source_gap_verified: bool = False
    disposition: BundleDisposition
    accounting_state: str = ""
    compiler_recoveries: list[BundleDropReason] = Field(default_factory=list)
    drop_reasons: list[BundleDropReason] = Field(default_factory=list)
    emitted_node_ids: list[str] = Field(default_factory=list)
    emitted_relations: list[str] = Field(default_factory=list)


class DiagnosticBundleCompilationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    input_candidates: int = Field(ge=0)
    unique_candidates: int = Field(ge=0)
    duplicate_candidates: int = Field(ge=0)
    disposition_counts: dict[str, int]
    recovered_items_by_reason: dict[str, int] = Field(default_factory=dict)
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
    ordinal: int


@dataclass(frozen=True)
class _EvidenceIndex:
    """Canonical anchor lookup plus physical/rendered adjacency information."""

    by_anchor: dict[str, tuple[_EvidenceRecord, ...]]
    ordered: tuple[_EvidenceRecord, ...]

    def get(self, anchor: str) -> tuple[_EvidenceRecord, ...] | None:
        return self.by_anchor.get(anchor)

    def __contains__(self, anchor: object) -> bool:
        return anchor in self.by_anchor


def _scoped_evidence_index(
    index: _EvidenceIndex,
    allowed_evidence_spans: Mapping[str, Sequence[str]],
) -> _EvidenceIndex:
    """Restrict canonical anchors to system-selected literal branch fragments.

    A table row may contain several cause/remedy pairs under one EvidenceUnit.
    Anchor-level filtering cannot prevent the compiler from accepting a hidden
    sibling branch.  This derived index retains the canonical locator but makes
    only exact fragments from the structural inventory resolvable.
    """

    scoped: list[_EvidenceRecord] = []
    for anchor, fragments in sorted(allowed_evidence_spans.items()):
        records = index.get(str(anchor).strip()) or ()
        exact_fragments = _dedupe_display(fragments)
        for record in records:
            canonical = _display_text(record.text)
            for fragment in exact_fragments:
                if fragment and fragment in canonical:
                    scoped.append(
                        _EvidenceRecord(
                            evidence_id=record.evidence_id,
                            page=record.page,
                            text=fragment,
                            locator=record.locator,
                            priority=record.priority,
                            ordinal=record.ordinal,
                        )
                    )
    by_anchor: dict[str, list[_EvidenceRecord]] = {}
    for record in scoped:
        by_anchor.setdefault(record.evidence_id, []).append(record)
    return _EvidenceIndex(
        by_anchor={anchor: tuple(records) for anchor, records in by_anchor.items()},
        ordered=tuple(scoped),
    )


def _dedupe_display(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(_display_text(value) for value in values if _display_text(value)))


def _display_text(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or ""))).strip()


def _identity_text(value: str) -> str:
    return _display_text(value).casefold()


def _canonical_value(value: Any, field: str = "") -> Any:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    if isinstance(value, Mapping):
        return {
            str(key): _canonical_value(item, str(key))
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        items = [_canonical_value(item) for item in value]
        if field in {"actions", "inspection_steps", "conditions"}:
            return items
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
        "record_window_id": candidate.record_window_id,
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

    payload = candidate.model_dump(
        mode="json",
        exclude={"resolution_status", "allowed_source_anchors"},
    )
    return f"dbranch_{_digest({'source_type': source_type, 'source_title': source_title, 'bundle': payload})}"


def _legacy_page(mapping: Mapping[str, Any]) -> int | None:
    for key in ("source_page", "page_number", "page"):
        value = mapping.get(key)
        if isinstance(value, int) and value >= 1:
            return value
        if isinstance(value, str) and value.strip().isdigit() and int(value) >= 1:
            return int(value)
    return None


def _legacy_records(
    chunk: Mapping[str, Any],
    *,
    start_ordinal: int = 0,
) -> list[_EvidenceRecord]:
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
                ordinal=start_ordinal,
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
                ordinal=start_ordinal + index,
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
) -> _EvidenceIndex:
    records: list[_EvidenceRecord] = []

    def evidence_order(unit: EvidenceUnit) -> tuple[int, int, int, int, str]:
        locator = unit.locator
        if not isinstance(locator, PdfLocator):
            return (0, 9, 0, 0, str(unit.evidence_id))
        if locator.block_index is not None:
            kind_rank, primary, secondary = 0, locator.block_index, 0
        elif locator.table_index is not None:
            kind_rank, primary, secondary = 1, locator.table_index, locator.row_index or 0
        elif locator.ocr_region_index is not None:
            kind_rank, primary, secondary = 2, locator.ocr_region_index, 0
        else:
            kind_rank, primary, secondary = 3, 0, 0
        return (locator.page, kind_rank, primary, secondary, str(unit.evidence_id))

    for unit in sorted(evidence_units, key=evidence_order):
        if not isinstance(unit.locator, PdfLocator):
            raise ValueError("Diagnostic PDF bundles require PdfLocator evidence units")
        records.append(
            _EvidenceRecord(
                evidence_id=str(unit.evidence_id),
                page=unit.locator.page,
                text=unit.locator.quote,
                locator=unit.locator.model_dump(mode="json"),
                priority=0,
                ordinal=len(records),
            )
        )
    for chunk in legacy_chunks:
        records.extend(_legacy_records(chunk, start_ordinal=len(records)))
    if text_with_pages:
        for chunk in _chunks_from_text_with_pages(text_with_pages):
            records.extend(_legacy_records(chunk, start_ordinal=len(records)))

    unique: dict[tuple[str, int, str], _EvidenceRecord] = {}
    for record in records:
        key = (record.evidence_id, record.page, _display_text(record.text))
        current = unique.get(key)
        if current is None or record.priority < current.priority:
            unique[key] = record

    by_anchor: dict[str, list[_EvidenceRecord]] = {}
    for record in unique.values():
        by_anchor.setdefault(record.evidence_id, []).append(record)
    rendered = {
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
    return _EvidenceIndex(
        by_anchor=rendered,
        ordered=tuple(sorted(unique.values(), key=lambda item: (item.priority, item.ordinal))),
    )


def _resolve_span(
    span: DiagnosticEvidenceSpan,
    *,
    path: str,
    index: _EvidenceIndex,
    allowed_source_anchors: frozenset[str] | None = None,
) -> tuple[list[ValidatedDiagnosticEvidenceSpan], EvidenceValidationProblem | None]:
    anchor = span.source_anchor.strip()
    records = index.get(anchor)
    page_records = [record for record in (records or ()) if record.page == span.source_page]
    quote = _display_text(span.quote)
    anchor_is_allowed = (
        allowed_source_anchors is None
        or anchor in allowed_source_anchors
    )
    matching = [
        record
        for record in page_records
        if anchor_is_allowed and quote and quote in _display_text(record.text)
    ]
    if matching:
        best_priority = min(record.priority for record in matching)
        preferred = [record for record in matching if record.priority == best_priority]
        canonical_texts = {_display_text(record.locator.get("quote", record.text)) for record in preferred}
        if len(canonical_texts) > 1:
            return [], EvidenceValidationProblem(
                code="ambiguous_source_anchor",
                path=path,
                message=f"{path}: anchor {anchor!r} resolves to conflicting source evidence",
            )

        record = preferred[0]
        return ([
            ValidatedDiagnosticEvidenceSpan(
                source_anchor=anchor,
                source_page=span.source_page,
                quote=quote,
                evidence_id=record.evidence_id,
                locator=record.locator,
            ),
        ], None)

    if allowed_source_anchors and anchor_is_allowed and page_records and quote:
        # Scoped cells can share one canonical row anchor. Accept a quoted
        # union only when it is literally present in that canonical row and
        # every non-separator character belongs to allowed cells. This cannot
        # admit a sibling cell omitted by the deterministic window.
        best_priority = min(record.priority for record in page_records)
        source_records = [record for record in page_records if record.priority == best_priority]
        canonical = {_display_text(record.locator.get("quote", "")) for record in source_records}
        if len(canonical) == 1:
            full = next(iter(canonical))
            if quote in full:
                coverage = [False] * len(full)
                for record in source_records:
                    fragment = _display_text(record.text)
                    start = full.find(fragment) if fragment else -1
                    while start >= 0:
                        coverage[start:start + len(fragment)] = [True] * len(fragment)
                        start = full.find(fragment, start + 1)
                start = full.find(quote)
                if all(coverage[i] or full[i].isspace() or full[i] == "|" for i in range(start, start + len(quote))):
                    record = source_records[0]
                    return [ValidatedDiagnosticEvidenceSpan(source_anchor=anchor, source_page=span.source_page, quote=quote, evidence_id=record.evidence_id, locator=record.locator)], None

    # In a system-owned record window the model does not own anchor routing.
    # Repair only the mechanical case where its normalized verbatim quote has
    # one, and only one, exact home in the immutable allow-list.  Page identity
    # remains strict; a wrong page is not silently rewritten.
    if allowed_source_anchors:
        relocated = _resolve_unique_window_direct_span(
            span,
            quote=quote,
            index=index,
            allowed_source_anchors=allowed_source_anchors,
        )
        if relocated is not None:
            return [relocated], None

    composite = _resolve_composite_span(
        span,
        path=path,
        anchor_records=page_records,
        index=index,
        allowed_source_anchors=allowed_source_anchors,
    )
    if composite:
        return composite, None

    if allowed_source_anchors is not None and not anchor_is_allowed:
        return [], EvidenceValidationProblem(
            code="source_anchor_outside_record_window",
            path=path,
            message=(
                f"{path}: source anchor {anchor!r} is outside the system-owned "
                "record window and its quote has no unique exact relocation inside it"
            ),
        )

    if not records:
        return [], EvidenceValidationProblem(
            code="unknown_source_anchor",
            path=path,
            message=f"{path}: source anchor {anchor!r} does not resolve",
        )
    if not page_records:
        pages = sorted({record.page for record in records})
        return [], EvidenceValidationProblem(
            code="source_page_mismatch",
            path=path,
            message=(
                f"{path}: anchor {anchor!r} is on page(s) {pages}, not page {span.source_page}"
            ),
        )
    return [], EvidenceValidationProblem(
        code="quote_not_in_anchored_evidence",
        path=path,
        message=(
            f"{path}: quote is not an exact lexical span of anchor {anchor!r} "
            "or a unique contiguous EvidenceUnit support set"
        ),
    )


def _resolve_unique_window_direct_span(
    span: DiagnosticEvidenceSpan,
    *,
    quote: str,
    index: _EvidenceIndex,
    allowed_source_anchors: frozenset[str],
) -> ValidatedDiagnosticEvidenceSpan | None:
    """Relocate one exact quote to a unique anchor in its immutable window."""

    if not quote:
        return None
    matches: dict[tuple[str, int, str], _EvidenceRecord] = {}
    for allowed_anchor in sorted(allowed_source_anchors):
        records = [
            record
            for record in (index.get(allowed_anchor) or ())
            if record.page == span.source_page
            and quote in _display_text(record.text)
        ]
        if not records:
            continue
        best_priority = min(record.priority for record in records)
        for record in records:
            if record.priority != best_priority:
                continue
            signature = (
                record.evidence_id,
                record.page,
                _display_text(record.locator.get("quote", record.text)),
            )
            matches[signature] = record
    if len(matches) != 1:
        return None
    record = next(iter(matches.values()))
    return ValidatedDiagnosticEvidenceSpan(
        source_anchor=record.evidence_id,
        source_page=record.page,
        quote=quote,
        evidence_id=record.evidence_id,
        locator=record.locator,
    )


def _records_are_contiguous(records: Sequence[_EvidenceRecord]) -> bool:
    if not records:
        return False
    if len({record.priority for record in records}) != 1:
        return False
    if any(right.ordinal != left.ordinal + 1 for left, right in zip(records, records[1:])):
        return False
    return all(0 <= right.page - left.page <= 1 for left, right in zip(records, records[1:]))


def _composite_span_parts(
    quote: str,
    records: Sequence[_EvidenceRecord],
) -> list[tuple[_EvidenceRecord, str]]:
    """Split one exact quote across its minimal contiguous canonical supports."""

    texts = [_display_text(record.text) for record in records]
    joined = " ".join(texts)
    start = joined.find(quote)
    if start < 0:
        return []
    finish = start + len(quote)
    parts: list[tuple[_EvidenceRecord, str]] = []
    cursor = 0
    for record, text in zip(records, texts):
        text_start = cursor
        text_finish = text_start + len(text)
        overlap_start = max(start, text_start)
        overlap_finish = min(finish, text_finish)
        if overlap_start < overlap_finish:
            piece = text[overlap_start - text_start : overlap_finish - text_start].strip()
            if piece:
                parts.append((record, piece))
        cursor = text_finish + 1
    return parts if len(parts) >= 2 else []


def _resolve_composite_span(
    span: DiagnosticEvidenceSpan,
    *,
    path: str,
    anchor_records: Sequence[_EvidenceRecord],
    index: _EvidenceIndex,
    allowed_source_anchors: frozenset[str] | None = None,
) -> list[ValidatedDiagnosticEvidenceSpan]:
    """Resolve a quote spanning adjacent EvidenceUnits without fuzzy matching.

    The quote must still occur byte-for-normalized-byte in a unique contiguous
    concatenation.  Each emitted EvidenceRef contains only the exact substring
    contributed by its canonical unit.
    """

    del path  # Kept in the signature for debugger/log call-site context.
    quote = _display_text(span.quote)
    if not quote:
        return []
    ordered = list(index.ordered)
    matches: list[tuple[int, int, list[tuple[_EvidenceRecord, str]]]] = []
    candidate_ranges: set[tuple[int, int]] = set()
    if allowed_source_anchors:
        # Search the complete immutable window, not around the model-selected
        # anchor.  Every support unit must be allow-listed and physically
        # contiguous in the canonical inventory.  At least one support keeps
        # the model-provided page attribution exact.
        for left, record in enumerate(ordered):
            if record.evidence_id not in allowed_source_anchors:
                continue
            for right in range(left + 2, min(len(ordered), left + 6) + 1):
                candidate_records = ordered[left:right]
                if not all(
                    item.evidence_id in allowed_source_anchors
                    for item in candidate_records
                ):
                    continue
                if not any(item.page == span.source_page for item in candidate_records):
                    continue
                candidate_ranges.add((left, right))
    else:
        for anchor_record in anchor_records:
            try:
                position = ordered.index(anchor_record)
            except ValueError:
                continue
            # Diagnostic records are deliberately local.  Six canonical units
            # are enough for split headings/problem/cause/remedy and keep
            # adjacency from becoming an unconstrained page shortcut.
            for left in range(max(0, position - 5), position + 1):
                for right in range(position + 1, min(len(ordered), left + 6) + 1):
                    candidate_ranges.add((left, right))

    for left, right in sorted(candidate_ranges):
        candidate_records = ordered[left:right]
        if len(candidate_records) < 2 or not _records_are_contiguous(candidate_records):
            continue
        parts = _composite_span_parts(quote, candidate_records)
        if parts and (
            not allowed_source_anchors
            or any(record.page == span.source_page for record, _piece in parts)
        ):
            matches.append((len(candidate_records), left, parts))
    if not matches:
        return []
    matches.sort(key=lambda item: (item[0], item[1]))
    best_size = matches[0][0]
    best = [item for item in matches if item[0] == best_size]
    signatures = {
        tuple((record.evidence_id, record.page, piece) for record, piece in parts)
        for _, _, parts in best
    }
    if len(signatures) != 1:
        return []
    parts = best[0][2]
    return [
        ValidatedDiagnosticEvidenceSpan(
            source_anchor=record.evidence_id,
            source_page=record.page,
            quote=piece,
            evidence_id=record.evidence_id,
            locator=record.locator,
        )
        for record, piece in parts
    ]


def _resolve_spans(
    spans: Sequence[DiagnosticEvidenceSpan],
    *,
    path: str,
    index: _EvidenceIndex,
    problems: list[EvidenceValidationProblem],
    allowed_source_anchors: frozenset[str] | None = None,
) -> list[ValidatedDiagnosticEvidenceSpan]:
    resolved: dict[tuple[str, int, str], ValidatedDiagnosticEvidenceSpan] = {}
    for position, span in enumerate(spans):
        items, problem = _resolve_span(
            span,
            path=f"{path}[{position}]",
            index=index,
            allowed_source_anchors=allowed_source_anchors,
        )
        if problem is not None:
            problems.append(problem)
        else:
            for item in items:
                resolved[(item.source_anchor, item.source_page, item.quote)] = item
    return [resolved[key] for key in sorted(resolved)]


def _validate_lineage_anchor(
    anchor: str,
    *,
    path: str,
    index: _EvidenceIndex,
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


def _validate_window_lineage_membership(
    *,
    record_anchor: str,
    branch_anchor: str,
    record_window_id: str,
    allowed_source_anchors: frozenset[str],
    problems: list[EvidenceValidationProblem],
) -> None:
    """Require system lineage to remain inside its immutable source window."""

    for path, anchor in (
        ("record_anchor", record_anchor),
        ("branch_anchor", branch_anchor),
    ):
        if anchor in allowed_source_anchors:
            continue
        problems.append(
            EvidenceValidationProblem(
                code="lineage_anchor_outside_record_window",
                path=path,
                message=(
                    f"{path} {anchor!r} is outside system-owned record window "
                    f"{record_window_id!r}"
                ),
            )
        )


def _validated_bundle(
    candidate: DiagnosticBundleCandidate,
    *,
    index: _EvidenceIndex,
    source_type: str,
    source_title: str,
    structural_edge_support: bool = False,
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
    allowed_source_anchors = frozenset({
        str(anchor).strip()
        for anchor in candidate.allowed_source_anchors
        if str(anchor).strip()
    })
    if candidate.record_window_id:
        _validate_window_lineage_membership(
            record_anchor=record_anchor,
            branch_anchor=branch_anchor,
            record_window_id=candidate.record_window_id,
            allowed_source_anchors=allowed_source_anchors,
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
            allowed_source_anchors=(
                allowed_source_anchors if candidate.record_window_id else None
            ),
        )
        links = _resolve_spans(
            indicator.failure_link_evidence,
            path=f"{prefix}.failure_link_evidence",
            index=index,
            problems=problems,
            allowed_source_anchors=(
                allowed_source_anchors if candidate.record_window_id else None
            ),
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
            allowed_source_anchors=(
                allowed_source_anchors if candidate.record_window_id else None
            ),
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
            allowed_source_anchors=(
                allowed_source_anchors if candidate.record_window_id else None
            ),
        )
        action_links = _resolve_spans(
            action.resolution_link_evidence,
            path=f"actions[{position}].resolution_link_evidence",
            index=index,
            problems=problems,
            allowed_source_anchors=(
                allowed_source_anchors if candidate.record_window_id else None
            ),
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

    inspection_steps: list[ValidatedDiagnosticInspectionStep] = []
    for position, step in enumerate(candidate.inspection_steps):
        step_claims = _resolve_spans(
            step.claim_evidence,
            path=f"inspection_steps[{position}].claim_evidence",
            index=index,
            problems=problems,
            allowed_source_anchors=(
                allowed_source_anchors if candidate.record_window_id else None
            ),
        )
        if step_claims:
            inspection_steps.append(
                ValidatedDiagnosticInspectionStep(
                    instruction_text=_display_text(step.instruction_text),
                    claim_evidence=step_claims,
                )
            )

    conditions: list[ValidatedDiagnosticCondition] = []
    for position, condition in enumerate(candidate.conditions):
        spans = _resolve_spans(
            condition.claim_evidence, path=f"conditions[{position}].claim_evidence",
            index=index, problems=problems,
            allowed_source_anchors=allowed_source_anchors if candidate.record_window_id else None,
        )
        if spans:
            conditions.append(ValidatedDiagnosticCondition(
                text=condition.text, applies_to=condition.applies_to,
                step_index=condition.step_index, claim_evidence=spans,
            ))

    component: ValidatedAffectedComponent | None = None
    if candidate.affected_component is not None:
        component_claims = _resolve_spans(
            candidate.affected_component.claim_evidence,
            path="affected_component.claim_evidence",
            index=index,
            problems=problems,
            allowed_source_anchors=(
                allowed_source_anchors if candidate.record_window_id else None
            ),
        )
        component_links = _resolve_spans(
            candidate.affected_component.affects_link_evidence,
            path="affected_component.affects_link_evidence",
            index=index,
            problems=problems,
            allowed_source_anchors=(
                allowed_source_anchors if candidate.record_window_id else None
            ),
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
    for step in inspection_steps:
        claim_anchors.update(span.source_anchor for span in step.claim_evidence)
    for condition in conditions:
        claim_anchors.update(span.source_anchor for span in condition.claim_evidence)
    if component is not None:
        claim_anchors.update(span.source_anchor for span in component.claim_evidence)
        edge_anchors.update(span.source_anchor for span in component.affects_link_evidence)

    if candidate.record_window_id:
        for anchor in sorted((claim_anchors | edge_anchors) - allowed_source_anchors):
            problems.append(
                EvidenceValidationProblem(
                    code="resolved_anchor_outside_record_window",
                    path="allowed_source_anchors",
                    message=(
                        f"Composite evidence resolved anchor {anchor!r} outside "
                        f"system-owned record window {candidate.record_window_id!r}"
                    ),
                )
            )

    candidate_claim_anchors = {
        span.source_anchor
        for indicator in candidate.indicators
        for span in indicator.claim_evidence
    }
    if candidate.failure is not None:
        candidate_claim_anchors.update(
            span.source_anchor for span in candidate.failure.claim_evidence
        )
    for action in candidate.actions:
        candidate_claim_anchors.update(span.source_anchor for span in action.claim_evidence)
    for step in candidate.inspection_steps:
        candidate_claim_anchors.update(span.source_anchor for span in step.claim_evidence)
    for condition in candidate.conditions:
        candidate_claim_anchors.update(span.source_anchor for span in condition.claim_evidence)
    if candidate.affected_component is not None:
        candidate_claim_anchors.update(
            span.source_anchor for span in candidate.affected_component.claim_evidence
        )
    candidate_support_anchors = set(candidate_claim_anchors)
    candidate_support_anchors.update(
        span.source_anchor
        for indicator in candidate.indicators
        for span in indicator.failure_link_evidence
    )
    for action in candidate.actions:
        candidate_support_anchors.update(
            span.source_anchor for span in action.resolution_link_evidence
        )
    if candidate.affected_component is not None:
        candidate_support_anchors.update(
            span.source_anchor for span in candidate.affected_component.affects_link_evidence
        )

    if not candidate.record_window_id:
        # Legacy/model-owned lineage remains subject to the historical gate.
        # A system-owned window has already validated existence + allow-list
        # membership above; requiring the LLM to echo those locators in a
        # particular evidence field would hand lineage ownership back to it.
        if record_anchor not in candidate_claim_anchors:
            problems.append(
                EvidenceValidationProblem(
                    code="lineage_anchor_outside_bundle",
                    path="record_anchor",
                    message=(
                        f"record_anchor {record_anchor!r} does not support any claim in this record"
                    ),
                )
            )
        branch_support_anchors = candidate_support_anchors
        if branch_anchor not in branch_support_anchors:
            problems.append(
                EvidenceValidationProblem(
                    code="lineage_anchor_outside_bundle",
                    path="branch_anchor",
                    message=(
                        f"branch_anchor {branch_anchor!r} does not belong to this branch's "
                        "claim/edge support set"
                    ),
                )
            )

    def supports_claim(link, claims):
        return any(
            _display_text(claim.quote) in _display_text(link.quote)
            or claim.evidence_id == link.evidence_id
            for claim in claims
        )

    def labeled_record_support(links, left, right):
        anchors = {span.evidence_id for span in links}
        if not ({span.evidence_id for span in left} & anchors and {span.evidence_id for span in right} & anchors):
            return False
        positions = [position for position, record in enumerate(index.ordered) if record.evidence_id in anchors]
        if not positions:
            return False
        region = index.ordered[min(positions):max(positions) + 1]
        if not _records_are_contiguous(region):
            return False
        text = "\n".join(record.text for record in region)
        roots = re.findall(r"(?im)^\s*(?:problem|symptom|fault|alarm|error(?: code)?)\s*:", text)
        causes = re.findall(r"(?im)^\s*(?:possible\s+)?(?:cause|reason)\s*:", text)
        remedies = re.findall(r"(?im)^\s*(?:remedy|solution|corrective action)\s*:", text)
        # Cause->remedy may start after the root, but no second cause/remedy
        # or unrelated problem can intervene. All spans remain literal.
        return len(roots) <= 1 and len(causes) == 1 and len(remedies) <= 1

    def explicit_cause_list_support(links, left, right):
        """A causal lead-in scopes consecutive bullets, never later remedies.

        This establishes only indicator -> possible cause. Physical proximity
        to a procedure or a shared component is not a resolution proof.
        """
        linked = {s.evidence_id for s in [*links, *left, *right]}
        for start, root in enumerate(index.ordered):
            if root.evidence_id not in linked or not any(s.evidence_id == root.evidence_id for s in left):
                continue
            if not re.search(r"(?i)\b(?:root\s+)?causes?\s+(?:may\s+be|can\s+be|include|are)\s*:\s*$", root.text):
                continue
            previous = root
            for bullet in index.ordered[start + 1:]:
                if bullet.page != root.page or not _records_are_contiguous([previous, bullet]):
                    break
                if not re.match(r"^\s*[\u2022\u25a0\u25a1\u25aa\u25cf\uf06e\uf071\uf06c]", bullet.text):
                    break
                if bullet.evidence_id in linked and any(s.evidence_id == bullet.evidence_id and _display_text(s.quote) in _display_text(bullet.text) for s in right):
                    return [ValidatedDiagnosticEvidenceSpan(source_anchor=r.evidence_id, source_page=r.page,
                              quote=_display_text(r.text), evidence_id=r.evidence_id, locator=r.locator) for r in (root, bullet)]
                previous = bullet
        return False

    def check_link(links, left, right, path):
        if not links or not left or not right or structural_edge_support:
            return
        # A literal span proving only the other endpoint cannot establish an
        # edge. Distributed endpoint unions need a system-verified table row.
        cause_list = path.startswith("indicators[") and explicit_cause_list_support(links, left, right)
        if not any(supports_claim(link, left) and supports_claim(link, right) for link in links) and not labeled_record_support(links, left, right) and not cause_list:
            problems.append(EvidenceValidationProblem(
                code="relation_endpoint_support_unestablished", path=path,
                message="The support does not cover both endpoints in one passage, one contiguous labeled record or a verified structural branch; adjudication is required.",
            ))

    if failure is not None:
        if not structural_edge_support and indicators and all(
            re.match(r"(?is)^\s*(?:\d+[.)]\s*)?(?:check|inspect|verify|examine|measure|test)\b", _display_text(span.locator.get("quote", "")))
            for indicator in indicators for span in indicator.claim_evidence
        ):
            problems.append(EvidenceValidationProblem(
                code="indicator_inferred_from_inspection", path="indicators.claim_evidence",
                message="The full source passage is an inspection instruction, not an observed diagnostic indicator. Quoting a noun fragment cannot establish a causal chain; retain the inspection for adjudication.",
            ))
        for position, indicator in enumerate(indicators):
            support = explicit_cause_list_support(indicator.failure_link_evidence, indicator.claim_evidence, failure.claim_evidence)
            if support:
                indicator = indicator.model_copy(update={"failure_link_evidence": [*indicator.failure_link_evidence, *support]})
                indicators[position] = indicator
            check_link(indicator.failure_link_evidence, indicator.claim_evidence, failure.claim_evidence, f"indicators[{position}].failure_link_evidence")
        for position, action in enumerate(actions):
            check_link(action.resolution_link_evidence, failure.claim_evidence, action.claim_evidence, f"actions[{position}].resolution_link_evidence")

    if problems:
        raise DiagnosticBundleEvidenceError(problems)

    procedure_context = []
    # A named numbered test has an explicit scope, including lettered subtests.
    # Preserve its source blocks in order; do not infer which branches to run.
    heading = re.compile(r"(?i)^\s*test\s+(\d+)([a-z]?)\s*[-–—:]\s+")
    root_position = next((i for i, r in enumerate(index.ordered) if r.evidence_id == record_anchor), None)
    if root_position is not None:
        starts = [(i, heading.match(r.text)) for i, r in enumerate(index.ordered[:root_position + 1])]
        starts = [(i, m) for i, m in starts if m and not m.group(2)]
        if starts:
            start, match = starts[-1]
            first = index.ordered[start]
            selected = []
            for r in index.ordered[start:]:
                next_heading = heading.match(r.text)
                if r.page - first.page > 9 or (next_heading and next_heading.group(1) != match.group(1)):
                    break
                if r.locator.get("block_index") is not None:
                    selected.append(r)
            if record_anchor in {r.evidence_id for r in selected} and branch_anchor in {r.evidence_id for r in selected}:
                procedure_context = [ValidatedDiagnosticEvidenceSpan(source_anchor=r.evidence_id, source_page=r.page,
                    quote=_display_text(r.text), evidence_id=r.evidence_id, locator=r.locator) for r in selected]
    indicators.sort(key=_canonical_json)
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
        record_window_id=candidate.record_window_id,
        record_anchor=record_anchor,
        branch_anchor=branch_anchor,
        indicators=indicators,
        failure=failure,
        actions=actions,
        inspection_steps=inspection_steps,
        conditions=conditions,
        procedure_context=procedure_context,
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
    # A source's negative answer to a conjunction does not entail two
    # negative observations. Keep the original candidate in review rather
    # than publishing a fluent but logically stronger paraphrase.
    def negative_conjunction(value):
        return bool(re.search(r"(?i)\b(?:not|no)\b[^.;?]*\band\b[^.;?]*\b(?:not|no)\b", value))
    conditional_evidence = [s.quote for c in candidate.conditions for s in c.claim_evidence]
    if any(re.search(r"(?i)\band\b.*\?", q) for q in conditional_evidence) and any(re.search(r"(?i)\bif no\b", q) for q in conditional_evidence):
        texts = [c.text for c in candidate.conditions] + [a.instruction_text for a in candidate.actions]
        texts += [candidate.failure.description] if candidate.failure else []
        if any(negative_conjunction(text) for text in texts):
            contradictions = True
            reasons.append(_reason("compound_negative_condition_strengthened", "A negative answer to a compound AND question was paraphrased as two negative facts; preserve the whole question and its outcome.", "conditions"))
    missing = False
    non_restorative_actions = [
        position
        for position, action in enumerate(candidate.actions)
        if _inspection_only_instruction(action.instruction_text, action.action_kind)
    ]
    for position in non_restorative_actions:
        reasons.append(
            _reason(
                "inspection_only_action",
                "A check/test/inspection without an explicit restorative step cannot be a CorrectiveAction.",
                f"actions[{position}]",
            )
        )

    if candidate.failure is not None and all(
        re.match(r"(?is)^\s*(?:(?:troubleshooting|remedy)\s*:\s*)?(?:\d+[.)]\s*)?(?:if\s+(?:yes|no)\s*,\s*)?(?:check|inspect|verify|replace|clean|adjust|tighten|loosen|contact|test)\b", span.quote)
        for span in candidate.failure.claim_evidence
    ):
        contradictions = True
        reasons.append(_reason(
            "failure_inferred_from_instruction", "An inspection or remedy alone does not state a technical failure; retain the candidate for adjudication.", "failure.claim_evidence",
        ))

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
        if candidate.inspection_steps:
            missing = True
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
    if candidate.resolution_status is ResolutionStatus.AMBIGUOUS:
        reasons.append(_reason("declared_ambiguous", "The extractor marked this branch as ambiguous."))
        return BundleDisposition.REVIEW, _sorted_reasons(reasons)
    if evidence_problems or contradictions:
        return BundleDisposition.REVIEW, _sorted_reasons(reasons)
    if non_restorative_actions:
        # Preserve the raw misclassified action for audit, but publish no
        # partial diagnostic nodes.  A pure inspection row is an explicit gap;
        # a mixed remedy/check list is contradictory and needs review.
        disposition = (
            BundleDisposition.GAP
            if len(non_restorative_actions) == len(candidate.actions)
            else BundleDisposition.REVIEW
        )
        return disposition, _sorted_reasons(reasons)
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
        if not candidate.inspection_steps:
            reasons.append(
                _reason(
                    "missing_inspection_steps",
                    "The record is check-only but no traceable inspection step was supplied.",
                    "inspection_steps",
                )
            )
        reasons.append(
            _reason(
                "check_only",
                "The source provides a diagnostic check but no restorative action.",
                "resolution_status",
            )
        )
        return BundleDisposition.GAP, _sorted_reasons(reasons)
    # A diagnostic branch may state both a check and an explicit restorative
    # action.  Inspection steps remain audit-only (the graph compiler never
    # turns them into CorrectiveAction nodes); their presence does not make the
    # separately typed restorative action ambiguous.
    if missing:
        return BundleDisposition.GAP, _sorted_reasons(reasons)
    return BundleDisposition.PUBLISH, []


def _sorted_reasons(reasons: Iterable[BundleDropReason]) -> list[BundleDropReason]:
    unique = {
        (reason.code, reason.path, reason.message): reason
        for reason in reasons
    }
    return [unique[key] for key in sorted(unique)]


def _accounting_state(
    candidate: DiagnosticBundleCandidate,
    disposition: BundleDisposition,
    reasons: Sequence[BundleDropReason],
) -> str:
    codes = {reason.code for reason in reasons}
    if disposition is BundleDisposition.PUBLISH:
        return "autonomously_publishable"
    if disposition is BundleDisposition.EXCLUDE:
        return "observed_excluded"
    if candidate.resolution_status is ResolutionStatus.AMBIGUOUS:
        return "compiled_semantically_ambiguous"
    if codes & {"check_only", "inspection_only_action"}:
        return "inspection_only_gap"
    if codes & {
        "missing_failure",
        "missing_actions",
        "missing_indicator_failure_evidence",
        "missing_resolution_evidence",
        "missing_affects_evidence",
        "unresolved_material_context",
    }:
        return "observed_structurally_incomplete"
    if codes:
        return "extracted_not_compilable"
    return "observed_unresolved"


def _is_asset_level(value: str | None) -> bool:
    return _identity_text(value).replace("-", "_") in {
        item.replace(" ", "_") for item in _GENERAL_MATERIAL_CONTEXTS
    }


def _recover_unlinked_optional_metadata(
    candidate: DiagnosticBundleCandidate,
) -> tuple[DiagnosticBundleCandidate, list[BundleDropReason]]:
    """Discard optional metadata that cannot have a grounded graph effect.

    ``material_context`` has no evidence field and the extractor is instructed
    to return null unless an affected component is established.  When that
    component is absent, publication already uses the asset level.  Removing
    this unsupported field therefore cannot create a Component or AFFECTS
    relation, while preserving the fully grounded diagnostic branch.
    """

    failure = candidate.failure
    if (
        failure is None
        or candidate.affected_component is not None
        or failure.material_context is None
        or _is_asset_level(failure.material_context)
    ):
        return candidate, []
    recovered = candidate.model_copy(
        update={"failure": failure.model_copy(update={"material_context": None})}
    )
    return recovered, [
        _reason(
            "discarded_unlinked_material_context",
            (
                "Optional material_context had no affected Component or evidence-bearing "
                "graph effect and was deterministically reset to null."
            ),
            "failure.material_context",
        )
    ]


_RESTORATIVE_VERBS = re.compile(
    r"\b(?:adjust|align|bleed|clean|clear|close|correct|drain|fill|flush|install|"
    r"lubricate|open|reconnect|reduce|increase|refill|remove|repair|replace|reset|"
    r"restart|restore|secure|set|tighten|unblock|update)\b",
    flags=re.IGNORECASE,
)
_INSPECTION_VERBS = re.compile(
    r"\b(?:check|confirm|determine|diagnose|examine|inspect|measure|monitor|observe|"
    r"test|verify)\b|\bto see (?:if|whether)\b",
    flags=re.IGNORECASE,
)


def _inspection_only_instruction(instruction: str, action_kind: str | None) -> bool:
    """Recognize only the conservative check-without-remedy case."""

    if str(action_kind or "").strip().casefold() == "escalation":
        return False
    text = _display_text(instruction)
    return bool(_INSPECTION_VERBS.search(text) and not _RESTORATIVE_VERBS.search(text))


def _required_source_value(value: str, field: str) -> str:
    normalized = _display_text(value)
    if not normalized:
        raise ValueError(f"{field} must not be empty")
    return normalized


def _candidate_referenced_anchors(candidate: DiagnosticBundleCandidate) -> set[str]:
    anchors = {candidate.record_anchor, candidate.branch_anchor}

    def add(spans: Sequence[DiagnosticEvidenceSpan]) -> None:
        anchors.update(span.source_anchor for span in spans)

    for indicator in candidate.indicators:
        add(indicator.claim_evidence)
        add(indicator.failure_link_evidence)
    if candidate.failure is not None:
        add(candidate.failure.claim_evidence)
    for action in candidate.actions:
        add(action.claim_evidence)
        add(action.resolution_link_evidence)
    for step in candidate.inspection_steps:
        add(step.claim_evidence)
    for condition in candidate.conditions:
        add(condition.claim_evidence)
    if candidate.affected_component is not None:
        add(candidate.affected_component.claim_evidence)
        add(candidate.affected_component.affects_link_evidence)
    return {str(anchor).strip() for anchor in anchors if str(anchor).strip()}


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
        tuple[str, str, str, str, str, str],
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
        key = (name, from_type, from_id, to_type, to_id, branch_id)
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
        material_context = component_id or ("asset_level" if _is_asset_level(bundle.failure.material_context) else "not_stated")
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
                # Provenance belongs on edge evidence.  Keeping a row-specific
                # anchor on a reusable semantic node caused deterministic ID
                # collisions for repeated remedies in troubleshooting tables.
                "source_reference": "typed_diagnostic_edge_evidence",
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
            branch_lineage_id=key[5],
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
    for step in bundle.inspection_steps:
        add(step.claim_evidence)
    for condition in bundle.conditions:
        add(condition.claim_evidence)
    if bundle.affected_component is not None:
        add(bundle.affected_component.claim_evidence)
        add(bundle.affected_component.affects_link_evidence)
    return sorted(ids)


def _candidate_evidence_ids(
    candidate: DiagnosticBundleCandidate,
    index: _EvidenceIndex,
) -> list[str]:
    """Return every source-owned anchor referenced by the original candidate."""

    anchors = _candidate_referenced_anchors(candidate)
    return sorted(anchor for anchor in anchors if anchor in index)


def _verified_inspection_source_gap(candidate, resolved, disposition, reasons, windows, units):
    """Recognize a complete, source-owned check-only remedy cell, never a miss.

Only simple atomic table rows qualify. Prose, partial quotations, conditional
alternatives and mixed check/remedy cells continue to require adjudication.
    """
    if (disposition is not BundleDisposition.GAP or resolved is None
            or candidate.resolution_status is not ResolutionStatus.CHECK_ONLY
            or candidate.failure is None or candidate.actions or not candidate.inspection_steps
            or {r.code for r in reasons} - {"check_only", "missing_actions"}):
        return False
    window = next((w for w in windows if w.get("window_id") == candidate.record_window_id), {})
    if (window.get("edge_policy") != "table_atomic_endpoint_union"
            or window.get("structure_status") != "atomic" or int(window.get("branch_count", 1)) != 1):
        return False
    unit = next((u for u in units if str(u.evidence_id) == candidate.branch_anchor), None)
    layout = unit.attributes.get("table_layout", {}) if unit is not None else {}
    cells, headers = layout.get("cells", []), layout.get("column_headers", [])
    if not cells or not headers or not re.fullmatch(r"(?i)(?:solution|remedy|troubleshooting|corrective action)s?", _display_text(headers[-1])):
        return False
    cell = _display_text(cells[-1])
    if not cell or not _inspection_only_instruction(cell, None):
        return False
    sentences = [s.strip() for s in re.split(r"[.;]+\s*", cell) if s.strip()]
    if not all(re.match(r"(?i)^(?:check|inspect|verify|measure|test)\b", sentence) for sentence in sentences):
        return False
    allowed = window.get("allowed_evidence_spans", {}).get(candidate.branch_anchor, [])
    if cell not in {_display_text(value) for value in allowed}:
        return False
    quoted = " ".join(_display_text(span.quote) for step in resolved.inspection_steps for span in step.claim_evidence if span.source_anchor == candidate.branch_anchor)
    return cell in quoted


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
    record_windows: Sequence[Mapping[str, Any]] = (),
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
    recovered_candidates = [
        _recover_unlinked_optional_metadata(candidate)
        for candidate in typed_candidates
    ]
    by_branch: dict[
        str, tuple[DiagnosticBundleCandidate, list[BundleDropReason]]
    ] = {}
    for candidate, recoveries in recovered_candidates:
        branch_id = diagnostic_branch_lineage_id(
            candidate,
            source_type=source_type,
            source_title=source_title,
        )
        current = by_branch.get(branch_id)
        if current is not None and _canonical_json(current[0]) != _canonical_json(candidate):
            raise ValueError(f"Conflicting candidates share branch lineage {branch_id}")
        if current is None:
            by_branch[branch_id] = (candidate, recoveries)

    index = _evidence_index(evidence_units, legacy_chunks, text_with_pages)
    window_scopes: dict[str, dict[str, list[str]]] = {}
    structural_windows = {
        str(window.get("window_id") or "") for window in record_windows
        if window.get("edge_policy") in {"table_atomic_endpoint_union", "prose_structural_endpoint_union"}
        and window.get("structure_status") == "atomic"
    }
    ambiguous_windows = {
        str(window.get("window_id") or "") for window in record_windows
        if window.get("structure_status") == "ambiguous_pairing"
    }
    for window in record_windows:
        window_id = str(window.get("window_id") or window.get("record_window_id") or "").strip()
        raw_scope = window.get("allowed_evidence_spans") or {}
        if not window_id or not isinstance(raw_scope, Mapping):
            continue
        window_scopes[window_id] = {
            str(anchor).strip(): [str(span) for span in spans or []]
            for anchor, spans in raw_scope.items()
            if str(anchor).strip() and isinstance(spans, Sequence) and not isinstance(spans, str)
        }
    validated: list[ValidatedDiagnosticBundle] = []
    staged: list[
        tuple[
            DiagnosticBundleCandidate,
            str,
            str,
            BundleDisposition,
            list[BundleDropReason],
            list[BundleDropReason],
            ValidatedDiagnosticBundle | None,
        ]
    ] = []
    for branch_id, (candidate, recoveries) in sorted(by_branch.items()):
        candidate_index = index
        if candidate.record_window_id in window_scopes:
            candidate_index = _scoped_evidence_index(
                index, window_scopes[candidate.record_window_id]
            )
        record_id = diagnostic_record_lineage_id(
            candidate,
            source_type=source_type,
            source_title=source_title,
        )
        evidence_problems: Sequence[EvidenceValidationProblem] = ()
        resolved: ValidatedDiagnosticBundle | None = None
        if candidate.resolution_status is ResolutionStatus.NOT_DIAGNOSTIC:
            exclusion_problems: list[EvidenceValidationProblem] = []
            record_anchor = _validate_lineage_anchor(
                candidate.record_anchor,
                path="record_anchor",
                index=candidate_index,
                problems=exclusion_problems,
            )
            branch_anchor = _validate_lineage_anchor(
                candidate.branch_anchor,
                path="branch_anchor",
                index=candidate_index,
                problems=exclusion_problems,
            )
            if candidate.record_window_id:
                _validate_window_lineage_membership(
                    record_anchor=record_anchor,
                    branch_anchor=branch_anchor,
                    record_window_id=candidate.record_window_id,
                    allowed_source_anchors=frozenset(
                        str(anchor).strip()
                        for anchor in candidate.allowed_source_anchors
                        if str(anchor).strip()
                    ),
                    problems=exclusion_problems,
                )
            evidence_problems = exclusion_problems
        else:
            try:
                resolved = _validated_bundle(
                    candidate,
                    index=candidate_index,
                    source_type=source_type,
                    source_title=source_title,
                    structural_edge_support=candidate.record_window_id in structural_windows and candidate.record_window_id in window_scopes,
                )
                validated.append(resolved)
            except DiagnosticBundleEvidenceError as exc:
                evidence_problems = exc.problems
        if candidate.record_window_id in ambiguous_windows and candidate.resolution_status is not ResolutionStatus.NOT_DIAGNOSTIC:
            evidence_problems = [*evidence_problems, EvidenceValidationProblem(
                code="structurally_ambiguous_pairing", path="record_window_id",
                message="The source window contains alternatives without a verified pairing. Literal endpoint spans alone do not resolve their relationship.",
            )]
        disposition, reasons = _classify_candidate(candidate, evidence_problems)
        staged.append(
            (candidate, record_id, branch_id, disposition, reasons, recoveries, resolved)
        )

    published = [
        resolved
        for _, _, _, disposition, _, _, resolved in staged
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
    recovery_counts: Counter[str] = Counter()
    disposition_counts: Counter[str] = Counter()
    for candidate, record_id, branch_id, disposition, reasons, recoveries, resolved in staged:
        disposition_counts[disposition.value] += 1
        recovery_counts.update(recovery.code for recovery in recoveries)
        if disposition is not BundleDisposition.PUBLISH:
            drop_counts.update(reason.code for reason in reasons)
        node_ids, relation_ids = emissions.get(branch_id, ([], []))
        entries.append(
            BundleCompilationEntry(
                record_lineage_id=record_id,
                branch_lineage_id=branch_id,
                record_window_id=candidate.record_window_id,
                record_anchor=candidate.record_anchor,
                branch_anchor=candidate.branch_anchor,
                evidence_ids=_candidate_evidence_ids(candidate, index),
                resolved_evidence_ids=_bundle_evidence_ids(resolved),
                candidate=candidate.model_dump(mode="json"),
                validated_record=resolved,
                source_gap_verified=_verified_inspection_source_gap(candidate, resolved, disposition, reasons, record_windows, evidence_units),
                disposition=disposition,
                accounting_state=_accounting_state(candidate, disposition, reasons),
                compiler_recoveries=recoveries,
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
        recovered_items_by_reason=dict(sorted(recovery_counts.items())),
        dropped_items_by_reason=dict(sorted(drop_counts.items())),
        entries=entries,
    )
    return DiagnosticBundleCompilationResult(
        ontology=ontology,
        validated_bundles=sorted(validated, key=lambda item: item.branch_lineage_id),
        report=report,
    )
