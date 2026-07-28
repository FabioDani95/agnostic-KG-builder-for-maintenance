# Piano di stabilizzazione e modularizzazione — KG Builder for Maintenance

> **Documento storico — piano completato e superato.** Fotografava la
> codebase prima della stabilizzazione avviata nell'aprile 2026. I componenti
> proposti (schemi, RunStore, replay, gateway mock, harness golden, split dei
> tool, trace e rimozione del frontend legacy) sono ora presenti; diversi file
> e conteggi citati sotto non esistono più. Non usare questo documento come
> descrizione corrente o backlog. Vedi [Architecture](../ARCHITECTURE.md) e
> [Cleanup Audit](../CLEANUP_AUDIT.md).

## 1. Executive summary

La codebase è funzionalmente ricca ma strutturalmente fragile in quattro punti: **tutto lo stato vive in un dict globale in-memory** (`pdf_store` in `backend/routers/upload.py:22`) che muore a ogni riavvio; **orchestrazione, business logic e presentazione sono fuse** in tre god-file (`orchestrator.py` 1521 righe, `tools.py` 2235 righe, `chat.js` 2960 righe); **i contratti SSE/widget sono dict non tipizzati** costruiti inline e consumati da uno switch frontend senza alcuna verifica di parità; **~2300 righe di `app.js` sono codice morto** (guardato da un elemento DOM che non esiste più). Non esiste modalità mock/no-token: ogni test end-to-end del flusso reale costa token.

Il piano è incrementale, in 13 PR piccole: prima una rete di sicurezza (test di caratterizzazione + schemi Pydantic validati), poi estrazione dello stato in un `RunState` persistito su filesystem (JSONL + snapshot, niente SQLite), poi un harness `scripts/eval_golden.py` che usa le tre fixture esistenti in `tests/golden` con modalità mock ed economica, infine cleanup del legacy frontend e trace strutturato. I workflow deterministici (`scoping_workflow`, `ontology_pipeline`, `extraction_workflow`) restano building block interni non toccati nella loro logica. `./run.sh`, pytest e Playwright restano invariati.

## 2. Current architecture map

```
run.sh → scripts/dev_server.mjs → uvicorn backend.main:app (porta 8000)

backend/main.py ── monta 9 router + static frontend/
│
├─ Router "chat-first" (runtime attivo)
│   ├─ routers/upload.py        → pdf_store globale in-memory (source of truth!)
│   ├─ routers/chat.py          → /chat/start, /message, /action, /stream (SSE), /history, /download
│   │                             + logica di chaining azioni (_CHAIN_ON_SUCCESS, _run_action)
│   └─ routers/multi_agent.py   → /multi-agent/status, /audit (read-only, puliti)
│
├─ Router "step-wise" legacy (usati dal blocco morto di app.js e da alcuni test)
│   ├─ routers/cutplan.py, extract.py, ontology.py, generate.py (579 righe)
│
├─ Conversazione (backend/services/conversation/)
│   ├─ orchestrator.py (1521)   → LLM tool-calling + ~15 scorciatoie euristiche regex
│   ├─ tools.py (2235)          → dispatch + ~30 tool + costruzione payload widget inline
│   ├─ gate.py                  → gate deterministico fase→tool (buono, da preservare)
│   ├─ events.py                → event bus per-run (dict globali _queues/_locks)
│   └─ critic.py                → critiche su triplette/draft
│
├─ Stato multi-agent (backend/graph/)
│   ├─ state.py                 → GraphState TypedDict + GraphPhase (buono)
│   ├─ store.py (606)           → mutatori update_*_state + build_status/audit_payload (misto)
│   └─ supervisor.py            → routing deterministico + supervisor_log
│
├─ Workflow deterministici (building block, da mantenere)
│   ├─ services/scoping_workflow.py, ontology_pipeline.py (1963), extraction_workflow.py
│   ├─ services/ontology_export_store.py → scrive output/<slug>/{ontology,conversation,metrics}.json
│   ├─ services/run_metrics.py  → token/costo per stage (base per l'eval)
│   └─ services/review_queue_service.py, confidence.py, style_cleanup_service.py, …
│
├─ LLM: services/llm_service.py — client OpenAI istanziato inline, nessun mock
│
frontend/
├─ index.html                   → startup form + chat layout
├─ app.js (2731)                → bootstrap + ~2300 righe morte (guard "cut-plan-screen")
├─ chat.js (2960)               → SSE client, switch _renderWidget, sheet, grafo, metriche
└─ widgets/{sections,triplet,required_fields,node_card}.js

modify/                         → editor grafo standalone (template HTML 2146 righe) esposto via /modify
scripts/run_manual_benchmark.py → costruisce lo store bypassando HTTP (pattern riusabile per l'eval)
tests/golden/                   → 3 manuali .md + 3 expected .json (non ancora usati da alcun test)
```

