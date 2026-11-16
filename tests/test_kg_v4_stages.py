"""The stages of the connected-graph pipeline, one by one, with a scripted model."""

from __future__ import annotations

import asyncio

import fitz
import pytest

from backend.kg_v3.llm import TruncatedResponse
from backend.kg_v4.enrich import Enricher, missing, real_description
from backend.kg_v4.extract import Extractor, uncovered_rows
from backend.kg_v4.gaps import (
    GapRepair,
    Retriever,
    find_gaps,
    follow_entry_pointers,
    link_named_parts,
    resolve_references,
)
from backend.kg_v4.model import CatalogueEntry, Evidence, Fact, Mention
from backend.kg_v4.resolve import Pair, Resolution, assemble, candidates, catalogue_mentions, identity, judge
from backend.kg_v4.sections import build_sections
from backend.kg_v4.survey import build_catalogue, catalogue_brief, reading_units, survey_document
from backend.kg_v4.verify import Verifier, statement
from tests.kg_v4_support import ScriptedModel, action, cause, find, read_manual, record, symptom


@pytest.fixture()
def manual(tmp_path):
    pdf, doc = read_manual(tmp_path)
    return pdf, doc, build_sections(pdf, doc)


def run(coroutine):
    return asyncio.run(coroutine)


def mention(key, type_, name, *, page=1, cites=(), **fields):
    return Mention(key=key, type=type_, name=name, unit_id="u1",
                   evidence=Evidence(page=page, segment_ids=list(cites), anchor="cited" if cites else "unit"), **fields)


def fact(number, relation, source, target, *, verdict="supported", record_="u1:A.R1", origin="extract"):
    return Fact(fact_id=f"f{number}", relation=relation, source=source, target=target, record=record_,
                evidence=Evidence(page=1), verdict=verdict, origin=origin)


# Sections ------------------------------------------------------------------


def test_every_segment_has_a_section_and_pointers_resolve(manual):
    _, doc, sections = manual
    assert sections.by_page == {1: "Maintenance", 2: "Troubleshooting", 3: "Clearing the air line"}
    assert sections.section("p2.t1.r4") == "Troubleshooting"
    assert all(sections.section(segment.segment_id, segment.page) for segment in doc.segments())
    assert sections.resolve("Clear the air line (page 3)") == ([3], "Clearing the air line")
    assert sections.resolve("see Clearing the air line")[0] == [3]


def test_printed_page_numbers_shift_pointers(tmp_path):
    document = fitz.open()
    for number in range(1, 9):
        page = document.new_page(width=595, height=842)
        page.insert_text((72, 60), f"Chapter {number} title", fontsize=16)
        page.insert_text((72, 100), "Body text of the page, long enough to be the common size.", fontsize=9)
        if number > 2:  # two unnumbered front pages: printed page 1 is PDF page 3
            page.insert_text((300, 820), str(number - 2), fontsize=8)
    pdf = tmp_path / "offset.pdf"
    document.save(pdf)
    sections = build_sections(pdf)
    assert sections.page_offset == 2
    assert sections.resolve("see page 4") == ([6], "Chapter 6 title")


def test_junk_bookmarks_are_ignored_and_real_ones_lead_the_trail(tmp_path):
    document = fitz.open()
    for number in range(1, 6):
        page = document.new_page(width=595, height=842)
        page.insert_text((72, 200), f"Topic {number} heading", fontsize=16)
        page.insert_text((72, 240), "Body text of the page, long enough to be the common size.", fontsize=9)
    document.set_toc([[1, "#EV#", number] for number in range(1, 6)])
    junk = tmp_path / "junk.pdf"
    document.save(junk)
    assert build_sections(junk).by_page[3] == "Topic 3 heading"
    document.set_toc([[1, "Service", 1], [2, "Troubleshooting", 3]])
    good = tmp_path / "good.pdf"
    document.save(good)
    assert build_sections(good).by_page[4].startswith("Service > Troubleshooting")


# Survey --------------------------------------------------------------------


