"""Offline measurement tools: quality card, loss analysis and the rebuild of saved V3 graphs."""

from __future__ import annotations

import asyncio
import json

from backend.kg_v4.gaps import link_named_parts
from backend.kg_v4.metrics import scorecard
from backend.kg_v4.model import Evidence, Fact, Mention
from backend.kg_v4.pipeline import Builder
from backend.kg_v4.resolve import assemble
from backend.kg_v4.sections import build_sections
from backend.kg_v4.survey import build_catalogue, is_the_machine, machine_words
from scripts.kg_loss_analysis import STAGES, analyse, markdown
from scripts.kg_rebuild_from_v3 import convert
from scripts.kg_scorecard import ROWS, label
from scripts.kg_scorecard import markdown as cards_markdown
from tests.kg_v4_support import ASSET, ScriptedModel, read_manual


def claim(claim_id, indicator, failure, action, segment):
    return {"claim_id": claim_id, "branch_id": claim_id.split(".")[0], "indicator": indicator, "failure": failure,
            "action": action, "conditions": "", "indicator_segments": [segment], "failure_segments": [segment],
            "action_segments": [segment]}


def test_each_claim_is_placed_at_the_stage_where_its_weakest_link_stopped():
    claims = [
        claim("R1.1", "Pump fails to operate", "Air supply restricted", "Clear the line", "p2.t1.r2"),
        claim("R2.1", "Output is low", "Worn packings", "Replace packings", "p2.t1.r4"),
        claim("R3.1", "Motor ices", "Wet air", "Dry the air", "p2.t1.r5"),
        claim("R4.1", "Pump leaks", "Loose belts", "Tighten belts", "p2.t1.r6"),
        claim("R5.1", "Belt squeals", "Belt worn", "Replace belt", "p7.b3"),
        claim("R6.1", "Noise", "Bearing worn", "Replace bearing", "p2.t1.r8"),
        claim("R7.1", "Code E1", "", "", "p2.t1.r9"),  # an indication only: not a chain
    ]
    run = {
        "read_pages": {2},
        "proposals": [("MAY_INDICATE", "Pump leaks", "Loose belts", {"p2.t1.r6"}),
                      ("RESOLVED_BY", "Loose belts", "Tighten belts", {"p2.t1.r6"}),
                      ("MAY_INDICATE", "Noise", "Bearing worn", {"p2.t1.r8"})],
        "kept": [("MAY_INDICATE", "Pump fails to operate", "Air supply restricted", {"p2.t1.r2"}, True),
                 ("RESOLVED_BY", "Air supply restricted", "Clear the line", {"p2.t1.r2"}, True),
                 ("MAY_INDICATE", "Output is low", "Worn packings", {"p2.t1.r4"}, True),
                 ("RESOLVED_BY", "Worn packings", "Replace packings", {"p2.t1.r4"}, True),
                 ("MAY_INDICATE", "Motor ices", "Wet air", {"p2.t1.r5"}, True),
                 ("MAY_INDICATE", "Pump leaks", "Loose belts", {"p2.t1.r6"}, True),
                 ("RESOLVED_BY", "Loose belts", "Tighten belts", {"p2.t1.r6"}, False)],
        "excluded": [("RESOLVED_BY", "Wet air", "Dry the air", {"p2.t1.r5"}, "reviewer_rejection")],
    }
    result = analyse(claims, run, recovered={"R1.1"})
    stages = {row["claim_id"]: (row["stage"], row["gate"]) for row in result["rows"]}
    assert stages == {
        "R1.1": ("recovered", ""), "R2.1": ("in_graph_not_matched", ""),
        "R3.1": ("discarded_by_gate", "reviewer_rejection"), "R4.1": ("in_graph_untrusted", ""),
        "R5.1": ("page_not_read", ""), "R6.1": ("lost_after_extraction", ""),
    }
    assert result["claims"] == 6 and sum(result["claims_by_stage"].values()) == 6
    assert result["gates"] == {"reviewer_rejection": 1} and result["pages_with_unextracted_claims"] == {7: 1}
    table = markdown("demo", result)
    assert all(stage in table for stage in STAGES) and "p7 (1)" in table


def test_a_card_reads_any_graph_file_and_names_what_it_measures(tmp_path):
    pdf, doc = read_manual(tmp_path)
    result = asyncio.run(Builder(doc=doc, asset=ASSET, llm=ScriptedModel(), pdf_path=pdf).run())
    run = tmp_path / "runs" / "test_pump" / "kg4_r1"
    run.mkdir(parents=True)
    (run / "graph.json").write_text(json.dumps(result.document))
    assert label(run / "graph.json") == ("test_pump", "kg4_r1")
    item = {"manual": "test_pump", "run": "kg4_r1", "graph": "runs/test_pump/kg4_r1/graph.json",
            **scorecard(result.document), "gold": None, "saved_recall": None}
    text = cards_markdown([item])
    assert "| Descrizioni vere (diverse dal nome) | 100% |" in text and "| Nodi generici usati come ponte | 0 |" in text
    assert "senza gold" in text and "Segnaposto: FailureMode.material_context 5" in text
    assert all(name in text for name, _ in ROWS)


