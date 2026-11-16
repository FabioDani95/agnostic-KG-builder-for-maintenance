"""Pages without usable text: chosen by free rules, read from their image, cited like any other."""

from __future__ import annotations

import asyncio

from backend.adapters.pdf import page_layout_inventory
from backend.kg_v4.estimate import estimate
from backend.kg_v4.extract import empty_condition, repeats
from backend.kg_v4.pipeline import BuildConfig, Builder
from backend.kg_v4.sections import SectionIndex
from backend.kg_v4.transcribe import add_sections, garbled, page_kind, pages_without_text
from tests.kg_v4_support import ASSET, ScriptedModel, read_manual


def build(tmp_path, model=None, **options):
    pdf, doc = read_manual(tmp_path, scanned=True)
    model = model or ScriptedModel()
    workdir = tmp_path / "run"
    result = asyncio.run(Builder(doc=doc, asset=ASSET, llm=model, pdf_path=pdf, workdir=workdir, **options).run())
    return result, model


def test_only_pages_without_usable_text_are_chosen(tmp_path):
    prose = "Tighten the drive belt until it deflects six millimetres at its centre. " * 3
    assert page_kind(prose, image_share=0.9, strokes=900) == "text"  # good text is never sent
    assert page_kind("VB series   48", image_share=0.7, strokes=2) == "scanned"
    assert page_kind("", image_share=0.0, strokes=900) == "scanned"  # lettering drawn as strokes
    assert page_kind("", image_share=0.0, strokes=3) == "blank"
    assert page_kind("��� �� " * 40, image_share=0.0, strokes=0) == "garbled"
    # Leader dots printed with a broken font do not make a readable page garbled.
    assert not garbled(prose + "Hex wrench " + "�" * 60 + " 1 Ea. Focus gauge " + "�" * 60 + " 1")

    pdf, doc = read_manual(tmp_path, scanned=True)
    assert pages_without_text(doc, page_layout_inventory(pdf)) == {2: "scanned"}
    typed = tmp_path / "typed"
    typed.mkdir()
    pdf, doc = read_manual(typed)
    assert pages_without_text(doc, page_layout_inventory(pdf)) == {}


def test_a_scanned_page_is_read_from_its_image_and_cited(tmp_path):
    result, model = build(tmp_path)
    document, report = result.document, result.report
    assert report["transcription"]["transcribed_pages"] == [2] and report["transcription"]["blocks"] == 7
    assert report["transcription"]["pages_without_text"] == {"scanned": 1}
    assert result.status == "approved" and report["unreadable_pages"] == []
    assert model.count("kg_v4_transcribe") == 1  # one call, for the one page without text

    label = {node["id"]: node["name"] for node in document["nodes"]}
    chain = {(edge["type"], label[edge["from"]], label[edge["to"]]): edge for edge in document["edges"]}
    assert ("RESOLVED_BY", "Worn packings", "Replace packings") in chain
    evidence = chain["MAY_INDICATE", "Pump fails to operate", "Air supply restricted"]["occurrences"][0]["evidence"][0]
    assert evidence["segment_id"] == "p2.o102" and evidence["page"] == 2 and evidence["transcribed"] is True
    assert evidence["section"] == "Troubleshooting" and "CAUSE: Air supply restricted" in evidence["text"]
    typed = next(node for node in document["nodes"] if node["name"] == "Cracked drive belt")["evidence"][0]
    assert "transcribed" not in typed  # text read from the text layer is not marked

    read = next(call for call in model.calls if call["name"] == "kg_v4_extract" and "p2.o102" in call["user"])
    assert "=== page 2 (transcribed) | section: Troubleshooting ===" in read["user"]
    assert read["images"] >= 1  # the extractor sees the page itself, not only its transcript


