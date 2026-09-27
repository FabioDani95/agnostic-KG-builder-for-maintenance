"""Model prices and the cost estimate of one model response."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Standard USD rates; GPT-6 Luna verified against OpenAI pricing on 2026-09-25.
# Historical campaign artifacts retain their original pricing snapshots.
MODEL_PRICING = {
    "gpt-6-sol": {
        "label": "GPT-6 Sol",
        "input_per_million": 2.00,
        "cached_input_per_million": 0.20,
        "output_per_million": 10.00,
        "cache_write_multiplier": 1.25,
        "long_context_threshold_tokens": 272000,
        "long_context_input_multiplier": 2.0,
        "long_context_output_multiplier": 1.5,
    },
    "gpt-6-luna": {
        "label": "GPT-6 Luna",
        "input_per_million": 0.10,
        "cached_input_per_million": 0.01,
        "output_per_million": 0.50,
        "cache_write_multiplier": 1.25,
        "long_context_threshold_tokens": 272000,
        "long_context_input_multiplier": 2.0,
        "long_context_output_multiplier": 1.5,
    },
    "gpt-5.6-sol": {
        "label": "GPT-5.6 Sol",
        "input_per_million": 4.00,
        "cached_input_per_million": 0.40,
        "output_per_million": 20.00,
        "cache_write_multiplier": 1.25,
        "long_context_threshold_tokens": 272000,
        "long_context_input_multiplier": 2.0,
        "long_context_output_multiplier": 1.5,
    },
    "gpt-5.6-terra": {
        "label": "GPT-5.6 Terra",
        "input_per_million": 2.00,
        "cached_input_per_million": 0.20,
        "output_per_million": 12.00,
        "cache_write_multiplier": 1.25,
        "long_context_threshold_tokens": 272000,
        "long_context_input_multiplier": 2.0,
        "long_context_output_multiplier": 1.5,
    },
    "gpt-5.6-luna": {
        "label": "GPT-5.6 Luna",
        "input_per_million": 0.20,
        "cached_input_per_million": 0.02,
        "output_per_million": 1.20,
        "cache_write_multiplier": 1.25,
        "long_context_threshold_tokens": 272000,
        "long_context_input_multiplier": 2.0,
        "long_context_output_multiplier": 1.5,
    },
    "gpt-5.4": {
        "label": "GPT-5.4",
        "input_per_million": 2.50,
        "cached_input_per_million": 0.25,
        "output_per_million": 15.00,
    },
    "gpt-5.4-mini": {
        "label": "GPT-5.4 Mini",
        "input_per_million": 0.75,
        "cached_input_per_million": 0.075,
        "output_per_million": 4.50,
    },
    "gpt-5.4-nano": {
        "label": "GPT-5.4 Nano",
        "input_per_million": 0.20,
        "cached_input_per_million": 0.02,
        "output_per_million": 1.25,
    },
    "gpt-5.4-pro": {
        "label": "GPT-5.4 Pro",
        "input_per_million": 30.00,
        "cached_input_per_million": None,
        "output_per_million": 180.00,
    },
}

def normalize_model_pricing_key(model_name: str | None) -> str:
    raw = str(model_name or "").strip().lower()
    if raw in {"gpt-5.6", "gpt-5.6-sol"} or raw.startswith("gpt-5.6-sol-"):
        return "gpt-5.6-sol"
    for candidate in (
        "gpt-6-sol",
        "gpt-6-luna",
        "gpt-5.6-terra",
        "gpt-5.6-luna",
        "gpt-5.4-pro",
        "gpt-5.4-mini",
        "gpt-5.4-nano",
        "gpt-5.4",
    ):
        if raw == candidate or raw.startswith(f"{candidate}-"):
            return candidate
    return "gpt-5.6-terra"


def pricing_for_model(model_name: str | None) -> dict[str, Any]:
    key = normalize_model_pricing_key(model_name)
    pricing = deepcopy(MODEL_PRICING[key])
    pricing["model_key"] = key
    return pricing


def estimate_cost_usd(
    prompt_tokens: int,
    completion_tokens: int,
    cached_prompt_tokens: int = 0,
    model_name: str | None = None,
    cache_write_prompt_tokens: int = 0,
) -> float:
    pricing = pricing_for_model(model_name)
    prompt_tokens = max(0, int(prompt_tokens or 0))
    completion_tokens = max(0, int(completion_tokens or 0))
    cached_prompt_tokens = min(
        prompt_tokens,
        max(0, int(cached_prompt_tokens or 0)),
    )
    cache_write_prompt_tokens = min(
        max(0, prompt_tokens - cached_prompt_tokens),
        max(0, int(cache_write_prompt_tokens or 0)),
    )
    cached_input_rate = pricing["cached_input_per_million"]
    # Models without a cached tier fall back to standard input pricing for estimation.
    effective_cached_rate = pricing["input_per_million"] if cached_input_rate is None else cached_input_rate
    ordinary_prompt_tokens = max(
        0,
        prompt_tokens - cached_prompt_tokens - cache_write_prompt_tokens,
    )
    cache_write_rate = pricing["input_per_million"] * float(
        pricing.get("cache_write_multiplier", 1.0) or 1.0
    )
    long_context = prompt_tokens > int(
        pricing.get("long_context_threshold_tokens", 0) or 0
    ) > 0
    input_multiplier = (
        float(pricing.get("long_context_input_multiplier", 1.0) or 1.0)
        if long_context
        else 1.0
    )
    output_multiplier = (
        float(pricing.get("long_context_output_multiplier", 1.0) or 1.0)
        if long_context
        else 1.0
    )
    estimated_cost = (
        (
            (ordinary_prompt_tokens / 1_000_000) * pricing["input_per_million"]
            + (cached_prompt_tokens / 1_000_000) * effective_cached_rate
            + (cache_write_prompt_tokens / 1_000_000) * cache_write_rate
        )
        * input_multiplier
        + (completion_tokens / 1_000_000)
        * pricing["output_per_million"]
        * output_multiplier
    )
    # Keep monetary estimates stable across platforms and exact-comparison
    # call sites while retaining substantially more precision than the ledger.
    return round(estimated_cost, 12)


def usage_from_response(response: Any, operation: str) -> dict[str, Any]:
    usage = getattr(response, "usage", None)
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    total_tokens = int(getattr(usage, "total_tokens", prompt_tokens + completion_tokens) or (prompt_tokens + completion_tokens))
    prompt_details = getattr(usage, "prompt_tokens_details", None)
    cached_prompt_tokens = int(getattr(prompt_details, "cached_tokens", 0) or 0)
    cache_write_prompt_tokens = int(
        getattr(prompt_details, "cache_write_tokens", 0) or 0
    )
    model_name = getattr(response, "model", "") or ""
    pricing = pricing_for_model(model_name)
    return {
        "operation": operation,
        "model": model_name,
        "pricing_model": pricing["model_key"],
        "prompt": prompt_tokens,
        "completion": completion_tokens,
        "total": total_tokens,
        "cached_prompt": cached_prompt_tokens,
        "cache_write_prompt": cache_write_prompt_tokens,
        "non_cached_prompt": max(0, prompt_tokens - cached_prompt_tokens),
        "estimated_cost_usd": round(
            estimate_cost_usd(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cached_prompt_tokens=cached_prompt_tokens,
                model_name=model_name,
                cache_write_prompt_tokens=cache_write_prompt_tokens,
            ),
            6,
        ),
    }
