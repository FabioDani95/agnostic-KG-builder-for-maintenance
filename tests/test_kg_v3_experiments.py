import asyncio

from backend.kg_v3.checker import CheckedRelation
from backend.kg_v3.contracts import Assertion, Certificate, ReadingUnit, Tier, VerifierVerdict
from backend.kg_v3.omissions import review_omissions
from backend.kg_v3.ontology import load_ontology
from backend.kg_v3.run import RunConfig
from tests.test_kg_v3_merger import _merged_cell_doc, _read_a


def test_omission_review_is_bounded_off_by_default_and_must_pass_checker():
    assert not RunConfig().omission_review
    p = _read_a()[0]
    relation = CheckedRelation(proposals=[p], assertion=Assertion(assertion_id='c', relation_type=p.relation_type,
        source_key='s', target_key='t', record_key='r', certificate=Certificate(
            segment_ids=p.cites, verifier_verdict=VerifierVerdict.NOT_SUPPORTED)))
    units = [ReadingUnit(unit_id=unit, pages=[28], segment_ids=['p28.t1.r2']) for unit in ['u001', 'u002']]

    class Reviewer:
        calls = []

        async def json(self, **kwargs):
            self.calls.append(kwargs['name'])
            if kwargs['name'] == 'kg_v3_verify':
                return {'verdicts': [{'id': 'S1', 'verdict': 'not_supported'}]}
            assert 'CURRENT BRANCH:' in kwargs['user'] and 'Blown fuse' in kwargs['user']
            return {'entities': [
                {'key': 'f', 'type': 'FailureMode', 'name': 'Blown fuse', 'cite': p.cites},
                {'key': 'a', 'type': 'CorrectiveAction', 'name': 'Invented repair', 'cite': p.cites}],
                'relations': [{'type': 'RESOLVED_BY', 'source': 'f', 'target': 'a', 'record': 'R1',
                               'cite': p.cites, 'conditions': []}]}

    llm = Reviewer()
    added, attempts = asyncio.run(review_omissions(llm, _merged_cell_doc(), units, [relation], load_ontology(), limit=1))
    assert attempts == ['u001'] and len(added) == 1
    assert added[0].assertion.tier is not Tier.GREEN
    assert llm.calls == ['kg_v3_omissions', 'kg_v3_verify']


def test_image_adapter_uses_archived_chat_content_and_flag_defaults_off():
    import json
    from types import SimpleNamespace

    from backend.kg_v3.llm import ModelClient

    assert not RunConfig().visual_verification

    class Provider:
        async def create(self, **kwargs):
            content = kwargs['messages'][1]['content']
            assert content[0] == {'type': 'text', 'text': 'Check row'}
            assert content[1]['image_url'] == {'url': 'data:image/png;base64,AA==', 'detail': 'high'}
            return SimpleNamespace(model='gpt-6-luna', usage=None, choices=[SimpleNamespace(
                finish_reason='stop', message=SimpleNamespace(content=json.dumps({'ok': True})))])

    client = SimpleNamespace(chat=SimpleNamespace(completions=Provider()))
    result = asyncio.run(ModelClient(model='gpt-6-luna', client_factory=lambda: client).json(
        system='test', user='Check row', images=['data:image/png;base64,AA=='], schema={}, name='test'))
    assert result == {'ok': True}


def test_visual_selection_requires_green_and_table_dependency(tmp_path):
    import fitz

    from backend.kg_v3.vision import row_images, table_dependent, visual_check
    from tests.test_kg_v3_merger import _agreed_relation

    doc = _merged_cell_doc()
    row = doc.segment('p28.t1.r3')
    doc.pages[28][2] = row.model_copy(update={'bbox': (20, 30, 300, 100)})
    doc.__post_init__()
    pdf = tmp_path / 'source.pdf'
    with fitz.open() as source:
        for _ in range(28):
            source.new_page()
        source[27].insert_text((30, 50), 'Low output | Check cable | If persists, service')
        source.save(pdf)
    r = _agreed_relation()
    r.assertion = r.assertion.model_copy(update={'certificate': r.assertion.certificate.model_copy(
        update={'segment_ids': [row.segment_id]})})
    assert table_dependent(doc, r)
    assert row_images(pdf, doc, [row.segment_id])[0].startswith('data:image/png;base64,')
    # A disabled/zero-cap experiment makes no calls.
    after, records = asyncio.run(visual_check(None, doc, [r], pdf, limit=0))
    assert after == [r] and not records
