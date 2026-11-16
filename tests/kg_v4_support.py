"""A three-page synthetic manual and a scripted model for the connected-graph pipeline tests.

The manual holds what the stages must handle: a heading trail, a troubleshooting table with a
merged cell, a remedy given without a cause, a cause without a remedy in its row, a pointer to
another page, a pointer to another entry, a maintenance sentence without a symptom and a
procedure on the page the pointer leads to. The scripted model answers each role from the text
it is shown, so a test fails when a stage shows the wrong passage.
"""

from __future__ import annotations

import re
from typing import Any

import fitz

from backend.kg_v3.llm import UsageTotals

ASSET = {"name": "Test pump", "description": "Test pump", "brand": "Acme", "model": "P1", "asset_type": "pump"}
TABLE = [
    ["PROBLEM", "CAUSE", "SOLUTION"],
    ["Pump fails to operate.", "Air supply restricted", "Clear the air line (page 3)"],
    [None, "Fluid dried on rod", "Clean the rod"],
    ["Output is low", "Worn packings", "Replace packings"],
    ["Motor ices", "", "Contact your distributor"],
    ["Pump leaks", "Loose drive belts", ""],
    ["Output pulses", "like 'Output is low'", ""],
]


def manual_pdf(path) -> None:
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 60), "Maintenance", fontsize=16)
    page.insert_text((72, 100), "Inspect the drive belt every week. Replace the drive belt if it is cracked.", fontsize=9)
    page.insert_text((72, 130), "The pump assembly holds the diaphragm and the air valve.", fontsize=9)
    page.insert_text((300, 820), "1", fontsize=8)

    page = document.new_page(width=595, height=842)
    page.insert_text((72, 60), "Troubleshooting", fontsize=16)
    xs, ys = [72, 222, 372, 540], [100 + 30 * index for index in range(len(TABLE) + 1)]
    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]))
    for index, y in enumerate(ys):
        # No line under the first cell of row 2: the PROBLEM cell spans two rows.
        page.draw_line((xs[1] if index == 2 else xs[0], y), (xs[3], y))
    for row_index, row in enumerate(TABLE):
        for column, text in enumerate(row):
            if text:
                page.insert_text((xs[column] + 4, ys[row_index] + 14), text, fontsize=9)
    page.insert_text((300, 820), "2", fontsize=8)

    page = document.new_page(width=595, height=842)
    page.insert_text((72, 60), "Clearing the air line", fontsize=16)
    page.insert_text((72, 100), "1. Close the air supply valve.", fontsize=9)
    page.insert_text((72, 120), "2. Disconnect the air line and blow it out with dry air.", fontsize=9)
    page.insert_text((72, 140), "3. Tighten the drive belts if the pump leaks.", fontsize=9)
    page.insert_text((300, 820), "3", fontsize=8)
    document.save(path)


def scanned_manual_pdf(path) -> None:
    """The same manual with its troubleshooting page as a picture: no text layer on page 2."""

    source = path.with_name("typed.pdf")
    manual_pdf(source)
    with fitz.open(source) as typed:
        document = fitz.open()
        document.insert_pdf(typed, from_page=0, to_page=0)
        page = document.new_page(width=595, height=842)
        page.insert_image(page.rect, pixmap=typed[1].get_pixmap(dpi=72))
        document.insert_pdf(typed, from_page=2, to_page=2)
        document.save(path)


def read_manual(tmp_path, *, scanned: bool = False):
    """(pdf path, read document) of the synthetic manual."""

    from backend.kg_v3.reader import read_document
    from scripts.kg_v3 import load_evidence

    pdf = tmp_path / "manual.pdf"
    if not pdf.exists():  # a second read of the same folder is the same file: a run can resume
        (scanned_manual_pdf if scanned else manual_pdf)(pdf)
    evidence, page_count, _ = load_evidence(pdf, ASSET)
    return pdf, read_document(list(evidence), page_count=page_count)


def segments_in(text: str) -> dict[str, str]:
    """Segment IDs of a rendered passage with their text."""

    return {match.group(1): match.group(2) for match in re.finditer(r"\[(p\d+\.[\w.]+)\][^\S\n]*([^\n]*)", text)}


def find(text: str, needle: str) -> str:
    """The ID of the segment that holds some words."""

    for segment_id, line in segments_in(text).items():
        if needle.lower() in line.lower():
            return segment_id
    raise AssertionError(f"the passage does not show {needle!r}")


