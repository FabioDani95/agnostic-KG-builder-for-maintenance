#!/usr/bin/env python3
"""One-shot v9 runner for the atomic-record second hardening campaign."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
CAMPAIGN_ROOT = Path(__file__).resolve().parent
FROZEN_ROOT = CAMPAIGN_ROOT.parent / "diagnostic_benchmark_20260812"
FROZEN_RUNNER = FROZEN_ROOT / "run_benchmark_once.py"
FROZEN_GOLD = FROZEN_ROOT / "golden.json"
ABSOLUTE_BUDGET_USD = 3.0
PER_RUN_CEILING_USD = 1.10
CAMPAIGN_ID = "pdf-g3-diagnostic-second-hardening-20260813-v9"
RUN_ID_PREFIX = "v9"
RUNNER_PATH = Path(__file__)

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


def _git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=REPOSITORY_ROOT, text=True
    ).strip()


def _code_tree_digest() -> tuple[str, list[str]]:
    """Hash HEAD plus every changed/untracked code/config file, excluding runs."""

    changed = set(filter(None, _git("diff", "--name-only", "HEAD").splitlines()))
    changed.update(
        filter(None, _git("ls-files", "--others", "--exclude-standard").splitlines())
    )
    included = sorted(
        path
        for path in changed
        if path in {"config.yaml", "requirements.txt", "requirements-dev.txt", "pyproject.toml"}
        or path.startswith(("backend/", "tests/", "scripts/"))
    )
    digest = hashlib.sha256()
    digest.update((_git("rev-parse", "HEAD") + "\n").encode())
    for relative in included:
        path = REPOSITORY_ROOT / relative
        digest.update(relative.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes() if path.is_file() else b"<deleted>")
        digest.update(b"\0")
    return digest.hexdigest(), included


def _load_runner() -> ModuleType:
    spec = importlib.util.spec_from_file_location("frozen_diagnostic_runner_v9", FROZEN_RUNNER)
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
            "campaign_id": CAMPAIGN_ID,
            "authorized_budget_usd": ABSOLUTE_BUDGET_USD,
            "per_run_hard_ceiling_usd": PER_RUN_CEILING_USD,
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
    ontology["diagnostic_atomic_table_max_output_tokens"] = 3000
    escalation = ontology["diagnostic_escalation"]
    escalation.update({
        "enabled": True,
        "max_chunks_per_run": 2,
        "reasoning_effort": "medium",
        "max_input_chars": 25000,
        "estimated_max_input_tokens": 8000,
        "schema_overhead_characters": 10000,
        "max_output_tokens": 4000,
    })
    config["pdf_generation_cost_guard"]["hard_ceiling_usd"] = PER_RUN_CEILING_USD
    config_digest = hashlib.sha256(
        json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "ontology_model": config["agents"]["ontology_draft"]["model"],
        "ontology_reasoning_effort": "medium",
        "diagnostic_bundle_max_output_tokens": 6000,
        "diagnostic_atomic_table_max_output_tokens": 3000,
        "terra_selective_recovery_max_windows": 2,
        "terra_reasoning_effort": "medium",
        "process_local_run_hard_ceiling_usd": PER_RUN_CEILING_USD,
        "effective_config_sha256": config_digest,
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
    import fitz

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--manual-id", required=True)
    parser.add_argument("--mode", choices=("mock", "real"), required=True)
    known, _unknown = parser.parse_known_args()
    manual = _manual_spec(known.manual_id)
    run_id = f"{RUN_ID_PREFIX}:{known.manual_id}"
    isolated_root = CAMPAIGN_ROOT / "runs" / known.mode / known.manual_id
    os.environ.update({
        "KG_OPERATIONAL_DB": str((isolated_root / "operational.db").resolve()),
        "KG_RAW_DIR": str((isolated_root / "raw").resolve()),
        "KG_INCOMING_DIR": str((isolated_root / "incoming").resolve()),
    })
    if known.mode == "real":
        os.environ.update({
            "KG_REAL_CALL_BUDGET_LEDGER": str(
                (CAMPAIGN_ROOT / "real_call_budget.jsonl").resolve()
            ),
            "KG_REAL_CALL_BUDGET_USD": f"{ABSOLUTE_BUDGET_USD:.2f}",
            "KG_REAL_CALL_RUN_ID": run_id,
            "KG_REAL_CALL_PDF_ID": f"sha256:{manual['sha256']}",
        })
    from backend.services.pdf_source_subgraph_generation import (
        PDF_SUBGRAPH_GENERATOR_VERSION,
    )

    tree_digest, tree_files = _code_tree_digest()
    profile = _apply_acceptance_profile()
    profile.update({
        "campaign_id": CAMPAIGN_ID,
        "manual_id": known.manual_id,
        "mode": known.mode,
        "git_head_sha": _git("rev-parse", "HEAD"),
        "code_tree_sha256": tree_digest,
        "code_tree_files": tree_files,
        "pipeline_version": PDF_SUBGRAPH_GENERATOR_VERSION,
        "pymupdf_version": str(fitz.VersionBind),
        "campaign_runner_sha256": hashlib.sha256(RUNNER_PATH.read_bytes()).hexdigest(),
        "golden_sha256": hashlib.sha256(FROZEN_GOLD.read_bytes()).hexdigest(),
        "golden_usage": "post_generation_evaluation_only",
        "absolute_real_budget_usd": ABSOLUTE_BUDGET_USD,
        "durable_per_call_guard": known.mode == "real",
    })
    _write_runtime_profile(known.manual_id, known.mode, profile)
    return int(_load_runner().main())


if __name__ == "__main__":
    raise SystemExit(main())
