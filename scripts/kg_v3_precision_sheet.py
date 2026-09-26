"""Blind precision review: a technician judges sampled graph relations against the manual.

``generate`` samples extracted relations from a V3 run and from the frozen v22
graphs, shuffles them without saying which system produced each, and writes a
Markdown sheet plus a separate key file. ``score`` reads the filled sheet and
reports precision per system with a 95% Wilson interval.

Usage:
    .venv/bin/python scripts/kg_v3_precision_sheet.py generate --v3 paper/experiments/v3_dev_20260926/r3
    .venv/bin/python scripts/kg_v3_precision_sheet.py score
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "paper/evaluation/v3_precision_review"
SHEET = OUT / "REVISIONE_PRECISIONE.md"
KEY = OUT / "chiave_non_aprire.json"
V22 = ROOT / "paper/experiments/robustness_continuation_20260926"
MANUALS = {"eastman_e554": "Eastman E-554", "danfoss_apf": "Danfoss APF",
           "graco_check_mate_200": "Graco Check-Mate 200", "hypertherm_powermax30_air": "Hypertherm Powermax30 AIR"}
DIAGNOSTIC = ("MAY_INDICATE", "INDICATES", "RESOLVED_BY", "AFFECTS")
VERBS = {"MAY_INDICATE": "può indicare la causa", "INDICATES": "(codice) indica la causa",
         "AFFECTS": "riguarda il componente", "RESOLVED_BY": "si affronta con"}
KINDS = {"repair": "riparazione", "inspection": "controllo o test", "escalation": "contattare l'assistenza"}
SEED = 20260927
PER_SYSTEM = 12
JUDGEMENT = re.compile(r"^### (R\d{3})\b.*?^- Giudizio: `([^`]*)`", re.S | re.M)


_CELL_LABEL = re.compile(r"^(?:TABLE COLUMNS: )?[^|:]{1,40}?(?: \(same as row above\))?: ")


def plain(text: str) -> str:
    """Same look for both systems: table cells without column labels, one space per gap."""

    cells = [_CELL_LABEL.sub("", cell.strip()) for cell in re.split(r"\s*\|\s*", str(text))]
    return " | ".join(" ".join(cell.split()) for cell in cells if cell)


def _evidence(pairs) -> list[tuple[int, str]]:
    seen, unique = set(), []
    for page, text in pairs:
        text = plain(text)
        if text and text not in seen:
            seen.add(text)
            unique.append((page, text))
    return unique[:3]


def _quote(text: str) -> str:
    return "\n".join(f"> {line}" for line in text.strip().splitlines() if line.strip())


def v3_items(run: Path, manual: str) -> list[dict]:
    data = json.loads((run / manual / "graph.json").read_text())
    nodes = {node["id"]: node for node in data["nodes"]}
    items = []
    for edge in data["edges"]:
        if edge.get("derived") or edge["type"] not in DIAGNOSTIC or not edge["trusted"]:
            continue
        evidence = edge["occurrences"][0]["evidence"]
        target = nodes[edge["to"]]
        items.append({
            "system": "v3", "manual": manual, "edge": edge["id"], "relation": edge["type"],
            "source": nodes[edge["from"]]["name"], "target": target["name"],
            "kind": target.get("properties", {}).get("action_kind", ""), "conditions": edge["conditions"],
            "evidence": _evidence((item["page"], item["text"]) for item in evidence),
        })
    return items


def v22_items(manual: str) -> list[dict]:
    data = json.loads((V22 / f"c12r1_{manual}" / "graph.json").read_text())
    nodes = {node["node_id"]: node for node in data["nodes"]}
    items = []
    for relation in data["relations"]:
        if relation["relation_type"] not in DIAGNOSTIC:
            continue
        target = nodes[relation["to_id"]]
        refs = relation.get("evidence_refs") or []
        items.append({
            "system": "v22", "manual": manual, "edge": relation["relation_id"], "relation": relation["relation_type"],
            "source": nodes[relation["from_id"]]["label"], "target": target["label"],
            "kind": (target.get("attributes") or {}).get("action_kind", "") or "", "conditions": [],
            "evidence": _evidence((ref["locator"].get("page"), ref["locator"].get("quote") or ref["quote"]) for ref in refs),
        })
    return items


def generate(run: Path, per_system: int) -> None:
    rng = random.Random(SEED)
    chosen = []
    for manual in MANUALS:
        for items in (v3_items(run, manual), v22_items(manual)):
            chosen.extend(rng.sample(items, min(per_system, len(items))))
    rng.shuffle(chosen)
    OUT.mkdir(parents=True, exist_ok=True)
    key = {}
    lines = [
        "# Revisione della precisione del grafo",
        "",
        f"{len(chosen)} affermazioni estratte da manuali di manutenzione, in ordine casuale. Per ognuna leggi",
        "cosa dice il manuale e cosa afferma il grafo, poi scrivi il giudizio tra i due accenti gravi",
        "al posto di `?`. Le istruzioni complete sono in fondo al file. Non aprire `chiave_non_aprire.json`:",
        "contiene il sistema che ha prodotto ogni affermazione e renderebbe la revisione non cieca.",
        "",
        "Revisore: ",
        "Data: ",
        "Tempo totale impiegato (minuti): ",
        "",
    ]
    for number, item in enumerate(chosen, start=1):
        item_id = f"R{number:03d}"
        key[item_id] = {name: item[name] for name in ("system", "manual", "edge", "relation")}
        pages = sorted({page for page, _ in item["evidence"] if page})
        kind = f" ({KINDS[item['kind']]})" if item.get("kind") in KINDS else ""
        lines += [f"### {item_id} · {MANUALS[item['manual']]}, pagina {', '.join(map(str, pages)) or '?'}", "",
                  "**Il manuale dice:**", ""]
        for _, text in item["evidence"]:
            lines += [_quote(text), ""]
        lines += [f"**Il grafo afferma:** «{item['source']}» **{VERBS[item['relation']]}** «{item['target']}»{kind}", ""]
        if item["conditions"]:
            lines += [f"Condizioni: {'; '.join(item['conditions'])}", ""]
        lines += ["- Giudizio: `?`", "- Nota: ", ""]
    lines += [
        "## Istruzioni",
        "",
        "- `C` corretto: il manuale afferma questo fatto, anche con parole diverse.",
        "- `P` parziale: giusto ma incompleto o impreciso in modo che conta (manca una condizione,",
        "  un'azione è più generica del manuale, un controllo è presentato come riparazione).",
        "- `S` sbagliato: il manuale non lo dice, lo dice di un'altra riga o di un altro problema, o",
        "  dice il contrario.",
        "- `N` non valutabile: il testo mostrato non basta; se puoi, controlla la pagina del PDF e",
        "  giudica, altrimenti lascia `N` e spiega nella nota.",
        "",
        "Giudica solo il fatto mostrato, non se il grafo è completo. Una nota breve è utile per `P`, `S` e `N`.",
    ]
    SHEET.write_text("\n".join(lines) + "\n", encoding="utf-8")
    KEY.write_text(json.dumps({"seed": SEED, "run": str(run.relative_to(ROOT)), "items": key}, indent=1) + "\n")
    print(f"{len(chosen)} items -> {SHEET.relative_to(ROOT)}")


def wilson(successes: int, total: int) -> tuple[float, float]:
    if not total:
        return (0.0, 0.0)
    z, p = 1.96, successes / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return (round(centre - margin, 3), round(centre + margin, 3))


def score(sheet: Path = SHEET) -> None:
    key = json.loads(KEY.read_text())["items"]
    judgements = {item: value.strip().upper() for item, value in JUDGEMENT.findall(sheet.read_text())}
    counts: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for item_id, value in judgements.items():
        entry = key[item_id]
        for scope in (entry["manual"], "all"):
            counts[(entry["system"], scope)][value if value in {"C", "P", "S", "N"} else "?"] += 1
    for (system, scope), count in sorted(counts.items()):
        judged = count["C"] + count["P"] + count["S"]
        strict = count["C"] / judged if judged else 0.0
        print(f"{system:4s} {scope:26s} C {count['C']:2d} P {count['P']:2d} S {count['S']:2d} N {count['N']:2d} "
              f"? {count['?']:2d} | precision {strict:.2f} {wilson(count['C'], judged)} | "
              f"with partial {((count['C'] + count['P']) / judged if judged else 0):.2f}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["generate", "score"])
    parser.add_argument("--v3", help="V3 run directory holding one folder per manual")
    parser.add_argument("--per-system", type=int, default=PER_SYSTEM)
    parser.add_argument("--sheet", default=str(SHEET), help="filled sheet to score")
    args = parser.parse_args()
    if args.action == "generate":
        generate(Path(args.v3).resolve(), args.per_system)
    else:
        score(Path(args.sheet))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
