"""Run the V3 PDF-to-graph pipeline from the command line.

Every model call goes through the archived, budgeted gateway. A run directory
keeps the state of each station, so running the same command again resumes
instead of repeating calls. ``--gates agent`` lets agents answer every gate;
``--gates interactive`` leaves doubts and approval to a person.

Example:
    .venv/bin/python scripts/kg_v3.py --manual graco_check_mate_200 --out runs/v3/graco --gates agent
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MANIFEST = ROOT / "paper/experiments/robustness_20260925/manifest.json"
CAMPAIGN = ROOT / "campaign"
# The V3 campaign has its own ledger and a 10 USD cap for every call it makes.
DEFAULT_LEDGER = CAMPAIGN / "real_call_budget.jsonl"
DEFAULT_BUDGET = "10"
GATE_PRESETS = {
    # An agent cannot judge a whole graph from its summary: in unattended runs
    # the approval is automatic and recorded as such.
    "agent": {"map": ["agent"], "doubts": ["agent"], "approval": ["auto"]},
    "auto": {"map": ["auto"], "doubts": ["auto"], "approval": ["auto"]},
    "interactive": {"map": ["agent"], "doubts": ["agent", "human"], "approval": ["human"]},
}


def synthetic_workspace(pdf: Path, asset: dict):
    """A workspace and source for command-line runs outside the application."""

    from backend.domain.sources import Source
    from backend.domain.workspace import Workspace

    sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
    stamp = "2026-09-26T00:00:00Z"
    workspace = Workspace.model_validate({
        "workspace_id": "ws_kgv3cli0000001", "status": "ready",
        "asset": {"asset_id": "asset_kgv3cli0001", **asset},
        "asset_identity_version": 1, "ontology_version": "1.0", "ontology_sha256": "0" * 64,
        "confirmed_at": stamp, "created_at": stamp, "updated_at": stamp, "identifiers": [],
    })
    source = Source.model_validate({
        "source_id": "src_kgv3cli000001", "workspace_id": workspace.workspace_id, "source_kind": "pdf",
        "authority": "normative", "file_name": pdf.name, "media_type": "application/pdf",
        "size_bytes": pdf.stat().st_size, "sha256": sha, "language_hints": ["en"], "status": "accepted",
        "created_at": stamp, "asset_assessment_id": None, "raw_relpath": None, "active_assessment": None,
    })
    return workspace, source, sha


def load_evidence(pdf: Path, asset: dict):
    import fitz

    from backend.adapters.pdf import PdfAdapter

    workspace, source, sha = synthetic_workspace(pdf, asset)
    with fitz.open(pdf) as document:
        page_count = document.page_count
    return PdfAdapter().inspect(path=pdf, workspace=workspace, source=source).evidence_units, page_count, sha


def manual_source(manual_id: str) -> tuple[Path, dict]:
    """PDF and machine identity of a campaign manual (campaign/<id>) or a development manual."""

    if (CAMPAIGN / manual_id / "info.yaml").exists():
        from scripts.campaign import asset

        return CAMPAIGN / manual_id / "manual.pdf", asset(manual_id)
    spec = next(item for item in json.loads(MANIFEST.read_text())["manuals"] if item["manual_id"] == manual_id)
    return ROOT / "paper/manuals/files" / spec["file_name"], spec["asset"]


async def run(args) -> dict:
    from backend.kg_v3.export import graph_json
    from backend.kg_v3.llm import ModelClient
    from backend.kg_v3.reader import read_document
    from backend.kg_v3.reviewers import InMemoryQuestionStore, render_question
    from backend.kg_v3.run import Pipeline, RunConfig

    started = time.perf_counter()
    if args.manual:
        pdf, asset = manual_source(args.manual)
    else:
        pdf = Path(args.pdf).resolve()
        asset = {"name": args.asset_name or pdf.stem, "description": args.asset_name or pdf.stem,
                 "brand": "not_stated", "model": "not_stated", "asset_type": "not_stated"}
    out = Path(args.out)
    out = (out if out.is_absolute() else ROOT / out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    Path(args.ledger).resolve().parent.mkdir(parents=True, exist_ok=True)
    evidence, page_count, sha = load_evidence(pdf, asset)
    os.environ.update({
        "KG_LLM_MODE": "real", "KG_LLM_TRACE_DIR": str(out / "provider_responses"),
        "KG_REAL_CALL_BUDGET_LEDGER": str(Path(args.ledger).resolve()),
        "KG_REAL_CALL_BUDGET_USD": str(args.budget), "KG_REAL_CALL_RUN_ID": args.run_id or out.name,
        "KG_REAL_CALL_PDF_ID": f"sha256:{sha}",
    })
    doc = read_document(list(evidence), page_count=page_count)
    read_seconds = time.perf_counter() - started
    config = RunConfig(model=args.model, reasoning_effort=args.reasoning, reads=args.reads,
                       gates=GATE_PRESETS[args.gates], agent_model=args.agent_model,
                       agent_reasoning_effort=args.agent_reasoning)
    llm = ModelClient(model=args.model, reasoning_effort=args.reasoning)
    agent_llm = ModelClient(model=args.agent_model, reasoning_effort=args.agent_reasoning)
    store = InMemoryQuestionStore()
    result = await Pipeline(doc=doc, asset_name=asset["name"], llm=llm, config=config, agent_llm=agent_llm,
                            human_store=store, workdir=out).run()
    result.report["seconds"].update(pdf_read=round(read_seconds, 3),
                                    end_to_end=round(time.perf_counter() - started, 3))
    result.report["provenance"] = {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "pdf_sha256": sha, "config": config.model_dump(mode="json"),
        "segment_ids": [segment.segment_id for segment in doc.segments()],
    }
    graph = graph_json(result, doc, asset=asset, source_title=pdf.name)
    (out / "graph.json").write_text(json.dumps(graph, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "report.json").write_text(json.dumps(result.report, ensure_ascii=False, indent=1), encoding="utf-8")
    pending = store.open_questions()
    (out / "questions_for_people.txt").write_text(
        "\n\n".join(render_question(question) for question in pending), encoding="utf-8")
    return result.report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manual", help="manual_id from the development manifest")
    source.add_argument("--pdf", help="path to any PDF")
    parser.add_argument("--asset-name", default="")
    parser.add_argument("--out", required=True)
    parser.add_argument("--gates", choices=sorted(GATE_PRESETS), default="agent")
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--reasoning", default="low")
    parser.add_argument("--reads", type=int, default=2)
    parser.add_argument("--agent-model", default="gpt-6-luna")
    parser.add_argument("--agent-reasoning", default="medium")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--budget", default=DEFAULT_BUDGET)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--spend-ceiling", help="stricter cumulative cap without changing the campaign ledger budget")
    args = parser.parse_args()
    if args.spend_ceiling:
        os.environ["KG_REAL_CALL_SPEND_CEILING_USD"] = args.spend_ceiling
    os.chdir(ROOT)  # settings read the API key from .env in the repository root
    report = asyncio.run(run(args))
    print(json.dumps({key: report[key] for key in ("status", "units", "failed_reads", "graph", "gates", "usage", "seconds")},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
