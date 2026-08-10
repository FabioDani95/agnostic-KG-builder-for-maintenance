#!/usr/bin/env python3
"""Transparent cost sensitivity model based on the measured Luna run.

No API is called.  The recommended-pipeline scenarios scale only the measured
ontology-stage usage and then add an explicit optional Terra adjudication batch.
They are engineering estimates, not measurements or provider invoices.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PRICING = {
    "gpt-5.6-luna": {"input": 0.20, "cached_input": 0.02, "output": 1.20},
    "gpt-5.6-terra": {"input": 2.00, "cached_input": 0.20, "output": 12.00},
}


def cost(model: str, prompt: int, cached: int, output: int) -> float:
    rates = PRICING[model]
    uncached = max(0, prompt - cached)
    return (
        uncached * rates["input"]
        + cached * rates["cached_input"]
        + output * rates["output"]
    ) / 1_000_000


def scaled(value: int | float, factor: float) -> int:
    return round(float(value) * factor)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("artifacts/acceptance/g3/e554/luna_validation/result.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    validation = json.loads(args.baseline.read_text(encoding="utf-8"))
    measured = validation["generation_metrics"]
    scoping = measured["stages"]["scoping"]
    ontology = measured["stages"]["ontology"]
    reconstructed = cost(
        "gpt-5.6-luna",
        measured["prompt_tokens"],
        measured["cached_prompt_tokens"],
        measured["completion_tokens"],
    )
    # Persisted cost is summed from per-call values rounded to six decimals;
    # recomputing once from aggregate tokens may differ by a few micro-dollars.
    assert abs(reconstructed - float(measured["estimated_cost_usd"])) < 0.00001

    scenario_inputs = [
        {
            "name": "low_no_escalation",
            "ontology_usage_factor_vs_measured": 0.40,
            "estimated_calls": 21,
            "terra_prompt_tokens": 0,
            "terra_cached_prompt_tokens": 0,
            "terra_output_tokens": 0,
            "terra_latency_allowance_seconds": 0,
        },
        {
            "name": "central_one_batched_escalation",
            "ontology_usage_factor_vs_measured": 0.55,
            "estimated_calls": 25,
            "terra_prompt_tokens": 12_000,
            "terra_cached_prompt_tokens": 0,
            "terra_output_tokens": 2_000,
            "terra_latency_allowance_seconds": 30,
        },
        {
            "name": "conservative_one_larger_escalation",
            "ontology_usage_factor_vs_measured": 0.70,
            "estimated_calls": 28,
            "terra_prompt_tokens": 20_000,
            "terra_cached_prompt_tokens": 0,
            "terra_output_tokens": 3_000,
            "terra_latency_allowance_seconds": 45,
        },
    ]

    scenarios: list[dict[str, Any]] = []
    for item in scenario_inputs:
        factor = item["ontology_usage_factor_vs_measured"]
        luna_prompt = int(scoping["prompt_tokens"]) + scaled(ontology["prompt_tokens"], factor)
        luna_cached = int(scoping["cached_prompt_tokens"]) + scaled(
            ontology["cached_prompt_tokens"], factor
        )
        luna_output = int(scoping["completion_tokens"]) + scaled(
            ontology["completion_tokens"], factor
        )
        luna_cost = cost("gpt-5.6-luna", luna_prompt, luna_cached, luna_output)
        terra_cost = cost(
            "gpt-5.6-terra",
            item["terra_prompt_tokens"],
            item["terra_cached_prompt_tokens"],
            item["terra_output_tokens"],
        )
        duration = (
            float(scoping["duration_seconds"])
            + float(ontology["duration_seconds"]) * factor
            + item["terra_latency_allowance_seconds"]
        )
        scenarios.append({
            **item,
            "measurement_status": "estimated_sensitivity_from_measured_stage_usage",
            "luna_usage": {
                "prompt_tokens": luna_prompt,
                "cached_prompt_tokens": luna_cached,
                "completion_tokens": luna_output,
                "total_tokens": luna_prompt + luna_output,
                "estimated_cost_usd": round(luna_cost, 6),
            },
            "terra_usage": {
                "prompt_tokens": item["terra_prompt_tokens"],
                "cached_prompt_tokens": item["terra_cached_prompt_tokens"],
                "completion_tokens": item["terra_output_tokens"],
                "total_tokens": item["terra_prompt_tokens"] + item["terra_output_tokens"],
                "estimated_cost_usd": round(terra_cost, 6),
            },
            "estimated_total_tokens": (
                luna_prompt + luna_output
                + item["terra_prompt_tokens"] + item["terra_output_tokens"]
            ),
            "estimated_total_cost_usd": round(luna_cost + terra_cost, 6),
            "estimated_duration_seconds": round(duration, 3),
        })

    payload = {
        "analysis_kind": "offline_cost_sensitivity",
        "pricing_usd_per_million_tokens": PRICING,
        "baseline": {
            "measurement_status": "measured_persisted_luna_run",
            "llm_calls": measured["llm_calls"],
            "prompt_tokens": measured["prompt_tokens"],
            "cached_prompt_tokens": measured["cached_prompt_tokens"],
            "completion_tokens": measured["completion_tokens"],
            "total_tokens": measured["total_tokens"],
            "duration_seconds": measured["duration_seconds"],
            "estimated_cost_usd": measured["estimated_cost_usd"],
            "aggregate_token_reconstruction_usd": round(reconstructed, 6),
        },
        "assumptions": [
            "Scoping usage is held at the exact measured Luna value.",
            "The relation-first contract removes the separate relation pass and routine per-chunk semantic-validator/re-extraction passes; the remaining ontology usage is represented as 40%, 55%, or 70% of measured ontology-stage tokens and duration.",
            "The structural component pass is included in those ontology factors.",
            "Terra is optional and limited to one batched ambiguity adjudication; it may not create a claim without a quote and resolvable anchor.",
            "Operation-level token buckets were not persisted, so factors cannot be measured before implementation. These scenarios are sensitivity bounds, not claimed outcomes.",
        ],
        "recommended_budget_policy": {
            "expected_scenario": "central_one_batched_escalation",
            "expected_cost_usd": next(
                item["estimated_total_cost_usd"]
                for item in scenarios
                if item["name"] == "central_one_batched_escalation"
            ),
            "expected_range_usd": [
                scenarios[0]["estimated_total_cost_usd"],
                scenarios[-1]["estimated_total_cost_usd"],
            ],
            "preflight_stop_usd": 0.35,
            "rule": "Skip optional escalation before a call when its conservative token ceiling would make the run forecast exceed $0.35; preserve the unresolved item as a gap.",
        },
        "scenarios": scenarios,
    }
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)


if __name__ == "__main__":
    main()
