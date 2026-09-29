"""Blind audit of the KPI judge: a person rereads pairs the judge called different.

A branch is missed either because the graph lacks it or because the three-vote judge answers
"different" for a fact the graph does state. This script samples, from judged campaign runs,
reference-versus-extracted pairs the judge answered "different" for missed claims, mixes in a
few pairs it answered "same" as a control, and writes a blind sheet plus a separate key. The
judge's votes come from its archive (campaign/results/judge): no model is called.

Usage:
    .venv/bin/python scripts/kg_v3_judge_audit.py                 # write the sheet
    .venv/bin/python scripts/kg_v3_judge_audit.py --score         # score the filled sheet
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.kg_v3_evaluate import build_pairs, pair_line, v3_edges  # noqa: E402
from scripts.kg_v3_precision_sheet import plain  # noqa: E402

CAMPAIGN = ROOT / "campaign"
OUT = CAMPAIGN / "results" / "judge_audit"
SEED = 20260929
BATCH = 40
KINDS = {"repair": "riparazione", "inspection": "controllo", "escalation": "assistenza"}
JUDGEMENT = re.compile(r"^### (A\d{3})\b.*?^- Giudizio: `([^`]*)`", re.S | re.M)


def archived_votes(judge_dir: Path) -> dict[str, list[dict]]:
    """Archived judge answers by the hash of the request text, most recent last."""

    found: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for path in judge_dir.glob("*.json"):
        data = json.loads(path.read_text())
        try:
            user = data["request"]["messages"][1]["content"]
            answer = json.loads(data["response"]["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError, ValueError):
            continue
        found[hashlib.sha1(user.encode()).hexdigest()].append((data.get("started_utc") or "", answer))
    return {key: [answer for _, answer in sorted(items, key=lambda item: item[0])] for key, items in found.items()}


def pair_votes(pairs: list, archive: dict[str, list[dict]]) -> list[int | None]:
    """'same' votes of the last three judge calls on each pair, batched as the judge batched them."""

    votes: list[int | None] = []
    for start in range(0, len(pairs), BATCH):
        batch = pairs[start:start + BATCH]
        ids = [f"P{index}" for index in range(1, len(batch) + 1)]
        user = "\n".join(pair_line(pair_id, relation, group) for pair_id, (relation, group) in zip(ids, batch))
        answers = archive.get(hashlib.sha1(user.encode()).hexdigest(), [])[-3:]
        if not answers:
            votes.extend([None] * len(batch))
            continue
        counts: Counter = Counter()
        for answer in answers:
            for item in answer.get("answers") or []:
                counts[item.get("id")] += item.get("answer") == "same"
        votes.extend(counts[pair_id] for pair_id in ids)
    return votes


def segment_texts(manual: str, run: Path) -> dict[str, tuple[int, str]]:
    """Segment text as the annotator saw it (TESTO.md), completed by the run's own evidence."""

    texts: dict[str, tuple[int, str]] = {}
    for line in (CAMPAIGN / manual / "gold" / "TESTO.md").read_text().splitlines():
        match = re.match(r"^\[(p(\d+)\.[^\]]+)\] (.*)$", line)
        if match:
            texts[match.group(1)] = (int(match.group(2)), match.group(3))
    for edge in json.loads((run / "graph.json").read_text())["edges"]:
        for occurrence in edge.get("occurrences", []):
            for item in occurrence.get("evidence", []):
                texts.setdefault(item["segment_id"], (item["page"], item["text"]))
    return texts


