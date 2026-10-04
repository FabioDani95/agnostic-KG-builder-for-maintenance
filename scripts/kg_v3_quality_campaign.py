"""Plan/run/score/report ablations in new directories; paid execution is explicit."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.kg_v3.quality_contracts import QualityConfig  # noqa: E402
from backend.kg_v3.run_state import atomic_json, file_hash, source_fingerprints, stable_id  # noqa: E402
from backend.services.model_pricing import MODEL_PRICING, estimate_cost_usd  # noqa: E402

CONDITIONS = {
    "Bsafe": QualityConfig(),
    "S": QualityConfig.quality_v1(
        semantic_merge_review=False,
        completeness_review=False,
        visual_routing=False,
        reference_retrieval=False,
        graph_review=False,
    ),
    "S+E": QualityConfig.quality_v1(
        completeness_review=False, visual_routing=False, reference_retrieval=False, graph_review=False
    ),
    "S+C": QualityConfig.quality_v1(
        semantic_merge_review=False, visual_routing=False, reference_retrieval=False, graph_review=False
    ),
    "S+V": QualityConfig.quality_v1(
        semantic_merge_review=False, completeness_review=False, reference_retrieval=False, graph_review=False
    ),
    "S+G": QualityConfig.quality_v1(semantic_merge_review=False, completeness_review=False, visual_routing=False),
    "ALL": QualityConfig.quality_v1(),
    "ALL-E": QualityConfig.quality_v1(semantic_merge_review=False),
    "ALL-C": QualityConfig.quality_v1(completeness_review=False),
    "ALL-V": QualityConfig.quality_v1(visual_routing=False),
    "ALL-G": QualityConfig.quality_v1(reference_retrieval=False, graph_review=False),
}


def plan(out, manuals, conditions, *, model="gpt-6-luna", replicas=3, baseline=None):
    if model not in MODEL_PRICING:
        raise ValueError("model has no verified local pricing profile")
    if out.exists():
        raise ValueError("campaign output exists; use a new directory")
    if replicas < 3:
        raise ValueError("campaign protocol requires at least three replicas")
    records, frozen = [], {}
    for name in manuals:
        directory = ROOT / "campaign" / name
        inputs = [directory / p for p in ("manual.pdf", "info.yaml", "gold/gold.json")]
        if any(not p.exists() for p in inputs):
            raise ValueError(f"missing corpus input for {name}")
        frozen[name] = {str(p): file_hash(p) for p in inputs}
        import fitz

        with fitz.open(inputs[0]) as pdf:
            pages = len(pdf)
            chars = sum(len(p.get_text()) for p in pdf)
        estimated_units = max(1, (chars + 8999) // 9000)
        for condition in conditions:
            if condition == "B0" and baseline is None:
                raise ValueError("B0 requires --baseline-source with a frozen complete executable checkout")
            cfg = CONDITIONS.get(condition)
            if condition != "B0" and cfg is None:
                raise ValueError(f"unknown condition {condition}")
            calls = {
                "map": 2 * ((pages + 19) // 20),
                "scan": max(1, (chars + 23999) // 24000),
                "extract": 2 * estimated_units,
                "verify": 2 * estimated_units,
                "merge": 34,
                "review": cfg.max_review_requests_per_document * cfg.max_review_rounds
                if cfg and (cfg.completeness_review or cfg.graph_review or cfg.reference_retrieval)
                else 0,
                "vision": pages * 2 if cfg and cfg.visual_routing else 0,
            }
            image_tokens = (calls["vision"] + calls["review"]) * 6 * 6000
            input_tokens = chars * 4 * 6 + sum(calls.values()) * (18000 * 4 + 4096) + image_tokens
            output_tokens = sum(calls.values()) * 8000
            # Estimates include retries/verifier; they are not a spending permission.
            cost = estimate_cost_usd(input_tokens * 3, output_tokens * 3, model_name=model)
            for replica in range(1, replicas + 1):
                records.append(
                    {
                        "manual": name,
                        "condition": condition,
                        "replica": replica,
                        "output": f"runs/{name}/{condition}/r{replica}",
                        "calls_estimated": calls,
                        "input_tokens_envelope": input_tokens * 3,
                        "output_tokens_envelope": output_tokens * 3,
                        "image_tokens_assumption_per_image": 6000,
                        "estimated_usd": cost,
                    }
                )
    out.mkdir(parents=True)
    for condition in conditions:
        if condition != "B0":
            atomic_json(out / "configs" / (condition + ".json"), CONDITIONS[condition])
    value = {
        "version": "kg-quality-campaign-1",
        "manuals": frozen,
        "matrix": records,
        "primary_model": model,
        "sources": source_fingerprints(),
        "scorer_sha256": file_hash(Path(__file__).with_name("kg_v3_quality_evaluate.py")),
        "pricing_basis": MODEL_PRICING[model],
        "pricing_source": "backend/services/model_pricing.py; local verified snapshot",
        "estimated_usd": sum(r["estimated_usd"] for r in records),
        "estimate_is_authorization": False,
        "estimate_limitations": "Planning estimates include configured retries/output/image assumptions; packet splits and provider billing need the runtime ledger. They are not guaranteed total bounds.",
        "paid_calls_authorized": False,
        "provider_calls": 0,
        "replicas": replicas,
        "baseline_source": str(baseline.resolve()) if baseline else None,
        "baseline_manifest_sha256": file_hash(baseline / "baseline_checkout_manifest.json") if baseline else None,
        "configs": {
            str((out / "configs" / (c + ".json")).resolve()): file_hash(out / "configs" / (c + ".json"))
            for c in conditions
            if c != "B0"
        },
        "campaign_runner_sha256": file_hash(Path(__file__)),
        "baseline_runner_sha256": file_hash(Path(__file__).with_name("kg_v3_baseline_run.py")),
        "exposure": "DEVELOPMENT",
        "seed": 1729,
        "bootstrap_replicates": 10000,
        "unmeasured": ["semantic_precision", "visual_path_accuracy", "branch_recall", "human_minutes"],
    }
    value["campaign_id"] = stable_id("campaign", [str(out.resolve()), value["sources"], value["manuals"], value["configs"]])
    atomic_json(out / "campaign_manifest.json", value)
    return value


def verify_inputs(manifest):
    for paths in manifest["manuals"].values():
        for p, sha in paths.items():
            if file_hash(Path(p)) != sha:
                raise ValueError(f"frozen campaign input changed: {p}")
    for p, sha in manifest.get("configs", {}).items():
        if file_hash(Path(p)) != sha:
            raise ValueError("campaign condition changed after planning")
    if (
        manifest.get("baseline_source")
        and file_hash(Path(manifest["baseline_source"]) / "baseline_checkout_manifest.json")
        != manifest["baseline_manifest_sha256"]
    ):
        raise ValueError("baseline manifest changed")
    if manifest.get("baseline_source"):
        baseline = Path(manifest["baseline_source"])
        checkout = json.loads((baseline / "baseline_checkout_manifest.json").read_text())
        for name, sha in checkout["files"].items():
            if file_hash(baseline / name) != sha:
                raise ValueError(f"baseline source changed: {name}")
    if manifest["sources"] != source_fingerprints():
        raise ValueError("campaign code/config changed after planning; prepare a new campaign")
    if manifest["scorer_sha256"] != file_hash(Path(__file__).with_name("kg_v3_quality_evaluate.py")):
        raise ValueError("scorer changed after planning")
    if manifest["campaign_runner_sha256"] != file_hash(Path(__file__)):
        raise ValueError("campaign runner changed after planning")
    if manifest["baseline_runner_sha256"] != file_hash(Path(__file__).with_name("kg_v3_baseline_run.py")):
        raise ValueError("baseline runner changed after planning")


def execute(out, manifest, *, authorization=None, replay=None, resume=False):
    verify_inputs(manifest)
    if replay is None:
        if (
            not authorization
            or authorization.get("authorized") is not True
            or not authorization.get("authorization_reference")
        ):
            raise ValueError("real run requires explicit budget authorization with reference, cap and ledger")
        if float(authorization.get("budget_usd", 0)) <= 0 or not authorization.get("ledger"):
            raise ValueError("positive authorized budget and shared ledger required")
        # B0 runs in its frozen checkout; every condition must spend from the
        # same ledger even when the operator supplies a repository-relative path.
        ledger = Path(authorization["ledger"]).expanduser()
        ledger = (ROOT / ledger).resolve() if not ledger.is_absolute() else ledger.resolve()
    results = []
    for row in manifest["matrix"]:
        dest = out / row["output"]
        if dest.exists() and not resume:
            raise ValueError(f"output exists: {dest}; use compatible --resume or new campaign")
        baseline = row["condition"] == "B0"
        executable_root = Path(manifest["baseline_source"]) if baseline else ROOT
        cmd = [
            sys.executable,
            str(executable_root / "scripts/kg_v3.py"),
            "--pdf",
            str(ROOT / "campaign" / row["manual"] / "manual.pdf"),
            "--info",
            str(ROOT / "campaign" / row["manual"] / "info.yaml"),
            "--out",
            str(dest.resolve()),
            "--model",
            manifest["primary_model"],
            "--gates",
            "agent",
        ]
        if not baseline:
            cmd.extend(["--quality-config", str((out / "configs" / (row["condition"] + ".json")).resolve())])
        if replay is not None:
            if baseline:
                cmd = [
                    sys.executable,
                    str(ROOT / "scripts/kg_v3_baseline_run.py"),
                    "--baseline-source",
                    str(executable_root),
                    "--replay",
                    str((replay / row["output"]).resolve()),
                    "--",
                    *cmd[2:],
                ]
            else:
                cmd.extend(["--replay", str((replay / row["output"]).resolve())])
        else:
            if not baseline:
                cmd.append("--authorize-spend")
            cmd.extend(
                [
                    "--budget",
                    str(authorization["budget_usd"]),
                    "--ledger",
                    str(ledger),
                    "--run-id",
                    manifest.get("campaign_id", stable_id("campaign", str(out.resolve())))
                    + "_" + row["manual"] + "_" + row["condition"] + "_" + str(row["replica"]),
                ]
            )
        outcome = subprocess.run(cmd, cwd=executable_root, capture_output=True, text=True)
        result = {
            **row,
            "exit_code": outcome.returncode,
            "command": cmd,
            "stdout": outcome.stdout,
            "stderr": outcome.stderr,
        }
        results.append(result)
        atomic_json(out / "execution.json", results)
    return results


def score_campaign(out, manifest, judgments_dir=None, score_out=None):
    verify_inputs(manifest)
    from backend.kg_v3.export import load_quality
    from scripts.kg_v3_quality_evaluate import (
        evaluation_bundle,
        legacy_predictions,
        project_gold,
        score,
        structural_metrics,
    )

    rows = []
    for row in manifest["matrix"]:
        run = out / row["output"]
        gold = json.loads((ROOT / "campaign" / row["manual"] / "gold/gold.json").read_text())
        if not (run / "graph.json").exists():
            projection = project_gold(gold)
            rows.append({**row, "status": "MISSING_RUN", "metrics": score(projection, [], [])})
            continue
        loaded = load_quality(run)
        judgment_path = (
            judgments_dir / row["manual"] / row["condition"] / f"r{row['replica']}.json" if judgments_dir else None
        )
        judgments = json.loads(judgment_path.read_text()) if judgment_path and judgment_path.exists() else {}
        gold = json.loads((ROOT / "campaign" / row["manual"] / "gold/gold.json").read_text())
        adjudication = judgments.get("adjudication", {})
        if adjudication and adjudication.get("gold_sha256") != file_hash(
            ROOT / "campaign" / row["manual"] / "gold/gold.json"
        ):
            raise ValueError("adjudication is not bound to frozen gold")
        if loaded["binding_status"] == "VERIFIED":
            bundle = evaluation_bundle(gold, loaded["quality"], adjudication, judgments)
            report_ = json.loads((run / "report.json").read_text())
            rows.append(
                {
                    **row,
                    "status": "SCORED_OFFLINE",
                    **bundle,
                    "operational": {
                        k: report_.get(k)
                        for k in (
                            "usage_total",
                            "usage",
                            "role_usage",
                            "seconds",
                            "gates",
                            "coverage_backlog",
                            "source_dispositions",
                            "validation",
                        )
                    },
                }
            )
        else:
            predictions, branches = legacy_predictions(
                loaded["graph"], adjudication, graph_sha256=file_hash(run / "graph.json")
            )
            projection = project_gold(gold, adjudication)
            mapping = [
                {
                    "gold_branch_id": b["branch_id"],
                    "branch_ids": adjudication.get("legacy_branch_alignment", {}).get(b["branch_id"], []),
                    "status": "VERIFIED"
                    if adjudication.get("legacy_branch_alignment", {}).get(b["branch_id"])
                    and all(
                        k in branches and branches[k]["scope_status"] == "VERIFIED_REVIEW"
                        for k in adjudication["legacy_branch_alignment"][b["branch_id"]]
                    )
                    else "AMBIGUOUS",
                }
                for b in projection["branches"]
            ]
            rows.append(
                {
                    **row,
                    "status": "LEGACY_ADJUDICATED"
                    if adjudication.get("legacy_fact_reviews")
                    else loaded["binding_status"],
                    "metrics": score(projection, predictions, mapping, judgments),
                    "predictions": predictions,
                    "reason": "SEPARATE_SOURCE_ADJUDICATION_REQUIRED; no certificates added to historical graph",
                    "structural": structural_metrics(loaded["graph"]),
                }
            )
    target = (score_out or out) / "scores.json"
    if target.exists():
        raise ValueError("score output exists; preserve it and use a new evaluation directory")
    atomic_json(target, rows)
    return rows


def report(out):
    rows = json.loads((out / "scores.json").read_text()) if (out / "scores.json").exists() else []
    groups = {}
    for row in rows:
        key = row["condition"]
        group = groups.setdefault(key, {"tp": 0, "fn": 0, "documents": [], "unjudged": 0})
        metrics = row.get("metrics", {})
        group["tp"] += metrics.get("tp", 0)
        group["fn"] += metrics.get("fn", 0)
        group["unjudged"] += metrics.get("unjudged", 0)
        group["documents"].append(
            {
                "manual": row["manual"],
                "replica": row["replica"],
                "recall": metrics.get("recall"),
                "status": row["status"],
            }
        )
    for group in groups.values():
        group["micro_recall"] = group["tp"] / (group["tp"] + group["fn"]) if group["tp"] + group["fn"] else None
        per_document = {}
        for row in group["documents"]:
            if row["recall"] is not None:
                per_document.setdefault(row["manual"], []).append(row["recall"])
        group["macro_document_recall"] = (
            sum(sum(v) / len(v) for v in per_document.values()) / len(per_document) if per_document else None
        )
        group["replica_ranges"] = {m: [min(v), max(v)] for m, v in per_document.items()}
    return {
        "conditions": groups,
        "promotion": "NOT_EVALUATED",
        "semantic_precision_measured": False,
        "historical_branch_score": "separate existing scorer; never run implicitly",
        "provider_calls_in_report": 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["plan", "run", "score", "report"])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--manuals", nargs="+")
    parser.add_argument("--conditions", nargs="+", default=["B0", "Bsafe", "S", "S+E", "S+C", "S+V", "S+G", "ALL"])
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--replicas", type=int, default=3)
    parser.add_argument("--baseline-source", type=Path)
    parser.add_argument("--budget-authorization", type=Path)
    parser.add_argument("--replay", type=Path)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--judgments", type=Path)
    parser.add_argument("--score-out", type=Path, help="new evaluation directory for repeated scoring")
    args = parser.parse_args()
    if args.operation == "plan":
        if not args.manuals:
            parser.error("--manuals required for plan")
        result = plan(
            args.out,
            args.manuals,
            args.conditions,
            model=args.model,
            replicas=args.replicas,
            baseline=args.baseline_source,
        )
    elif args.operation == "report":
        result = report(args.out)
    else:
        manifest = json.loads((args.out / "campaign_manifest.json").read_text())
        if args.operation == "run":
            auth = json.loads(args.budget_authorization.read_text()) if args.budget_authorization else None
            result = execute(args.out, manifest, authorization=auth, replay=args.replay, resume=args.resume)
        else:
            result = score_campaign(args.out, manifest, args.judgments, args.score_out)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
