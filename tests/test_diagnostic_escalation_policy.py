from __future__ import annotations

import json

import pytest

from backend.app_config import get_diagnostic_escalation_config
from backend.domain.diagnostic_bundles import DiagnosticChunkOutput
from backend.services.ontology_workflow import (
    _chunk_call_ledger_entries,
    _diagnostic_escalation_priority,
    _diagnostic_escalation_reason,
    _diagnostic_output_token_limit,
    _merge_escalated_chunk_metrics,
    _prefer_escalated_diagnostic_report,
)
from backend.services.pdf_cost_guard import estimate_pdf_generation_envelope
from backend.services.run_metrics import aggregate_usage, estimate_cost_usd


def _envelope(**overrides):
    kwargs = {
        "model_name": "gpt-5.6-luna",
        "chunk_input_characters": [12000, 14000, 9000, 8000, 5000],
        "extraction_max_output_tokens": 16000,
        "coverage_enabled": True,
        "coverage_max_input_tokens": 30000,
        "coverage_max_output_tokens": 4500,
        "resolution_enabled": True,
        "resolution_max_targets": 6,
        "resolution_max_input_tokens": 12500,
        "resolution_max_output_tokens": 2500,
        "scoping_actual_cost_usd": 0.005,
    }
    kwargs.update(overrides)
    return estimate_pdf_generation_envelope(**kwargs)


def _usage_entry(model: str, operation: str, effort: str, role: str) -> dict:
    return {
        "operation": operation,
        "model": model,
        "pricing_model": model,
        "prompt": 100,
        "completion": 20,
        "total": 120,
        "cached_prompt": 0,
        "non_cached_prompt": 100,
        "estimated_cost_usd": 0.001,
        "reasoning_effort": effort,
        "call_role": role,
        "escalation_reason": "zero_publishable_candidates" if role == "escalation" else "",
    }


def test_diagnostic_escalation_defaults_fail_closed() -> None:
    cfg = get_diagnostic_escalation_config()

    assert cfg["enabled"] is False
    assert cfg["max_chunks_per_run"] == 0
    assert cfg["primary_model"] == "gpt-5.6-luna"
    assert cfg["model"] == "gpt-5.6-terra"
    schema_characters = len(json.dumps(
        DiagnosticChunkOutput.model_json_schema(),
        sort_keys=True,
        separators=(",", ":"),
    ))
    # Reserve the schema plus provider JSON-envelope/name metadata without
    # coupling the application test to an OpenAI SDK private helper.
    assert cfg["schema_overhead_characters"] >= schema_characters + 1000


def test_cost_envelope_reserves_each_configured_terra_call() -> None:
    baseline = _envelope()
    escalated = _envelope(
        diagnostic_escalation_enabled=True,
        diagnostic_escalation_model_name="gpt-5.6-terra",
        diagnostic_escalation_max_calls=1,
        diagnostic_escalation_max_input_characters=60000,
        diagnostic_escalation_fixed_prompt_overhead_characters=10000,
        diagnostic_escalation_max_output_tokens=4000,
    )

    assert escalated["maximum_call_count"] == baseline["maximum_call_count"] + 1
    assert escalated["assumptions"]["diagnostic_escalation_max_calls"] == 1
    assert escalated["assumptions"]["diagnostic_escalation_max_input_characters"] == 60000
    assert (
        escalated["assumptions"][
            "diagnostic_escalation_fixed_prompt_overhead_characters"
        ]
        == 10000
    )
    assert escalated["assumptions"]["diagnostic_escalation_ceiling_prompt_tokens"] == 70000
    assert escalated["by_stage_max_usd"]["diagnostic_escalation"] == round(
        estimate_cost_usd(
            prompt_tokens=70000,
            completion_tokens=4000,
            cache_write_prompt_tokens=70000,
            model_name="gpt-5.6-terra",
        ),
        6,
    )
    assert escalated["conservative_max_cost_usd"] > baseline["conservative_max_cost_usd"]


