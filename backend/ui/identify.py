"""Read the machine a manual is about from its first pages: one small, fast model call.

The interface fills the «Macchina» fields with it right after an upload. The call runs in its
own process (``python -m backend.ui.identify``) so the budget ledger is set up exactly as for a
run: every real call goes through the budgeted gateway, under a tight spend ceiling.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
MODEL = "gpt-6-luna"  # the lightest model of the pipeline, without reasoning: about a second
# Pages are read one by one until there is enough text to name the machine: a cover with a
# title needs one page, a cover that is only a picture needs the next ones too.
ENOUGH_CHARACTERS = 1500
MAX_PAGES = 5
MAX_CHARACTERS = 6000
SCANNED_BELOW = 200  # fewer characters than this in the first pages: read the cover as an image
FIELDS = ("name", "brand", "model", "type")

SYSTEM = """You read the first pages of a technical manual and say which machine it is about.
Answer only from what the pages show; never guess a maker or a model that is not written.
- brand: the manufacturer, as printed (e.g. "Graco", "ABB").
- model: the model or series designation, as printed (e.g. "GTX 2000EX", "ACS580-01").
- type: what the machine is, as a short generic noun phrase in lowercase, in the manual's language
  (e.g. "texture sprayer", "variable frequency drive").
- name: how a person would name it in a list: brand, model and type together
  (e.g. "Graco GTX 2000EX texture sprayer").
Use an empty string for anything the pages do not state."""

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": list(FIELDS),
    "properties": {field: {"type": "string"} for field in FIELDS},
}


def first_pages(pdf: Path) -> tuple[str, str | None]:
    """Text of the first pages, as many as it takes to have enough (at most MAX_PAGES), and the
    cover as a PNG data URL when there is almost no text (a scanned manual)."""

    import fitz

    with fitz.open(pdf) as document:
        parts: list[str] = []
        for index in range(min(MAX_PAGES, document.page_count)):
            parts.append(re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", document[index].get_text("text"))).strip())
            if sum(len(part) for part in parts) >= ENOUGH_CHARACTERS:
                break
        text = "\n".join(part for part in parts if part)[:MAX_CHARACTERS]
        cover = None
        if len(text) < SCANNED_BELOW and document.page_count:
            png = document[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).tobytes("png")
            cover = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    return text, cover


def clean(answer: dict[str, Any]) -> dict[str, str]:
    machine = {field: " ".join(str(answer.get(field) or "").split()) for field in FIELDS}
    if not machine["name"]:
        machine["name"] = " ".join(part for part in (machine["brand"], machine["model"], machine["type"]) if part)
    return machine


async def identify(pdf: Path) -> dict[str, Any]:
    from backend.kg_v3.llm import ModelClient

    started = time.monotonic()
    text, cover = first_pages(pdf)
    client = ModelClient(model=MODEL, reasoning_effort="none", timeout_seconds=45, attempts=2)
    user = f"First pages of the manual:\n\n{text}" if text else "The first page of the manual is attached."
    answer = await client.json(system=SYSTEM, user=user, schema=SCHEMA, name="machine_identity",
                               max_output_tokens=300, images=[cover] if cover else None)
    return {"machine": clean(answer), "model": MODEL, "seconds": round(time.monotonic() - started, 2),
            "cost_usd": client.usage.estimated_cost_usd, "read": "cover" if cover else "text"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--budget", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--spend-ceiling", required=True)
    args = parser.parse_args()
    pdf = Path(args.pdf).resolve()
    os.environ.update({
        "KG_REAL_CALL_BUDGET_LEDGER": str(Path(args.ledger).resolve()), "KG_REAL_CALL_BUDGET_USD": args.budget,
        "KG_REAL_CALL_RUN_ID": args.run_id, "KG_REAL_CALL_PDF_ID": f"sha256:{pdf.stem}",
        "KG_REAL_CALL_SPEND_CEILING_USD": args.spend_ceiling,
    })
    os.chdir(ROOT)  # settings read the API key from .env in the repository root
    print(json.dumps(asyncio.run(identify(pdf))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
