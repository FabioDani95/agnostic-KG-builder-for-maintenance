"""Technician confirmation of the historical gold rewritten as manual segments.

``generate`` writes a Markdown sheet: for each of the 34 historical cases it
shows the reference text and the segments where the agent located it, plus an
appendix with every segment of the pages involved. ``apply`` reads the filled
sheet and stores the technician's decisions in paper/evaluation/gold_segments_v1,
replacing segment IDs where the technician corrected them.

Usage:
    .venv/bin/python scripts/kg_v3_gold_sheet.py generate
    .venv/bin/python scripts/kg_v3_gold_sheet.py apply
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

GOLD_SEGMENTS = ROOT / "paper/evaluation/gold_segments_v1"
SHEET = GOLD_SEGMENTS / "CONFERMA_GOLD.md"
MANUALS = {"eastman_e554": "Eastman E-554", "danfoss_apf": "Danfoss APF", "graco_check_mate_200": "Graco Check-Mate 200"}
FIELDS = {"indicator": "problema", "failure": "causa", "action": "azione"}
KINDS = {"repair": "riparazione", "inspection": "controllo"}
BLOCK = re.compile(r"^### ([A-Z]\d+) ·.*?(?=^### |^## |\Z)", re.S | re.M)


from backend.kg_v3.contracts import SEGMENT_ID_PATTERN  # noqa: E402


def _value(block: str, label: str) -> str:
    match = re.search(rf"^- {label}: `([^`]*)`", block, re.M) or re.search(rf"^- {label}:[ \t]*(.*)$", block, re.M)
    return match.group(1).strip() if match else ""


def generate() -> None:
    from backend.kg_v3.reader import render_segment
    from scripts.kg_v3_evaluate import load_doc

    lines = [
        "# Conferma dei 34 casi di riferimento",
        "",
        "Ogni caso del vecchio gold è stato ritrovato automaticamente nel manuale e collegato ai",
        "segmenti (paragrafi o righe di tabella, con ID come `p11.t1.r3`). Per ogni caso conferma",
        "se la posizione è giusta e se il caso stesso è corretto. Istruzioni in fondo al file.",
        "",
        "Revisore: ",
        "Data: ",
        "Tempo totale impiegato (minuti): ",
        "",
    ]
    appendix = []
    for manual, title in MANUALS.items():
        data = json.loads((GOLD_SEGMENTS / f"{manual}.json").read_text())
        doc, _ = load_doc(manual)
        pages = sorted({page for claim in data["claims"] for page in claim["pages"]})
        lines += [f"## {title}", ""]
        for claim in data["claims"]:
            kind = KINDS.get(claim.get("action_kind", ""), "")
            code = f" (codice {claim['code']})" if claim.get("code") else ""
            lines += [f"### {claim['claim_id']} · {title}, pagina {', '.join(map(str, claim['pages']))}", "",
                      f"**Caso:** problema «{claim['indicator']}»{code} → causa «{claim['failure']}»"
                      + (f" → azione «{claim['action']}» ({kind})" if claim.get("action") else " → nessuna azione"), "",
                      "**Dove è stato trovato:**", ""]
            for field, label in FIELDS.items():
                for segment_id in claim.get(f"{field}_segments") or []:
                    segment = doc.segment(segment_id)
                    text = render_segment(segment).split("] ", 1)[-1] if segment else "(segmento non trovato)"
                    lines.append(f"- {label} → `{segment_id}`: {text[:400]}")
                if claim.get(field) and not claim.get(f"{field}_segments"):
                    lines.append(f"- {label} → nessun segmento trovato")
            lines += ["", "- Posizione: `?`", "- ID corretti: ", "- Caso: `?`", "- Correzione: ", "- Nota: ", ""]
        appendix += [f"### Segmenti di {title}", ""]
        for page in pages:
            for segment in doc.pages.get(page, []):
                appendix.append(f"- `{segment.segment_id}` {render_segment(segment).split('] ', 1)[-1][:300]}")
        appendix.append("")
    lines += [
        "## Istruzioni",
        "",
        "- **Posizione:** `S` se i segmenti indicati contengono davvero problema, causa e azione del",
        "  caso; `N` se no, e in **ID corretti** scrivi quelli giusti presi dall'appendice, nella",
        "  forma `problema=p37.b11 causa=p37.b11 azione=p37.b12`.",
        "- **Caso:** `C` se il caso è corretto come scritto; `M` se va modificato (scrivi in",
        "  **Correzione** la versione giusta, per esempio `causa=...` o `azione=...`); `X` se il",
        "  manuale non lo afferma e il caso va tolto.",
        "- Una causa che il manuale non nomina non si inventa: in quel caso scrivi `M` e",
        "  `causa=non indicata nel manuale`.",
        "",
        "## Appendice: tutti i segmenti delle pagine coinvolte",
        "",
        *appendix,
    ]
    SHEET.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{sum(len(json.loads((GOLD_SEGMENTS / f'{m}.json').read_text())['claims']) for m in MANUALS)} cases -> "
          f"{SHEET.relative_to(ROOT)}")


def apply() -> None:
    reviewed = {match.group(1): match.group(0) for match in BLOCK.finditer(SHEET.read_text())}
    header = SHEET.read_text().split("## ", 1)[0]
    reviewer = re.search(r"^Revisore:[ \t]*(.*)$", header, re.M)
    total = done = 0
    for manual in MANUALS:
        path = GOLD_SEGMENTS / f"{manual}.json"
        data = json.loads(path.read_text())
        for claim in data["claims"]:
            total += 1
            block = reviewed.get(claim["claim_id"])
            if block is None:
                continue
            position, verdict = _value(block, "Posizione").upper(), _value(block, "Caso").upper()
            if position not in {"S", "N"} or verdict not in {"C", "M", "X"}:
                continue
            done += 1
            review = {"position": position, "verdict": verdict, "correction": _value(block, "Correzione"),
                      "note": _value(block, "Nota"), "reviewer": reviewer.group(1).strip() if reviewer else ""}
            for key, value in re.findall(r"(problema|causa|azione)=([\w.]+)", _value(block, "ID corretti")):
                if not re.match(SEGMENT_ID_PATTERN, value):
                    print(f"{claim['claim_id']}: '{value}' is not a segment ID, ignored")
                    continue
                field = {label: name for name, label in FIELDS.items()}[key]
                claim[f"{field}_segments"] = [value]
            claim["technician_review"] = review
        claims = data["claims"]
        if all("technician_review" in claim for claim in claims):
            data["status"] = "technician_confirmed"
        path.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"applied {done}/{total} reviewed cases")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", choices=["generate", "apply"])
    args = parser.parse_args()
    generate() if args.action == "generate" else apply()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
