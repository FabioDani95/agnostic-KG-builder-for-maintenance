"""Run the frozen v22 generator on a manual, as the comparison baseline of the V3 campaign.

The manual goes through the real workspace API with an isolated database and the
campaign ledger. The v22 graph is written to <out>/graph.json with its timing.

Usage:
    .venv/bin/python scripts/kg_v3_v22_baseline.py --manual genie_scissor --out campaign/genie_scissor/runs/v22
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.kg_v3 import DEFAULT_BUDGET, DEFAULT_LEDGER, manual_source  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manual", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--budget", default=DEFAULT_BUDGET)
    args = parser.parse_args()
    os.chdir(ROOT)
    pdf, asset = manual_source(args.manual)
    out = (ROOT / args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    Path(args.ledger).resolve().parent.mkdir(parents=True, exist_ok=True)
    os.environ.update({
        "KG_PDF_GENERATOR": "legacy_v22", "KG_LLM_MODE": "real",
        # Campaign PDFs can exceed the 50 MB upload limit of the web app (ABB ACS580 is 55 MB).
        "KG_MAX_UPLOAD_BYTES": str(512 * 1024 * 1024), "KG_MAX_REQUEST_BYTES": str(520 * 1024 * 1024),
        "KG_OPERATIONAL_DB": str(out / "operational.db"), "KG_RAW_DIR": str(out / "raw"),
        "KG_INCOMING_DIR": str(out / "incoming"), "KG_LLM_TRACE_DIR": str(out / "provider_responses"),
        "KG_REAL_CALL_BUDGET_LEDGER": str(Path(args.ledger).resolve()), "KG_REAL_CALL_BUDGET_USD": args.budget,
        "KG_REAL_CALL_RUN_ID": f"v22_{args.manual}_{out.name}",
        "KG_REAL_CALL_PDF_ID": "sha256:" + hashlib.sha256(pdf.read_bytes()).hexdigest(),
    })
    from fastapi.testclient import TestClient

    from backend.main import create_app

    started = time.perf_counter()
    state = {"manual": args.manual, "status": "running"}
    try:
        with TestClient(create_app()) as client:
            response = client.post("/api/workspaces", json={"asset": asset, "identifiers": [], "assertion": {
                "reason": "Identity from the campaign registry.", "observation_basis": "operator_record",
                "operator": "V3 campaign baseline runner"}})
            response.raise_for_status()
            workspace_id = response.json()["workspace"]["workspace_id"]
            response = client.post(f"/api/workspaces/{workspace_id}/sources", data={"authority": "normative"},
                                   files={"file": (pdf.name, BytesIO(pdf.read_bytes()), "application/pdf")})
            response.raise_for_status()
            source_id = response.json()["source"]["source_id"]
            response = client.post(f"/api/workspaces/{workspace_id}/g3/sources/{source_id}/generate")
            response.raise_for_status()
            entry = next(item for item in response.json()["sources"] if item["source_id"] == source_id)
            (out / "graph.json").write_text(json.dumps(entry["subgraph"], ensure_ascii=False, indent=1))
        state["status"] = "completed"
    except Exception as exc:
        state.update(status="failed", error=f"{type(exc).__name__}: {exc}"[:2000])
    state["seconds"] = round(time.perf_counter() - started, 3)
    (out / "timing.json").write_text(json.dumps(state, indent=1))
    print(json.dumps(state))
    return 0 if state["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