def candidates_for_audit(manual: str, run: Path, missing: set[str], archive: dict) -> tuple[list, list]:
    """(different, same) pair records of one run: the judge's best pair for each missed claim, and controls."""

    gold = json.loads((CAMPAIGN / manual / "gold" / "gold.json").read_text())
    claims = [claim for claim in gold["claims"] if claim.get("failure") or claim.get("action")]
    edges = v3_edges(run)
    pairs, keys = build_pairs(claims, edges)
    votes = pair_votes(pairs, archive)
    by_claim: dict[tuple[str, str], list[int]] = defaultdict(list)
    for index, (claim_id, kind, _group) in enumerate(keys):
        by_claim[(claim_id, kind)].append(index)
    nodes = {node["id"]: node for node in json.loads((run / "graph.json").read_text())["nodes"]}
    claim_of = {claim["claim_id"]: claim for claim in claims}
    # The trusted problems of each cause, to show which branch an action pair belongs to.
    problems: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        if edge["type"] in {"MAY_INDICATE", "INDICATES"} and edge["trusted"] and edge["source_name"] not in problems[edge["target"]]:
            problems[edge["target"]].append(edge["source_name"])

    def record(index: int, verdict: str) -> dict:
        claim_id, kind, _ = keys[index]
        relation, group = pairs[index]
        overlap = bool(set().union(*(edge["segments"] for edge in group)) & relation["segments"]) if group else False
        return {"manual": manual, "run": run.name, "claim": claim_id, "kind": kind, "votes_same": votes[index],
                "judge": verdict, "overlap": overlap, "reference": relation, "claim_data": claim_of[claim_id],
                "graph_problems": problems.get(group[0]["source"], [])[:3] if group else [],
                "extracted": [{**edge, "segments": sorted(edge["segments"]),
                               "target_kind": nodes.get(edge["target"], {}).get("properties", {}).get("action_kind", "")}
                              for edge in group]}

    different, same = [], []
    for claim_id in sorted(missing):
        claim = claim_of.get(claim_id)
        if claim is None:
            continue
        judged_same = {kind for kind in ("indicator", "action")
                       if any((votes[i] or 0) >= 2 for i in by_claim[(claim_id, kind)])}
        failing = "indicator" if "indicator" not in judged_same else "action"
        if failing == "action" and (not claim.get("action") or "action" in judged_same):
            continue  # the action matched on another cause: not a judge disagreement
        options = [i for i in by_claim[(claim_id, failing)] if votes[i] is not None and votes[i] < 2]
        if options:
            best = max(options, key=lambda i: (votes[i], record(i, "").get("overlap"), -i))
            different.append(record(best, "different"))
    found = {claim["claim_id"] for claim in claims} - missing
    for claim_id in sorted(found):
        options = [i for kind in ("indicator", "action") for i in by_claim[(claim_id, kind)] if (votes[i] or 0) >= 2]
        if options:
            same.append(record(options[0], "same"))
    return different, same


def sample(pools: dict[str, tuple[list, list]], total_different: int, total_same: int, rng: random.Random) -> list:
    """Stratified by manual: every manual gets at least two different pairs when it has them."""

    def spread(groups: dict[str, list], total: int, floor: int) -> list:
        # One pair per claim across runs, so a single branch is not reread three times.
        unique = {}
        for manual, items in groups.items():
            by_claim: dict[tuple, list] = defaultdict(list)
            for item in items:
                by_claim[(item["claim"], item["kind"])].append(item)
            unique[manual] = [rng.choice(options) for _, options in sorted(by_claim.items())]
        counts = {manual: min(floor, len(items)) for manual, items in unique.items()}
        rest = total - sum(counts.values())
        weights = {manual: len(items) - counts[manual] for manual, items in unique.items()}
        while rest > 0 and any(weights.values()):
            manual = max(weights, key=lambda key: weights[key] / (counts[key] + 1))
            counts[manual] += 1
            weights[manual] -= 1
            rest -= 1
        chosen = []
        for manual, items in unique.items():
            chosen.extend(rng.sample(items, counts[manual]))
        return chosen

    different = spread({manual: pool[0] for manual, pool in pools.items()}, total_different, 2)
    same = spread({manual: pool[1] for manual, pool in pools.items()}, total_same, 1)
    chosen = different + same
    rng.shuffle(chosen)
    return chosen


