"""Run the V3 PDF-to-graph pipeline from the command line.

Every model call goes through the archived, budgeted gateway. A run directory
keeps the state of each station, so running the same command again resumes
instead of repeating calls. ``--gates agent`` lets agents answer every gate;
``--gates interactive`` leaves doubts and approval to a person.

Example:
    .venv/bin/python scripts/kg_v3.py --manual graco_gtx_2000ex --out runs/v3/graco --gates agent
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CAMPAIGN = ROOT / "campaign"
# The V3 campaign has its own ledger and a 20 USD cap for every call it makes.
DEFAULT_LEDGER = CAMPAIGN / "real_call_budget.jsonl"
DEFAULT_BUDGET = "20"
GATE_PRESETS = {
    # An agent cannot judge a whole graph from its summary: in unattended runs
    # the approval is automatic and recorded as such.
    "agent": {"map": ["agent"], "doubts": ["agent"], "approval": ["auto"]},
    "auto": {"map": ["auto"], "doubts": ["auto"], "approval": ["auto"]},
    "interactive": {"map": ["agent"], "doubts": ["agent", "human"], "approval": ["human"]},
    # Runs started from the interface: the approval is the person's button, never automatic.
    "ui-agent": {"map": ["agent"], "doubts": ["agent"], "approval": []},
    "ui-interactive": {"map": ["agent"], "doubts": ["agent", "human"], "approval": []},
    "ui-human": {"map": ["agent"], "doubts": ["human"], "approval": []},
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
    """PDF and machine identity of a campaign manual (campaign/<id>)."""

    from scripts.campaign import asset

    if not (CAMPAIGN / manual_id / "info.yaml").exists():
        raise SystemExit(f"unknown manual {manual_id!r}: create it with scripts/campaign.py new")
    return CAMPAIGN / manual_id / "manual.pdf", asset(manual_id)


def info_asset(path: Path) -> dict:
    """Machine identity from an info.yaml written like the campaign's."""

    import yaml

    machine = yaml.safe_load(path.read_text(encoding="utf-8"))["machine"]
    return {"name": machine["name"], "description": machine["name"], "brand": machine.get("brand", "not_stated"),
            "model": machine.get("model", "not_stated"), "asset_type": machine.get("type", "not_stated")}


USAGE_SUMS = ("calls", "failed_calls", "prompt_tokens", "completion_tokens", "estimated_cost_usd")


def with_earlier_attempts(report: dict, earlier: dict | None) -> dict:
    """A resumed run reports all its attempts: step times and model usage add up, so a resume
    (which reuses the saved state and costs almost nothing) does not hide what the run took."""

    if not earlier:
        return {**report, "attempts": 1}
    seconds = {key: round(float((earlier.get("seconds") or {}).get(key, 0.0)) + float(value), 3)
               for key, value in (report.get("seconds") or {}).items()}
    for key, value in (earlier.get("seconds") or {}).items():
        seconds.setdefault(key, value)
    merged = {**report, "seconds": seconds, "attempts": int(earlier.get("attempts") or 1) + 1}
    for field in ("usage", "agent_usage", "usage_total"):
        now, before = report.get(field) or {}, earlier.get(field) or {}
        if not now and not before:
            continue
        total = {**before, **now}
        for key in USAGE_SUMS:
            if key in now or key in before:
                total[key] = round(float(before.get(key) or 0) + float(now.get(key) or 0), 6)
                if key != "estimated_cost_usd":
                    total[key] = int(total[key])
        operations = dict(before.get("by_operation") or {})
        for name, count in (now.get("by_operation") or {}).items():
            operations[name] = operations.get(name, 0) + count
        if operations:
            total["by_operation"] = dict(sorted(operations.items()))
        merged[field] = total
    merged['call_provenance'] = [*earlier.get('call_provenance', []), *report.get('call_provenance', [])]
    roles = {}
    for role in set(earlier.get('role_usage', {})) | set(report.get('role_usage', {})):
        roles[role] = with_earlier_attempts({'usage': report.get('role_usage', {}).get(role, {})}, {'usage': earlier.get('role_usage', {}).get(role, {})})['usage']
    if roles:
        merged['role_usage'] = roles
    return merged


