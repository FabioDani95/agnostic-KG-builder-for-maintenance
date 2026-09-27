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
