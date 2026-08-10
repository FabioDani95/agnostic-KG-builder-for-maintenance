# Piano definitivo d'implementazione

## Decisione architetturale

Implementare una pipeline PDF G3 a due estrazioni coordinate e tre proiezioni:

```text
EvidenceUnit immutabili dell'intero PDF
        │
        ├── scope diagnostic_primary ── relation-first bundles ─┐
        ├── scope structural_inventory ─ component claims ─────┤
        └── retrieval_only (intero manuale) ─ completion mirata┘
                                                                │
                                 merge + canonicalizzazione globale
                                                                │
                                  grounding claim-specific obbligatorio
                                                                │
                                     publication gate deterministico
                                      │             │            │
                                   publish         gap        exclude
                                      │
                           canonical graph + ID projections
                           ├── diagnostic
                           └── structural
```

L'estrazione relation-first riduce il rumore a monte; il gate resta l'autorità finale. Nessuna entità o relazione viene aggiunta all'ontologia. I ruoli di evidenza, la provenance, le proiezioni, i gap e la review queue sono metadata del processo/revisione.

## Contratti funzionali definitivi

### Catena diagnostica completa

Il gate deriva i percorsi dal contratto ontologico caricato a runtime. Con lo schema corrente sono completi:

1. `Symptom -MAY_INDICATE→ FailureMode -RESOLVED_BY→ CorrectiveAction`;
2. `Asset -GENERATES_ERROR→ ErrorCode -INDICATES→ FailureMode -RESOLVED_BY→ CorrectiveAction`.

`AFFECTS` è opzionale. Se presente deve essere esplicito e grounded; non si inventa un componente per completare una catena.

### Regole di pubblicazione per tipo

| Tipo | Condizione di pubblicazione nel canonico | Vista diagnostica | Vista strutturale |
|---|---|---|---|
| Asset | è esattamente l'Asset canonico del workspace ed è grounded dall'asserzione operatore | sì se esiste diagnosi | sì se esiste struttura |
| Component | ha `HAS_COMPONENT` grounded; non è un alias non canonico | solo se endpoint di `AFFECTS` pubblicato | sì |
| Symptom | partecipa ad almeno un percorso completo grounded | sì | no |
| ErrorCode | ha `GENERATES_ERROR`, `INDICATES` e raggiunge un'azione | sì | no |
| FailureMode | è raggiunta da Symptom o ErrorCode e ha almeno una `RESOLVED_BY` grounded | sì | no |
| CorrectiveAction | ha almeno una `RESOLVED_BY` grounded in ingresso | sì | no |

Un candidato incompleto non viene silenziosamente perso: riceve una disposition target-specific `gap` o `exclude`. `gap` significa che la fonte esprime una parte diagnostica rilevante ma non sostiene la catena completa; `exclude` significa che il candidato non ha semantica diagnostica nel contratto corrente, per esempio una istruzione puramente preventiva, di sicurezza o installazione.

### Definizione di CorrectiveAction

Una `CorrectiveAction` è materializzata soltanto dal range di una `RESOLVED_BY` valida. La quote della relazione deve sostenere sia la FailureMode sia l'effetto restaurativo dell'azione. Verbi come inspect/check/monitor/avoid/install/calibrate non vengono vietati lessicalmente: possono essere correttivi nel contesto giusto. In assenza di quel contesto non sono pubblicati come azioni.

### Provenance obbligatoria

Ogni relazione pubblicata deve avere almeno una reference con:

```json
{
  "evidence_id": "ev_...",
  "quote": "testo esatto non vuoto",
  "anchor": {"page": 37, "block_id": "...", "char_start": 0, "char_end": 80},
  "support_role": "direct|derived_structural"
}
```

Il nome definitivo può seguire le convenzioni Pydantic esistenti, ma i quattro concetti sono obbligatori. `support_role` è provenance operativa. Per un link strutturale deterministico, `derived_structural` significa che la quote prova direttamente l'esistenza/ownership del componente o codice; non autorizza inferenze causali. Non unire automaticamente l'evidenza degli endpoint e non propagare tutta l'evidenza incidente nei nodi.

## Sequenza d'implementazione

### Fase 0 — Feature flag, versione e guardrail