def test_transcripts_are_kept_and_limits_and_failures_are_reported(tmp_path):
    first = tmp_path / "first"
    first.mkdir()
    _, model = build(first)
    again, replay = build(first)  # same directory: nothing is paid twice
    assert model.count("kg_v4_transcribe") == 1 and replay.count("kg_v4_transcribe") == 0
    assert again.report["transcription"]["transcribed_pages"] == [2]

    capped = tmp_path / "capped"
    capped.mkdir()
    result, model = build(capped, config=BuildConfig(transcribe_max_pages=0))
    assert model.count("kg_v4_transcribe") == 0 and result.status == "incomplete"
    assert result.report["transcription"]["pages_over_the_limit"] == [2]
    assert "pages_over_the_transcription_limit" in result.report["incomplete_reasons"]

    off = tmp_path / "off"
    off.mkdir()
    result, model = build(off, config=BuildConfig(transcribe=False))
    assert model.count("kg_v4_transcribe") == 0 and result.report["transcription"] == {}
    assert result.report["unreadable_pages"] == [2]

    def unreachable(user, schema):
        raise RuntimeError("provider down")

    failed = tmp_path / "failed"
    failed.mkdir()
    result, _ = build(failed, model=ScriptedModel(kg_v4_transcribe=unreachable))
    assert result.report["transcription"]["failed_pages"] == [2]
    assert "failed_transcriptions" in result.report["incomplete_reasons"]
    assert not (failed / "run" / "state" / "transcript_2.json").exists()  # a failed read is read again


def test_headings_and_page_numbers_read_on_images_name_the_pages():
    sections = SectionIndex(page_count=6, by_page={page: "" for page in range(1, 7)})
    transcripts = [
        {"page": 3, "printed_page": "- 12 -", "blocks": [{"kind": "heading", "text": "4. Alarms"},
                                                         {"kind": "text", "text": "Alarm 401 means overheat."}]},
        {"page": 4, "printed_page": "13", "blocks": [{"kind": "text", "text": "Alarm 402 means low oil."}]},
        {"page": 5, "printed_page": "14", "blocks": [{"kind": "text", "text": "Before the next title."},
                                                     {"kind": "text", "text": "More of the same."},
                                                     {"kind": "heading", "text": "5. Lubrication"},
                                                     {"kind": "text", "text": "Grease every month."}]},
    ]
    add_sections(sections, transcripts)
    assert sections.by_page[3] == "4. Alarms" and sections.by_page[4] == "4. Alarms"  # a page continues
    assert sections.by_page[5] == "4. Alarms" and sections.by_segment["p5.o104"] == "5. Lubrication"
    assert sections.page_offset == -9 and sections.pdf_page(13) == 4  # "see page 13" finds PDF page 4
    assert sections.heading_pages(number="5") == [5]


def test_empty_conditions_and_causes_that_repeat_the_problem():
    assert empty_condition("if", "1") and empty_condition("order", "(2).")
    assert not empty_condition("expected", "0") and not empty_condition("if", "5 V") and not empty_condition("if", "if worn")
    assert repeats("Defective or misadjusted component",
                   "Defective or misadjusted components in the interlock, monitor and door seal")
    assert repeats("The pump leaks", "Pump leaks")
    assert not repeats("Worn seal", "Pump leaks at the seal") and not repeats("Leak", "Pump leaks at the seal")


def test_the_estimate_counts_one_call_per_page_without_text(tmp_path):
    _, doc = read_manual(tmp_path)
    plain, scanned = estimate(doc, BuildConfig()), estimate(doc, BuildConfig(), pages_to_transcribe=40)
    assert "transcribe" not in plain["high"]["roles"] and scanned["high"]["roles"]["transcribe"]["calls"] == 40
    assert scanned["estimated_cost_usd"][1] > plain["estimated_cost_usd"][1]
    assert estimate(doc, BuildConfig(transcribe_max_pages=10), pages_to_transcribe=40)["pages_to_transcribe"] == 10
    assert estimate(doc, BuildConfig(transcribe=False), pages_to_transcribe=40)["pages_to_transcribe"] == 0