**Tipi widget emessi dal backend** (da `tools.py`): `sections`, `ontology_review`, `triplet`, `triplet_review_start`, `required_fields`, `node_draft`, `extraction_graph`, `modify_workspace_sync`, `export`, `run_metrics` — il frontend li gestisce tutti oggi, ma la parità è garantita solo per coincidenza manuale.

## 3. Main problems (con file coinvolti)

| # | Problema | File | Impatto |
|---|----------|------|---------|
| P1 | Stato solo in-memory: `pdf_store` globale; un riavvio (o `KG_RELOAD=1`!) perde run, conversazione, decisioni umane | `backend/routers/upload.py:22`, tutti i consumer | Nessun replay/debug; demo fragili |
| P2 | Router chat non sottile: chaining di azioni, tagging client_action, emissione eventi nel router | `backend/routers/chat.py:180-233` | Logica non testabile senza HTTP |
| P3 | Accesso a stato privato del bus (`evt_bus._queues`) dal router | `backend/routers/chat.py:99,129,153` | Accoppiamento, nessuna API pubblica |
| P4 | Eventi SSE e payload widget: dict liberi, nessuno schema | `events.py`, `tools.py`, `frontend/chat.js:492` | Rotture silenziose backend→frontend |
| P5 | `orchestrator.py` mescola: routing euristico regex, chiamate LLM, gestione history, follow-up | `orchestrator.py:1323-1521` | Difficile testare/evolvere |
| P6 | `tools.py` 2235 righe: 30 tool + costruzione payload + import inline sparsi | `tools.py` | God-file |
| P7 | `graph/store.py` mescola mutazione stato e proiezioni per API (`build_status_payload`) | `graph/store.py:556-607` | Confini poco chiari |
| P8 | Nessuna modalità mock/no-token: `OpenAI(...)` istanziato inline in `llm_service.py` e `orchestrator.py` | `llm_service.py:133`, `orchestrator.py:1337` | Eval e test E2E costosi |
| P9 | ~2300 righe morte in `app.js` (guard `getElementById("cut-plan-screen")`, elemento rimosso) + fetch a endpoint legacy | `frontend/app.js:447-2731` | Rumore, manutenzione fantasma |
| P10 | Golden fixture presenti ma **mai usate**: nessun test le legge; inoltre sono `.md` mentre l'ingestion accetta solo PDF | `tests/golden/`, `upload.py:41` | Zero regression detection sulla qualità |
| P11 | Osservabilità frammentata: `phase_history`, `supervisor_log`, `run_metrics`, `conversation.tool_calls` sono 4 log paralleli non correlati e non persistiti | `graph/store.py`, `run_metrics.py` | Debug post-mortem impossibile |
| P12 | Export ontology in `tools.py::_export_ontology` (130 righe) duplica in parte la logica di `generate.py` | `tools.py:1652`, `generate.py:329` | Due percorsi di export divergenti |

## 4. Target architecture

