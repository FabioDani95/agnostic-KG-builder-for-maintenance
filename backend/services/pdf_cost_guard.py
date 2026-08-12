"""Conservative preflight for one bounded PDF G3 generation."""

from __future__ import annotations

import json
from typing import Any

from backend.domain.diagnostic_bundles import DiagnosticChunkOutput
from backend.services.run_metrics import estimate_cost_usd

_DIAGNOSTIC_RESPONSE_FORMAT_MIN_OVERHEAD_CHARACTERS = len(json.dumps(
    DiagnosticChunkOutput.model_json_schema(),
    sort_keys=True,
    separators=(",", ":"),
)) + 1000


def estimate_pdf_generation_envelope(
    *,
    model_name: str,
    chunk_input_characters: list[int],
    extraction_max_output_tokens: int,
    coverage_enabled: bool,
    coverage_max_input_tokens: int,
    coverage_max_output_tokens: int,
    resolution_enabled: bool,
    resolution_max_targets: int,
    resolution_max_input_tokens: int,
    resolution_max_output_tokens: int,
    scoping_actual_cost_usd: float = 0.0,
    scoping_actual_call_count: int = 0,
    fixed_prompt_overhead_characters: int = 30000,
    diagnostic_escalation_enabled: bool = False,
    diagnostic_escalation_model_name: str = "gpt-5.6-terra",
    diagnostic_escalation_max_calls: int = 0,
    diagnostic_escalation_max_input_characters: int = 0,
    diagnostic_escalation_fixed_prompt_overhead_characters: int = 10000,
    diagnostic_escalation_max_output_tokens: int = 0,
) -> dict[str, Any]:
    """Return central and conservative cost without making an API call.

    For the ceiling, one character is counted as one token, every prompt token
    is priced as a cache write, and no cache-hit credit is assumed. Each call is
    priced independently so the GPT-5.6 long-context multiplier is applied only
    when that individual request crosses its threshold. The relation-first path
    disables SDK retries and output-parse retries, so the call count below is a
    genuine maximum rather than an average.
    """
    chunk_count = len(chunk_input_characters)
    draft_prompt_ceilings = [
        max(0, int(characters)) + max(0, int(fixed_prompt_overhead_characters))
        for characters in chunk_input_characters
    ]
    draft_output_per_call = max(0, int(extraction_max_output_tokens))
    draft_ceiling = sum(
        estimate_cost_usd(
            prompt_tokens=prompt_tokens,
            completion_tokens=draft_output_per_call,
            cache_write_prompt_tokens=prompt_tokens,
            model_name=model_name,
        )
        for prompt_tokens in draft_prompt_ceilings
    )

    coverage_ceiling = 0.0
    if coverage_enabled:
        coverage_ceiling = estimate_cost_usd(
            prompt_tokens=max(0, int(coverage_max_input_tokens)),
            completion_tokens=max(0, int(coverage_max_output_tokens)),
            cache_write_prompt_tokens=max(0, int(coverage_max_input_tokens)),
            model_name=model_name,
        )

    if resolution_enabled and int(resolution_max_targets) <= 0:
        raise ValueError("A positive resolution target cap is required for a bounded cost envelope")
    resolution_calls = max(0, int(resolution_max_targets)) if resolution_enabled else 0
    resolution_ceiling = resolution_calls * estimate_cost_usd(
        prompt_tokens=max(0, int(resolution_max_input_tokens)),
        completion_tokens=max(0, int(resolution_max_output_tokens)),
        cache_write_prompt_tokens=max(0, int(resolution_max_input_tokens)),
        model_name=model_name,
    )
    escalation_calls = (
        max(0, int(diagnostic_escalation_max_calls))
        if diagnostic_escalation_enabled
        else 0
    )
    escalation_model = str(diagnostic_escalation_model_name or "").strip()
    if escalation_calls and not escalation_model:
        raise ValueError("A diagnostic escalation model is required for a bounded cost envelope")
    if escalation_calls and (
        int(diagnostic_escalation_max_input_characters) <= 0
        or int(diagnostic_escalation_max_output_tokens) <= 0
    ):
        raise ValueError(
            "Positive diagnostic escalation input/output caps are required for "
            "a bounded cost envelope"
        )
    if escalation_calls and (
        int(diagnostic_escalation_fixed_prompt_overhead_characters)
        < _DIAGNOSTIC_RESPONSE_FORMAT_MIN_OVERHEAD_CHARACTERS
    ):
        raise ValueError(
            "Diagnostic escalation schema overhead is below the current "
            f"structured-output minimum of "
            f"{_DIAGNOSTIC_RESPONSE_FORMAT_MIN_OVERHEAD_CHARACTERS} characters"
        )
    # The hard ceiling deliberately prices every permitted input character as
    # one token. This matches the conservative rule used for draft chunks and
    # cannot under-reserve relative to the runtime max_input_chars guardrail.
    escalation_input_ceiling = max(
        0,
        int(diagnostic_escalation_max_input_characters),
    )
    escalation_schema_overhead = max(
        0,
        int(diagnostic_escalation_fixed_prompt_overhead_characters),
    )
    escalation_prompt_ceiling = escalation_input_ceiling + escalation_schema_overhead
    escalation_ceiling = escalation_calls * estimate_cost_usd(
        prompt_tokens=escalation_prompt_ceiling,
        completion_tokens=max(0, int(diagnostic_escalation_max_output_tokens)),
        cache_write_prompt_tokens=escalation_prompt_ceiling,
        model_name=escalation_model,
    )
    ceiling = (
        float(scoping_actual_cost_usd)
        + draft_ceiling
        + coverage_ceiling
        + resolution_ceiling
        + escalation_ceiling
    )

    # Central case uses the normal four-characters-per-token approximation and
    # 40% of bounded output.  It is an estimate, explicitly distinct from the
    # cache-write maximum above.
    draft_prompt_central_per_call = [
        (max(0, int(characters)) + max(0, int(fixed_prompt_overhead_characters))) // 4
        for characters in chunk_input_characters
    ]
    draft_output_central_per_call = round(draft_output_per_call * 0.40)
    central = float(scoping_actual_cost_usd) + sum(
        estimate_cost_usd(
            prompt_tokens=prompt_tokens,
            completion_tokens=draft_output_central_per_call,
            model_name=model_name,
        )
        for prompt_tokens in draft_prompt_central_per_call
    )
    if coverage_enabled:
        central += estimate_cost_usd(
            prompt_tokens=coverage_max_input_tokens // 2,
            completion_tokens=round(coverage_max_output_tokens * 0.35),
            model_name=model_name,
        )
    if resolution_enabled:
        # The gate normally leaves only a subset of the capped targets.
        central_resolution_calls = min(resolution_calls, 2)
        central += central_resolution_calls * estimate_cost_usd(
            prompt_tokens=resolution_max_input_tokens // 2,
            completion_tokens=round(resolution_max_output_tokens * 0.35),
            model_name=model_name,
        )
    if escalation_calls:
        # Selective recovery is exceptional. The central estimate reserves one
        # compact retry using the normal four-characters-per-token estimate,
        # while the hard ceiling reserves the configured maximum call count at
        # the deliberately conservative one-character-per-token rate.
        central += estimate_cost_usd(
            prompt_tokens=escalation_prompt_ceiling // 4,
            completion_tokens=round(
                max(0, int(diagnostic_escalation_max_output_tokens)) * 0.35
            ),
            model_name=escalation_model,
        )

    post_scoping_maximum_call_count = (
        chunk_count + int(coverage_enabled) + resolution_calls + escalation_calls
    )
    return {
        "policy": "pdf_relation_first_bounded_v2",
        "model": model_name,
        "diagnostic_escalation_model": escalation_model if escalation_calls else "",
        "chunk_count": chunk_count,
        "maximum_call_count": max(0, int(scoping_actual_call_count)) + post_scoping_maximum_call_count,
        "maximum_post_scoping_call_count": post_scoping_maximum_call_count,
        "assumptions": {
            "sdk_retries": 0,
            "manual_retries": 0,
            "draft_parse_retries": 0,
            "cached_input_credit": 0,
            "cache_write_prompt_tokens_per_prompt_token": 1,
            "cache_write_price_multiplier": 1.25,
            "long_context_pricing_applied_per_call": True,
            "ceiling_prompt_tokens_per_character": 1,
            "fixed_prompt_overhead_characters_per_chunk": fixed_prompt_overhead_characters,
            "diagnostic_escalation_max_calls": escalation_calls,
            "diagnostic_escalation_max_input_characters": (
                escalation_input_ceiling if escalation_calls else 0
            ),
            "diagnostic_escalation_fixed_prompt_overhead_characters": (
                escalation_schema_overhead if escalation_calls else 0
            ),
            "diagnostic_escalation_min_schema_overhead_characters": (
                _DIAGNOSTIC_RESPONSE_FORMAT_MIN_OVERHEAD_CHARACTERS
                if escalation_calls
                else 0
            ),
            "diagnostic_escalation_ceiling_prompt_tokens": (
                escalation_prompt_ceiling if escalation_calls else 0
            ),
            "diagnostic_escalation_max_output_tokens": (
                max(0, int(diagnostic_escalation_max_output_tokens)) if escalation_calls else 0
            ),
        },
        "central_estimated_cost_usd": round(central, 6),
        "conservative_max_cost_usd": round(ceiling, 6),
        "by_stage_max_usd": {
            "scoping_already_spent": round(float(scoping_actual_cost_usd), 6),
            "draft": round(draft_ceiling, 6),
            "coverage_completion": round(coverage_ceiling, 6),
            "resolution_completion": round(resolution_ceiling, 6),
            "diagnostic_escalation": round(escalation_ceiling, 6),
        },
    }