1. Aggiungere una versione di pipeline/config distinta, per esempio `pdf_relation_first_v1`, disattivata per default finché i test non passano.
2. Includere versione, policy di grounding, policy di projection e modello/escalation nel config hash.
3. Mantenere il reader backward-compatible con revisioni prive dei nuovi metadata.
4. Non migrare né riscrivere revisioni immutabili esistenti.
5. Aggiungere un budget preflight per run: target $0,30, hard stop di previsione $0,35 per la nuova configurazione. Il tetto riguarda il forecast conservativo prima di ogni chiamata opzionale.

File:

- `backend/config.py` o il modulo corrente che compone il config hash;
- `backend/domain/subgraphs.py` per la versione del payload;
- test di fingerprint/config già esistenti.

### Fase 1 — Estendere soltanto l'envelope operativo

In `backend/domain/subgraphs.py`:

1. Aggiungere `RelationEvidenceRef` o estendere `GraphEvidenceRef` senza alterare proprietà ontologiche.
2. Estendere `SourceGraphRelation` con `evidence_refs`; mantenere temporaneamente `evidence_ids` come campo derivato/backward-compatible.
3. Estendere `KnowledgeGap` con:
   - `target_kind`;
   - `target_id`;
   - `stage`;
   - `blocking`;
   - `disposition` (`gap`, `exclude`, `review`);
   - `evidence_ids`.
4. Aggiungere `GraphProjection` con `node_ids` e `relation_ids` e una mappa `projections` nell'envelope della revisione.
5. Persistire `review_queue` finalizzata con ID target, severità, reason code, candidate IDs, evidence refs e disposizione proposta.

Questi campi non entrano in `ontology_schema.JSON`, non sono copiati nelle proprietà dei nodi e non possono essere usati per aggirare dominio/range.

In `backend/storage/repositories/subgraphs.py`:

- verificare che il JSON payload immutabile persista i nuovi campi;
- lasciare invariati trigger e semantica delle decisioni;
- aggiungere test di round-trip per payload vecchio e nuovo.

### Fase 2 — Scoping multi-ruolo

In `backend/prompts/scoping_prompt.py:SECTION_SELECTION_PROMPT_TEMPLATE`:

1. sostituire l'unica decisione “seleziona” con classificazione a ruoli non esclusivi;
2. definire i ruoli con descrizioni manual-agnostic;
3. evitare istruzioni che privilegino genericamente il richiamo “component-rich” nella passata diagnostica;
4. non includere esempi, label o pagine E-554/gold.

In `backend/services/cutplan_service.py`:

- conservare `is_component_inventory_section`, ma farlo produrre `structural_inventory` anziché forzare `diagnostic_primary`;
- separare score diagnostico, strutturale e retrieval;
- derivare i ruoli da segnali testuali/layout generici;
- mantenere il fallback deterministico se lo scoping LLM fallisce.

In `backend/services/scoping_workflow.py:create_cut_plan_workflow`:

- sostituire il reintegro indiscriminato di `restored_component_pages` con assegnazione alla passata strutturale;
- mantenere `selected_pages` legacy come unione dei ruoli per compatibilità e KPI;
- indicizzare tutte le EvidenceUnit del PDF come `retrieval_only`, senza inviarle tutte al modello;
- registrare pagine/unità per ruolo nei KPI.

Definition of done: una pagina può appartenere a più ruoli; nessuna regola usa numero pagina, produttore o terminologia gold.

### Fase 3 — EvidenceUnit e chunking orientato ai claim

`backend/adapters/pdf.py` è una base valida e va preservata: EvidenceUnit immutabili, ordine di lettura, dedup native/OCR e anchor canonici non richiedono una riscrittura.

In `backend/services/ontology_workflow.py:_split_pages_by_section`:

1. introdurre `build_diagnostic_evidence_batches` che raggruppa:
   - una riga di tabella con header risolti;
   - blocchi contigui sotto lo stesso heading causale;
   - finestre contigue entro limite token;
2. non fare flush per ogni variazione della firma di sezioni sovrapposte;
3. non dividere una riga sintomo/causa/rimedio;
4. preservare sempre `evidence_id` e anchor in ogni batch;
5. introdurre batch strutturali più ampi per liste/diagrammi, separati da quelli diagnostici.