INSTRUCTIONS = """## Come compilare

**Che cosa stai controllando.** Il valutatore dei KPI confronta il tuo gold con il grafo usando un
giudice automatico (tre voti). Un ramo conta come ritrovato solo se il giudice dice «stessa cosa».
Qui rileggi alcune coppie e dici tu se il grafo afferma la stessa cosa del tuo gold. Il foglio è
cieco: non sai che cosa ha risposto il giudice su ogni voce (la risposta è nella chiave, da non aprire).

**Ogni voce ha tre parti.**
- **Il manuale dice:** i segmenti del manuale citati dal gold e dal grafo, con ID e pagina.
- **Riferimento (il tuo gold):** una sola relazione del ramo: *problema → causa* oppure *causa → azione*.
  Il contesto è la tua nota di condizioni per tutto il ramo.
- **Il grafo afferma:** la relazione del grafo messa a confronto. Per *causa → azione* sono elencati
  tutti i passi che il grafo collega a quella causa nella stessa voce del manuale, ciascuno con le sue
  condizioni: valgono insieme.

**Che cosa scrivere** tra gli accenti gravi, al posto di `?`:

- `U` **uguale**: il grafo dice lo stesso fatto del riferimento, anche con parole diverse, con più
  dettagli o con un nome più corto. Un tecnico che usa il grafo arriverebbe allo stesso fatto.
- `S` **sbagliato il sistema**: il grafo dice un'altra cosa, oppure manca una parte che conta
  (un'azione, una condizione, un numero, una direzione, una negazione), oppure unisce parti di voci
  diverse del manuale.
- `G` **gold discutibile**: il grafo è fedele al manuale e la differenza viene dal riferimento
  (troppo specifico, impreciso o sbagliato rispetto al manuale). Spiega nella nota.
- `N` **non valutabile**: il testo mostrato non basta nemmeno guardando il PDF. Spiega nella nota.

**Regole utili.**
- Conta il significato, non le parole. Numeri, unità, codici, direzioni e negazioni devono coincidere.
- Se il riferimento dice «causa non indicata nel manuale» e il grafo ha una causa marcata *non scritta
  nel manuale*, quel nome è una lettura del sistema: giudica il problema e l'azione, non il nome
  della causa.
- Una condizione del tuo contesto non deve comparire su ogni passo; è `S` solo se il grafo la
  contraddice o se un'azione che nel manuale è condizionata («se persiste, contatta l'assistenza») è
  presentata senza la sua condizione.
- Se hai dubbi, apri il PDF alla pagina indicata. Una nota breve è utile per `S`, `G` e `N`.

Quando hai finito: `.venv/bin/python scripts/kg_v3_judge_audit.py --score`
(Tempo previsto: circa 30–45 minuti.)

"""


def _quote(text: str) -> str:
    return "\n".join(f"> {line}" for line in text.strip().splitlines() if line.strip())


def _context(items) -> str:
    from backend.kg_v3.contracts import context_text

    return context_text(items or [], scope="relation") or "nessuna"


def render(item: dict, number: int, texts: dict[str, tuple[int, str]], title: str) -> list[str]:
    reference, claim = item["reference"], item["claim_data"]
    cited = sorted(set(reference["segments"]) | {s for edge in item["extracted"] for s in edge["segments"]},
                   key=lambda s: (texts.get(s, (0, ""))[0], s))[:6]
    pages = sorted({texts[s][0] for s in cited if s in texts})
    lines = [f"### A{number:03d} · {title}, pagina {', '.join(map(str, pages)) or '?'}", "", "**Il manuale dice:**", ""]
    for segment in cited:
        if segment in texts:
            lines += [f"`{segment}`", "", _quote(plain(texts[segment][1])), ""]
    code = f" (codice {claim['code']})" if claim.get("code") else ""
    cause = f"«{claim['failure']}»" if claim.get("failure") else "causa non indicata nel manuale"
    conditions = claim.get("conditions") or "nessuna"
    if item["kind"] == "indicator":
        lines += [f"**Riferimento (il tuo gold):** problema «{claim['indicator']}»{code} → {cause}", "",
                  f"Contesto del ramo: {conditions}", ""]
        edge = item["extracted"][0]
        unwritten = " *(non scritta nel manuale)*" if not edge.get("target_stated", True) else ""
        lines += [f"**Il grafo afferma:** problema «{edge['source_name']}» → causa «{edge['target_name']}»{unwritten}",
                  "", f"Condizioni: {_context(edge.get('conditions'))}", ""]
    else:
        kind = KINDS.get(claim.get("action_kind"), "")
        lines += [f"**Riferimento (il tuo gold):** {cause} → azione «{claim['action']}»" + (f" ({kind})" if kind else ""),
                  "", f"Ramo del gold: problema «{claim['indicator']}»{code}. Contesto del ramo: {conditions}", ""]
        first = item["extracted"][0]
        unwritten = " *(non scritta nel manuale)*" if not first.get("source_stated", True) else ""
        lines += [f"**Il grafo afferma:** causa «{first['source_name']}»{unwritten} → passi:", ""]
        for edge in item["extracted"]:
            step_kind = KINDS.get(edge.get("target_kind"), "")
            lines.append(f"- «{edge['target_name']}»" + (f" ({step_kind})" if step_kind else "")
                         + f"; condizioni: {_context(edge.get('conditions'))}")
        shown = "; ".join(f"«{name}»" for name in item.get("graph_problems", [])) or "nessuno"
        lines += ["", f"Problemi collegati a questa causa nel grafo: {shown}", ""]
    return lines + ["- Giudizio: `?`", "- Nota: ", ""]


