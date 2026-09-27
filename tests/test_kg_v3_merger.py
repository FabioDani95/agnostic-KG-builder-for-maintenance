"""Reads that name one end differently, with names judged different, are never fused."""

from __future__ import annotations

from backend.kg_v3.checker import CheckedRelation
from backend.kg_v3.contracts import (
    Assertion,
    Certificate,
    Segment,
    SegmentKind,
    Tier,
    VerifierVerdict,
    Witness,
)
from backend.kg_v3.extractor import Endpoint, Proposal
from backend.kg_v3.merger import MergePair, assemble, identity, merge_candidates, split_disagreements
from backend.kg_v3.reader import DocumentText

ROW = "p44.b1"
DOC = DocumentText(page_count=44, pages={44: [Segment(
    segment_id=ROW, page=44, kind=SegmentKind.TEXT, evidence_id="ev1",
    text="Pump does not attain its pumping speed: valve of the pressure balance line does not close.")]})


def _proposal(read: str, cause: str) -> Proposal:
    return Proposal(unit_id="u001", read=read, relation_type="MAY_INDICATE", record="R6", cites=[ROW],
                    source=Endpoint(type="Symptom", name="Pump does not attain its pumping speed", cites=[ROW]),
                    target=Endpoint(type="FailureMode", name=cause, cites=[ROW]))


def _agreed_relation() -> CheckedRelation:
    certificate = Certificate(segment_ids=[ROW], witnesses=[Witness.STRUCTURE, Witness.AGREEMENT, Witness.VERIFIER],
                              verifier_verdict=VerifierVerdict.SUPPORTED)
    assertion = Assertion(assertion_id="u001.c1", relation_type="MAY_INDICATE",
                          source_key="Symptom:Pump does not attain its pumping speed",
                          target_key="FailureMode:Pressure balance line valve does not open",
                          record_key="u001:A.R6", certificate=certificate)
    return CheckedRelation(assertion=assertion, proposals=[
        _proposal("A", "Pressure balance line valve does not open"),
        _proposal("B", "Pressure balance line valve does not close")])


def test_differently_named_ends_of_one_relation_are_always_judged():
    pairs = merge_candidates([_agreed_relation()])
    names = {frozenset((pair.left_name, pair.right_name)) for pair in pairs}
    assert frozenset(("Pressure balance line valve does not open",
                      "Pressure balance line valve does not close")) in names


def test_names_judged_different_split_the_relation_and_lose_agreement():
    relation = _agreed_relation()
    lead, other = relation.proposals
    different = [MergePair(left=identity(lead.target), right=identity(other.target), left_name="", right_name="",
                           type="FailureMode", verdict="different")]
    parts = split_disagreements(DOC, [relation], different)
    assert len(parts) == 2
    kept, apart = parts
    assert Witness.AGREEMENT not in kept.assertion.certificate.witnesses
    assert kept.assertion.certificate.witnesses == [Witness.STRUCTURE, Witness.VERIFIER]
    assert kept.assertion.tier is Tier.GREEN
    # The other name keeps only its structural witness: it becomes a question, not a lost fact.
    assert apart.assertion.certificate.witnesses == [Witness.STRUCTURE]
    assert apart.assertion.tier is Tier.YELLOW
    assert apart.assertion.target_key.endswith("does not close")
    graph = assemble(parts, [])
    targets = {graph.nodes_by_id[edge.target].name for edge in graph.edges}
    assert targets == {"Pressure balance line valve does not open", "Pressure balance line valve does not close"}


def test_names_not_judged_different_stay_one_relation():
    relation = _agreed_relation()
    assert split_disagreements(DOC, [relation], []) == [relation]


# Merged cells ---------------------------------------------------------------

def _merged_cell_doc() -> DocumentText:
    from backend.kg_v3.contracts import TableCoordinates

    headers = ["Problem", "Checks", "Escalation"]

    def row(number: int, text: str, inherited: list[int]) -> Segment:
        return Segment(segment_id=f"p28.t1.r{number}", page=28, kind=SegmentKind.TABLE_ROW, text=text,
                       evidence_id=f"ev{number}",
                       table=TableCoordinates(table=1, row=number, headers=headers, inherited_columns=inherited))

    return DocumentText(page_count=28, pages={28: [
        row(1, "Problem | Checks | Escalation", []),
        row(2, "No output | Replace the fuse | If the problem persists, contact service", []),
        row(3, "Low output | Check the cable | If the problem persists, contact service", [2]),
    ]})


def _read_a() -> list[Proposal]:
    def end(type_, name, cite):
        return Endpoint(type=type_, name=name, cites=[cite])

    r2, r3 = "p28.t1.r2", "p28.t1.r3"
    return [
        Proposal(unit_id="u001", read="A", relation_type="MAY_INDICATE", record="R1", cites=[r2],
                 source=end("Symptom", "No output", r2), target=end("FailureMode", "Blown fuse", r2)),
        Proposal(unit_id="u001", read="A", relation_type="RESOLVED_BY", record="R1", cites=[r2],
                 source=end("FailureMode", "Blown fuse", r2), target=end("CorrectiveAction", "Replace the fuse", r2)),
        Proposal(unit_id="u001", read="A", relation_type="RESOLVED_BY", record="R1", cites=[r2],
                 source=end("FailureMode", "Blown fuse", r2), target=end("CorrectiveAction", "Contact service", r2)),
        Proposal(unit_id="u001", read="A", relation_type="MAY_INDICATE", record="R2", cites=[r3],
                 source=end("Symptom", "Low output", r3), target=end("FailureMode", "Damaged cable", r3)),
        Proposal(unit_id="u001", read="A", relation_type="RESOLVED_BY", record="R2", cites=[r3],
                 source=end("FailureMode", "Damaged cable", r3), target=end("CorrectiveAction", "Check the cable", r3)),
    ]


class _Verifier:
    """Supports every statement except the fuse remedy for the cable cause (not in that row)."""

    async def json(self, *, user: str, schema: dict, **_kwargs):
        ids = schema["properties"]["verdicts"]["items"]["properties"]["id"]["enum"]
        blocks = dict(zip(ids, user.split("Statement ")[1:]))
        return {"verdicts": [{"id": item, "verdict": "not_supported" if "Damaged cable" in blocks[item]
                              and "Replace the fuse" in blocks[item] else "supported"} for item in ids]}


def test_a_merged_cell_remedy_reaches_every_row_that_repeats_it():
    from backend.kg_v3.checker import STRUCTURE_READ, Checker, inherited_cell_proposals
    from backend.kg_v3.ontology import load_ontology

    doc = _merged_cell_doc()
    hypotheses = inherited_cell_proposals(doc, _read_a())
    assert {(item.source.name, item.target.name) for item in hypotheses} == {
        ("Damaged cable", "Replace the fuse"), ("Damaged cable", "Contact service")}
    import asyncio

    checked = asyncio.run(Checker(_Verifier(), load_ontology(), extractor_id="test").check(doc, _read_a()))
    kept = {(item.proposals[0].source.name, item.proposals[0].target.name) for item in checked
            if item.proposals[0].read == STRUCTURE_READ}
    # Only the verified hypothesis survives; the first row's own remedy is not copied.
    assert kept == {("Damaged cable", "Contact service")}