```
backend/
├─ schemas/                      ← NUOVO: contratti Pydantic condivisi
│   ├─ chat_events.py            (ChatEvent: progress|chat_delta|widget|critique|needs_input|done|error|thinking)
│   ├─ widgets.py                (WidgetPayload: un modello per ciascuno dei 10 tipi, + WidgetType enum)
│   ├─ actions.py                (HumanAction: action, payload, client_action_id, gate_result)
│   ├─ run_state.py              (RunState: wrapping tipizzato di GraphState + conversation + metriche)
│   ├─ pipeline.py               (PipelineStep: step, agent, input_digest, output_summary, decision,
│   │                             confidence, human_handoff, artifacts, error, retry_count, tokens, cost)
│   └─ export.py                 (ExportArtifact: ontology_path, metrics_path, conversation_path, versione)
│
├─ runstore/                     ← NUOVO: persistenza run su filesystem
│   ├─ run_store.py              (RunStore: create/load/append_event/snapshot/list_runs)
│   └─ layout: data/runs/<run_id>/
│        manifest.json           (input, config_snapshot effettiva, modelli, timestamps)
│        input/manual.{pdf|md} + pages.json
│        events.jsonl            (ogni ChatEvent + HumanAction, append-only)
│        trace.jsonl             (PipelineStep, append-only)
│        state_snapshots/<phase>.json
│        export/ (artefatti finali)  metrics.json
│
├─ services/conversation/
│   ├─ orchestrator.py           (solo: costruzione messaggi, LLM loop, follow-up)
│   ├─ heuristics.py             ← estratto: intent regex, direct replies, scope guard, rerun detection
│   ├─ actions.py                ← estratto da routers/chat.py: run_action + chaining
│   ├─ tools/                    ← tools.py splittato per fase (scoping.py, ontology.py,
│   │                              extraction.py, review.py, export.py, inspect.py) + dispatch.py
│   └─ events.py                 (API pubblica: register/emit/stream; _queues privato davvero)
│
├─ services/llm_gateway.py       ← NUOVO: unico punto di creazione client LLM;
│                                  KG_LLM_MODE=real|mock (mock = risposte deterministiche da fixture)
│
├─ routers/ (adattatori sottili: parse request → chiamata servizio → response)
│
frontend/
├─ app.js                        (~400 righe: bootstrap + startup form)
├─ chat/ (split incrementale di chat.js: stream.js, render.js, sheet.js, graph.js, metrics.js)
└─ widgets/registry.js           ← NUOVO: mappa widget_type → renderer (fonte di verità testabile)

scripts/
├─ eval_golden.py                ← NUOVO: harness sui 3 golden esistenti
└─ replay_run.py                 ← NUOVO: replay/debug da data/runs/<run_id>/
```

**Decisione persistenza: filesystem, non SQLite.** Motivazioni: (a) il progetto già persiste tutto come JSON (`output/`, `benchmark_runs/`, `data/generated/`); (b) run singolo-utente MVP, nessuna concorrenza multi-processo; (c) JSONL append-only dà replay gratis e diff leggibili in git; (d) SQLite aggiungerebbe migrazione schema senza beneficio a questa scala. Un `data/runs/index.json` (o scan delle directory) basta come indice. Se in futuro servissero query cross-run, si aggiunge un indice SQLite *sopra* i file senza cambiare il formato.

## 5. Roadmap in PR piccole

Ordine pensato per: prima la rete di sicurezza, poi lo stato, poi l'eval (che sblocca tutto il resto in sicurezza), poi cleanup.

### PR1 — Test di caratterizzazione del flusso chat (rete di sicurezza)
- **Scopo**: fotografare il comportamento attuale di SSE/widget/azioni prima di qualunque refactor.
- **File**: nuovo `tests/test_chat_event_characterization.py`; nessuna modifica a codice di produzione.
- **Dettagli**: con `TestClient` FastAPI e monkeypatch delle chiamate LLM (pattern già usato in `test_chat_tools_state.py`), eseguire: load manuale → `/chat/start` → azioni `approve_cut_plan`, `run_extraction`, `approve_triplet`, `export_ontology` e catturare la sequenza di eventi SSE. Asserire per ogni evento: `type` ∈ insieme noto, chiavi top-level presenti, `widget` ∈ i 10 tipi noti.
- **Test**: il file stesso; `python3 -m pytest tests/test_chat_event_characterization.py`.
- **Criterio completamento**: test verdi che coprono tutti gli 8 tipi evento e ≥8 dei 10 tipi widget.
- **Rischio**: basso (solo test).
- **Delegabile**: **sì**.