Testare determinismo e proprietà “ogni EvidenceUnit primaria compare in un solo batch dello stesso ruolo”, consentendo che una EvidenceUnit abbia ruoli diversi.

### Fase 4 — Contratto relation-first e orchestrazione Luna

In `backend/prompts/ontology_prompt.py`:

1. aggiungere un template `DIAGNOSTIC_BUNDLE_EXTRACTION_PROMPT_TEMPLATE` costruito dallo schema runtime;
2. chiedere bundle composti da indicator, FailureMode, CorrectiveAction, relazioni e relation evidence;
3. consentire bundle parziali come candidati espliciti, mai come nodi pubblicati;
4. richiedere `AFFECTS` solo se la quote nomina/sostiene il componente;
5. vietare l'invenzione di una FailureMode per promuovere una procedura;
6. precisare che sicurezza, prevenzione, ispezione e installazione non sono `CorrectiveAction` senza `RESOLVED_BY` esplicita;
7. creare un template strutturale separato per Asset/Component/`HAS_COMPONENT` e Asset/ErrorCode/`GENERATES_ERROR` quando presenti;
8. rimuovere qualsiasi obbligo di produrre tutti i tipi in ogni chunk.

In `backend/services/ontology_pipeline.py:_build_graph` e `build_initial_ontology`:

- aggiungere il path relation-first dietro feature flag;
- una chiamata Luna per batch diagnostico, più batch strutturali necessari;
- validare JSON, domain/range, endpoint e quote localmente;
- non eseguire per default il secondo pass generalizzato di relation extraction;
- non eseguire per default validation LLM e re-extraction su ogni chunk;
- inviare soltanto record falliti/ambigui alla completion/adjudication finale;
- mantenere retry automatici già previsti dal client nei KPI, ma nessun retry manuale.

Il vecchio path resta disponibile solo per confronto/rollback fino al go-live.

### Fase 5 — Merge e canonicalizzazione globale

In `backend/services/ontology_workflow.py:_merge_pipeline_results`:

1. conservare separatamente candidate bundle e claim evidence;
2. effettuare un merge provvisorio per ID locale;
3. chiamare una nuova fase globale prima di coverage/resolution completion.

Creare `backend/services/ontology_canonicalization_service.py` oppure isolare equivalente logica testabile. Algoritmo:

1. **blocking:** stesso node type e chiavi lessicali/morfologiche compatibili;
2. **safe auto-merge:** normalizzazione esatta o variante morfologica, proprietà non conflittuali, stesso material context o contesto compatibile, vicinato/evidence non contraddittori;
3. **semantic checks:** riusare `symptoms_match`, `failure_modes_match`, `corrective_actions_match` da `backend/services/ontology_semantics.py`; aggiungere matcher conservativo per Component/ErrorCode;
4. **hard non-merge:** tipi diversi, verbi/condizioni opposti, assieme-parte, generico-specifico con identità non provata, codici errore diversi;
5. **uncertain:** creare candidate review/adjudication records; un solo batch opzionale per run;
6. **rewrite:** produrre `canonical_id_map`, riscrivere gli endpoint, deduplicare relazioni identiche e unire solo evidence ref claim-specific;
7. rieseguire schema, domain/range e contradiction tests.

Non usare embedding/fuzzy threshold da solo come decisione di merge.

### Fase 6 — Completion mirata e retrieval

In `backend/services/coverage_completion_service.py` e `backend/services/resolution_completion_service.py`:

1. costruire target soltanto per:
   - Symptom con evidenza valida ma senza FailureMode;
   - ErrorCode con ownership valida ma senza FailureMode;
   - FailureMode raggiunta da Symptom/ErrorCode ma senza azione;
   - arco con quote presente ma anchor/semantica ambigua;
2. escludere FailureMode standalone non indicator-reachable dai target di resolution;
3. recuperare top EvidenceUnit dall'intero manuale usando label, contesto materiale, heading, tabelle e pagine adiacenti;
4. raggruppare target che condividono le stesse EvidenceUnit in una singola chiamata Luna;
5. imporre un massimo token/chiamate derivato dal budget preflight;
6. accettare un completamento solo se la quote restituita è substring normalizzata della EvidenceUnit e l'anchor si risolve;
7. su `not_found`, creare un gap target-specific senza retry manuale.