def test_catalogue_has_one_entry_per_part_with_hierarchy():
    raw = [
        {"name": "Drive belt", "part_of": "", "category": "mechanical", "description": "Drives the pump.", "page": 1},
        {"name": "Drive belts", "part_of": "Drive unit", "category": "mechanical", "description": "", "page": 4},
        {"name": "Air pump, water chiller or exhaust fan", "part_of": "", "category": "", "description": "", "page": 2},
        {"name": "Water", "part_of": "", "category": "", "description": "", "page": 2},
        {"name": "Machine", "part_of": "", "category": "", "description": "", "page": 2},
    ]
    codes = [{"code": "E-12", "meaning": "Overheat", "page": 6}, {"code": "e12", "meaning": "Overheat", "page": 9}]
    catalogue = build_catalogue(raw, codes)
    parts = {entry.name: entry for entry in catalogue if entry.type == "Component"}
    assert set(parts) == {"Drive belt", "Drive unit", "Air pump", "water chiller", "exhaust fan"}
    assert parts["Drive belt"].aliases == ["Drive belts"] and parts["Drive belt"].part_of == "Drive unit"
    assert parts["Drive belt"].pages == [1, 4] and parts["Drive belt"].description == "Drives the pump."
    assert [(entry.code, entry.pages) for entry in catalogue if entry.type == "ErrorCode"] == [("E-12", [6, 9])]
    brief = catalogue_brief(catalogue, [1])
    assert "Drive belt (part of Drive unit)" in brief and "E-12" not in brief  # the code is far from page 1


def test_survey_reads_every_page_once_and_selects_by_content(manual):
    _, doc, sections = manual
    model = ScriptedModel()
    survey = run(survey_document(model, doc, asset_name="Test pump"))
    assert model.count("kg_v4_survey") == 1
    assert survey.diagnostic_pages() == [1, 2]  # the maintenance sentence counts, the procedure page does not
    assert survey.asset["description"].startswith("Air-operated")
    assert {entry.name for entry in survey.catalogue} >= {"Drive belt", "Pump assembly", "Diaphragm", "Packings"}
    assert "Water" not in {entry.name for entry in survey.catalogue}
    units = reading_units(doc, survey, sections)
    assert [unit.pages for unit in units] == [[1, 2]]
    assert reading_units(doc, survey, sections, extra_pages={3})[0].pages == [1, 2, 3]


def test_a_failed_survey_batch_is_read_anyway(manual):
    _, doc, _ = manual

    def broken(user, schema):
        raise RuntimeError("provider down")

    survey = run(survey_document(ScriptedModel(kg_v4_survey=broken), doc, asset_name="Test pump"))
    assert survey.failed_batches == [[1, 2, 3]] and survey.diagnostic_pages() == [1, 2, 3]


# Extraction ----------------------------------------------------------------


def extractor(manual, model, **options):
    _, doc, sections = manual
    survey = run(survey_document(ScriptedModel(), doc, asset_name="Test pump"))
    unit = reading_units(doc, survey, sections)[0]
    return Extractor(model, doc, sections, asset_name="Test pump", catalogue=survey.catalogue, **options), unit


def test_records_become_mentions_and_facts_with_page_and_section(manual):
    model = ScriptedModel()
    reader, unit = extractor(manual, model)
    records = run(reader.extract(unit))
    user = model.calls[-1]["user"]
    assert user.startswith("Known components of this machine") and "\nPassage:\n" in user
    assert "=== page 1 | section: Maintenance ===" in user  # every page opens with its section
    by_key = {item.key: item for item in records.mentions}
    relations = sorted((item.relation, by_key[item.source].name, by_key[item.target].name) for item in records.facts)
    assert ("MAY_INDICATE", "Pump fails to operate", "Fluid dried on rod") in relations
    assert ("RESOLVED_BY", "Fluid dried on rod", "Clean the rod") in relations
    assert ("ADDRESSED_BY", "Motor ices", "Contact your distributor") in relations  # no placeholder cause
    assert ("OBSERVED_ON", "Pump fails to operate", "Pump assembly") in relations
    assert ("ACTS_ON", "Replace packings", "Packings") in relations
    assert ("AFFECTS", "Cracked drive belt", "Drive belts") in relations  # one mention per part and passage
    assert not any("nspecified" in item.name for item in records.mentions)
    # The merged cell: both causes belong to one record, the other rows to their own.
    rod = next(item for item in records.facts if by_key[item.target].name == "Clean the rod")
    air = next(item for item in records.facts if by_key[item.target].name == "Clear the air line")
    low = next(item for item in records.facts if by_key[item.target].name == "Replace packings")
    assert rod.record == air.record != low.record
    assert all(item.evidence.page and item.evidence.section for item in records.facts)
    assert rod.evidence.segment_ids == ["p2.t1.r3"] and rod.evidence.section == "Troubleshooting"
    belt = next(item for item in records.facts if by_key[item.target].name == "Replace the drive belt")
    assert belt.evidence.section == "Maintenance" and [c.text for c in belt.conditions] == ["if cracked"]
    assert [(ref.text, by_key[ref.mention].name) for ref in records.references] == [
        ("page 3", "Clear the air line"), ("like 'Output is low'", "Output pulses")]
    assert [by_key[key].name for key in records.no_remedy] == ["Loose drive belts"]
    problem = next(item for item in records.mentions if item.name == "Pump fails to operate")
    assert problem.attributes == {"severity": "high"} and problem.description.startswith("The pump does not start")


