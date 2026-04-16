# Paper TODO and Phased Plan

Documento operativo per chiudere il paper, con focus sulle attivita` automatizzabili con script e sulle decisioni da congelare prima dei run.

## 1. Checklist complessiva per il paper

### 1.1 Dataset sperimentale

- [ ] Definire il campione finale di manuali per lingua: `DE`, `IT`, `EN`
- [ ] Definire gli `equipment types` inclusi nel dataset
- [ ] Fissare il formato canonico di annotazione gold standard
- [ ] Far annotare i manuali da 2 esperti di dominio
- [ ] Calcolare inter-annotator agreement
- [ ] Raccogliere statistiche per lingua:
  - [ ] numero manuali
  - [ ] pagine totali
  - [ ] entita` annotate
  - [ ] relazioni annotate

Classificazione:
- Manuale: scelta campione, annotazione esperti
- Scriptabile: statistiche dataset, export aggregati, agreement
- Misto: import/adjudication del gold standard

### 1.2 Baseline runs

- [ ] Run LLM generico zero-shot con solo schema + testo
- [ ] Run stesso LLM in few-shot con `N` esempi annotati in-context
- [ ] Run MaintKG con `max_retries=0`
- [ ] Run MaintKG senza advisory agents
- [ ] Run MaintKG completo

Classificazione:
- Scriptabile: orchestration dei run, salvataggio output, aggregazione metriche
- Misto: definizione prompt baseline e scelta esempi few-shot

### 1.3 Ablation study

- [ ] Reflective loop con `max_retries = 0, 1, 2`
- [ ] Conteggio issue corretti per iterazione
- [ ] Disabilitare ciascun advisory agent singolarmente
- [ ] Sweep di `theta_high` e `theta_low`
- [ ] Registrare:
  - [ ] auto-approve rate
  - [ ] human review rate
  - [ ] qualita` finale

Classificazione:
- Quasi tutta scriptabile, se ogni run salva config, confidence e outcome in formato strutturato

### 1.4 Metriche

- [ ] Precision / Recall / F1 per `entity type`
- [ ] Precision / Recall / F1 per `relation type`
- [ ] Metriche per lingua
- [ ] Metriche overall
- [ ] Triplet-level F1 su catene diagnostiche complete
- [ ] Reliability diagram
- [ ] HITL efficiency:
  - [ ] percentuale auto-approved
  - [ ] percentuale human-reviewed
  - [ ] tempo medio review per manuale
  - [ ] tempo vs estrazione manuale completa

Classificazione:
- Scriptabile: quasi tutto
- Misto: il confronto con estrazione manuale completa richiede una baseline umana misurata bene

### 1.5 Materiale da verificare nell'applicativo

- [ ] Documentare almeno 1-2 esempi di schema extensibility
- [ ] Generare e includere il diagramma LangGraph (Fig. 2)
- [ ] Verificare `fig_architecture.tex` / figura architetturale (Fig. 1)
- [ ] Estrarre distribuzione dei confidence scores da sample run reale

Classificazione:
- Scriptabile: generazione figure da dati e verifiche file-based
- Misto: selezione esempi da mostrare nel paper

### 1.6 Dettagli implementativi da documentare

- [ ] Mappare quale LLM e` usato per quale agent
- [ ] Congelare chunk size, overlap, max retries, soglie confidence
- [ ] Calcolare tempo medio di processing per manuale
- [ ] Calcolare statistiche di consumo token

Classificazione:
- Scriptabile: tempi, token, aggregati
- Misto: tabella finale e testo paper

### 1.7 Feedback qualitativo

- [ ] Raccogliere commenti degli esperti di dominio su:
  - [ ] audit trail
  - [ ] spiegazioni confidence
  - [ ] usabilita`

Classificazione:
- Manuale: raccolta feedback
- Scriptabile: solo aggregazione/sintesi strutturata se il feedback viene raccolto in un form

## 2. Cosa va definito prima dei run

Questa sezione e` il prerequisito critico. Se non viene congelata prima, i risultati non saranno difendibili nel paper.

### 2.1 Evaluation contract

Da fissare prima di implementare o lanciare benchmark:

- Unita` di valutazione:
  - entity span
  - relation edge
  - diagnostic chain / triplet completo
- Formato canonico unico per:
  - gold standard
  - predizioni baseline
  - predizioni MaintKG
  - log HITL
- Convenzioni ID:
  - `document_id`
  - `language`
  - `equipment_type`
  - `page`
  - `chunk_id`
  - `node_id`
  - `relation_id`

### 2.2 Matching rules

Da esplicitare nel paper e codificare negli script:

- Entity match:
  - span esatto + type
  - oppure overlap + type
  - oppure canonical mention + type
- Relation match:
  - stesso subject
  - stesso predicate
  - stesso object
  - regola di matching su span o su ID canonicali
- Chain / triplet match:
  - exact match dell'intera catena
  - oppure match parziale con scoring decomponibile
- Policy di deduplicazione:
  - come trattare entita` duplicate tra chunk
  - come trattare relazioni duplicate multi-pagina