async def run(args) -> dict:
    started = time.perf_counter()
    if args.manual:
        pdf, asset = manual_source(args.manual)
    else:
        pdf = Path(args.pdf).resolve()
        asset = {"name": args.asset_name or pdf.stem, "description": args.asset_name or pdf.stem,
                 "brand": "not_stated", "model": "not_stated", "asset_type": "not_stated"}
        if args.info:
            asset = info_asset(Path(args.info))
    out = Path(args.out)
    out = (out if out.is_absolute() else ROOT / out).resolve()
    resumed = (out / "state").exists()
    out.mkdir(parents=True, exist_ok=True)
    on_event = None
    if args.events:
        from backend.ui.events import EventLog

        on_event = EventLog(out / "events.jsonl")
        manual_id = args.manual or (Path(args.info).resolve().parent.name if args.info else pdf.stem)
        on_event("run_started", {"manual_id": manual_id, "version_id": out.name,
                                 "mode": "resume" if resumed else "live"})
        on_event("step_started", {"step": "pdf_read"})
    try:
        from backend.kg_v3.run_state import run_lock
        with run_lock(out):
            return await _run(args, pdf, asset, out, started, on_event)
    except BaseException as error:
        if on_event is not None:
            on_event("run_failed", {"message": f"{type(error).__name__}: {error}"})
        raise