### PR2 — Schemi Pydantic per ChatEvent, WidgetPayload, HumanAction
- **Scopo**: dare un tipo a ogni payload che attraversa il confine backend↔frontend.
- **File**: nuovi `backend/schemas/__init__.py`, `chat_events.py`, `widgets.py`, `actions.py`. Nessun call-site cambiato.
- **Dettagli**: modellare esattamente ciò che il codice emette *oggi* (usare la PR1 come specifica). `WidgetType` come `StrEnum` con i 10 valori. Discriminated union su `type` per gli eventi e su `widget` per i payload. Campi extra tollerati (`model_config = ConfigDict(extra="allow")`) in questa fase per non rompere nulla.
- **Test**: nuovo `tests/test_schemas_contract.py`: valida contro gli schemi le fixture di eventi catturate in PR1.
- **Criterio completamento**: ogni evento emesso nei test di caratterizzazione valida senza errori.
- **Rischio**: basso.
- **Delegabile**: **sì**.

### PR3 — Event bus con API pubblica + router chat sottile
- **Scopo**: `routers/chat.py` diventa adattatore puro; il chaining va in un servizio.
- **File**: `backend/services/conversation/events.py` (aggiungere `is_registered`/`ensure_registered`); nuovo `backend/services/conversation/actions.py` (sposta `_CHAIN_ON_SUCCESS`, `_CHAIN_PREAMBLE`, `_run_action`, `_tag_client_action` da chat.py); `backend/routers/chat.py` si riduce a validazione request + delega.
- **Dettagli**: `actions.run_action(pdf_id, store, action: HumanAction, on_event) -> ActionOutcome`; il gate check resta dentro il servizio, non nel router. Emissione widget passa da `WidgetPayload` (validazione attiva, `extra="allow"`).
- **Test**: PR1 resta verde; nuovo `tests/test_chat_actions_service.py` che testa il chaining (`approve_cut_plan` → `draft_ontology`) senza HTTP.
- **Criterio completamento**: `routers/chat.py` < 120 righe, zero accessi a `evt_bus._queues`, Playwright `chat_bootstrap.spec.js` verde.
- **Rischio**: medio (tocca il percorso caldo delle azioni).
- **Delegabile**: sì con supervisione (la PR1 fa da guardia).

### PR4 — RunState e separazione mutatori/proiezioni
- **Scopo**: un modulo che possiede lo stato del run, distinto dalle proiezioni per API.
- **File**: nuovo `backend/schemas/run_state.py`; nuovo `backend/graph/projections.py` (sposta `build_status_payload`, `build_audit_payload`, `_coverage_summary`, `_grounding_summary`, ecc. da `store.py`); `backend/graph/store.py` resta solo con i mutatori `update_*_state`/`_record_phase`; `backend/routers/multi_agent.py` importa da `projections`.
- **Dettagli**: `RunState` Pydantic che convalida `GraphState` (i TypedDict restano il formato runtime; RunState serve per persistenza e API). Nessun cambiamento di comportamento.
- **Test**: `test_multi_agent_state.py` e `test_multi_agent_mode_flow.py` verdi; nuovo test che `RunState.model_validate(graph_state)` passa dopo ogni fase del flusso mock.
- **Criterio completamento**: `graph/store.py` < 450 righe, proiezioni importate solo dai router.
- **Rischio**: basso-medio.
- **Delegabile**: **sì**.

