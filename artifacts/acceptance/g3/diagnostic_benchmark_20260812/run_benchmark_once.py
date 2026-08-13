#!/usr/bin/env python3
"""Run one isolated PDF G3 benchmark generation exactly once.

The script exercises the application routes for workspace creation, PDF upload,
automatic preparation and G3 source-subgraph generation. It never approves,
rejects, merges or processes structured sources.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from io import BytesIO
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.app_config import get_pdf_generation_cost_guard_config  # noqa: E402
from backend.config import settings  # noqa: E402
from backend.main import create_app  # noqa: E402
from backend.services.llm_gateway import llm_mode  # noqa: E402

CAMPAIGN_ROOT = Path(__file__).resolve().parent
GOLD_PATH = CAMPAIGN_ROOT / "golden.json"
MANUAL_ROOT = REPOSITORY_ROOT / "output" / "pdf" / "diagnostic_benchmark_manuals"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _load_gold(manual_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    campaign = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    for manual in campaign["manuals"]:
        if manual["manual_id"] == manual_id:
            return campaign, manual
    raise ValueError(f"Unknown manual_id: {manual_id}")


def _revision(payload: dict[str, Any] | None, source_id: str) -> dict[str, Any] | None:
    for item in (payload or {}).get("sources") or []:
        if item.get("source_id") == source_id:
            return item.get("subgraph")
    return None


def _call_ledger(revision: dict[str, Any]) -> list[dict[str, Any]]:
    stages = ((revision.get("generation_metrics") or {}).get("stages") or {})
    calls: list[dict[str, Any]] = []
    for stage_name, stage in stages.items():
        for item in (stage.get("details") or {}).get("call_ledger") or []:
            calls.append({**item, "stage": stage_name, "global_call_index": len(calls) + 1})
    return calls


def _prior_real_spend(exclude_manual_id: str) -> float:
    total = 0.0
    real_root = CAMPAIGN_ROOT / "runs" / "real"
    if not real_root.exists():
        return total
    for ledger_path in real_root.glob("*/real_api_ledger.json"):
        if ledger_path.parent.name == exclude_manual_id:
            continue
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        total += float(ledger.get("actual_spend_usd", 0) or 0)
    return round(total, 6)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manual-id", required=True)
    parser.add_argument("--mode", choices=("mock", "real"), required=True)
    args = parser.parse_args()

    campaign, manual = _load_gold(args.manual_id)
    run_root = CAMPAIGN_ROOT / "runs" / args.mode / args.manual_id
    state_path = run_root / "run_state.json"
    response_path = run_root / "generation_response.json"
    ledger_path = run_root / "real_api_ledger.json"

    if state_path.exists():
        old_state = json.loads(state_path.read_text(encoding="utf-8"))
        if old_state.get("generation_started"):
            raise RuntimeError(f"The {args.mode} one-shot run already started for {args.manual_id}")
    if llm_mode() != args.mode:
        raise RuntimeError(f"KG_LLM_MODE must be {args.mode}; got {llm_mode()}")
    if args.mode == "real" and not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is unavailable")
    required_env = ("KG_OPERATIONAL_DB", "KG_RAW_DIR", "KG_INCOMING_DIR")
    missing_env = [name for name in required_env if not os.environ.get(name)]
    if missing_env:
        raise RuntimeError(f"Missing isolated-store environment: {', '.join(missing_env)}")

    manual_path = MANUAL_ROOT / manual["file_name"]
    pdf_bytes = manual_path.read_bytes()
    actual_sha = hashlib.sha256(pdf_bytes).hexdigest()
    if actual_sha != manual["sha256"]:
        raise RuntimeError(f"Frozen manual hash mismatch: {actual_sha}")

    guard = get_pdf_generation_cost_guard_config()
    hard_ceiling = float(guard.get("hard_ceiling_usd", 0) or 0)
    prior_spend = _prior_real_spend(args.manual_id) if args.mode == "real" else 0.0
    authorized = float(campaign["authorized_budget_usd"])
    if args.mode == "real":
        if hard_ceiling > float(campaign["per_run_hard_ceiling_usd"]):
            raise RuntimeError("Configured PDF ceiling exceeds the frozen per-run authorization")
        if prior_spend + hard_ceiling > authorized:
            raise RuntimeError("Cumulative real-call envelope exceeds the campaign budget")

    run_root.mkdir(parents=True, exist_ok=True)
    state: dict[str, Any] = {
        "manual_id": args.manual_id,
        "manual_sha256": actual_sha,
        "mode": args.mode,
        "generation_started": False,
        "authorized_campaign_budget_usd": authorized,
        "prior_measured_spend_usd": prior_spend,
        "run_hard_ceiling_usd": hard_ceiling,
        "api_key_present": bool(settings.OPENAI_API_KEY) if args.mode == "real" else False,
        "api_key_exposed": False,
        "approval_decision_taken": False,
        "merge_started": False,
        "structured_source_processed": False,
        "operational_db": os.environ["KG_OPERATIONAL_DB"],
        "raw_store": os.environ["KG_RAW_DIR"],
        "status": "initializing",
    }
    _write_json(state_path, state)

    client = TestClient(create_app())
    asset = manual["asset"]
    workspace_response = client.post(
        "/api/workspaces",
        json={
            "asset": asset,
            "identifiers": [],
            "assertion": {
                "reason": "Identity transcribed from the frozen benchmark manual before generation.",
                "observation_basis": "operator_record",
                "operator": "Codex PDF G3 diagnostic benchmark",
            },
        },
    )
    workspace_response.raise_for_status()
    workspace = workspace_response.json()["workspace"]
    workspace_id = workspace["workspace_id"]

    upload_response = client.post(
        f"/api/workspaces/{workspace_id}/sources",
        data={"authority": "normative"},
        files={"file": (manual["file_name"], BytesIO(pdf_bytes), "application/pdf")},
    )
    upload_response.raise_for_status()
    registration = upload_response.json()
    source_id = registration["source"]["source_id"]

    state.update(
        {
            "status": "generating",
            "generation_started": True,
            "workspace_id": workspace_id,
            "asset_id": workspace["asset"]["asset_id"],
            "source_id": source_id,
            "source_preparation": registration.get("preparation"),
        }
    )
    _write_json(state_path, state)

    started = time.perf_counter()
    payload: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    try:
        response = client.post(f"/api/workspaces/{workspace_id}/g3/sources/{source_id}/generate")
        if response.status_code == 200:
            payload = response.json()
            _write_json(response_path, payload)
        else:
            try:
                body: Any = response.json()
            except Exception:
                body = response.text
            error = {"status_code": response.status_code, "body": body}
    except Exception as exc:
        error = {"exception_type": type(exc).__name__, "message": str(exc)}
    elapsed = round(time.perf_counter() - started, 3)

    revision = _revision(payload, source_id)
    metrics = (revision or {}).get("generation_metrics") or {}
    calls = _call_ledger(revision or {})
    preflight = (
        ((((metrics.get("stages") or {}).get("ontology") or {}).get("details") or {})
        .get("cost_preflight") or {})
    )
    measured_cost = float(metrics.get("estimated_cost_usd", 0) or 0)
    ledger = {
        "campaign_id": campaign["campaign_id"],
        "manual_id": args.manual_id,
        "mode": args.mode,
        "authorized_campaign_budget_usd": authorized,
        "prior_measured_spend_usd": prior_spend,
        "run_hard_ceiling_usd": hard_ceiling,
        "actual_spend_usd": round(measured_cost, 6),
        "remaining_measured_budget_usd": round(authorized - prior_spend - measured_cost, 6),
        "call_count": len(calls),
        "calls": calls,
        "preflight": preflight,
        "elapsed_seconds": elapsed,
        "workspace_id": workspace_id,
        "source_id": source_id,
        "revision_id": (revision or {}).get("source_subgraph_revision_id"),
        "pipeline_version": (revision or {}).get("pipeline_version"),
        "error": error,
    }
    _write_json(ledger_path, ledger)
    state.update(
        {
            "status": "completed" if revision is not None else "stopped_without_retry",
            "elapsed_seconds": elapsed,
            "revision_id": ledger["revision_id"],
            "revision_status": (revision or {}).get("status"),
            "approval_eligible": (revision or {}).get("approval_eligible"),
            "actual_spend_usd": ledger["actual_spend_usd"],
            "error": error,
        }
    )
    _write_json(state_path, state)
    print(json.dumps({
        "manual_id": args.manual_id,
        "mode": args.mode,
        "status": state["status"],
        "workspace_id": workspace_id,
        "source_id": source_id,
        "revision_id": ledger["revision_id"],
        "approval_eligible": state["approval_eligible"],
        "calls": len(calls),
        "actual_spend_usd": ledger["actual_spend_usd"],
        "preflight_ceiling_usd": preflight.get("conservative_max_cost_usd"),
        "elapsed_seconds": elapsed,
        "error": error,
    }, ensure_ascii=False))
    return 0 if revision is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
