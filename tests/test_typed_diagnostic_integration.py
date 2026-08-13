from __future__ import annotations

import asyncio
from types import SimpleNamespace

from backend.models import OntologyDraftRequest
from backend.services.ontology_pipeline import build_initial_ontology
from backend.services.ontology_workflow import (
    _finalize_run_level_quality,
    _merge_pipeline_results,
    draft_ontology_workflow,
)

ASSET_IDENTITY = {
    "asset_id": "asset_typed_integration",
    "name": "Generic pump skid",
    "description": "Pump skid used for typed diagnostic integration tests.",
    "brand": "Generic",
    "model": "P-1",
    "asset_type": "pump_skid",
}

PAGE_8_TEXT = (
    "[[EVIDENCE_ID: ev_typed_page_8]]\n"
    "Problem: Pump vibration.\n"
    "Pump vibration is caused by a loose coupling."
)
PAGE_9_TEXT = (
    "[[EVIDENCE_ID: ev_typed_page_9]]\n"
    "Remedy: To resolve the loose coupling, tighten the coupling to specification.\n"
    "Tighten the coupling to specification."
)


def _configure_fixture(monkeypatch) -> None:
    monkeypatch.setenv("KG_LLM_MODE", "mock")
    monkeypatch.setenv("KG_LLM_FIXTURE", "typed_diagnostic_integration")
    monkeypatch.setenv("KG_LLM_MOCK_DIR", "tests/fixtures")


def _assert_compiled_typed_chain(result) -> None:
    report = result.diagnostic_contract_report
    assert report["schema_version"] == "1.0"
    assert report["candidate_count"] == 1
    assert report["publish_count"] == 1
    assert report["unresolved_count"] == 0

    assert len(result.ontology.nodes["Symptom"]) == 1
    assert len(result.ontology.nodes["FailureMode"]) == 1
    assert len(result.ontology.nodes["CorrectiveAction"]) == 1
    evidence_by_relation = {
        relation.name: [item.model_dump(mode="json") for item in relation.evidence]
        for relation in result.ontology.relations
        if relation.name in {"MAY_INDICATE", "RESOLVED_BY"}
    }
    assert {
        name: [item["quote"] for item in evidence]
        for name, evidence in evidence_by_relation.items()
    } == {
        "MAY_INDICATE": ["Pump vibration is caused by a loose coupling"],
        "RESOLVED_BY": [
            "To resolve the loose coupling, tighten the coupling to specification"
        ],
    }
    assert evidence_by_relation["MAY_INDICATE"][0]["source_anchor"] == "ev_typed_page_8"
    assert evidence_by_relation["RESOLVED_BY"][0]["source_anchor"] == "ev_typed_page_9"


def test_build_initial_ontology_compiles_nonempty_typed_fixture_with_edge_evidence(
    monkeypatch,
):
    _configure_fixture(monkeypatch)
    text = f"--- PAGE 8 ---\n{PAGE_8_TEXT}\n\n--- PAGE 9 ---\n{PAGE_9_TEXT}"

    result, metrics = build_initial_ontology(
        text_with_pages=text,
        source_type="technical PDF",
        source_title="Typed pump manual",
        target_language="en",
        model_name="mock",
        asset_identity=ASSET_IDENTITY,
        extraction_role="diagnostic",
        relation_first=True,
    )

    _assert_compiled_typed_chain(result)
    assert result.diagnostic_contract_report["parsed"] is True
    assert result.diagnostic_contract_report["records"][0]["disposition"] == "publish"
    assert metrics["llm_calls"] == 1
    assert metrics["total_tokens"] == 0


def test_typed_compiler_error_returns_blocked_escalation_report(
    monkeypatch,
) -> None:
    _configure_fixture(monkeypatch)

    def _raise_compiler_error(*_args, **_kwargs):
        raise ValueError("deterministic compiler fixture failure")

    monkeypatch.setattr(
        "backend.services.diagnostic_bundle_compiler.compile_diagnostic_bundles",
        _raise_compiler_error,
    )
    text = f"--- PAGE 8 ---\n{PAGE_8_TEXT}\n\n--- PAGE 9 ---\n{PAGE_9_TEXT}"

    result, metrics = build_initial_ontology(
        text_with_pages=text,
        source_type="technical PDF",
        source_title="Typed pump manual",
        target_language="en",
        model_name="mock",
        asset_identity=ASSET_IDENTITY,
        extraction_role="diagnostic",
        relation_first=True,
    )

    report = result.diagnostic_contract_report
    assert result.status == "blocked"
    assert any(issue.code == "empty_draft_content" for issue in result.schema_issues)
    assert report["parsed"] is True
    assert report["candidate_count"] == 1
    assert report["publish_count"] == 0
    assert report["unresolved_count"] == 1
    assert report["drop_reasons"] == {"diagnostic_compiler_error": 1}
    assert report["error_type"] == "ValueError"
    assert report["escalation_recommended"] is True
    assert metrics["llm_calls"] == 1
    assert len(metrics["llm_call_entries"]) == 1


