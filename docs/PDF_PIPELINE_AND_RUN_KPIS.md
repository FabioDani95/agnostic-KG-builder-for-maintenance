# Pipeline PDF G3 e KPI di esecuzione

Data: `2026-08-09`

## Scopo

Questo documento descrive il percorso PDF source-scoped usato da G3, le
correzioni introdotte dopo l'analisi del manuale E-554 e il contratto dei KPI
mostrati dopo la generazione. L'implementazione è stata verificata senza
effettuare nuove chiamate API reali e senza rigenerare E-554.

L'analisi forense della precedente esecuzione è conservata in
`artifacts/acceptance/g3/e554/pdf_pipeline_root_cause.md`; la ricostruzione dei
costi storici, necessariamente stimata perché la revisione precedente non
persistiva il ledger, è in
`artifacts/acceptance/g3/e554/pdf_pipeline_cost_reconstruction.json`.

## Flusso corrente

```text
PDF originale
  -> inventario G1 RawUnit/EvidenceUnit immutabile
  -> renderer semantico ordinato e con EVIDENCE_ID
  -> Asset canonico del workspace (contesto, non target di estrazione)
  -> scoping (regole/ToC/LLM; keyword solo fallback)
  -> partizione univoca delle pagine in chunk
  -> estrazione e finalizzazione ontologica
  -> risoluzione provenance anchor-first, quote fallback
  -> validazione strict
  -> SourceSubgraphRevision + generation_metrics immutabili
  -> revisione UI
```

### Ordine e contenuto della pagina

Gli `evidence_id` sono hash opachi e non codificano la posizione. Il renderer
`evidence_units_to_legacy_pages` ordina quindi ogni pagina usando il locator:

1. `block_index` per i blocchi nativi;
2. `table_index` + `row_index` per le righe tabellari;
3. `ocr_region_index` per le regioni OCR.

Le righe tabellari già contenute nel testo principale non vengono ripetute. Se
un OCR regionale è più completo del testo a blocchi viene usato come lettura
principale. Ogni unità resa porta il marker stabile
`[[EVIDENCE_ID: ev_...]]`.

### Scoping e chunking

- Se ToC, regole o selezione LLM producono sezioni affidabili, lo scan keyword
  non viene unito al cut plan.
- Lo scan keyword viene eseguito soltanto come fallback quando non esiste una
  selezione affidabile.
- Sezioni sovrapposte sono contesto many-to-many della pagina, non copie della
  pagina. Ogni pagina fisica entra in un solo chunk.
- I limiti `max_pages_per_chunk` e `max_input_chars` restano applicati; una
  pagina più grande del limite forma da sola un chunk.

### Identità e provenance

- Nel percorso workspace/G3 l'Asset è quello dichiarato e confermato
  dall'operatore prima del caricamento delle fonti. Il PDF non può ridefinirlo.
- Lo scoping G3 usa `discover_asset_identity=false`: sui documenti piccoli non
  esegue la chiamata di product identification; con una ToC estrae soltanto
  `document_type`, lingua e indice, senza richiedere prodotto, marca o modello.
- Il modello ontologico estrae soltanto i cinque tipi source-derived:
  Component, Symptom, FailureMode, CorrectiveAction ed ErrorCode. Un unico nodo
  Asset viene iniettato deterministicamente da `workspace.asset`; eventuali
  Asset restituiti impropriamente dal modello vengono scartati.
- `HAS_COMPONENT` e `GENERATES_ERROR` sono relazioni strutturali derivate dal
  sistema e non vengono richieste all'LLM.
- Il comportamento precedente di product discovery resta disponibile soltanto
  ai caller legacy/standalone, per i quali `discover_asset_identity` rimane
  `true` di default.
- Un `asset_id` esplicito è preservato byte-per-byte. La normalizzazione viene
  applicata solo quando l'ID deve essere derivato da un nome nel percorso
  legacy.
- Ogni relazione può restituire `source_anchor`, copiato dal marker
  `EVIDENCE_ID`. Il bridge verifica che la citazione appartenga all'unità
  indicata, poi usa pagina/citazione come compatibilità per output precedenti.
- Un nodo standalone viene associato alle evidenze tramite label, codice,
  descrizione o istruzione; la sola presenza sulla stessa pagina non è più
  sufficiente.
- Il validatore richiede esattamente un Asset e un `HAS_COMPONENT` dal suo ID
  a ogni Component, oltre ai controlli già presenti su schema, endpoint,
  domain/range e provenance.

## Routing dei modelli

Il bridge G3 usa i modelli per ruolo dichiarati in `config.yaml`:

- `agents.scoping.model` e `reasoning_effort` per il cut plan;
- `agents.ontology_draft.model` e `reasoning_effort` per estrazione,
  relation pass, validazione semantica, coverage e resolution completion.

`KG_GENERATION_MODEL`/`MODEL_NAME` resta un fallback, non sovrascrive un modello
di ruolo esplicito. Il routing effettivo entra in `input_config_hash`, quindi
un cambio di modello o reasoning effort invalida correttamente la cache
semantica.

### Profilo economico per il rerun E-554

Il profilo di accettazione corrente usa:

| Fase | Modello | Reasoning | Motivo |
|---|---|---|---|
| scoping | `gpt-5.6-luna` | `low` | compito strutturato e verificabile deterministicamente |
| ontology + finalizzazione | `gpt-5.6-luna` | `medium` | preserva più capacità nel punto in cui si misura la qualità semantica |

Ai prezzi di listino registrati nel catalogo locale, Luna costa `$0.20/M`
token input e `$1.20/M` token output, contro `$2/M` e `$12/M` di Terra. A
parità di token la vecchia stima E-554 di `$3.19–$6.42` diventerebbe quindi
circa `$0.32–$0.64`; le correzioni a scoping e chunking dovrebbero ridurre
ulteriormente il lavoro, ma questo resta da misurare nella singola run reale.

Il profilo non disabilita coverage o resolution completion e non impone un cap
artificiale alle lacune: risparmiare eliminando fasi cambierebbe il test di
qualità. La regola operativa è invece **una sola run**, senza rilancio a fronte
di errori o risultato insoddisfacente senza una nuova autorizzazione.

Per una run reale è necessaria `OPENAI_API_KEY` in `.env`. Per test e sviluppo
offline usare esplicitamente:

```bash
KG_LLM_MODE=mock OPENAI_API_KEY='' .venv/bin/python -m pytest
```

## Contratto dei KPI

Ogni nuova revisione PDF persiste `generation_metrics` dentro il proprio
`payload_json`. Le metriche rimangono quindi disponibili dopo riavvio e sono
coerenti con la revisione visualizzata.

Campi principali:

| Campo | Significato |
|---|---|
| `duration_seconds` | tempo wall-clock della generazione G3 |
| `llm_calls` | chiamate LLM completate e contabilizzate |
| `prompt_tokens` | token input riportati dalle risposte API |
| `cached_prompt_tokens` | quota input servita da cache |
| `non_cached_prompt_tokens` | `prompt - cached_prompt` |
| `completion_tokens` | token output riportati dalle risposte API |
| `total_tokens` | totale provider |
| `estimated_cost_usd` | stima a prezzi di listino configurati |
| `by_model` | stessi contatori aggregati per modello tariffario |
| `stages` | dettaglio per scoping e ontology, inclusi chunk e retry |
| `execution_mode` | `real`, `mock` o altra modalità gateway |

Nei dettagli di ciascuno stage viene persistito anche il
`reasoning_effort` effettivamente richiesto (`low`, `medium` oppure `default`).

Formula applicata per ciascuna chiamata:

```text
cost = non_cached_input / 1M * input_rate
     + cached_input     / 1M * cached_input_rate
     + output           / 1M * output_rate
```

Il costo è una stima, non un dato di fatturazione: usa il modello restituito
dall'API e il catalogo in `backend/services/run_metrics.py`. La UI lo etichetta
come “Costo stimato” e mostra anche durata, token, chiamate, modelli e numero di
chunk. Le revisioni create prima di questo contratto hanno
`generation_metrics = null`: il costo storico non viene inventato.

## Verifica senza API reali

Le regressioni coprono:

- ordine dei blocchi e anchor nel renderer;
- unicità delle pagine con sezioni sovrapposte;
- esclusione delle keyword quando esiste un cut plan affidabile;
- conservazione dell'Asset ID opaco;
- assenza di product discovery in G3, sia sui documenti piccoli sia nel prompt
  ToC, mantenendo invariata l'identità del workspace;
- scarto deterministico di Asset inventati o duplicati nell'output LLM;
- derivazione di `HAS_COMPONENT` e `GENERATES_ERROR` senza affidarsi al modello;
- risoluzione anchor-first e fail-closed delle citazioni non risolte;
- persistenza round-trip dei KPI;
- invarianti Asset/Component del validatore;
- rendering responsive della card KPI.

Una futura campagna qualitativa reale deve essere una decisione esplicita del
Product Owner. Solo allora si potranno confrontare qualità, costo e tempo del
nuovo output con la baseline E-554; questa modifica non dichiara quel confronto
già superato.
