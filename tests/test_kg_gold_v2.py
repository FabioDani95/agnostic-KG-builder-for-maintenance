"""Gold v2 tool: a small example gold is validated, counted and exported without reading any PDF."""

from __future__ import annotations

import copy

from scripts.kg_gold_v2 import (
    check,
    export_claims,
    iaa_pages,
    pages_sheet,
    quote_overlap,
    review_sample,
    review_sheet,
    segments_digest,
    statistics,
)

SEGMENTS = {
    "p1.b1": "Owner's manual of the example pump",
    "p2.t1.r2": "Pump fails to operate | 1. Restricted air supply | 1. Clear the air line; inspect the regulator "
                "and replace if at fault",
    "p2.t1.r3": "E-07 | Low oil level | Add oil. See page 3",
    "p3.b1": "Adding oil",
    "p3.b2": "1. Stop the pump. 2. Remove the filler cap. 3. Add oil up to the mark.",
    "p3.b3": "Replace the hose if cracked.",
}


def evidence(page: int, segments: list[str], quote: str) -> dict:
    return {"pages": [page], "section": "Troubleshooting", "segments": segments, "quote": quote}


def example() -> dict:
    questions = [{"id": f"Q{number:02d}", "type": "symptom_causes_actions", "text": f"Question {number}?",
                  "answer_items": ["B001"]} for number in range(1, 13)]
    questions += [
        {"id": "Q13", "type": "code_meaning_actions", "text": "What does E-07 mean?", "answer_items": ["B002"]},
        {"id": "Q14", "type": "procedure_steps", "text": "How do I add oil?", "answer_items": ["P001"]},
        {"id": "Q15", "type": "maintenance_condition", "text": "When do I replace the hose?", "answer_items": ["B003"]},
    ]
    return {
        "schema": "kg-gold-2", "manual_id": "example", "created": "2026-11-13",
        "annotator": {"kind": "ai", "model": "claude-fable-5-2", "human_review": False},
        "reader": {"segments_sha256": segments_digest(SEGMENTS), "note": ""},
        "pages": [
            {"page": 1, "content": ["cover"], "diagnostic": False, "note": "Cover"},
            {"page": 2, "content": ["troubleshooting table"], "diagnostic": True, "note": "Faults and one code"},
            {"page": 3, "content": ["procedure"], "diagnostic": True, "note": "Adding oil, hose check"},
        ],
        "branches": [
            {"id": "B001", "category": "fault", "scope": "core",
             "problem": {"type": "symptom", "text": "Pump fails to operate", "code": ""},
             "cause": {"text": "Restricted air supply", "stated": True},
             "actions": [
                 {"order": 1, "kind": "repair", "text": "Clear the air line", "expected": "", "condition": "",
                  "component": "air line"},
                 {"order": 2, "kind": "inspection", "text": "Inspect the regulator", "expected": "", "condition": "",
                  "component": "regulator"},
                 {"order": 3, "kind": "repair", "text": "Replace the regulator", "expected": "",
                  "condition": "if at fault", "component": "Regulator"},
             ],
             "components": ["air line", "regulator"], "conditions": [], "references": [],
             "evidence": evidence(2, ["p2.t1.r2"], "Restricted air supply ... Clear the air line"),
             "certainty": "certain", "note": ""},
            {"id": "B002", "category": "error_code", "scope": "core",
             "problem": {"type": "code", "text": "Low oil level", "code": "E-07"},
             "cause": None,
             "actions": [{"order": 1, "kind": "repair", "text": "Add oil", "expected": "", "condition": "",
                          "component": ""}],
             "components": [], "conditions": [],
             "references": [{"text": "See page 3", "target_pages": [3], "target_items": ["P001"]}],
             "evidence": evidence(2, ["p2.t1.r3"], "E-07 Low oil level Add oil"),
             "certainty": "certain", "note": ""},
            {"id": "B003", "category": "condition_maintenance", "scope": "extended",
             "problem": {"type": "inspection", "text": "Hose condition", "code": ""},
             "cause": None,
             "actions": [{"order": 1, "kind": "repair", "text": "Replace the hose", "expected": "",
                          "condition": "if cracked", "component": "hose"}],
             "components": ["hose"], "conditions": [], "references": [],
             "evidence": evidence(3, ["p3.b3"], "Replace the hose if cracked"),
             "certainty": "certain", "note": ""},
        ],
        "procedures": [
            {"id": "P001", "category": "procedure", "scope": "extended", "title": "Adding oil",
             "steps": ["Stop the pump", "Remove the filler cap", "Add oil up to the mark"],
             "evidence": evidence(3, ["p3.b1", "p3.b2"], "Remove the filler cap"), "certainty": "certain", "note": ""},
        ],
        "entities": {
            "components": [
                {"name": "air line", "aliases": [], "part_of": "", "part_number": "", "pages": [2]},
                {"name": "regulator", "aliases": ["air regulator"], "part_of": "air line", "part_number": "R-1",
                 "pages": [2]},
                {"name": "hose", "aliases": [], "part_of": "", "part_number": "", "pages": [3]},
            ],
            "symptoms": [{"name": "Pump fails to operate", "aliases": []}],
            "codes": [{"code": "E-07", "meaning": "Low oil level", "aliases": []}],
            "false_friends": [{"a": "air line", "b": "oil line", "reason": "different circuits"}],
            "synonyms": [{"names": ["regulator", "air regulator"], "note": ""}],
        },
        "questions": questions,
    }


