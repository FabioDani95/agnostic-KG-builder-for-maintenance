"""The connected-graph pipeline end to end with a scripted model: graph, export, resume, consumers."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest

from backend.kg_v3.ontology import load_ontology
from backend.kg_v4.estimate import estimate
from backend.kg_v4.metrics import connectivity, node_quality, scorecard
from backend.kg_v4.pipeline import BuildConfig, Builder
from backend.kg_v4.scoring import historical_edges
from tests.kg_v4_support import ASSET, ScriptedModel, read_manual

ROOT = Path(__file__).resolve().parents[1]


def build(tmp_path, model=None, **options):
    pdf, doc = read_manual(tmp_path)
    model = model or ScriptedModel()
    builder = Builder(doc=doc, asset=ASSET, llm=model, pdf_path=pdf, **options)
    return asyncio.run(builder.run()), model, doc


@pytest.fixture(scope="module")
def result(tmp_path_factory):
    return build(tmp_path_factory.mktemp("kg4"))[0]


def names(document):
    return {node["id"]: node["name"] for node in document["nodes"]}


def edges(document, *, derived=False):
    label = names(document)
    return {(edge["type"], label[edge["from"]], label[edge["to"]]) for edge in document["edges"]
            if bool(edge.get("derived")) == derived}


def test_an_autonomous_run_builds_complete_chains_without_placeholders(result):
    document = result.document
    assert result.status == "approved" and result.report["approval"] == "automatic"
    assert result.report["incomplete_reasons"] == [] and result.report["open_gaps"] == {}
    found = edges(document)
    assert {("MAY_INDICATE", "Pump fails to operate", "Air supply restricted"),
            ("RESOLVED_BY", "Air supply restricted", "Clear the air line"),
            ("ADDRESSED_BY", "Motor ices", "Contact your distributor"),
            ("MAY_INDICATE", "Output pulses", "Worn packings"),  # the pointer "like 'Output is low'"
            ("RESOLVED_BY", "Loose drive belts", "Tighten the drive belts"),  # found on another page
            ("ACTS_ON", "Tighten the drive belts", "Drive belt"),
            ("AFFECTS", "Cracked drive belt", "Drive belt")} <= found
    assert not any("nspecified" in node["name"] for node in document["nodes"])
    assert edges(document, derived=True) == {("HAS_COMPONENT", "Test pump", name)
                                              for name in ("Air line", "Drive belt", "Packings", "Pump assembly")}
    assert result.report["facts_by_origin"]["gap_repair"] == 2 and result.report["facts_by_origin"]["reference"] == 1
    assert result.report["references"] == {"printed": 2, "resolved": 1}


def test_every_node_is_described_and_every_fact_has_page_and_section(result):
    document = result.document
    nodes = {node["name"]: node for node in document["nodes"]}
    assert nodes["Test pump"]["properties"]["description"].startswith("Air-operated diaphragm pump")
    belt = nodes["Drive belt"]
    assert belt["aliases"] == ["Drive belts"] and belt["description_source"] == "manual"
    assert belt["properties"]["description"] == "Belt that drives the pump; it is inspected every week."
    assert belt["properties"]["category"] == "mechanical"
    clear = nodes["Clear the air line"]["properties"]
    assert clear["instruction_text"].startswith("Close the air supply valve")
    assert clear["source_reference"] == "p. 2, Troubleshooting" and clear["action_kind"] == "repair"
    replace = nodes["Replace the drive belt"]
    assert replace["properties"]["instruction_text"] == "Replace the drive belt (if: if cracked)"
    assert replace["name_derived_properties"] == ["instruction_text"]
    assert nodes["Cracked drive belt"]["properties"]["entry_status"] == "none_in_manual"
    assert nodes["Loose drive belts"]["properties"]["remedy_status"] == "stated"
    assert nodes["Output is low"]["inferred_properties"] == ["severity"]
    assert nodes["Worn packings"]["placeholder_properties"] == []  # material_context is no longer in the ontology
    for edge in document["edges"]:
        for occurrence in edge["occurrences"]:
            assert occurrence["evidence"], edge
            assert all(item["page"] and item["segment_id"] and item["text"] for item in occurrence["evidence"])
            if not edge.get("derived"):
                assert all(item["section"] for item in occurrence["evidence"])
                assert occurrence["confidence"] in {"high", "medium", "low"} and occurrence["origin"]
    card = result.report["scorecard"]
    assert card["node_quality"]["real_description_share"] == 1.0
    assert card["node_quality"]["placeholder_by_property"] == {}
    assert card["node_quality"]["descriptions_about_the_manual"] == 0
    assert card["provenance"]["with_section_share"] == 1.0
    assert card["connectivity"]["entries_with_complete_chain_share"] == 1.0
    assert card["connectivity"]["causes_with_action_or_declared_share"] == 1.0


def test_a_contradicted_fact_is_listed_with_its_reason_not_dropped(tmp_path):
    def verdicts(user, schema):
        ids = schema["properties"]["answers"]["items"]["properties"]["id"]["enum"]
        lines = dict(line.split(": ", 1) for line in user.split("Statements:\n")[1].splitlines())
        return {"answers": [
            {"id": item, "verdict": "contradicted", "problem": "other_entry", "reason": "remedy of the rod row"}
            if "'Replace packings'" in lines[item] and "prescribes" in lines[item] else
            {"id": item, "verdict": "unclear", "problem": "", "reason": "not sure"} if "Motor ices" in lines[item] else
            {"id": item, "verdict": "supported", "problem": "", "reason": ""} for item in ids]}

    document = build(tmp_path, ScriptedModel(kg_v4_verify=verdicts))[0].document
    assert ("RESOLVED_BY", "Worn packings", "Replace packings") not in edges(document)
    excluded = document["excluded_relations"]
    assert [(item["relation"], item["target"], item["reason"]) for item in excluded] == [
        ("RESOLVED_BY", "CorrectiveAction:Replace packings", "other_entry: remedy of the rod row")]
    assert excluded[0]["certificate"]["page"] == 2 and excluded[0]["certificate"]["section"] == "Troubleshooting"
    unclear = next(edge for edge in document["edges"] if edge["type"] == "ADDRESSED_BY")
    assert unclear["tier"] == "yellow" and unclear["trusted"] is False and unclear["confidence"] == "low"


def test_a_run_resumes_without_calling_again_and_refuses_other_inputs(tmp_path):
    first, model, doc = build(tmp_path, workdir=tmp_path / "run")
    calls = len(model.calls)
    assert (tmp_path / "run/state/manifest.json").exists() and (tmp_path / "run/state/survey.json").exists()
    again = ScriptedModel()
    second = asyncio.run(Builder(doc=doc, asset=ASSET, llm=again, pdf_path=tmp_path / "manual.pdf",
                                 workdir=tmp_path / "run").run())
    assert calls > 5 and again.calls == []
    assert second.document["nodes"] == first.document["nodes"] and second.document["edges"] == first.document["edges"]
    with pytest.raises(ValueError, match="different inputs"):
        Builder(doc=doc, asset=ASSET, llm=again, pdf_path=tmp_path / "manual.pdf", workdir=tmp_path / "run",
                config=BuildConfig(model="another-model"))
    # More workers or a larger gap budget do not change facts: the same directory resumes.
    Builder(doc=doc, asset=ASSET, llm=again, pdf_path=tmp_path / "manual.pdf", workdir=tmp_path / "run",
            config=BuildConfig(concurrency=2, gap_max_calls=3))


def test_a_failed_read_makes_the_run_incomplete_and_is_read_again(tmp_path):
    state = {"fail": True}

    def flaky(user, schema):
        if state["fail"]:
            raise RuntimeError("provider down")
        return ScriptedModel().extract(user, schema)

    model = ScriptedModel(kg_v4_extract=flaky)
    first, _, doc = build(tmp_path, model, workdir=tmp_path / "run")
    assert first.status == "incomplete" and "failed_extraction_reads" in first.report["incomplete_reasons"]
    state["fail"] = False
    second = asyncio.run(Builder(doc=doc, asset=ASSET, llm=model, pdf_path=tmp_path / "manual.pdf",
                                 workdir=tmp_path / "run").run())
    assert second.status == "approved" and len(second.document["edges"]) > 10


def test_stages_can_be_switched_off(tmp_path):
    config = BuildConfig(verify=False, resolve_with_model=False, gap_rounds=0, enrich=False, link_named_parts=False)
    outcome, model, _ = build(tmp_path, config=config)
    assert {call["name"] for call in model.calls} == {"kg_v4_survey", "kg_v4_extract"}
    assert outcome.report["facts_by_verdict"] == {"unchecked": outcome.report["extraction"]["facts"] + 3}
    assert outcome.report["graph"]["edges_by_tier"] == {"yellow": outcome.report["graph"]["edges"]}
    assert outcome.report["open_gaps"] == {"cause_without_problem": 1}
    nodes = {node["name"]: node for node in outcome.document["nodes"]}
    assert nodes["Loose drive belts"]["properties"]["remedy_status"] == "not_in_entry"  # its own row gives none
    # Without enrichment and with nothing read, the description is the name and is counted as missing.
    assert nodes["Clean the rod"]["description_source"] == "name"
    assert nodes["Clean the rod"]["properties"]["description"] == "Clean the rod"


def test_the_interface_and_the_editor_read_the_export(result, tmp_path):
    from backend.ui.graph_document import schema, with_occurrence_ids
    from backend.ui.graph_validation import validate

    document = json.loads(json.dumps(result.document))
    assert document["version"] == "kg-v3-graph-2" and document["pipeline"] == "kg-v4"
    graph = with_occurrence_ids(document)
    ontology = schema()
    issues = validate(graph, graph, ontology)
    assert [issue for issue in issues if issue["severity"] == "error"] == []
    # New relations and declared absences are understood: no false alarms on complete knowledge.
    assert {issue["code"] for issue in issues} <= {"SIMILAR_NAME", "NOT_STATED", "UNVERIFIED_CONTENT"}


def test_evidence_matches_the_reader_index_the_page_images_rely_on(result, tmp_path):
    from backend.kg_v3.export import _evidence

    _, doc = read_manual(tmp_path)
    for node in result.document["nodes"]:
        for item in node["evidence"]:
            expected = _evidence(doc, [item["segment_id"]])[0]
            assert {key: item[key] for key in ("text", "page", "bbox", "evidence_id")} == {
                key: expected[key] for key in ("text", "page", "bbox", "evidence_id")}


def test_the_historical_scorer_reads_the_graph(result):
    from scripts.kg_v3_evaluate import build_pairs

    scored = historical_edges(result.document)
    by_type = {}
    for edge in scored:
        by_type.setdefault(edge["type"], []).append(edge)
    assert set(by_type) == {"MAY_INDICATE", "RESOLVED_BY"}
    # The remedy given without a cause is shown as the scorer expects: an unnamed, unstated cause.
    direct = next(edge for edge in by_type["MAY_INDICATE"] if edge["source_name"] == "Motor ices")
    assert direct["target_stated"] is False and direct["target_name"] == "Unspecified cause of Motor ices"
    remedy = next(edge for edge in by_type["RESOLVED_BY"] if edge["source"] == direct["target"])
    assert remedy["target_name"] == "Contact your distributor" and remedy["record"] == direct["record"]
    assert remedy["segments"] == {"p2.t1.r5"} and remedy["trusted"]
    claims = [{"claim_id": "R1.1", "branch_id": "R1", "indicator": "Pump fails to operate.", "failure": "Fluid dried on rod",
               "action": "Clean the rod", "indicator_segments": ["p2.t1.r3"], "failure_segments": ["p2.t1.r3"],
               "action_segments": ["p2.t1.r3"], "conditions": ""},
              {"claim_id": "R2.1", "branch_id": "R2", "indicator": "Motor ices", "failure": "",
               "action": "Contact your distributor", "indicator_segments": ["p2.t1.r5"], "failure_segments": [],
               "action_segments": ["p2.t1.r5"], "conditions": ""}]
    pairs, keys = build_pairs(claims, scored)
    assert {(claim, kind) for claim, kind, _ in keys} == {("R1.1", "indicator"), ("R1.1", "action"),
                                                          ("R2.1", "indicator"), ("R2.1", "action")}


def test_a_remedy_without_a_cause_is_scored_by_its_problem_not_by_its_citation():
    """A flowchart: one problem, many outcome records, and a gold that cites the title."""
    from scripts.kg_v3_evaluate import build_pairs

    def step(number, action, cite):
        cause = f"unnamed:no-heat:R{number}"
        shared = {"record": f"R{number}", "trusted": True, "conditions": [], "segments": {cite}}
        return [{**shared, "type": "MAY_INDICATE", "source": "no-heat", "target": cause, "source_name": "No heat",
                 "target_name": "Unspecified cause of No heat", "source_stated": True, "target_stated": False},
                {**shared, "type": "RESOLVED_BY", "source": cause, "target": f"a{number}", "target_name": action,
                 "source_name": "Unspecified cause of No heat", "source_stated": False, "target_stated": True}]

    edges = [edge for number in range(1, 13) for edge in step(number, f"Check connector {number}", f"p2.b{number}")]
    edges += step(13, "Replace the magnetron", "p2.b40")
    claim = {"claim_id": "F.1", "branch_id": "F", "indicator": "No heat", "failure": "", "conditions": "",
             "action": "Replace the magnetron", "indicator_segments": ["p1.b1"], "failure_segments": [],
             "action_segments": ["p2.b99"]}  # the gold cites the title and another block of the box
    assert build_pairs([claim], edges)[0] == []  # historical: no shared citation, nothing to judge
    pairs, keys = build_pairs([claim], edges, unnamed_by_problem=True)
    by_kind = {kind: group for _, kind, group in keys}
    assert len(pairs) == 2 and len(by_kind["indicator"]) == 13  # one verdict covers all unnamed causes
    assert [edges[index]["target_name"] for index in by_kind["action"]] == ["Replace the magnetron"]


def test_metrics_read_graphs_of_the_previous_pipeline_too(result):
    old = {"version": "kg-v3-graph-2", "nodes": [
        {"id": "a", "type": "Asset", "name": "M", "properties": {}},
        {"id": "s", "type": "Symptom", "name": "No heat", "properties": {"description": "No heat", "severity": "Unknown"}},
        {"id": "f", "type": "FailureMode", "name": "Unspecified cause of no heat",
         "properties": {"description": "Unspecified cause of no heat", "material_context": "not_stated"}},
        {"id": "x", "type": "CorrectiveAction", "name": "Check fuse",
         "properties": {"description": "Check fuse", "instruction_text": "Check fuse", "source_type": "technical PDF",
                        "source_title": "manual.pdf", "source_reference": "page 3"}},
        {"id": "c", "type": "Component", "name": "Fuse", "properties": {"description": "Fuse", "category": "not_stated"}},
        {"id": "c2", "type": "Component", "name": "Fuses", "properties": {"description": "Fuses", "category": "not_stated"}},
    ], "edges": [
        {"id": "1", "type": "MAY_INDICATE", "from": "s", "to": "f", "tier": "green", "occurrences": [{"evidence": [{"page": 3}]}]},
        {"id": "2", "type": "RESOLVED_BY", "from": "f", "to": "x", "tier": "green", "occurrences": [{"evidence": [{"page": 3}]}]},
        {"id": "3", "type": "HAS_COMPONENT", "from": "a", "to": "c", "derived": True, "occurrences": []},
        {"id": "4", "type": "HAS_COMPONENT", "from": "a", "to": "c2", "derived": True, "occurrences": []},
    ], "excluded_relations": [{}]}
    links = connectivity(old)
    assert links["components"] == 3 and links["largest_component_share"] == 0.6 and links["isolated_nodes"] == 2
    assert links["excluded_share"] == 0.3333 and links["entries_with_complete_chain"] == 1
    quality = node_quality(old)
    assert quality["real_description_share"] == 0.0 and quality["exact_duplicates"] == 1
    assert quality["placeholder_attributes"] == 3 and quality["attributes_repeating_the_name"] == 1
    assert quality["weak_instruction_share"] == 1.0 and quality["compound_action_names"] == 0
    assert quality["generic_nodes_used_as_bridge"] == 1 and quality["name_defects"] == {"generic": 1}
    new = scorecard(result.document)
    assert new["pipeline"] == "kg-v4" and new["node_quality"]["generic_nodes_used_as_bridge"] == 0


def test_the_extended_ontology_is_explicit_and_the_previous_pipeline_keeps_its_subset():
    legacy, full = load_ontology(), load_ontology(full=True)
    assert [relation.name for relation in legacy.relations] == [
        "HAS_COMPONENT", "MAY_INDICATE", "AFFECTS", "RESOLVED_BY", "GENERATES_ERROR", "INDICATES"]
    added = {relation.name: (relation.domain, relation.range) for relation in full.relations}
    assert {key: added[key] for key in ("PART_OF", "ACTS_ON", "OBSERVED_ON", "ADDRESSED_BY", "CLEARED_BY")} == {
        "PART_OF": ("Component", "Component"), "ACTS_ON": ("CorrectiveAction", "Component"),
        "OBSERVED_ON": ("Symptom", "Component"), "ADDRESSED_BY": ("Symptom", "CorrectiveAction"),
        "CLEARED_BY": ("ErrorCode", "CorrectiveAction")}
    data = json.loads((ROOT / "ontology_schema.JSON").read_text(encoding="utf-8"))
    assert all(item.get("rationale") for item in data["relations"] if item.get("added_in"))
    assert full.root == legacy.root == "Asset"


def test_estimate_is_a_range_and_makes_no_call(tmp_path):
    _, doc = read_manual(tmp_path)
    plan = estimate(doc, BuildConfig())
    assert plan["estimated_cost_usd"][0] <= plan["estimated_cost_usd"][1] < 0.05
    assert set(plan["low"]["roles"]) == {"survey", "extract", "verify", "resolve", "gap", "enrich"}
    assert estimate(doc, BuildConfig(verify=False, enrich=False, gap_rounds=0))["high"]["roles"]["verify"]["calls"] == 0


def test_command_line_estimates_and_preflights_without_a_provider_and_refuses_unbudgeted_runs(tmp_path):
    from tests.kg_v4_support import manual_pdf

    pdf = tmp_path / "manual.pdf"
    manual_pdf(pdf)
    script = [sys.executable, str(ROOT / "scripts/kg_build.py"), "--pdf", str(pdf), "--asset-name", "Test pump"]
    plan = subprocess.run([*script, "--estimate"], capture_output=True, text=True, timeout=120)
    assert plan.returncode == 0, plan.stderr
    assert '"provider_calls": 0' in plan.stdout and '"plan"' in plan.stdout
    ready = subprocess.run([*script, "--preflight", "--out", str(tmp_path / "run")], capture_output=True, text=True,
                           timeout=120)
    assert ready.returncode == 0 and '"preflight": "READY"' in ready.stdout, ready.stderr
    refused = subprocess.run([*script, "--out", str(tmp_path / "real")], capture_output=True, text=True, timeout=120)
    assert refused.returncode != 0 and "real calls need --authorize-spend" in refused.stderr
    historical = subprocess.run([*script, "--out", str(tmp_path / "real"), "--authorize-spend", "--budget", "1",
                                 "--ledger", str(ROOT / "campaign/real_call_budget.jsonl")],
                                capture_output=True, text=True, timeout=120)
    assert historical.returncode != 0 and "use a new ledger file" in historical.stderr
    assert not (tmp_path / "real").exists()


def test_the_live_view_follows_the_run_on_the_same_stations(tmp_path):
    from backend.ui.events import EventTranslator

    raw = []
    build(tmp_path, on_event=lambda kind, data: raw.append((kind, data)))
    translator = EventTranslator()
    events = [event for kind, data in raw for event in translator.feed(kind, data, 0.0)]
    stations = [event.data["station"] for event in events if event.kind == "station" and event.data["state"] == "running"]
    assert stations[:3] == ["map", "extract", "check"] and set(stations) <= {"map", "extract", "check", "merge"}
    mapped = next(event for event in events if event.kind == "pages_mapped")
    assert [page["label"] for page in mapped.data["pages"]] == ["diagnostic", "diagnostic", "other"]
    extracted = next(event for event in events if event.kind == "unit_extracted")
    assert extracted.data["total"] == 1 and len(extracted.data["nodes"]) >= 15 and len(extracted.data["edges"]) >= 14
    assert {node["type"] for node in extracted.data["nodes"]} >= {"Symptom", "FailureMode", "CorrectiveAction", "Component"}
    checked = [event for event in events if event.kind == "relations_checked"]
    assert checked and all(edge["tier"] == "green" for edge in checked[0].data["edges"])
    # The remedy found by the gap search appears while the run is still going.
    assert any(node["name"] == "Tighten the drive belts" for event in checked for node in event.data["nodes"])
