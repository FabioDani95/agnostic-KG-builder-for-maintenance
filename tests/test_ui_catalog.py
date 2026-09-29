"""Manuals, versions and plain-language questions read from a campaign tree."""

from __future__ import annotations

from pathlib import Path

import pytest

from backend.kg_v3.reviewers import render_question
from backend.ui.catalog import Catalog
from backend.ui.questions import open_for_people, pending_questions, question_views, relation_sentence
from tests.ui_support import campaign_tree

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def tree(tmp_path, manual_doc):
    return campaign_tree(tmp_path, manual_doc)


def test_versions_come_from_every_run_folder_but_v22(tree):
    manual = Catalog(tree / "campaign", tree / "workspace").manual("test_pump")
    assert manual.machine.brand == "Acme" and manual.pages == 1 and manual.origin == "campaign"
    by_id = {version.version_id: version for version in manual.versions}
    assert set(by_id) == {"runs~v3_r1", "runs_E~v3_r1", "runs_F_budget_failed~v3_r2"}
    assert by_id["runs~v3_r1"].iteration == "" and by_id["runs_E~v3_r1"].iteration == "E"
    assert by_id["runs_F_budget_failed~v3_r2"].iteration == "F budget failed"
    assert by_id["runs_F_budget_failed~v3_r2"].status == "failed"
    current = by_id["runs~v3_r1"]
    assert current.repetition == 1 and current.commit == "abcdef1"
    assert current.status == "approved" and current.decided_by == "auto"
    assert current.open_questions > 0 and current.verified + current.doubtful > 0


def test_workspace_runs_join_the_campaign_manual(tree):
    copy = tree / "workspace" / "test_pump" / "runs" / "risposte-1"
    copy.mkdir(parents=True)
    (copy / "report.json").write_text('{"status": "awaiting_approval"}', encoding="utf-8")
    (copy / "origin.json").write_text('{"from": "campaign/test_pump/runs/v3_r1"}', encoding="utf-8")
    manual = Catalog(tree / "campaign", tree / "workspace").manual("test_pump")
    added = next(version for version in manual.versions if version.origin == "workspace")
    assert added.version_id == "workspace~risposte-1" and added.copied_from.endswith("runs/v3_r1")
    assert manual.origin == "campaign"  # the workspace folder has no info.yaml of its own


def test_the_selection_matches_what_the_command_line_publishes(tree):
    run = tree / "campaign" / "test_pump" / "runs" / "v3_r1"
    offered, _ = pending_questions(run)
    assert "\n\n".join(map(render_question, offered)) == (run / "questions_for_people.txt").read_text()


@pytest.mark.skipif(not (ROOT / "campaign/lg_lmh2235st/runs/v3_r1/state").exists(),
                    reason="local run state of LG is not in this clone")
def test_the_selection_matches_the_lg_run():
    run = ROOT / "campaign/lg_lmh2235st/runs/v3_r1"
    offered, _ = pending_questions(run)
    assert "\n\n".join(map(render_question, offered)) == (run / "questions_for_people.txt").read_text()


def test_questions_read_as_plain_italian(tree):
    run = tree / "campaign" / "test_pump" / "runs" / "v3_r1"
    views = question_views(run, open_for_people(run)[0])
    assert views and all(view.title_it == "Il manuale dice questo?" for view in views)
    for view in views:
        assert len(view.claims_it) == len(view.proposal)
        assert all("->" not in claim for claim in view.claims_it)
        assert [option.label_it for option in view.options] == ["Sì, è giusto", "Solo in parte", "No"]
        assert [option.needs_statements for option in view.options] == [False, True, False]


def relation(kind, source, target, conditions=()):
    return {"assertion": {"relation_type": kind, "source_key": "", "target_key": "",
                          "conditions": [{"kind": k, "text": t} for k, t in conditions]},
            "proposals": [{"source": source, "target": target}]}


def test_one_sentence_per_relation_type():
    symptom = {"type": "Symptom", "name": "No output", "stated": True}
    cause = {"type": "FailureMode", "name": "Worn packings", "stated": True}
    unnamed = {"type": "FailureMode", "name": "Low voltage", "stated": False}
    action = {"type": "CorrectiveAction", "name": "Replace packings", "kind": "repair", "stated": True}
    code = {"type": "ErrorCode", "name": "E-01", "stated": True}
    part = {"type": "Component", "name": "Packings", "stated": True}
    assert relation_sentence(relation("MAY_INDICATE", symptom, cause)) == \
        "Se succede «No output», una causa possibile è «Worn packings»."
    assert relation_sentence(relation("INDICATES", code, unnamed)) == \
        "Il codice «E-01» indica «Low voltage» (causa non scritta nel manuale)."
    assert relation_sentence(relation("RESOLVED_BY", cause, action, [("if", "Pump is cold.")])) == \
        "Se la causa è «Worn packings», si interviene con «Replace packings» (una riparazione). Vale se: Pump is cold."
    assert relation_sentence(relation("AFFECTS", cause, part)) == \
        "La causa «Worn packings» riguarda il componente «Packings»."