def test_a_fact_without_citation_is_kept_and_anchored(manual):
    def uncited(user, schema):
        return {"records": [record("R1", problem={**symptom("Output is low", cite="x"), "cite": []}, causes=[
            {**cause("Worn packings", cite="x"), "cite": [], "actions": [
                {**action("Do something the passage never words", cite="x"), "cite": []}]}])],
                "components": [], "unclear": []}

    reader, unit = extractor(manual, ScriptedModel(kg_v4_extract=uncited), reread_rows=False)
    records = run(reader.extract(unit))
    by_key = {item.key: item for item in records.mentions}
    assert len(records.facts) == 2
    indicate = next(item for item in records.facts if item.relation == "MAY_INDICATE")
    assert indicate.evidence.anchor == "matched" and indicate.evidence.segment_ids == ["p2.t1.r4"]
    unworded = next(item for item in records.facts if item.relation == "RESOLVED_BY")
    assert by_key[unworded.target].evidence.anchor == "unit"  # still has the page and section of its entry
    assert unworded.evidence.page == 2 and unworded.evidence.section == "Troubleshooting"


def test_a_cause_that_repeats_the_problem_and_a_bare_number_condition_are_dropped(manual):
    def tautology(user, schema):
        row = find(user, "Worn packings")
        return {"records": [record("R1", problem=symptom("Output is low at the pump outlet", cite=row), causes=[
            cause("Low output", cite=row, actions=[
                action("Replace packings", cite=row, conditions=[("order", "1"), ("if", "if worn")])])])],
                "components": [], "unclear": []}

    reader, unit = extractor(manual, ScriptedModel(kg_v4_extract=tautology), reread_rows=False)
    records = run(reader.extract(unit))
    by_key = {item.key: item for item in records.mentions}
    assert [item.type for item in records.mentions] == ["Symptom", "CorrectiveAction"]  # no cause node
    fact, = records.facts
    assert (fact.relation, by_key[fact.source].name, by_key[fact.target].name) == (
        "ADDRESSED_BY", "Output is low at the pump outlet", "Replace packings")
    assert [(item.kind, item.text) for item in fact.conditions] == [("if", "if worn")]


def test_unused_table_rows_are_read_once_more(manual):
    calls = []

    def partial(user, schema):
        calls.append(user)
        full = ScriptedModel().extract(user, schema)
        if len(calls) == 1:  # the first read skips the packings row
            full["records"] = [item for item in full["records"] if item["problem"]["name"] != "Output is low"]
        return full

    reader, unit = extractor(manual, ScriptedModel(kg_v4_extract=partial))
    records = run(reader.extract(unit))
    assert len(calls) == 2 and "p2.t1.r4" in calls[1] and "(context)" in calls[1]
    again = [item for item in records.facts if item.origin == "reread"]
    by_key = {item.key: item for item in records.mentions}
    assert {by_key[item.target].name for item in again} >= {"Worn packings", "Replace packings"}
    assert uncovered_rows(reader.doc, unit, records) == []


