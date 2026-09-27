import json
from types import SimpleNamespace

from backend.kg_v3.checker import CheckedRelation, Checker, group_candidates, statement
from backend.kg_v3.contracts import ContextItem, ReadingUnit, Segment, SegmentKind
from backend.kg_v3.export import graph_json
from backend.kg_v3.extractor import parse_read
from backend.kg_v3.merger import assemble
from backend.kg_v3.ontology import extraction_schema, load_ontology
from backend.kg_v3.reader import DocumentText
from scripts.kg_v3_evaluate import pair_line, v3_edges


def test_typed_context_section_scope_export_and_legacy_graph(tmp_path):
    spec = load_ontology()
    unit = ReadingUnit(unit_id='u1', pages=[1], section='test', segment_ids=['p1.b2'], context_segment_ids=['p1.b1'])
    conditions = [{'kind': kind, 'text': f'{kind} detail', 'cite': ['p1.b2']}
                  for kind in ['if', 'prerequisite', 'expected', 'order']]
    data = {'entities': [{'key': 'f', 'type': 'FailureMode', 'name': 'low battery', 'cite': ['p1.b2']},
                         {'key': 'a', 'type': 'CorrectiveAction', 'name': 'replace battery', 'cite': ['p1.b2']}],
            'relations': [{'type': 'RESOLVED_BY', 'source': 'f', 'target': 'a', 'record': 'R1',
                           'conditions': conditions, 'cite': ['p1.b2']}],
            'section_context': [{'kind': 'warning', 'text': 'Do not turn off', 'cite': ['p1.b1'], 'records': ['R1']},
                                {'kind': 'warning', 'text': 'Other procedure only', 'cite': ['p1.b1'], 'records': ['R2']}]}
    proposals, _, _ = parse_read(data, unit=unit, read='A', spec=spec, allowed={'p1.b1', 'p1.b2'})
    p = proposals[0]
    assert {c.kind for c in p.conditions} == {'if', 'prerequisite', 'warning', 'expected', 'order'}
    assert all(c.text != 'Other procedure only' for c in p.conditions)
    assert 'p1.b1' in p.all_cites
    assert '[expected] expected detail' in statement(spec, p)
    assert '[warning] Do not turn off' in statement(spec, p)
    checker = Checker(None, spec, extractor_id='test')
    candidate = group_candidates([p])[0]
    candidate.structure = True
    checked = [CheckedRelation(assertion=checker._assertion(candidate), proposals=[p])]
    doc = DocumentText(page_count=1, pages={1: [Segment(segment_id=f'p1.b{i}', page=1, kind=SegmentKind.TEXT,
                  text='source text', evidence_id=f'e{i}') for i in [1, 2]]})
    result = SimpleNamespace(graph=assemble(checked, []), relations=checked, status='test', report={})
    exported = graph_json(result, doc, asset={'name': 'machine'}, source_title='test')
    edge = exported['edges'][0]
    assert edge['conditions'] == edge['occurrences'][0]['conditions']
    (tmp_path / 'graph.json').write_text(json.dumps(exported))
    assert {c['kind'] for c in v3_edges(tmp_path)[0]['conditions']} == {c.kind for c in p.conditions}
    exported['edges'][0]['conditions'] = ['legacy threshold']
    (tmp_path / 'graph.json').write_text(json.dumps(exported))
    old = v3_edges(tmp_path)[0]
    line = pair_line('p1', {'kind': 'action', 'left': 'low battery', 'right': 'replace battery'}, [old])
    assert '[if] legacy threshold' in line
    assert ContextItem.model_validate('legacy threshold').kind == 'if'
    assert extraction_schema(spec, ['p1.b1'])['properties']['relations']['items']['properties']['conditions']['items']['type'] == 'object'
