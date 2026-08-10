"""Conservative preflight for one bounded PDF G3 generation."""

from __future__ import annotations

from typing import Any

from backend.services.run_metrics import estimate_cost_usd


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
) -> dict[str, Any]:
    """Return central and conservative cost without making an API call.

    For the ceiling, one character is counted as one token and no cache credit
    is assumed.  Each enabled call uses its configured maximum output.  The
    relation-first path disables SDK retries and output-parse retries, so the
    call count below is a genuine maximum rather than an average.
    """
    chunk_count = len(chunk_input_characters)
    draft_prompt_ceiling = sum(
        max(0, int(characters)) + max(0, int(fixed_prompt_overhead_characters))
        for characters in chunk_input_characters
    )
    draft_output_ceiling = chunk_count * max(0, int(extraction_max_output_tokens))
    draft_ceiling = estimate_cost_usd(
        prompt_tokens=draft_prompt_ceiling,
        completion_tokens=draft_output_ceiling,
        model_name=model_name,
    )

    coverage_ceiling = 0.0
    if coverage_enabled:
        coverage_ceiling = estimate_cost_usd(
            prompt_tokens=max(0, int(coverage_max_input_tokens)),
            completion_tokens=max(0, int(coverage_max_output_tokens)),
            model_name=model_name,
        )

    if resolution_enabled and int(resolution_max_targets) <= 0:
        raise ValueError("A positive resolution target cap is required for a bounded cost envelope")
    resolution_calls = max(0, int(resolution_max_targets)) if resolution_enabled else 0
    resolution_ceiling = resolution_calls * estimate_cost_usd(
        prompt_tokens=max(0, int(resolution_max_input_tokens)),
        completion_tokens=max(0, int(resolution_max_output_tokens)),
        model_name=model_name,
    )
    ceiling = float(scoping_actual_cost_usd) + draft_ceiling + coverage_ceiling + resolution_ceiling

    # Central case uses the normal four-characters-per-token approximation and
    # 40% of bounded output.  It is an estimate, explicitly distinct from the
    # no-cache maximum above.
    draft_prompt_central = sum(
        (max(0, int(characters)) + max(0, int(fixed_prompt_overhead_characters))) // 4
        for characters in chunk_input_characters
    )
    draft_output_central = round(draft_output_ceiling * 0.40)
    central = float(scoping_actual_cost_usd) + estimate_cost_usd(
        prompt_tokens=draft_prompt_central,
        completion_tokens=draft_output_central,
        model_name=model_name,
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

    post_scoping_maximum_call_count = chunk_count + int(coverage_enabled) + resolution_calls
    return {
        "policy": "pdf_relation_first_bounded_v1",
        "model": model_name,
        "chunk_count": chunk_count,
        "maximum_call_count": max(0, int(scoping_actual_call_count)) + post_scoping_maximum_call_count,
        "maximum_post_scoping_call_count": post_scoping_maximum_call_count,
        "assumptions": {
            "sdk_retries": 0,
            "manual_retries": 0,
            "draft_parse_retries": 0,
            "cached_input_credit": 0,
            "ceiling_prompt_tokens_per_character": 1,
            "fixed_prompt_overhead_characters_per_chunk": fixed_prompt_overhead_characters,
        },
        "central_estimated_cost_usd": round(central, 6),
        "conservative_max_cost_usd": round(ceiling, 6),
        "by_stage_max_usd": {
            "scoping_already_spent": round(float(scoping_actual_cost_usd), 6),
            "draft": round(draft_ceiling, 6),
            "coverage_completion": round(coverage_ceiling, 6),
            "resolution_completion": round(resolution_ceiling, 6),
        },
    }