def test_a_truncated_answer_splits_the_passage(manual):
    sizes = []

    def truncating(user, schema):
        owned = [line for line in user.split("Passage", 1)[1].splitlines() if line.startswith("[") and "(context)" not in line]
        sizes.append(len(owned))
        if len(owned) > 8:
            raise TruncatedResponse("too long")
        return ScriptedModel().extract(user, schema)

    reader, unit = extractor(manual, ScriptedModel(kg_v4_extract=truncating), reread_rows=False)
    records = run(reader.extract(unit))
    assert sizes[0] > 8 and len(sizes) >= 3 and not records.failed_reads
    names = {item.name for item in records.mentions}
    assert {"Air supply restricted", "Worn packings", "Cracked drive belt"} <= names
    assert len({item.key for item in records.mentions}) == len(records.mentions)


def test_a_failed_read_is_reported_not_raised(manual):
    def broken(user, schema):
        raise RuntimeError("provider down")

    reader, unit = extractor(manual, ScriptedModel(kg_v4_extract=broken))
    records = run(reader.extract(unit))
    assert records.failed_reads == 1 and not records.facts


# Verification --------------------------------------------------------------


def test_only_a_stated_problem_of_meaning_rejects_a_fact(manual):
    _, doc, _ = manual
    mentions = {"s": mention("s", "Symptom", "Output is low"), "c": mention("c", "FailureMode", "Worn packings"),
                "a": mention("a", "CorrectiveAction", "Replace packings", kind="inspection"),
                "x": mention("x", "CorrectiveAction", "Clean the rod", kind="repair")}
    facts = [fact(1, "MAY_INDICATE", "s", "c", verdict="unchecked"), fact(2, "RESOLVED_BY", "c", "a", verdict="unchecked"),
             fact(3, "RESOLVED_BY", "c", "x", verdict="unchecked"), fact(4, "ADDRESSED_BY", "s", "x", verdict="unchecked")]

    def verdicts(user, schema):
        assert "S2: For the cause 'Worn packings' the manual prescribes [inspection]: 'Replace packings'." in user
        assert "is given directly for the problem 'Output is low'" in user and "[p2.t1.r4]" in user
        return {"answers": [
            {"id": "S1", "verdict": "supported", "problem": "", "reason": ""},
            {"id": "S2", "verdict": "contradicted", "problem": "", "reason": "wording differs"},  # no problem named
            {"id": "S3", "verdict": "contradicted", "problem": "other_entry", "reason": "remedy of the rod row"},
        ]}

    verifier = Verifier(ScriptedModel(kg_v4_verify=verdicts), doc)
    checked = run(verifier.check(facts, mentions, ["p2.t1.r4"]))
    assert [item.verdict for item in checked] == ["supported", "unclear", "contradicted", "unchecked"]
    assert checked[2].reason == "other_entry: remedy of the rod row" and checked[2].confidence == "rejected"
    assert statement(facts[0], mentions) == "The problem 'Output is low' may be caused by 'Worn packings'."


def test_verification_failure_leaves_facts_unchecked(manual):
    _, doc, _ = manual

    def broken(user, schema):
        raise RuntimeError("provider down")

    verifier = Verifier(ScriptedModel(kg_v4_verify=broken), doc)
    mentions = {"s": mention("s", "Symptom", "A"), "c": mention("c", "FailureMode", "B")}
    checked = run(verifier.check([fact(1, "MAY_INDICATE", "s", "c", verdict="unchecked")], mentions, ["p2.t1.r4"]))
    assert checked[0].verdict == "unchecked" and verifier.failed_batches == 1


# Resolution ----------------------------------------------------------------


def test_equal_names_are_one_node_with_aliases_and_all_provenance():
    mentions = [mention("a", "Component", "Drive roll", page=26, cites=["p26.b1"], description="Feeds the wire."),
                mention("b", "Component", "Drive rolls", page=29, cites=["p29.t1.r2"]),
                mention("c", "Component", "drive roll", page=29, cites=["p29.t1.r3"]),
                mention("f", "FailureMode", "Worn drive roll", page=29, cites=["p29.t1.r2"])]
    facts = [fact(1, "AFFECTS", "f", "a"), fact(2, "AFFECTS", "f", "b", record_="u2:A.R4")]
    graph, of_mention = assemble(mentions, facts)
    assert of_mention["a"] == of_mention["b"] == of_mention["c"]
    node = graph.nodes[of_mention["a"]]
    assert node.name == "Drive roll" and node.aliases == ["Drive rolls"]  # a change of case is no alias
    assert node.description == "Feeds the wire." and [item.page for item in node.evidence] == [26, 29, 29]
    assert len(graph.edges) == 1 and [item.record for item in graph.edges[0].facts] == ["u1:A.R1", "u2:A.R4"]