`build_resolution_targets` non deve più interpretare “ogni FailureMode senza azione” come un target.

### Fase 7 — Eliminare closure causale non grounded

In `backend/services/ontology_pipeline_coercion.py:_normalize_ontology_instance`:

- rimuovere l'inferenza `AFFECTS` basata sul solo semantic match con evidenza vuota;
- non materializzare `HAS_COMPONENT`/`GENERATES_ERROR` senza una claim evidence strutturale;
- mantenere normalizzazioni puramente sintattiche e schema-safe.

In `backend/services/graph_closure_service.py:close_grounded_gaps`:

- disattivare la closure `AFFECTS` per similarità/co-occorrenza;
- oppure restringere il servizio a candidate proposal che non entrano nel grafo finché non esiste una quote diretta;
- rimuovere la creazione di quote vuote.

In `backend/services/evidence_grounding_service.py:ground_relation_evidence`:

- validare tutte le relazioni, incluse `AFFECTS`, `HAS_COMPONENT` e `GENERATES_ERROR`;
- separare risolvibilità dell'ID, corrispondenza della quote, risolvibilità dell'anchor e sufficienza semantica;
- restituire metriche per relation type;
- una relazione con uno dei controlli fallito non è pubblicabile.

### Fase 8 — Adapter senza fanout e Asset canonico

In `backend/services/pdf_source_subgraph_generation.py:PdfSourceSubgraphBuilder._to_revision`:

1. preservare `evidence_refs` complete sulle relazioni;
2. eliminare il fuzzy fallback che pubblica nodi diagnostici standalone;
3. non unire automaticamente evidence degli endpoint nelle relazioni;
4. non riversare tutte le evidenze incidenti nei nodi;
5. associare a ogni nodo soltanto evidenze che provano direttamente la sua identità/proprietà;
6. usare `EvidenceRepository.ensure_asset_assertion_evidence` per l'Asset canonico del workspace;
7. continuare a verificare che nome/brand/model/type/ID dell'Asset non siano sovrascritti dal PDF;
8. emettere candidati, non pubblicazione, per endpoint non grounded.

In `backend/storage/repositories/evidence.py:ensure_asset_assertion_evidence`, aggiungere soltanto eventuali test di disponibilità/round-trip; non cambiare la semantica dell'asserzione.

### Fase 9 — Publication gate e strict validation

Creare `backend/services/diagnostic_publication_service.py` con funzioni pure:

- `classify_candidate_dispositions(...)`;
- `build_complete_diagnostic_projection(...)`;
- `build_structural_projection(...)`;
- `build_canonical_publishable_union(...)`;
- `validate_publication_invariants(...)`.

Ordine deterministico:

1. canonical asset enforcement;
2. schema/domain/range/endpoints;
3. relation evidence validation;
4. canonical ID rewrite e duplicate relation collapse;
5. ricerca dei percorsi completi;
6. disposition di nodi/relazioni incompleti;
7. costruzione proiezioni come ID set;
8. controllo zero isolati per il canonico pubblicabile;
9. metriche e gap target-specific.

Integrare il risultato in `backend/services/source_subgraph_generation.py:_strict_validation`. La strict validation finale deve bloccare la pubblicabilità se:

- Asset canonico mancante/diverso/multiplo;
- schema, proprietà, domain/range o endpoint non validi;
- nodo pubblicato isolato;
- Symptom/ErrorCode pubblicato senza percorso completo;
- FailureMode pubblicata senza indicator in ingresso o azione in uscita;
- CorrectiveAction pubblicata senza `RESOLVED_BY` in ingresso;
- relazione senza quote/anchor risolvibile;
- exact normalized duplicate residuo;
- projection ID non presente nel canonico.

I candidati incompleti correttamente trasformati in gap non devono rendere falso il 100% della **proiezione pubblicata**. I gap di grounding/schema sull'insieme pubblicabile restano bloccanti. I gap di copertura dichiarata possono essere non bloccanti ma devono restare visibili e richiedere una policy esplicita di accettazione; nessuna revisione viene auto-approvata.

