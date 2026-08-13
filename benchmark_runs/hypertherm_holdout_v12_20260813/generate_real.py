#!/usr/bin/env python3
"""One-shot v12 Hypertherm graph run under the cumulative USD 2.00 guard."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = Path(__file__).resolve().parent
BUDGET_USD = 3.00
RUN_ID = "hypertherm-holdout-real-v12-recovery"
PDF_SHA256 = "3c2b7cd62ae1b8b69f8b86fcbf9b36f4ee1fc8d35fed3f90d6271f8ef50d5c45"
SHARED_LEDGER = (
    REPOSITORY_ROOT
    / "benchmark_runs"
    / "hypertherm_holdout_20260813"
    / "real_call_budget.jsonl"
)


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=REPOSITORY_ROOT, text=True
    ).strip()


def apply_run_profile() -> dict[str, Any]:
    from backend.app_config import load_config
    from backend.services.pdf_source_subgraph_generation import (
        PDF_SUBGRAPH_GENERATOR_VERSION,
    )

    config = load_config()
    config["agents"]["ontology_draft"]["reasoning_effort"] = "medium"
    ontology = config["ontology"]
    # Structural chunks contain at most 12 pages and do not need the legacy
    # 16k completion envelope.  This keeps the conservative whole-run reserve
    # inside the remaining cumulative authorization without reducing input.
    ontology["extraction_max_output_tokens"] = 8000
    ontology["diagnostic_bundle_max_output_tokens"] = 8000
    ontology["diagnostic_atomic_table_max_output_tokens"] = 3000
    ontology["diagnostic_max_pages_per_chunk"] = 4
    escalation = ontology["diagnostic_escalation"]
    escalation.update(
        {
            "enabled": True,
            "primary_model": "gpt-5.6-luna",
            "model": "gpt-5.6-terra",
            "max_chunks_per_run": 4,
            "reasoning_effort": "medium",
            "max_input_chars": 60000,
            "estimated_max_input_tokens": 15000,
            "schema_overhead_characters": 10000,
            "max_output_tokens": 16000,
        }
    )
    config["pdf_generation_cost_guard"]["preferred_cost_usd"] = 2.75
    config["pdf_generation_cost_guard"]["hard_ceiling_usd"] = 2.75
    digest = hashlib.sha256(
        json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "pipeline": PDF_SUBGRAPH_GENERATOR_VERSION,
        "git_head": git("rev-parse", "HEAD"),
        "working_tree_diff_sha256": hashlib.sha256(
            subprocess.check_output(
                ["git", "diff", "--binary"], cwd=REPOSITORY_ROOT
            )
        ).hexdigest(),
        "llm_mode": "real",
        "absolute_budget_usd": BUDGET_USD,
        "ontology_model": config["agents"]["ontology_draft"]["model"],
        "ontology_reasoning_effort": "medium",
        "terra_enabled": True,
        "terra_model": "gpt-5.6-terra",
        "terra_reasoning_effort": "medium",
        "terra_max_chunks_per_run": 4,
        "shared_budget_ledger": str(SHARED_LEDGER.resolve()),
        "effective_config_sha256": digest,
        "golden_usage": "absent",
        "config_restoration": "process_exit",
    }


async def run() -> int:
    os.environ.update(
        {
            "KG_LLM_MODE": "real",
            "KG_OPERATIONAL_DB": str((RUN_ROOT / "operational.db").resolve()),
            "KG_RAW_DIR": str((RUN_ROOT / "raw").resolve()),
            "KG_INCOMING_DIR": str((RUN_ROOT / "incoming").resolve()),
            "KG_REAL_CALL_BUDGET_LEDGER": str(SHARED_LEDGER.resolve()),
            "KG_REAL_CALL_BUDGET_USD": f"{BUDGET_USD:.2f}",
            "KG_REAL_CALL_RUN_ID": RUN_ID,
            "KG_REAL_CALL_PDF_ID": f"sha256:{PDF_SHA256}",
        }
    )
    if str(REPOSITORY_ROOT) not in sys.path:
        sys.path.insert(0, str(REPOSITORY_ROOT))

    from backend.config import settings
    from backend.services.real_call_budget_ledger import RealCallBudgetLedger
    from backend.services.source_subgraph_generation import SourceSubgraphGenerationService

    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is unavailable")
    state_path = RUN_ROOT / "real_run_state_recovery.json"
    if state_path.exists():
        raise RuntimeError("The one-shot real Hypertherm recovery already started")

    prepared = json.loads((RUN_ROOT / "preparation.json").read_text(encoding="utf-8"))
    if prepared["pdf"]["sha256"] != PDF_SHA256:
        raise RuntimeError("Prepared PDF hash does not match the authorized Hypertherm bytes")
    workspace_id = prepared["workspace"]["workspace_id"]
    source_id = prepared["source"]["source_id"]
    profile = apply_run_profile()
    write_json(RUN_ROOT / "real_runtime_profile.json", profile)

    state: dict[str, Any] = {
        "run_id": RUN_ID,
        "workspace_id": workspace_id,
        "source_id": source_id,
        "pdf_sha256": PDF_SHA256,
        "generation_started": True,
        "status": "generating",
        "absolute_budget_usd": BUDGET_USD,
        "golden_loaded": False,
        "approval_decision_taken": False,
        "merge_started": False,
        "structured_source_processed": False,
    }
    write_json(state_path, state)

    started = time.perf_counter()
    try:
        view = await SourceSubgraphGenerationService().generate(workspace_id, source_id)
        payload = view.model_dump(mode="json")
        write_json(RUN_ROOT / "generation_response_recovery.json", payload)
        matching = [
            item.get("subgraph")
            for item in payload.get("sources", [])
            if item.get("source_id") == source_id and item.get("subgraph") is not None
        ]
        if len(matching) != 1:
            raise RuntimeError(f"Expected one Hypertherm subgraph, found {len(matching)}")
        graph = matching[0]
        write_json(RUN_ROOT / "hypertherm_graph_v12_recovery.json", graph)
        metrics = graph.get("generation_metrics") or {}
        ledger = RealCallBudgetLedger(
            SHARED_LEDGER,
            absolute_budget_usd=f"{BUDGET_USD:.2f}",
        ).snapshot().as_dict()
        state.update(
            {
                "status": "completed",
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "revision_id": graph.get("source_subgraph_revision_id"),
                "revision_status": graph.get("status"),
                "approval_eligible": graph.get("approval_eligible"),
                "node_count": len(graph.get("nodes") or []),
                "relation_count": len(graph.get("relations") or []),
                "review_item_count": len(graph.get("review_queue") or []),
                "knowledge_gap_count": len(graph.get("knowledge_gaps") or []),
                "actual_spend_usd": metrics.get("estimated_cost_usd", 0),
                "llm_calls": metrics.get("llm_calls", 0),
                "ledger": ledger,
                "graph_json": str(
                    (RUN_ROOT / "hypertherm_graph_v12_recovery.json").resolve()
                ),
            }
        )
        write_json(state_path, state)
        print(json.dumps(state, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        ledger_path = SHARED_LEDGER
        ledger = None
        if ledger_path.exists():
            ledger = RealCallBudgetLedger(
                ledger_path,
                absolute_budget_usd=f"{BUDGET_USD:.2f}",
            ).snapshot().as_dict()
        state.update(
            {
                "status": "stopped_without_retry",
                "elapsed_seconds": round(time.perf_counter() - started, 3),
                "error": {"type": type(exc).__name__, "message": str(exc)},
                "ledger": ledger,
            }
        )
        write_json(state_path, state)
        raise


def main() -> int:
    return asyncio.run(run())


if __name__ == "__main__":
    raise SystemExit(main())