### 2.3 Metriche ufficiali da congelare

- `micro` e `macro` P/R/F1
- P/R/F1 per `entity type`
- P/R/F1 per `relation type`
- P/R/F1 per lingua
- overall micro-average
- triplet-level F1
- agreement annotatori
- calibration:
  - reliability diagram
  - opzionale: `ECE`, `Brier score`
- HITL efficiency:
  - auto-approve rate
  - human-review rate
  - tempo review / manuale

### 2.4 Configurazioni sperimentali da congelare

- Lista manuali inclusi
- Lingue incluse
- Equipment types inclusi
- Prompt baseline zero-shot
- Prompt baseline few-shot
- Numero `N` esempi per few-shot
- Configurazioni MaintKG:
  - full
  - no reflective loop
  - no advisory agents
  - ablation per singolo agent
- Range di sweep per:
  - `theta_high`
  - `theta_low`
  - `max_retries`

## 3. Parti automatizzabili con script

Le seguenti componenti possono essere implementate in modo pulito e riproducibile.

### 3.1 Inventario dataset e statistiche

Script proposti:

- `scripts/paper_dataset_stats.py`
- `scripts/paper_manifest_validate.py`

Output attesi:

- `reports/dataset_summary.json`
- `reports/dataset_summary_by_language.csv`
- `reports/dataset_summary_by_equipment.csv`

Metriche estraibili:

- numero manuali per lingua
- numero manuali per equipment type
- pagine per manuale
- pagine totali per lingua
- entita` annotate per tipo e lingua
- relazioni annotate per tipo e lingua

### 3.2 Agreement tra annotatori

Script proposto:

- `scripts/paper_agreement.py`

Output attesi:

- `reports/agreement_summary.json`
- `reports/agreement_by_language.csv`
- `reports/agreement_by_label.csv`

Metriche estraibili:

- Cohen's kappa se le annotazioni sono discretizzate in unita` allineate
- F1 annotatore A vs annotatore B su:
  - entita`
  - relazioni
- accordo per tipo
- accordo per lingua

Nota:
- Per information extraction spesso F1 su span/type/relation e` piu` robusto e piu` leggibile di una kappa forzata male.

### 3.3 Orchestrazione benchmark e ablation

