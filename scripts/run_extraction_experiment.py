"""Isolated, resumable experiment execution without gold or historical runners.

Every invocation has a unique run directory and shares one durable budget ledger.
This script never approves or merges generated source graphs.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import sys
import time
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n")


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--manual", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--code-root", type=Path, default=ROOT)
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--reasoning", default="low")
    parser.add_argument("--output-tokens", type=int, default=24000)
    parser.add_argument("--strategy", choices=["semantic", "hybrid"], default="hybrid")
    parser.add_argument("--baseline", action="store_true")
    parser.add_argument("--packet-pages", help="Development packet, physical pages separated by commas")
    parser.add_argument("--focused", action="store_true", help="Use deterministic source windows for the packet")
    parser.add_argument("--escalation-calls", type=int, default=0)
    parser.add_argument("--per-run-ceiling", type=float, default=8.0)
    args = parser.parse_args()
    campaign = args.campaign.resolve()
    manifest = json.loads((campaign / "manifest.json").read_text())
    cap = str(manifest["budget_cap_usd"])
    if float(cap) > 20:
        raise RuntimeError("Campaign exceeds the explicit USD 20 authorization")
    spec = next(item for item in manifest["manuals"] if item["manual_id"] == args.manual)
    pdf = ROOT / "paper/manuals/files" / spec["file_name"]
    if digest(pdf) != spec["sha256"]:
        raise RuntimeError("Source PDF digest mismatch")
    run = campaign / "runs" / args.run_id
    run.mkdir(parents=True, exist_ok=False)
    os.environ.update({
        "KG_LLM_MODE": "real", "KG_GENERATION_MODEL": args.model, "MODEL_NAME": args.model,
        "KG_OPERATIONAL_DB": str(run / "operational.db"), "KG_RAW_DIR": str(run / "raw"),
        "KG_INCOMING_DIR": str(run / "incoming"), "KG_LLM_TRACE_DIR": str(run / "provider_responses"),
        "KG_REAL_CALL_BUDGET_LEDGER": str(campaign / "real_call_budget.jsonl"),
        "KG_REAL_CALL_BUDGET_USD": cap, "KG_REAL_CALL_RUN_ID": args.run_id,
        "KG_REAL_CALL_PDF_ID": "sha256:" + spec["sha256"],
    })
    sys.path.insert(0, str(args.code_root.resolve()))
    from backend.app_config import load_config
    from backend.config import settings
    from backend.services.real_call_budget_ledger import RealCallBudgetLedger

    ledger = RealCallBudgetLedger(campaign / "real_call_budget.jsonl", absolute_budget_usd=cap)
    cfg = load_config()
    if not args.baseline:
        cfg["ontology"].update(
            diagnostic_bundle_max_output_tokens=args.output_tokens,
            diagnostic_atomic_table_max_output_tokens=min(16000, args.output_tokens),
            diagnostic_context_strategy=args.strategy,
        )
        cfg["ontology"]["diagnostic_escalation"].update(
            enabled=bool(args.escalation_calls), primary_model=args.model,
            model="gpt-6-sol", reasoning_effort="medium",
            max_chunks_per_run=args.escalation_calls, max_output_tokens=24000,
            schema_overhead_characters=30000,
        )
        cfg["agents"]["ontology_draft"].update(model=args.model, reasoning_effort=args.reasoning)
    cfg["pdf_generation_cost_guard"].update(hard_ceiling_usd=args.per_run_ceiling, preferred_cost_usd=args.per_run_ceiling)
    sources = [*args.code_root.glob("backend/**/*.py"), args.code_root / "config.yaml", args.code_root / "ontology_schema.JSON"]
    code_hashes = {str(p.relative_to(args.code_root)): digest(p) for p in sorted(sources) if p.is_file()}
    profile = {
        "run_id": args.run_id, "manual_id": args.manual, "pdf_sha256": spec["sha256"],
        "arguments": vars(args), "config": cfg, "code_files": code_hashes,
        "code_sha256": hashlib.sha256(json.dumps(code_hashes, sort_keys=True).encode()).hexdigest(),
        "runner_sha256": digest(Path(__file__)),
        "packages": {name: importlib.metadata.version(name) for name in ["openai", "pymupdf", "pydantic", "fastapi", "httpx"]},
        "gold_used_in_generation": False, "human_approval_performed": False,
    }
    write(run / "runtime_profile.json", profile)
    state = {"status": "running", "started_utc": datetime.now(timezone.utc).isoformat(), "budget_before": ledger.snapshot().as_dict()}
    write(run / "timing.json", state)
    started = time.perf_counter()
    try:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("No API credential configured")
        if args.packet_pages:
            from backend.adapters.pdf import PdfAdapter
            from backend.domain.sources import Source
            from backend.domain.workspace import Workspace
            from backend.services.diagnostic_record_windowing import build_diagnostic_record_windows
            from backend.services.ontology_pipeline import build_initial_ontology
            from backend.services.ontology_workflow import _render_diagnostic_windows
            from backend.services.pdf_service import format_text_with_pages
            timestamp = state["started_utc"].replace("+00:00", "Z")
            workspace = Workspace.model_validate({
                "workspace_id": "ws_packet00000001", "status": "ready",
                "asset": {"asset_id": "asset_packet00001", **spec["asset"]},
                "asset_identity_version": 1, "ontology_version": "1.0", "ontology_sha256": digest(args.code_root / "ontology_schema.JSON"),
                "confirmed_at": timestamp, "created_at": timestamp, "updated_at": timestamp, "identifiers": [],
            })
            source = Source.model_validate({
                "source_id": "src_packet00000001", "workspace_id": workspace.workspace_id,
                "source_kind": "pdf", "authority": "normative", "file_name": spec["file_name"],
                "media_type": "application/pdf", "size_bytes": pdf.stat().st_size, "sha256": spec["sha256"],
                "language_hints": ["en"], "status": "accepted", "created_at": timestamp,
                "asset_assessment_id": None, "raw_relpath": None, "active_assessment": None,
            })
            included = {int(value) for value in args.packet_pages.split(",")}
            adapter = PdfAdapter().inspect(path=pdf, workspace=workspace, source=source, included_pages=included, scope_version=1)
            units = list(adapter.evidence_units)
            windows = [window.model_dump(mode="json") for window in build_diagnostic_record_windows(units)] if args.focused else []
            pages = [{"page_number": page, "text": "\n".join(f"[[EVIDENCE_ID: {unit.evidence_id}]]\n{unit.locator.quote}" for unit in units if unit.locator.page == page)} for page in sorted(included)]
            text = _render_diagnostic_windows(windows) if windows else format_text_with_pages(pages)
            write(run / "packet.json", {"pages": sorted(included), "evidence": [u.model_dump(mode="json") for u in units], "windows": windows, "text": text})
            result, metrics = build_initial_ontology(
                text_with_pages=text, source_type="technical PDF", source_title=spec["file_name"],
                target_language="en", model_name=args.model, reasoning_effort=args.reasoning,
                asset_identity=spec["asset"], extraction_role="diagnostic", relation_first=True,
                diagnostic_call_options={"record_windows": windows, "max_output_tokens": args.output_tokens},
                diagnostic_evidence_units=units,
            )
            write(run / "generation_response.json", result.model_dump(mode="json"))
            write(run / "metrics.json", metrics)
            write(run / "graph.json", result.ontology.model_dump(mode="json"))
        else:
            from fastapi.testclient import TestClient

            from backend.main import create_app
            with TestClient(create_app()) as client:
                response = client.post("/api/workspaces", json={"asset": spec["asset"], "identifiers": [], "assertion": {"reason": "Identity transcribed from source metadata, no diagnostic gold.", "observation_basis": "operator_record", "operator": "robustness experiment runner"}})
                response.raise_for_status()
                workspace_id = response.json()["workspace"]["workspace_id"]
                response = client.post(f"/api/workspaces/{workspace_id}/sources", data={"authority": "normative"}, files={"file": (spec["file_name"], BytesIO(pdf.read_bytes()), "application/pdf")})
                response.raise_for_status()
                source_id = response.json()["source"]["source_id"]
                state.update(workspace_id=workspace_id, source_id=source_id)
                response = client.post(f"/api/workspaces/{workspace_id}/g3/sources/{source_id}/generate")
                write(run / "generation_response.json", response.json())
                response.raise_for_status()
                entry = next(item for item in response.json()["sources"] if item["source_id"] == source_id)
                write(run / "graph.json", entry["subgraph"])
        state["status"] = "completed"
    except Exception as exc:
        state.update(status="failed", error_type=type(exc).__name__, error=str(exc).replace(settings.OPENAI_API_KEY, "[REDACTED]") if settings.OPENAI_API_KEY else str(exc))
    finally:
        state.update(total_elapsed_seconds=round(time.perf_counter() - started, 3), finished_utc=datetime.now(timezone.utc).isoformat(), budget_after=ledger.snapshot().as_dict())
        write(run / "timing.json", state)
    print(json.dumps(state), flush=True)
    return 0 if state["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