def action(name, kind="repair", *, cite, component="", instruction="", expected="", conditions=(), reference=""):
    return {"name": name, "kind": kind, "instruction": instruction, "expected": expected, "component": component,
            "conditions": [{"kind": kind_, "text": text} for kind_, text in conditions], "reference": reference,
            "cite": [cite]}


def cause(name, *, cite, actions=(), component="", description="", no_remedy=False, conditions=()):
    return {"name": name, "description": description, "component": component,
            "conditions": [{"kind": kind_, "text": text} for kind_, text in conditions], "no_remedy": no_remedy,
            "cite": [cite], "actions": list(actions)}


def record(label, *, problem=None, causes=(), actions=(), see_also=""):
    empty = {"type": "", "name": "", "code": "", "description": "", "severity": "", "component": "", "cite": []}
    return {"record": label, "problem": {**empty, **(problem or {})}, "see_also": see_also,
            "actions": list(actions), "causes": list(causes)}


def symptom(name, *, cite, component="", description="", severity=""):
    return {"type": "Symptom", "name": name, "code": "", "description": description, "severity": severity,
            "component": component, "cite": [cite]}


class ScriptedModel:
    """Answers each role as a careful reader of the synthetic manual would."""

    def __init__(self, **overrides: Any) -> None:
        self.usage = UsageTotals()
        self.calls: list[dict[str, Any]] = []
        self.overrides = overrides

    async def json(self, *, system: str, user: str, schema: dict[str, Any], name: str, max_output_tokens: int = 0,
                   images: list[str] | None = None, reasoning_effort: str | None = None) -> dict[str, Any]:
        self.calls.append({"name": name, "user": user, "system": system, "schema": schema,
                           "images": len(images or [])})
        self.usage.add({"prompt": len(user) // 4, "completion": 50, "estimated_cost_usd": 0.0001}, name)
        handler = self.overrides.get(name) or getattr(self, name.removeprefix("kg_v4_"))
        return handler(user, schema) if callable(handler) else handler

    def count(self, name: str) -> int:
        return sum(call["name"] == name for call in self.calls)

    # Roles ----------------------------------------------------------------

    def transcribe(self, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Page 2 as a careful reader copies it from its picture: the title and the table, row by row."""

        blocks, problem = [{"kind": "heading", "text": "Troubleshooting"}], ""
        for row in TABLE[1:]:
            problem = row[0] or problem  # a cell that spans two rows is repeated
            blocks.append({"kind": "table_row", "text": " | ".join(
                f"{title}: {cell}" for title, cell in zip(TABLE[0], (problem, *row[1:])))})
        blocks.append({"kind": "text", "text": "  "})  # nothing printed: not a block
        return {"legible": True, "language": "en", "printed_page": "2", "blocks": blocks}

    def survey(self, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        pages = schema["properties"]["pages"]["items"]["properties"]["page"]["enum"]
        out = {"pages": [], "components": [], "codes": [],
               "machine": {"description": "", "brand": "", "model": "", "type": ""}}
        for page in pages:
            if page == 1:
                out["machine"]["description"] = "Air-operated diaphragm pump for transferring fluids."
                out["pages"].append({"page": 1, "kinds": ["maintenance"], "evidence": [find(user, "Replace the drive belt")]})
                out["components"] += [
                    {"name": "Drive belt", "part_of": "", "category": "mechanical", "part_number": "",
                     "description": "Belt that drives the pump; it is inspected every week.", "page": 1},
                    {"name": "Diaphragm", "part_of": "Pump assembly", "category": "mechanical", "part_number": "",
                     "description": "", "page": 1},
                    {"name": "Air valve", "part_of": "Pump assembly", "category": "pneumatic", "part_number": "",
                     "description": "", "page": 1},
                    {"name": "Water", "part_of": "", "category": "other", "part_number": "", "description": "", "page": 1},
                ]
            elif page == 2:
                out["pages"].append({"page": 2, "kinds": ["troubleshooting"], "evidence": [find(user, "Worn packings")]})
                out["components"] += [
                    {"name": "Packings", "part_of": "", "category": "consumable", "part_number": "", "description": "",
                     "page": 2},
                    {"name": "Drive belts", "part_of": "", "category": "mechanical", "part_number": "",
                     "description": "", "page": 2},
                ]
            else:
                out["pages"].append({"page": page, "kinds": ["repair_procedure"], "evidence": []})
        return out

    def extract(self, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        ids = segments_in(user.split("Passage", 1)[-1])
        owned = {key: text for key, text in ids.items() if "(context)" not in text}
        records = []
        row = next((key for key, text in owned.items() if "Air supply restricted" in text), None)
        if row:
            rod = find(user, "Fluid dried on rod")
            records.append(record("R1", problem=symptom(
                "Pump fails to operate", cite=row, component="Pump assembly",
                description="The pump does not start although air is supplied.", severity="high"), causes=[
                cause("Air supply restricted", cite=row, description="Not enough air reaches the pump.", actions=[
                    action("Clear the air line", cite=row, component="Air line", reference="page 3")]),
                cause("Fluid dried on rod", cite=rod, actions=[action("Clean the rod", cite=rod)]),
            ]))
        row = next((key for key, text in owned.items() if "Worn packings" in text), None)
        if row:
            records.append(record("R2", problem=symptom("Output is low", cite=row), causes=[
                cause("Worn packings", cite=row, component="Packings", actions=[
                    action("Replace packings", cite=row, component="Packings")])]))
        row = next((key for key, text in owned.items() if "Motor ices" in text), None)
        if row:
            records.append(record("R3", problem=symptom("Motor ices", cite=row), actions=[
                action("Contact your distributor", "escalation", cite=row)]))
        row = next((key for key, text in owned.items() if "Pump leaks" in text and "Loose" in text), None)
        if row:
            records.append(record("R4", problem=symptom("Pump leaks", cite=row), causes=[
                cause("Loose drive belts", cite=row, component="Drive belts", no_remedy=True)]))
        row = next((key for key, text in owned.items() if "Output pulses" in text), None)
        if row:
            records.append(record("R5", problem=symptom("Output pulses", cite=row), see_also="like 'Output is low'"))
        block = next((key for key, text in owned.items() if "Replace the drive belt" in text), None)
        if block:
            records.append(record("R6", causes=[cause("Cracked drive belt", cite=block, component="Drive belt", actions=[
                action("Replace the drive belt", cite=block, component="Drive belt", conditions=[("if", "if cracked")]),
            ])]))
        return {"records": records, "components": [], "unclear": []}

    def verify(self, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        ids = schema["properties"]["answers"]["items"]["properties"]["id"]["enum"]
        return {"answers": [{"id": item, "verdict": "supported", "problem": "", "reason": ""} for item in ids]}

    def resolve(self, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        ids = schema["properties"]["answers"]["items"]["properties"]["id"]["enum"]
        return {"answers": [{"id": item, "answer": "different", "reason": "not shown to be the same"} for item in ids]}

    def gap(self, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        answers = []
        for line in user.split("Passages:", 1)[0].splitlines():
            match = re.match(r"(G\d+): (\w+) '([^']*)'", line)
            if not match:
                continue
            label, _, name = match.groups()
            answer = {"id": label, "status": "not_stated", "actions": [], "causes": [], "problems": []}
            if name == "Loose drive belts" and "cause without remedy" in line and "Tighten the drive belts" in user:
                answer.update(status="found", actions=[action(
                    "Tighten the drive belts", cite=find(user.split("Passages:", 1)[1], "Tighten the drive belts"),
                    component="Drive belts", conditions=[("if", "if the pump leaks")])])
            answers.append(answer)
        return {"answers": answers}

    def enrich(self, user: str, schema: dict[str, Any]) -> dict[str, Any]:
        nodes = []
        for label, kind, name in re.findall(r"^(N\d+) \[(\w+)[^\]]*\] '([^']*)'", user, flags=re.M):
            item = {"id": label, "description": f"{name}, as it shows on the test pump during operation.",
                    "severity": "", "category": "", "instruction_text": "", "expected_result": "", "inferred": []}
            if kind == "Symptom":
                item.update(severity="medium", inferred=["severity"])
            elif kind == "Component":
                item["category"] = "mechanical"
            elif kind == "CorrectiveAction":
                if "air line" in name.lower():
                    item["instruction_text"] = "Close the air supply valve, disconnect the air line and blow it out."
                elif name == "Clean the rod":  # the row says no more than the name; the reader adds nothing
                    item["instruction_text"] = "Clean the rod."
            nodes.append(item)
        return {"nodes": nodes}
