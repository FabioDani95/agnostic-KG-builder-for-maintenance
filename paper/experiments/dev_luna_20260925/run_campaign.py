"""Development extraction pilot; cumulative durable USD 15 cap, no gold in prompts."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BUDGET = '15.00'
MODEL = 'gpt-6-luna'
LEDGER = OUT / 'real_call_budget.jsonl'


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + '\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def environment(run_id, sha):
    run = OUT / 'runs' / 'real' / run_id
    os.environ.update({
        'KG_LLM_MODE': 'real', 'KG_GENERATION_MODEL': MODEL, 'MODEL_NAME': MODEL,
        'KG_OPERATIONAL_DB': str(run / 'operational.db'),
        'KG_RAW_DIR': str(run / 'raw'), 'KG_INCOMING_DIR': str(run / 'incoming'),
        'KG_REAL_CALL_BUDGET_LEDGER': str(LEDGER), 'KG_REAL_CALL_BUDGET_USD': BUDGET,
        'KG_REAL_CALL_RUN_ID': run_id, 'KG_REAL_CALL_PDF_ID': sha,
    })


def snapshot():
    from backend.services.real_call_budget_ledger import RealCallBudgetLedger
    return RealCallBudgetLedger(LEDGER, absolute_budget_usd=BUDGET).snapshot().as_dict()


def smoke():
    environment('provider_smoke', 'synthetic-no-manual')
    from backend.config import settings
    from backend.services.llm_gateway import get_client
    from pydantic import BaseModel

    class Check(BaseModel):
        symptom: str
        action: str

    path = OUT / 'provider_smoke.json'
    if path.exists():
        return 0 if json.loads(path.read_text())['status'] == 'passed' else 1
    started = time.perf_counter()
    result = {'started_utc': now(), 'requested_model': MODEL, 'status': 'running'}
    write(path, result)
    try:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError('OPENAI_API_KEY unavailable')
        response = get_client(timeout=30, max_retries=0).chat.completions.parse(
            model=MODEL, reasoning_effort='low', max_completion_tokens=1500,
            service_tier='default',
            messages=[{'role': 'user', 'content': 'Extract only the stated symptom and action: If the filter is clogged, clean the filter.'}],
            response_format=Check,
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError('No structured output returned')
        result.update(status='passed', returned_model=response.model,
                      output=parsed.model_dump(), usage=response.usage.model_dump())
    except Exception as exc:
        message = str(exc)
        if settings.OPENAI_API_KEY:
            message = message.replace(settings.OPENAI_API_KEY, '[REDACTED]')
        result.update(status='failed', error_type=type(exc).__name__, error=message)
    result.update(elapsed_seconds=round(time.perf_counter()-started,3), finished_utc=now(), budget=snapshot())
    write(path, result)
    print(json.dumps(result), flush=True)
    return 0 if result['status']=='passed' else 1


def manual(ident):
    manifest = json.loads((OUT/'manifest.json').read_text())
    spec = next(x for x in manifest['manuals'] if x['manual_id']==ident)
    environment(ident, 'sha256:'+spec['sha256'])
    from backend.app_config import load_config
    from backend.services.pdf_source_subgraph_generation import PDF_SUBGRAPH_GENERATOR_VERSION
    cfg = load_config()
    # Keep the committed extraction profile; change only the run cost envelope.
    cfg['pdf_generation_cost_guard']['hard_ceiling_usd'] = 3.5
    cfg['pdf_generation_cost_guard']['preferred_cost_usd'] = 3.5
    assert cfg['agents']['ontology_draft']['model']==MODEL
    assert cfg['ontology']['diagnostic_escalation']['enabled'] is False
    run = OUT/'runs'/'real'/ident
    write(run/'runtime_profile.json', {
        'git_head': manifest['git_head'], 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'pipeline_version': PDF_SUBGRAPH_GENERATOR_VERSION, 'config': cfg,
        'config_sha256': hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest(),
        'packages': {n:importlib.metadata.version(n) for n in ['openai','pymupdf','pydantic','fastapi']},
        'gold_usage':'not_loaded_by_runner', 'shared_budget_usd':15,
    })
    base = ROOT/'artifacts/acceptance/g3/diagnostic_benchmark_20260812/run_benchmark_once.py'
    module_spec=importlib.util.spec_from_file_location('isolated_pilot_runner',base)
    runner=importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(runner)
    runner.CAMPAIGN_ROOT=OUT
    runner.MANUAL_ROOT=ROOT/'paper/manuals/files'
    runner._load_gold=lambda _: ({'campaign_id':OUT.name,'authorized_budget_usd':15,'per_run_hard_ceiling_usd':3.5},spec)
    sys.argv=[str(Path(__file__)), '--manual-id',ident,'--mode','real']
    started=time.perf_counter()
    timing={'started_utc':now(),'manual_id':ident,'status':'running'}
    write(run/'timing.json',timing)
    code=1
    try:
        code=runner.main()
        timing['status']='completed' if code==0 else 'failed'
    except Exception as exc:
        from backend.config import settings
        message=str(exc)
        if settings.OPENAI_API_KEY:message=message.replace(settings.OPENAI_API_KEY,'[REDACTED]')
        timing.update(status='failed',error_type=type(exc).__name__,error=message)
    finally:
        timing.update(finished_utc=now(),total_elapsed_seconds=round(time.perf_counter()-started,3),budget=snapshot())
        state_path=run/'run_state.json'
        if state_path.exists():
            state=json.loads(state_path.read_text())
            timing['generation_elapsed_seconds']=state.get('elapsed_seconds')
            if state.get('elapsed_seconds') is not None:
                timing['preparation_and_overhead_seconds']=round(timing['total_elapsed_seconds']-state['elapsed_seconds'],3)
        write(run/'timing.json',timing)
    print(json.dumps(timing),flush=True)
    return code


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--manual')
    args=parser.parse_args()
    sys.path.insert(0,str(ROOT))
    if args.smoke:return smoke()
    if args.manual:return manual(args.manual)
    path=OUT/'campaign_state.json'
    if path.exists():raise RuntimeError('Campaign already started; inspect records before resuming')
    state={'started_utc':now(),'budget_cap_usd':15,'status':'running','manuals':[]}
    write(path,state)
    started=time.perf_counter()
    try:
        proc=subprocess.run([sys.executable,str(Path(__file__)),'--smoke'],cwd=ROOT)
        if proc.returncode:
            state['status']='blocked_provider_smoke'
            return 1
        for m in json.loads((OUT/'manifest.json').read_text())['manuals']:
            ident=m['manual_id'];log=OUT/f'{ident}.log'
            with log.open('x') as stream:
                proc=subprocess.run([sys.executable,str(Path(__file__)),'--manual',ident],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
            state['manuals'].append({'manual_id':ident,'return_code':proc.returncode})
            write(path,state)
            print(json.dumps(state['manuals'][-1]),flush=True)
        state['status']='completed' if all(x['return_code']==0 for x in state['manuals']) else 'completed_with_failures'
    finally:
        state.update(finished_utc=now(),elapsed_seconds=round(time.perf_counter()-started,3),budget=snapshot())
        write(path,state)
    return 0 if state['status']=='completed' else 1


if __name__=='__main__':
    raise SystemExit(main())
