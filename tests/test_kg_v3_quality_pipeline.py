"""Offline acceptance cases T01–T30: model responses are explicit fixtures."""

from __future__ import annotations

import asyncio
import re

import fitz
import pytest
from pydantic import ValidationError

from backend.kg_v3.checker import Checker, group_candidates, same_relation
from backend.kg_v3.contracts import (
    ContextItem,
    DocumentMap,
    PageLabel,
    PageMapEntry,
    ReviewerIdentity,
    ReviewerKind,
    Segment,
    SegmentKind,
    Tier,
)
from backend.kg_v3.coverage import inventory, queue_requests, update_coverage
from backend.kg_v3.export import load_quality, write_exports
from backend.kg_v3.extractor import Endpoint, Proposal, parse_read
from backend.kg_v3.llm import UsageTotals
from backend.kg_v3.mapper import assert_atomic_ownership, build_quality_units
from backend.kg_v3.merger import MergePair, assemble, identity, judge_pairs
from backend.kg_v3.navigation import diagnostic_paths
from backend.kg_v3.omissions import apply_review_delta
from backend.kg_v3.ontology import load_ontology
from backend.kg_v3.quality_contracts import DocumentIdentity, QualityConfig
from backend.kg_v3.questions import apply_relation_answers, approval_payload, approval_question, relation_questions
from backend.kg_v3.reader import DocumentText, read_document
from backend.kg_v3.references import resolve_document_reference
from backend.kg_v3.run import Pipeline, RunConfig
from backend.kg_v3.run_state import RunState, atomic_json, digest, input_manifest, run_lock
from backend.kg_v3.source_index import bind_proposal, build_source_index
from backend.kg_v3.validation import validate_quality
from backend.kg_v3.visual_catalog import QualityImages, catalog_page_region
from scripts.kg_v3 import load_evidence
from tests.test_kg_v3_reader import ASSET, troubleshooting_pdf

SPEC = load_ontology()
PERSON = ReviewerIdentity(kind=ReviewerKind.HUMAN, name="maintenance reviewer")


def index_for(doc):
    manifest = input_manifest(doc, RunConfig(), "Pump", None, SPEC)
    identity_ = DocumentIdentity(
        document_id="doc",
        pdf_sha256=manifest["pdf_sha256"],
        asset_scope_id="pump",
        source_title="fixture",
        parser_fingerprint=manifest["parser_base_fingerprint"],
        inventory_fingerprint=manifest["document_basis_sha256"],
    )
    return build_source_index(doc, doc.page_geometry, identity_)


def table_doc(actions="1. Inspect fuse 2. Replace fuse 3. Contact service", two=False):
    from backend.kg_v3.contracts import TableCoordinates

    rows = [["PROBLEM", "CAUSE", "SOLUTION"], ["No power", "Blown fuse", actions]]
    if two:
        rows.append(["No output", "Blown fuse", "Clean contacts"])
    segments = [
        Segment(
            segment_id=f"p1.t1.r{n}",
            page=1,
            kind=SegmentKind.TABLE_ROW,
            evidence_id="synthetic table",
            text=" | ".join(row),
            table=TableCoordinates(table=1, row=n, headers=rows[0], cell_items=[[v] for v in row]),
        )
        for n, row in enumerate(rows, 1)
    ]
    return DocumentText(page_count=1, pages={1: segments})


def page_map(doc):
    return DocumentMap(entries=[PageMapEntry(page=p, label=PageLabel.DIAGNOSTIC) for p in range(1, doc.page_count + 1)])


def setup_table(actions="Replace fuse", two=False, max_chars=9000):
    doc = table_doc(actions, two)
    index = index_for(doc)
    units = build_quality_units(doc, page_map(doc), index, max_chars=max_chars)
    return doc, index, units


def proposal(doc, index, units, row=2, action=None, read="A", inferred=False, conditions=(), method="PRIMARY"):
    cells = index.atomic_refs[f"p1.t1.r{row}"]
    cause = next(r for r in cells if index.evidence[r].column == 1)
    if action is None:
        action = next(r for r in cells if index.evidence[r].column == 2)
    unit = next(u for u in units if action in u.owned_evidence_ref_ids)
    text = re.sub(r"^\s*\d+[.)]\s*", "", index.evidence[action].exact_text)
    kind = "inspection" if text.startswith("Inspect") else "escalation" if text.startswith("Contact") else "repair"
    p = Proposal(
        unit_id=unit.unit_id,
        read=read,
        relation_type="RESOLVED_BY",
        record="arbitrary model record",
        source=Endpoint(
            type="FailureMode",
            name="Incorrect voltage" if inferred else "Blown fuse",
            cites=[cause],
            stated=not inferred,
            denotation_status="INFERRED" if inferred else "STATED",
        ),
        target=Endpoint(type="CorrectiveAction", name=text, kind=kind, cites=[action], denotation_status="STATED"),
        cites=[cause, action],
        conditions=list(conditions),
        extraction_method=method,
        premise_refs=[action] if inferred else [],
    )
    return bind_proposal(index, doc, p, unit)


