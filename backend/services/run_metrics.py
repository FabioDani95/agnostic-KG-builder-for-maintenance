from __future__ import annotations

from copy import deepcopy
from time import perf_counter
from typing import Any

from backend.observability.trace import compact_digest, compact_summary
from backend.runstore import append_trace_step


MODEL_PRICING = {
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

AGENT_STAGE_MAP = {
    "scoping": "scoping_agent",
    "ontology": "ontology_draft_agent",
    "extraction": "extraction_agent",
    "validation": "validation_agent",
    "coverage": "coverage_agent",
    "grounding": "grounding_agent",
    "conflict_resolution": "conflict_resolution_agent",
    "refinement": "refiner_agent",
    "export": "export",
}


def now_perf() -> float:
    return perf_counter()


def normalize_model_pricing_key(model_name: str | None) -> str:
    raw = str(model_name or "").strip().lower()
    for candidate in ("gpt-5.4-pro", "gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.4"):
        if raw == candidate or raw.startswith(f"{candidate}-"):
            return candidate
    return "gpt-5.4"


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
) -> float:
    pricing = pricing_for_model(model_name)
    cached_prompt_tokens = max(0, int(cached_prompt_tokens or 0))
    prompt_tokens = max(0, int(prompt_tokens or 0))
    completion_tokens = max(0, int(completion_tokens or 0))
    cached_input_rate = pricing["cached_input_per_million"]
    # Models without a cached tier fall back to standard input pricing for estimation.
    effective_cached_rate = pricing["input_per_million"] if cached_input_rate is None else cached_input_rate
    non_cached_prompt_tokens = max(0, prompt_tokens - cached_prompt_tokens)
    return (
        (non_cached_prompt_tokens / 1_000_000) * pricing["input_per_million"]
        + (cached_prompt_tokens / 1_000_000) * effective_cached_rate
        + (completion_tokens / 1_000_000) * pricing["output_per_million"]
    )


def usage_from_response(response: Any, operation: str) -> dict[str, Any]:
    usage = getattr(response, "usage", None)
    prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
    completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
    total_tokens = int(getattr(usage, "total_tokens", prompt_tokens + completion_tokens) or (prompt_tokens + completion_tokens))
    prompt_details = getattr(usage, "prompt_tokens_details", None)
    cached_prompt_tokens = int(getattr(prompt_details, "cached_tokens", 0) or 0)
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
        "non_cached_prompt": max(0, prompt_tokens - cached_prompt_tokens),
        "estimated_cost_usd": round(
            estimate_cost_usd(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                cached_prompt_tokens=cached_prompt_tokens,
                model_name=model_name,
            ),
            6,
        ),
    }


def aggregate_usage(entries: list[dict[str, Any]] | None) -> dict[str, Any]:
    items = entries or []
    prompt_tokens = sum(int(item.get("prompt", 0) or 0) for item in items)
    completion_tokens = sum(int(item.get("completion", 0) or 0) for item in items)
    cached_prompt_tokens = sum(int(item.get("cached_prompt", 0) or 0) for item in items)
    total_tokens = sum(int(item.get("total", 0) or 0) for item in items)
    models = sorted({str(item.get("model", "") or "") for item in items if item.get("model")})
    pricing_models = sorted({str(item.get("pricing_model", "") or "") for item in items if item.get("pricing_model")})
    operations = sorted({str(item.get("operation", "") or "") for item in items if item.get("operation")})
    by_model: dict[str, dict[str, Any]] = {}
    for item in items:
        pricing_model = str(item.get("pricing_model", "") or "")
        if not pricing_model:
            continue
        bucket = by_model.setdefault(pricing_model, {
            "label": pricing_for_model(pricing_model)["label"],
            "llm_calls": 0,
            "prompt_tokens": 0,
            "cached_prompt_tokens": 0,
            "non_cached_prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost_usd": 0.0,
        })
        bucket["llm_calls"] += 1
        bucket["prompt_tokens"] += int(item.get("prompt", 0) or 0)
        bucket["cached_prompt_tokens"] += int(item.get("cached_prompt", 0) or 0)
        bucket["non_cached_prompt_tokens"] += int(item.get("non_cached_prompt", 0) or 0)
        bucket["completion_tokens"] += int(item.get("completion", 0) or 0)
        bucket["total_tokens"] += int(item.get("total", 0) or 0)
        bucket["estimated_cost_usd"] = round(
            float(bucket["estimated_cost_usd"]) + float(item.get("estimated_cost_usd", 0) or 0),
            6,
        )

    return {
        "llm_calls": len(items),
        "prompt_tokens": prompt_tokens,
        "cached_prompt_tokens": cached_prompt_tokens,
        "non_cached_prompt_tokens": max(0, prompt_tokens - cached_prompt_tokens),
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": round(sum(float(item.get("estimated_cost_usd", 0) or 0) for item in items), 6),
        "models": models,
        "pricing_models": pricing_models,
        "operations": operations,
        "by_model": by_model,
    }