def test_false_friends_are_never_proposed_nor_merged_even_if_a_model_says_same():
    mentions = [mention("x", "Component", "X-axis limit switch"), mention("y", "Component", "Y-axis limit switch"),
                mention("i", "FailureMode", "Inner shaft sealing ring is defective"),
                mention("o", "FailureMode", "Outer shaft sealing ring is defective"),
                mention("t", "FailureMode", "Tool probe does not operate correctly"),
                mention("w", "FailureMode", "Work probe does not operate correctly"),
                mention("l", "Component", "Liner"), mention("cl", "Component", "Cable liner")]
    ask, apart = candidates(mentions)
    assert {(pair.left_name, pair.right_name) for pair in apart} == {
        ("X-axis limit switch", "Y-axis limit switch"),
        ("Inner shaft sealing ring is defective", "Outer shaft sealing ring is defective")}
    asked = {(pair.left_name, pair.right_name): pair.note for pair in ask}
    assert asked == {("Tool probe does not operate correctly", "Work probe does not operate correctly"):
                     "one word differs: tool / work", ("Cable liner", "Liner"): ""}

    forced = Resolution(same=[Pair(left=identity(mentions[0]), right=identity(mentions[1]), type="Component",
                                   left_name="X-axis limit switch", right_name="Y-axis limit switch")])
    facts = [fact(1, "AFFECTS", "i", "x"), fact(2, "AFFECTS", "o", "y")]
    graph, of_mention = assemble(mentions, facts, forced)
    assert of_mention["x"] != of_mention["y"]
    assert graph.kept_apart[0]["reason"] == "different axis or letter"


def test_the_model_decides_close_names_and_a_chain_cannot_join_known_differences():
    mentions = [mention("a", "Component", "Liner"), mention("b", "Component", "Cable liner"),
                mention("c", "Component", "Gun liner"), mention("f", "FailureMode", "Dirty liner")]
    facts = [fact(1, "AFFECTS", "f", "a"), fact(2, "AFFECTS", "f", "b"), fact(3, "AFFECTS", "f", "c")]

    def answers(user, schema):
        assert "N1 [Component] 'Cable liner'" in user and "fact: The fault 'Dirty liner' concerns the part" in user
        ids = schema["properties"]["answers"]["items"]["properties"]["id"]["enum"]
        return {"answers": [{"id": item, "reason": "as the manual uses them", "answer": "same"} for item in ids]}

    model = ScriptedModel(kg_v4_resolve=answers)
    resolution, _ = run(judge(model, mentions, facts))
    # "Liner" was compared with each of the two; the two were never compared with each other.
    assert sorted((pair.left_name, pair.right_name) for pair in resolution.same) == [
        ("Cable liner", "Liner"), ("Gun liner", "Liner")]
    graph, of_mention = assemble(mentions, facts, resolution)
    assert of_mention["a"] == of_mention["b"] != of_mention["c"]
    assert graph.kept_apart and graph.kept_apart[0]["reason"] == "never compared"
    again, _ = run(judge(model, mentions, facts, resolution))
    assert model.count("kg_v4_resolve") == 1 and again.decided() == resolution.decided()  # nothing asked twice
    alone, _ = run(judge(None, mentions, facts))
    assert not alone.same and len(alone.unjudged) == 2  # without a model nothing more is merged


