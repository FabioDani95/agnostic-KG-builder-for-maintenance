#!/usr/bin/env python3
"""One-shot wrapper for the v8 record-window hardening campaign.

It reuses the frozen route-level runner without modifying the prior campaign,
applies a process-local Luna/Terra acceptance profile, and enables the durable
campaign-wide per-call $1.00 guard before any real API invocation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CAMPAIGN_ROOT = Path(__file__).resolve().parent
FROZEN_ROOT = CAMPAIGN_ROOT.parent / "diagnostic_benchmark_20260812"
FROZEN_RUNNER = FROZEN_ROOT / "run_benchmark_once.py"
FROZEN_GOLD = FROZEN_ROOT / "golden.json"
ABSOLUTE_BUDGET_USD = 1.0

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("frozen_diagnostic_runner", FROZEN_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load the frozen benchmark runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.CAMPAIGN_ROOT = CAMPAIGN_ROOT
    module.GOLD_PATH = FROZEN_GOLD
    original_load_gold = module._load_gold

    def load_gold(manual_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        campaign, manual = original_load_gold(manual_id)
        campaign = dict(campaign)
        campaign.update({
            "campaign_id": "pdf-g3-diagnostic-hardening-20260812-v8",
            "authorized_budget_usd": ABSOLUTE_BUDGET_USD,
            "per_run_hard_ceiling_usd": 0.60,
        })
        return campaign, manual

    module._load_gold = load_gold
    return module


def _manual_spec(manual_id: str) -> dict[str, Any]:
    campaign = json.loads(FROZEN_GOLD.read_text(encoding="utf-8"))
    return next(item for item in campaign["manuals"] if item["manual_id"] == manual_id)


def _apply_acceptance_profile() -> dict[str, Any]:
    from backend.app_config import load_config

    config = load_config()
    config["agents"]["ontology_draft"]["reasoning_effort"] = "medium"
    ontology = config["ontology"]
    ontology["diagnostic_bundle_max_output_tokens"] = 6000
    escalation = ontology["diagnostic_escalation"]
    escalation.update({
        "enabled": True,
        "max_chunks_per_run": 1,
        "reasoning_effort": "medium",
        "max_input_chars": 25000,
        "estimated_max_input_tokens": 8000,
        "schema_overhead_characters": 10000,
        "max_output_tokens": 4000,
    })
    config["pdf_generation_cost_guard"]["hard_ceiling_usd"] = 0.60
    # The checked-in production values are never edited; this mutable cached
    # overlay dies with the isolated one-shot process.
    return {
        "ontology_model": config["agents"]["ontology_draft"]["model"],
        "ontology_reasoning_effort": "medium",
        "diagnostic_bundle_max_output_tokens": 6000,
        "terra_selective_recovery_max_windows": 1,
        "terra_reasoning_effort": "medium",
        "process_local_run_hard_ceiling_usd": 0.60,
        "config_restoration": "process_exit",
    }


def _write_runtime_profile(manual_id: str, mode: str, profile: dict[str, Any]) -> None:
    path = CAMPAIGN_ROOT / "runs" / mode / manual_id / "runtime_profile.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--manual-id", required=True)
    parser.add_argument("--mode", choices=("mock", "real"), required=True)
    known, _unknown = parser.parse_known_args()
    manual = _manual_spec(known.manual_id)
    run_id = f"v8:{known.manual_id}"
    if known.mode == "real":
        os.environ.update({
            "KG_REAL_CALL_BUDGET_LEDGER": str(
                (CAMPAIGN_ROOT / "real_call_budget.jsonl").resolve()
            ),
            "KG_REAL_CALL_BUDGET_USD": f"{ABSOLUTE_BUDGET_USD:.2f}",
            "KG_REAL_CALL_RUN_ID": run_id,
            "KG_REAL_CALL_PDF_ID": f"sha256:{manual['sha256']}",
        })
    profile = _apply_acceptance_profile()
    profile.update({
        "manual_id": known.manual_id,
        "mode": known.mode,
        "absolute_real_budget_usd": ABSOLUTE_BUDGET_USD,
        "durable_per_call_guard": known.mode == "real",
    })
    _write_runtime_profile(known.manual_id, known.mode, profile)
    runner = _load_runner()
    return int(runner.main())


if __name__ == "__main__":
    raise SystemExit(main())
