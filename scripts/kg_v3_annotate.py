"""Blind gold annotation for new manuals, independent of any system output.

    register  record a PDF, its machine identity and its split in the campaign registry
    sheet     write ANNOTAZIONE.md for the chosen pages: instructions, an empty branch
              template and every segment of those pages with its ID
    parse     read the filled sheet and write gold.json (one claim per action)

The segments come from the V3 reader, which uses no model: the sheet reveals nothing
about extraction results.

Usage:
    .venv/bin/python scripts/kg_v3_annotate.py register --pdf paper/manuals/files/v3/genie.pdf \\
        --id genie_scissor --split dev --name "Genie scissor lift" --brand Genie --model GS \\
        --type "scissor lift"
    .venv/bin/python scripts/kg_v3_annotate.py sheet --id genie_scissor --pages 45-52,60
    .venv/bin/python scripts/kg_v3_annotate.py parse --id genie_scissor
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REGISTRY = ROOT / "paper/manuals/v3_campaign_manuals.json"
GOLD_DIR = ROOT / "paper/evaluation/gold_v3"
KINDS = {"riparazione": "repair", "controllo": "inspection", "assistenza": "escalation"}
NOT_STATED = "non indicata nel manuale"
TEMPLATE = """### Ramo R1
- problema:  | ID:
- codice:
- causa:  | ID:
- azione:  | tipo: riparazione | ID:
- componente:  | ID:
- condizioni:
- nota:
"""


def registry() -> dict:
    return json.loads(REGISTRY.read_text()) if REGISTRY.exists() else {"manuals": []}


def entry(manual_id: str) -> dict:
    found = next((item for item in registry()["manuals"] if item["manual_id"] == manual_id), None)
    if found is None:
        raise SystemExit(f"{manual_id} is not registered")
    return found


def pages_from(text: str) -> list[int]:
    pages: set[int] = set()
    for part in text.split(","):
        start, _, end = part.strip().partition("-")
        if start:
            pages.update(range(int(start), int(end or start) + 1))
    return sorted(pages)


def register(args) -> None:
    pdf = Path(args.pdf).resolve()
    data = registry()
    data["manuals"] = [item for item in data["manuals"] if item["manual_id"] != args.id]
    data["manuals"].append({
        "manual_id": args.id, "file": str(pdf.relative_to(ROOT)),
        "sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(), "split": args.split,
        "asset": {"name": args.name, "description": args.description or args.name, "brand": args.brand,
                  "model": args.model, "asset_type": args.type},
        "registered_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "exposure": "not_run",
    })
    REGISTRY.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"registered {args.id} ({args.split})")


def load_doc(manual: dict):
    from backend.kg_v3.reader import read_document
    from scripts.kg_v3 import load_evidence

    evidence, page_count, sha = load_evidence(ROOT / manual["file"], manual["asset"])
    if sha != manual["sha256"]:
        raise SystemExit(f"{manual['manual_id']}: PDF changed since registration")
    return read_document(list(evidence), page_count=page_count)


def sheet(args) -> None:
    from backend.kg_v3.reader import render_segments

    manual = entry(args.id)
    pages = pages_from(args.pages)
    doc = load_doc(manual)
    target = GOLD_DIR / args.id / "ANNOTAZIONE.md"
    if target.exists() and not args.force:
        raise SystemExit(f"{target.relative_to(ROOT)} exists; use --force to overwrite it")
    target.parent.mkdir(parents=True, exist_ok=True)
    listing = render_segments([segment for page in pages for segment in doc.pages.get(page, [])], doc=doc)
    missing = [page for page in pages if page not in doc.pages]
    lines = [
        f"# Annotazione del gold: {manual['asset']['name']}",
        "",
        f"Manuale `{manual['manual_id']}`, split **{manual['split']}**, pagine {args.pages}.",
        "",
        "Annotatore: ",
        "Data: ",
        "Tempo impiegato (minuti): ",
        "Pagine del perimetro (se cambi quelle sopra, scrivile qui): ",
        "",
        "## Istruzioni",
        "",
        "- Leggi le pagine nel PDF e, sotto, il testo diviso in segmenti con i loro ID.",
        "- Per **ogni ramo** del perimetro (una riga di tabella, un problema con i suoi passi,",
        "  un codice di allarme) copia il modello e compilalo. Numera i rami R1, R2, ...",
        "- **problema**: il sintomo o il significato del codice; il codice va in **codice**.",
        f"- **causa**: come scritta nel manuale, oppure `{NOT_STATED}`. Mai dedurla dal rimedio.",
        "- **azione**: una riga per ogni rimedio o controllo, in ordine; **tipo** è `riparazione`,",
        "  `controllo` o `assistenza`. Un ramo senza azioni lascia la riga vuota.",
        "- **componente**: solo se il manuale dice che quella parte è guasta o da regolare.",
        "- **condizioni**: \"se...\", \"solo quando...\", valori, esiti dei test.",
        "- **ID**: i segmenti dove l'elemento è scritto, separati da virgole (`p11.t1.r2, p11.t1.r3`).",
        "- Non guardare grafi o risultati del sistema per questo manuale.",
        "",
        "## Rami",
        "",
        TEMPLATE,
        "## Testo del manuale in segmenti",
        "",
        *(f"Pagine senza testo leggibile: {', '.join(map(str, missing))} (annotale dal PDF senza ID)."
          for _ in [0] if missing),
        "```text",
        listing,
        "```",
    ]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    manual_pages = registry()
    for item in manual_pages["manuals"]:
        if item["manual_id"] == args.id:
            item["pages"] = pages
    REGISTRY.write_text(json.dumps(manual_pages, indent=1, ensure_ascii=False) + "\n")
    print(f"sheet -> {target.relative_to(ROOT)} ({sum(len(doc.pages.get(page, [])) for page in pages)} segments)")


def _line(block: str, key: str) -> list[dict]:
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


def parse(args) -> None:
    from backend.kg_v3.contracts import SEGMENT_ID_PATTERN

    manual = entry(args.id)
    text = (GOLD_DIR / args.id / "ANNOTAZIONE.md").read_text()
    header = text.split("## Istruzioni", 1)[0]
    annotator = (re.search(r"^Annotatore:[ \t]*(.*)$", header, re.M) or [None, ""])[1].strip()
    override = (re.search(r"^Pagine del perimetro.*?:[ \t]*(.*)$", header, re.M) or [None, ""])[1].strip()
    branches = re.findall(r"^### Ramo (\S+)\n(.*?)(?=^### |^## |\Z)", text.split("## Rami", 1)[1], re.S | re.M)
    claims, problems = [], []
    for branch_id, block in branches:
        problem = (_line(block, "problema") or [{"text": ""}])[0]
        if not problem["text"]:
            continue
        cause = (_line(block, "causa") or [{"text": NOT_STATED, "ids": []}])[0]
        actions = [item for item in _line(block, "azione") if item["text"]]
        code = (_line(block, "codice") or [{"text": ""}])[0]["text"]
        component = (_line(block, "componente") or [{"text": "", "ids": []}])[0]
        for field in [problem, cause, component, *actions]:
            bad = [item for item in field.get("ids", []) if not re.match(SEGMENT_ID_PATTERN, item)]
            if bad:
                problems.append(f"{branch_id}: invalid IDs {bad}")
        stated = cause["text"].lower() != NOT_STATED and bool(cause["text"])
        base = {
            "branch_id": branch_id, "pages": manual.get("pages", []), "indicator": problem["text"], "code": code,
            "failure": cause["text"] if stated else "", "failure_stated": stated,
            "indicator_segments": problem["ids"], "failure_segments": cause["ids"] if stated else [],
            "component": component["text"], "component_segments": component.get("ids", []),
            "conditions": (_line(block, "condizioni") or [{"text": ""}])[0]["text"],
        }
        for number, action in enumerate(actions or [{"text": "", "ids": [], "kind": ""}], start=1):
            if action["text"] and not action["kind"]:
                problems.append(f"{branch_id}: action '{action['text'][:40]}' has no tipo")
            claims.append({**base, "claim_id": f"{branch_id}.{number}", "action": action["text"],
                           "action_kind": action["kind"], "action_segments": action["ids"]})
    gold = {"manual_id": args.id, "split": manual["split"], "status": "annotated", "annotator": annotator,
            "pages": pages_from(override) if override else manual.get("pages", []),
            "branches": len({claim["branch_id"] for claim in claims}), "claims": claims}
    (GOLD_DIR / args.id / "gold.json").write_text(json.dumps(gold, indent=1, ensure_ascii=False) + "\n")
    print(f"{args.id}: {gold['branches']} branches, {len(claims)} claims, annotator '{annotator}'")
    for item in problems:
        print("  check:", item)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    reg = commands.add_parser("register")
    for name in ("--pdf", "--id", "--name", "--brand", "--model", "--type"):
        reg.add_argument(name, required=True)
    reg.add_argument("--split", choices=["dev", "test"], required=True)
    reg.add_argument("--description", default="")
    sht = commands.add_parser("sheet")
    sht.add_argument("--id", required=True)
    sht.add_argument("--pages", required=True, help="for example 45-52,60")
    sht.add_argument("--force", action="store_true")
    prs = commands.add_parser("parse")
    prs.add_argument("--id", required=True)
    args = parser.parse_args()
    {"register": register, "sheet": sheet, "parse": parse}[args.command](args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
