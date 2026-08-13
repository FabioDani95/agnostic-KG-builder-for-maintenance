"""Deterministic, provenance-preserving diagnostic record windows.

The diagnostic model must never infer table row membership from a page-sized
text blob.  This module turns the canonical PDF EvidenceUnit inventory into
small, system-owned windows before any model call.  Numbered cause/remedy lists
inside one physical table row are split into atomic branches when their pairing
is deterministic.  When a visual table suppresses repeated root cells, only
those cells are carried forward; cause and action cells from the preceding row
are never part of the current branch's evidence scope.

The implementation is intentionally vendor- and document-agnostic.  It uses
only canonical locators, physical adjacency and generic diagnostic labels.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from typing import Iterable, Literal, Sequence

from pydantic import BaseModel, ConfigDict, Field

from backend.adapters.pdf import pdf_evidence_sort_key
from backend.domain.evidence import EvidenceUnit
from backend.domain.locators import PdfLocator


class DiagnosticRecordWindow(BaseModel):
    """One bounded diagnostic record presented to the typed extractor.

    ``record_anchor``/``root_anchor`` identify the observable symptom or fault
    root.  ``branch_anchor`` identifies the current table row (or the first
    block for an unstructured record).  ``allowed_source_anchors`` is a hard
    compiler allow-list owned by this deterministic stage, not by the model.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    window_id: str = Field(pattern=r"^diagwin_[a-f0-9]{24}$")
    window_kind: Literal["table_row", "contiguous_blocks"]
    source_id: str
    record_anchor: str
    root_anchor: str
    branch_anchor: str
    allowed_source_anchors: list[str] = Field(min_length=1)
    # Exact source fragments visible to and admissible for this branch.  An
    # anchor allow-list alone is insufficient when one canonical table-row
    # EvidenceUnit contains several diagnostic branches.
    allowed_evidence_spans: dict[str, list[str]] = Field(default_factory=dict)
    evidence_ids: list[str] = Field(min_length=1)
    page_numbers: list[int] = Field(min_length=1)
    text_with_pages: str = Field(min_length=1)
    table_key: str | None = None
    inherited_root: bool = False
    branch_ordinal: int = Field(default=1, ge=1)
    branch_count: int = Field(default=1, ge=1)
    structure_status: Literal["atomic", "ambiguous_pairing"] = "atomic"
    edge_policy: Literal[
        "prose_direct",
        "table_atomic_endpoint_union",
        "prose_layout_endpoint_union",
    ] = "prose_direct"


_HEADER_TERMS = {
    "action",
    "alarm",
    "cause",
    "check",
    "code",
    "condition",
    "correction",
    "corrective action",
    "error",
    "failure",
    "fault",
    "indication",
    "possible cause",
    "problem",
    "remedy",
    "resolution",
    "solution",
    "symptom",
    "trouble",
}
_ROOT_LABEL_RE = re.compile(
    r"(?im)^\s*(?:problem|symptom|fault|failure|alarm|error(?:\s+(?:code|message))?"
    r"|trouble|condition)\s*(?::|#|[-\u2013\u2014]\s+)"
)
_CAUSE_LABEL_RE = re.compile(r"(?im)^\s*(?:possible\s+)?(?:cause|reason)\s*:")
_ACTION_LABEL_RE = re.compile(
    r"(?im)^\s*(?:corrective\s+action|remedy|solution|correction|resolution|action)\s*:"
)
_CAUSE_HEADER_TERMS = ("possible cause", "possible fault", "cause", "reason")
_ACTION_HEADER_TERMS = (
    "corrective action",
    "troubleshooting",
    "remedy",
    "solution",
    "correction",
    "resolution",
    "action",
    "check",
)
_NUMBERED_ITEM_RE = re.compile(r"(?<!\w)(\d{1,2})\s+(?=[A-Z])")
_NUMBERED_BLOCK_RE = re.compile(
    r"(?i)^\s*(?:troubleshooting\s*:\s*)?(\d{1,2})\s*[.)]\s*"
)
_ALPHA_BLOCK_RE = re.compile(r"(?i)^\s*([a-z])\s*[.)]\s*")
_SECTION_ONLY_RE = re.compile(
    r"(?i)^\s*(?:trouble\s*shooting(?:\s+guide)?|fault\s+finding(?:\s+guide)?|"
    r"diagnostics?|maintenance|installation|"
    r"operation|specifications?)\s*$"
)