def v3_graph():
    def node(key, kind, name, segment, **properties):
        return {"id": key, "type": kind, "name": name, "properties": properties, "stated_in_source": True,
                "evidence": [{"segment_id": segment}]}

    def edge(key, kind, source, target, tier, segment, record="u1:A.R1"):
        return {"id": key, "type": kind, "from": source, "to": target, "tier": tier,
                "occurrences": [{"tier": tier, "record": record, "evidence": [{"segment_id": segment}],
                                 "conditions": [{"kind": "if", "text": "if cracked", "cite": [], "scope": "relation"}]}]}

    return {"version": "kg-v3-graph-2", "source_title": "manual.pdf", "nodes": [
        {"id": "asset", "type": "Asset", "name": "Test pump", "properties": {"name": "Test pump"}},
        node("s1", "Symptom", "Motor ices", "p2.t1.r5"),
        node("ph", "FailureMode", "Unspecified cause of motor ices", "p2.t1.r5"),
        node("a1", "CorrectiveAction", "Contact your distributor", "p2.t1.r5", action_kind="escalation"),
        node("s2", "Symptom", "Pump leaks", "p2.t1.r6"),
        node("f2", "FailureMode", "Loose drive belts", "p2.t1.r6"),
        node("c1", "Component", "Drive belt", "p1.b2"),
        node("c2", "Component", "Drive belts", "p2.t1.r6"),
        node("f3", "FailureMode", "Cracked drive belt", "p1.b2"),
        node("a2", "CorrectiveAction", "Replace the drive belt", "p1.b2", action_kind="repair"),
    ], "edges": [
        edge("e1", "MAY_INDICATE", "s1", "ph", "green", "p2.t1.r5"),
        edge("e2", "RESOLVED_BY", "ph", "a1", "green", "p2.t1.r5"),
        edge("e3", "MAY_INDICATE", "s2", "f2", "yellow", "p2.t1.r6"),
        edge("e4", "AFFECTS", "f3", "c1", "green", "p1.b2"),
        edge("e6", "AFFECTS", "f2", "c2", "green", "p2.t1.r6"),
        edge("e7", "RESOLVED_BY", "f3", "a2", "green", "p1.b2"),
        {"id": "e5", "type": "HAS_COMPONENT", "from": "asset", "to": "c1", "derived": True, "occurrences": []},
    ], "excluded_relations": [
        {"relation": "RESOLVED_BY", "source": "FailureMode:Loose drive belts", "target": "CorrectiveAction:Tighten the belts",
         "certificate": {"segment_ids": ["p3.b4"], "rejected_by": {"kind": "agent"}}}]}


def test_a_saved_v3_graph_is_rebuilt_without_placeholders_and_with_component_links(tmp_path):
    pdf, doc = read_manual(tmp_path)
    sections = build_sections(pdf, doc)
    mentions, facts, stats = convert(v3_graph(), doc, sections, keep_excluded=False)
    assert stats == {"placeholder_causes_removed": 1, "direct_links": 1, "excluded_kept": 0}
    assert "Unspecified cause of motor ices" not in {item.name for item in mentions}
    graph, _ = assemble(mentions, facts)
    graph, of_mention = assemble(mentions, [*facts, *link_named_parts(graph, mentions)])
    names = {node.node_id: node.name for node in graph.nodes.values()}
    edges = {(edge.relation, names[edge.source], names[edge.target]): edge for edge in graph.edges}
    direct = edges[("ADDRESSED_BY", "Motor ices", "Contact your distributor")]
    assert direct.facts[0].verdict == "supported" and direct.facts[0].evidence.section == "Troubleshooting"
    assert [item.text for item in direct.facts[0].conditions] == ["if cracked"]
    assert edges[("MAY_INDICATE", "Pump leaks", "Loose drive belts")].facts[0].verdict == "unclear"
    # "Drive belt" and "Drive belts" are one part, and the action that names it is linked to it.
    assert of_mention["c1"] == of_mention["c2"]
    assert edges[("AFFECTS", "Loose drive belts", "Drive belt")].facts[0].origin == "import"
    assert edges[("ACTS_ON", "Replace the drive belt", "Drive belt")].facts[0].origin == "name_mention"
    kept, kept_facts, kept_stats = convert(v3_graph(), doc, sections, keep_excluded=True)
    assert kept_stats["excluded_kept"] == 1 and "Tighten the belts" in {item.name for item in kept}
    tighten = next(item.key for item in kept if item.name == "Tighten the belts")
    assert next(fact for fact in kept_facts if fact.target == tighten).verdict == "unclear"