def test_catalogue_gives_names_hierarchy_and_only_touched_parts_enter():
    catalogue = [CatalogueEntry(type="Component", name="Diaphragm pump", aliases=["Pump"], part_of="Fluid section",
                                category="hydraulic", part_number="246887", description="Moves the material.", pages=[5]),
                 CatalogueEntry(type="Component", name="Fluid section", pages=[5]),
                 CatalogueEntry(type="Component", name="Hopper", part_of="Fluid section", pages=[5]),
                 CatalogueEntry(type="ErrorCode", name="Overheat", code="E12", pages=[9])]
    extra, hierarchy = catalogue_mentions(catalogue)
    mentions = [*extra, mention("f", "FailureMode", "Pump stalled"), mention("p", "Component", "pump"),
                mention("e", "ErrorCode", "Motor too hot", code="e-12")]
    graph, of_mention = assemble(mentions, [*hierarchy, fact(1, "AFFECTS", "f", "p")])
    pump = graph.nodes[of_mention["p"]]
    assert pump.name == "Diaphragm pump" and pump.aliases == ["Pump"]
    assert pump.properties == {"category": "hydraulic", "part_number": "246887"}
    names = {node.name for node in graph.nodes.values()}
    assert "Fluid section" in names and "Hopper" not in names  # the untouched sibling stays out
    assert [(edge.relation, graph.nodes[edge.target].name) for edge in graph.out_edges(pump.node_id)] == [
        ("PART_OF", "Fluid section")]
    code = next(node for node in graph.nodes.values() if node.type == "ErrorCode")
    assert code.code and {code.name, *code.aliases} == {"Overheat", "Motor too hot"}  # one code, kept without edges


def test_hierarchy_stays_a_forest_and_rejected_facts_are_listed():
    mentions = [mention("a", "Component", "A part"), mention("b", "Component", "B part"),
                mention("f", "FailureMode", "A part worn"), mention("x", "CorrectiveAction", "Replace A part")]
    facts = [fact(1, "PART_OF", "a", "b"), fact(2, "PART_OF", "b", "a"), fact(3, "AFFECTS", "f", "a"),
             Fact(fact_id="f4", relation="RESOLVED_BY", source="f", target="x", record="r", evidence=Evidence(page=3),
                  verdict="contradicted", reason="other_entry: remedy of another row")]
    graph, _ = assemble(mentions, facts)
    assert sum(edge.relation == "PART_OF" for edge in graph.edges) == 1
    assert [item["reason"] for item in graph.rejected] == ["other_entry: remedy of another row"]
    assert "Replace A part" not in {node.name for node in graph.nodes.values()}


# Gaps ----------------------------------------------------------------------


def built(manual, model=None):
    _, doc, sections = manual
    model = model or ScriptedModel()
    survey = run(survey_document(model, doc, asset_name="Test pump"))
    unit = reading_units(doc, survey, sections)[0]
    records = run(Extractor(model, doc, sections, asset_name="Test pump", catalogue=survey.catalogue).extract(unit))
    extra, hierarchy = catalogue_mentions(survey.catalogue, sections)
    mentions = [*records.mentions, *extra]
    facts = [*records.facts, *hierarchy]
    graph, of_mention = assemble(mentions, facts)
    return doc, sections, records, mentions, facts, graph, of_mention


def test_the_graph_lists_what_a_diagnosis_would_miss(manual):
    *_, graph, _ = built(manual)
    gaps = {(gap.kind, gap.name) for gap in find_gaps(graph)}
    assert gaps == {("cause_without_remedy", "Loose drive belts"), ("cause_without_problem", "Cracked drive belt"),
                    ("problem_without_diagnosis", "Output pulses")}


def test_retrieval_finds_where_a_name_is_written(manual):
    _, doc, _ = manual
    retriever = Retriever(doc)
    assert retriever.search("loose drive belts pump leaks", limit=1, exclude_pages={2}) == ["p3.b4"]
    assert retriever.window(["p3.b3"], radius=1) == ["p3.b2", "p3.b3", "p3.b4"]