class Fake:
    def __init__(self, supported=True, fail_review=False):
        self.model = "gpt-6-luna"
        self.usage = UsageTotals()
        self.calls = []
        self.supported = supported
        self.fail_review = fail_review
        self.call_records = []

    async def json(self, **kw):
        self.calls.append(kw)
        name, schema = kw["name"], kw["schema"]
        if name == "kg_v3_verify":
            prop = schema["properties"]["verdicts"]["items"]["properties"]
            refs = prop.get("cited_evidence_ids", {}).get("items", {}).get("enum", [])
            return {
                "verdicts": [
                    {
                        "id": id_,
                        "verdict": "supported" if self.supported else "not_supported",
                        "scope_verdict": "supported",
                        "cited_evidence_ids": refs,
                        "issues": [],
                    }
                    for id_ in prop["id"]["enum"]
                ]
            }
        if name == "kg_quality_review":
            if self.fail_review:
                raise RuntimeError("budget exhausted")
            return {
                "additions": [],
                "replacements": [],
                "conflicts": [],
                "resolved_item_bindings": [],
                "unresolved_items": [],
            }
        if name == "kg_v3_merge":
            ids = schema["properties"]["answers"]["items"]["properties"]["id"]["enum"]
            refs = sorted(set(re.findall(r"\[(p\d+\.[a-z0-9.]+)\]", kw["user"])))
            return {
                "answers": [
                    {"id": id_, "answer": "same", "rationale": "same source identifier", "cited_segments": refs}
                    for id_ in ids
                ]
            }
        if name == "kg_quality_visual_route":
            ref = schema["properties"]["evidence_ref_ids"]["items"]["enum"][0]
            assert kw["images"]
            return {"relevance": "DIAGNOSTIC", "reason": "printed troubleshooting diagram", "evidence_ref_ids": [ref]}
        if name == "kg_quality_visual_layout":
            return {
                "regions": [
                    {"key": key, "bbox": box, "role": role, "transcription": text}
                    for key, box, role, text in [
                        ("q", [20, 20, 140, 60], "question", "No power"),
                        ("o", [20, 65, 65, 90], "outcome", "Yes"),
                        ("t", [65, 90, 100, 140], "transition", ""),
                        ("d", [20, 145, 160, 180], "destination", "Replace fuse"),
                    ]
                ],
                "paths": [
                    {"question": "q", "outcome": "o", "outcome_value": "Yes", "transition": "t", "destination": "d"}
                ],
                "conflicts": [],
            }
        if name == "kg_v3_extract":
            props = schema["properties"]
            refs = props["entities"]["items"]["properties"]["cite"]["items"]["enum"]
            branch = next(
                (b for b in props["relations"]["items"]["properties"].get("branch_id", {}).get("enum", []) if b), ""
            )
            # Visual fixture deliberately has no invented textual segment.
            if "no machine-readable text" in kw["user"]:
                endpoints = [
                    ("s", "Symptom", "No power", ""),
                    ("f", "FailureMode", "Blown fuse", ""),
                    ("a", "CorrectiveAction", "Replace fuse", "repair"),
                ]
                entities = [
                    {
                        "key": key,
                        "type": type_,
                        "name": text,
                        "code": "",
                        "kind": kind,
                        "stated": True,
                        "cite": refs,
                        "denotation_status": "STATED",
                    }
                    for key, type_, text, kind in endpoints
                ]
                relations = [
                    {
                        "type": type_,
                        "source": s,
                        "target": t,
                        "record": "R1",
                        "conditions": [],
                        "cite": refs,
                        "branch_id": branch,
                        "premise_refs": [],
                        "branch_path_refs": refs,
                        "support_rationale": "",
                    }
                    for type_, s, t in [("MAY_INDICATE", "s", "f"), ("RESOLVED_BY", "f", "a")]
                ]
                return {"entities": entities, "relations": relations, "unclear": [], "section_context": []}
            return {"entities": [], "relations": [], "unclear": [], "section_context": []}
        if name == "kg_v3_map":
            return {
                "pages": [
                    {"page": p, "label": "other", "section": "", "unsure": False}
                    for p in schema["properties"]["pages"]["items"]["properties"]["page"]["enum"]
                ]
            }
        if name == "kg_v3_scan":
            return {"diagnostic_pages": []}
        raise AssertionError(name)


def check(doc, index, units, ps, llm=None):
    return asyncio.run(
        Checker(llm or Fake(), SPEC, extractor_id="fixture", units=units, source_index=index).check(doc, ps)
    )


@pytest.mark.parametrize("reads", [1, 2])
def test_t01_empty_citations_never_gain_proof(reads):
    doc = DocumentText(
        page_count=1,
        pages={
            1: [
                Segment(
                    segment_id="p1.b1",
                    page=1,
                    kind=SegmentKind.TEXT,
                    evidence_id="synthetic packaging",
                    text="Packaging only",
                )
            ]
        },
    )
    index = index_for(doc)
    unit = build_quality_units(doc, page_map(doc), index)[0]
    data = {
        "entities": [
            {"key": "s", "type": "Symptom", "name": "Pump hot", "cite": []},
            {"key": "f", "type": "FailureMode", "name": "Invented cause", "cite": []},
        ],
        "relations": [
            {"type": "MAY_INDICATE", "source": "s", "target": "f", "record": "R1", "conditions": [], "cite": []}
        ],
    }
    ps = [
        p
        for r in "AB"[:reads]
        for p in parse_read(data, unit=unit, read=r, spec=SPEC, allowed=set(unit.owned_evidence_ref_ids))[0]
    ]
    assert ps and all("MISSING_EVIDENCE" in p.validation_issues for p in ps)
    assert check(doc, index, [unit], ps) == []
    assert all(d["reason"] == "MISSING_EVIDENCE" for d in index.dispositions)


def test_t02_real_adapter_geometry_reaches_crop(tmp_path):
    pdf = tmp_path / "manual.pdf"
    troubleshooting_pdf(pdf)
    evidence, count, _ = load_evidence(pdf, ASSET)
    doc = read_document(list(evidence), page_count=count)
    row = doc.segment("p1.t1.r2")
    assert row.bbox and row.table.cell_bboxes
    index = index_for(doc)
    ref, url = catalog_page_region(pdf, doc, index, 1, bbox=row.bbox)
    assert index.evidence[ref].bbox == row.bbox and url.startswith("data:image/png;")
    assert index.regions[index.evidence[ref].region_id].segment_ids
    with pytest.raises(ValueError):
        catalog_page_region(pdf, doc, index, 1, bbox=(-1, 0, 10, 10))


def test_t03_t08_conditions_and_action_kinds_are_distinct():
    doc, index, units = setup_table(
        "1. Inspect fuse 2. Replace fuse if at fault 3. Contact service if problem persists"
    )
    actions = [r for r in index.atomic_refs["p1.t1.r2"] if index.evidence[r].column == 2]
    first = proposal(doc, index, units, action=actions[0])
    repair = proposal(
        doc, index, units, action=actions[1], conditions=[ContextItem(kind="if", text="at fault", cite=(actions[1],))]
    )
    escalation = proposal(
        doc,
        index,
        units,
        action=actions[2],
        conditions=[ContextItem(kind="if", text="problem persists", cite=(actions[2],))],
    )
    relations = check(
        doc,
        index,
        units,
        [
            first,
            first.model_copy(update={"read": "B"}),
            repair,
            repair.model_copy(update={"read": "B"}),
            escalation,
            escalation.model_copy(update={"read": "B"}),
        ],
    )
    assert len(relations) == 3 and all(r.assertion.tier is Tier.GREEN for r in relations)
    bykind = {r.proposals[0].target.kind: r.assertion.conditions for r in relations}
    assert bykind["inspection"] == []
    assert bykind["repair"][0].text == "at fault"
    assert bykind["escalation"][0].text == "problem persists"


def read_delta(ps):
    entities, relations = [], []
    for n, p in enumerate(ps):
        for key, end in [(f"s{n}", p.source), (f"t{n}", p.target)]:
            entities.append(
                {
                    "key": key,
                    "type": end.type,
                    "name": end.name,
                    "kind": end.kind,
                    "code": end.code,
                    "stated": end.stated,
                    "cite": end.cites,
                    "denotation_status": end.denotation_status,
                }
            )
        relations.append(
            {
                "type": p.relation_type,
                "source": f"s{n}",
                "target": f"t{n}",
                "record": f"R{n}",
                "conditions": [c.model_dump(mode="json") for c in p.conditions],
                "cite": p.cites,
                "branch_id": p.branch_id,
            }
        )
    return {"additions": [{"entities": entities, "relations": relations}], "replacements": [], "conflicts": []}