def problems(gold: dict, sheet: str | None = None) -> list[str]:
    return check(gold, SEGMENTS, 3, pages_sheet(gold) if sheet is None else sheet)


def test_the_example_gold_is_valid():
    assert problems(example()) == []


def test_quotes_are_matched_by_words_not_characters():
    assert quote_overlap("restricted AIR-supply ... clear the air line", SEGMENTS["p2.t1.r2"]) == 1.0
    gold = example()
    gold["branches"][0]["evidence"]["quote"] = "The motor bearing is worn and noisy"
    assert any("B001: quote not found" in item for item in problems(gold))


def test_segments_must_exist_in_the_current_reader_and_on_the_cited_page():
    gold = example()
    gold["branches"][0]["evidence"]["segments"] = ["p2.t1.r9"]
    assert any("p2.t1.r9 is not in the current reader" in item for item in problems(gold))
    gold = example()
    gold["branches"][0]["actions"][0]["segments"] = ["p3.b3"]
    assert any("p3.b3 is on a page missing from evidence.pages" in item for item in problems(gold))
    gold = example()
    gold["reader"]["segments_sha256"] = "0" * 64
    assert any("segments_sha256" in item for item in problems(gold))


def test_every_page_is_in_the_map_and_in_the_sheet():
    gold = example()
    del gold["pages"][0]
    assert any("missing from the page map: [1]" in item for item in problems(gold))
    assert any("PAGINE.md: missing pages: [2]" in item
               for item in problems(example(), "| 1 | cover | no | x |\n| 3 | procedure | sì | x |\n"))


def test_diagnostic_pages_and_items_agree():
    gold = example()
    gold["pages"][2]["diagnostic"] = False
    found = problems(gold)
    assert any("B003: page 3 holds a extended item but is not marked diagnostic" in item for item in found)
    gold = example()
    gold["pages"][0]["diagnostic"] = True
    assert any("page 1 is marked diagnostic but no item cites it" in item for item in problems(gold))


def test_references_questions_and_ids_point_to_existing_items():
    gold = example()
    gold["branches"][1]["references"][0]["target_items"] = ["P009"]
    gold["questions"][0]["answer_items"] = ["B777"]
    gold["branches"][2]["id"] = "B001"
    found = problems(gold)
    assert any("reference to unknown item P009" in item for item in found)
    assert any("Q01: answer item B777 does not exist" in item for item in found)
    assert any("B001: ID used 2 times" in item for item in found)
    gold = example()
    gold["branches"][1]["references"][0] = {"text": "See the dealer catalogue", "target_pages": [], "target_items": []}
    assert any("points nowhere" in item for item in problems(gold))


