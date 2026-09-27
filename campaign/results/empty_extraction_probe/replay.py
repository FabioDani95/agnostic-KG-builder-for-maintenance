"""Controlled intervention: replay Atlas D/r3's exact two empty reads, then allow live recovery.

This is not an independent run and never replaces any of the 18 campaign D runs.
Only map/gate-map state is reused; checks, merge and review after recovery run again.
"""
import asyncio
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
from backend.kg_v3 import llm  # noqa: E402
from scripts.kg_v3 import run  # noqa: E402

manual = 'atlascopco_drb_booster'
source = ROOT / f'campaign/{manual}/runs_D_pending/v3_r3'
if not source.exists():
    source = ROOT / f'campaign/{manual}/runs/v3_r3'
out = ROOT / f'campaign/{manual}/runs_empty_probe/v3_r1'
assert not out.exists(), 'Preserve existing probe; do not overwrite or repeat implicitly'
(out / 'state').mkdir(parents=True)
inputs = ROOT / 'campaign/results/empty_extraction_probe'
inputs.mkdir(exist_ok=True)
traces = []
for name in ('686ba6ca47b04d48abf8a4325da8641a', 'd734da4ae8ea4a8dbb084d29c91000e0'):
    path = source / f'provider_responses/{name}.json'
    trace = json.loads(path.read_text())
    shutil.copy2(path, inputs / f'{name}.json')
    traces.append(trace)
for name in ('map.json', 'gate_map.json'):
    shutil.copy2(source / 'state' / name, out / 'state' / name)
events = []
OriginalClient = llm.ModelClient


class ReplayThenLive(OriginalClient):
    async def json(self, **kwargs):
        if kwargs.get('name') == 'kg_v3_extract' and len(events) < 2:
            trace = traces[len(events)]
            request = trace['request']
            assert kwargs['system'] == request['messages'][0]['content']
            assert kwargs['user'] == request['messages'][1]['content']
            assert kwargs['schema'] == request['response_format']['json_schema']['schema']
            result = llm.decode_json(trace['response']['choices'][0]['message']['content'])
            assert result['entities'] and not result['relations']
            events.append({'original_call_id': trace['call_id'], 'entities': len(result['entities']),
                           'relations': len(result['relations']), 'new_cost_usd': 0})
            return result
        return await super().json(**kwargs)


llm.ModelClient = ReplayThenLive
os.environ['KG_REAL_CALL_SPEND_CEILING_USD'] = '7.204403'
args = SimpleNamespace(manual=manual, out=str(out), ledger=str(ROOT / 'campaign/real_call_budget.jsonl'),
                       budget='10', run_id='empty_extraction_controlled_probe', gates='agent',
                       model='gpt-6-luna', reasoning='low', agent_model='gpt-6-luna', agent_reasoning='medium', reads=2)
report = asyncio.run(run(args))
assert len(events) == 2, 'Both original reads must be replayed exactly'
manifest = {'design': __doc__, 'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            'original_run': str(source.relative_to(ROOT)), 'probe_run': str(out.relative_to(ROOT)),
            'replayed_reads': events, 'original_graph_sha256': hashlib.sha256((source / 'graph.json').read_bytes()).hexdigest(),
            'report': report, 'note': 'Usage excludes the two replayed calls, whose original costs remain in campaign D.'}
(inputs / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ('status', 'graph', 'failed_reads', 'incomplete_reasons', 'usage')}))