def test_t04_row_cite_is_not_three_actions_and_delta_is_idempotent():
    doc, index, units = setup_table("1. Inspect fuse 2. Replace fuse 3. Contact service")
    actions = [r for r in index.atomic_refs["p1.t1.r2"] if index.evidence[r].column == 2]
    ps = [proposal(doc, index, units, action=r) for r in actions]
    original = check(doc, index, units, [ps[0], ps[0].model_copy(update={"read": "B"})])
    ledger = update_coverage(inventory(index, doc, page_map(doc), units), index, original)
    assert sum(i.status == "REPRESENTED" for i in ledger.items if i.kind in {"REPAIR", "INSPECTION", "ESCALATION"}) == 1
    checker = Checker(Fake(), SPEC, extractor_id="fixture", units=units, source_index=index)

    async def run():
        out, delta = await apply_review_delta(
            read_delta(ps), doc=doc, index=index, unit=units[0], checker=checker, relations=original, spec=SPEC
        )
        again, _ = await apply_review_delta(
            read_delta(ps), doc=doc, index=index, unit=units[0], checker=checker, relations=out, spec=SPEC
        )
        return out, again, delta

    out, again, delta = asyncio.run(run())
    assert len(out) == len(again) == 3 and len(delta["accepted"]) == 2
    ledger = update_coverage(ledger, index, again)
    assert all(i.status == "REPRESENTED" for i in ledger.items if i.kind in {"REPAIR", "INSPECTION", "ESCALATION"})


def test_t05_branch_local_failures_and_no_cross_branch_paths():
    doc, index, units = setup_table(two=True)
    ps = [proposal(doc, index, units, row=n, read=r) for n in [2, 3] for r in "AB"]
    rs = check(doc, index, units, ps)
    graph = assemble(rs, [])
    causes = [n for n in graph.nodes.values() if n.type == "FailureMode"]
    assert len(causes) == 2 and len({n.node_id for n in causes}) == 2
    p = ps[0].model_copy(update={"target": ps[-1].target, "cites": ps[0].source.cites + ps[-1].target.cites})
    contaminated = check(doc, index, units, [p])[0]
    assert contaminated.assertion.tier is Tier.RED
    assert "CROSS_BRANCH_CONTAMINATION" in contaminated.assertion.certificate.validation_issues


def test_t06_cross_page_context_requires_path():
    doc, index, units = setup_table(two=True)
    a, b = [proposal(doc, index, units, row=n) for n in [2, 3]]
    mixed = a.model_copy(update={"target": b.target, "cites": a.source.cites + b.target.cites})
    bound = bind_proposal(index, doc, mixed, units[0])
    assert "CROSS_BRANCH_CONTAMINATION" in bound.validation_issues
    assert check(doc, index, units, [bound])[0].assertion.tier is not Tier.GREEN


def test_t07_expected_values_do_not_validate_an_invented_failure():
    doc, index, units = setup_table("Check input voltage; expected 230 V")
    p = proposal(doc, index, units, inferred=True)
    bad = check(doc, index, units, [p, p.model_copy(update={"read": "B"})], Fake(supported=False))
    assert all(r.assertion.tier is Tier.RED for r in bad)
    assert bad[0].assertion.certificate.epistemic_status == "INFERRED_FROM_TEXT"


def test_t09_literal_conflict_quarantines_statement():
    doc, index, units = setup_table()
    p = proposal(doc, index, units)
    action = p.target.cites[0]
    index.dispositions.append({"reason": "SOURCE_CONFLICT", "page": 1, "evidence_ref_ids": [action],
                               "description": "printed Yes arrow contradicts printed destination"})
    p = bind_proposal(index, doc, p, units[0])
    rs = check(doc, index, units, [p, p.model_copy(update={"read": "B"})])
    assert rs[0].assertion.tier is not Tier.GREEN
    assert "SOURCE_CONFLICT" in rs[0].assertion.certificate.validation_issues


def test_t09_ambiguity_or_page_note_does_not_quarantine_the_page():
    doc, index, units = setup_table()
    index.dispositions.append({"reason": "VISUAL_AMBIGUITY", "page": 1, "evidence_ref_ids": [],
                               "description": "the No arrow continues on the next page"})
    index.dispositions.append({"reason": "SOURCE_CONFLICT", "page": 1, "evidence_ref_ids": [],
                               "description": "unlocated contradiction"})
    p = proposal(doc, index, units)
    assert "SOURCE_CONFLICT" not in p.validation_issues
    rs = check(doc, index, units, [p, p.model_copy(update={"read": "B"})])
    assert rs[0].assertion.tier is Tier.GREEN


@pytest.mark.parametrize("a,b", [("A7AB", "7A7B"), ("003", "010"), ("010", "013")])
def test_t10_codes_remain_distinct(a, b):
    doc, index, units = setup_table()
    p = proposal(doc, index, units)
    ends = [p.source.model_copy(update={"type": "ErrorCode", "name": "Alarm", "code": code}) for code in [a, b]]
    assert identity(ends[0]) != identity(ends[1])
    assert not same_relation(p.model_copy(update={"source": ends[0]}), p.model_copy(update={"source": ends[1]}))


def test_t11_merge_needs_sources_from_both_sides():
    doc, index, units = setup_table(two=True)
    refs = index.atomic_refs["p1.t1.r2"][:1] + index.atomic_refs["p1.t1.r3"][:1]
    pair = MergePair(
        left="a",
        right="b",
        left_name="Connector 123",
        right_name="Plug 123",
        type="Component",
        left_cites=[refs[0]],
        right_cites=[refs[1]],
    )
    plan = asyncio.run(judge_pairs(Fake(), [pair], doc))
    assert plan.same and set(plan.same[0].cited_segments) >= {"p1.t1.r2", "p1.t1.r3"}
    blind = MergePair(**{**pair.model_dump(), "right_cites": []})
    assert not asyncio.run(judge_pairs(Fake(), [blind], doc)).same


def test_t12_inherited_cells_have_origin(tmp_path):
    pdf = tmp_path / "manual.pdf"
    troubleshooting_pdf(pdf)
    evidence, count, _ = load_evidence(pdf, ASSET)
    doc = read_document(list(evidence), page_count=count)
    index = index_for(doc)
    merged = [index.evidence[r] for r in index.atomic_refs["p1.t1.r3"] if index.evidence[r].column == 0]
    assert all(r.inherited_from for r in merged)
    units = build_quality_units(doc, page_map(doc), index, max_chars=200)
    assert any(
        set(r.inherited_from) & set(u.context_evidence_ref_ids)
        for r in merged
        for u in units
        if r.evidence_ref_id in u.owned_evidence_ref_ids
    )


