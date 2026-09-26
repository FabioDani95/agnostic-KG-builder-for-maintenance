"""Read-only run analysis; historical lexical probes are not semantic gold.

The generator never imports this module. Output is written to a separate
analysis directory; frozen graph, responses, source stores and gold are untouched.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def normalized(value):
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", str(value or ""))).strip()


def historical_tools():
    path = ROOT / "artifacts/acceptance/g3/diagnostic_benchmark_second_hardening_20260813/analyze_campaign.py"
    spec = importlib.util.spec_from_file_location("historical_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    wrapped = module._load()
    return wrapped, wrapped._load_frozen_analyzer()


def historical_probe(graph, spec, paths, analyzer):
    evidence = {e["evidence_id"]: e for e in graph["evidence"]}
    witnesses = []
    neighbours = {}
    for claim in spec["expected_claims"]:
        if claim.get("expected_gap") == "inspection_only":
            candidates = [(min(analyzer.score_expected_gap(claim, analyzer.gap_text(gap, evidence)).values()), gap.get("target_id")) for gap in graph["knowledge_gaps"] if gap.get("code") == "pdf_diagnostic_record_gap"]
            best = max(candidates, default=(0, None), key=lambda x: x[0])
            witnesses.append({"claim_id": claim["claim_id"], "kind": "expected_gap", "present": best[0] >= .55, "score": best[0], "target_id": best[1]})
            continue
        candidates = []
        for path in paths:
            scores = analyzer.score_claim_path(claim, path)
            candidates.append((min(scores.values()), path, scores))
        best = max(candidates, default=(0, {}, {}), key=lambda x: x[0])
        neighbours[claim["claim_id"]] = sorted({p["branch_lineage_id"] for score, p, _ in candidates if score >= .55 and set(claim["pages"]) & set(p["pages"])})
        witnesses.append({"claim_id": claim["claim_id"], "kind": "published_path", "present": best[0] >= .55, "score": best[0], "field_scores": best[2], "best_path": best[1]})
    assigned = {}
    def augment(claim, seen):
        for branch in neighbours[claim]:
            if branch in seen:
                continue
            seen.add(branch)
            if branch not in assigned or augment(assigned[branch], seen):
                assigned[branch] = claim
                return True
        return False
    for claim in neighbours:
        augment(claim, set())
    return {
        "status": "historical_lexical_probe_not_validated_quality",
        "gold_total": len(spec["expected_claims"]),
        "autonomous_probe": sum(w["present"] for w in witnesses if w["kind"] == "published_path"),
        "expected_gap_probe": sum(w["present"] for w in witnesses if w["kind"] == "expected_gap"),
        "one_to_one_source_page_branch_probe": len(assigned), "one_to_one_assignments": assigned,
        "witnesses": witnesses,
        "semantic_precision": None, "semantic_recall": None,
    }


def grounding(graph, run):
    with sqlite3.connect((run / "operational.db").resolve().as_uri() + "?mode=ro", uri=True) as conn:
        units = {u["evidence_id"]: u for (raw,) in conn.execute("SELECT payload_json FROM evidence_units") if (u := json.loads(raw))}
    failures, refs = [], 0
    for relation in graph["relations"]:
        if not relation.get("evidence_refs"):
            failures.append({"relation": relation["relation_id"], "error": "no_refs"})
        for ref in relation.get("evidence_refs", []):
            refs += 1
            unit = units.get(ref["evidence_id"], {})
            locator = unit.get("locator", {})
            valid = (ref["source_anchor"] == ref["evidence_id"] and ref.get("locator", {}).get("page") == locator.get("page") and normalized(ref["quote"]) in normalized(locator.get("quote")) and bool(normalized(ref["quote"])))
            if not valid:
                failures.append({"relation": relation["relation_id"], "ref": ref, "error": "canonical_ref_mismatch"})
    return {"references": refs, "failures": failures, "all_refs_literal_in_canonical_source": not failures, "semantic_support_verified": False}


def review_packet(graph, paths, target):
    lines = ["# Catene estratte da verificare", "", "Predizioni non approvate da tecnici. Pagine fisiche, base 1. Questo fascicolo va aperto dopo l'annotazione indipendente del gold.", ""]
    records = {e["branch_lineage_id"]: e for e in graph.get("diagnostic_compilation_ledger", {}).get("records", [])}
    grouped = defaultdict(list)
    for path in paths:
        grouped[path["branch_lineage_id"]].append(path)
    for number, (branch, items) in enumerate(sorted(grouped.items()), 1):
        entry = records.get(branch, {})
        candidate = entry.get("candidate") or {}
        lines += [f"## Ramo {number}", "", f"ID: `{branch}`. Pagine: {sorted({p for item in items for p in item['pages']})}.", ""]
        lines += [f"- {p['indicator']} → {p['failure_mode']} → {p['corrective_action']}" for p in items]
        lines += ["", "Ispezioni e condizioni:", "", "```json", json.dumps({k: candidate.get(k, []) for k in ("inspection_steps", "conditions")}, ensure_ascii=False, indent=2), "```", "", "Evidenze del record e dei collegamenti:", "", "```json", json.dumps(entry.get("validated_record") or candidate, ensure_ascii=False, indent=2), "```", ""]
    target.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign", type=Path, required=True)
    parser.add_argument("--output", type=Path, help="Separate output directory for a follow-up; preserves earlier analyses")
    args = parser.parse_args()
    campaign = args.campaign.resolve()
    out = args.output.resolve() if args.output else campaign / "analysis"
    out.mkdir(parents=True, exist_ok=True)
    events = [json.loads(line) for line in (campaign / "real_call_budget.jsonl").read_text().splitlines()]
    reservations = {e["call_id"]: e for e in events if e["event"] == "call_reserved"}
    finalized = {e["call_id"]: e for e in events if e["event"] == "call_finalized"}
    costs = defaultdict(lambda: {"calls": 0, "charged_usd": 0., "observed_estimated_usd": 0., "unknown_usage_calls": 0, "failed_calls": 0, "prompt_tokens": 0, "completion_tokens": 0})
    for call, event in finalized.items():
        cost = costs[reservations[call]["run_id"]]
        cost["calls"] += 1
        cost["charged_usd"] += event["charged_cost_usd"]
        cost["observed_estimated_usd"] += event.get("actual_cost_usd") or 0
        cost["unknown_usage_calls"] += event.get("actual_usage") is None
        cost["failed_calls"] += event["status"] != "succeeded"
        for key in ("prompt_tokens", "completion_tokens"):
            cost[key] += (event.get("actual_usage") or {}).get(key, 0)
    golden = ROOT / "artifacts/acceptance/g3/diagnostic_benchmark_20260812/golden.json"
    specs = {s["manual_id"]: s for s in read(golden)["manuals"]}
    wrapped, analyzer = historical_tools()
    rows = []
    for run in sorted((campaign / "runs").iterdir()):
        if not (run / "runtime_profile.json").exists():
            rows.append({"run_id": run.name, "status": "local_setup_failed_no_profile", "cost": costs[run.name]})
            continue
        profile = read(run / "runtime_profile.json")
        timing = read(run / "timing.json")
        row = {"run_id": run.name, "manual_id": profile["manual_id"], "status": timing["status"], "elapsed_seconds": timing.get("total_elapsed_seconds"), "code_sha256": profile["code_sha256"], "model": profile["arguments"]["model"], "packet_pages": profile["arguments"].get("packet_pages"), "cost": costs[run.name]}
        archive = [read(p) for p in (run / "provider_responses").glob("*.json")]
        row["response_archives"] = {"count": len(archive), "response_available": sum(bool(a.get("response")) for a in archive), "with_usage": sum(bool((a.get("response") or {}).get("usage")) for a in archive), "statuses": dict(Counter(a["status"] for a in archive)), "missing_finalized_call_ids": sorted(set(c for c in finalized if reservations[c]["run_id"] == run.name) - {a.get("call_id") for a in archive})}
        if not (run / "graph.json").exists():
            rows.append(row)
            continue
        graph = read(run / "graph.json")
        if row["packet_pages"]:
            report = read(run / "generation_response.json")["diagnostic_contract_report"]
            row["diagnostics"] = {k: report.get(k) for k in ("candidate_count", "publish_count", "unresolved_count", "drop_reasons", "invalid_record_count")}
        else:
            ledger = graph.get("diagnostic_compilation_ledger", {})
            row.update(nodes=len(graph["nodes"]), relations=len(graph["relations"]), review=graph["review_summary"], approval_eligible=graph["approval_eligible"])
            row["diagnostics"] = {k: ledger.get(k) for k in ("candidate_count", "publish_count", "unresolved_count", "contract_failure_count", "drop_reasons", "diagnostic_input_coverage_complete", "diagnostic_extraction_complete")}
            occurrences = Counter(e.get("record_window_id") for e in ledger.get("records", []) if e.get("disposition") == "publish" and e.get("record_window_id"))
            row["multiple_published_records_in_one_window"] = {k: n for k, n in occurrences.items() if n > 1}
            row["dispositions"] = dict(Counter(e["disposition"] for e in ledger.get("records", [])))
            row["canonical_grounding"] = grounding(graph, run)
            paths = wrapped._branch_aware_paths(graph)
            row["diagnostic_paths"] = len(paths)
            row["distinct_graph_branches"] = len({p["branch_lineage_id"] for p in paths})
            if row["manual_id"] in specs:
                score = historical_probe(graph, specs[row["manual_id"]], paths, analyzer)
                write(out / f"{run.name}_historical_probe.json", score)
                row["historical_probe"] = {k: v for k, v in score.items() if k not in {"witnesses", "one_to_one_assignments"}}
            review_packet(graph, paths, out / f"{run.name}_diagnostic_paths_for_review.md")
        rows.append(row)
    replays = []
    for replay in sorted((campaign / "replays").glob("c*r1_*")):
        state = read(replay / "replay.json")
        profile = read(replay / "runtime_profile.json")
        source_run = Path(profile["source_run"])
        manual = read(source_run / "runtime_profile.json")["manual_id"]
        row = {"run_id": replay.name, "source_run": source_run.name, "manual_id": manual, "mode": "offline_exact_provider_replay", "status": state["status"], "api_calls_made": state["api_calls_made"], "network_attempts": state["network_attempts"], "unused_exchanges": state["unused_exchanges"], "code_sha256": profile["code_sha256"]}
        if state["status"] == "completed":
            graph = read(replay / "graph.json")
            ledger = graph["diagnostic_compilation_ledger"]
            paths = wrapped._branch_aware_paths(graph)
            graph_branches = {p["branch_lineage_id"] for p in paths}
            published = {e["branch_lineage_id"] for e in ledger.get("records", []) if e["disposition"] == "publish"}
            row.update(nodes=len(graph["nodes"]), relations=len(graph["relations"]), distinct_graph_branches=len(graph_branches), review=graph["review_summary"], approval_eligible=graph["approval_eligible"], compiled_branches_missing_from_graph=sorted(published - graph_branches), canonical_grounding=grounding(graph, source_run))
            row["diagnostics"] = {k: ledger.get(k) for k in ("candidate_count", "publish_count", "unresolved_count", "drop_reasons", "contract_failure_count")}
            row["completeness"] = {k: ledger.get(k) for k in ("diagnostic_input_coverage_complete", "diagnostic_contract_processing_complete", "diagnostic_extraction_complete", "pending_diagnostic_records", "semantic_completeness_validated")}
            occurrences = Counter(e.get("record_window_id") for e in ledger.get("records", []) if e.get("disposition") == "publish" and e.get("record_window_id"))
            row["multiple_published_records_in_one_window"] = {k: n for k, n in occurrences.items() if n > 1}
            row["inspection_step_occurrences"] = sum(len(e["record"]["inspection_steps"]) for e in graph.get("diagnostic_records", []))
            row["condition_occurrences"] = sum(len(e["record"]["conditions"]) for e in graph.get("diagnostic_records", []))
            row["verified_source_gap_information"] = graph["publication_metrics"].get("verified_source_gap_information", 0)
            if manual in specs:
                score = historical_probe(graph, specs[manual], paths, analyzer)
                write(out / f"{replay.name}_historical_probe.json", score)
                row["historical_probe"] = {k: v for k, v in score.items() if k not in {"witnesses", "one_to_one_assignments"}}
            review_packet(graph, paths, out / f"{replay.name}_diagnostic_paths_for_review.md")
        replays.append(row)
    result = {"evaluation_status": "development_only_pending_technicians", "gold_sha256": hashlib.sha256(golden.read_bytes()).hexdigest(), "budget": {"cap_usd": 20, "calls_reserved": len(reservations), "calls_finalized": len(finalized), "charged_usd": sum(c["charged_usd"] for c in costs.values()), "observed_estimated_usd": sum(c["observed_estimated_usd"] for c in costs.values()), "unknown_usage_calls": sum(c["unknown_usage_calls"] for c in costs.values()), "all_reservations_within_cap": all(e["committed_before_usd"] + e["active_reserved_before_usd"] + e["worst_case_cost_usd"] <= 20 + 1e-9 for e in reservations.values()), "no_envelope_breaches": not any(e.get("envelope_breached") for e in finalized.values()), "active_calls": sorted(set(reservations) - set(finalized))}, "runs": rows, "replays": replays}
    write(out / "results.json", result)
    lines = ["# Misure della campagna di sviluppo", "", "Generato da `scripts/analyze_extraction_experiment.py`. Il matching storico è un probe lessicale: non misura precisione o recall semantici validati. Un record pubblicabile non equivale a un ramo corretto completo.", "", "| Run | Stato | Secondi | Chiamate | USD prudenziali | Nodi/relazioni | Rami nel grafo | Review | Probe storico autonomo |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        if row.get("packet_pages"):
            continue
        score = row.get("historical_probe", {})
        lines.append(f"| {row['run_id']} | {row['status']} | {row.get('elapsed_seconds', '')} | {row['cost']['calls']} | {row['cost']['charged_usd']:.6f} | {row.get('nodes', '')}/{row.get('relations', '')} | {row.get('distinct_graph_branches', '')} | {row.get('review', {}).get('total', '')} | {str(score['autonomous_probe']) + '/' + str(score['gold_total']) if score else '—'} |")
    lines += ["", "Confronti su pacchetti (stessa fonte e codice P1, singola esecuzione per profilo):", "", "| Run | Pagine | Pubblicabili | Irrisolti | USD |", "|---|---|---:|---:|---:|"]
    for row in rows:
        if row.get("packet_pages"):
            lines.append(f"| {row['run_id']} | {row['packet_pages']} | {row.get('diagnostics', {}).get('publish_count', '')} | {row.get('diagnostics', {}).get('unresolved_count', '')} | {row['cost']['charged_usd']:.6f} |")
    lines += ["", "C3–C6 usano le stesse risposte C2 mediante replay offline a richiesta identica. Zero rete e zero nuova spesa: C3 isola normalizzazione/export, C4 aggiunge i controlli sulle ispezioni, C5 distingue le celle di sola ispezione interamente verificate, C6 separa completezza di elaborazione e completezza dell’estrazione. Non sono repliche LLM indipendenti e il loro tempo non è il tempo di estrazione.", "", "| Replay | Nodi/relazioni | Rami nel grafo | Compilati persi nel grafo | Review | Probe storico autonomo | Ispezioni/condizioni conservate |", "|---|---:|---:|---:|---:|---:|---:|"]
    for row in replays:
        if row["status"] != "completed":
            continue
        score = row.get("historical_probe", {})
        lines.append(f"| {row['run_id']} (fonte: {row['source_run']}) | {row['nodes']}/{row['relations']} | {row['distinct_graph_branches']} | {len(row['compiled_branches_missing_from_graph'])} | {row['review']['total']} | {str(score['autonomous_probe']) + '/' + str(score['gold_total']) if score else '—'} | {row['inspection_step_occurrences']}/{row['condition_occurrences']} |")
    lines += ["", "Budget cumulativo (stima prudenziale, non fattura):", "", "```json", json.dumps(result["budget"], indent=2), "```", "", "B1 e C2 eseguono i manuali in sequenza; C1 ne esegue fino a due insieme. Ogni manuale usa concorrenza interna per chunk. I tempi sono monotonic elapsed del runner; non dedurre velocità causali da singole repliche o dagli orologi UTC, che hanno mostrato discontinuità nell'ambiente.", "", "La corrispondenza letterale delle evidenze è controllata contro le EvidenceUnit SQLite originali. Non certifica il significato della relazione. Il gold storico non è stato modificato; Hypertherm non dispone ancora di gold tecnico. Le predizioni e i moduli di scoring restano separati dalla produzione."]
    (out / "MEASUREMENTS.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"runs": len(rows), "budget": result["budget"]}))


if __name__ == "__main__":
    main()
