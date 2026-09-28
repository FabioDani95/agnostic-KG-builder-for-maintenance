"""One entry point for the V3 evaluation campaign; every input and output lives in campaign/.

    status              what is ready for each manual
    new <id>            create campaign/<id>/ with info.yaml to fill in
    prepare <id>        read manual.pdf: write gold/TESTO.md and an empty gold/ANNOTAZIONE.md
    gold <id>           read gold/ANNOTAZIONE.md into gold/gold.json and report mistakes
    run <id>            3 V3 runs (runs/v3_r1..r3); skips done runs
    kpi [ids]           protocol KPIs for annotated manuals -> campaign/results/kpi.json and kpi.md
    precision [ids]     blind precision sheet (V3 run 1, mixed with the saved v22 graph where one exists)
                        -> campaign/results/precision/
    precision --score   precision of the filled sheet

The campaign has its own ledger, campaign/real_call_budget.jsonl, capped at 20 USD.
See campaign/README.md and paper/evaluation/PROTOCOLLO_V3.md.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CAMPAIGN = ROOT / "campaign"
LEDGER = CAMPAIGN / "real_call_budget.jsonl"
BUDGET = "20"
KINDS = {"riparazione": "repair", "controllo": "inspection", "assistenza": "escalation"}
NOT_STATED = "non indicata nel manuale"
INFO_TEMPLATE = """# Compila i campi e metti il PDF in questa cartella con il nome manual.pdf.
split: dev          # dev = sviluppo (serve a migliorare il sistema), test = prova finale
machine:
  name: ""          # per esempio "Genie GS-1930 scissor lift"
  brand: ""
  model: ""
  type: ""          # per esempio "scissor lift"