def image_pdf(path, pages=1):
    document = fitz.open()
    # Rasterized printed diagram, with zero native text in the target PDF.
    drawing = fitz.open()
    p = drawing.new_page(width=200, height=200)
    p.insert_text((22, 40), "No power")
    p.insert_text((22, 80), "Yes")
    p.draw_line((80, 90), (80, 140))
    p.insert_text((22, 165), "Replace fuse")
    png = p.get_pixmap().tobytes("png")
    for _ in range(pages):
        page = document.new_page(width=200, height=200)
        page.insert_image(page.rect, stream=png)
    document.save(path)
    document.close()
    drawing.close()


@pytest.mark.parametrize("supported", [True, False])
def test_t13_t15_t26_visual_only_pipeline_and_projection(tmp_path, supported):
    pdf = tmp_path / "image.pdf"
    image_pdf(pdf)
    doc = DocumentText(page_count=1)
    llm = Fake(supported=supported)
    cfg = RunConfig(
        quality=QualityConfig.quality_v1(completeness_review=False, reference_retrieval=False, graph_review=False),
        gates={"map": ["auto"], "doubts": [], "approval": ["auto"]},
    )
    pipeline = Pipeline(doc=doc, asset_name="Pump", pdf_path=pdf, llm=llm, workdir=tmp_path / "run", config=cfg)
    result = asyncio.run(pipeline.run())
    assert doc.segments() == [] and result.units and all(not u.segment_ids for u in result.units)
    assert all(c["images"] for c in llm.calls if c["name"] in {"kg_v3_extract", "kg_v3_verify"})
    public = result.quality_bundle["validation"]["public_assertion_ids"]
    assert bool(public) == supported
    projected = write_exports(tmp_path / "run", result, doc, asset=ASSET, source_title="image.pdf")
    loaded = load_quality(tmp_path / "run")
    assert loaded["binding_status"] == "VERIFIED"
    assert projected["projection_status"] == "EMPTY" and projected["status"] != "approved"
    assert len(loaded["quality"]["public_assertion_ids"]) == (2 if supported else 0)
    assert not projected["edges"]

    class NoCalls(Fake):
        async def json(self, **kw):
            raise AssertionError("resume called provider")

    resumed = Pipeline(
        doc=DocumentText(page_count=1),
        asset_name="Pump",
        pdf_path=pdf,
        llm=NoCalls(),
        workdir=tmp_path / "run",
        config=cfg,
    )
    again = asyncio.run(resumed.run())
    assert again.quality_bundle["validation"]["public_assertion_ids"] == public


def test_t14_regions_over_the_cap_are_sent_as_whole_pages_or_refused(tmp_path):
    pdf = tmp_path / "seven.pdf"
    image_pdf(pdf, 7)
    doc = DocumentText(page_count=7)
    index = index_for(doc)
    pages = [index.evidence[catalog_page_region(pdf, doc, index, p)[0]].region_id for p in range(1, 8)]
    images = QualityImages(pdf, doc, index, max_images=2)
    with pytest.raises(ValueError, match="IMAGE_PACKET_LIMIT"):
        images.crops(pages)
    one_page = [index.evidence[catalog_page_region(pdf, doc, index, 1, bbox=(0, 0, 50 + 10 * n, 50 + 10 * n))[0]].region_id
                for n in range(5)]
    assert len(images.crops(one_page)) == 1  # the whole page carries every region of it
    assert len(images.crops(one_page[:2])) == 2


def test_t16_answers_are_bound_to_one_branch():
    from backend.kg_v3.contracts import Answer

    doc, index, units = setup_table(two=True)
    ps = [proposal(doc, index, units, row=n) for n in [2, 3]]
    rs = check(doc, index, units, ps, Fake(supported=False))
    # An unclear verifier permits an exact human decision; the other branch stays yellow.
    rs = [
        r.model_copy(
            update={
                "assertion": r.assertion.model_copy(
                    update={
                        "certificate": r.assertion.certificate.model_copy(
                            update={"verifier_verdict": None, "validation_issues": []}
                        )
                    }
                )
            }
        )
        for r in rs
    ]
    qs = relation_questions(doc, SPEC, rs)
    assert len(qs) == 2
    answer = Answer(question_id=qs[0].question_id, option_id="accept", answered_by=PERSON)
    out = apply_relation_answers(rs, qs, [answer])
    assert sum(r.assertion.tier is Tier.GREEN for r in out) == 1


def test_t17_t27_t30_approval_is_content_bound():
    doc, index, units = setup_table()
    p = proposal(doc, index, units)
    rs = check(doc, index, units, [p, p.model_copy(update={"read": "B"})])
    g = assemble(rs, [])
    before = approval_question(["counts"], approval_payload(g))
    # A workflow summary change leaves approval content unchanged.
    assert approval_question(["new workflow summary"], approval_payload(g)).question_id == before.question_id
    changed = g.model_copy(deep=True)
    next(iter(changed.nodes.values())).name = "Semantically different"
    assert approval_question(["counts"], approval_payload(changed)).question_id != before.question_id
    renamed = g.model_copy(deep=True)
    next(iter(renamed.nodes.values())).concept_id = "new-concept"
    assert rs[0].assertion.assertion_id == renamed.edges[0].assertions[0].assertion_id
    assert rs[0].assertion.original_fact == renamed.edges[0].assertions[0].original_fact


@pytest.mark.parametrize("change", ["pdf", "model", "context", "prompt", "ocr"])
def test_t18_resume_rejects_semantic_dependencies(tmp_path, change, monkeypatch):
    doc, index, units = setup_table()
    cfg = RunConfig()
    manifest = input_manifest(doc, cfg, "Pump", None, SPEC)
    state = RunState(tmp_path / "run", manifest)
    state.save("extract", {"response": "frozen"})
    if change == "model":
        cfg = cfg.model_copy(update={"model": "gpt-6-sol"})
    elif change in {"pdf", "context", "ocr"}:
        segments = doc.pages[1][:]
        target = segments[1]
        segments[1] = target.model_copy(
            update={
                "text": target.text + (" changed PDF" if change == "pdf" else " new context"),
                "low_quality": change == "ocr",
            }
        )
        doc = DocumentText(page_count=1, pages={1: segments})
    else:
        import backend.kg_v3.run_state as run_state

        real = run_state.source_fingerprints()
        monkeypatch.setattr(
            run_state, "source_fingerprints", lambda: {**real, "backend/kg_v3/prompts.py": "changed prompt"}
        )
    changed = input_manifest(doc, cfg, "Pump", None, SPEC)
    with pytest.raises(ValueError, match="incompatible"):
        RunState(tmp_path / "run", changed)
    assert RunState(tmp_path / "run", manifest).load("extract") == {"response": "frozen"}
    atomic_json(tmp_path / "run" / "state" / "extract.json", {"response": "edited"})
    with pytest.raises(ValueError, match="checksum"):
        state.load("extract")