def write(runs_name: str, different: int, same: int) -> None:
    sheet, key_path = OUT / "REVISIONE_GIUDICE.md", OUT / "chiave_non_aprire.json"
    if sheet.exists() or key_path.exists():
        raise SystemExit(f"{sheet.relative_to(ROOT)} or its key exists; preserved.")
    kpi = json.loads((CAMPAIGN / "results" / "kpi_F.json").read_text())
    archive = archived_votes(CAMPAIGN / "results" / "judge" / "provider_responses")
    from scripts.campaign import asset

    pools, texts, titles = {}, {}, {}
    for manual, data in kpi["manuals"].items():
        titles[manual] = asset(manual)["name"]
        different_items, same_items = [], []
        for run_name, row in data["systems"].items():
            run = CAMPAIGN / manual / runs_name / run_name
            texts[(manual, run_name)] = segment_texts(manual, run)
            found_different, found_same = candidates_for_audit(manual, run, set(row["missing_claims"]), archive)
            different_items += found_different
            same_items += found_same
        pools[manual] = (different_items, same_items)
    chosen = sample(pools, different, same, random.Random(SEED))
    lines = ["# Revisione del giudice dei KPI", "",
             f"{len(chosen)} confronti tra il tuo gold e il grafo, in ordine casuale.", "",
             "Revisore: ", "Data: ", "Tempo totale impiegato (minuti): ", "", INSTRUCTIONS, "## Voci", ""]
    key = {}
    for number, item in enumerate(chosen, start=1):
        lines += render(item, number, texts[(item["manual"], item["run"])], titles[item["manual"]])
        key[f"A{number:03d}"] = {name: item[name] for name in ("manual", "run", "claim", "kind", "judge", "votes_same")}
    OUT.mkdir(parents=True, exist_ok=True)
    sheet.write_text("\n".join(lines) + "\n", encoding="utf-8")
    key_path.write_text(json.dumps({"seed": SEED, "runs": runs_name, "kpi": "kpi_F.json",
                                    "pool_sizes": {m: {"different": len(p[0]), "same": len(p[1])} for m, p in pools.items()},
                                    "items": key}, indent=1) + "\n")
    print(f"{len(chosen)} items -> {sheet.relative_to(ROOT)}")


def score() -> None:
    key = json.loads((OUT / "chiave_non_aprire.json").read_text())["items"]
    judgements = {item: value.strip().upper() for item, value in JUDGEMENT.findall((OUT / "REVISIONE_GIUDICE.md").read_text())}
    table: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for item_id, value in judgements.items():
        entry = key[item_id]
        for scope in (entry["manual"], "all"):
            table[(entry["judge"], scope)][value if value in {"U", "S", "G", "N"} else "?"] += 1
    for (judge, scope), counts in sorted(table.items()):
        judged = counts["U"] + counts["S"] + counts["G"]
        print(f"giudice {judge:9s} {scope:24s} U {counts['U']:2d} S {counts['S']:2d} G {counts['G']:2d} "
              f"N {counts['N']:2d} ? {counts['?']:2d}")
    different = table[("different", "all")]
    judged = different["U"] + different["S"] + different["G"]
    if judged:
        print(f"Tra le coppie che il giudice dice diverse: uguali per il revisore {different['U']}/{judged}, "
              f"errore del sistema {different['S']}/{judged}, gold discutibile {different['G']}/{judged}.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--score", action="store_true")
    parser.add_argument("--runs-name", default="runs")
    parser.add_argument("--different", type=int, default=32)
    parser.add_argument("--same", type=int, default=8)
    args = parser.parse_args()
    if args.score:
        score()
    else:
        write(args.runs_name, args.different, args.same)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
