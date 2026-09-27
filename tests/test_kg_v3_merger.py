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


def test_transitive_merge_cannot_cross_a_different_constraint():
    base = _agreed_relation()
    ends = [Endpoint(type="FailureMode", name=name, cites=[ROW]) for name in ('alpha', 'beta', 'gamma')]
    relations = [base.model_copy(update={'proposals': [base.proposals[0].model_copy(update={'target': end})]})
                 for end in ends]

    def pair(a, b):
        return MergePair(left=identity(ends[a]), right=identity(ends[b]), left_name=ends[a].name,
                         right_name=ends[b].name, type='FailureMode')

    graph = assemble(relations, [pair(0, 1), pair(1, 2)], [pair(0, 2)])
    assert len([n for n in graph.nodes.values() if n.type == 'FailureMode']) == 2
    assert all(not {'alpha', 'gamma'} <= {n.name, *n.aliases} for n in graph.nodes.values())
    assert graph.blocked_merges[0]['reason'] == 'different'


def test_numeric_conflict_blocks_judge_and_alias_unions():
    base = _agreed_relation()
    a, b = [Endpoint(type='FailureMode', name=f'pressure {number}', cites=[ROW]) for number in (10, 20)]
    base.proposals[0].target, base.proposals[1].target = a, b
    pair = MergePair(left=identity(a), right=identity(b), left_name=a.name, right_name=b.name, type='FailureMode')
    graph = assemble([base], [pair])
    assert len([n for n in graph.nodes.values() if n.type == 'FailureMode']) == 2
    assert graph.blocked_merges[0]['reason'] == 'different_numbers'


def test_named_inferred_causes_do_not_merge_through_common_remedies():
    from backend.kg_v3.checker import _end_matches

    ends = [Endpoint(type='FailureMode', name=name, stated=False, cites=[ROW]) for name in
            ['Power switch is not ON', 'Clogged cable liner or contact tip', 'Spool gun switch set incorrectly']]
    assert not _end_matches(ends[0], ends[1], .5)
    relations = []
    for end in ends:
        for action in ['Check the machine', 'Contact service']:
            base = _agreed_relation()
            base.proposals = [Proposal(unit_id='u001', read='A', record='R1', relation_type='RESOLVED_BY',
                                       source=end, target=Endpoint(type='CorrectiveAction', name=action, cites=[ROW]),
                                       cites=[ROW])]
            relations.append(base)
    graph = assemble(relations, [])
    assert {n.name for n in graph.nodes.values() if n.type == 'FailureMode'} == {e.name for e in ends}


def test_placeholders_in_different_rows_do_not_merge_through_shared_remedies():
    relations = []
    for number, name in enumerate(['Unspecified cause of alpha', 'Unspecified cause of beta'], 2):
        for action in ['Check the machine', 'Contact service']:
            base = _agreed_relation()
            base.proposals = [Proposal(unit_id='u001', read='A', record=f'R{number}', relation_type='RESOLVED_BY',
                                       source=Endpoint(type='FailureMode', name=name, stated=False,
                                                       cites=[f'p1.t1.r{number}']),
                                       target=Endpoint(type='CorrectiveAction', name=action))]
            relations.append(base)
    graph = assemble(relations, [])
    assert len([n for n in graph.nodes.values() if n.type == 'FailureMode']) == 2


# Merged cells ---------------------------------------------------------------

def _merged_cell_doc() -> DocumentText:
    from backend.kg_v3.contracts import TableCoordinates

    headers = ["Problem", "Checks", "Escalation"]

    def row(number: int, text: str, inherited: list[int]) -> Segment:
        return Segment(segment_id=f"p28.t1.r{number}", page=28, kind=SegmentKind.TABLE_ROW, text=text,
                       evidence_id=f"ev{number}",
                       table=TableCoordinates(table=1, row=number, headers=headers, inherited_columns=inherited,
                                              confirmed_inherited_columns=inherited))

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


def test_inherited_actions_preserve_distinct_immediate_and_conditional_occurrences():
    from backend.kg_v3.checker import Checker, group_candidates, inherited_cell_proposals
    from backend.kg_v3.contracts import ContextItem
    from backend.kg_v3.ontology import load_ontology

    proposals = _read_a()
    immediate = proposals[2]
    conditional = immediate.model_copy(update={"read": "B", "conditions": [
        ContextItem(kind="if", text="Checks failed and problem persists", cite=("p28.t1.r2",))]})
    proposals.append(conditional)
    assert len(group_candidates([immediate, conditional])) == 2
    inherited = [p for p in inherited_cell_proposals(_merged_cell_doc(), proposals)
                 if p.target.name == "Contact service"]
    assert len(inherited) == 2
    assert {tuple(c.kind for c in p.conditions) for p in inherited} == {(), ("if",)}
    assert next(p for p in inherited if p.conditions).conditions == conditional.conditions
    checker = Checker(None, load_ontology(), extractor_id="test")
    checked = []
    for candidate in group_candidates([immediate, conditional, *inherited]):
        candidate.structure = True
        checked.append(CheckedRelation(assertion=checker._assertion(candidate), proposals=candidate.proposals))
    graph = assemble(checked, [])
    assert len(graph.edges) == 2
    for edge in graph.edges:
        assert len(edge.assertions) == 2
        assert edge.conditions == []  # no invented conjunction of alternatives
        assert {bool(a.conditions) for a in edge.assertions} == {False, True}