def test_t19_single_writer_and_reserved_audit_cap(tmp_path):
    from backend.kg_v3.omissions import choose_units

    with run_lock(tmp_path):
        with pytest.raises(ValueError, match="another writer"):
            with run_lock(tmp_path):
                pass
    doc, index, units = setup_table()
    ledger = queue_requests(inventory(index, doc, page_map(doc), units), index, [], audit_count=2)
    work = [r for r in ledger.requests if not r.audit]
    audit = [r for r in ledger.requests if r.audit]
    assert work and audit
    groups = {"u_work_a": work, "u_work_b": work, "u_audit": audit}
    chosen = choose_units(groups, room=2, audit_slots=1)
    assert len(chosen) == 2 and "u_audit" in chosen


def test_t20_repair_cannot_override_human_reject():
    doc, index, units = setup_table()
    p = proposal(doc, index, units)
    rs = check(doc, index, units, [p, p.model_copy(update={"read": "B"})])
    cert = rs[0].assertion.certificate.model_copy(update={"rejected_by": PERSON})
    original = [rs[0].model_copy(update={"assertion": rs[0].assertion.model_copy(update={"certificate": cert})})]
    checker = Checker(Fake(), SPEC, extractor_id="fixture", source_index=index, units=units)
    out, delta = asyncio.run(
        apply_review_delta(
            read_delta([p]), doc=doc, index=index, unit=units[0], checker=checker, relations=original, spec=SPEC
        )
    )
    assert len(out) == 1 and out[0].assertion.tier is Tier.RED and delta["accepted"] == []
    assert any(d["reason"] == "HUMAN_REJECT_STANDS" for d in index.dispositions)


def test_t20_changed_proof_needs_a_new_exact_human_decision():
    from backend.kg_v3.contracts import Answer

    doc, index, units = setup_table()
    p = proposal(doc, index, units)
    checked = check(doc, index, units, [p, p.model_copy(update={"read": "B"})])
    rejected = checked[0].model_copy(update={"assertion": checked[0].assertion.model_copy(update={
        "certificate": checked[0].assertion.certificate.model_copy(update={"rejected_by": PERSON})
    })})
    indicator = next(r for r in index.atomic_refs["p1.t1.r2"] if index.evidence[r].column == 0)
    changed = p.model_copy(update={"cites": [*p.cites, indicator]})
    out, delta = asyncio.run(apply_review_delta(
        read_delta([changed]), doc=doc, index=index, unit=units[0],
        checker=Checker(Fake(), SPEC, extractor_id="fixture", source_index=index, units=units),
        relations=[rejected], spec=SPEC,
    ))
    assert len(out) == 2 and delta["accepted"] == []
    assert out[0].assertion.tier is Tier.RED and out[1].assertion.tier is Tier.YELLOW
    assert "HUMAN_REVIEW_REQUIRED" in out[1].assertion.certificate.validation_issues
    question = relation_questions(doc, SPEC, out)[0]
    agent = ReviewerIdentity(kind=ReviewerKind.AGENT, name="fixture agent", prompt_hash=digest("fixture brief"))
    by_agent = apply_relation_answers(out, [question], [
        Answer(question_id=question.question_id, option_id="accept", answered_by=agent,
               rationale="The simulated independent verifier supported the changed evidence.")
    ])
    assert by_agent[1].assertion.tier is Tier.YELLOW
    by_human = apply_relation_answers(out, [question], [
        Answer(question_id=question.question_id, option_id="accept", answered_by=PERSON,
               content_fingerprint=question.content_fingerprint)
    ])
    assert by_human[0].assertion.tier is Tier.RED and by_human[1].assertion.tier is Tier.GREEN


def test_t21_legacy_is_read_only_and_stale_projection_is_unverified(tmp_path):
    atomic_json(tmp_path / "graph.json", {"version": "kg-v3-graph-2", "nodes": [], "edges": []})
    raw = (tmp_path / "graph.json").read_bytes()
    loaded = load_quality(tmp_path)
    assert loaded["scope_status"] == "LEGACY_UNKNOWN" and (tmp_path / "graph.json").read_bytes() == raw


def test_t23_path_uses_occurrence_not_aggregate_tier():
    doc, index, units = setup_table()
    p = proposal(doc, index, units)
    sym = index.atomic_refs["p1.t1.r2"][0]
    indicator = p.model_copy(
        update={
            "relation_type": "MAY_INDICATE",
            "source": Endpoint(type="Symptom", name="No power", cites=[sym], denotation_status="STATED"),
            "target": p.source,
            "cites": [sym, *p.source.cites],
        }
    )
    rs = check(
        doc,
        index,
        units,
        [p, p.model_copy(update={"read": "B"}), indicator, indicator.model_copy(update={"read": "B"})],
    )
    g = assemble(rs, [])
    start = next(n.node_id for n in g.nodes.values() if n.type == "Symptom")
    assert len(diagnostic_paths(g, index, start)["paths"]) == 1
    actionedge = next(e for e in g.edges if e.relation_type == "RESOLVED_BY")
    a = actionedge.assertions[0]
    actionedge.assertions = [a.model_copy(update={"certificate": a.certificate.model_copy(update={"witnesses": []})})]
    assert not diagnostic_paths(g, index, start)["paths"]


def test_t24_stable_ids_when_reads_reversed_or_labels_change():
    doc, index, units = setup_table()
    a = proposal(doc, index, units, read="A")
    b = proposal(doc, index, units, read="B")
    assert a.proposal_id == b.proposal_id
    candidates = group_candidates([a, b])
    reversed_ = group_candidates([b.model_copy(update={"record": "R999"}), a])
    assert candidates[0].candidate_id == reversed_[0].candidate_id
    g1 = assemble(check(doc, index, units, [a, b]), [])
    g2 = assemble(check(doc, index, units, [b, a]), [])
    assert digest(approval_payload(g1)) == digest(approval_payload(g2))


def test_t25_no_delta_does_not_mean_complete():
    doc, index, units = setup_table()
    ledger = update_coverage(inventory(index, doc, page_map(doc), units), index, [])
    assert all(i.status != "REPRESENTED" for i in ledger.items)
    assert ledger.counts()["inventory_exhaustiveness"] == "PARTIAL"


def test_t28_atomic_splits_keep_parent_only_as_context():
    doc, index, units = setup_table(max_chars=120)
    assert_atomic_ownership(units, index)
    refs = [r for u in units for r in u.owned_evidence_ref_ids]
    assert len(refs) == len(set(refs))
    assert all(set(u.owned_evidence_ref_ids).isdisjoint(u.context_evidence_ref_ids) for u in units)
    assert all(index.evidence[r].kind != "TEXT_SPAN" for r in refs)