### Fase 10 — Knowledge gap e review queue finali

In `backend/services/review_queue_service.py:build_review_queue`:

- spostare la chiamata dopo adapter, grounding, canonicalizzazione e gate;
- costruire un item per target/candidate group, non per ripetizione di warning intermedio;
- deduplicare per `(reason_code, target_kind, target_id, candidate_ids)`;
- distinguere `blocking`, `review`, `advisory`;
- includere quote/anchor e disposition proposta;
- non mostrare come review gli elementi già deterministicamente esclusi se non vi è ambiguità.

In `backend/services/pdf_source_subgraph_generation.py`, sostituire l'aggregazione `(code, evidence_ids)` con chiave target-specific. KPI da persistere:

- candidati per disposition;
- gap per codice e blocking state;
- queue per severità;
- relazioni grounded per tipo;
- entità per proiezione;
- canonical merge auto/adjudicated/rejected.

### Fase 11 — API

In `backend/routers/subgraphs.py` e nei relativi response model:

1. il GET workspace restituisce il grafo canonico una sola volta e la mappa delle proiezioni;
2. opzionalmente accettare `projection=diagnostic|structural|canonical` per ridurre payload, mantenendo default backward-compatible;
3. esporre relation evidence, gap target-specific e final review queue;
4. non aggiungere endpoint che mutino una revisione immutabile;
5. lasciare la decisione esplicita dell'utente separata dalla generation.

Testare che una revisione legacy continui a essere leggibile con una proiezione `canonical` sintetizzata dall'intero payload.

### Fase 12 — UI di revisione

In `frontend/app/graph.js`:

1. aggiungere selettore `Diagnostica` (default), `Strutturale`, `Canonico`;
2. filtrare usando `node_ids`/`relation_ids` della proiezione, non ricostruendo una seconda copia;
3. mostrare nella vista catene soltanto percorsi completi;
4. mostrare incompletezze in gap/review con target, quote, pagina e disposition;
5. sostituire `TIPI_TOCCATI` hard-coded con riferimenti target-specific del backend;
6. correggere il redraw affinché conservi la vista attiva e non torni sempre alla mappa;
7. applicare ricerca/filtro anche ai gap;
8. mostrare grounding distinto da semplice presenza di evidence ID.

In `frontend/app/detail.js`:

- mostrare quote e anchor per la relazione selezionata;
- distinguere evidence diretta e strutturale derivata;
- consentire navigazione all'EvidenceUnit.

In `frontend/app/i18n.js` e CSS associato:

- aggiungere label per proiezioni, disposition e stati di grounding;
- mantenere accessibilità e comportamento responsive.

La UI non deve cambiare la semantica di approvazione: continua a inviare una decisione solo su azione esplicita.

### Fase 13 — Controllo costo e telemetria

Nel client/orchestratore LLM esistente:

1. definire un ledger per run con costo effettivo e ceiling della chiamata successiva;
2. registrare modello, effort, operazione, input/cached/output token, costo e durata per chiamata;
3. nessuna chiamata concorrente nella modalità di benchmark/acceptance;
4. Luna low per scoping, Luna medium per bundle/completion;
5. Terra soltanto nel batch `ambiguity_adjudication`;
6. prima del batch Terra calcolare il costo conservativo con max input/output;
7. saltare il batch se forecast run > $0,35 e trasformare gli item in gap/review;
8. persistere risparmio/cache e conteggi per fase.

Target di progetto: caso centrale $0,226350; scenario conservativo $0,301724; hard no-go preflight sopra $0,35.

## Mappa file/funzioni

