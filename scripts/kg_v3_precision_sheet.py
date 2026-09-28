"""Blind precision review: a person judges sampled graph relations against the manual.

``write_sheet`` samples relations of each manual, shuffles them without saying which
system produced each, and writes a Markdown sheet plus a separate key file. ``score``
reads the filled sheet and reports precision per system with a 95% Wilson interval.
Driven by ``scripts/campaign.py precision``.
"""

from __future__ import annotations

import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

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


def v3_items(graph: Path, manual: str) -> list[dict]:
    data = json.loads(graph.read_text())
    nodes = {node["id"]: node for node in data["nodes"]}
    items = []
    for edge in data["edges"]:
        if edge.get("derived") or edge["type"] not in DIAGNOSTIC or not edge["trusted"]:
            continue
        evidence = [item for occurrence in edge["occurrences"] for item in occurrence["evidence"]]
        target = nodes[edge["to"]]
        items.append({
            "system": "v3", "manual": manual, "edge": edge["id"], "relation": edge["type"],
            "source": nodes[edge["from"]]["name"], "target": target["name"],
            "kind": target.get("properties", {}).get("action_kind", ""), "conditions": edge["conditions"],
            "evidence": _evidence((item["page"], item["text"]) for item in evidence),
            "evidence_pages": sorted({item["page"] for item in evidence if item.get("page")}),
        })
    return items


def v22_items(graph: Path, manual: str) -> list[dict]:
    data = json.loads(graph.read_text())
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
            "evidence_pages": sorted({ref["locator"]["page"] for ref in refs if ref["locator"].get("page")}),
        })
    return items


def write_sheet(sources: list[tuple[str, Path, Path | None]], per_system: int, sheet: Path, key_path: Path,
                titles: dict[str, str], origin: str, gold_pages: dict[str, list[int]] | None = None) -> None:
    """Blind sheet sampling V3 and v22 relations of each manual; the key goes to a separate file."""

    if sheet.exists() or key_path.exists():
        raise FileExistsError("Refusing to overwrite a precision sheet or its key; choose new paths.")
    rng = random.Random(SEED)
    chosen = []
    for manual, v3_graph, v22_graph in sources:
        groups = [v3_items(v3_graph, manual)]
        if v22_graph is not None and v22_graph.exists():
            groups.append(v22_items(v22_graph, manual))
        for items in groups:
            for item in items:
                pages = set(item.get("evidence_pages", []))
                item["outside_gold_pages"] = (bool(pages) and manual in (gold_pages or {})
                                               and not (pages & set(gold_pages[manual])))
            outside = [item for item in items if item["outside_gold_pages"]]
            selected = rng.sample(outside, min((per_system + 1) // 2, len(outside)))
            rest = [item for item in items if item not in selected]
            chosen.extend(selected + rng.sample(rest, min(per_system - len(selected), len(rest))))
    rng.shuffle(chosen)
    _write_blind(chosen, sheet, key_path, titles, origin)


def _same_link(item: dict, other: dict) -> bool:
    from scripts.kg_v3_evaluate import token_f1

    return (item["relation"] == other["relation"] and token_f1(item["source"], other["source"]) >= 0.5
            and token_f1(item["target"], other["target"]) >= 0.5)


def new_link_items(after: Path, before: Path, manual: str) -> list[dict]:
    """Trusted relations of a run, marked new when no trusted relation of the earlier run says the same."""

    earlier = v3_items(before, manual) if before.exists() else []
    items = v3_items(after, manual)
    for item in items:
        item["system"] = "v3_new" if not any(_same_link(item, other) for other in earlier) else "v3_kept"
        item["outside_gold_pages"] = False
    return items


def write_new_links_sheet(sources: list[tuple[str, Path, Path]], per_manual: int, sheet: Path, key_path: Path,
                          titles: dict[str, str], origin: str) -> dict[str, dict[str, int]]:
    """Blind sheet of new trusted relations, mixed with a third of relations the earlier run had too."""

    if sheet.exists() or key_path.exists():
        raise FileExistsError("Refusing to overwrite a precision sheet or its key; choose new paths.")
    rng = random.Random(SEED)
    chosen, counts = [], {}
    for manual, after, before in sources:
        items = new_link_items(after, before, manual)
        new = [item for item in items if item["system"] == "v3_new"]
        kept = [item for item in items if item["system"] == "v3_kept"]
        counts[manual] = {"new": len(new), "kept": len(kept)}
        picked = rng.sample(new, min(per_manual - per_manual // 3, len(new)))
        chosen.extend(picked + rng.sample(kept, min(per_manual - len(picked), len(kept))))
    rng.shuffle(chosen)
    _write_blind(chosen, sheet, key_path, titles, origin)
    return counts


def _write_blind(chosen: list[dict], sheet: Path, key_path: Path, titles: dict[str, str], origin: str) -> None:
    sheet.parent.mkdir(parents=True, exist_ok=True)
    key = {}
    lines = [
        "# Revisione della precisione del grafo",
        "",
        f"{len(chosen)} affermazioni estratte da manuali di manutenzione, in ordine casuale. Per ognuna leggi",
        "cosa dice il manuale e cosa afferma il grafo, poi scrivi il giudizio tra i due accenti gravi",
        f"al posto di `?`. Le istruzioni complete sono in fondo al file. Non aprire `{key_path.name}`:",
        "contiene il sistema che ha prodotto ogni affermazione e renderebbe la revisione non cieca.",
        "",
        "Revisore: ",
        "Data: ",
        "Tempo totale impiegato (minuti): ",
        "",
    ]
    for number, item in enumerate(chosen, start=1):
        item_id = f"R{number:03d}"
        key[item_id] = {name: item[name] for name in ("system", "manual", "edge", "relation", "outside_gold_pages")}
        pages = sorted({page for page, _ in item["evidence"] if page})
        kind = f" ({KINDS[item['kind']]})" if item.get("kind") in KINDS else ""
        lines += [f"### {item_id} · {titles.get(item['manual'], item['manual'])}, pagina {', '.join(map(str, pages)) or '?'}", "",
                  "**Il manuale dice:**", ""]
        for _, text in item["evidence"]:
            lines += [_quote(text), ""]
        lines += [f"**Il grafo afferma:** «{item['source']}» **{VERBS[item['relation']]}** «{item['target']}»{kind}", ""]
        if item["conditions"]:
            from backend.kg_v3.contracts import context_text

            lines += [f"Contesto: {context_text(item['conditions'])}", ""]
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
    sheet.write_text("\n".join(lines) + "\n", encoding="utf-8")
    key_path.write_text(json.dumps({"seed": SEED, "run": origin, "items": key}, indent=1) + "\n")
    print(f"{len(chosen)} items -> {sheet}")


def wilson(successes: int, total: int) -> tuple[float, float]:
    if not total:
        return (0.0, 0.0)
    z, p = 1.96, successes / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    margin = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return (round(centre - margin, 3), round(centre + margin, 3))


def score(sheet: Path, key_path: Path) -> None:
    key = json.loads(key_path.read_text())["items"]
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
