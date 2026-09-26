# Riproduzione e confini degli artifact

Usare il Python dell'ambiente documentato nei `runtime_profile.json`. `source_c11.tar.gz` contiene codice, risorse JSON/SQL, frontend, configurazione e dipendenze dichiarate delle quattro nuove estrazioni C11. `source_c12.tar.gz` congela il recupero delle continuazioni anche dalle pagine strutturali, generatore v22. `source_final_v22.tar.gz` aggiunge gli ultimi script di analisi/riproduzione; il backend coincide con C12. Estrarre gli archivi in directory nuove, mai sulla checkout corrente. `source_final.tar.gz` è lo snapshot intermedio v21; non è la versione finale.

I quattro run reali sono in `../robustness_20260925/runs/c11_full_<manual_id>/`, con profilo, tempi, database, grafo e scambi provider. C12 è in `c12r1_<manual_id>/`; i database sorgente restano quelli C11, in sola lettura. `continuation.json` registra richieste riutilizzate, nuove e bloccate; `new_provider_responses/` contiene le due nuove chiamate Hypertherm. I primi tentativi C12 falliti sono distinti e non vanno incorporati nel risultato accettato.

## Ripetere la verifica offline finale

Il runner `scripts/replay_extraction_experiment.py` confronta le richieste esatte, blocca HTTP sincrono/asincrono e usa una credenziale fittizia. Una richiesta assente non attiva una chiamata reale. Con sorgente C12 estratta in `/tmp/kg-robustness-c12`, dalla radice della repository:

```sh
.venv/bin/python scripts/replay_extraction_experiment.py \
  --run paper/experiments/robustness_20260925/runs/c11_full_hypertherm_powermax30_air \
  --code-root /tmp/kg-robustness-c12 \
  --extra-response-dir paper/experiments/robustness_continuation_20260926/c12r1_hypertherm_powermax30_air/new_provider_responses \
  --output /tmp/c12-hypertherm-replay-new
```

Sugli altri tre manuali usare il corrispondente run C11 senza `--extra-response-dir` e una directory output nuova. Questo è un replay esatto **della composizione C11+C12**, non una nuova estrazione. I replay eseguiti sono in `replay_c12_<manual_id>/`, con hash di ogni scambio letto e rete bloccata. `replay_verification.json` confronta i grafi ai risultati C12; esclude dal confronto solo gli identificatori/tempi di revisione e la telemetria/registrazione raw del replay, elencate puntualmente nell’artifact.

## Verifica senza modello e analisi

Verifica API su backup SQLite temporaneo:

```sh
.venv/bin/python scripts/verify_diagnostic_record_review.py \
  --source-run paper/experiments/robustness_20260925/runs/c7_hypertherm_powermax30_air \
  --output /tmp/review-verification-new.json
```

Probe appaiato del compilatore, senza chiamate o rigenerazione del grafo:

```sh
.venv/bin/python scripts/recompile_diagnostic_candidates.py \
  --graph paper/experiments/robustness_20260925/replays/c8r1_hypertherm_powermax30_air/graph.json \
  --source-run paper/experiments/robustness_20260925/runs/c7_hypertherm_powermax30_air \
  --output /tmp/c8-candidates-final-probe-new.json
```

Analisi in sola lettura dei risultati finali e del costo ledger:

```sh
.venv/bin/python scripts/analyze_robustness_continuation.py \
  --campaign paper/experiments/robustness_20260925 \
  --continuation paper/experiments/robustness_continuation_20260926 \
  --output /tmp/robustness-final-results-new.json
```

Suite tecnica: `.venv/bin/pytest -q`. Il test SEC loopback deve poter aprire una porta locale. Test frontend: `node --test tests/frontend/diagnostic_branches.test.cjs`.

## Nuove estrazioni e limiti dei confronti

Per nuove chiamate usare `scripts/run_extraction_experiment.py` con un nuovo run-id e codice congelato; non riutilizzare directory esistenti. Il runner legge il ledger cumulativo `paper/experiments/robustness_20260925/real_call_budget.jsonl` e il cap di 20 USD. Le tariffe verificate sono in `pricing_checked.md`; un diverso periodo o modello richiede una verifica aggiornata. Gli argomenti effettivi e la configurazione di ciascun run sono nel suo profilo. Non lanciare il runner reale per riprodurre un risultato offline.

La continuazione con rete limitata usa `scripts/continue_extraction_experiment.py`: `--run` C11, `--code-root` congelato, `--campaign` originale, `--output` nuovo; solo Hypertherm ammette `--new-pages 96,97,98,99,100 --max-new-calls 4`. Senza pagine ammesse ogni divergenza viene bloccata. Il runner r1 usato è preservato con hash in `incremental_runner_r1.py/json`. Gli usage dei cache hit non sono nuova spesa: contare esclusivamente gli eventi finalizzati del ledger.

C9→C10 sugli stessi candidati è un probe del compilatore. I pacchetti C10 low/medium sono nuove estrazioni dirette e non esercitano il recupero end-to-end. C11 comprende quattro nuove estrazioni complete; C12 è incrementale. Nessuno è un test blind. I documenti sono esposti allo sviluppo; gli audit dell'agente non sostituiscono il gold dei tecnici.

Gli avvii C10 senza risorse runtime e il run Eastman C10 con feedback contaminante sono conservati come fallimenti. Gli archivi supplementari C10 documentano le risorse non Python mancanti. `offline_tests_r1.*` conserva il test che ha rilevato la contaminazione; la suite finale verifica che il feedback non entri nelle evidenze.