def _normalized(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def _unit_text(unit: EvidenceUnit) -> str:
    return str(unit.content.observation or unit.locator.quote or "").strip()


def _table_cells(unit: EvidenceUnit) -> list[str]:
    return [cell.strip() for cell in _unit_text(unit).split("|")]


def _looks_like_header(cells: Sequence[str]) -> bool:
    nonempty = [_normalized(cell) for cell in cells if _normalized(cell)]
    if len(nonempty) < 2:
        return False
    matches = sum(
        value in _HEADER_TERMS
        or any(value.startswith(f"{term} ") for term in _HEADER_TERMS)
        for value in nonempty
    )
    return matches >= 2 and matches * 2 >= len(nonempty)


def _header_signature(cells: Sequence[str]) -> str:
    return "|".join(_normalized(cell) for cell in cells)


def _stable_window_id(
    *,
    kind: str,
    source_id: str,
    record_anchor: str,
    branch_anchor: str,
    allowed_anchors: Sequence[str],
    branch_discriminator: str = "",
) -> str:
    payload = json.dumps(
        {
            "kind": kind,
            "source_id": source_id,
            "record_anchor": record_anchor,
            "branch_anchor": branch_anchor,
            "allowed_anchors": list(allowed_anchors),
            "branch_discriminator": branch_discriminator,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"diagwin_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:24]}"


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _page_marker(page: int) -> str:
    return f"--- PAGE {page} ---"


def _render_table_window(
    *,
    row: EvidenceUnit,
    header_cells: Sequence[str],
    root: EvidenceUnit,
    root_text: str,
    branch_cells: Sequence[str],
    branch_ordinal: int,
    branch_count: int,
    structure_status: str,
) -> str:
    locator = row.locator
    root_locator = root.locator
    assert isinstance(locator, PdfLocator)
    assert isinstance(root_locator, PdfLocator)

    parts: list[str] = []
    if header_cells:
        # Header text is structural context, not an evidence anchor available
        # for claims.  This avoids turning a column label into a symptom.
        parts.append(f"TABLE COLUMNS (CONTEXT ONLY): {' | '.join(header_cells)}")
    parts.append(
        "STRUCTURAL INVENTORY (SYSTEM OWNED): "
        f"branch {branch_ordinal}/{branch_count}; status={structure_status}"
    )
    if root.evidence_id != row.evidence_id:
        parts.extend(
            [
                _page_marker(root_locator.page),
                f"[[EVIDENCE_ID: {root.evidence_id}]]",
                f"ROOT CELL (CONTEXT ONLY): {root_text}",
            ]
        )
    parts.extend(
        [
            _page_marker(locator.page),
            f"[[EVIDENCE_ID: {row.evidence_id}]]",
            "CURRENT ATOMIC RECORD (each field is an exact source span):",
            *[f"FIELD {index + 1}: {cell}" for index, cell in enumerate(branch_cells) if cell],
        ]
    )
    return "\n\n".join(parts)


def _header_column_index(
    header_cells: Sequence[str],
    terms: Sequence[str],
) -> int | None:
    for index, cell in enumerate(header_cells):
        value = _normalized(cell)
        if any(value == term or value.startswith(f"{term} ") for term in terms):
            return index
    return None


def _split_numbered_items(value: str) -> list[str]:
    """Split an explicit numbered list while preserving literal source text."""

    text = str(value or "").strip()
    matches = list(_NUMBERED_ITEM_RE.finditer(text))
    if len(matches) < 2:
        return [text] if text else []
    prefix = text[: matches[0].start()].strip()
    if prefix:
        return [text]
    return [
        text[match.start() : (matches[position + 1].start() if position + 1 < len(matches) else len(text))].strip()
        for position, match in enumerate(matches)
    ]


def _atomic_table_branches(
    cells: Sequence[str],
    header_cells: Sequence[str],
) -> list[tuple[list[str], str]]:
    """Return deterministic atomic row views plus their structural status.

    Equal numbered cause/action lists pair positionally.  One shared action may
    be broadcast to several explicit causes because the physical row itself
    establishes that scope.  Any other cardinality mismatch is retained as one
    ambiguous window rather than guessed.
    """

    cause_index = _header_column_index(header_cells, _CAUSE_HEADER_TERMS)
    action_index = _header_column_index(header_cells, _ACTION_HEADER_TERMS)
    if (
        cause_index is None
        or action_index is None
        or cause_index >= len(cells)
        or action_index >= len(cells)
    ):
        return [(list(cells), "atomic")]

    causes = _split_numbered_items(cells[cause_index])
    actions = _split_numbered_items(cells[action_index])
    if len(causes) <= 1:
        return [(list(cells), "atomic")]
    if len(actions) not in {1, len(causes)}:
        return [(list(cells), "ambiguous_pairing")]

    branches: list[tuple[list[str], str]] = []
    for position, cause in enumerate(causes):
        atomic = list(cells)
        atomic[cause_index] = cause
        atomic[action_index] = actions[position] if len(actions) == len(causes) else actions[0]
        branches.append((atomic, "atomic"))
    return branches


def _merge_evidence_scope(
    *items: tuple[str, Sequence[str]],
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for anchor, spans in items:
        values = _dedupe(str(span).strip() for span in spans if str(span).strip())
        if values:
            result[anchor] = _dedupe([*result.get(anchor, []), *values])
    return result


def _physical_table_groups(
    units: Sequence[EvidenceUnit],
) -> list[tuple[tuple[str, int], list[EvidenceUnit]]]:
    grouped: dict[tuple[str, int], list[EvidenceUnit]] = defaultdict(list)
    for unit in units:
        locator = unit.locator
        if not isinstance(locator, PdfLocator):
            continue
        if locator.table_index is None or locator.row_index is None:
            continue
        grouped[(unit.source_id, locator.table_index)].append(unit)
    result = []
    for key, rows in grouped.items():
        rows.sort(key=pdf_evidence_sort_key)
        result.append((key, rows))
    result.sort(key=lambda item: pdf_evidence_sort_key(item[1][0]))
    return result


def _table_windows(units: Sequence[EvidenceUnit]) -> list[DiagnosticRecordWindow]:
    windows: list[DiagnosticRecordWindow] = []
    previous_source: str | None = None
    previous_page: int | None = None
    previous_header_signature = ""
    previous_root: tuple[EvidenceUnit, list[str]] | None = None

    for (source_id, table_index), rows in _physical_table_groups(units):
        first_locator = rows[0].locator
        assert isinstance(first_locator, PdfLocator)
        first_cells = _table_cells(rows[0])
        has_header = _looks_like_header(first_cells)
        # A table locator is structural evidence, not proof that the table is
        # troubleshooting.  Without a diagnostic header, turning every row in
        # parts/specification/maintenance tables into an LLM call recreates the
        # permissive baseline and can exhaust the bounded campaign budget.
        if not has_header:
            previous_source = source_id
            previous_page = first_locator.page
            previous_header_signature = ""
            previous_root = None
            continue
        header_cells = first_cells if has_header else []
        cause_index = _header_column_index(header_cells, _CAUSE_HEADER_TERMS)
        data_rows = rows[1:] if has_header else rows
        if not data_rows:
            previous_source = source_id
            previous_page = first_locator.page
            previous_header_signature = _header_signature(header_cells)
            previous_root = None
            continue

        signature = _header_signature(header_cells)
        first_data_cells = _table_cells(data_rows[0])
        first_data_has_blank_root = not (first_data_cells and first_data_cells[0].strip())
        # The adapter assigns a fresh physical table index on each page.  A
        # repeated header on the immediately following page plus a suppressed
        # first root cell is the only condition under which we regard it as the
        # same logical table.  A new table on the same page always resets.
        is_cross_page_continuation = bool(
            previous_root
            and previous_source == source_id
            and previous_page is not None
            and first_locator.page == previous_page + 1
            and signature
            and signature == previous_header_signature
            and first_data_has_blank_root
        )
        active_root = previous_root if is_cross_page_continuation else None

        for row in data_rows:
            locator = row.locator
            assert isinstance(locator, PdfLocator)
            cells = _table_cells(row)
            root_cells = [
                cell.strip()
                for cell in cells[:cause_index]
                if cell.strip()
            ] if cause_index is not None else ([cells[0].strip()] if cells and cells[0].strip() else [])
            if root_cells:
                active_root = (row, root_cells)
            inherited = bool(active_root and active_root[0].evidence_id != row.evidence_id)
            # An orphan continuation row remains isolated.  It must never
            # inherit a symptom from a different table merely because the
            # first cell is visually empty.
            root, root_spans = active_root or (row, [])
            allowed = _dedupe([root.evidence_id, row.evidence_id])
            pages = sorted(
                {
                    locator.page,
                    root.locator.page if isinstance(root.locator, PdfLocator) else locator.page,
                }
            )
            atomic_branches = _atomic_table_branches(cells, header_cells)
            branch_count = len(atomic_branches)
            for branch_ordinal, (branch_cells, structure_status) in enumerate(
                atomic_branches, start=1
            ):
                current_spans = (
                    [cell for cell in branch_cells[cause_index:] if cell]
                    if inherited and cause_index is not None
                    else [cell for cell in branch_cells if cell]
                )
                scope = _merge_evidence_scope(
                    (root.evidence_id, root_spans if inherited else []),
                    (row.evidence_id, current_spans),
                )
                window_id = _stable_window_id(
                    kind="table_row",
                    source_id=source_id,
                    record_anchor=root.evidence_id,
                    branch_anchor=row.evidence_id,
                    allowed_anchors=allowed,
                    branch_discriminator=json.dumps(
                        {
                            "branch_ordinal": branch_ordinal,
                            "branch_count": branch_count,
                            "branch_cells": branch_cells,
                            "structure_status": structure_status,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                )
                windows.append(
                    DiagnosticRecordWindow(
                        window_id=window_id,
                        window_kind="table_row",
                        source_id=source_id,
                        record_anchor=root.evidence_id,
                        root_anchor=root.evidence_id,
                        branch_anchor=row.evidence_id,
                        allowed_source_anchors=allowed,
                        allowed_evidence_spans=scope,
                        evidence_ids=allowed,
                        page_numbers=pages,
                        text_with_pages=_render_table_window(
                            row=row,
                            header_cells=header_cells,
                            root=root,
                            root_text=" | ".join(root_spans),
                            branch_cells=branch_cells,
                            branch_ordinal=branch_ordinal,
                            branch_count=branch_count,
                            structure_status=structure_status,
                        ),
                        table_key=f"{source_id}:table:{table_index}",
                        inherited_root=inherited,
                        branch_ordinal=branch_ordinal,
                        branch_count=branch_count,
                        structure_status=structure_status,
                        edge_policy="table_atomic_endpoint_union",
                    )
                )

        last_locator = rows[-1].locator
        assert isinstance(last_locator, PdfLocator)
        previous_source = source_id
        previous_page = last_locator.page
        previous_header_signature = signature
        previous_root = active_root

    return windows


def _looks_like_record_root(text: str) -> bool:
    if _SECTION_ONLY_RE.fullmatch(text.strip()):
        return False
    return bool(_ROOT_LABEL_RE.search(text))


def _looks_like_section_boundary(text: str) -> bool:
    stripped = text.strip()
    if not stripped or _looks_like_record_root(stripped):
        return False
    if _CAUSE_LABEL_RE.search(stripped) or _ACTION_LABEL_RE.search(stripped):
        return False
    first_line = stripped.splitlines()[0].strip()
    embedded_heading = bool(
        len(first_line) <= 90
        and first_line
        and not first_line.endswith((".", ":", ";", ","))
        and len(stripped.splitlines()) > 1
        and any(character.isalpha() for character in first_line)
        and _explicit_step_number(first_line) is None
        and not _looks_like_alpha_substep(first_line)
        and not first_line.casefold().startswith("troubleshooting")
    )
    return bool(
        _ROOT_LABEL_RE.search(stripped)
        or embedded_heading
        or (
            len(stripped) <= 90
            and "\n" not in stripped
            and not stripped.endswith((".", ":", ";", ","))
            and (stripped.isupper() or stripped.istitle())
        )
    )


def _explicit_step_number(text: str) -> int | None:
    match = _NUMBERED_BLOCK_RE.match(str(text or ""))
    return int(match.group(1)) if match else None


def _looks_like_alpha_substep(text: str) -> bool:
    return bool(_ALPHA_BLOCK_RE.match(str(text or "")))


def _root_declares_explicit_causes(text: str) -> bool:
    return bool(re.search(
        r"(?i)\b(?:caused\s+by|due\s+to|typically\s+caused|cause\s*:)",
        str(text or ""),
    ))


def _step_groups(supports: Sequence[EvidenceUnit]) -> list[list[EvidenceUnit]]:
    """Group each numbered prose item with its physical alpha substeps."""

    groups: list[list[EvidenceUnit]] = []
    prefix: list[EvidenceUnit] = []
    for unit in supports:
        text = _unit_text(unit)
        if _explicit_step_number(text) is not None:
            groups.append([unit])
        elif groups and _looks_like_alpha_substep(text):
            groups[-1].append(unit)
        elif not groups:
            prefix.append(unit)
        else:
            # Page artifacts and unnumbered continuations belong to the
            # preceding physical step; a new record/section is stopped by the
            # caller before grouping.
            groups[-1].append(unit)
    if prefix:
        if groups:
            groups[0] = [*prefix, *groups[0]]
        else:
            groups.append(prefix)
    return groups


def _split_prose_record(
    root: EvidenceUnit,
    supports: Sequence[EvidenceUnit],
) -> tuple[list[list[EvidenceUnit]], str]:
    groups = _step_groups(supports)
    if len(groups) <= 1:
        return [[root, *supports]], "prose_direct"

    root_text = _unit_text(root)
    record_text = "\n".join(_unit_text(unit) for unit in (root, *supports))
    numbered = [
        unit
        for group in groups
        for unit in group
        if _explicit_step_number(_unit_text(unit)) is not None
    ]
    # A named procedure (calibration, setup, replacement...) whose steps form
    # one sequence remains a single record.  Otherwise, multiple numbered
    # maintenance-bearing items are independent troubleshooting branches and
    # are presented one at a time with immutable root context.
    procedure = bool(re.search(
        r"(?i)\b(?:procedure|proceed\s+as\s+follows)\b",
        record_text,
    ))
    if procedure or len(numbered) <= 1:
        return [[root, *supports]], "prose_direct"
    edge_policy = (
        "prose_direct"
        if _root_declares_explicit_causes(root_text)
        else "prose_layout_endpoint_union"
    )
    return [[root, *group] for group in groups], edge_policy


def _block_is_contiguous(previous: EvidenceUnit, current: EvidenceUnit) -> bool:
    previous_locator = previous.locator
    current_locator = current.locator
    if not isinstance(previous_locator, PdfLocator) or not isinstance(current_locator, PdfLocator):
        return False
    if current_locator.page == previous_locator.page:
        if previous_locator.block_index is None or current_locator.block_index is None:
            return False
        return current_locator.block_index <= previous_locator.block_index + 2
    return (
        current_locator.page == previous_locator.page + 1
        and current_locator.block_index is not None
        and current_locator.block_index <= 2
    )


def _table_overlap_block_ids(units: Sequence[EvidenceUnit]) -> set[str]:
    rows_by_page: dict[tuple[str, int], list[str]] = defaultdict(list)
    blocks: list[EvidenceUnit] = []
    for unit in units:
        locator = unit.locator
        if not isinstance(locator, PdfLocator):
            continue
        if locator.table_index is not None and locator.row_index is not None:
            rows_by_page[(unit.source_id, locator.page)].append(_normalized(_unit_text(unit)))
        elif locator.block_index is not None:
            blocks.append(unit)

    overlaps: set[str] = set()
    for block in blocks:
        locator = block.locator
        assert isinstance(locator, PdfLocator)
        block_text = _normalized(_unit_text(block))
        matching_rows = [
            row_text
            for row_text in rows_by_page.get((block.source_id, locator.page), [])
            if row_text and row_text in block_text
        ]
        if len(matching_rows) >= 2 or (
            len(matching_rows) == 1 and matching_rows[0] == block_text
        ):
            overlaps.add(block.evidence_id)
    return overlaps


def _render_block_window(records: Sequence[EvidenceUnit]) -> str:
    parts: list[str] = []
    previous_page: int | None = None
    for unit in records:
        locator = unit.locator
        assert isinstance(locator, PdfLocator)
        if locator.page != previous_page:
            parts.append(_page_marker(locator.page))
            previous_page = locator.page
        parts.extend(
            [
                f"[[EVIDENCE_ID: {unit.evidence_id}]]",
                _unit_text(unit),
            ]
        )
    return "\n\n".join(parts)


def _block_windows(
    units: Sequence[EvidenceUnit],
    *,
    max_block_units: int,
) -> list[DiagnosticRecordWindow]:
    overlap_ids = _table_overlap_block_ids(units)
    by_source: dict[str, list[EvidenceUnit]] = defaultdict(list)
    for unit in units:
        locator = unit.locator
        if (
            isinstance(locator, PdfLocator)
            and locator.block_index is not None
            and locator.table_index is None
            and unit.evidence_id not in overlap_ids
        ):
            by_source[unit.source_id].append(unit)

    windows: list[DiagnosticRecordWindow] = []
    for source_id, records in sorted(by_source.items()):
        records.sort(key=pdf_evidence_sort_key)
        root_indexes = [
            index for index, unit in enumerate(records) if _looks_like_record_root(_unit_text(unit))
        ]
        for root_position, start in enumerate(root_indexes):
            stop_before = root_indexes[root_position + 1] if root_position + 1 < len(root_indexes) else len(records)
            root = records[start]
            supports: list[EvidenceUnit] = []
            previous = root
            for unit in records[start + 1 : stop_before]:
                if _looks_like_record_root(_unit_text(unit)):
                    break
                if not _block_is_contiguous(previous, unit):
                    break
                if _looks_like_section_boundary(_unit_text(unit)):
                    break
                supports.append(unit)
                previous = unit

            structural_records, edge_policy = _split_prose_record(root, supports)
            for structural_record in structural_records:
                # Bound one sequential procedure without silently dropping
                # evidence. Alternative branches are already atomized above.
                support_capacity = max(1, max_block_units - 1)
                branch_supports = structural_record[1:]
                batches = [
                    branch_supports[index : index + support_capacity]
                    for index in range(0, len(branch_supports), support_capacity)
                ] or [[]]
                for batch in batches:
                    selected = [root, *batch]
                    allowed = [unit.evidence_id for unit in selected]
                    branch_anchor = batch[0].evidence_id if batch else root.evidence_id
                    page_numbers = sorted(
                        {
                            unit.locator.page
                            for unit in selected
                            if isinstance(unit.locator, PdfLocator)
                        }
                    )
                    window_id = _stable_window_id(
                        kind="contiguous_blocks",
                        source_id=source_id,
                        record_anchor=root.evidence_id,
                        branch_anchor=branch_anchor,
                        allowed_anchors=allowed,
                    )
                    windows.append(
                        DiagnosticRecordWindow(
                            window_id=window_id,
                            window_kind="contiguous_blocks",
                            source_id=source_id,
                            record_anchor=root.evidence_id,
                            root_anchor=root.evidence_id,
                            branch_anchor=branch_anchor,
                            allowed_source_anchors=allowed,
                            allowed_evidence_spans={
                                unit.evidence_id: [_unit_text(unit)] for unit in selected
                            },
                            evidence_ids=allowed,
                            page_numbers=page_numbers,
                            text_with_pages=_render_block_window(selected),
                            edge_policy=edge_policy,
                        )
                    )
    return windows


def build_diagnostic_record_windows(
    evidence_units: Sequence[EvidenceUnit],
    *,
    included_pages: Iterable[int] | None = None,
    max_block_units: int = 16,
) -> list[DiagnosticRecordWindow]:
    """Build stable, bounded windows from canonical PDF evidence.

    Table rows take precedence over layout blocks that duplicate their text.
    The function is pure: output order and IDs depend only on canonical input,
    not on caller order or model behavior.
    """

    if max_block_units < 1:
        raise ValueError("max_block_units must be at least 1")
    allowed_pages = {int(page) for page in included_pages} if included_pages is not None else None
    eligible = [
        unit
        for unit in evidence_units
        if isinstance(unit.locator, PdfLocator)
        and (allowed_pages is None or unit.locator.page in allowed_pages)
        and _unit_text(unit)
    ]
    table = _table_windows(eligible)
    blocks = _block_windows(eligible, max_block_units=max_block_units)
    physical_position = {
        unit.evidence_id: pdf_evidence_sort_key(unit)
        for unit in eligible
    }
    return sorted(
        [*table, *blocks],
        key=lambda window: (
            physical_position.get(
                window.branch_anchor,
                (min(window.page_numbers), 9, 0, 0, window.branch_anchor),
            ),
            0 if window.window_kind == "table_row" else 1,
            window.window_id,
        ),
    )


__all__ = ["DiagnosticRecordWindow", "build_diagnostic_record_windows"]