### PR5 — RunStore: persistenza su filesystem
- **Scopo**: ogni run scrive manifest, input, eventi, decisioni umane, snapshot di fase, export e metriche in `data/runs/<run_id>/`.
- **File**: nuovi `backend/runstore/__init__.py`, `run_store.py`; hook in `upload.py::load_manual` (manifest + input), `conversation/events.py` (tee di ogni evento su `events.jsonl`), `conversation/actions.py` (HumanAction su `events.jsonl`), `graph/store.py::persist_graph_state` (snapshot per fase, debounced per fase e non per ogni mutazione), `_export_ontology` (copia artefatti in `export/`).
- **Dettagli**: scrittura sincrona append (file piccoli, run singolo); `KG_RUNS_DIR` per redirigere nei test (stesso pattern di `KG_OUTPUT_DIR` in `ontology_export_store.py:20`). Il manifest include `config_snapshot` effettiva (già costruita da `_build_config_snapshot`) e modelli selezionati. Il RunStore è un *observer*: `pdf_store` resta la source of truth runtime (la migrazione completa non è in scope).
- **Test**: nuovo `tests/test_run_store.py` (flusso mock → layout directory, eventi in ordine, snapshot per fase); Playwright verde con `KG_RUNS_DIR=runs_e2e` in `playwright.config.js`.
- **Criterio completamento**: dopo un run mock completo la directory contiene manifest, ≥1 snapshot per fase attraversata, events.jsonl con tutti gli eventi SSE e le azioni umane, export e metrics.
- **Rischio**: medio (I/O nel percorso caldo; mitigato dal tee best-effort con try/except come già fa `make_on_event`).
- **Delegabile**: sì con supervisione.

### PR6 — Replay/debug: `scripts/replay_run.py`
- **Scopo**: ricostruire e ispezionare un run persistito.
- **File**: nuovo `scripts/replay_run.py`.
- **Dettagli**: modalità: `--summary` (timeline fasi, decisioni, costi da metrics), `--events` (ri-stampa events.jsonl filtrabile per tipo), `--state <phase>` (dump snapshot), `--diff <run_id2>` (diff strutturale tra due run: conteggi nodi/triplette per fase). Solo lettura, zero LLM.
- **Test**: `tests/test_replay_run.py` su una directory run fixture generata dal test di PR5.
- **Criterio completamento**: replay di un run reale registrato manualmente funziona end-to-end.
- **Rischio**: basso.
- **Delegabile**: **sì**.