def test_typed_length_exception_preserves_paid_usage_and_finish_reason(
    monkeypatch,
) -> None:
    class _LengthError(Exception):
        def __init__(self) -> None:
            super().__init__("Could not parse response content as the length limit was reached")
            self.completion = SimpleNamespace(
                model="gpt-5.6-luna",
                usage=SimpleNamespace(
                    prompt_tokens=1000,
                    completion_tokens=8000,
                    total_tokens=9000,
                    prompt_tokens_details=SimpleNamespace(
                        cached_tokens=0,
                        cache_write_tokens=900,
                    ),
                ),
            )

    class _Completions:
        @staticmethod
        def parse(**_kwargs):
            raise _LengthError()

    monkeypatch.setattr(
        "backend.services.ontology_pipeline._get_client",
        lambda *_args, **_kwargs: SimpleNamespace(
            chat=SimpleNamespace(completions=_Completions())
        ),
    )
    text = f"--- PAGE 8 ---\n{PAGE_8_TEXT}\n\n--- PAGE 9 ---\n{PAGE_9_TEXT}"

    result, metrics = build_initial_ontology(
        text_with_pages=text,
        source_type="technical PDF",
        source_title="Typed pump manual",
        target_language="en",
        model_name="gpt-5.6-luna",
        asset_identity=ASSET_IDENTITY,
        extraction_role="diagnostic",
        relation_first=True,
    )

    assert result.diagnostic_contract_report["finish_reason"] == "length"
    assert result.diagnostic_contract_report["parsed"] is False
    assert metrics["llm_calls"] == 1
    assert metrics["prompt_tokens"] == 1000
    assert metrics["completion_tokens"] == 8000
    assert metrics["llm_call_entries"][0]["call_role"] == "primary"


def test_typed_record_crosses_page_8_9_chunk_boundary_via_real_workflow_overlap(
    monkeypatch,
):
    _configure_fixture(monkeypatch)
    pages = [
        {
            "page_number": page,
            "text": (
                PAGE_8_TEXT
                if page == 8
                else PAGE_9_TEXT
                if page == 9
                else f"[[EVIDENCE_ID: ev_typed_page_{page}]]\nReference page {page}."
            ),
            "text_source": "native_text",
        }
        for page in range(1, 11)
    ]
    store = {
        "pdf_id": "pdf_typed_boundary",
        "filename": "typed-boundary.pdf",
        "pages": pages,
        "asset_identity": ASSET_IDENTITY,
        "asset_identity_is_canonical": True,
        "cut_plan": {
            "pages_to_keep": list(range(1, 11)),
            "sections": [
                {
                    "name": "Troubleshooting",
                    "start": 1,
                    "end": 10,
                    "source": "fixture",
                }
            ],
        },
        "pdf_extraction_roles": {
            "diagnostic_pages": list(range(1, 11)),
            "structural_pages": [],
        },
        # This deliberately incomplete advisory inventory must never reduce
        # the semantic scope to page 8.
        "diagnostic_record_windows": [{
            "window_id": "window_only_page_8",
            "record_anchor": "ev_typed_page_8",
            "branch_anchor": "ev_typed_page_8",
            "allowed_source_anchors": ["ev_typed_page_8"],
            "page_numbers": [8],
            "text_with_pages": f"--- PAGE 8 ---\n{PAGE_8_TEXT}",
        }],
    }

    result = asyncio.run(draft_ontology_workflow(
        store,
        OntologyDraftRequest(
            pdf_id="pdf_typed_boundary",
            source_type="technical PDF",
            source_title="Typed boundary manual",
            # The gateway remains in deterministic mock mode; Luna pricing keeps
            # the real production cost guard representative and below its cap.
            model_name="gpt-5.6-luna",
            pages_to_keep=list(range(1, 11)),
            target_language="en",
        ),
    ))

    _assert_compiled_typed_chain(result)
    assert result.status == "ready"
    assert not any(issue.code == "empty_draft_content" for issue in result.schema_issues)
    chunks = result.diagnostic_contract_report["chunks"]
    assert len(chunks) == 3
    assert sum(chunk["publish_count"] for chunk in chunks) == 1
    assert any(chunk["unresolved_count"] == 0 for chunk in chunks)
    report = result.diagnostic_contract_report
    assert report["diagnostic_input_policy"] == "semantic_scope_full_page_v1"
    assert report["expected_diagnostic_pages"] == list(range(1, 11))
    assert report["processed_diagnostic_pages"] == list(range(1, 11))
    assert report["unprocessed_diagnostic_pages"] == []
    assert report["diagnostic_page_coverage_complete"] is True