Esiste gia` una base utile:

- `scripts/run_manual_benchmark.py`
- `backend/services/run_metrics.py`

Estensioni consigliate:

- `scripts/paper_run_suite.py`
- `scripts/paper_retry_matrix.py`
- `scripts/paper_agent_ablation.py`
- `scripts/paper_threshold_sweep.py`

Output attesi:

- `benchmark_runs/paper/<run_id>/*.json`
- `reports/run_registry.csv`
- `reports/ablation_summary.csv`

Da registrare per ogni run:

- configurazione completa
- modello/i usati
- manuale e lingua
- durata totale
- token prompt/completion/total
- costo stimato
- confidence report
- issue counts per iterazione
- stato finale del run

### 3.4 Evaluation delle predizioni contro il gold

Script proposto:

- `scripts/paper_evaluate.py`

Output attesi:

- `reports/eval_overall.json`
- `reports/eval_by_language.csv`
- `reports/eval_entities_by_type.csv`
- `reports/eval_relations_by_type.csv`
- `reports/eval_triplets.csv`

Metriche estraibili:

- P/R/F1 entities
- P/R/F1 relations
- P/R/F1 per lingua
- P/R/F1 overall
- triplet-level F1
- confusion tables per label

### 3.5 Calibration e confidence analysis

Script proposti:

- `scripts/paper_calibration.py`
- `scripts/paper_confidence_plots.py`

Output attesi:

- `reports/calibration.json`
- `figures/reliability_diagram.pdf`
- `figures/confidence_distribution.pdf`

Metriche estraibili:

- reliability bins
- expected calibration error
- distribuzione confidence
- percentuali:
  - auto-approve
  - human-review
  - auto-reject, se usato

### 3.6 HITL efficiency

Script proposto:

- `scripts/paper_hitl_metrics.py`

Output attesi:

- `reports/hitl_summary.json`
- `reports/hitl_by_manual.csv`

Metriche estraibili:

- review rate
- auto-approve rate
- tempo medio review per manuale
- tempo medio review per nodo
- confronto con baseline di revisione manuale completa

Prerequisito:
- l'app deve loggare in modo consistente gli eventi di review con timestamp e decisione

### 3.7 Figure e tabelle per il paper

Script proposto:

- `scripts/paper_build_tables.py`

Output attesi:

- `paper_assets/table_dataset.tex`
- `paper_assets/table_main_results.tex`
- `paper_assets/table_ablation.tex`
- `paper_assets/fig_confidence_distribution.pdf`
- `paper_assets/fig_reliability_diagram.pdf`

## 4. Piano per fasi sulle parti scriptabili

### Fase 0 - Congelare il protocollo

Obiettivo:
- evitare run non confrontabili

Da fare:
- definire il formato unico di `gold`, `prediction`, `run_config`, `hitl_log`
- definire matching rules
- definire metriche ufficiali
- definire naming convention e layout cartelle

Deliverable:
- `paper_eval_spec.md`
- `paper_eval_schema.json`
- `paper_eval_config.yaml`

Exit criteria:
- ogni run puo` essere valutato dagli stessi script senza conversioni manuali

### Fase 1 - Inventario dataset e validazione input

Obiettivo:
- sapere esattamente cosa entra nel benchmark

Da fare:
- creare un manifest del dataset
- validare metadati per lingua, equipment type, source PDF
- estrarre statistiche base del dataset

Script:
- `paper_manifest_validate.py`
- `paper_dataset_stats.py`

Deliverable:
- manifest pulito
- tabelle dataset per lingua e tipo

Dipendenze:
- Fase 0

### Fase 2 - Import gold standard e agreement

Obiettivo:
- rendere valutabile il dataset annotato

Da fare:
- convertire/export annotazioni annotatore A e B nel formato canonico
- calcolare agreement per lingua, tipo, livello entity/relation
- produrre report per adjudication

Script:
- `paper_agreement.py`

Deliverable:
- agreement summary
- report per conflitti

Dipendenze:
- Fase 0
- gold standard disponibile

### Fase 3 - Harness di benchmark per baseline e ablation

Obiettivo:
- rendere riproducibili tutti i run principali del paper

Da fare:
- standardizzare il salvataggio dei run
- orchestrare baseline zero-shot e few-shot
- orchestrare MaintKG full
- orchestrare ablation:
  - `max_retries`
  - advisory agents
  - thresholds

Script:
- `paper_run_suite.py`
- `paper_retry_matrix.py`
- `paper_agent_ablation.py`
- `paper_threshold_sweep.py`

Deliverable:
- registry dei run
- output strutturati per tutti i setting

Dipendenze:
- Fase 0
- accesso ai modelli/config stabili

### Fase 4 - Evaluation automatica

Obiettivo:
- trasformare tutti i run in metriche confrontabili

Da fare:
- confrontare predizioni vs gold
- generare metriche per lingua, label e overall
- aggiungere triplet-level scoring

Script:
- `paper_evaluate.py`

Deliverable:
- report entity metrics
- report relation metrics
- report triplet metrics

Dipendenze:
- Fase 2
- Fase 3

### Fase 5 - Calibration e HITL analysis

Obiettivo:
- coprire la parte piu` originale del sistema oltre alla sola F1

Da fare:
- aggregare confidence vs correctness
- costruire reliability diagram
- calcolare auto-approve rate / human-review rate
- stimare efficienza review

Script:
- `paper_calibration.py`
- `paper_confidence_plots.py`
- `paper_hitl_metrics.py`

Deliverable:
- figure di calibration
- tabella efficienza HITL

Dipendenze:
- Fase 3
- Fase 4
- logging review affidabile

### Fase 6 - Export paper-ready

Obiettivo:
- produrre asset finali direttamente includibili nel paper

Da fare:
- esportare tabelle in `csv` e `latex`
- esportare figure finali
- congelare una cartella `paper_assets/`

Script:
- `paper_build_tables.py`

Deliverable:
- figure e tabelle definitive

Dipendenze:
- Fase 1
- Fase 4
- Fase 5

## 5. Ordine consigliato di implementazione

Ordine pragmatico:

1. Fase 0 - protocollo e metriche
2. Fase 1 - manifest e dataset stats
3. Fase 2 - agreement e gold import
4. Fase 3 - harness benchmark
5. Fase 4 - evaluation
6. Fase 5 - calibration e HITL
7. Fase 6 - export figure/tabelle

Motivo:
- senza protocollo chiaro, i benchmark vanno rifatti
- senza gold standard normalizzato, non ha senso automatizzare evaluation
- senza output run uniformi, ablation e figure diventano lavoro manuale

## 6. Cose non da automatizzare subito

Queste non sono il primo collo di bottiglia tecnico:

- raccolta annotazioni dei 2 esperti
- scelta editoriale degli esempi di schema extensibility
- feedback qualitativo degli esperti
- scrittura narrativa del paper

Vanno preparate in parallelo, ma non devono bloccare la costruzione della pipeline di metriche.

## 7. Stato attuale del repo da sfruttare

Gia` presenti e riusabili:

- `scripts/run_manual_benchmark.py` per esecuzioni benchmark per manuale
- `backend/services/run_metrics.py` per tempi, token e costi stimati
- `benchmark_runs/` come cartella di output iniziale

Gap principali da colmare:

- formato canonico unico di evaluation
- script dedicati a agreement, evaluation e figure paper-ready
- registry coerente dei run per baseline e ablation