def test_gap_repair_finds_remedies_elsewhere_and_declares_what_the_manual_lacks(manual):
    doc, sections, records, mentions, facts, graph, of_mention = built(manual)
    model = ScriptedModel()
    by_key = {item.key: item for item in mentions}
    statuses: dict = {}
    repair = GapRepair(model, doc, sections, asset_name="Test pump", verifier=Verifier(model, doc),
                       references=resolve_references(records.references, sections))
    found_mentions, found_facts, stats = run(repair.repair(graph, by_key, statuses))
    asked = [call["user"] for call in model.calls if call["name"] == "kg_v4_gap"]
    belts = next(text for text in asked if "'Loose drive belts'" in text)
    assert "[p2.t1.r6]" in belts and "[p3.b4]" in belts  # its own row, and the page where the remedy is written
    assert stats["asked"] == 3 and stats["new_facts"] == 2 and all(item.verdict == "supported" for item in found_facts)
    assert {item.origin for item in found_facts} == {"gap_repair"}
    graph, of_mention = assemble([*mentions, *found_mentions], [*facts, *found_facts], statuses=statuses)
    loose = next(node for node in graph.nodes.values() if node.name == "Loose drive belts")
    remedy = graph.out_edges(loose.node_id, "RESOLVED_BY")[0]
    assert graph.nodes[remedy.target].name == "Tighten the drive belts"
    assert remedy.facts[0].evidence.page == 3 and remedy.facts[0].evidence.section == "Clearing the air line"
    assert loose.properties["remedy_status"] == "stated"
    cracked = next(node for node in graph.nodes.values() if node.name == "Cracked drive belt")
    assert cracked.properties["entry_status"] == "none_in_manual"
    pulses = next(node for node in graph.nodes.values() if node.name == "Output pulses")
    assert pulses.properties["diagnosis_status"] == "not_stated"
    assert find_gaps(graph) == []
    again = run(repair.repair(graph, {**by_key, **{item.key: item for item in found_mentions}}, statuses))
    assert again[2]["calls"] == 0  # nothing is asked twice


def test_gap_budget_defers_instead_of_guessing(manual):
    doc, sections, records, mentions, facts, graph, _ = built(manual)
    statuses: dict = {}
    repair = GapRepair(ScriptedModel(), doc, sections, asset_name="Test pump", max_calls=1)
    _, _, stats = run(repair.repair(graph, {item.key: item for item in mentions}, statuses))
    assert stats["calls"] == 1 and stats["deferred"] >= 1
    assert len(statuses) <= 1  # a gap that was not asked gets no status


def test_a_pointer_to_another_entry_is_followed(manual):
    _, sections, records, mentions, facts, graph, of_mention = built(manual)
    by_key = {item.key: item for item in mentions}
    references = resolve_references(records.references, sections)
    assert [(ref.text, ref.target_pages) for ref in references] == [("page 3", [3]), ("like 'Output is low'", [])]
    pointed = follow_entry_pointers(graph, references, of_mention, by_key)
    assert [(item.relation, by_key[item.source].name, by_key[item.target].name, item.origin) for item in pointed] == [
        ("MAY_INDICATE", "Output pulses", "Worn packings", "reference")]
    assert "as for 'Output is low'" in pointed[0].conditions[0].text


def test_an_item_is_linked_to_the_part_its_own_name_names():
    mentions = [mention("m", "Component", "Motor"), mention("fm", "Component", "Fan motor"),
                mention("f", "FailureMode", "Fan motor bearings worn"), mention("s", "Symptom", "Motor hums"),
                mention("a", "CorrectiveAction", "Replace the fan motors"), mention("z", "FailureMode", "Blown fuse")]
    facts = [fact(1, "MAY_INDICATE", "s", "f"), fact(2, "RESOLVED_BY", "f", "a"), fact(3, "MAY_INDICATE", "s", "z"),
             fact(4, "AFFECTS", "z", "m")]
    graph, _ = assemble(mentions, facts)
    by_key = {item.key: item for item in mentions}
    found = link_named_parts(graph, mentions)
    links = {(item.relation, by_key[item.source].name, by_key[item.target].name) for item in found}
    # The longest part name wins: a fan motor is not also linked to every motor.
    assert links == {("AFFECTS", "Fan motor bearings worn", "Fan motor"), ("OBSERVED_ON", "Motor hums", "Motor"),
                     ("ACTS_ON", "Replace the fan motors", "Fan motor")}
    assert {item.origin for item in found} == {"name_mention"}
    graph, _ = assemble(mentions, [*facts, *found])
    assert "Fan motor" in {node.name for node in graph.nodes.values()}  # the link brings the part in
    assert link_named_parts(graph, mentions) == []


# Enrichment ----------------------------------------------------------------


