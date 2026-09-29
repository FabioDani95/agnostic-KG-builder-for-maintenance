"""A small campaign tree for the interface tests, built from the scripted pipeline run."""

from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path

from backend.kg_v3.export import graph_json
from backend.kg_v3.reviewers import render_question
from tests.test_kg_v3_pipeline import ScriptedProvider, pipeline
from tests.test_kg_v3_reader import ASSET, troubleshooting_pdf

INFO = """split: dev
machine:
  name: "Test pump"
  brand: "Acme"
  model: "P-1"
  type: "pump"
"""
# Doubts left to nobody: every doubt stays pending, as after an agent that was not sure.
OPEN_DOUBTS = {"map": ["auto"], "doubts": [], "approval": ["auto"]}


def scripted_run(doc, run_dir: Path, gates: dict | None = None) -> dict:
    """A run folder written like scripts/kg_v3.py writes it."""

    job, store = pipeline(doc, ScriptedProvider(), run_dir, gates=gates or OPEN_DOUBTS)
    result = asyncio.run(job.run())
    result.report["provenance"] = {"commit": "abcdef1234567"}
    graph = graph_json(result, doc, asset=ASSET, source_title="manual.pdf")
    (run_dir / "graph.json").write_text(json.dumps(graph), encoding="utf-8")
    (run_dir / "report.json").write_text(json.dumps(result.report), encoding="utf-8")
    (run_dir / "questions_for_people.txt").write_text(
        "\n\n".join(render_question(question) for question in store.open_questions()), encoding="utf-8")
    return graph


def campaign_tree(root: Path, doc) -> Path:
    """campaign/test_pump with a current run, an older iteration, a v22 run and a failed run."""

    manual = root / "campaign" / "test_pump"
    manual.mkdir(parents=True)
    (manual / "info.yaml").write_text(INFO, encoding="utf-8")
    (manual / "manual.json").write_text(json.dumps({"pages": 1}), encoding="utf-8")
    troubleshooting_pdf(manual / "manual.pdf")
    current = manual / "runs" / "v3_r1"
    current.mkdir(parents=True)
    scripted_run(doc, current)
    shutil.copytree(current, manual / "runs_E" / "v3_r1")
    (manual / "runs_C" / "v22").mkdir(parents=True)
    (manual / "runs_C" / "v22" / "report.json").write_text("{}", encoding="utf-8")
    failed = manual / "runs_F_budget_failed" / "v3_r2" / "state"
    failed.mkdir(parents=True)
    shutil.copy(current / "state" / "map.json", failed / "map.json")
    return root
