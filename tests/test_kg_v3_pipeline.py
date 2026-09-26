"""V3 end to end with a scripted provider: reads, checks, questions, merge, export and resume."""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest

from backend.kg_v3.contracts import ReviewerKind, Tier, Witness
from backend.kg_v3.export import graph_json
from backend.kg_v3.extractor import parse_read
from backend.kg_v3.llm import ModelClient, TruncatedResponse
from backend.kg_v3.ontology import load_ontology
from backend.kg_v3.reader import read_document
from backend.kg_v3.reviewers import InMemoryQuestionStore
from backend.kg_v3.run import Pipeline, RunConfig
from scripts.kg_v3 import load_evidence
from tests.test_kg_v3_reader import ASSET, troubleshooting_pdf


def entity(key, type_, name, cite, kind="", code=""):
    return {"key": key, "type": type_, "name": name, "code": code, "kind": kind, "stated": True, "cite": [cite]}


def relation(type_, source, target, record, cite):
    return {"type": type_, "source": source, "target": target, "record": record, "conditions": [], "cite": [cite]}


READ_A = {
    "entities": [
        entity("E1", "Symptom", "Pump fails to operate", "p1.t1.r2"),
        entity("E2", "FailureMode", "Air supply restricted", "p1.t1.r2"),
        entity("E3", "CorrectiveAction", "Clear the line", "p1.t1.r2", kind="repair"),
        entity("E4", "FailureMode", "Fluid dried on rod", "p1.t1.r3"),
        entity("E5", "CorrectiveAction", "Clean the rod", "p1.t1.r3", kind="repair"),
    ],
    "relations": [
        relation("MAY_INDICATE", "E1", "E2", "R1", "p1.t1.r2"),
        relation("RESOLVED_BY", "E2", "E3", "R1", "p1.t1.r2"),
        relation("MAY_INDICATE", "E1", "E4", "R2", "p1.t1.r3"),
        relation("RESOLVED_BY", "E5", "E4", "R2", "p1.t1.r3"),  # reversed: repaired from the end types
    ],
    "unclear": [],
}
READ_B = {  # same rows in other words; misses the rod remedy
    "entities": [
        entity("E1", "Symptom", "Pump does not operate", "p1.t1.r2"),
        entity("E2", "FailureMode", "Restricted air supply", "p1.t1.r2"),
        entity("E3", "CorrectiveAction", "Clear the supply line", "p1.t1.r2", kind="repair"),
        entity("E4", "FailureMode", "Fluid dried on the rod", "p1.t1.r3"),
    ],
    "relations": [
        relation("MAY_INDICATE", "E1", "E2", "R1", "p1.t1.r2"),
        relation("RESOLVED_BY", "E2", "E3", "R1", "p1.t1.r2"),
        relation("MAY_INDICATE", "E1", "E4", "R2", "p1.t1.r3"),
    ],
    "unclear": [],
}
COVERAGE = {  # the row both reads skipped
    "entities": [
        entity("E1", "Symptom", "Output is low", "p1.t1.r4"),
        entity("E2", "FailureMode", "Worn packings", "p1.t1.r4"),
        entity("E3", "CorrectiveAction", "Replace packings", "p1.t1.r4", kind="repair"),
        entity("E4", "Component", "Packings", "p1.t1.r4"),
    ],
    "relations": [relation("MAY_INDICATE", "E1", "E2", "R1", "p1.t1.r4"),
                  relation("RESOLVED_BY", "E2", "E3", "R1", "p1.t1.r4"),
                  relation("AFFECTS", "E2", "E4", "R1", "p1.t1.r4")],
    "unclear": [],
}


