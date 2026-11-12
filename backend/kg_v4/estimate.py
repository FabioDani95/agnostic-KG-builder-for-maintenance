"""Plan and cost estimate of a run, computed from the read PDF without any model call.

The survey decides which pages are read, so before it runs the estimate is a range: the low
end assumes that a third of the text pages hold troubleshooting knowledge, the high end that
all of them do. Token counts use four characters per token; output sizes come from the share
of input the roles returned in development runs. An estimate is not a spending limit: the
budget ledger enforces the limit.
"""

from __future__ import annotations

from typing import Any

from backend.kg_v3.mapper import scan_batches
from backend.kg_v3.reader import DocumentText, render_segment
from backend.kg_v4.resolve import JUDGE_BATCH, MAX_JUDGED_PAIRS
from backend.services.model_pricing import estimate_cost_usd

CHARS_PER_TOKEN = 4
# Output tokens per input token, by role; reasoning tokens are billed as output.
OUTPUT_SHARE = {"survey": 0.25, "extract": 0.9, "verify": 0.15, "resolve": 0.3, "gap": 0.35, "enrich": 0.45}
PROMPT_TOKENS = {"survey": 900, "extract": 1900, "verify": 500, "resolve": 400, "gap": 500, "enrich": 500}


def estimate(doc: DocumentText, config, *, diagnostic_share: float | None = None) -> dict[str, Any]:
    """Calls, tokens and cost by role; with no share given, a low and a high scenario."""

    if diagnostic_share is None:
        low, high = estimate(doc, config, diagnostic_share=1 / 3), estimate(doc, config, diagnostic_share=1.0)
        return {"model": config.model, "pages": doc.page_count, "text_pages": len(doc.pages),
                "low": low, "high": high,
                "estimated_cost_usd": [low["estimated_cost_usd"], high["estimated_cost_usd"]],
                "note": "estimate from text length; the budget ledger enforces the real limit"}
    text_chars = sum(len(render_segment(segment)) + 1 for segment in doc.segments())
    read_chars = text_chars * diagnostic_share
    units = max(1, round(read_chars / config.unit_max_chars)) if read_chars else 0
    facts = read_chars / 55  # about one fact per 55 characters of troubleshooting text
    roles = {
        "survey": (len(scan_batches(doc)), text_chars / CHARS_PER_TOKEN),
        "extract": (round(units * 1.2), read_chars * 1.25 / CHARS_PER_TOKEN + units * 1200),
        "verify": ((round(units * 1.3) if config.verify else 0), read_chars * 1.5 / CHARS_PER_TOKEN if config.verify else 0),
        "resolve": ((min(MAX_JUDGED_PAIRS, round(facts / 6)) // JUDGE_BATCH + 1) if config.resolve_with_model else 0, 0),
        "gap": (config.gap_max_calls if config.gap_rounds else 0, 0),
        "enrich": (min(config.enrich_max_calls, round(facts / 14) + 1) if config.enrich else 0, 0),
    }
    per_call = {"resolve": 2600, "gap": 3200, "enrich": 3800}
    out: dict[str, Any] = {"units": units, "roles": {}}
    total = 0.0
    for role, (calls, tokens) in roles.items():
        prompt = int(tokens or calls * per_call.get(role, 0)) + calls * PROMPT_TOKENS[role]
        completion = int(prompt * OUTPUT_SHARE[role])
        cost = estimate_cost_usd(prompt, completion, model_name=config.model)
        total += cost
        out["roles"][role] = {"calls": calls, "prompt_tokens": prompt, "completion_tokens": completion,
                              "estimated_cost_usd": round(cost, 4)}
    out["calls"] = sum(item["calls"] for item in out["roles"].values())
    out["estimated_cost_usd"] = round(total, 4)
    return out