| File | Simbolo | Modifica |
|---|---|---|
| `backend/prompts/scoping_prompt.py` | `SECTION_SELECTION_PROMPT_TEMPLATE` | output multi-ruolo |
| `backend/services/cutplan_service.py` | scoring, `is_component_inventory_section`, selezione TOC | score separati per ruolo |
| `backend/services/scoping_workflow.py` | `create_cut_plan_workflow` | niente reintegro diagnostico degli inventari; KPI ruoli |
| `backend/adapters/pdf.py` | bridge EvidenceUnit | preservare; aggiungere solo test anchor/row |
| `backend/prompts/ontology_prompt.py` | nuovi template bundle/structural | relation-first, quote/anchor obbligatorie |
| `backend/services/ontology_pipeline.py` | `_build_graph`, `build_initial_ontology` | nuovo path Luna, eliminare pass generalizzati |
| `backend/services/ontology_workflow.py` | `_split_pages_by_section`, `_merge_pipeline_results`, `_finalize_run_level_quality`, `draft_ontology_workflow` | batch causali, canonicalizzazione, nuova sequenza finale |
| `backend/services/ontology_pipeline_coercion.py` | `_normalize_ontology_instance` | stop `AFFECTS`/link senza claim evidence |
| `backend/services/ontology_semantics.py` | matcher type-specific | usarli nel merge globale; matcher conservativi mancanti |
| `backend/services/ontology_canonicalization_service.py` | nuovo | candidate blocking, decisione, ID rewrite |
| `backend/services/coverage_completion_service.py` | target/completion | soltanto indicator-reachable, batch retrieval |
| `backend/services/resolution_completion_service.py` | `build_resolution_targets`, `complete_resolution_gaps` | target ridotti e raggruppati |
| `backend/services/graph_closure_service.py` | `close_grounded_gaps` | rimuovere auto-`AFFECTS` senza quote |
| `backend/services/evidence_grounding_service.py` | `ground_relation_evidence` | 100% di relation type, quattro controlli distinti |
| `backend/services/diagnostic_publication_service.py` | nuovo | gate, disposition, proiezioni, invarianti |
| `backend/services/source_subgraph_generation.py` | `_strict_validation` | integrare invarianti pubblicabili |
| `backend/services/pdf_source_subgraph_generation.py` | `PdfSourceSubgraphBuilder._to_revision` | preservare claim evidence, niente fanout/fuzzy standalone, gap target-specific |
| `backend/services/review_queue_service.py` | `build_review_queue` | dopo gate, target-specific e persistita |
| `backend/domain/subgraphs.py` | `SourceGraphRelation`, `KnowledgeGap`, `SourceSubgraphRevision` | envelope provenance/proiezioni/queue |
| `backend/storage/repositories/subgraphs.py` | round-trip payload | compatibilità e immutabilità |
| `backend/storage/repositories/evidence.py` | `ensure_asset_assertion_evidence` | usare per Asset canonico |
| `backend/routers/subgraphs.py` | GET G3 | esporre proiezioni e provenance |
| `frontend/app/graph.js` | modello, viste, `ridisegna` | default diagnostica, filtri/gap/catene corretti |
| `frontend/app/detail.js` | inspector | quote/anchor per relazione |
| `frontend/app/i18n.js`, CSS | testi/stili | nuove superfici |

## Ordine dei test durante l'implementazione

1. unit test dei nuovi domain model e backward compatibility;
2. unit test dei ruoli di scope;
3. unit test dei batch EvidenceUnit e table row;
4. contract test del prompt con client mock;
5. canonicalization unit/property tests;
6. completion/retrieval test con found/not-found;
7. grounding e publication gate sintetici;
8. repository/API round-trip;
9. UI unit/e2e su proiezioni e gap;
10. replay delle nove fixture mock;
11. replay E-554 offline sul payload/candidate fixture;
12. solo dopo il superamento offline, una run reale separata con preflight e autorizzazione, secondo `acceptance_plan.md`.

## Rollback

Il feature flag consente di tornare al path legacy senza riscrivere revisioni. Ogni nuova run crea una nuova revisione; non si modifica o sostituisce la baseline Luna. I reader tollerano l'assenza dei nuovi campi, mentre i writer del nuovo path producono sempre la nuova versione completa.

## Non-obiettivi

- non aggiungere tipi come PreventiveAction, SafetyInstruction o InstallationProcedure in questa modifica;
- non fondere componenti assieme/parte con regole lessicali;
- non rendere `AFFECTS` obbligatorio;
- non incorporare E-554, Eastman, pagine o gold nei prompt/regole;
- non approvare automaticamente revisioni;
- non avviare CSV o merge come effetto della generation/review;
- non sostituire globalmente Luna con Terra.
