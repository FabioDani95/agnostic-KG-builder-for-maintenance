"""Bounded recovery planning; no rewriting, inference or automatic approval."""
from __future__ import annotations

import json
import re
from typing import Any

RECOVERABLE_CODES = {
    "quote_not_in_anchored_evidence", "source_page_mismatch", "unknown_source_anchor",
    "relation_endpoint_support_unestablished", "missing_resolution_evidence",
    "missing_indicator_failure_evidence", "lineage_anchor_outside_bundle",
}


def procedure_context_packets(pages, *, max_chars, max_pages=8, min_pages=4, diagnostic_page_numbers=None):
    """Supplement split chunks with a bounded, explicitly delimited named test.

    Only source headings delimit the procedure. No number or manufacturer is
    privileged. References in running prose and lettered subtests are not roots.
    """
    headings = []
    for index, page in enumerate(pages):
        matches = re.findall(r"(?im)^\s*Test\s+(\d+)\s*[-–—:]\s+[^\n]+", page["text"])
        if matches:
            headings.append((index, matches[0]))
    result = []
    for (start, number), (stop, following) in zip(headings, headings[1:]):
        group = pages[start:stop]
        if diagnostic_page_numbers is not None and group[0]["page_number"] not in diagnostic_page_numbers:
            continue
        if following == number or not min_pages < len(group) <= max_pages:
            continue
        if any(b["page_number"] != a["page_number"] + 1 for a, b in zip(group, group[1:])):
            continue
        if sum(len(p["text"]) + 80 for p in group) <= max_chars:
            result.append(group)
    return result


def recovery_feedback(report: dict[str, Any]) -> str:
    """Compiler diagnostics are repair targets, never source evidence."""
    targets = [{"branch_lineage_id": r.get("branch_lineage_id"),
                "candidate": r.get("candidate"), "errors": r.get("drop_reasons", [])}
               for r in report.get("records", [])
               if r.get("disposition") == "review" and
               RECOVERABLE_CODES.intersection(x.get("code") for x in r.get("drop_reasons", []))]
    return ("\n\nREPAIR TARGETS (prior untrusted predictions, NOT evidence):\n"
            + json.dumps(targets, ensure_ascii=False)
            + "\nRe-read the source and return only corrected target records. Keep all source-stated conditions, "
              "prerequisites and ordered checks. A missing cause is not permission to invent one. "
              "Do not return unrelated records or use these diagnostics as citations.") if targets else ""


def recovery_packets(report: dict[str, Any], pages: list[dict], windows: list[dict], *, limit: int) -> list[tuple[list[dict], list[dict]]]:
    """Re-read smaller source packets after truncation or record validation failure.

    Refusals are never retried. A valid sibling is retained by the caller.
    Compiler failures receive one bounded repair with the original source.
    A prediction referring exclusively to absent anchors has no local target.
    """
    if limit <= 0 or report.get("refusal"):
        return []
    invalid = [entry for entry in report.get("records", []) if entry.get("accounting_state") == "record_schema_invalid"]
    truncated = report.get("finish_reason") == "length"
    if not truncated and not invalid:
        anchors = {anchor.strip() for page in pages for anchor in
                   re.findall(r"\[\[EVIDENCE_ID:\s*([^\]]+)\]\]", page["text"])}
        recoverable = [r for r in report.get("records", []) if r.get("disposition") == "review"
                       and RECOVERABLE_CODES.intersection(x.get("code") for x in r.get("drop_reasons", []))
                       and ("unknown_lineage_anchor" not in {x.get("code") for x in r.get("drop_reasons", [])}
                            or anchors.intersection([r.get("record_anchor"), r.get("branch_anchor"), *r.get("resolved_evidence_ids", [])]))
                       and "structurally_ambiguous_pairing" not in {x.get("code") for x in r.get("drop_reasons", [])}]
        if not recoverable:
            return []
        ids = {r.get("record_window_id") for r in recoverable}
        selected = [w for w in windows if w.get("window_id") in ids]
        # Keep the whole source chunk for prose: dropping the previous page
        # drops test prerequisites. One bounded attempt, never recursive.
        return [(pages, selected if windows else [])]
    target_windows = windows
    target_pages = pages
    if invalid and not truncated:
        ids = {str(entry.get("record_window_id") or "") for entry in invalid}
        selected = [window for window in windows if window.get("window_id") in ids]
        if selected:
            target_windows = selected
        numbers: set[int] = set()
        def visit(value):
            if isinstance(value, dict):
                if isinstance(value.get("source_page"), int):
                    numbers.add(value["source_page"])
                for item in value.values():
                    visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)
        for entry in invalid:
            visit(entry.get("invalid_payload"))
        if numbers:
            target_pages = [page for page in pages if page["page_number"] in numbers]
    if target_windows:
        groups = [target_windows]
        if len(target_windows) > 1 and limit > 1:
            midpoint = (len(target_windows) + 1) // 2
            groups = [target_windows[:midpoint], target_windows[midpoint:]]
        return [([p for p in target_pages if p["page_number"] in {n for w in group for n in w["page_numbers"]}], group) for group in groups][:limit]
    if len(target_pages) > 1 and limit > 1:
        midpoint = (len(target_pages) + 1) // 2
        # Include a page of continuation context; no information is dropped.
        # Two-page packets cannot shrink with overlap, but retry is still bound.
        return [(target_pages[:midpoint + (len(target_pages) > 2)], []), (target_pages[midpoint:], [])]
    return [(target_pages, [])] if target_pages else []
