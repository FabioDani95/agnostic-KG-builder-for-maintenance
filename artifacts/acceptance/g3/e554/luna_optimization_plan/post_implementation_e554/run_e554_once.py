#!/usr/bin/env python3
"""Execute the single authorized E-554 post-implementation generation.

The harness creates a separate workspace, never calls a decision/merge/CSV
endpoint, and refuses to start if its append-only budget ledger says that a
full generation has already been attempted.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

REPOSITORY_ROOT = Path(__file__).resolve().parents[6]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.config import settings  # noqa: E402
from backend.main import create_app  # noqa: E402
from backend.services.llm_gateway import llm_mode  # noqa: E402
from backend.storage.repositories.subgraphs import SourceSubgraphRepository  # noqa: E402

ROOT = Path(__file__).resolve().parent
LEDGER_PATH = ROOT / "real_api_ledger.json"
RESPONSE_PATH = ROOT / "generation_response.json"
STATE_PATH = ROOT / "run_state.json"
MANUAL_PATH = Path("/Users/fabiodaniele/Downloads/E-554.pdf")
MANUAL_SHA256 = "a7467316234f2d84550e7c267bf709fda55e1023055d9569dc27348f192641d0"
BASELINE_REVISION_ID = "sgrev_OR8HyabEt7ntt0Z00LZEoA"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _load_ledger() -> dict[str, Any]:
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def _baseline_snapshot() -> dict[str, Any]:
    revision = SourceSubgraphRepository().get(BASELINE_REVISION_ID)
    return {
        "revision_id": revision.source_subgraph_revision_id,
        "workspace_id": revision.workspace_id,
        "status": revision.status.value,
        "approval_decision_id": revision.approval_decision_id,
        "input_config_hash": revision.input_config_hash,
    }


def _call_ledger(revision_payload: dict[str, Any]) -> list[dict[str, Any]]:
    stages = ((revision_payload.get("generation_metrics") or {}).get("stages") or {})
    calls: list[dict[str, Any]] = []
    for stage_name in ("scoping", "ontology"):
        stage = stages.get(stage_name) or {}
        for item in (stage.get("details") or {}).get("call_ledger") or []:
            calls.append({
                **item,
                "global_call_index": len(calls) + 1,
                "stage": stage_name,
            })
    return calls


def main() -> int:
    ledger = _load_ledger()
    if int(ledger.get("full_generations_started", 0) or 0) != 0:
        raise RuntimeError("The authorized one-shot full generation has already been started")
    if llm_mode() != "real":
        raise RuntimeError("KG_LLM_MODE must be real for the authorized measurement")
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is unavailable")
    if not MANUAL_PATH.is_file():
        raise RuntimeError(f"Manual not found: {MANUAL_PATH}")
    if hashlib.sha256(MANUAL_PATH.read_bytes()).hexdigest() != MANUAL_SHA256:
        raise RuntimeError("The E-554 manual hash does not match the frozen acceptance input")

    baseline_before = _baseline_snapshot()
    if baseline_before["status"] != "reviewing" or baseline_before["approval_decision_id"] is not None:
        raise RuntimeError("The retained Luna baseline is no longer an undecided reviewing revision")

    state: dict[str, Any] = {
        "status": "preparing_experimental_workspace",
        "baseline_before": baseline_before,
        "manual_sha256": MANUAL_SHA256,
        "llm_mode": llm_mode(),
        "real_api_key_present": True,
        "real_api_key_exposed": False,
        "csv_processed": False,
        "merge_started": False,
        "review_decision_taken": False,
    }
    _write_json(STATE_PATH, state)

    client = TestClient(create_app())
    workspace_response = client.post(
        "/api/workspaces",
        json={
            "asset": {
                "name": "Eastman Eagle S3L",
                "description": "Operator-confirmed experimental workspace for the Eastman Eagle S3L.",
                "brand": "Eastman",
                "model": "Eagle S3L",
                "asset_type": "automated cutting machine",
            },
            "identifiers": [],
            "assertion": {
                "reason": "Identity copied from the operator-confirmed canonical baseline for an isolated test.",
                "observation_basis": "operator_record",
                "operator": "Codex G3 isolated acceptance harness",
            },
        },
    )
    workspace_response.raise_for_status()
    workspace_payload = workspace_response.json()
    workspace_id = workspace_payload["workspace"]["workspace_id"]
    asset_id = workspace_payload["workspace"]["asset"]["asset_id"]

    with MANUAL_PATH.open("rb") as manual_file:
        upload_response = client.post(
            f"/api/workspaces/{workspace_id}/sources",
            data={"authority": "normative"},
            files={"file": ("E-554.pdf", manual_file, "application/pdf")},
        )
    upload_response.raise_for_status()
    source_payload = upload_response.json()
    source_id = source_payload["source"]["source_id"]

    state.update({
        "status": "ready_to_generate",
        "experimental_workspace_id": workspace_id,
        "experimental_asset_id": asset_id,
        "experimental_source_id": source_id,
        "source_preparation": source_payload.get("preparation"),
    })
    _write_json(STATE_PATH, state)

    ledger["full_generations_started"] = 1
    ledger["experimental_workspace_id"] = workspace_id
    ledger["experimental_asset_id"] = asset_id
    ledger["experimental_source_id"] = source_id
    ledger["preflight"]["status"] = "generation_started"
    _write_json(LEDGER_PATH, ledger)

    started_at = time.perf_counter()
    response_payload: dict[str, Any] | None = None
    error_payload: dict[str, Any] | None = None
    try:
        generation_response = client.post(
            f"/api/workspaces/{workspace_id}/g3/sources/{source_id}/generate"
        )
        if generation_response.status_code != 200:
            error_payload = {
                "status_code": generation_response.status_code,
                "body": generation_response.json(),
            }
        else:
            response_payload = generation_response.json()
            _write_json(RESPONSE_PATH, response_payload)
    except Exception as exc:  # one shot: record and stop; never retry
        error_payload = {"exception_type": type(exc).__name__, "message": str(exc)}

    elapsed = round(time.perf_counter() - started_at, 3)
    revision_payload: dict[str, Any] | None = None
    if response_payload is not None:
        for source_view in response_payload.get("sources") or []:
            if source_view.get("source_id") == source_id:
                revision_payload = source_view.get("subgraph")
                break

    calls = _call_ledger(revision_payload or {})
    measured_cost = float(
        ((revision_payload or {}).get("generation_metrics") or {}).get("estimated_cost_usd", 0)
        or 0
    )
    ledger.update({
        "calls": calls,
        "actual_spend_usd": round(measured_cost, 6),
        "remaining_budget_usd": round(0.5 - measured_cost, 6),
        "full_generations_completed": 1 if revision_payload is not None else 0,
        "measured_wall_time_seconds": elapsed,
        "experimental_revision_id": (
            revision_payload.get("source_subgraph_revision_id") if revision_payload else None
        ),
        "experimental_revision_status": revision_payload.get("status") if revision_payload else None,
        "error": error_payload,
    })
    ledger["preflight"]["status"] = "completed" if revision_payload else "stopped_without_retry"
    _write_json(LEDGER_PATH, ledger)

    baseline_after = _baseline_snapshot()
    state.update({
        "status": "completed" if revision_payload else "stopped_without_retry",
        "elapsed_seconds": elapsed,
        "baseline_after": baseline_after,
        "baseline_unchanged": baseline_before == baseline_after,
        "experimental_revision_id": (
            revision_payload.get("source_subgraph_revision_id") if revision_payload else None
        ),
        "experimental_revision_status": revision_payload.get("status") if revision_payload else None,
        "error": error_payload,
    })
    _write_json(STATE_PATH, state)

    print(json.dumps({
        "status": state["status"],
        "workspace_id": workspace_id,
        "source_id": source_id,
        "revision_id": state["experimental_revision_id"],
        "baseline_unchanged": state["baseline_unchanged"],
        "calls": len(calls),
        "actual_spend_usd": ledger["actual_spend_usd"],
        "elapsed_seconds": elapsed,
        "error": error_payload,
    }, ensure_ascii=False))
    return 0 if revision_payload is not None else 1


if __name__ == "__main__":
    sys.exit(main())
