"""Verify correction API on a disposable SQLite backup; never change source runs."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    origin = args.source_run / 'operational.db'
    before = hashlib.sha256(origin.read_bytes()).hexdigest()
    clone = Path(tempfile.mkdtemp(prefix='kg-review-verified-')) / 'operational.db'
    with sqlite3.connect(origin.resolve().as_uri() + '?mode=ro', uri=True) as src, sqlite3.connect(clone) as dst:
        src.backup(dst)
    os.environ.update(KG_OPERATIONAL_DB=str(clone), KG_LLM_MODE='mock')
    from fastapi.testclient import TestClient

    from backend.domain.ids import new_id, utc_now
    from backend.domain.subgraphs import SourceSubgraphRevision
    from backend.main import create_app
    from backend.services.pdf_source_subgraph_generation import pdf_input_config_hash
    from backend.services.source_subgraph_generation import SourceSubgraphGenerationService

    service = SourceSubgraphGenerationService()
    graph = SourceSubgraphRevision.model_validate_json((args.source_run / 'graph.json').read_text())
    seed = graph.model_copy(update={'source_subgraph_revision_id': new_id('source_subgraph'), 'created_at': utc_now(),
        'supersedes': graph.source_subgraph_revision_id, 'input_config_hash': pdf_input_config_hash(), 'review_base_config_hash': None})
    service.subgraphs.create(seed)
    target = next(r for r in seed.diagnostic_compilation_ledger['records'] if r.get('disposition') == 'publish'
                  and 'completely clogged' in (r.get('candidate', {}).get('failure') or {}).get('name', ''))
    branch = target['branch_lineage_id']
    payload = {'candidate': deepcopy(target['candidate']), 'reviewer': 'Automated application check; not human annotation',
               'reason': 'Recompile a source-supported branch and preserve all unrelated claims.'}
    client = TestClient(create_app())
    url = f'/api/g3/subgraphs/{seed.source_subgraph_revision_id}/records/{branch}/correction'
    response = client.post(url, json=payload)
    assert response.status_code == 200, response.text
    after = service.subgraphs.current_for_workspace(seed.workspace_id)[seed.source_id]
    assert after.validation.passed
    unchanged = [r.model_dump(mode='json') for r in seed.relations if r.branch_lineage_id != branch]
    assert all(r in [x.model_dump(mode='json') for x in after.relations] for r in unchanged)
    assert client.post(url, json=payload).status_code == 409
    assert client.post(f'/api/g3/subgraphs/{after.source_subgraph_revision_id}/decision', json={'action':'approve','note':'Must remain blocked'}).status_code == 409
    changed_branch = after.diagnostic_review_history[-1]['after']['branch_lineage_id']
    bad = deepcopy(payload)
    bad['candidate']['indicators'][0]['claim_evidence'][0]['quote'] = 'THIS QUOTE IS NOT PRESENT IN THE SOURCE'
    bad['reason'] = 'Negative test: invalid citation must not enter the publication graph.'
    response = client.post(f'/api/g3/subgraphs/{after.source_subgraph_revision_id}/records/{changed_branch}/correction', json=bad)
    assert response.status_code == 200, response.text
    invalid = service.subgraphs.current_for_workspace(seed.workspace_id)[seed.source_id]
    assert invalid.diagnostic_review_history[-1]['after']['disposition'] == 'review'
    assert not invalid.approval_eligible
    assert len(invalid.diagnostic_review_history) == 2
    assert not any(r.branch_lineage_id == changed_branch for r in invalid.relations)
    assert hashlib.sha256(origin.read_bytes()).hexdigest() == before
    result = {'mode':'isolated_copy_no_model_calls_not_human_annotation','copy':str(clone),'source_run':str(args.source_run),
              'source_database_unchanged':True,'valid_status':200,'stale_status':409,'residual_approval_status':409,
              'invalid_status':200,'invalid_remains_review':True,'unchanged_other_relations':len(unchanged),'history_entries':2,
              'workspace_id':seed.workspace_id,'source_id':seed.source_id}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
