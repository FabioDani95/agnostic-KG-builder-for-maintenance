"""Phased benchmark runner for the multi-agent ontology pipeline.

Runs scoping, ontology draft, and/or legacy triplet extraction against a PDF
in the manuals/ folder without going through the HTTP layer. Produces a
structured JSON report with per-phase counts, durations, and cost estimates
so runs can be compared across manuals and configurations.

Usage
-----
    python -m scripts.run_manual_benchmark \\
        --pdf manuals/alex_duetto_3_owners_manual.pdf \\
        --page-offset 1 \\
        --phase scoping

Phases
------
- scoping        → only the cut-plan workflow (cheap, LLM calls small)
- ontology       → ontology draft (requires scoping to have run first in the same invocation)
- extract        → legacy triplet extraction (requires scoping)
- all            → scoping → ontology → extract, sequentially
- scoping+ontology → the two new-flow phases without the legacy triplet extraction

Notes
-----
- Uses the real OPENAI_API_KEY from the environment via backend.config.settings.
- Logs everything at INFO level so per-step progress is visible.
- Reports are written to benchmark_runs/<timestamp>_<manual>_<phase>.json.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import shutil
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )
    # Silence noisy HTTP libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _build_store(pdf_path: Path) -> dict:
    """Replicate the side effects of POST /api/load-manual without FastAPI."""
    from backend.graph.store import seed_graph_state
    from backend.routers.upload import DATA_DIR, pdf_store
    from backend.services.pdf_service import extract_text_by_page
    from backend.services.run_metrics import ensure_run_metrics

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pdf_id = str(uuid.uuid4())
    target = DATA_DIR / f"{pdf_id}.pdf"
    shutil.copy2(str(pdf_path), str(target))

    pages = extract_text_by_page(str(target))
    if not pages:
        raise RuntimeError(f"Could not extract text from PDF: {pdf_path}")

    store = {
        "pdf_id": pdf_id,
        "filename": pdf_path.name,
        "pdf_path": str(target),
        "pages": pages,
        "page_count": len(pages),
        "source_type": "",
        "source_title": "",
        "selected_models": {
            "scoping": None,
            "ontology_draft": None,
            "extraction": None,
        },
    }
    pdf_store[pdf_id] = store
    ensure_run_metrics(store)
    seed_graph_state(store, pdf_id)
    return store


# ─── Phase runners ──────────────────────────────────────────────────────────

def _run_scoping_phase(store: dict, page_offset: int, model_name: str) -> dict:
    from backend.agents.scoping_agent import run_scoping_agent
    from backend.models import CutPlanRequest

    req = CutPlanRequest(
        pdf_id=store["pdf_id"],
        model_name=model_name,
        page_offset=page_offset,
    )
    t0 = time.perf_counter()
    cut_plan = run_scoping_agent(store, req)
    duration = round(time.perf_counter() - t0, 2)

    # Approve the cut plan so downstream phases can pick it up
    from backend.models import CutPlanApproval, CutPlanApprovalSection
    from backend.services.scoping_workflow import approve_cut_plan_workflow

    approval = CutPlanApproval(
        pdf_id=store["pdf_id"],
        pages_to_keep=cut_plan.pages_to_keep,
        page_offset=page_offset,
        sections=[
            CutPlanApprovalSection(
                name=section.name,
                page_range=section.page_range,
                source=section.source,
            )
            for section in cut_plan.sections
        ],
    )
    approve_cut_plan_workflow(store, approval)

    stage_metrics = store.get("run_metrics", {}).get("stages", {}).get("scoping", {})

    report = {
        "phase": "scoping",
        "duration_seconds": duration,
        "total_pages": cut_plan.total_pages,
        "selected_pages": len(cut_plan.pages_to_keep),
        "pages_to_keep": cut_plan.pages_to_keep,
        "sections": [
            {
                "name": section.name,
                "start": section.page_range.start,
                "end": section.page_range.end,
                "source": section.source,
            }
            for section in cut_plan.sections
        ],
        "product_info": cut_plan.product_info.model_dump() if cut_plan.product_info else None,
        "toc_found": cut_plan.toc is not None,
        "toc_entries": len(cut_plan.toc.entries) if cut_plan.toc else 0,
        "skipped": cut_plan.skipped,
        "llm_calls": stage_metrics.get("llm_calls", 0),
        "total_tokens": stage_metrics.get("total_tokens", 0),
        "prompt_tokens": stage_metrics.get("prompt_tokens", 0),
        "completion_tokens": stage_metrics.get("completion_tokens", 0),
        "estimated_cost_usd": stage_metrics.get("estimated_cost_usd", 0.0),
        "models": stage_metrics.get("models", []),
    }
    return report


async def _run_ontology_phase(store: dict, model_name: str, target_language: str) -> dict:
    from backend.agents.ontology_draft_agent import run_ontology_draft_agent
    from backend.models import OntologyDraftRequest

    req = OntologyDraftRequest(
        pdf_id=store["pdf_id"],
        source_type=store.get("source_type") or "Owner's manual",
        source_title=store.get("source_title") or store["filename"],
        model_name=model_name,
        pages_to_keep=None,  # fall back to cut_plan.pages_to_keep
        target_language=target_language,
    )
    t0 = time.perf_counter()
    result = await run_ontology_draft_agent(store, req)
    duration = round(time.perf_counter() - t0, 2)

    stage_metrics = store.get("run_metrics", {}).get("stages", {}).get("ontology", {})

    nodes_by_type = {
        node_type: len(node_list)
        for node_type, node_list in (result.ontology.nodes or {}).items()
    }
    total_nodes = sum(nodes_by_type.values())
    total_relations = len(result.ontology.relations or [])

    confidence_summary = None
    if result.confidence_report is not None:
        confidence_summary = {
            "theta_high": result.confidence_report.theta_high,
            "theta_low": result.confidence_report.theta_low,
            "auto_reject_enabled": result.confidence_report.auto_reject_enabled,
            "counts": dict(result.confidence_report.counts or {}),
            "entries_by_classification": {
                classification: [
                    {
                        "node_type": entry.node_type,
                        "node_id": entry.node_id,
                        "score": entry.score,
                        "reasons": entry.reasons,
                    }
                    for entry in result.confidence_report.entries
                    if entry.classification == classification
                ]
                for classification in ("auto_approve", "human_review", "auto_reject")
            },
        }

    report = {
        "phase": "ontology",
        "duration_seconds": duration,
        "status": result.status,
        "total_nodes": total_nodes,
        "nodes_by_type": nodes_by_type,
        "total_relations": total_relations,
        "relations_by_name": _count_by(result.ontology.relations, key=lambda r: r.name),
        "semantic_issues": len(result.semantic_issues),
        "schema_issues": len(result.schema_issues),
        "schema_issues_detail": [
            {"severity": i.severity, "code": i.code, "message": i.message,
             "target_type": i.target_type, "target_id": i.target_id}
            for i in result.schema_issues
        ],
        "graph_issues": len(result.graph_issues),
        "suggested_relations": len(result.suggested_relations),
        "human_required_fields": len(result.human_required_fields),
        "retry_count": result.retry_count,
        "is_schema_compliant": result.is_schema_compliant,
        "confidence": confidence_summary,
        "llm_calls": stage_metrics.get("llm_calls", 0),
        "total_tokens": stage_metrics.get("total_tokens", 0),
        "prompt_tokens": stage_metrics.get("prompt_tokens", 0),
        "completion_tokens": stage_metrics.get("completion_tokens", 0),
        "estimated_cost_usd": stage_metrics.get("estimated_cost_usd", 0.0),
        "chunk_count": stage_metrics.get("details", {}).get("chunk_count"),
    }
    return report


def _run_extract_phase(store: dict, model_name: str, target_language: str) -> dict:
    from backend.agents.extraction_agent import run_extraction_agent
    from backend.models import ExtractRequest

    req = ExtractRequest(
        pdf_id=store["pdf_id"],
        source_type=store.get("source_type") or "Owner's manual",
        source_title=store.get("source_title") or store["filename"],
        model_name=model_name,
        pages_to_keep=None,  # fall back to cut_plan.pages_to_keep
        target_language=target_language,
    )
    t0 = time.perf_counter()
    result = run_extraction_agent(store, req)
    duration = round(time.perf_counter() - t0, 2)

    stage_metrics = store.get("run_metrics", {}).get("stages", {}).get("extraction", {})

    triplets = getattr(result, "triplets", []) or []
    triplet_count = len(triplets)
    total_fm = sum(len(t.failure_modes) for t in triplets)
    total_ca = sum(len(t.corrective_actions) for t in triplets)

    return {
        "phase": "extract",
        "duration_seconds": duration,
        "triplet_count": triplet_count,
        "total_symptoms": triplet_count,
        "total_failure_modes": total_fm,
        "total_corrective_actions": total_ca,
        "llm_calls": stage_metrics.get("llm_calls", 0),
        "total_tokens": stage_metrics.get("total_tokens", 0),
        "prompt_tokens": stage_metrics.get("prompt_tokens", 0),
        "completion_tokens": stage_metrics.get("completion_tokens", 0),
        "estimated_cost_usd": stage_metrics.get("estimated_cost_usd", 0.0),
    }


def _count_by(items, key) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items or []:
        k = key(item)
        counts[k] = counts.get(k, 0) + 1
    return counts


# ─── CLI ────────────────────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pdf", required=True, help="Path to PDF (relative to repo root)")
    parser.add_argument("--page-offset", type=int, default=0, help="Offset between manual pages and absolute PDF pages")
    parser.add_argument(
        "--phase",
        choices=["scoping", "ontology", "extract", "scoping+ontology", "all"],
        default="scoping",
        help="Which phase(s) to run",
    )
    parser.add_argument("--model", default=None, help="Override model name (defaults to backend default)")
    parser.add_argument("--target-language", default="en")
    parser.add_argument("--output-dir", default="benchmark_runs")
    parser.add_argument("--log-level", default="INFO")
    return parser.parse_args()


async def _main_async() -> int:
    args = _parse_args()
    _setup_logging(args.log_level)
    logger = logging.getLogger("benchmark")

    pdf_path = (REPO_ROOT / args.pdf).resolve()
    if not pdf_path.exists():
        logger.error("PDF not found: %s", pdf_path)
        return 2

    from backend.app_config import get_confidence_config, get_effective_reflective_loop_config
    from backend.config import settings as _settings  # noqa: F401 — ensure env is loaded

    model_name = args.model or _settings.MODEL_NAME

    logger.info("=" * 70)
    logger.info("Benchmark run — %s", pdf_path.name)
    logger.info("  page_offset=%d  phase=%s  model=%s", args.page_offset, args.phase, model_name)
    logger.info("  reflective_loop=%s", get_effective_reflective_loop_config())
    logger.info("  confidence_enabled=%s", get_confidence_config().get("enabled"))
    logger.info("=" * 70)

    store = _build_store(pdf_path)
    logger.info("Store ready — pdf_id=%s pages=%d", store["pdf_id"], store["page_count"])

    report: dict = {
        "started_at": _now_iso(),
        "pdf": str(pdf_path.relative_to(REPO_ROOT)),
        "page_offset": args.page_offset,
        "phase": args.phase,
        "model": model_name,
        "reflective_loop": get_effective_reflective_loop_config(),
        "confidence_enabled": get_confidence_config().get("enabled"),
        "stages": {},
    }

    phases_to_run = {
        "scoping": ["scoping"],
        "ontology": ["scoping", "ontology"],
        "extract": ["scoping", "extract"],
        "scoping+ontology": ["scoping", "ontology"],
        "all": ["scoping", "ontology", "extract"],
    }[args.phase]

    try:
        if "scoping" in phases_to_run:
            logger.info("─── Phase: scoping ───")
            report["stages"]["scoping"] = _run_scoping_phase(store, args.page_offset, model_name)

        # Stop here if user only asked for scoping
        if args.phase == "scoping":
            pass
        else:
            if "ontology" in phases_to_run:
                logger.info("─── Phase: ontology draft ───")
                report["stages"]["ontology"] = await _run_ontology_phase(store, model_name, args.target_language)

            if "extract" in phases_to_run:
                logger.info("─── Phase: legacy triplet extraction ───")
                report["stages"]["extract"] = _run_extract_phase(store, model_name, args.target_language)
    except Exception as exc:
        logger.exception("Phase failed: %s", exc)
        report["error"] = str(exc)

    report["finished_at"] = _now_iso()

    output_dir = (REPO_ROOT / args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = pdf_path.stem.replace(" ", "_")
    output_path = output_dir / f"{timestamp}_{stem}_{args.phase}.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    logger.info("Report written to %s", output_path.relative_to(REPO_ROOT))

    # Pretty summary on stdout
    print("\n" + "=" * 70)
    print(f"BENCHMARK SUMMARY — {pdf_path.name} (phase={args.phase})")
    print("=" * 70)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if "error" not in report else 1


def main() -> int:
    return asyncio.run(_main_async())


if __name__ == "__main__":
    sys.exit(main())