async def _run(args, pdf: Path, asset: dict, out: Path, started: float, on_event) -> dict:
    from backend.kg_v3.export import write_exports
    from backend.kg_v3.llm import ModelClient
    from backend.kg_v3.quality_contracts import QualityConfig
    from backend.kg_v3.reader import read_document
    from backend.kg_v3.reviewers import InMemoryQuestionStore, render_question
    from backend.kg_v3.run import Pipeline, RunConfig
    from backend.kg_v3.run_state import atomic_bytes
    quality_path = getattr(args, 'quality_config', None)
    quality = QualityConfig.model_validate_json(Path(quality_path).read_text()) if quality_path else QualityConfig()
    replay_path = getattr(args, 'replay', None)
    if quality_path and not replay_path and not getattr(args, 'preflight', False) and not getattr(args, 'authorize_spend', False):
        raise ValueError('quality real calls require --authorize-spend and an explicitly authorised --budget/--ledger')
    Path(args.ledger).resolve().parent.mkdir(parents=True, exist_ok=True)
    evidence, page_count, sha = load_evidence(pdf, asset)
    os.environ.update({
        "KG_LLM_MODE": "real", "KG_LLM_TRACE_DIR": str(out / "provider_responses"),
        "KG_REAL_CALL_BUDGET_LEDGER": str(Path(args.ledger).resolve()),
        "KG_REAL_CALL_BUDGET_USD": str(args.budget), "KG_REAL_CALL_RUN_ID": args.run_id or out.name,
        "KG_REAL_CALL_PDF_ID": f"sha256:{sha}",
    })
    doc = read_document(list(evidence), page_count=page_count)
    from backend.kg_v3.mapper import attach_pdf_sections

    attach_pdf_sections(doc, pdf)
    read_seconds = time.perf_counter() - started
    if on_event is not None:
        on_event("step_finished", {"step": "pdf_read", "seconds": round(read_seconds, 3)})
    config = RunConfig(quality=quality, asset_scope_id=getattr(args, 'asset_scope_id', '') or asset['name'], model=args.model, reasoning_effort=args.reasoning, reads=args.reads,
                       gates=GATE_PRESETS[args.gates], agent_model=args.agent_model,
                       agent_reasoning_effort=args.agent_reasoning, human_question_budget=args.human_questions)
    provider_factory = None
    if getattr(args, 'preflight', False):
        class PreflightProvider:
            def __init__(self):
                from types import SimpleNamespace
                self.chat = SimpleNamespace(completions=self)
            async def create(self, **_kwargs):
                raise AssertionError('preflight must never call a provider')
        provider_factory = PreflightProvider
    if replay_path:
        from backend.kg_v3.replay import ReplayProvider
        replay_provider = ReplayProvider(Path(replay_path))
        def provider_factory():
            return replay_provider
    llm = ModelClient(model=args.model, reasoning_effort=args.reasoning, client_factory=provider_factory)
    agent_llm = ModelClient(model=args.agent_model, reasoning_effort=args.agent_reasoning, client_factory=provider_factory)
    roles = {}
    if replay_path or getattr(args, 'preflight', False):
        roles = {role: ModelClient(model=getattr(quality, role + '_model') or args.model,
                                  reasoning_effort=getattr(quality, role + '_reasoning'), client_factory=provider_factory)
                 for role in ('review', 'verify', 'vision')}
    if args.human_store:
        from backend.ui.store import STORE_NAME, FileQuestionStore

        store = FileQuestionStore(out / STORE_NAME, budget=config.human_question_budget)
    else:
        store = InMemoryQuestionStore()
    pipeline = Pipeline(doc=doc, pdf_path=pdf, asset_name=asset['name'], llm=llm, config=config, agent_llm=agent_llm,
                        human_store=store, workdir=out, on_event=on_event, role_clients=roles)
    if getattr(args, 'preflight', False):
        pipeline._prepare()
        return {'preflight': 'READY', 'profile': quality.profile, 'role_profiles': pipeline.role_profiles,
                'provider_calls': 0, 'quality_measured': False}
    result = await pipeline.run(lock_held=True)
    result.report["seconds"].update(pdf_read=round(read_seconds, 3),
                                    end_to_end=round(time.perf_counter() - started, 3))
    earlier = json.loads((out / 'report.json').read_text()) if (out / 'report.json').exists() else None
    result.report = with_earlier_attempts(result.report, earlier)
    result.report['execution_mode'] = 'exact_replay' if replay_path else 'real'
    graph = write_exports(out, result, doc, asset=asset, source_title=pdf.name)
    pending = store.open_questions()
    atomic_bytes(out / 'questions_for_people.txt', '\n\n'.join(render_question(q) for q in pending).encode())
    if on_event is not None:
        on_event("run_finished", {"graph": graph, "status": result.status, "open_questions": len(pending)})
    return result.report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--manual", help="manual ID of a campaign folder (campaign/<id>)")
    source.add_argument("--pdf", help="path to any PDF")
    parser.add_argument("--asset-name", default="")
    parser.add_argument("--info", help="info.yaml with the machine identity, for --pdf")
    parser.add_argument("--events", action="store_true", help="write interface events to <out>/events.jsonl")
    parser.add_argument("--human-store", action="store_true",
                        help="keep questions for a person and their answers in <out>/people.json")
    parser.add_argument('--quality-config', help='versioned quality configuration; opt-in P1')
    parser.add_argument('--asset-scope-id', default='')
    parser.add_argument('--preflight', action='store_true', help='validate input/config/manifest without provider calls')
    parser.add_argument('--replay', help='exact archived provider responses; cache misses never call network')
    parser.add_argument('--authorize-spend', action='store_true', help='explicitly permit real quality calls under the supplied budget')
    parser.add_argument("--out", required=True)
    parser.add_argument("--gates", choices=sorted(GATE_PRESETS), default="agent")
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--reasoning", default="low")
    parser.add_argument("--reads", type=int, default=2)
    parser.add_argument("--agent-model", default="gpt-6-luna")
    parser.add_argument("--agent-reasoning", default="medium")
    parser.add_argument("--human-questions", type=int, default=10, help="most questions a person gets in this run")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--budget", default=DEFAULT_BUDGET)
    parser.add_argument("--run-id", default="")
    parser.add_argument("--spend-ceiling", help="stricter cumulative cap without changing the campaign ledger budget")
    args = parser.parse_args()
    if args.quality_config and args.authorize_spend and '--budget' not in sys.argv:
        parser.error('real quality runs require an explicitly supplied --budget')
    if args.spend_ceiling:
        os.environ["KG_REAL_CALL_SPEND_CEILING_USD"] = args.spend_ceiling
    os.chdir(ROOT)  # settings read the API key from .env in the repository root
    report = asyncio.run(run(args))
    print(json.dumps({key: report[key] for key in ("preflight", "status", "units", "failed_reads", "graph", "gates", "usage", "seconds") if key in report},
                     indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