def summarize_stage(
    stage: str,
    started_at: float,
    usage_entries: list[dict[str, Any]] | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = aggregate_usage(usage_entries)
    summary.update({
        "stage": stage,
        "duration_seconds": round(max(0.0, perf_counter() - started_at), 3),
        "details": details or {},
    })
    return summary


def ensure_run_metrics(store: dict[str, Any]) -> dict[str, Any]:
    metrics = store.setdefault("run_metrics", {})
    metrics.setdefault("pricing_basis", {
        "label": "Estimated using configured model pricing",
        "models": deepcopy(MODEL_PRICING),
    })
    metrics.setdefault("stages", {})
    return metrics


def record_stage_metrics(store: dict[str, Any], stage: str, summary: dict[str, Any]) -> None:
    metrics = ensure_run_metrics(store)
    metrics["stages"][stage] = summary
    pdf_id = str(store.get("pdf_id") or (store.get("graph_state") or {}).get("pdf_id") or "")
    if pdf_id:
        details = summary.get("details") or {}
        append_trace_step(pdf_id, {
            "step": f"{stage}_metrics",
            "phase": stage,
            "agent": AGENT_STAGE_MAP.get(stage, stage),
            "input_digest": compact_digest(details),
            "output_summary": {
                "duration_seconds": summary.get("duration_seconds"),
                "llm_calls": summary.get("llm_calls", 0),
                "operations": compact_summary(summary.get("operations", [])),
                "details": compact_summary(details),
            },
            "decision": "recorded stage metrics",
            "human_handoff": int(details.get("human_required_count", 0) or details.get("needs_human", 0) or 0) > 0,
            "retry_count": int(details.get("retry_count", 0) or 0),
            "tokens": int(summary.get("total_tokens", 0) or 0),
            "cost": float(summary.get("estimated_cost_usd", 0.0) or 0.0),
        })


def build_metrics_payload(store: dict[str, Any]) -> dict[str, Any]:
    metrics = ensure_run_metrics(store)
    stages = metrics.get("stages", {})
    totals_by_model: dict[str, dict[str, Any]] = {}
    for stage in stages.values():
        for model_key, model_data in (stage.get("by_model", {}) or {}).items():
            bucket = totals_by_model.setdefault(model_key, {
                "label": pricing_for_model(model_key)["label"],
                "llm_calls": 0,
                "prompt_tokens": 0,
                "cached_prompt_tokens": 0,
                "non_cached_prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0,
            })
            for field in ("llm_calls", "prompt_tokens", "cached_prompt_tokens", "non_cached_prompt_tokens", "completion_tokens", "total_tokens"):
                bucket[field] += int(model_data.get(field, 0) or 0)
            bucket["estimated_cost_usd"] = round(
                float(bucket["estimated_cost_usd"]) + float(model_data.get("estimated_cost_usd", 0) or 0),
                6,
            )

    totals = {
        "duration_seconds": round(sum(float(stage.get("duration_seconds", 0) or 0) for stage in stages.values()), 3),
        "llm_calls": sum(int(stage.get("llm_calls", 0) or 0) for stage in stages.values()),
        "prompt_tokens": sum(int(stage.get("prompt_tokens", 0) or 0) for stage in stages.values()),
        "cached_prompt_tokens": sum(int(stage.get("cached_prompt_tokens", 0) or 0) for stage in stages.values()),
        "non_cached_prompt_tokens": sum(int(stage.get("non_cached_prompt_tokens", 0) or 0) for stage in stages.values()),
        "completion_tokens": sum(int(stage.get("completion_tokens", 0) or 0) for stage in stages.values()),
        "total_tokens": sum(int(stage.get("total_tokens", 0) or 0) for stage in stages.values()),
        "estimated_cost_usd": round(sum(float(stage.get("estimated_cost_usd", 0) or 0) for stage in stages.values()), 6),
        "by_model": totals_by_model,
    }

    scoping = stages.get("scoping", {})
    extraction = stages.get("extraction", {})
    selected_pages = int(
        extraction.get("details", {}).get("selected_pages")
        or scoping.get("details", {}).get("selected_pages")
        or 0
    )
    total_pages = int(scoping.get("details", {}).get("total_pages") or store.get("page_count") or len(store.get("pages", [])) or 0)
    extracted_triplets = int(extraction.get("details", {}).get("triplet_count") or 0)
    validated_triplets = len(store.get("validated_triplets") or [])
    discarded_triplets = max(0, extracted_triplets - validated_triplets)

    # Node count by type from the stored ontology pipeline state
    ontology_pipeline = store.get("ontology_pipeline") or {}
    ontology_snapshot = ontology_pipeline.get("ontology") or {}
    ontology_nodes = ontology_snapshot.get("nodes") or {}
    nodes_by_type = {
        node_type: len(node_list)
        for node_type, node_list in ontology_nodes.items()
        if isinstance(node_list, list) and node_list
    }

    from backend.services.ontology_coverage import compute_graph_coverage

    graph_coverage = compute_graph_coverage(ontology_snapshot)
    resolution_completion = (
        ontology_pipeline.get("resolution_completion_report")
        or (stages.get("ontology", {}).get("details", {}) or {}).get("resolution_completion")
        or {}
    )

    return {
        "document": {
            "filename": store.get("filename", ""),
            "total_pages": total_pages,
            "selected_pages": selected_pages,
        },
        "pricing_basis": metrics.get("pricing_basis", {}),
        "pricing_catalog": deepcopy(MODEL_PRICING),
        "stages": stages,
        "agent_token_ledger": project_agent_token_ledger(store),
        "totals": totals,
        "nodes_by_type": nodes_by_type,
        "graph_coverage": graph_coverage,
        "resolution_completion": resolution_completion,
        "review": {
            "validated_triplets": validated_triplets,
            "discarded_triplets": discarded_triplets,
            "extracted_triplets": extracted_triplets,
        },
        "derived_kpis": {
            "pages_kept_ratio": round((selected_pages / total_pages), 4) if total_pages else 0.0,
            "seconds_per_selected_page": round((totals["duration_seconds"] / selected_pages), 3) if selected_pages else 0.0,
            "cost_per_selected_page_usd": round((totals["estimated_cost_usd"] / selected_pages), 6) if selected_pages else 0.0,
            "cost_per_extracted_triplet_usd": round((totals["estimated_cost_usd"] / extracted_triplets), 6) if extracted_triplets else 0.0,
        },
    }


def project_agent_token_ledger(store: dict[str, Any]) -> dict[str, Any]:
    """Project existing stage metrics into a Phase 1 per-agent token ledger."""
    metrics = ensure_run_metrics(store)
    stages = metrics.get("stages", {})
    ledger: dict[str, dict[str, Any]] = {}
    for stage_name, stage_data in stages.items():
        agent_name = AGENT_STAGE_MAP.get(stage_name)
        if not agent_name:
            continue
        ledger[agent_name] = {
            "calls": int(stage_data.get("llm_calls", 0) or 0),
            "prompt_tokens": int(stage_data.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(stage_data.get("completion_tokens", 0) or 0),
            "cached_tokens": int(stage_data.get("cached_prompt_tokens", 0) or 0),
            "total_tokens": int(stage_data.get("total_tokens", 0) or 0),
            "estimated_cost": round(float(stage_data.get("estimated_cost_usd", 0) or 0), 6),
            "models": list(stage_data.get("models", []) or []),
            "stage": stage_name,
        }
    return ledger