def test_enrichment_writes_what_nodes_lack_from_their_own_passages(manual):
    doc, sections, records, mentions, facts, graph, _ = built(manual)
    model = ScriptedModel()
    before = {node.name: missing(node) for node in graph.nodes.values()}
    assert before["Pump fails to operate"] == [] and before["Clean the rod"] == ["description", "instruction_text"]
    stats = run(Enricher(model, doc, asset_name="Test pump",
                         references=resolve_references(records.references, sections)).enrich(graph))
    prompt = "\n".join(call["user"] for call in model.calls if call["name"] == "kg_v4_enrich")
    assert "'Pump fails to operate'" not in prompt  # a node that lacks nothing costs nothing
    block = prompt.split("'Clear the air line'", 1)[1].split("\n\nN", 1)[0]
    assert "[p2.t1.r2]" in block and "The manual points to:" in block and find(block, "blow it out") == "p3.b3"
    nodes = {node.name: node for node in graph.nodes.values()}
    assert real_description(nodes["Clean the rod"])
    assert nodes["Clear the air line"].properties["instruction_text"].startswith("Close the air supply valve")
    assert nodes["Output is low"].properties["severity"] == "medium" and nodes["Output is low"].inferred == ["severity"]
    assert nodes["Pump fails to operate"].properties["severity"] == "high"  # what was read is not overwritten
    assert nodes["Drive belt"].description == "Belt that drives the pump; it is inspected every week."
    assert stats["nodes_improved"] >= stats["nodes_lacking"] - 5 and stats["nodes_deferred"] == 0


# Diagram pages -------------------------------------------------------------


def test_a_drawn_flowchart_page_is_shown_as_image_and_read_with_its_neighbours(tmp_path):
    from backend.kg_v3.reader import read_document
    from backend.kg_v4.images import DiagramImages, drawn_pages, pages_to_read_with
    from scripts.kg_v3 import load_evidence

    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 60), "No heat", fontsize=16)
    page.insert_text((72, 100), "If the oven does not heat, follow the flowchart on the next page.", fontsize=9)
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 60), "Keypad failure", fontsize=16)
    for index in range(60):  # boxes and arrows, almost no text
        page.draw_line((72 + 5 * index, 200), (72 + 5 * index, 400))
    page = document.new_page(width=595, height=842)
    page.insert_text((72, 60), "Specifications", fontsize=16)
    pdf = tmp_path / "flow.pdf"
    document.save(pdf)
    evidence, count, _ = load_evidence(pdf, {"name": "Oven", "description": "Oven", "brand": "x", "model": "x",
                                             "asset_type": "oven"})
    doc = read_document(list(evidence), page_count=count)
    images = DiagramImages(pdf, doc)
    assert images.drawn == {2} and 2 in images.pages
    assert drawn_pages(doc, {2: {"drawing_count": 10}}) == set()
    assert pages_to_read_with({1}, {2}) == {2} and pages_to_read_with({1}, {3}) == set()
    assert pages_to_read_with({1}, {2, 3}) == {2, 3}  # a flowchart may run over several pages
    shown, _ = images.for_segments([segment.segment_id for segment in doc.pages[2]])
    assert len(shown) == 1 and shown[0].startswith("data:image/png;base64,")


def test_a_diagram_page_that_yields_no_fact_is_read_once_more(manual):
    class Images:  # page 2 is shown as an image, as a flowchart page would be
        pages = {2}

        def for_segments(self, segment_ids):
            return [], {}

    calls = []

    def first_read_misses_page_2(user, schema):
        calls.append(user)
        full = ScriptedModel().extract(user, schema)
        if len(calls) == 1:
            full["records"] = [item for item in full["records"] if item["record"] == "R6"]  # page 1 only
        return full

    reader, unit = extractor(manual, ScriptedModel(kg_v4_extract=first_read_misses_page_2), reread_rows=False)
    reader.images = Images()
    records = run(reader.extract(unit))
    assert len(calls) == 2
    owned = [line for line in calls[1].split("Passage", 1)[1].splitlines()
             if line.startswith("[") and "(context)" not in line]
    assert owned and all(line.startswith("[p2.") for line in owned)  # only the diagram page is owned
    assert "[p1.b1] (context) Maintenance" in calls[1]  # with the title of the page before
    assert any(fact.origin == "reread" and fact.relation == "RESOLVED_BY" for fact in records.facts)
    assert any("diagram page 2 read again" in note for note in records.notes)
    # A page that already gave facts is not read again.
    calls.clear()
    reader2, unit2 = extractor(manual, ScriptedModel(kg_v4_extract=lambda u, s: (calls.append(u), ScriptedModel().extract(u, s))[1]),
                               reread_rows=False)
    reader2.images = Images()
    run(reader2.extract(unit2))
    assert len(calls) == 1
