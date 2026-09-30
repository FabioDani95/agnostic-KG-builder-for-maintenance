"""Local browser fixture: synthetic graphs/PDF/SSE, no extraction or model calls.

Run: .venv/bin/python -m tests.graph_editor_browser_fixture --root /tmp/kg-editor-qa
Finish fake live: same command with --finish-live (while server is running).
"""

from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path

import fitz
import uvicorn

from backend.ui.api import UiSettings, create_app
from backend.ui.evidence import Evidence
from backend.ui.graph_document import schema
from backend.ui.jobs import JobError, Jobs
from tests.test_ui_graph_document import fixture_graph
from tests.ui_support import INFO


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def events(path, finished):
    values = [
        {
            "seq": 1,
            "t": 0,
            "cost_usd": 0,
            "kind": "run_started",
            "data": {"manual_id": "livepump", "version_id": "runs~v3_r1"},
        }
    ]
    if finished:
        values.append(
            {
                "seq": 2,
                "t": 1,
                "cost_usd": 0,
                "kind": "run_finished",
                "data": {"status": "approved", "verified": 1, "doubtful": 0, "excluded": 0, "open_questions": 0},
            }
        )
    path.write_text("\n".join(json.dumps(e) for e in values) + "\n")


def populate(root):
    for name in ("pump", "pdfpump", "largepump", "livepump", "typedpump"):
        run = root / "campaign" / name / "runs/v3_r1"
        run.mkdir(parents=True, exist_ok=True)
        (run.parent.parent / "info.yaml").write_text(INFO.replace("Test pump", name + " (synthetic)"))
        write(run / "graph.json", fixture_graph())
        write(run / "report.json", {"status": "approved", "provenance": {"commit": "fixture"}})
    typed = root / "campaign/typedpump/runs/v3_r1"
    ontology = schema()
    next(n for n in ontology["nodes"] if n["name"] == "Symptom")["properties"] += [
        {"name": "count", "type": "number", "required": False},
        {"name": "enabled", "type": "boolean", "required": False},
        {"name": "list", "type": "array", "items": "string", "required": False},
        {"name": "nullable", "type": "string", "required": False},
    ]
    write(typed / "ontology.json", ontology)
    graph = fixture_graph()
    graph["nodes"][1]["properties"].update(count=1, enabled=True, list=["initial"], nullable="initial")
    write(typed / "graph.json", graph)
    history = root / "campaign/pump/runs/v3_r0"
    graph = fixture_graph()
    graph["nodes"][1]["name"] = graph["nodes"][1]["properties"]["name"] = "Historical noise"
    write(history / "graph.json", graph)
    write(history / "report.json", {"status": "approved"})
    os.utime(history / "report.json", (1700000000, 1700000000))
    manual = root / "campaign/pdfpump"
    if not (manual / "manual.pdf").exists():
        with fitz.open() as pdf:
            page = pdf.new_page(width=595, height=842)
            page.insert_text((60, 80), "Maintenance fixture: noise indicates wear.", fontsize=14)
            page.insert_text((60, 110), "Replace the worn bearing after disconnecting power.", fontsize=12)
            pdf.save(manual / "manual.pdf")
    evidence = Evidence(root / ".readonly-cache")
    doc = evidence.document(manual)
    segment = evidence.segment(manual, doc.segments()[0].segment_id)
    graph = fixture_graph()
    graph["nodes"][1]["evidence"] = [segment]
    graph["edges"][0]["occurrences"][0]["evidence"] = [segment]
    write(manual / "runs/v3_r1/graph.json", graph)
    large = fixture_graph()
    originals = copy.deepcopy(large["nodes"][1:])
    large["nodes"] = [large["nodes"][0]]
    large["edges"] = []
    for index in range(200):
        for original in originals:
            node = copy.deepcopy(original)
            node["id"] += f"_{index}"
            node["name"] = node["properties"]["name"] = f"{node['name']} {index}"
            for key in node["properties"]:
                if key.endswith("_id"):
                    node["properties"][key] = node["id"]
            large["nodes"].append(node)
        for kind, source, target in (("MAY_INDICATE", "sym", "cause"), ("RESOLVED_BY", "cause", "action")):
            large["edges"].append(
                {
                    "id": f"{kind}_{index}",
                    "type": kind,
                    "from": f"{source}_{index}",
                    "to": f"{target}_{index}",
                    "tier": None,
                    "trusted": False,
                    "conditions": [],
                    "occurrences": [
                        {"record": "synthetic", "tier": None, "trusted": False, "conditions": [], "evidence": []}
                    ],
                }
            )
    write(root / "campaign/largepump/runs/v3_r1/graph.json", large)
    run = root / "campaign/livepump/runs/v3_r1"
    write(run / "job.json", {"pid": os.getpid()})
    write(run / "report.json", {"status": "running"})
    events(run / "events.jsonl", False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8017)
    parser.add_argument("--finish-live", action="store_true")
    args = parser.parse_args()
    if args.finish_live:
        run = args.root / "campaign/livepump/runs/v3_r1"
        write(run / "job.json", {"pid": 0})
        write(run / "report.json", {"status": "approved"})
        events(run / "events.jsonl", True)
        return
    populate(args.root)
    repo = Path(__file__).resolve().parents[1]

    # Refuse every extraction/resumption even if a QA operator clicks the wrong action.
    def offline_job(*args, **kwargs):
        raise JobError("Synthetic browser fixture: extraction disabled")

    Jobs.start = Jobs.apply = Jobs.approve = offline_job
    app = create_app(
        UiSettings(
            campaign=args.root / "campaign",
            workspace=args.root / "workspace",
            ledger=args.root / "ledger",
            frontend=repo / "frontend/dist",
        )
    )
    uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