source_url: ""      # da dove viene il PDF
"""
BRANCH = """### Ramo R1
- problema:  | ID:
- codice:
- causa:  | ID:
- azione:  | tipo: riparazione | ID:
- componente:  | ID:
- condizioni:
- nota:
"""


def folder(manual: str) -> Path:
    return CAMPAIGN / manual


def info(manual: str) -> dict:
    data = yaml.safe_load((folder(manual) / "info.yaml").read_text()) or {}
    machine = data.get("machine") or {}
    if not all(str(machine.get(key) or "").strip() for key in ("name", "brand", "model", "type")):
        raise SystemExit(f"{manual}: complete machine name, brand, model and type in info.yaml")
    if data.get("split") not in {"dev", "test"}:
        raise SystemExit(f"{manual}: split must be dev or test")
    return data


def asset(manual: str) -> dict:
    machine = info(manual)["machine"]
    return {"name": machine["name"], "description": machine["name"], "brand": machine["brand"],
            "model": machine["model"], "asset_type": machine["type"]}


def read_manual(manual: str):
    from backend.kg_v3.reader import read_document
    from scripts.kg_v3 import load_evidence

    pdf = folder(manual) / "manual.pdf"
    if not pdf.exists():
        raise SystemExit(f"{manual}: put the PDF in {pdf.relative_to(ROOT)}")
    evidence, page_count, sha = load_evidence(pdf, asset(manual))
    from backend.kg_v3.mapper import attach_pdf_sections

    doc = read_document(list(evidence), page_count=page_count)
    attach_pdf_sections(doc, pdf)
    return doc, evidence, sha


# Commands -----------------------------------------------------------------

def cmd_new(args) -> None:
    target = folder(args.id)
    if not re.fullmatch(r"[a-z0-9_]+", args.id):
        raise SystemExit("use lowercase letters, digits and underscores for the manual ID")
    (target / "gold").mkdir(parents=True, exist_ok=True)
    (target / "runs").mkdir(exist_ok=True)
    if not (target / "info.yaml").exists():
        (target / "info.yaml").write_text(INFO_TEMPLATE)
    print(f"created {target.relative_to(ROOT)}: fill info.yaml and add manual.pdf")


def cmd_prepare(args) -> None:
    from backend.kg_v3.reader import render_segments

    doc, _, sha = read_manual(args.id)
    gold = folder(args.id) / "gold"
    gold.mkdir(exist_ok=True)
    unreadable = ", ".join(map(str, doc.unreadable_pages)) or "nessuna"
    text = [f"# Testo in segmenti: {asset(args.id)['name']}", "",
            "Ogni riga inizia con l'ID del segmento da copiare nel foglio di annotazione. Cerca la pagina",
            f"con «=== page N ===». Pagine senza testo leggibile: {unreadable}.", "", "```text",
            render_segments(doc.segments(), doc=doc), "```"]
    (gold / "TESTO.md").write_text("\n".join(text) + "\n", encoding="utf-8")
    sheet = gold / "ANNOTAZIONE.md"
    if sheet.exists() and not args.force:
        print(f"kept existing {sheet.relative_to(ROOT)} (use --force to reset it)")
    else:
        sheet.write_text("\n".join([
            f"# Annotazione del gold: {asset(args.id)['name']}", "",
            "Annotatore: ", "Data: ", "Tempo impiegato (minuti): ",
            "Pagine annotate (tutte le pagine diagnostiche, per esempio 45-52, 60): ", "",
            "## Istruzioni", "",
            "- Apri `manual.pdf` e trova le pagine diagnostiche (guasti, allarmi, troubleshooting).",
            "  Scrivile sopra in «Pagine annotate»: dentro quelle pagine annota **tutti** i rami.",
            "- Un ramo è una voce: una riga di tabella, un problema con i suoi passi, un codice.",
            "  Copia il modello «Ramo» per ogni voce e numera R1, R2, ...",
            "- **problema**: sintomo o significato del codice; il codice va in **codice**.",
            f"- **causa**: come scritta nel manuale, oppure `{NOT_STATED}`. Mai dedurla dal rimedio.",
            "- **azione**: una riga per ogni rimedio o controllo, in ordine; **tipo**: `riparazione`,",
            "  `controllo` o `assistenza`. Nessuna azione: lascia la riga vuota.",
            "- **componente**: solo se il manuale dice che quella parte è guasta o da regolare.",
            "- **condizioni**: \"se...\", \"solo quando...\", valori, esiti dei test.",
            "- **ID**: dal file `TESTO.md`, separati da virgole (`p11.t1.r2, p11.t1.r3`).",
            "- Non guardare grafi o risultati del sistema per questo manuale.",
            "- Il giorno dopo ricontrolla circa un ramo su cinque e correggi se serve.", "",
            "## Rami", "", BRANCH]) + "\n", encoding="utf-8")
    meta = {"sha256": sha, "pages": doc.page_count, "unreadable_pages": doc.unreadable_pages}
    (folder(args.id) / "manual.json").write_text(json.dumps(meta, indent=1) + "\n")
    print(f"{args.id}: {doc.page_count} pages, {len(doc.segments())} segments -> gold/TESTO.md, gold/ANNOTAZIONE.md")


def _lines(block: str, key: str) -> list[dict]:
    items = []
    for match in re.finditer(rf"^- {key}:(.*)$", block, re.M):
        parts = [part.strip() for part in match.group(1).split("|")]
        value = {"text": parts[0], "ids": [], "kind": ""}
        for part in parts[1:]:
            name, _, content = part.partition(":")
            if name.strip().lower() == "id":
                value["ids"] = [item.strip() for item in content.split(",") if item.strip()]
            elif name.strip().lower() == "tipo":
                value["kind"] = KINDS.get(content.strip().lower(), "")
        items.append(value)
    return items


def pages_from(text: str) -> list[int]:
    pages: set[int] = set()
    for part in text.replace("–", "-").split(","):
        start, _, end = part.strip().partition("-")
        if start.strip().isdigit():
            pages.update(range(int(start), int(end or start) + 1))
    return sorted(pages)


def parse_sheet(text: str) -> tuple[dict, list[str]]:
    """Filled ANNOTAZIONE.md -> gold with one claim per action, plus problems to fix."""

    from backend.kg_v3.contracts import SEGMENT_ID_PATTERN

    header = text.split("## Istruzioni", 1)[0]

    def field(label: str) -> str:
        # The header line may be written as a list item ("- Annotatore: ...").
        return (re.search(rf"^(?:[-*][ \t]+)?{label}.*?:[ \t]*(.*)$", header, re.M) or [None, ""])[1].strip()

    problems = [] if pages_from(field("Pagine annotate")) else ["write the annotated pages at the top"]
    claims = []
    body = text.split("## Rami", 1)[-1]
    for branch_id, block in re.findall(r"^### Ramo (\S+)\n(.*?)(?=^### |^## |\Z)", body, re.S | re.M):
        problem = (_lines(block, "problema") or [{"text": "", "ids": []}])[0]
        if not problem["text"]:
            continue
        cause = (_lines(block, "causa") or [{"text": "", "ids": []}])[0]
        component = (_lines(block, "componente") or [{"text": "", "ids": []}])[0]
        actions = [item for item in _lines(block, "azione") if item["text"]]
        stated = bool(cause["text"]) and cause["text"].lower() != NOT_STATED
        if not cause["text"]:
            problems.append(f"{branch_id}: write the cause or '{NOT_STATED}'")
        for item in [problem, cause, component, *actions]:
            bad = [value for value in item["ids"] if not re.match(SEGMENT_ID_PATTERN, value)]
            if bad:
                problems.append(f"{branch_id}: IDs not found in TESTO.md format: {bad}")
        if not problem["ids"]:
            problems.append(f"{branch_id}: the problem has no ID")
        base = {"branch_id": branch_id, "indicator": problem["text"],
                "code": (_lines(block, "codice") or [{"text": ""}])[0]["text"],
                "failure": cause["text"] if stated else "", "failure_stated": stated,
                "indicator_segments": problem["ids"], "failure_segments": cause["ids"] if stated else [],
                "component": component["text"], "component_segments": component["ids"],
                "conditions": (_lines(block, "condizioni") or [{"text": ""}])[0]["text"]}
        for number, action in enumerate(actions or [{"text": "", "ids": [], "kind": ""}], start=1):
            if action["text"] and not action["kind"]:
                problems.append(f"{branch_id}: action '{action['text'][:40]}' needs tipo")
            claims.append({**base, "claim_id": f"{branch_id}.{number}", "action": action["text"],
                           "action_kind": action["kind"], "action_segments": action["ids"]})
    gold = {"annotator": field("Annotatore"), "date": field("Data"), "minutes": field("Tempo impiegato"),
            "pages": pages_from(field("Pagine annotate")), "branches": len({claim["branch_id"] for claim in claims}),
            "claims": claims}
    return gold, problems


def cmd_gold(args) -> None:
    doc, _, _ = read_manual(args.id)
    gold, problems = parse_sheet((folder(args.id) / "gold" / "ANNOTAZIONE.md").read_text())
    known = {segment.segment_id for segment in doc.segments()}
    for claim in gold["claims"]:
        for key in ("indicator_segments", "failure_segments", "action_segments", "component_segments"):
            missing = [value for value in claim[key] if value not in known]
            if missing:
                problems.append(f"{claim['branch_id']}: IDs not in this manual: {missing}")
    gold.update(manual_id=args.id, split=info(args.id)["split"], status="annotated")
    (folder(args.id) / "gold" / "gold.json").write_text(json.dumps(gold, indent=1, ensure_ascii=False) + "\n")
    print(f"{args.id}: {gold['branches']} branches, {len(gold['claims'])} claims, pages {gold['pages']}, "
          f"annotator '{gold['annotator']}'")
    for item in dict.fromkeys(problems):
        print("  to fix:", item)


def cmd_run(args) -> None:
    info(args.id)
    if not (folder(args.id) / "gold" / "gold.json").exists() and not args.without_gold:
        raise SystemExit(f"{args.id}: annotate and read the gold first (the protocol runs after the gold)")
    runs = folder(args.id) / "runs"
    for number in range(1, args.reps + 1):
        out = runs / f"v3_r{number}"
        if (out / "graph.json").exists():
            print(f"{out.relative_to(ROOT)} already done")
            continue
        cmd_status(args)
        subprocess.run([sys.executable, str(ROOT / "scripts/kg_v3.py"), "--manual", args.id, "--out", str(out),
                        "--gates", "agent", "--budget", args.budget, "--run-id", f"{args.run_prefix}_{args.id}_v3_r{number}",
                        *(["--spend-ceiling", args.spend_ceiling] if args.spend_ceiling else [])], check=True)
        cmd_status(args)


def cmd_kpi(args) -> None:
    ids = args.ids or [path.parent.parent.name for path in sorted(CAMPAIGN.glob("*/gold/gold.json"))]
    subprocess.run([sys.executable, str(ROOT / "scripts/kg_v3_kpi.py"), "--manuals", ",".join(ids),
                    "--runs", "campaign", "--runs-name", args.runs_name, "--out", args.out, "--budget", args.budget,
                    *(["--v3-only"] if args.v3_only else []),
                    *(["--spend-ceiling", args.spend_ceiling] if args.spend_ceiling else [])], check=True)


def cmd_precision(args) -> None:
    from scripts.kg_v3_precision_sheet import score, write_sheet

    target = CAMPAIGN / "results" / "precision"
    suffix = "_2" if args.new else ""
    sheet, key = target / f"REVISIONE_PRECISIONE{suffix}.md", target / f"chiave_non_aprire{suffix}.json"
    if args.score:
        score(sheet, key)
        return
    if sheet.exists() or key.exists():
        raise SystemExit(f"{sheet.relative_to(ROOT)} or its key exists; preserved. Use --new for the second sheet.")
    ids = args.ids or [path.parents[2].name for path in sorted(CAMPAIGN.glob("*/runs/v3_r1/graph.json"))]
    sources = [(manual, folder(manual) / "runs" / "v3_r1" / "graph.json", folder(manual) / "runs" / "v22" / "graph.json")
               for manual in ids]
    sources = [(manual, v3, v22 if v22.exists() else folder(manual) / "runs_C/v22/graph.json")
               for manual, v3, v22 in sources]
    gold_pages = {manual: json.loads((folder(manual) / "gold/gold.json").read_text())["pages"] for manual in ids}
    write_sheet(sources, args.per_system, sheet, key, {manual: asset(manual)["name"] for manual in ids},
                "campaign", gold_pages)


def cmd_status(_args) -> None:
    rows = []
    for path in sorted(item for item in CAMPAIGN.iterdir() if (item / "info.yaml").exists()):
        manual = path.name
        split = (yaml.safe_load((path / "info.yaml").read_text()) or {}).get("split", "?")
        gold = json.loads((path / "gold" / "gold.json").read_text()) if (path / "gold" / "gold.json").exists() else None
        runs = sorted(item.name for item in (path / "runs").glob("*") if (item / "graph.json").exists())
        rows.append(f"{manual:28s} {split:5s} pdf:{'yes' if (path / 'manual.pdf').exists() else 'NO '} "
                    f"sheet:{'yes' if (path / 'gold' / 'ANNOTAZIONE.md').exists() else 'no '} "
                    f"gold:{str(gold['branches']) + ' branches' if gold else 'no'} runs:{','.join(runs) or '-'}")
    spent = 0.0
    if LEDGER.exists():
        spent = sum(float(json.loads(line).get("charged_cost_usd") or 0) for line in LEDGER.read_text().splitlines()
                    if json.loads(line).get("event") == "call_finalized")
    print("\n".join(rows) or "no manuals yet: python scripts/campaign.py new <id>")
    print(f"campaign spend: {spent:.3f} of {BUDGET} USD")


def cmd_quality(args) -> None:
    from scripts.kg_v3_quality import markdown, write_results

    print(markdown(write_results(CAMPAIGN, ROOT / args.out, args.runs_name)))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    quality = commands.add_parser("quality", help="offline graph quality without gold or model calls")
    quality.add_argument("--runs-name", default="runs")
    quality.add_argument("--out", default="campaign/results/quality.json")
    for name in ("new", "prepare", "gold"):
        command = commands.add_parser(name)
        command.add_argument("id")
        if name == "prepare":
            command.add_argument("--force", action="store_true")
    run = commands.add_parser("run")
    run.add_argument("id")
    run.add_argument("--budget", default=BUDGET)
    run.add_argument("--spend-ceiling")
    run.add_argument("--reps", type=int, default=3)
    run.add_argument("--run-prefix", default="campaign", help="ledger label for this frozen iteration")
    run.add_argument("--without-gold", action="store_true", help="only for development checks")
    kpi = commands.add_parser("kpi")
    kpi.add_argument("ids", nargs="*")
    kpi.add_argument("--runs-name", default="runs")
    kpi.add_argument("--out", default="campaign/results/kpi.json")
    kpi.add_argument("--budget", default=BUDGET)
    kpi.add_argument("--spend-ceiling")
    kpi.add_argument("--v3-only", action="store_true")
    precision = commands.add_parser("precision")
    precision.add_argument("ids", nargs="*")
    precision.add_argument("--score", action="store_true")
    precision.add_argument("--new", action="store_true", help="use the second blind sheet; preserve the original")
    precision.add_argument("--force", action="store_true", help="deprecated; existing sheets are always preserved")
    precision.add_argument("--per-system", type=int, default=12)
    args = parser.parse_args()
    CAMPAIGN.mkdir(exist_ok=True)
    {"status": cmd_status, "new": cmd_new, "prepare": cmd_prepare, "gold": cmd_gold, "run": cmd_run,
     "kpi": cmd_kpi, "precision": cmd_precision, "quality": cmd_quality}[args.command](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
