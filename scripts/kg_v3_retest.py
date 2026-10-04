"""One command for the real re-test after the quality-profile fixes of 1 October 2026.

It runs the pipeline on development manuals, scores every run with the historical judge
(gpt-6-luna, reasoning low, three votes: the same scorer as campaign F and the pilot) and prints
branch recall next to the earlier numbers of the same manuals. Runs already finished are reused,
so the command can be started again after an interruption (for example an empty API balance).

    # Plan and cost estimate only, no API call:
    .venv/bin/python scripts/kg_v3_retest.py --dry-run
    # Real run, after recharging the provider balance:
    .venv/bin/python scripts/kg_v3_retest.py

Spending goes through the pilot's ledger and the cumulative cap authorized for these tests
(10 USD); the command never raises it. Outputs: experiments/kg_quality_retest/.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PILOT = ROOT / "experiments/kg_quality_pilot_20261001"
LEDGER = PILOT / "budget.jsonl"
BUDGET = "10"  # cumulative cap Fabio authorized for these tests (5 + 5 USD)
CEILING = "9.50"  # stop before the cap, leaving room for calls already in flight
OUT = ROOT / "experiments/kg_quality_retest"
PROFILES = {"ALL": ROOT / "docs/kg_quality/quality_v1.json", "Bsafe": ROOT / "docs/kg_quality/base_safe.json"}
# Rough cost per run in USD, from the pilot (Bsafe 0.16-0.23; ALL now reads like Bsafe plus review).
RUN_COST = {"ALL": 0.6, "Bsafe": 0.25}
JUDGE_COST = 0.15


def spent() -> float:
    """Cumulative amount in the ledger, open reservations included (not an invoice)."""
    from backend.services.real_call_budget_ledger import RealCallBudgetLedger

    snapshot = RealCallBudgetLedger(LEDGER, absolute_budget_usd=BUDGET).snapshot()
    return float(snapshot.committed_usd + snapshot.active_reserved_usd)


def run_dir(manual: str, profile: str, replica: int) -> Path:
    return OUT / manual / f"{profile}_r{replica}"


def extract(manual: str, profile: str, replica: int) -> bool:
    """One pipeline run, unless its graph already exists. False when the provider refused."""
    out = run_dir(manual, profile, replica)
    if (out / "graph.json").exists() and (out / "report.json").exists():
        print(f"  {manual} {profile} r{replica}: already done, reused")
        return True
    command = [sys.executable, str(ROOT / "scripts/kg_v3.py"), "--manual", manual, "--out", str(out),
               "--quality-config", str(PROFILES[profile]), "--gates", "agent", "--authorize-spend",
               "--budget", BUDGET, "--spend-ceiling", CEILING, "--ledger", str(LEDGER),
               "--run-id", f"retest_{manual}_{profile}_{replica}"]
    print(f"  {manual} {profile} r{replica}: running ...", flush=True)
    done = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    (out / "stdout.txt").parent.mkdir(parents=True, exist_ok=True)
    (out / "stdout.txt").write_text(done.stdout)
    (out / "stderr.txt").write_text(done.stderr)
    refused = "credit_balance_exhausted" in done.stderr or "insufficient_quota" in done.stderr
    if done.returncode != 0:
        print(f"    failed (exit {done.returncode}); see {out / 'stderr.txt'}")
    return not refused


def references() -> dict:
    """Earlier branch recall of the same manuals: campaign F and the pilot (same judge)."""
    refs: dict = {}
    kpi_f = json.loads((ROOT / "campaign/results/kpi_F.json").read_text())
    for manual, data in kpi_f["manuals"].items():
        refs.setdefault(manual, {})["F (before the K work)"] = [s["branch_recall"][0] for s in data["systems"].values()
                                                                 if s.get("branch_recall")]
    pilot = json.loads((PILOT / "additional_tests_v1/historical_scores.json").read_text())
    for row in pilot["rows"]:
        if row.get("branch_recall") and row.get("processing_status") == "PROCESSED":  # partial runs left out
            refs.setdefault(row["manual"], {}).setdefault(f"pilot {row['condition']} (before fixes)", []).append(
                row["branch_recall"][0])
    return refs


def table(results: dict, manuals: list[str]) -> str:
    refs = references()
    lines = ["| Manual | Measure | Branches recovered |", "|---|---|---|"]
    for manual in manuals:
        data = results["manuals"].get(manual)
        if not data:
            continue
        total = data["branches"]
        for name, values in refs.get(manual, {}).items():
            lines.append(f"| {manual} | {name} | {', '.join(str(v) for v in values)} / {total} |")
        for name, row in sorted(data["systems"].items()):
            hits = row["branch_recall"][0]
            lines.append(f"| {manual} | **{name.removeprefix('v3_')} (fixed code)** | "
                         f"**{hits} / {total} ({100 * hits / total:.1f}%)**, cost {row.get('cost_usd')} USD |")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manuals", default="grizzly_g0872,lg_lmh2235st")
    parser.add_argument("--profiles", default="ALL", help="comma-separated: ALL, Bsafe")
    parser.add_argument("--replicas", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true", help="print plan and estimate, no API call")
    args = parser.parse_args()
    manuals = [m.strip() for m in args.manuals.split(",") if m.strip()]
    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    todo = [(m, p, r) for m in manuals for p in profiles for r in range(1, args.replicas + 1)
            if not (run_dir(m, p, r) / "graph.json").exists()]
    estimate = sum(RUN_COST[p] for _, p, _ in todo) + JUDGE_COST * len(manuals) * len(profiles) * args.replicas
    print(f"Ledger {LEDGER.relative_to(ROOT)}: spent {spent():.2f} of {BUDGET} USD (stop at {CEILING}).")
    print(f"Runs to make: {len(todo)}; rough cost of runs and judge: {estimate:.2f} USD.")
    for item in todo:
        print("  -", *item)
    if args.dry_run:
        return 0
    for manual, profile, replica in todo:
        if not extract(manual, profile, replica):
            print("The provider refused for lack of credit: recharge the balance and start again.")
            return 2
    os.environ.update({"KG_LLM_MODE": "real", "KG_REAL_CALL_BUDGET_LEDGER": str(LEDGER),
                       "KG_REAL_CALL_BUDGET_USD": BUDGET, "KG_REAL_CALL_SPEND_CEILING_USD": CEILING,
                       "KG_REAL_CALL_RUN_ID": "retest_judge", "KG_REAL_CALL_PDF_ID": "evaluation",
                       "KG_LLM_TRACE_DIR": str(OUT / "judge/provider_responses")})
    os.chdir(ROOT)
    from scripts.kg_v3_kpi import evaluate

    results = asyncio.run(evaluate(manuals, OUT, runs_name="none", v3_only=True))
    (OUT / "kpi.json").write_text(json.dumps(results, indent=1) + "\n")
    report = table(results, manuals)
    (OUT / "RESULTS.md").write_text("# Re-test after the quality-profile fixes\n\n" + report + "\n")
    print(report)
    print(f"\nSpent so far {spent():.2f} of {BUDGET} USD. Details: {OUT.relative_to(ROOT)}/kpi.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