def test_quality_packing_bounds_paragraph_units_without_widening_scope():
    paragraphs = [Segment(segment_id=f"p1.b{n}", page=1, kind=SegmentKind.TEXT,
                          text=f"Problem {n}. Inspect component {n}.", evidence_id=f"paragraph {n}")
                  for n in range(1, 251)]
    ignored = Segment(segment_id="p2.b1", page=2, kind=SegmentKind.TEXT,
                      text="Packaging only.", evidence_id="unselected page")
    doc = DocumentText(page_count=2, pages={1: paragraphs, 2: [ignored]})
    index = index_for(doc)
    mapping = DocumentMap(entries=[PageMapEntry(page=1, label=PageLabel.DIAGNOSTIC),
                                  PageMapEntry(page=2, label=PageLabel.OTHER)])
    units = build_quality_units(doc, mapping, index)
    assert len(units) < 10
    assert sum(len(u.entry_ids) for u in units) == 250
    assert sum(len(u.branch_ids) for u in units) == 250
    assert all(u.pages == [1] for u in units)
    assert all(b.scope_status == "PROVISIONAL" for b in index.branches.values())
    assert_atomic_ownership(units, index)
    original = [u.model_dump(mode="json") for u in units]
    index = index.model_copy(update={"entries": dict(reversed(list(index.entries.items())))})
    assert [u.model_dump(mode="json") for u in build_quality_units(doc, mapping, index)] == original


def test_quality_units_read_like_the_base_profile():
    """The title above a table stays readable with it: quality units are the base units."""
    from backend.kg_v3.mapper import build_units

    base = table_doc()
    prose = Segment(segment_id="p1.b1", page=1, kind=SegmentKind.TEXT,
                    text="Troubleshooting: pump", evidence_id="same page title")
    doc = DocumentText(page_count=1, pages={1: [prose, *base.pages[1]]})
    index = index_for(doc)
    units = build_quality_units(doc, page_map(doc), index)
    legacy = build_units(doc, page_map(doc))
    assert [(u.unit_id, u.segment_ids, u.context_segment_ids) for u in units] == [
        (u.unit_id, u.segment_ids, u.context_segment_ids) for u in legacy]
    assert_atomic_ownership(units, index)
    owned = [r for u in units for r in u.owned_evidence_ref_ids]
    assert set(owned) == {r for seg in ["p1.b1", "p1.t1.r1", "p1.t1.r2"] for r in index.atomic_refs[seg]}


def test_packed_paragraphs_do_not_authorize_cross_branch_remedies():
    doc = DocumentText(page_count=1, pages={1: [
        Segment(segment_id="p1.b1", page=1, kind=SegmentKind.TEXT,
                text="No power: blown fuse. Replace fuse.", evidence_id="problem A"),
        Segment(segment_id="p1.b2", page=1, kind=SegmentKind.TEXT,
                text="No output: corroded contacts. Clean contacts.", evidence_id="problem B"),
    ]})
    index = index_for(doc)
    units = build_quality_units(doc, page_map(doc), index)
    assert len(units) == 1 and len(units[0].entry_ids) == 2
    a, b = (index.atomic_refs[f"p1.b{n}"][0] for n in [1, 2])
    borrowed = Proposal(unit_id=units[0].unit_id, read="A", record="same packed unit",
        relation_type="RESOLVED_BY", source=Endpoint(type="FailureMode", name="blown fuse", cites=[a]),
        target=Endpoint(type="CorrectiveAction", name="Clean contacts", kind="repair", cites=[b]), cites=[a, b])
    bound = bind_proposal(index, doc, borrowed, units[0])
    # Prose joins blocks legitimately; the verifier, reading the passage, decides.
    rejected = check(doc, index, units, [bound, bound.model_copy(update={"read": "B"})], Fake(supported=False))
    assert all(r.assertion.tier is Tier.RED for r in rejected)
    assert rejected[0].assertion.certificate.semantic_verification_required


def test_t29_index_revisions_resume_and_detect_tampering(tmp_path):
    doc, index, units = setup_table()
    manifest = input_manifest(doc, RunConfig(), "Pump", None, SPEC)
    state = RunState(tmp_path, manifest)
    state.revise_index(index, {"stage": "parser"})
    index.applied_delta_ids.append("attempt-fixed")
    state.revise_index(index, {"attempt_id": "attempt-fixed"})
    assert state.load_index()["applied_delta_ids"] == ["attempt-fixed"]
    assert len(list((tmp_path / "source_index_revisions").glob("*.json"))) == 2
    changed = index.model_dump(mode="json")
    changed["applied_delta_ids"].append("invented")
    atomic_json(tmp_path / "source_index.json", changed)
    with pytest.raises(ValueError, match="immutable revision"):
        state.load_index()


@pytest.mark.parametrize("ocr", [False, True])
@pytest.mark.parametrize("supported", [False, True])
def test_prose_and_uncertain_ocr_pipeline_require_verification_and_resume(tmp_path, ocr, supported):
    class TextFake(Fake):
        async def json(self, **kw):
            if kw["name"] == "kg_v3_map":
                self.calls.append(kw)
                return {"pages": [{"page": 1, "label": "diagnostic", "section": "Troubleshooting", "unsure": False}]}
            if kw["name"] == "kg_v3_extract":
                self.calls.append(kw)
                props = kw["schema"]["properties"]
                refs = props["entities"]["items"]["properties"]["cite"]["items"]["enum"]
                assert "branch_id" not in props["relations"]["items"]["properties"]
                return {"entities": [
                    {"key": "cause", "type": "FailureMode", "name": "Blown fuse", "kind": "", "code": "",
                     "stated": True, "cite": refs, "denotation_status": "STATED"},
                    {"key": "action", "type": "CorrectiveAction", "name": "Replace fuse", "kind": "repair", "code": "",
                     "stated": True, "cite": refs, "denotation_status": "STATED"},
                ], "relations": [
                    {"type": "RESOLVED_BY", "source": "cause", "target": "action", "record": "arbitrary",
                     "conditions": [], "cite": refs, "premise_refs": []},
                ], "unclear": [], "section_context": []}
            return await super().json(**kw)

    doc = DocumentText(page_count=1, pages={1: [Segment(
        segment_id="p1.o1" if ocr else "p1.b1", page=1,
        kind=SegmentKind.OCR_TEXT if ocr else SegmentKind.TEXT,
        evidence_id="synthetic OCR" if ocr else "synthetic prose",
        text="Blown fuse. Replace fuse.", low_quality=ocr,
    )]})
    cfg = RunConfig(quality=QualityConfig.quality_v1(
        completeness_review=False, reference_retrieval=False, graph_review=False, visual_routing=False),
        gates={"map": ["auto"], "doubts": [], "approval": ["auto"]})
    client = TextFake(supported=supported)
    pipeline = Pipeline(doc=doc, asset_name="Pump", llm=client, config=cfg, workdir=tmp_path / "run")
    result = asyncio.run(pipeline.run())
    assert any(c["name"] == "kg_v3_verify" for c in client.calls)
    assert len(result.quality_bundle["validation"]["public_assertion_ids"]) == (1 if supported else 0)
    assert all(r.assertion.certificate.semantic_verification_required for r in result.relations)
    if ocr:
        assert all(r.transcription_status == "UNCERTAIN" for r in pipeline.source_index.evidence.values())
    write_exports(pipeline.workdir, result, doc, asset=ASSET, source_title="synthetic OCR/prose")
    assert load_quality(pipeline.workdir)["binding_status"] == "VERIFIED"

    class NoCalls(TextFake):
        async def json(self, **kw):
            raise AssertionError("identical prose/OCR resume called provider")

    resumed = Pipeline(doc=doc, asset_name="Pump", llm=NoCalls(supported=supported), config=cfg, workdir=pipeline.workdir)
    again = asyncio.run(resumed.run())
    assert again.quality_bundle["validation"]["public_assertion_ids"] == result.quality_bundle["validation"]["public_assertion_ids"]


