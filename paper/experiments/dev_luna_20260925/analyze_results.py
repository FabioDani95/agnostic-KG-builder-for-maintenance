"""Summarise development runs without treating partial historical gold as precision."""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))


def read(path):
    return json.loads(path.read_text())


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def load_analyzer():
    path=ROOT/'artifacts/acceptance/g3/diagnostic_benchmark_second_hardening_20260813/analyze_campaign.py'
    spec=importlib.util.spec_from_file_location('historical_semantic_analyzer',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    wrapped=module._load()
    wrapped.RUNS_ROOT=OUT/'runs/real'
    analyzer=wrapped._load_frozen_analyzer()
    analyzer.published_paths=wrapped._branch_aware_paths
    analyzer.exact_grounding=wrapped._strict_grounding
    return analyzer


def main():
    campaign=read(OUT/'campaign_state.json')
    if campaign['status']=='running':raise RuntimeError('Do not analyse an unfinished campaign')
    events=[json.loads(x) for x in (OUT/'real_call_budget.jsonl').read_text().splitlines()]
    reserved={e['call_id']:e for e in events if e['event']=='call_reserved'}
    costs=defaultdict(lambda:dict(calls=0,estimated_usd=0.,charged_usd=0.,unknown_cost_calls=0,failed_calls=0,prompt_tokens=0,completion_tokens=0,models=Counter()))
    for event in events:
        if event['event']!='call_finalized':continue
        request=reserved[event['call_id']];d=costs[request['run_id']]
        d['calls']+=1;d['models'][request['model']]+=1
        d['charged_usd']+=float(event['charged_cost_usd'])
        if event.get('actual_cost_usd') is None:d['unknown_cost_calls']+=1
        else:d['estimated_usd']+=float(event['actual_cost_usd'])
        d['failed_calls']+=int(str(event.get('status','')).startswith('failed'))
        for key in ('prompt_tokens','completion_tokens'):d[key]+=int((event.get('actual_usage') or {}).get(key,0))
    manifest=read(OUT/'manifest.json')
    golden=ROOT/'artifacts/acceptance/g3/diagnostic_benchmark_20260812/golden.json'
    specs={m['manual_id']:m for m in read(golden)['manuals']}
    analyzer=load_analyzer()
    budget_audit={
        'cap_usd':15,
        'all_reservations_within_cap':all(float(e['committed_before_usd'])+float(e['active_reserved_before_usd'])+float(e['worst_case_cost_usd'])<=15+1e-10 for e in reserved.values()),
        'no_token_envelope_breaches':all(not e.get('envelope_breached',False) for e in events if e['event']=='call_finalized'),
        'all_attempts_finalized':len(reserved)==sum(e['event']=='call_finalized' for e in events),
    }
    results=[]
    for manual in manifest['manuals']:
        ident=manual['manual_id'];run=OUT/'runs/real'/ident
        result={'manual_id':ident,'label':manual['asset']['name'],'cost':costs.get(ident), 'timing':read(run/'timing.json') if (run/'timing.json').exists() else None}
        response_path=run/'generation_response.json'
        if response_path.exists():
            response=read(response_path)
            revisions=[s['subgraph'] for s in response.get('sources',[]) if s.get('subgraph')]
            if len(revisions)!=1:raise RuntimeError('Ambiguous revision')
            rev=revisions[0];write(run/'graph.json',rev)
            ledger = rev.get('diagnostic_compilation_ledger') or {}
            result['diagnostic_compilation'] = {k:ledger.get(k) for k in ['candidate_count','publish_count','unresolved_count','contract_failure_count','drop_reasons','diagnostic_page_coverage_complete','unreadable_page_count']}
            result.update(nodes=len(rev['nodes']),relations=len(rev['relations']),node_types=dict(Counter(x['node_type'] for x in rev['nodes'])),review=rev['review_summary'],approval_eligible=rev['approval_eligible'],validation=rev['validation'],publication=rev['publication_metrics'],exact_grounding=analyzer.exact_grounding(rev))
            if ident in specs:
                try:
                    evaluation=analyzer.analyze_manual(specs[ident])
                    write(run/'historical_gold_evaluation.json',evaluation)
                    result['historical_gold']={k:v for k,v in evaluation['semantic'].items() if k not in ['witnesses','forbidden']}
                except Exception as exc:result['evaluation_error']=f'{type(exc).__name__}: {exc}'
            else:result['historical_gold']=None
            lines=['# Extracted diagnostic paths for expert review','', 'Automatically extracted, not expert-approved. Source page numbers are physical PDF pages.','']
            for i,p in enumerate(analyzer.published_paths(rev),1):
                lines.append(f"## Path {i}\n\n```json\n{json.dumps(p,ensure_ascii=False,indent=2)}\n```\n")
            (run/'diagnostic_paths_for_review.md').write_text('\n'.join(lines))
        results.append(result)
    summary={'budget_audit':budget_audit,'campaign':campaign,'manuals':results,'smoke_cost':costs.get('provider_smoke'),'gold_sha256':hashlib.sha256(golden.read_bytes()).hexdigest(),'evaluation_limit':'Historical partial/development gold and lexical matcher. No estimate of full semantic precision. Hypertherm has no gold. No direct causal comparison with v11 because code and model differ.'}
    write(OUT/'results.json',summary)
    lines=['# Risultati del pilot di estrazione','','Campagna di sviluppo sui quattro manuali già osservati. Modello: GPT-6 Luna. Nessun gold fornito al generatore. Configurazione corrente con escalation disabilitata.','','| Manuale | Stato | Tempo totale (s) | Generazione (s) | Chiamate | Costo contabilizzato USD | Nodi / relazioni | Review | Gold storico: autonomi / totale |','|---|---|---:|---:|---:|---:|---|---:|---|']
    for r in results:
        t=r.get('timing') or {};c=r.get('cost') or {};g=r.get('historical_gold') or {}
        score=f"{g['autonomous_expected_claims_present']}/{g['gold_claims_total']}" if g else 'Non disponibile'
        lines.append(f"| {r['label']} | {t.get('status','non avviato')} | {t.get('total_elapsed_seconds','')} | {t.get('generation_elapsed_seconds','')} | {c.get('calls',0)} | {c.get('charged_usd',0):.6f} | {r.get('nodes','-')} / {r.get('relations','-')} | {(r.get('review') or {}).get('total','-')} | {score} |")
    lines+=['',f"Durata campagna, incluso smoke test e avvio dei processi: {campaign['elapsed_seconds']:.3f} secondi.",f"Registro cumulativo: {json.dumps(campaign['budget'],ensure_ascii=False)}",'', 'Il cap è 15 USD complessivi. La tabella riporta il costo contabilizzato: stima sui token osservati più importo massimo prenotato per i tentativi senza consumo osservabile. Non è una fattura. results.json separa estimated_usd (parte calcolabile dai token), charged_usd (importo prudenziale complessivo) e unknown_cost_calls. Preparazione e overhead sono separati dalla generazione nei timing.json.', '', '## Interpretazione e limiti', '', 'Nodi, relazioni e validità dello schema non misurano da soli la correttezza diagnostica. I risultati sul gold storico usano il matching già adottato nella campagna precedente: sono indicatori di sviluppo da controllare manualmente. Il gold è limitato alle parti annotate; Hypertherm non ha un gold. Non attribuire un cambiamento rispetto a v11 al solo modello: anche codice e configurazione differiscono.', '', 'I grafi restano sottoposti ai gate di revisione. Le liste diagnostic_paths_for_review.md servono al controllo dei tecnici, non sono istruzioni manutentive approvate.', '', '## File', '', 'manifest.json identifica PDF e commit; runtime_profile.json congela configurazione e dipendenze; real_call_budget.jsonl contiene tutte le prenotazioni/finalizzazioni; timing.json misura le durate; generation_response.json e graph.json conservano gli output; historical_gold_evaluation.json conserva i confronti dove disponibili. results.json è il riepilogo strutturato.']
    (OUT/'REPORT.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'manuals':len(results),'status':campaign['status'],'budget':campaign['budget']}))


if __name__=='__main__':main()