def test_merge_preserves_chunk_contract_failure_without_detected_anchors(monkeypatch):
    _configure_fixture(monkeypatch)
    text = f"--- PAGE 8 ---\n{PAGE_8_TEXT}\n\n--- PAGE 9 ---\n{PAGE_9_TEXT}"
    successful, _metrics = build_initial_ontology(
        text_with_pages=text,
        source_type="technical PDF",
        source_title="Typed pump manual",
        target_language="en",
        model_name="mock",
        asset_identity=ASSET_IDENTITY,
        extraction_role="diagnostic",
        relation_first=True,
    )
    failed = successful.model_copy(update={
        "status": "blocked",
        "ontology": successful.ontology.model_copy(update={
            "nodes": {node_type: [] for node_type in successful.ontology.nodes},
            "relations": [],
        }),
        "semantic_issues": [],
        "schema_issues": [],
        "human_required_fields": [],
        "is_schema_compliant": False,
        "is_ready_for_human_review": False,
        "diagnostic_contract_report": {
            "schema_version": "1.0",
            "parsed": False,
            "refusal": False,
            "finish_reason": "provider_error",
            "input_pages": [10],
            "candidate_input_anchors": [],
            "records": [],
            "candidate_count": 0,
            "publish_count": 0,
            "unresolved_count": 1,
            "escalation_recommended": True,
        },
    })

    merged = _merge_pipeline_results(
        [successful, failed],
        asset_identity=ASSET_IDENTITY,
    )

    report = merged.diagnostic_contract_report
    assert report["contract_failure_count"] == 1
    assert report["parsed"] is False
    assert report["finish_reason"] == "incomplete"
    assert report["escalation_recommended"] is True
    assert merged.status == "blocked"
    assert merged.is_schema_compliant is False
    assert merged.is_ready_for_human_review is False

    finalized, _usage, _resolution, _quality = _finalize_run_level_quality(
        merged,
        [
            {"page_number": 8, "text": PAGE_8_TEXT},
            {"page_number": 9, "text": PAGE_9_TEXT},
            {"page_number": 10, "text": "Reference page without diagnostics."},
        ],
        "mock",
        ASSET_IDENTITY,
        relation_first=True,
    )
    assert finalized.status == "blocked"
    assert finalized.is_schema_compliant is False
    assert finalized.is_ready_for_human_review is False


def test_merge_deduplicates_drop_reason_accounting_for_overlapped_record(monkeypatch):
    _configure_fixture(monkeypatch)
    text = f"--- PAGE 8 ---\n{PAGE_8_TEXT}\n\n--- PAGE 9 ---\n{PAGE_9_TEXT}"
    result, _metrics = build_initial_ontology(
        text_with_pages=text,
        source_type="technical PDF",
        source_title="Typed pump manual",
        target_language="en",
        model_name="mock",
        asset_identity=ASSET_IDENTITY,
        extraction_role="diagnostic",
        relation_first=True,
    )
    record = {
        **result.diagnostic_contract_report["records"][0],
        "disposition": "review",
        "drop_reasons": [{
            "code": "ambiguous_branch",
            "path": "",
            "message": "Branch pairing needs review.",
        }],
    }
    overlapped = result.model_copy(update={
        "diagnostic_contract_report": {
            **result.diagnostic_contract_report,
            "publish_count": 0,
            "unresolved_count": 1,
            "records": [record],
            "drop_reasons": {"ambiguous_branch": 1},
        },
    })

    merged = _merge_pipeline_results(
        [overlapped, overlapped],
        asset_identity=ASSET_IDENTITY,
    )

    assert merged.diagnostic_contract_report["candidate_count"] == 1
    assert merged.diagnostic_contract_report["unresolved_count"] == 1
    assert merged.diagnostic_contract_report["drop_reasons"] == {
        "ambiguous_branch": 1,
    }