def test_config_prerequisites_and_strict_contracts():
    assert not QualityConfig().branch_identity
    with pytest.raises(ValidationError):
        QualityConfig(completeness_review=True)
    with pytest.raises(ValidationError):
        QualityConfig.quality_v1(max_review_rounds=3)
    with pytest.raises(ValidationError):
        QualityConfig.quality_v1(unrequested_p2=True)


def test_ambiguous_printed_page_never_chooses_arbitrarily():
    doc, index, units = setup_table()
    index.printed_pages["18"] = [1, 2]
    assert resolve_document_reference("see page 18", index)["status"] == "Ambiguous"
    assert resolve_document_reference("physical page 1", index)["status"] == "Resolved"


class RecoveringFake(Fake):
    """Primary omits actions; reviewer returns independently checked deltas."""

    pipeline = None

    async def json(self, **kw):
        if kw["name"] == "kg_v3_map":
            self.calls.append(kw)
            return {
                "pages": [
                    {"page": p, "label": "diagnostic", "section": "Troubleshooting", "unsure": False}
                    for p in kw["schema"]["properties"]["pages"]["items"]["properties"]["page"]["enum"]
                ]
            }
        if kw["name"] in {"kg_v3_extract", "kg_quality_review"}:
            self.calls.append(kw)
            if kw["name"] == "kg_quality_review" and self.fail_review:
                raise RuntimeError("budget exhausted")
            schema = kw["schema"]
            allowed = set(schema["properties"]["entities"]["items"]["properties"]["cite"]["items"]["enum"])
            # The reader shows numbered remedy items as "[p1.t1.r2/3.1] 1. Inspect fuse".
            items = dict(re.findall(r"^\[(p1\.t1\.r2/3\.\d+)\] (.+)$", kw["user"], re.M))
            actions = sorted(a for a in items if a in allowed)
            if kw["name"] == "kg_v3_extract":
                actions = actions[:1]
            cause = "p1.t1.r2" if "p1.t1.r2" in allowed else ""
            entities, relations = [], []
            if cause:
                entities.append({"key": "cause", "type": "FailureMode", "name": "Blown fuse", "kind": "", "code": "",
                                 "stated": True, "cite": [cause], "denotation_status": "STATED"})
            for n, alias in enumerate(actions):
                text = re.sub(r"^\s*\d+[.)]\s*", "", items[alias])
                kind = ("inspection" if text.startswith("Inspect") else
                        "escalation" if text.startswith("Contact") else "repair")
                entities.append({"key": f"a{n}", "type": "CorrectiveAction", "name": text, "kind": kind, "code": "",
                                 "stated": True, "cite": [alias], "denotation_status": "STATED"})
                if cause:
                    relations.append({"type": "RESOLVED_BY", "source": "cause", "target": f"a{n}", "record": f"R{n}",
                                      "conditions": [], "cite": [cause, alias], "premise_refs": []})
            return {"entities": entities, "relations": relations, "unclear": [], "section_context": []}
        return await super().json(**kw)


def recovering_pipeline(tmp_path, llm, workdir=None):
    doc = table_doc()
    cfg = RunConfig(
        quality=QualityConfig.quality_v1(visual_routing=False, reference_retrieval=False, graph_review=False),
        gates={"map": ["auto"], "doubts": [], "approval": ["auto"]},
    )
    pipeline = Pipeline(doc=doc, asset_name="Pump", llm=llm, config=cfg, workdir=workdir or tmp_path / "run")
    llm.pipeline = pipeline
    return pipeline


def test_quality_recovery_end_to_end_and_resume_without_calls(tmp_path):
    llm = RecoveringFake()
    pipeline = recovering_pipeline(tmp_path, llm)
    result = asyncio.run(pipeline.run())
    green = [r for r in result.relations if r.assertion.tier is Tier.GREEN]
    assert len(green) == 3
    assert {r.proposals[0].target.kind for r in green} == {"inspection", "repair", "escalation"}
    assert any(c["name"] == "kg_quality_review" for c in llm.calls)
    assert all(
        i.status == "REPRESENTED" for i in pipeline.coverage.items if i.kind in {"INSPECTION", "REPAIR", "ESCALATION"}
    )
    projection = write_exports(pipeline.workdir, result, pipeline.doc, asset=ASSET, source_title="fixture")
    assert load_quality(pipeline.workdir)["binding_status"] == "VERIFIED"
    changed = dict(projection)
    changed["nodes"][0]["name"] = "edited graph, identical counts"
    atomic_json(pipeline.workdir / "graph.json", changed)
    assert load_quality(pipeline.workdir)["binding_status"] == "STALE"

    class NoCalls(RecoveringFake):
        async def json(self, **kw):
            raise AssertionError("provider called on identical resume")

    resumed = recovering_pipeline(tmp_path, NoCalls())
    again = asyncio.run(resumed.run())
    assert len(again.quality_bundle["validation"]["public_assertion_ids"]) == 3


def test_t19_exhausted_budget_is_persisted_and_not_retried_identically(tmp_path):
    llm = RecoveringFake(fail_review=True)
    pipeline = recovering_pipeline(tmp_path, llm)
    result = asyncio.run(pipeline.run())
    assert result.report["review_status"] == "BACKLOG"
    assert any(r.status == "DEFERRED" for r in pipeline.coverage.requests)
    calls = sum(c["name"] == "kg_quality_review" for c in llm.calls)
    resumed = recovering_pipeline(tmp_path, RecoveringFake(fail_review=True))
    asyncio.run(resumed.run())
    assert not resumed.llm.calls and calls > 0


