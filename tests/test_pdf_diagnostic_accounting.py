from __future__ import annotations

from types import SimpleNamespace

from backend.domain.locators import PdfLocator
from backend.services.pdf_source_subgraph_generation import (
    _diagnostic_accounting_summary,
)


def _evidence(evidence_id: str, page: int):
    return SimpleNamespace(
        evidence_id=evidence_id,
        locator=PdfLocator(
            page=page,
            quote=f"Canonical evidence {evidence_id}",
            extraction_method="native_text",
            block_index=page,
        ),
    )


def test_publish_gap_and_exclude_are_all_complete_dispositions() -> None:
    by_id = {
        evidence_id: _evidence(evidence_id, page)
        for evidence_id, page in (("ev_publish", 10), ("ev_gap", 11), ("ev_exclude", 12))
    }
    report = {
        "schema_version": "1.0",
        "parsed": True,
        "refusal": False,
        "finish_reason": "stop",
        "candidate_count": 3,
        # A declared gap remains unresolved for graph publication, but it has
        # an auditable disposition and therefore does not make accounting false.
        "unresolved_count": 1,
        "candidate_pages": [10, 11, 12],
        "candidate_page_count": 3,
        "candidate_evidence_anchors": [
            {"evidence_id": "ev_publish", "page": 10},
            {"evidence_id": "ev_gap", "page": 11},
            {"evidence_id": "ev_exclude", "page": 12},
        ],
        "candidate_evidence_anchor_count": 3,
        "candidate_windows": [
            {
                "record_window_id": "window-publish",
                "allowed_source_anchors": ["ev_publish"],
                "pages": [10],
            },
            {
                "record_window_id": "window-gap",
                "allowed_source_anchors": ["ev_gap"],
                "pages": [11],
            },
            {
                "record_window_id": "window-exclude",
                "allowed_source_anchors": ["ev_exclude"],
                "pages": [12],
            },
        ],
        "candidate_window_count": 3,
        "records": [
            {
                "record_window_id": "window-publish",
                "record_anchor": "ev_publish",
                "evidence_ids": [],
                "resolved_evidence_ids": ["ev_publish"],
                "disposition": "publish",
            },
            {
                "record_window_id": "window-gap",
                "branch_anchor": "ev_gap",
                "evidence_ids": [],
                "disposition": "gap",
            },
            {
                "record_window_id": "window-exclude",
                "candidate": {
                    "record_window_id": "window-exclude",
                    "allowed_source_anchors": ["ev_exclude"],
                },
                "disposition": "exclude",
            },
        ],
    }

    summary = _diagnostic_accounting_summary(report, evidence_by_id=by_id)

    assert summary["complete"] is True
    assert summary["disposed_entry_count"] == 3
    assert summary["unaccounted_candidate_pages"] == []
    assert summary["unaccounted_candidate_evidence_ids"] == []
    assert summary["unaccounted_candidate_window_ids"] == []


def test_review_is_accounted_even_though_it_is_not_publishable() -> None:
    by_id = {"ev_review": _evidence("ev_review", 20)}
    report = {
        "schema_version": "1.0",
        "parsed": True,
        "refusal": False,
        "finish_reason": "stop",
        "candidate_count": 1,
        "unresolved_count": 1,
        "candidate_pages": [20],
        "candidate_page_count": 1,
        "candidate_evidence_anchors": [{"evidence_id": "ev_review", "page": 20}],
        "candidate_evidence_anchor_count": 1,
        "records": [
            {
                "record_anchor": "ev_review",
                "branch_anchor": "ev_review",
                "evidence_ids": [],
                "disposition": "review",
                "drop_reasons": [{"code": "ambiguous_branch"}],
            }
        ],
    }

    summary = _diagnostic_accounting_summary(report, evidence_by_id=by_id)

    # Accounting is an inventory property, not a synonym for autonomous
    # publication or approval eligibility.
    assert summary["complete"] is True
    assert summary["accounted_candidate_evidence_ids"] == ["ev_review"]


def test_missing_candidate_entry_or_window_disposition_fails_accounting() -> None:
    by_id = {
        "ev_one": _evidence("ev_one", 30),
        "ev_two": _evidence("ev_two", 31),
    }
    report = {
        "schema_version": "1.0",
        "parsed": True,
        "refusal": False,
        "finish_reason": "stop",
        "candidate_count": 2,
        "candidate_pages": [30, 31],
        "candidate_page_count": 2,
        "candidate_evidence_anchors": [
            {"evidence_id": "ev_one", "page": 30},
            {"evidence_id": "ev_two", "page": 31},
        ],
        "candidate_evidence_anchor_count": 2,
        "candidate_windows": [
            {"record_window_id": "window-one", "allowed_source_anchors": ["ev_one"]},
            {"record_window_id": "window-two", "allowed_source_anchors": ["ev_two"]},
        ],
        "candidate_window_count": 2,
        "records": [
            {
                "record_window_id": "window-one",
                "evidence_ids": ["ev_one"],
                "disposition": "publish",
            }
        ],
    }

    summary = _diagnostic_accounting_summary(report, evidence_by_id=by_id)

    assert summary["complete"] is False
    assert summary["unaccounted_candidate_pages"] == [31]
    assert summary["unaccounted_candidate_evidence_ids"] == ["ev_two"]
    assert summary["unaccounted_candidate_window_ids"] == ["window-two"]


def test_missing_disposition_fails_even_when_provenance_is_present() -> None:
    by_id = {"ev_missing": _evidence("ev_missing", 40)}
    report = {
        "schema_version": "1.0",
        "parsed": True,
        "refusal": False,
        "finish_reason": "stop",
        "candidate_count": 1,
        "candidate_pages": [40],
        "candidate_page_count": 1,
        "records": [{"record_anchor": "ev_missing", "evidence_ids": ["ev_missing"]}],
    }

    summary = _diagnostic_accounting_summary(report, evidence_by_id=by_id)

    assert summary["complete"] is False
    assert summary["entries_without_disposition"] == [0]
