from backend.kg_v3.checker import CheckedRelation
from backend.kg_v3.contracts import Assertion, Certificate, Segment, SegmentKind, Witness
from backend.kg_v3.extractor import Endpoint, Proposal
from backend.kg_v3.merger import assemble
from backend.kg_v3.navigation import reconnect_proposals
from backend.kg_v3.reader import DocumentText


def test_orphan_procedure_links_only_to_its_unique_known_introduction():
    texts = ['Problem alpha.', '1. Inspect first part.', '2. Inspect second part.', 'Other problem.']
    doc = DocumentText(page_count=1, pages={1: [Segment(segment_id=f'p1.b{i}', page=1, kind=SegmentKind.TEXT,
                    text=text, evidence_id=f'e{i}') for i, text in enumerate(texts, 1)]})
    problem = Endpoint(type='Symptom', name='alpha', cites=['p1.b1'])
    cause = Endpoint(type='FailureMode', name='second part', cites=['p1.b3'])
    proposals = [Proposal(unit_id='u1', read='A', record='R1', relation_type='MAY_INDICATE', source=problem,
                          target=Endpoint(type='FailureMode', name='first part', cites=['p1.b2']), cites=['p1.b1']),
                 Proposal(unit_id='u1', read='A', record='R2', relation_type='RESOLVED_BY', source=cause,
                          target=Endpoint(type='CorrectiveAction', name='inspect', cites=['p1.b3']), cites=['p1.b3'])]
    relations = [CheckedRelation(proposals=[p], assertion=Assertion(assertion_id=f'a{i}', relation_type=p.relation_type,
                    source_key=p.source.name, target_key=p.target.name, record_key=p.record,
                    certificate=Certificate(segment_ids=p.all_cites, witnesses=[Witness.STRUCTURE, Witness.AGREEMENT])))
                 for i, p in enumerate(proposals)]
    graph = assemble(relations, [])
    repairs = reconnect_proposals(doc, graph, relations)
    assert len(repairs) == 1
    assert repairs[0].source == problem and repairs[0].target == cause
    # An unrelated preceding/following block is not the sequence's introduction.
    problem.cites = ['p1.b4']
    assert reconnect_proposals(doc, graph, relations) == []
