"""Parse raw LLM markdown-table output into ExtractionResult."""

from __future__ import annotations

import logging
import re

from backend.models import (
    CorrectiveAction,
    ExtractionResult,
    FailureMode,
    Severity,
    Symptom,
    Triplet,
)

logger = logging.getLogger(__name__)


def _parse_table_rows(table_text: str) -> list[list[str]]:
    """Parse a Markdown table into a list of row values (excluding header and separator)."""
    lines = [ln.strip() for ln in table_text.strip().split("\n") if ln.strip()]
    rows = []
    for line in lines:
        if line.startswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            # Skip separator rows (---|---|---)
            if cells and all(re.match(r"^-+:?$|^:?-+:?$", c) for c in cells):
                continue
            rows.append(cells)
    # First row is header, rest are data
    return rows


_TABLE_HEADER_RE = {
    "symptom": re.compile(r"^\|\s*symptom_id\s*\|", re.IGNORECASE),
    "failure": re.compile(r"^\|\s*failure_mode_id\s*\|", re.IGNORECASE),
    "action": re.compile(r"^\|\s*action_id\s*\|", re.IGNORECASE),
}


def _is_known_table_header(line: str) -> bool:
    return any(pattern.search(line.strip()) for pattern in _TABLE_HEADER_RE.values())


def _extract_markdown_table(lines: list[str], start_index: int) -> str:
    """Return one Markdown table, stopping at the next table/header boundary."""
    table_lines: list[str] = []
    for index in range(start_index, len(lines)):
        stripped = lines[index].strip()
        if index > start_index and _is_known_table_header(stripped):
            break
        if table_lines and (not stripped or stripped.startswith("#")):
            break
        if stripped.startswith("|"):
            table_lines.append(lines[index])
            continue
        if table_lines:
            break
    return "\n".join(table_lines).strip()


def _split_tables(raw: str) -> tuple[str, str, str]:
    """Split the raw LLM output into exactly the three expected Markdown tables."""
    lines = raw.splitlines()
    table_by_kind = {"symptom": "", "failure": "", "action": ""}
    for index, line in enumerate(lines):
        stripped = line.strip()
        for kind, pattern in _TABLE_HEADER_RE.items():
            if table_by_kind[kind] or not pattern.search(stripped):
                continue
            table_by_kind[kind] = _extract_markdown_table(lines, index)
    return (
        table_by_kind["symptom"],
        table_by_kind["failure"],
        table_by_kind["action"],
    )


def _parse_severity(val: str) -> Severity:
    """Parse severity string, defaulting to Medium if invalid."""
    val_clean = val.strip().capitalize()
    try:
        return Severity(val_clean)
    except ValueError:
        return Severity.MEDIUM


def _parse_page_cell(val: str) -> int:
    match = re.search(r"\d+", str(val or ""))
    if not match:
        return 0
    try:
        return int(match.group(0))
    except ValueError:
        return 0


def parse_extraction(raw: str, source_type: str, source_title: str) -> ExtractionResult:
    """Parse the raw LLM response into structured ExtractionResult."""
    sym_table, fm_table, ca_table = _split_tables(raw)

    # Parse Symptoms
    sym_rows = _parse_table_rows(sym_table)
    symptoms: list[Symptom] = []
    for row in sym_rows[1:]:  # skip header
        if len(row) >= 4:
            evidence_page = _parse_page_cell(row[4]) if len(row) >= 5 else 0
            symptoms.append(Symptom(
                symptom_id=row[0],
                name=row[1],
                description=row[2],
                severity=_parse_severity(row[3]),
                evidence_page=evidence_page,
            ))

    # Parse FailureModes
    fm_rows = _parse_table_rows(fm_table)
    failure_modes: list[FailureMode] = []
    for row in fm_rows[1:]:
        if len(row) >= 5:
            evidence_page = _parse_page_cell(row[5]) if len(row) >= 6 else 0
            failure_modes.append(FailureMode(
                failure_mode_id=row[0],
                name=row[1],
                description=row[2],
                material_context=row[3],
                linked_symptom_id=row[4],
                evidence_page=evidence_page,
            ))

    # Parse CorrectiveActions
    ca_rows = _parse_table_rows(ca_table)
    corrective_actions: list[CorrectiveAction] = []
    for row in ca_rows[1:]:
        if len(row) >= 8:
            try:
                page = int(row[6])
            except ValueError:
                page = 0
            corrective_actions.append(CorrectiveAction(
                action_id=row[0],
                name=row[1],
                description=row[2],
                instruction_text=row[3],
                source_type=row[4] if row[4] else source_type,
                source_title=row[5] if row[5] else source_title,
                source_page=page,
                linked_failure_mode_id=row[7],
            ))

    # Group into triplets
    triplets = _group_into_triplets(symptoms, failure_modes, corrective_actions)

    return ExtractionResult(
        triplets=triplets,
        raw_symptom_table=sym_table,
        raw_failure_mode_table=fm_table,
        raw_corrective_action_table=ca_table,
    )


def _group_into_triplets(
    symptoms: list[Symptom],
    failure_modes: list[FailureMode],
    corrective_actions: list[CorrectiveAction],
) -> list[Triplet]:
    """Group flat lists into Symptom-based triplets."""
    triplets = []
    for sym in symptoms:
        linked_fms = [fm for fm in failure_modes if fm.linked_symptom_id == sym.symptom_id]
        linked_cas = []
        for fm in linked_fms:
            linked_cas.extend(
                ca for ca in corrective_actions if ca.linked_failure_mode_id == fm.failure_mode_id
            )
        triplets.append(Triplet(
            symptom=sym,
            failure_modes=linked_fms,
            corrective_actions=linked_cas,
        ))
    return triplets