class ScriptedProvider:
    """Answers by response-format name, like the real provider would."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.chat = SimpleNamespace(completions=self)

    async def create(self, **kwargs):
        name = kwargs["response_format"]["json_schema"]["name"]
        schema = kwargs["response_format"]["json_schema"]["schema"]
        self.calls.append(name)
        if name == "kg_v3_map":
            content = {"pages": [{"page": 1, "label": "diagnostic", "section": "Troubleshooting", "unsure": False}]}
        elif name == "kg_v3_extract":
            content = [READ_A, READ_B, COVERAGE][min(self.calls.count(name), 3) - 1]
        elif name == "kg_v3_verify":
            ids = schema["properties"]["verdicts"]["items"]["properties"]["id"]["enum"]
            content = {"verdicts": [{"id": item, "verdict": "unclear"} for item in ids]}
        elif name == "kg_v3_merge":
            ids = schema["properties"]["answers"]["items"]["properties"]["id"]["enum"]
            content = {"answers": [{"id": item, "answer": "same"} for item in ids]}
        else:  # AgentDecision: confirm the map, accept doubts
            option = "confirm" if "(map_review)" in kwargs["messages"][1]["content"] else "accept"
            content = {"option_id": option, "correction": "", "keep_statements": [], "page_label_changes": [],
                       "rationale": "The row states it.", "cited_segment_ids": [], "confident": True}
        usage = SimpleNamespace(prompt_tokens=100, completion_tokens=40, total_tokens=140, prompt_tokens_details=None)
        message = SimpleNamespace(content=json.dumps(content), refusal=None)
        return SimpleNamespace(model="gpt-6-luna", usage=usage,
                               choices=[SimpleNamespace(finish_reason="stop", message=message)])


class FailingProvider(ScriptedProvider):
    async def create(self, **kwargs):
        raise AssertionError("a resumed run must not call the provider")


@pytest.fixture()
def doc(tmp_path):
    pdf = tmp_path / "manual.pdf"
    troubleshooting_pdf(pdf)
    evidence, page_count, _ = load_evidence(pdf, ASSET)
    return read_document(list(evidence), page_count=page_count)


def pipeline(doc, provider, workdir, **config):
    llm = ModelClient(model="gpt-6-luna", client_factory=lambda: provider)
    gates = config.pop("gates", {"map": ["agent"], "doubts": ["agent"], "approval": ["auto"]})
    store = InMemoryQuestionStore()
    return Pipeline(doc=doc, asset_name="Test pump", llm=llm, agent_llm=llm, workdir=workdir,
                    human_store=store, config=RunConfig(gates=gates, **config)), store


def test_full_run_is_complete_clean_and_resumable(doc, tmp_path):
    provider = ScriptedProvider()
    run, _ = pipeline(doc, provider, tmp_path / "run")
    result = asyncio.run(run.run())

    assert result.status == "approved"
    assert provider.calls.count("kg_v3_extract") == 3  # two reads and one coverage read
    edges = {(edge.relation_type, result.graph.nodes_by_id[edge.source].name, result.graph.nodes_by_id[edge.target].name)
             for edge in result.graph.edges}
    assert edges == {
        ("MAY_INDICATE", "Pump fails to operate", "Air supply restricted"),
        ("RESOLVED_BY", "Air supply restricted", "Clear the line"),
        ("MAY_INDICATE", "Pump fails to operate", "Fluid dried on rod"),
        ("RESOLVED_BY", "Fluid dried on rod", "Clean the rod"),
        ("MAY_INDICATE", "Output is low", "Worn packings"),
        ("RESOLVED_BY", "Worn packings", "Replace packings"),
        ("AFFECTS", "Worn packings", "Packings"),
    }
    assert all(edge.tier is Tier.GREEN for edge in result.graph.edges)
    symptom = next(node for node in result.graph.nodes.values() if node.name == "Pump fails to operate")
    assert symptom.aliases == ["Pump does not operate"]

    by_record = {item.assertion.record_key.split(":", 1)[1]: item.assertion.certificate for item in result.relations}
    assert set(by_record["A.R1"].witnesses) == {Witness.STRUCTURE, Witness.AGREEMENT}
    reviewed = [item.assertion.certificate for item in result.relations
                if Witness.REVIEWER in item.assertion.certificate.witnesses]
    assert len(reviewed) == 4 and all(item.confirmed_by.kind is ReviewerKind.AGENT for item in reviewed)
    assert result.report["gates"]["doubts"] == {"questions": 2, "answered": 2, "pending": 0}

    exported = graph_json(result, doc, asset=ASSET, source_title="manual.pdf")
    types = {edge["type"] for edge in exported["edges"]}
    assert {"MAY_INDICATE", "RESOLVED_BY", "AFFECTS", "HAS_COMPONENT"} <= types
    remedy = next(node for node in exported["nodes"] if node["name"] == "Clear the line")
    assert remedy["properties"]["action_kind"] == "repair" and remedy["evidence"][0]["page"] == 1
    occurrence = next(edge for edge in exported["edges"] if edge["type"] == "RESOLVED_BY")["occurrences"][0]
    assert occurrence["evidence"][0]["segment_id"].startswith("p1.t1.r")

    assert all(unit.unit_id.startswith("u001-") for unit in result.units[:1])
    resumed, _ = pipeline(doc, FailingProvider(), tmp_path / "run")
    again = asyncio.run(resumed.run())
    assert len(again.graph.edges) == len(result.graph.edges) and again.status == "approved"


def test_people_get_only_the_budgeted_questions(doc, tmp_path):
    run, store = pipeline(doc, ScriptedProvider(), tmp_path / "run",
                          gates={"map": ["auto"], "doubts": ["human"], "approval": ["human"]},
                          human_question_budget=1)
    result = asyncio.run(run.run())
    assert len(store.open_questions()) == 2  # one doubt within the budget, then the approval
    assert result.status == "awaiting_approval"
    assert result.report["gates"]["doubts"]["pending"] == 2
    unverified = [edge for edge in result.graph.edges if edge.tier is Tier.YELLOW]
    assert len(unverified) == 4  # visible, not trusted


def test_small_mistakes_are_repaired_or_noted_never_fatal():
    spec = load_ontology()
    from backend.kg_v3.contracts import ReadingUnit

    unit = ReadingUnit(unit_id="u1", pages=[1], segment_ids=["p1.b1", "p1.b2"])
    data = {
        "entities": [entity("E1", "Symptom", "No power", "p1.b1"), entity("E2", "FailureMode", "Blown fuse", "p9.b9"),
                     entity("E3", "Asset", "Machine", "p1.b1"), {"key": "E4", "type": "Component"}],
        "relations": [relation("RESOLVED_BY", "E1", "E2", "R1", "p9.b9"), relation("MAY_INDICATE", "E1", "E3", "R1", "p1.b1")],
        "unclear": [{"note": "figure", "cite": ["p1.b2"]}],
    }
    proposals, unclear, notes = parse_read(data, unit=unit, read="A", spec=spec, allowed={"p1.b1", "p1.b2"})
    assert [(item.relation_type, item.source.name, item.target.name) for item in proposals] == [
        ("MAY_INDICATE", "No power", "Blown fuse")]
    assert proposals[0].cites == [] and proposals[0].source.cites == ["p1.b1"]  # unknown citations dropped
    assert "relation type repaired from the types of its ends" in proposals[0].notes
    assert unclear[0]["cites"] == ["p1.b2"] and len(notes) == 3


def test_truncated_answers_split_the_unit(doc):
    class Truncating(ScriptedProvider):
        async def create(self, **kwargs):
            name = kwargs["response_format"]["json_schema"]["name"]
            if name == "kg_v3_extract" and len(kwargs["messages"][1]["content"].splitlines()) > 4:
                self.calls.append(name)
                message = SimpleNamespace(content="{", refusal=None)
                return SimpleNamespace(model="gpt-6-luna", usage=None,
                                       choices=[SimpleNamespace(finish_reason="length", message=message)])
            return await super().create(**kwargs)

    from backend.kg_v3.contracts import DocumentMap, PageLabel, PageMapEntry
    from backend.kg_v3.extractor import Extractor
    from backend.kg_v3.mapper import build_units

    provider = Truncating()
    llm = ModelClient(model="gpt-6-luna", client_factory=lambda: provider)
    unit = build_units(doc, DocumentMap(entries=[PageMapEntry(page=1, label=PageLabel.DIAGNOSTIC)]))[0]
    extraction = asyncio.run(Extractor(llm, load_ontology(), asset_name="Test pump", reads=1).extract(doc, unit))
    assert any("split" in note for note in extraction.notes)
    with pytest.raises(TruncatedResponse):
        asyncio.run(llm.json(system="s", user="\n".join(["x"] * 9), schema={}, name="kg_v3_extract"))


def test_application_builder_emits_a_valid_revision(tmp_path, monkeypatch):
    from backend.kg_v3 import app_builder
    from scripts.kg_v3 import synthetic_workspace

    pdf = tmp_path / "manual.pdf"
    troubleshooting_pdf(pdf)
    workspace, source, _ = synthetic_workspace(pdf, ASSET)
    evidence, page_count, _ = load_evidence(pdf, ASSET)
    provider = ScriptedProvider()
    monkeypatch.setenv("KG_PDF_GENERATOR", "v3")
    monkeypatch.setattr(app_builder, "ModelClient",
                        lambda **kwargs: ModelClient(client_factory=lambda: provider, **kwargs))
    monkeypatch.setattr(app_builder, "run_config", lambda: RunConfig(
        gates={"map": ["agent"], "doubts": ["agent", "human"], "approval": []}))
    assert app_builder.kg_v3_enabled()

    from backend.domain.sources import SourceKind

    # In the application this is the operator's attestation of the asset identity.
    attestation = evidence[0].model_copy(update={"evidence_id": "ev_operator_asset",
                                                 "source_kind": SourceKind.OPERATOR_INPUT})
    revision = asyncio.run(app_builder.V3PdfSubgraphBuilder().build_revision(
        workspace=workspace, source=source, scope={"included_pages": [1]}, evidence=list(evidence),
        fingerprint="0" * 64, config_hash=app_builder.kg_v3_config_hash(), supersedes=None,
        operator_evidence=[attestation]))

    assert revision.validation.passed, revision.validation.issues
    assert revision.approval_eligible and revision.pipeline_version.startswith("kg-v3")
    assert revision.review_queue == []  # the agent settled every doubt
    resolved = [item for item in revision.relations if item.relation_type == "RESOLVED_BY"]
    assert len(resolved) == 3 and all(item.attributes["tier"] == "green" for item in resolved)
    assert all(ref.quote in ref.locator["quote"] for item in resolved for ref in item.evidence_refs)
    assert resolved[0].attributes["certificates"][0]["segment_ids"]
    asset = next(node for node in revision.nodes if node.node_type == "Asset")
    assert asset.node_id == workspace.asset.asset_id and asset.evidence_ids == ["ev_operator_asset"]


def test_oversized_readings_stop_before_spending(doc, tmp_path):
    run, _ = pipeline(doc, ScriptedProvider(), tmp_path / "run", max_units=0)
    with pytest.raises(ValueError, match="max_units"):
        asyncio.run(run.run())


def test_a_changed_graph_asks_for_approval_again():
    from backend.kg_v3.questions import approval_question

    first, second = approval_question(["10 relations"]), approval_question(["11 relations"])
    assert first.question_id != second.question_id and first.question_id.startswith("approval:")
