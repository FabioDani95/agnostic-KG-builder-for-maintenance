from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from backend.services.real_call_budget_ledger import (
    ActualTokenUsage,
    RealCallBudgetLedger,
    TokenEnvelope,
)


@pytest.fixture(scope="module")
def analyzer():
    path = (
        Path(__file__).resolve().parents[1]
        / "artifacts"
        / "acceptance"
        / "g3"
        / "diagnostic_benchmark_hardening_20260812"
        / "analyze_campaign.py"
    )
    spec = importlib.util.spec_from_file_location("v8_campaign_analyzer_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _node(node_id: str, node_type: str, label: str) -> dict:
    return {"node_id": node_id, "node_type": node_type, "label": label}


def _relation(
    relation_id: str,
    relation_type: str,
    from_id: str,
    to_id: str,
    branch: str,
) -> dict:
    return {
        "relation_id": relation_id,
        "relation_type": relation_type,
        "from_id": from_id,
        "to_id": to_id,
        "branch_lineage_id": branch,
        "evidence_ids": [],
        "evidence_refs": [],
    }


def test_branch_join_reuses_failure_without_cross_pairing(analyzer) -> None:
    revision = {
        "nodes": [
            _node("s1", "Symptom", "Symptom one"),
            _node("s2", "Symptom", "Symptom two"),
            _node("f", "FailureMode", "Shared cause"),
            _node("a1", "CorrectiveAction", "Action one"),
            _node("a2", "CorrectiveAction", "Action two"),
        ],
        "relations": [
            _relation("i1", "MAY_INDICATE", "s1", "f", "branch-1"),
            _relation("i2", "MAY_INDICATE", "s2", "f", "branch-2"),
            _relation("r1", "RESOLVED_BY", "f", "a1", "branch-1"),
            _relation("r2", "RESOLVED_BY", "f", "a2", "branch-2"),
        ],
    }

    paths = analyzer._branch_aware_paths(revision)

    assert {
        (path["indicator_id"], path["corrective_action_id"])
        for path in paths
    } == {("s1", "a1"), ("s2", "a2")}
    assert analyzer._branch_lineage_audit(revision)["passed"] is True


def test_missing_branch_lineage_is_fail_closed(analyzer) -> None:
    revision = {
        "nodes": [
            _node("s", "Symptom", "Symptom"),
            _node("f", "FailureMode", "Cause"),
            _node("a", "CorrectiveAction", "Action"),
        ],
        "relations": [
            _relation("i", "MAY_INDICATE", "s", "f", ""),
            _relation("r", "RESOLVED_BY", "f", "a", "branch-1"),
        ],
    }

    assert analyzer._branch_aware_paths(revision) == []
    audit = analyzer._branch_lineage_audit(revision)
    assert audit["passed"] is False
    assert audit["missing_relation_ids"] == ["i"]
    assert audit["orphan_action_branches"] == [
        {"failure_mode_id": "f", "branch_lineage_id": "branch-1"}
    ]


def _grounded_revision(*, quote: str, include_refs: bool = True) -> dict:
    locator = {
        "kind": "pdf",
        "page": 7,
        "quote": "Power off, then inspect the fuse.",
        "extraction_method": "native_text",
        "block_index": 3,
        "canonical_text": "Power off, then inspect the fuse.",
    }
    ref_locator = {key: value for key, value in locator.items() if key != "canonical_text"}
    refs = [
        {
            "evidence_id": "ev-1",
            "source_anchor": "ev-1",
            "quote": quote,
            "locator": ref_locator,
        }
    ] if include_refs else []
    return {
        "evidence": [{"evidence_id": "ev-1", "locator": locator}],
        "relations": [{
            "relation_id": "rel-1",
            "relation_type": "RESOLVED_BY",
            "from_id": "f",
            "to_id": "a",
            "evidence_ids": ["ev-1"],
            "evidence_refs": refs,
        }],
    }


def test_grounding_requires_literal_span_and_at_least_one_ref(analyzer) -> None:
    exact = analyzer._strict_grounding(
        _grounded_revision(quote="Power off, then inspect the fuse.")
    )
    punctuation_changed = analyzer._strict_grounding(
        _grounded_revision(quote="Power off then inspect the fuse")
    )
    missing_refs = analyzer._strict_grounding(
        _grounded_revision(quote="", include_refs=False)
    )

    assert exact["passed"] is True
    assert exact["relations_exact"] == 1
    assert punctuation_changed["passed"] is False
    assert "quote_is_exact_nonempty_span" in punctuation_changed["unresolved"][0]["reason"]
    assert missing_refs["passed"] is False
    assert missing_refs["unresolved"][0]["reason"] == "relation_has_no_evidence_refs"
    assert analyzer._strict_grounding({"evidence": [], "relations": []})["passed"] is False


def test_real_run_authentication_checks_mode_sha_version_and_identity(
    analyzer,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = b"frozen manual"
    digest = hashlib.sha256(payload).hexdigest()
    (tmp_path / "manual.pdf").write_bytes(payload)
    monkeypatch.setattr(analyzer, "MANUAL_ROOT", tmp_path)
    spec = {"manual_id": "manual", "file_name": "manual.pdf", "sha256": digest}
    revision = {
        "source_subgraph_revision_id": "revision",
        "workspace_id": "workspace",
        "source_id": "source",
        "pipeline_version": analyzer.EXPECTED_PIPELINE_VERSION,
        "status": "reviewing",
    }
    state = {
        "mode": "real",
        "status": "completed",
        "error": None,
        "generation_started": True,
        "manual_id": "manual",
        "manual_sha256": digest,
        "revision_id": "revision",
        "workspace_id": "workspace",
        "source_id": "source",
        "revision_status": "reviewing",
        "approval_decision_taken": False,
        "api_key_present": True,
        "api_key_exposed": False,
        "authorized_campaign_budget_usd": 1.0,
    }
    ledger = {
        "mode": "real",
        "error": None,
        "manual_id": "manual",
        "campaign_id": analyzer.CAMPAIGN_ID,
        "pipeline_version": analyzer.EXPECTED_PIPELINE_VERSION,
        "revision_id": "revision",
        "workspace_id": "workspace",
        "source_id": "source",
        "authorized_campaign_budget_usd": 1.0,
        "call_count": 0,
        "calls": [],
    }

    audit = analyzer._run_authenticity(
        spec,
        {"revision": revision, "state": state, "ledger": ledger},
    )
    assert audit["passed"] is True

    state["mode"] = "mock"
    assert analyzer._run_authenticity(
        spec,
        {"revision": revision, "state": state, "ledger": ledger},
    )["passed"] is False


def test_shared_budget_ledger_reconciles_every_real_call(
    analyzer,
    tmp_path: Path,
) -> None:
    path = tmp_path / "real_call_budget.jsonl"
    spec = {"manual_id": "manual", "sha256": "a" * 64}
    ledger = RealCallBudgetLedger(path, absolute_budget_usd=1.0)
    reservation = ledger.call(
        call_id="v8:manual:call-1",
        stage="chat.parse:DiagnosticChunkOutput",
        run_id="v8:manual",
        pdf_id=f"sha256:{spec['sha256']}",
        model="gpt-5.6-luna",
        reasoning_effort="medium",
        token_envelope=TokenEnvelope(
            max_prompt_tokens=1000,
            max_completion_tokens=100,
        ),
    )
    finalization = reservation.finalize(
        usage=ActualTokenUsage(prompt_tokens=100, completion_tokens=20),
    )
    actual = float(finalization.actual_cost_usd or 0)
    artifacts = {
        "manual": {
            "revision": {"pipeline_version": analyzer.EXPECTED_PIPELINE_VERSION},
            "ledger": {
                "call_count": 1,
                "calls": [{"model": "gpt-5.6-luna"}],
                "actual_spend_usd": actual,
            }
        }
    }

    audit = analyzer._shared_budget_ledger_audit(
        [spec],
        artifacts,
        path=path,
    )
    assert audit["passed"] is True
    assert audit["reservation_count"] == audit["finalized_count"] == 1
    assert audit["actual_spend_usd"] == pytest.approx(actual)

    artifacts["manual"]["ledger"]["call_count"] = 2
    failed = analyzer._shared_budget_ledger_audit([spec], artifacts, path=path)
    assert failed["passed"] is False
    assert "run_call_count_mismatch:manual" in failed["failures"]


def test_preflight_stopped_run_becomes_explicit_zero_recall_no_go(analyzer) -> None:
    spec = {
        "manual_id": "manual",
        "gold_scope": "exhaustive_troubleshooting_table",
        "gold_claim_recall_floor": 0.75,
        "must_keep_pdf_pages": [11],
        "expected_claims": [{
            "claim_id": "C1",
            "symptom": "Pump stops",
            "failure_mode": "Fuse open",
            "corrective_action": "Replace fuse",
            "expected_disposition": "publish",
        }],
        "forbidden_pairings": [],
    }
    error = {
        "status_code": 409,
        "body": {
            "detail": (
                "PDF generation cost preflight failed: conservative maximum "
                "$0.627536 exceeds the $0.60 ceiling."
            )
        },
    }
    artifacts = {
        "revision": None,
        "state": {
            "status": "stopped_without_retry",
            "error": error,
            "approval_decision_taken": False,
            "merge_started": False,
            "structured_source_processed": False,
        },
        "ledger": {
            "actual_spend_usd": 0,
            "call_count": 0,
            "elapsed_seconds": 3.5,
            "run_hard_ceiling_usd": 0.6,
            "error": error,
        },
    }

    result = analyzer._failed_manual_result(spec, artifacts)

    assert result["semantic"]["gold_claim_recall"] == 0
    assert result["semantic"]["gold_claims_present"] == 0
    assert result["integrity"]["passed"] is False
    assert result["verdict"] == {
        "semantic": "fail",
        "publication_integrity": "fail",
    }
    assert result["operations"]["conservative_preflight_usd"] == 0.627536
    assert result["run_failure"]["status"] == "stopped_without_retry"


def test_final_report_contains_critical_before_after_and_ledger_detail(analyzer) -> None:
    result = json.loads(analyzer.OUTPUT_PATH.read_text(encoding="utf-8"))
    before = json.loads(analyzer.BEFORE_PATH.read_text(encoding="utf-8"))

    report = analyzer._render(result, before)

    assert "| eastman_e554 | 2/8 → 4/8 | 0/8 → 0/8 |" in report
    assert "| danfoss_apf | 1/8 → 6/8 | 1/8 → 3/8 |" in report
    assert "3 autonomous published witness(es), 3 explicit inspection gap(s)" in report
    assert "review-only claims: E4, E6, E7, E8" in report
    assert "stopped_without_retry" in report
    assert "two paid scoping" in report
    assert "42 reservations, 42 finalizations" in report
    assert "936/936 refs; 153/153 rels" in report
    assert "The correct critical decision is **NO-GO**" in report
