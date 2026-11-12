"""Build a connected maintenance graph from a PDF manual, autonomously.

    read -> survey -> extract -> verify -> resolve -> gaps -> enrich -> export

A run asks nobody anything. Its directory keeps the state of every step, so the same command
resumes instead of repeating calls. Real calls need an explicit authorisation, a budget and a
ledger file of your choice; without them only ``--estimate``, ``--preflight`` and ``--replay`` work.

Examples:
    .venv/bin/python scripts/kg_build.py --manual grizzly_g0872 --estimate
    .venv/bin/python scripts/kg_build.py --manual grizzly_g0872 --out experiments/kg4/grizzly_r1 \\
        --authorize-spend --budget 2 --ledger experiments/kg4/budget.jsonl
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HISTORICAL_LEDGERS = ("campaign/real_call_budget.jsonl", "experiments/kg_quality_pilot_20261001/budget.jsonl")


def source(args) -> tuple[Path, dict]:
    from scripts.kg_v3 import info_asset, manual_source

    if args.manual:
        return manual_source(args.manual)
    pdf = Path(args.pdf).resolve()
    if args.info:
        return pdf, info_asset(Path(args.info))
    name = args.asset_name or pdf.stem
    return pdf, {"name": name, "description": name, "brand": "not_stated", "model": "not_stated",
                 "asset_type": "not_stated"}


def read(pdf: Path, asset: dict):
    """The read document, its sections and the PDF hash."""

    from backend.kg_v3.reader import read_document
    from backend.kg_v4.sections import build_sections
    from scripts.kg_v3 import load_evidence

    evidence, page_count, sha = load_evidence(pdf, asset)
    doc = read_document(list(evidence), page_count=page_count)
    return doc, build_sections(pdf, doc), sha


def build_config(args):
    from backend.kg_v4.pipeline import BuildConfig

    return BuildConfig(model=args.model, reasoning_effort=args.reasoning, verify=not args.no_verify,
                       gap_max_calls=args.gap_calls, gap_rounds=0 if args.gap_calls == 0 else 2,
                       enrich=args.enrich_calls > 0, enrich_max_calls=args.enrich_calls,
                       extra_pages=[int(page) for page in args.pages.split(",") if page.strip()])


def pending_approval(out: Path, document: dict) -> None:
    """For runs started from the interface: the graph waits for the person's button."""

    from backend.kg_v3.questions import approval_question
    from backend.kg_v3.run_state import atomic_json

    counts = document["report"]["graph"]
    question = approval_question([f"{counts['nodes']} nodes and {counts['edges']} relations.",
                                  f"Relations by tier: {counts['edges_by_tier']}."],
                                 {"nodes": counts["nodes"], "edges": counts["edges"]})
    atomic_json(out / "state" / "gate_approval.json", {"questions": [question.model_dump(mode="json")], "answers": [],
                                                       "pending": [question.question_id]})