def test_cost_envelope_exposes_current_ceiling_conflict_before_calls() -> None:
    escalated = _envelope(
        diagnostic_escalation_enabled=True,
        diagnostic_escalation_model_name="gpt-5.6-terra",
        diagnostic_escalation_max_calls=5,
        diagnostic_escalation_max_input_characters=60000,
        diagnostic_escalation_max_output_tokens=4000,
    )

    assert escalated["conservative_max_cost_usd"] > 0.49


def test_cost_envelope_rejects_unbounded_terra_configuration() -> None:
    with pytest.raises(
        ValueError,
        match="Positive diagnostic escalation input/output caps",
    ):
        _envelope(
            diagnostic_escalation_enabled=True,
            diagnostic_escalation_model_name="gpt-5.6-terra",
            diagnostic_escalation_max_calls=1,
            diagnostic_escalation_max_input_characters=0,
            diagnostic_escalation_max_output_tokens=4000,
        )


def test_cost_envelope_rejects_structured_schema_underreserve() -> None:
    with pytest.raises(ValueError, match="schema overhead is below"):
        _envelope(
            diagnostic_escalation_enabled=True,
            diagnostic_escalation_model_name="gpt-5.6-terra",
            diagnostic_escalation_max_calls=1,
            diagnostic_escalation_max_input_characters=60000,
            diagnostic_escalation_fixed_prompt_overhead_characters=1,
            diagnostic_escalation_max_output_tokens=4000,
        )


def test_cost_envelope_applies_long_context_pricing_per_call() -> None:
    envelope = _envelope(
        chunk_input_characters=[120000, 120000],
        fixed_prompt_overhead_characters=30000,
        extraction_max_output_tokens=0,
        coverage_enabled=False,
        resolution_enabled=False,
    )
    per_call_cost = estimate_cost_usd(
        prompt_tokens=150000,
        completion_tokens=0,
        cache_write_prompt_tokens=150000,
        model_name="gpt-5.6-luna",
    )

    assert envelope["policy"] == "pdf_relation_first_bounded_v2"
    assert envelope["by_stage_max_usd"]["draft"] == round(2 * per_call_cost, 6)
    assert envelope["by_stage_max_usd"]["draft"] < estimate_cost_usd(
        prompt_tokens=300000,
        completion_tokens=0,
        cache_write_prompt_tokens=300000,
        model_name="gpt-5.6-luna",
    )


def test_cost_envelope_prices_typed_and_structural_output_caps_separately() -> None:
    envelope = _envelope(
        chunk_input_characters=[1000, 1000],
        chunk_max_output_tokens=[4000, 16000],
        fixed_prompt_overhead_characters=0,
        coverage_enabled=False,
        resolution_enabled=False,
    )
    expected = sum(
        estimate_cost_usd(
            prompt_tokens=1000,
            completion_tokens=output,
            cache_write_prompt_tokens=1000,
            model_name="gpt-5.6-luna",
        )
        for output in (4000, 16000)
    )
    assert envelope["by_stage_max_usd"]["draft"] == round(expected, 6)


def test_escalation_is_selective_and_never_retries_refusals() -> None:
    assert _diagnostic_escalation_reason({
        "refusal": True,
        "escalation_recommended": True,
    }) is None

    assert _diagnostic_escalation_reason({
        "parsed": True,
        "candidate_count": 1,
        "publish_count": 0,
        "unresolved_count": 1,
        "drop_reasons": {"check_only": 1},
        "escalation_recommended": True,
    }) is None
    assert _diagnostic_escalation_reason({
        "parsed": True,
        "candidate_count": 1,
        "publish_count": 0,
        "unresolved_count": 1,
        "drop_reasons": {"record_window_missing_disposition": 1},
        "escalation_recommended": True,
    }) == "invalid_or_ambiguous_candidates"


