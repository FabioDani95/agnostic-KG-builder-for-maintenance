"""Quality card of a graph: every measure that needs no judge, for any manual and pipeline version.

Offline and read-only. It reads ``graph.json`` files and writes, per graph, a JSON with all the
measures of backend/kg_v4/metrics.py and one Markdown file with the cards side by side:

* grounded connectivity (without the asset node and its derived links): components, share of
  the largest one, causes reachable from a symptom or code, causes with an action or a declared
  absence, complete chains;
* node quality: real descriptions, required attributes filled from the manual, placeholders,
  generic or noisy names, candidates for residual duplicates and for wrongly merged false friends;
* provenance: facts with page and section, by confidence;
* cost, tokens and time from the run report.

Branch recall and precision need a gold and judges: when the manual has a gold, the card shows
its size and the recall of a saved judgement, if one is given. Nothing here is a new measurement
of a pipeline: a card describes the graph file it was computed from.

Usage:
    .venv/bin/python scripts/kg_scorecard.py --discover --out experiments/my_cards
    .venv/bin/python scripts/kg_scorecard.py path/to/run/graph.json --out experiments/my_cards
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.kg_v4.metrics import scorecard  # noqa: E402

PILOT = ROOT / "experiments/kg_quality_pilot_20261001"


def discover() -> list[Path]:
    """Graphs of the test manuals present on this machine: campaign, pilot base profile, interface runs."""

    found = sorted((ROOT / "campaign").glob("*/runs/v3_r1/graph.json"))
    found += sorted((PILOT / "fixed_v1/runs").glob("*/Bsafe/r1/graph.json"))
    found += sorted((ROOT / "workspace").glob("*/runs/*/graph.json"))
    return found


def label(path: Path) -> tuple[str, str]:
    """(manual, run label) of a graph path."""

    parts = path.resolve().parts
    if "campaign" in parts:
        index = parts.index("campaign")
        return parts[index + 1], f"campaign/{parts[-2]}"
    if "workspace" in parts:
        index = parts.index("workspace")
        return parts[index + 1], f"workspace/{parts[-2]}"
    if "runs" in parts:
        index = len(parts) - 1 - parts[::-1].index("runs")
        return parts[index + 1], "/".join(parts[index + 2:-1]) or parts[-2]
    return path.parent.name, path.parent.name


def gold_block(manual: str) -> dict | None:
    path = ROOT / "campaign" / manual / "gold" / "gold.json"
    if not path.exists():
        return None
    claims = json.loads(path.read_text())["claims"]
    scored = [claim for claim in claims if claim.get("failure") or claim.get("action")]
    return {"branches": len({claim["branch_id"] for claim in scored}), "claims": len(scored),
            "pages": len({int(segment.split(".")[0][1:]) for claim in claims
                          for key in ("indicator_segments", "failure_segments", "action_segments")
                          for segment in claim.get(key, [])})}


def saved_recall(manual: str, run: str) -> dict | None:
    """Branch recall of a saved judgement for this graph, when one exists; never recomputed here."""

    if run.startswith("campaign/"):
        path = ROOT / "campaign/results/kpi_F.json"
        if path.exists():
            row = json.loads(path.read_text())["manuals"].get(manual, {}).get("systems", {}).get(run.split("/", 1)[1])
            if row:
                return {"branch_recall": row["branch_recall"], "claim_recall": row["claim_recall"],
                        "source": "campaign/results/kpi_F.json", "judge": "LLM, three votes"}
    if run.startswith("Bsafe/"):
        path = PILOT / "gold_measurement_v1/historical_scores.json"
        if path.exists():
            for row in json.loads(path.read_text())["rows"]:
                if (row["manual"], row["condition"], f"r{row['replica']}") == (manual, "Bsafe", run.split("/")[1]):
                    if row.get("branch_recall_bounds", [0, 1])[0] == row.get("branch_recall_bounds", [0, 1])[1]:
                        return {"branch_recall": row["branch_recall"], "claim_recall": row["claim_recall"],
                                "source": str(path.relative_to(ROOT)), "judge": "LLM, three votes"}
    return None


def card(path: Path) -> dict:
    graph = json.loads(path.read_text())
    manual, run = label(path)
    result = {"manual": manual, "run": run, "graph": str(path.resolve().relative_to(ROOT)), **scorecard(graph)}
    result["gold"] = gold_block(manual)
    result["saved_recall"] = saved_recall(manual, run) if result["gold"] else None
    return result


def _pct(value) -> str:
    return "n.d." if value is None else f"{round(100 * value)}%"


ROWS = (
    ("Nodi (senza Asset)", lambda c: c["connectivity"]["nodes"]),
    ("Archi fondati", lambda c: c["connectivity"]["edges"]),
    ("Componenti connesse", lambda c: c["connectivity"]["components"]),
    ("Quota componente maggiore", lambda c: _pct(c["connectivity"]["largest_component_share"])),
    ("  solo archi letti dal manuale", lambda c: _pct(c["connectivity"]["variants"]["extracted_only"]["largest_component_share"])),
    ("  senza azioni di assistenza", lambda c: _pct(c["connectivity"]["variants"]["without_escalation_actions"]["largest_component_share"])),
    ("Cause con azione", lambda c: _pct(c["connectivity"]["causes_with_action_share"])),
    ("Cause con azione o assenza dichiarata", lambda c: _pct(c["connectivity"]["causes_with_action_or_declared_share"])),
    ("Cause raggiungibili da sintomo/codice", lambda c: _pct(c["connectivity"]["causes_reachable_share"])),
    ("Sintomi/codici con catena completa", lambda c: _pct(c["connectivity"]["entries_with_complete_chain_share"])),
    ("Relazioni scartate", lambda c: _pct(c["connectivity"]["excluded_share"])),
    ("Descrizioni vere (diverse dal nome)", lambda c: _pct(c["node_quality"]["real_description_share"])),
    ("  ricavate dal manuale", lambda c: _pct(c["node_quality"]["descriptions_from_manual_share"])),
    ("Attributi obbligatori compilati", lambda c: _pct(c["node_quality"]["filled_required_attribute_share"])),
    ("  dal manuale (non segnaposto, non il nome)", lambda c: _pct(c["node_quality"]["required_attributes_from_manual_share"])),
    ("Nomi generici / rumore / troncati", lambda c: "{} / {} / {}".format(
        *(c["node_quality"]["name_defects"].get(key, 0) for key in ("generic", "layout_noise", "truncated")))),
    ("Nodi generici usati come ponte", lambda c: c["node_quality"]["generic_nodes_used_as_bridge"]),
    ("Duplicati esatti", lambda c: c["node_quality"]["exact_duplicates"]),
    ("Candidati duplicati (schermo lessicale)", lambda c: c["node_quality"]["duplicate_candidates"]),
    ("Fusioni sospette (falsi amici)", lambda c: c["node_quality"]["suspect_merges"]),
    ("Fatti con pagina e sezione", lambda c: _pct(c["provenance"]["with_section_share"])),
    ("Recall rami (giudizio salvato)", lambda c: "{}/{}".format(*c["saved_recall"]["branch_recall"]) if c.get("saved_recall")
     else ("non giudicato" if c.get("gold") else "senza gold")),
    ("Costo stimato USD", lambda c: c["cost"]["estimated_cost_usd"] or "n.d."),
    ("Secondi", lambda c: round(c["cost"]["seconds"]) if c["cost"]["seconds"] else "n.d."),
)


def markdown(cards: list[dict]) -> str:
    lines = ["# Schede di qualità dei grafi", "",
             "Misure offline calcolate dai file `graph.json` indicati. La connettività esclude il nodo Asset e i suoi",
             "archi derivati. I candidati duplicati e le fusioni sospette sono schermi lessicali da far giudicare a una",
             "persona, non verdetti. Il recall è quello di un giudizio salvato (giudice LLM), mai ricalcolato qui.", ""]
    for start in range(0, len(cards), 4):
        group = cards[start:start + 4]
        lines.append("| Misura | " + " | ".join(f"{item['manual']}<br>{item['run']}" for item in group) + " |")
        lines.append("|---|" + "---:|" * len(group))
        for name, value in ROWS:
            lines.append(f"| {name} | " + " | ".join(str(value(item)) for item in group) + " |")
        lines.append("")
    lines += ["## Esempi per grafo", ""]
    for item in cards:
        quality = item["node_quality"]
        lines.append(f"**{item['manual']} · {item['run']}** (`{item['graph']}`)")
        if quality["placeholder_by_property"]:
            lines.append("- Segnaposto: " + ", ".join(f"{key} {value}" for key, value in quality["placeholder_by_property"].items()))
        for key, title in (("generic", "Nomi generici"), ("layout_noise", "Rumore"), ("truncated", "Troncati")):
            if quality["name_defect_examples"].get(key):
                lines.append(f"- {title}: " + "; ".join(quality["name_defect_examples"][key][:3]))
        if quality["duplicate_candidate_examples"]:
            lines.append("- Candidati duplicati: " + "; ".join(
                f"{pair['left']} ~ {pair['right']}" for pair in quality["duplicate_candidate_examples"][:3]))
        if quality["suspect_merge_examples"]:
            lines.append("- Fusioni sospette: " + "; ".join(
                f"{pair['left']} / {pair['right']} ({pair['reason']})" for pair in quality["suspect_merge_examples"][:3]))
        hubs = ", ".join(f"{hub['name']} ({hub['degree']})" for hub in item["connectivity"]["highest_degree_nodes"][:3])
        lines += [f"- Nodi di grado più alto: {hubs}", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("graphs", nargs="*", help="graph.json files")
    parser.add_argument("--discover", action="store_true", help="every graph of the test manuals found on this machine")
    parser.add_argument("--out", required=True, help="directory for the cards")
    args = parser.parse_args()
    paths = [Path(item) for item in args.graphs] + (discover() if args.discover else [])
    if not paths:
        parser.error("give graph.json files or --discover")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cards = [card(path if path.is_absolute() else ROOT / path) for path in paths]
    for item in cards:
        name = f"{item['manual']}__{item['run'].replace('/', '_')}.json"
        (out / name).write_text(json.dumps(item, indent=1, ensure_ascii=False) + "\n")
    (out / "SCHEDE.md").write_text(markdown(cards) + "\n")
    print(markdown(cards).split("## Esempi per grafo")[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