def test_t29_crash_after_delta_commit_does_not_repeat_review(tmp_path, monkeypatch):
    class SimulatedCrash(BaseException):
        pass

    original = RunState.save

    def crash(self, stage, payload, *args, **kwargs):
        if stage == "quality_review_checkpoint":
            raise SimulatedCrash()
        return original(self, stage, payload, *args, **kwargs)

    llm = RecoveringFake()
    pipeline = recovering_pipeline(tmp_path, llm)
    monkeypatch.setattr(RunState, "save", crash)
    with pytest.raises(SimulatedCrash):
        asyncio.run(pipeline.run())
    completed = [c["user"] for c in llm.calls if c["name"] == "kg_quality_review"]
    assert completed
    monkeypatch.setattr(RunState, "save", original)
    resumed = recovering_pipeline(tmp_path, RecoveringFake())
    result = asyncio.run(resumed.run())
    repeated = [c["user"] for c in resumed.llm.calls if c["name"] == "kg_quality_review"]
    assert not set(completed) & set(repeated)
    assert len(result.quality_bundle["validation"]["public_assertion_ids"]) == 3
    assert len(set(resumed.source_index.applied_delta_ids)) == len(resumed.source_index.applied_delta_ids)


def test_isolated_entities_are_preserved_as_observations():
    from backend.kg_v3.source_index import inventory_mentions

    doc, index, units = setup_table()
    ref = index.atomic_refs["p1.t1.r2"][1]
    inventory_mentions(
        index, [{"type": "FailureMode", "name": "Blown fuse", "cite": [ref], "stated": True}], units[0], "A"
    )
    assert len(index.mentions) == 1
    assert not validate_quality(assemble([], []), [], index, doc)["public_assertion_ids"]


def test_t28_context_action_needs_verification_from_cause_only_child():
    doc, index, units = setup_table()
    action = next(r for r in index.atomic_refs["p1.t1.r2"] if index.evidence[r].column == 2)
    unit = next(u for u in units if action in u.owned_evidence_ref_ids)
    # A child unit owning the cause but reading the action only as context.
    child = unit.model_copy(update={"owned_evidence_ref_ids": [r for r in unit.owned_evidence_ref_ids if r != action],
                                    "context_evidence_ref_ids": [*unit.context_evidence_ref_ids, action]})
    p = proposal(doc, index, units, action=action)
    p = p.model_copy(update={"unit_id": child.unit_id, "validation_issues": []})
    rebound = bind_proposal(index, doc, p, child)
    assert "CONTEXT_ONLY_TARGET" in rebound.validation_issues
    rejected = check(doc, index, [child], [rebound], Fake(supported=False))
    assert all(r.assertion.tier is not Tier.GREEN for r in rejected)
    verified = check(doc, index, [child], [rebound, rebound.model_copy(update={"read": "B"})])
    assert all("CONTEXT_ONLY_TARGET" not in r.assertion.certificate.validation_issues for r in verified)


def test_text_only_agent_keeps_visual_question_pending(tmp_path):
    from backend.kg_v3.contracts import AnswerOption, Question, QuestionKind
    from backend.kg_v3.reviewers import AgentReviewer

    class NoCalls:
        async def __call__(self, **kw):
            raise AssertionError("text reviewer cannot judge image evidence")

    question = Question(
        question_id="image",
        kind=QuestionKind.RELATION_CHECK,
        title="Does the native image support this relation?",
        proposal=["Printed outcome leads to remedy"],
        source_regions=[
            {"page": 1, "bbox": [0, 0, 10, 10], "render_fingerprint": "hash", "image_path": str(tmp_path / "crop.png")}
        ],
        options=[
            AnswerOption(option_id="accept", label="Confirm", effect="Confirm"),
            AnswerOption(option_id="reject", label="Reject", effect="Reject"),
            AnswerOption(option_id="correct", label="Partial", effect="Keep selected statements"),
        ],
        default_option_id="accept",
    )
    reviewer = AgentReviewer(NoCalls(), model="gpt-6-luna")
    assert asyncio.run(reviewer.review([question])) == []


def test_t29_visual_catalog_crash_reuses_completed_model_responses(tmp_path, monkeypatch):
    class SimulatedCrash(BaseException):
        pass

    original = RunState.save

    def crash(self, stage, payload, *args, **kwargs):
        if stage == "quality_routes":
            raise SimulatedCrash()
        return original(self, stage, payload, *args, **kwargs)

    pdf = tmp_path / "image.pdf"
    image_pdf(pdf)
    cfg = RunConfig(
        quality=QualityConfig.quality_v1(completeness_review=False, reference_retrieval=False, graph_review=False),
        gates={"map": ["auto"], "doubts": [], "approval": ["auto"]},
    )
    pipeline = Pipeline(
        doc=DocumentText(page_count=1),
        asset_name="Pump",
        pdf_path=pdf,
        llm=Fake(),
        config=cfg,
        workdir=tmp_path / "run",
    )
    monkeypatch.setattr(RunState, "save", crash)
    with pytest.raises(SimulatedCrash):
        asyncio.run(pipeline.run())
    monkeypatch.setattr(RunState, "save", original)
    llm = Fake()
    resumed = Pipeline(
        doc=DocumentText(page_count=1), asset_name="Pump", pdf_path=pdf, llm=llm, config=cfg, workdir=tmp_path / "run"
    )
    result = asyncio.run(resumed.run())
    assert not any(c["name"] in {"kg_quality_visual_route", "kg_quality_visual_layout"} for c in llm.calls)
    assert len(result.quality_bundle["validation"]["public_assertion_ids"]) == 2


def test_numbered_branches_can_share_one_printed_indicator_cell():
    doc = table_doc("1. Replace fuse 2. Clean contacts")
    row = doc.pages[1][1]
    doc.pages[1][1] = row.model_copy(
        update={"text": "No power | 1. Blown fuse 2. Dirty contacts | 1. Replace fuse 2. Clean contacts"}
    )
    doc = DocumentText(page_count=1, pages=doc.pages)
    index = index_for(doc)
    units = build_quality_units(doc, page_map(doc), index)
    cells = index.atomic_refs["p1.t1.r2"]
    symptom = next(r for r in cells if index.evidence[r].column == 0)
    causes = [r for r in cells if index.evidence[r].column == 1]
    assert len(index.ref_branches[symptom]) == 2
    for cause in causes:
        p = Proposal(
            unit_id=units[0].unit_id,
            read="A",
            relation_type="MAY_INDICATE",
            record="R1",
            source=Endpoint(type="Symptom", name="No power", denotation_status="STATED", cites=[symptom]),
            target=Endpoint(
                type="FailureMode",
                name=re.sub(r"^\d+[.]\s*", "", index.evidence[cause].exact_text),
                denotation_status="STATED",
                cites=[cause],
            ),
            cites=[symptom, cause],
        )
        p = bind_proposal(index, doc, p, units[0])
        assert "CROSS_BRANCH_CONTAMINATION" not in p.validation_issues
        rs = check(doc, index, units, [p, p.model_copy(update={"read": "B"})])
        assert rs[0].assertion.tier is Tier.GREEN