def test_escalation_priority_preserves_the_cap_for_hard_contract_failures() -> None:
    zero_publishable = {
        "parsed": True,
        "candidate_count": 2,
        "publish_count": 0,
        "escalation_recommended": True,
    }
    parse_failed = {
        "parsed": False,
        "finish_reason": "error",
        "escalation_recommended": True,
    }
    truncated = {
        "parsed": False,
        "finish_reason": "length",
        "escalation_recommended": True,
    }

    assert _diagnostic_escalation_priority(truncated) > _diagnostic_escalation_priority(parse_failed)
    assert _diagnostic_escalation_priority(parse_failed) > _diagnostic_escalation_priority(zero_publishable)


def test_equal_priority_candidates_rank_more_unresolved_records_first() -> None:
    reports = [
        ({"parsed": True, "candidate_count": 6, "publish_count": 1, "unresolved_count": 3,
          "escalation_recommended": True}, 1),
        ({"parsed": True, "candidate_count": 9, "publish_count": 0, "unresolved_count": 8,
          "escalation_recommended": True}, 4),
    ]
    ranked = sorted(
        reports,
        key=lambda item: (
            -_diagnostic_escalation_priority(item[0]),
            -int(item[0]["unresolved_count"]),
            -int(item[0]["candidate_count"]),
            item[1],
        ),
    )

    assert ranked[0][1] == 4
    assert _diagnostic_escalation_reason({
        "parsed": True,
        "candidate_count": 0,
        "publish_count": 0,
        "escalation_recommended": True,
    }) == "zero_diagnostic_candidates"
    assert _diagnostic_escalation_reason({
        "parsed": True,
        "candidate_count": 2,
        "publish_count": 0,
        "escalation_recommended": True,
    }) == "zero_publishable_candidates"
    assert _diagnostic_escalation_reason({
        "parsed": True,
        "candidate_count": 2,
        "publish_count": 2,
        "unresolved_count": 0,
        "escalation_recommended": False,
    }) is None


def test_escalated_result_only_wins_when_contract_score_improves() -> None:
    primary = {"parsed": True, "candidate_count": 3, "publish_count": 2, "unresolved_count": 1}
    better = {"parsed": True, "candidate_count": 3, "publish_count": 3, "unresolved_count": 0}
    lower_coverage = {"parsed": True, "candidate_count": 1, "publish_count": 1, "unresolved_count": 0}

    assert _prefer_escalated_diagnostic_report(primary, better) is True
    assert _prefer_escalated_diagnostic_report(primary, lower_coverage) is False


def test_atomic_table_output_bound_is_smaller_than_multibranch_prose_bound() -> None:
    cfg = {
        "diagnostic_bundle_max_output_tokens": 8000,
        "diagnostic_atomic_table_max_output_tokens": 3000,
    }
    atomic = [{"window_kind": "table_row", "structure_status": "atomic"}]
    prose = [{"window_kind": "contiguous_blocks", "structure_status": "atomic"}]

    assert _diagnostic_output_token_limit(atomic, cfg) == 3000
    assert _diagnostic_output_token_limit(prose, cfg) == 8000


def test_escalated_chunk_ledger_preserves_each_model_and_effort() -> None:
    primary_entry = _usage_entry(
        "gpt-5.6-luna", "diagnostic_bundle_extraction", "medium", "primary"
    )
    terra_entry = _usage_entry(
        "gpt-5.6-terra", "diagnostic_bundle_escalation", "high", "escalation"
    )
    primary = {
        **aggregate_usage([primary_entry]),
        "llm_call_entries": [primary_entry],
        "chunk_index": 2,
        "extraction_role": "diagnostic",
    }
    terra = {
        **aggregate_usage([terra_entry]),
        "llm_call_entries": [terra_entry],
    }

    merged = _merge_escalated_chunk_metrics(primary, terra)
    ledger = _chunk_call_ledger_entries(merged, "low")

    assert merged["llm_calls"] == 2
    assert [entry["model"] for entry in ledger] == ["gpt-5.6-luna", "gpt-5.6-terra"]
    assert [entry["reasoning_effort"] for entry in ledger] == ["medium", "high"]
    assert [entry["call_role"] for entry in ledger] == ["primary", "escalation"]
    assert all(entry["chunk_index"] == 2 for entry in ledger)