def test_core_items_need_segments_actions_and_listed_components():
    gold = example()
    gold["branches"][0]["evidence"]["segments"] = []
    gold["branches"][0]["actions"] = []
    gold["branches"][2]["components"] = ["gearbox"]
    found = problems(gold)
    assert any("B001: core item without segments" in item for item in found)
    assert any("B001: no action" in item for item in found)
    assert any("component 'gearbox' is not in the inventory" in item for item in found)
    gold = example()
    gold["branches"][1]["actions"] = []  # a code may have a meaning only
    assert problems(gold) == []


def test_schema_scope_and_ambiguity_are_checked():
    gold = example()
    gold["branches"][0]["scope"] = "extended"
    gold["branches"][1]["certainty"] = "ambiguous"
    found = problems(gold)
    assert any("category fault has scope core" in item for item in found)
    assert any("B002: ambiguous without the reason" in item for item in found)
    gold = example()
    gold["annotator"]["kind"] = "human"
    assert problems(gold)[0].startswith("schema: annotator.kind")


def test_questions_cover_core_and_extended_categories():
    gold = example()
    gold["questions"] = gold["questions"][:14]
    found = problems(gold)
    assert any("questions: 14, expected 15 to 30" in item for item in found)
    assert any("no question about category condition_maintenance" in item for item in found)


def test_statistics_count_items_by_category_and_scope():
    numbers = statistics(example())
    assert numbers["by_category"] == {"fault": 1, "error_code": 1, "condition_maintenance": 1, "procedure": 1}
    assert numbers["by_scope"] == {"core": 2, "extended": 2}
    assert numbers["actions_by_kind"] == {"repair": 4, "inspection": 1}
    assert (numbers["diagnostic_pages"], numbers["components"], numbers["questions"]) == (2, 3, 15)


def test_the_gold_says_which_scopes_were_independently_verified():
    gold = example()
    assert statistics(gold)["independently_verified_scopes"] == []
    gold["verification"] = {"independent_scopes": ["core", "extended"], "note": "context annotated once"}
    assert problems(gold) == [] and statistics(gold)["independently_verified_scopes"] == ["core", "extended"]
    gold["verification"]["independent_scopes"] = ["everything"]
    assert problems(gold)[0].startswith("schema: verification.independent_scopes")


def test_claims_have_the_gold_v1_format_without_procedures():
    data = export_claims(example())
    claims = data["claims"]
    assert [claim["claim_id"] for claim in claims] == ["B001.1", "B001.2", "B001.3", "B002.1", "B003.1"]
    first, third, code = claims[0], claims[2], claims[3]
    assert first["indicator"] == "Pump fails to operate" and first["failure"] == "Restricted air supply"
    assert first["failure_stated"] and first["action_kind"] == "repair" and first["category"] == "fault"
    assert first["indicator_segments"] == first["failure_segments"] == first["action_segments"] == ["p2.t1.r2"]
    assert third["conditions"] == "if at fault" and third["scope"] == "core"
    assert code["failure"] == "" and not code["failure_stated"] and code["failure_segments"] == [] and code["code"] == "E-07"
    assert data["branches"] == 3 and data["pages"] == [2, 3] and "AI" in data["annotator"]
    gold = example()
    gold["branches"][1]["actions"] = []
    assert export_claims(gold)["claims"][3]["action"] == ""


def test_samples_are_reproducible_and_stratified():
    gold = example()
    assert iaa_pages(gold) == iaa_pages(copy.deepcopy(gold)) and len(iaa_pages(gold)) == 1
    chosen, others = review_sample(gold)
    assert {item["category"] for item in chosen} == {"fault", "error_code", "condition_maintenance", "procedure"}
    assert [page["page"] for page in others] == [1]
    sheet = review_sheet(gold)
    assert "fatto da un'AI" in sheet and "[ ] corretto" in sheet and "pagina 1" in sheet