def test_the_machine_itself_is_not_a_part_and_never_a_hub():
    asset = {"name": "DRB booster", "asset_type": "vacuum booster pump"}
    words = machine_words(asset)
    assert is_the_machine("Pump", words) and is_the_machine("pumps", words)
    assert not is_the_machine("Pump rotor", words) and not is_the_machine("Motor", words)
    catalogue = build_catalogue([{"name": "Pump", "page": 1}, {"name": "Pump rotor", "page": 1}], [], words)
    assert [entry.name for entry in catalogue] == ["Pump rotor"]

    def mention(key, kind, name):
        return Mention(key=key, type=kind, name=name, unit_id="u1", evidence=Evidence(page=1))

    mentions = [mention("p", "Component", "Pump"), mention("r", "Component", "Pump rotor"),
                mention("f1", "FailureMode", "Pump gets too hot"), mention("f2", "FailureMode", "Pump rotor seized"),
                mention("s", "Symptom", "Pump is loud")]
    facts = [Fact(fact_id="1", relation="MAY_INDICATE", source="s", target="f1", record="r", evidence=Evidence(page=1)),
             Fact(fact_id="2", relation="MAY_INDICATE", source="s", target="f2", record="r", evidence=Evidence(page=1))]
    graph, _ = assemble(mentions, facts)
    by_key = {item.key: item for item in mentions}
    assert {(by_key[fact.source].name, by_key[fact.target].name) for fact in link_named_parts(graph, mentions, words)} == {
        ("Pump rotor seized", "Pump rotor")}
    assert len(link_named_parts(graph, mentions)) == 3  # without the guard every item hangs on "Pump"


def test_versions_are_compared_with_a_tolerance_band_and_three_views_of_recall():
    from scripts.kg_compare import recall, verdict

    claims = [{"claim_id": "R1.1", "branch_id": "R1"}, {"claim_id": "R1.2", "branch_id": "R1"},
              {"claim_id": "R2.1", "branch_id": "R2"}, {"claim_id": "R3.1", "branch_id": "R3"}]
    found = recall(claims, {"R1.1", "R2.1"})
    # One branch complete, one half found, one missed: strict 1/3, partial credit (0.5 + 1 + 0) / 3.
    assert found["recall_branches"] == 0.3333 and found["recall_coverage"] == 0.5 and found["recall_claims"] == 0.5
    assert found["branch_counts"] == [1, 3] and found["claim_counts"] == [2, 4]
    assert recall([], set())["recall_branches"] is None
    assert verdict("recall_branches", 0.52, 0.50) == "same"  # inside the band: replicas differ by as much
    assert verdict("recall_branches", 0.60, 0.50) == "better" and verdict("recall_branches", 0.40, 0.50) == "worse"
    assert verdict("excluded", 0.10, 0.30) == "better"  # fewer exclusions is better
    assert verdict("generic_bridges", 0, 13) == "better" and verdict("nodes", 10, 500) == ""
    assert verdict("recall_claims", None, 0.5) == ""


def test_loss_analysis_reads_runs_of_the_connected_graph_pipeline(tmp_path):
    from backend.kg_v3.run_state import atomic_json
    from scripts.kg_loss_analysis import load_run

    pdf, doc = read_manual(tmp_path)
    run = tmp_path / "run"
    result = asyncio.run(Builder(doc=doc, asset=ASSET, llm=ScriptedModel(), pdf_path=pdf, workdir=run).run())
    atomic_json(run / "graph.json", result.document)
    atomic_json(run / "report.json", result.report)
    loaded = load_run(run)
    assert loaded["read_pages"] == {1, 2}
    assert ("RESOLVED_BY", "Fluid dried on rod", "Clean the rod", {"p2.t1.r3"}) in loaded["proposals"]
    # The direct remedy is shown as the gold writes it: an unnamed cause between problem and action.
    assert ("RESOLVED_BY", "Unspecified cause of Motor ices", "Contact your distributor", {"p2.t1.r5"}, True) in loaded["kept"]
    claims = [claim("R1.1", "Motor ices", "", "Contact your distributor", "p2.t1.r5"),
              claim("R2.1", "Fan is loud", "Bearing worn", "Replace bearing", "p2.t1.r4")]
    stages = {row["claim_id"]: row["stage"] for row in analyse(claims, loaded, recovered=set())["rows"]}
    # Both have a trusted candidate on their row; without a judgement neither counts as recovered.
    assert stages == {"R1.1": "in_graph_not_matched", "R2.1": "in_graph_not_matched"}


def test_a_judgement_is_read_only_against_the_gold_it_was_made_on(tmp_path):
    import pytest

    from scripts.kg_loss_analysis import recovered_claims
    from scripts.kg_v3_kpi import GOLDS

    assert set(GOLDS) == {"gold", "gold_v2"}
    judged = tmp_path / "kpi.json"
    judged.write_text(json.dumps({"gold": "gold_v2", "manuals": {"m": {"systems": {"v3_r1": {"missing_claims": []}}}}}))
    with pytest.raises(ValueError, match="judged on gold_v2"):
        recovered_claims(judged, "m", "v3_r1", "gold")
