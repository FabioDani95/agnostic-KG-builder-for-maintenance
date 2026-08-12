#!/usr/bin/env python3
"""Run the authorized autonomous E-554 v7 acceptance exactly once.

The harness uses an isolated operational database and raw store supplied by the
caller, creates a new workspace/revision, never approves or merges anything,
and persists the complete response and measured call ledger for offline audit.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

REPOSITORY_ROOT = Path(__file__).resolve().parents[6]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from backend.app_config import (  # noqa: E402
    get_diagnostic_escalation_config,
    get_pdf_generation_cost_guard_config,
)
from backend.config import settings  # noqa: E402
from backend.main import create_app  # noqa: E402
from backend.services.llm_gateway import llm_mode  # noqa: E402

ROOT = Path(__file__).resolve().parent / "v7_real_run"
STATE_PATH = ROOT / "run_state.json"
RESPONSE_PATH = ROOT / "generation_response.json"
LEDGER_PATH = ROOT / "real_api_ledger.json"
SOURCE_REVISION = "d0d91ebbee3345f7663f10e1694b75bf94758d37^"
SOURCE_PATH = "manuals/batch_manuals/eagle_s3l_laser_cutting_system_service_manual.pdf"
SOURCE_SHA256 = "a7467316234f2d84550e7c267bf709fda55e1023055d9569dc27348f192641d0"
AUTHORIZED_CEILING_USD = 1.00
PRIOR_ATTEMPT_RESERVED_USD = 0.50
RUN_HARD_CEILING_USD = 0.50


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n",
        encoding="utf-8",
    )


def _recover_pdf() -> bytes:
    completed = subprocess.run(
        ["git", "show", f"{SOURCE_REVISION}:{SOURCE_PATH}"],
        cwd=REPOSITORY_ROOT,
        check=True,
        stdout=subprocess.PIPE,
    )
    payload = completed.stdout
    actual = hashlib.sha256(payload).hexdigest()
    if actual != SOURCE_SHA256:
        raise RuntimeError(f"Frozen E-554 hash mismatch: {actual}")
    return payload


def _revision_from_response(payload: dict[str, Any], source_id: str) -> dict[str, Any] | None:
    for source_view in payload.get("sources") or []:
        if source_view.get("source_id") == source_id:
            return source_view.get("subgraph")
    return None


def _call_ledger(revision: dict[str, Any]) -> list[dict[str, Any]]:
    stages = ((revision.get("generation_metrics") or {}).get("stages") or {})
    calls: list[dict[str, Any]] = []
    for stage_name, stage in stages.items():
        for item in (stage.get("details") or {}).get("call_ledger") or []:
            calls.append(
                {
                    **item,
                    "global_call_index": len(calls) + 1,
                    "stage": stage_name,
                }
            )
    return calls


def main() -> int:
    if STATE_PATH.exists():
        previous = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        if previous.get("generation_started"):
            raise RuntimeError("The authorized v7 one-shot run has already started")
    if llm_mode() != "real":
        raise RuntimeError("KG_LLM_MODE must be real")
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is unavailable")
    if not os.environ.get("KG_OPERATIONAL_DB"):
        raise RuntimeError("KG_OPERATIONAL_DB must identify an isolated database")
    if not os.environ.get("KG_RAW_DIR") or not os.environ.get("KG_INCOMING_DIR"):
        raise RuntimeError("KG_RAW_DIR and KG_INCOMING_DIR must identify isolated stores")

    guard = get_pdf_generation_cost_guard_config()
    escalation = get_diagnostic_escalation_config()
    if float(guard.get("hard_ceiling_usd", 0) or 0) != RUN_HARD_CEILING_USD:
        raise RuntimeError("Configured run ceiling is not the authorized $1.00")
    if PRIOR_ATTEMPT_RESERVED_USD + RUN_HARD_CEILING_USD > AUTHORIZED_CEILING_USD:
        raise RuntimeError("Cumulative real-call envelope exceeds the authorized $1.00")
    if not escalation.get("enabled") or int(escalation.get("max_chunks_per_run", 0) or 0) != 1:
        raise RuntimeError("The authorized run requires exactly one bounded Terra escalation")
    if str(escalation.get("primary_model") or "") != "gpt-5.6-luna":
        raise RuntimeError("The authorized primary diagnostic model must be Luna")
    if str(escalation.get("model") or "") != "gpt-5.6-terra":
        raise RuntimeError("The authorized selective escalation model must be Terra")

    pdf_bytes = _recover_pdf()
    state: dict[str, Any] = {
        "status": "initializing_isolated_workspace",
        "generation_started": False,
        "authorized_ceiling_usd": AUTHORIZED_CEILING_USD,
        "prior_attempt_reserved_usd": PRIOR_ATTEMPT_RESERVED_USD,
        "run_hard_ceiling_usd": RUN_HARD_CEILING_USD,
        "cumulative_maximum_usd": round(
            PRIOR_ATTEMPT_RESERVED_USD + RUN_HARD_CEILING_USD, 6
        ),
        "llm_mode": llm_mode(),
        "api_key_present": True,
        "api_key_exposed": False,
        "source_revision": SOURCE_REVISION,
        "source_path": SOURCE_PATH,
        "manual_sha256": SOURCE_SHA256,
        "operational_db": os.environ["KG_OPERATIONAL_DB"],
        "raw_store": os.environ["KG_RAW_DIR"],
        "approval_decision_taken": False,
        "merge_started": False,
        "csv_processed": False,
    }
    _write_json(STATE_PATH, state)

    client = TestClient(create_app())
    workspace_response = client.post(
        "/api/workspaces",
        json={
            "asset": {
                "name": "Eastman Eagle S3L",
                "description": "Operator-confirmed isolated v7 acceptance workspace.",
                "brand": "Eastman",
                "model": "Eagle S3L",
                "asset_type": "automated cutting machine",
            },
            "identifiers": [],
            "assertion": {
                "reason": "Identity copied from the operator-confirmed frozen acceptance record.",
                "observation_basis": "operator_record",
                "operator": "Codex isolated E-554 v7 acceptance harness",
            },
        },
    )
    workspace_response.raise_for_status()
    workspace = workspace_response.json()["workspace"]
    workspace_id = workspace["workspace_id"]

    from io import BytesIO

    upload_response = client.post(
        f"/api/workspaces/{workspace_id}/sources",
        data={"authority": "normative"},
        files={"file": ("E-554.pdf", BytesIO(pdf_bytes), "application/pdf")},
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
    _write_json(STATE_PATH, state)

    started_at = time.perf_counter()
    response_payload: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    try:
        response = client.post(
            f"/api/workspaces/{workspace_id}/g3/sources/{source_id}/generate"
        )
        if response.status_code == 200:
            response_payload = response.json()
            _write_json(RESPONSE_PATH, response_payload)
        else:
            error = {"status_code": response.status_code, "body": response.json()}
    except Exception as exc:
        error = {"exception_type": type(exc).__name__, "message": str(exc)}
    elapsed = round(time.perf_counter() - started_at, 3)

    revision = (
        _revision_from_response(response_payload, source_id)
        if response_payload is not None
        else None
    )
    metrics = (revision or {}).get("generation_metrics") or {}
    calls = _call_ledger(revision or {})
    preflight = (
        (((metrics.get("stages") or {}).get("ontology") or {}).get("details") or {})
        .get("cost_preflight")
        or {}
    )
    measured_cost = float(metrics.get("estimated_cost_usd", 0) or 0)
    ledger = {
        "activity": "e554_v7_real_autonomous_acceptance",
        "authorized_ceiling_usd": AUTHORIZED_CEILING_USD,
        "prior_attempt_reserved_usd": PRIOR_ATTEMPT_RESERVED_USD,
        "run_hard_ceiling_usd": RUN_HARD_CEILING_USD,
        "cumulative_maximum_usd": round(
            PRIOR_ATTEMPT_RESERVED_USD + RUN_HARD_CEILING_USD, 6
        ),
        "actual_spend_usd": round(measured_cost, 6),
        "remaining_authorized_budget_usd": round(
            AUTHORIZED_CEILING_USD - PRIOR_ATTEMPT_RESERVED_USD - measured_cost,
            6,
        ),
        "call_count": len(calls),
        "calls": calls,
        "preflight": preflight,
        "workspace_id": workspace_id,
        "source_id": source_id,
        "revision_id": (revision or {}).get("source_subgraph_revision_id"),
        "pipeline_version": (revision or {}).get("pipeline_version"),
        "elapsed_seconds": elapsed,
        "error": error,
    }
    _write_json(LEDGER_PATH, ledger)
    state.update(
        {
            "status": "completed" if revision is not None else "stopped_without_retry",
            "elapsed_seconds": elapsed,
            "revision_id": (revision or {}).get("source_subgraph_revision_id"),
            "revision_status": (revision or {}).get("status"),
            "approval_eligible": (revision or {}).get("approval_eligible"),
            "actual_spend_usd": ledger["actual_spend_usd"],
            "error": error,
        }
    )
    _write_json(STATE_PATH, state)

    print(
        json.dumps(
            {
                "status": state["status"],
                "workspace_id": workspace_id,
                "source_id": source_id,
                "revision_id": state["revision_id"],
                "revision_status": state["revision_status"],
                "approval_eligible": state["approval_eligible"],
                "calls": len(calls),
                "actual_spend_usd": ledger["actual_spend_usd"],
                "preflight_ceiling_usd": preflight.get("conservative_max_cost_usd"),
                "elapsed_seconds": elapsed,
                "error": error,
            },
            ensure_ascii=False,
        )
    )
    return 0 if revision is not None else 1


if __name__ == "__main__":
    raise SystemExit(main())