### PR7 — LLM gateway con modalità mock/no-token
- **Scopo**: un unico punto di creazione client LLM; `KG_LLM_MODE=mock` per run a costo zero.
- **File**: nuovo `backend/services/llm_gateway.py`; modifiche puntuali in `llm_service.py` (`call_openai_scoping`, `call_openai`), `conversation/orchestrator.py` (AsyncOpenAI), `style_cleanup_service.py`, `ontology_pipeline.py` e altri call-site (`grep -rn "OpenAI(" backend/`).
- **Dettagli**: `get_client()` / `get_async_client()` che rispettano `KG_LLM_MODE`. Il mock è **fixture-driven**: risponde con contenuti deterministici da `tests/golden/mock_responses/<fixture_id>/<stage>.json` (file di *risposte mock*, non nuovi golden manual — i manuali restano i 3 esistenti). Per l'extraction il mock restituisce la tabella markdown che `parse_extraction` già sa parsare. Fallback: se non c'è fixture, risposta vuota valida + warning.
- **Test**: nuovo `tests/test_llm_gateway.py`; test che esegue scoping+extraction su `clean_pump_manual` in mock e produce un'ontologia non vuota.
- **Criterio completamento**: `KG_LLM_MODE=mock python3 -m pytest tests/test_llm_gateway.py` passa senza `OPENAI_API_KEY`.
- **Rischio**: medio (tocca i call-site LLM; mitigato: default `real`, comportamento identico).
- **Delegabile**: sì con supervisione (l'elenco call-site va verificato).

### PR8 — Fixture loader: manuali markdown → store
- **Scopo**: permettere ai golden `.md` di entrare nella pipeline (che oggi accetta solo PDF).
- **File**: nuovo `backend/services/manual_loader.py` (o `scripts/_golden_common.py`): `build_store_from_markdown(path) -> store` che replica `_build_store` di `run_manual_benchmark.py:63` ma splitta il markdown in "pagine" (i golden dichiarano `Evidence page: N`, quindi mappa sezione→pagina dichiarata nel loader).
- **Dettagli**: il loader produce `store["pages"]` nello stesso formato di `extract_text_by_page`, `ensure_run_metrics`, `seed_graph_state`. Nessun endpoint HTTP nuovo.
- **Test**: `tests/test_manual_loader.py`: i 3 golden si caricano, page_count coerente con `expected_scoping.must_keep_pages`.
- **Criterio completamento**: i 3 golden producono store validi consumabili da `scoping_workflow`.
- **Rischio**: basso.
- **Delegabile**: **sì**.

### PR9 — `scripts/eval_golden.py`: harness di valutazione
- **Scopo**: comando unico che esegue la pipeline sui 3 golden e confronta con `tests/golden/expected/*.json`.
- **File**: nuovo `scripts/eval_golden.py`; output in `eval_runs/<timestamp>/report.json` + `report.md`.
- **Dettagli**:
  - CLI: `python3 scripts/eval_golden.py [--fixtures clean_pump_manual,…] [--mode mock|economy|full] [--baseline eval_runs/<ts>] [--fail-on-regression]`.
  - `--mode mock`: `KG_LLM_MODE=mock`, zero token (default). `--mode economy`: modelli nano da config, solo scoping+ontology+extraction. `--mode full`: config reale.
  - Esegue per ogni fixture: loader (PR8) → `scoping_workflow` → `ontology_pipeline`/draft → extraction → export via gli stessi servizi del runtime (non via HTTP), come già fa `run_manual_benchmark.py`.
  - **Metriche per fixture**:
    - *schema compliance*: `is_schema_compliant` + conteggio `schema_issues` per severità;
    - *campi mancanti*: `human_required_fields` count + lista;
    - *coverage triplette*: matching fuzzy-normalizzato (lowercase, strip, numeri/unità preservati — come da README golden) delle `expected_triplets` su symptom/failure_mode/corrective_action → `matched/expected`;
    - *approximate precision/recall*: recall = expected matchate / expected; precision = triplette estratte che matchano ≥1 expected o superano i check strutturali / totale estratte (dichiarata "approximate" nel report);
    - *interventi umani*: `expected_human_review.required` vs review queue reale (`review_queue_service`) + `human_required_fields` → boolean match + conteggi;
    - *export checks*: `min_symptoms/min_failure_modes/min_corrective_actions/required_relations` contro l'ontologia esportata;
    - *costo stimato / durata*: da `run_metrics` (`estimated_cost_usd`, `duration_seconds` per stage);
    - *diff baseline*: confronto col report `--baseline` (o l'ultimo in `eval_runs/`): delta per metrica, exit code ≠ 0 con `--fail-on-regression` se recall o compliance peggiorano.
- **Test**: `tests/test_eval_golden.py` esegue l'harness in mock sui 3 golden e verifica che il report abbia tutte le sezioni.
- **Criterio completamento**: `python3 scripts/eval_golden.py` (mock) gira in < 60 s senza API key e produce report leggibile; `--mode economy` gira con API key e riporta costi reali.
- **Rischio**: medio (il matching approssimato va tarato; mitigazione: soglie permissive iniziali, riportare sempre i non-match).
- **Delegabile**: la struttura sì; la taratura del matching meglio con modello forte.

### PR10 — Contract test frontend/backend
- **Scopo**: garantire che ogni payload emesso dal backend sia renderizzabile dal frontend.
- **File**: nuovo `frontend/widgets/registry.js` (mappa `widget_type → renderer`, usata da `_renderWidget`); nuovo `tests/test_widget_contract.py`; nuovo `tests/widget_render.spec.js` (Playwright).
- **Dettagli**:
  - Backend: test che `WidgetType` enum (PR2) ⊆ chiavi di `registry.js`.
  - Payload fixtures: per ogni tipo widget, un payload d'esempio catturato dai test di caratterizzazione, validato dallo schema Pydantic e salvato in `tests/fixtures/widgets/*.json`.
  - Playwright: pagina che importa `registry.js` e renderizza ogni fixture → nessuna eccezione, elemento non vuoto.
  - Contract test dedicati per: chat events (8 tipi), widget payload (10 tipi), human actions (gate: azione permessa/bloccata per fase con `gate.check`), ontology review (`ontology_review` ↔ `renderOntologyReviewWidget`), triplet review (`triplet` + `triplet_review_start`), export-ready (payload `export` + condizioni di rifiuto di `_export_ontology`: schema issues critici, required fields).
- **Test**: i file stessi; corrono in pytest e `npx playwright test`.
- **Criterio completamento**: aggiungere un widget type nel backend senza registrarlo nel frontend fa fallire un test.
- **Rischio**: basso.
- **Delegabile**: **sì**.

### PR11 — Cleanup frontend legacy (incrementale)
- **Scopo**: rimuovere codice morto, non riscrivere.
- **File**: `frontend/app.js`, `frontend/chat.js`, `frontend/index.html`.
- **Dettagli**, in 3 step separati (uno per PR se si vuole massima prudenza):
  1. Eliminare il blocco `if (document.getElementById("cut-plan-screen")) { … }` (`app.js:447-2731`): morto perché l'elemento non esiste più in `index.html`. Con esso spariscono le fetch legacy a `/extract-tables`, `/ontology/draft`, `/ontology/review`, `/ontology/apply-suggestions`, `/cut-plan/approve`, `/generate-json`. `app.js` scende a ~400 righe.
  2. Rimuovere da `index.html` eventuali nodi orfani riferiti solo dal blocco eliminato.
  3. Split di `chat.js` in moduli (`chat/stream.js`, `chat/widgets.js` con il registry di PR10, `chat/sheet.js`, `chat/graph.js`, `chat/metrics.js`) — spostamenti puri, nessun cambio di logica, uno-due moduli per PR.
- **Test**: Playwright esistenti (`chat_bootstrap`, `frontend_flow`, `chat_ui_polish`) + `widget_render.spec.js` di PR10 verdi dopo ogni step.
- **Criterio completamento**: nessuna funzione definita ma mai chiamata in app.js; chat.js < 800 righe per modulo.
- **Rischio**: basso per step 1 (guard verificabile), medio per step 3.
- **Delegabile**: step 1-2 **sì**; step 3 sì con supervisione.

### PR12 — Trace strutturato multi-agent
- **Scopo**: un unico trace per run che correla step, decisioni, confidence, handoff umani, artefatti, errori/retry.
- **File**: nuovo `backend/schemas/pipeline.py` (`PipelineStep`, vedi §4); nuovo `backend/observability/trace.py` (`TraceRecorder.record(step)` → `trace.jsonl` nel RunStore); hook nei punti che oggi scrivono `phase_history` (`store.py:101`), `supervisor_log` (`supervisor.py`), `record_stage_metrics`, review queue e azioni umane (PR3), retry del reflective loop.
- **Dettagli**: input/output sintetici = digest (hash + conteggi + primi N item), mai testo integrale del manuale; `confidence` dai verdetti/grounding dove disponibile; `human_handoff=true` quando il gate/review queue richiede intervento. `build_audit_payload` viene rialimentato dal trace persistito così `/multi-agent/audit` funziona anche dopo restart (lookup su `data/runs/` quando il run non è in memoria).
- **Test**: nuovo `tests/test_trace_recorder.py`: run mock → trace con uno step per fase, tokens/costo coerenti con `run_metrics`; audit endpoint risponde per un run non in memoria.
- **Criterio completamento**: `scripts/replay_run.py --summary` mostra la timeline completa da `trace.jsonl`; l'eval harness (PR9) allega il trace al report.
- **Rischio**: medio.
- **Delegabile**: parzialmente (schema e recorder sì; i punti di hook richiedono giudizio).

### PR13 — Deprecazione soft dei router step-wise (opzionale, ultima)
- **Scopo**: ridurre superficie API senza rompere i test.
- **File**: `backend/routers/{cutplan,extract,ontology}.py`, `backend/main.py`.
- **Dettagli**: dopo PR11 nessun frontend li chiama. Marcare deprecated nelle docstring, spostare i test che li usano (`test_multi_agent_mode_flow.py`, `test_generate_export_route.py`) sui servizi sottostanti, poi montarli solo se `KG_ENABLE_LEGACY_ROUTES=1`. **Non** rimuovere `generate.py` finché la logica condivisa con l'export chat non è unificata (P12) — unificazione da valutare dopo l'eval harness, che la protegge.
- **Test**: suite completa verde con e senza il flag.
- **Criterio completamento**: default senza route legacy; Playwright verde.
- **Rischio**: medio (dipendenze nascoste); per questo è ultima e flaggata.
- **Delegabile**: sì con supervisione.

## 6. Prime 3 task pronte per un modello meno forte

1. **PR1 — Test di caratterizzazione** *(solo aggiunta di test)*: "Scrivi `tests/test_chat_event_characterization.py` usando `fastapi.testclient` e i pattern di monkeypatch LLM già presenti in `tests/test_chat_tools_state.py`. Cattura e asserisci la sequenza eventi SSE per il flusso load→start→approve_cut_plan→run_extraction→approve_triplet→export. Non modificare codice di produzione."
2. **PR2 — Schemi Pydantic** *(codice nuovo isolato)*: "Crea `backend/schemas/{chat_events,widgets,actions}.py` modellando esattamente i dict emessi da `backend/services/conversation/events.py` e i 10 tipi widget emessi in `tools.py` (grep `\"widget\":`). `extra='allow'`. Aggiungi `tests/test_schemas_contract.py`. Non cambiare alcun call-site."
3. **PR11 step 1 — Rimozione blocco morto in app.js** *(delete verificabile)*: "In `frontend/app.js` elimina il blocco guardato da `if (document.getElementById(\"cut-plan-screen\"))` (righe ~447–2731; l'elemento non esiste in `index.html`). Verifica con `npx playwright test tests/chat_bootstrap.spec.js tests/frontend_flow.spec.js` e che `grep cut-plan-screen frontend/` non trovi nulla."

(PR6 e PR8 sono i candidati successivi in ordine di delegabilità.)

## 7. Test strategy

- **Piramide**: unit (servizi e schemi, pytest, mock LLM via monkeypatch → poi via `KG_LLM_MODE=mock`), contract (schemi Pydantic + parità registry widget + fixture payload), integrazione (flusso chat completo in-process con LLM mock, RunStore su dir temporanea), E2E (Playwright esistenti + `widget_render.spec.js`), qualità (eval_golden in mock come gate CI, in economy on-demand).
- **Regola per ogni PR di refactor**: i test di caratterizzazione (PR1) e i Playwright esistenti devono restare verdi *senza modifiche*; se un test va cambiato, il contratto è cambiato e va giustificato nel PR.
- **Golden**: usati solo da `eval_golden.py` e dai test del loader; matching su chiavi semantiche normalizzate, mai su testo esatto (come da `tests/golden/README.md`). Nessun nuovo manuale.
- **Isolamento ambiente**: `KG_OUTPUT_DIR` (già esistente), più i nuovi `KG_RUNS_DIR` e `KG_LLM_MODE`, tutti impostati in `playwright.config.js` e nelle fixture pytest, così nessun test sporca `output/` o `data/runs/` reali.
- **CI suggerita**: `python3 -m pytest` + `npx playwright test` + `KG_LLM_MODE=mock python3 scripts/eval_golden.py --fail-on-regression`.

## 8. Non-goals

- **Nessun runtime `classic`**: i router step-wise restano solo come superficie deprecata dietro flag (PR13); i workflow deterministici restano building block interni chiamati dai tool.
- **Niente database** (SQLite/Postgres), niente code, niente websocket al posto di SSE.
- **Nessuna riscrittura frontend** (framework, bundler, TypeScript): solo rimozione di codice morto e split in moduli ES nativi.
- **Nessun nuovo golden manual** né modifica agli expected esistenti; le uniche fixture nuove sono *risposte mock* e *payload widget*, che non sono golden manual.
- **Nessun cambiamento alla qualità di estrazione** (i bug noti da `extraction_quality_audit` sono un filone separato — l'eval harness di PR9 è il prerequisito che lo renderà misurabile).
- **Nessuna migrazione di `pdf_store`** a source of truth persistita in questa fase: il RunStore è observer; l'inversione (reload di un run da disco) è un'estensione naturale post-PR6 ma fuori scope.
- `./run.sh`, `scripts/dev_server.mjs`, compatibilità pytest/Playwright: invariati.