async def run(args) -> dict:
    from backend.kg_v3.llm import ModelClient
    from backend.kg_v3.run_state import atomic_json, run_lock
    from backend.kg_v4.estimate import estimate
    from backend.kg_v4.pipeline import Builder

    started = time.perf_counter()
    pdf, asset = source(args)
    config = build_config(args)
    doc, sections, sha = read(pdf, asset)
    if args.estimate:
        return {"plan": "read -> survey -> extract -> verify -> resolve -> gaps -> enrich -> export",
                "pdf": str(pdf), **estimate(doc, config), "provider_calls": 0}
    out = Path(args.out)
    out = (out if out.is_absolute() else ROOT / out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    on_event = None
    if args.events:
        from backend.ui.events import EventLog

        on_event = EventLog(out / "events.jsonl")
        on_event("run_started", {"manual_id": args.manual or pdf.stem, "version_id": out.name,
                                 "mode": "resume" if (out / "state").exists() else "live"})
        on_event("step_started", {"step": "pdf_read"})
        on_event("step_finished", {"step": "pdf_read", "seconds": round(time.perf_counter() - started, 3)})
    factory = None
    mode = "real"
    if args.preflight:
        mode = "preflight"

        class Refusing:
            def __init__(self):
                from types import SimpleNamespace
                self.chat = SimpleNamespace(completions=self)

            async def create(self, **_kwargs):
                raise AssertionError("preflight must never call a provider")
        factory = Refusing
    elif args.replay:
        from backend.kg_v3.replay import ReplayProvider

        mode, provider = "exact_replay", ReplayProvider(Path(args.replay))

        def factory():
            return provider
    else:
        ledger = Path(args.ledger).resolve()
        ledger.parent.mkdir(parents=True, exist_ok=True)
        os.environ.update({
            "KG_LLM_MODE": "real", "KG_LLM_TRACE_DIR": str(out / "provider_responses"),
            "KG_REAL_CALL_BUDGET_LEDGER": str(ledger), "KG_REAL_CALL_BUDGET_USD": str(args.budget),
            "KG_REAL_CALL_RUN_ID": args.run_id or out.name, "KG_REAL_CALL_PDF_ID": f"sha256:{sha}",
        })
        if args.spend_ceiling:
            os.environ["KG_REAL_CALL_SPEND_CEILING_USD"] = args.spend_ceiling
    try:
        with run_lock(out):
            llm = ModelClient(model=args.model, reasoning_effort=args.reasoning, client_factory=factory)
            builder = Builder(doc=doc, asset=asset, llm=llm, config=config, pdf_path=pdf, workdir=out,
                              sections=sections, source_title=pdf.name, on_event=on_event)
            if args.preflight:
                return {"preflight": "READY", "pages": doc.page_count, "text_pages": len(doc.pages),
                        "headings": len(sections.headings), "printed_page_offset": sections.page_offset,
                        "input_manifest": builder.manifest, "provider_calls": 0, **estimate(doc, config)}
            result = await builder.run()
            earlier = json.loads((out / "report.json").read_text()) if (out / "report.json").exists() else None
            from scripts.kg_v3 import with_earlier_attempts

            report = with_earlier_attempts(result.report, earlier)
            report["seconds"]["end_to_end"] = round(time.perf_counter() - started, 3)
            report["execution_mode"] = mode
            if args.approval == "person" and result.status == "approved":
                report["status"] = result.document["status"] = "awaiting_approval"
                report["approval"] = "person"
            result.document["report"] = report
            if report["status"] == "awaiting_approval":
                pending_approval(out, result.document)
            atomic_json(out / "graph.json", result.document)
            atomic_json(out / "report.json", report)
            atomic_json(out / "input_manifest.json", builder.manifest)
    except BaseException as error:
        if on_event is not None:
            on_event("run_failed", {"message": f"{type(error).__name__}: {error}"})
        raise
    if on_event is not None:
        on_event("run_finished", {"graph": result.document, "status": report["status"], "open_questions": 0})
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    origin = parser.add_mutually_exclusive_group(required=True)
    origin.add_argument("--manual", help="manual ID of a campaign folder (campaign/<id>)")
    origin.add_argument("--pdf", help="path to any PDF")
    parser.add_argument("--asset-name", default="")
    parser.add_argument("--info", help="info.yaml with the machine identity, for --pdf")
    parser.add_argument("--out", help="run directory; a new one for every change of PDF, model or prompts")
    parser.add_argument("--estimate", action="store_true", help="print the plan and the cost estimate; no calls")
    parser.add_argument("--preflight", action="store_true", help="check input, sections and manifest; no calls")
    parser.add_argument("--replay", help="archived provider responses; a miss never reaches the network")
    parser.add_argument("--authorize-spend", action="store_true", help="permit real calls under --budget and --ledger")
    parser.add_argument("--budget", help="cumulative cap of the ledger in USD")
    parser.add_argument("--ledger", help="budget ledger file of this experiment (never a historical one)")
    parser.add_argument("--spend-ceiling", help="stricter cumulative cap without changing the ledger budget")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--reasoning", default="low")
    parser.add_argument("--no-verify", action="store_true", help="skip the meaning check (facts stay 'unchecked')")
    parser.add_argument("--gap-calls", type=int, default=24, help="most calls of the gap search; 0 turns it off")
    parser.add_argument("--enrich-calls", type=int, default=40, help="most calls of node enrichment; 0 turns it off")
    parser.add_argument("--pages", default="", help="extra PDF pages to read, comma-separated")
    parser.add_argument("--approval", choices=("automatic", "person"), default="automatic",
                        help="person: the finished graph waits for approval in the interface")
    parser.add_argument("--events", action="store_true", help="write interface events to <out>/events.jsonl")
    args = parser.parse_args()
    real = not (args.estimate or args.preflight or args.replay)
    if not args.estimate and not args.out:
        parser.error("--out is required unless --estimate is given")
    if real:
        if not (args.authorize_spend and args.budget and args.ledger):
            parser.error("real calls need --authorize-spend, --budget and --ledger; use --estimate to see the cost")
        ledger = Path(args.ledger).resolve()
        if any(ledger == (ROOT / name).resolve() for name in HISTORICAL_LEDGERS):
            parser.error("use a new ledger file: historical ledgers are preserved evidence")
    os.chdir(ROOT)  # settings read the API key from .env in the repository root
    report = asyncio.run(run(args))
    keys = ("plan", "preflight", "status", "pages", "text_pages", "headings", "printed_page_offset", "units",
            "failed_reads", "graph", "open_gaps",
            "estimated_cost_usd", "low", "high", "usage", "seconds", "provider_calls", "note")
    print(json.dumps({key: report[key] for key in keys if key in report}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
