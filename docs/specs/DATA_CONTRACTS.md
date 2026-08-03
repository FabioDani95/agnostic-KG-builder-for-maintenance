# Contratti di dominio e dati

## 1. Scopo

Questo documento definisce i contratti logici che separano ingestion, pipeline
semantica, review e pubblicazione.

I nomi fisici di classi e tabelle possono differire, ma semantica, cardinalità
e invarianti non possono essere indebolite.

## 2. Identificativi e regole generali

### DC-ID-001 — Formato

Gli identificativi devono essere stringhe non vuote, stabili e opache.
Prefissi raccomandati:

| Entità | Prefisso |
|---|---|
| Workspace | `ws_` |
| Source | `src_` |
| Evidence unit | `ev_` |
| Batch | `batch_` |
| Run | `run_` |
| Candidate | `cand_` |
| Review decision | `decision_` |
| Graph | `kg_` |

Gli ID dei nodi devono usare il campo identificativo dichiarato
dall'ontologia.

### DC-ID-002 — Unicità dei nodi

Gli ID dei nodi pubblicati devono essere globalmente univoci nel grafo, anche
fra tipi differenti, perché il formato delle relazioni usa `from_id` e `to_id`
senza ripetere il tipo.

### DC-ID-003 — Stabilità

Una volta pubblicato, l'ID di un'entità non deve cambiare per:

- differenze di maiuscole;
- punteggiatura;
- traduzione;
- nuova evidenza;
- modifica non identitaria della descrizione.

Un merge o split che cambia identità richiede una decisione tracciata.

### DC-TIME-001 — Timestamp

I timestamp generati dall'applicazione devono essere UTC ISO 8601 con suffisso
`Z`. Timestamp sorgente ambigui devono preservare il valore originale e non
ricevere una timezone inventata.

## 3. Workspace

```json
{
  "workspace_id": "ws_machine_001",
  "status": "sources_required",
  "asset": {
    "asset_id": "asset_machine_001",
    "name": "Machine A",
    "description": "Primary machine under maintenance",
    "brand": "Example",
    "model": "M-100",
    "asset_type": "injection_molding_machine"
  },
  "created_at": "2026-07-28T12:00:00Z",
  "updated_at": "2026-07-28T12:00:00Z"
}
```

Invarianti:

- esiste esattamente un asset centrale;
- `asset` usa soltanto proprietà dichiarate dall'ontologia;
- alias, seriale, equipment tag e identificativi cliente restano in un record
  operativo separato;
- cambiare l'identità della macchina invalida mapping e decisioni dipendenti.

## 4. Source

```json
{
  "source_id": "src_manual_001",
  "workspace_id": "ws_machine_001",
  "source_kind": "pdf",
  "authority": "normative",
  "file_name": "maintenance_manual.pdf",
  "media_type": "application/pdf",
  "size_bytes": 123456,
  "sha256": "...",
  "language_hints": ["en"],
  "status": "accepted",
  "asset_assessment_id": "srcassess_001",
  "created_at": "2026-07-28T12:00:00Z"
}
```

### DC-SRC-001 — `source_kind`

Valori MVP:

- `pdf`;
- `csv`;
- `xlsx`;
- `json`;
- `jsonl`;
- `operator_input`, riservato a dati inseriti o corretti dall'operatore.

`operator_input` non è un formato di upload. Serve a rendere tracciabili
onboarding della macchina, correzioni e inserimenti effettuati attraverso
l'HITL.

### DC-SRC-002 — `authority`

Valori:

- `normative`;
- `observational`;
- `operational`;
- `informal`.

Il valore può essere proposto automaticamente, ma deve essere visibile e
modificabile al Gate 1.

Per `operator_input`, file name, media type, size e file hash sono omessi; la
source deve invece riferire la decisione o sessione HITL che l'ha generata.

### DC-SRC-003 — `status`

Valori minimi:

- `uploaded`;
- `assessing`;
- `accepted`;
- `quarantined`;
- `excluded`;
- `duplicate`;
- `failed_terminal`.

`accepted` significa che l'operatore ha caricato un formato supportato nel
workspace della macchina. Non è una classificazione del contenuto e non
significa `ready`, `processed` o pubblicata.

### DC-SRC-ASSESS-001 — Record di attribuzione operatore

Durante la migrazione ogni `Source` conserva un record append-only compatibile
con lo schema storico. Il caricamento del formato supportato produce sempre
`compatible` con reason `OPERATOR_SELECTED_SUPPORTED_FILE`: è un artifact
tecnico della scelta dell'operatore, non un assessment del contenuto e non un
gate UI.

```json
{
  "assessment_id": "srcassess_001",
  "source_id": "src_manual_001",
  "workspace_id": "ws_machine_001",
  "asset_identity_version": 1,
  "observed_claims": [],
  "outcome": "compatible",
  "reason_codes": ["OPERATOR_SELECTED_SUPPORTED_FILE"],
  "decided_by": {
    "kind": "deterministic_rule",
    "decision_id": null,
    "operator_assertion_id": null
  },
  "supersedes": null,
  "created_at": "2026-07-28T12:00:00Z"
}
```

Gli enum `uncertain` e `incompatible` possono restare nello schema fisico per
compatibilità con dati storici, ma non sono prodotti dal flusso G1 corrente.
La UI non mostra segnali, conferme, override o quarantene di appartenenza.
Rimuovere e ricaricare un file non altera il raw content-addressed.

## 5. Source locator

`locator` è una discriminated union identificata da `kind`.

### 5.1 PDF

```json
{
  "kind": "pdf",
  "page": 42,
  "section": "Troubleshooting",
  "quote": "Check the hydraulic pressure before restarting.",
  "extraction_method": "native_text"
}
```

Vincoli:

- `page` è fisica, 1-based;
- `quote` deve poter essere verificata nel testo estratto;
- `extraction_method` è `native_text`, `table` oppure `ocr`;
- pagina stampata e offset possono essere metadati aggiuntivi del locator.

### 5.2 CSV

```json
{
  "kind": "table_row",
  "table_id": "table_events",
  "table_name": "machine_logs",
  "record": 102,
  "line_start": 102,
  "line_end": 104,
  "columns": ["alarm_code", "description", "action"]
}
```

`record` identifica il record logico 1-based dopo l'header e prima di filtri o
sort. `line_start` e `line_end` identificano le linee fisiche occupate dal
record. In un CSV con newline quoted possono essere differenti.

### 5.3 XLSX

```json
{
  "kind": "xlsx_row",
  "sheet": "Maintenance",
  "row": 18,
  "cells": ["A18", "D18", "F18"]
}
```

### 5.4 JSON o JSONL

```json
{
  "kind": "json_path",
  "json_path": "$.events[17]",
  "line": null
}
```

Per JSONL `line` è obbligatorio. Il path deve riferirsi alla struttura raw
prima di flattening o join.

### 5.5 Input dell'operatore

```json
{
  "kind": "operator_input",
  "assertion_id": "assert_001",
  "decision_id": "decision_assert_001",
  "field_path": "FailureMode:fm_brake_relay_failure.material_context"
}
```

Il locator `operator_input` è ammesso soltanto per onboarding o decisioni HITL
contestuali. Non costituisce un comando generico di modifica del grafo.

## 6. Raw unit, accounting e stati

### DC-DISPOSITION-001 — Unità raw e disposizione terminale

Una `RawUnit` nasce durante l'inventario deterministico del formato, prima di
scope, mapping, join, deduplica e filtri semantici.

```json
{
  "raw_unit_id": "raw_src_logs_001_000102",
  "parent_raw_unit_id": null,
  "unit_kind": "table_record",
  "source_id": "src_logs_001",
  "structure_id": "table_events",
  "locator": {
    "kind": "table_row",
    "table_id": "table_events",
    "table_name": "machine_logs",
    "record": 102,
    "line_start": 102,
    "line_end": 104,
    "columns": ["alarm_code", "description", "action"]
  },
  "raw_hash": "...",
  "adapter_version": "csv-v1"
}
```

L'unità è:

| Formato | Unità raw canonica |
|---|---|
| PDF | top-level: una pagina fisica, inclusa una pagina vuota o illeggibile; child: ogni blocco testo, riga tabella o regione OCR estratti, con `parent_raw_unit_id` della pagina |
| CSV | un record logico dopo l'header; un record quoted multiline resta una sola unità e conserva l'intervallo di linee fisiche |
| XLSX | una riga non vuota nella regione dati di ogni foglio inventariato; header e righe vuote strutturali non sono unità |
| JSON | ogni elemento di una collection omogenea inventariata; un oggetto standalone selezionato è una unità; una leaf scalare non è una unità |
| JSONL | ogni linea non vuota, inclusa una linea malformata che riceverà esito `failed` |

Ogni tentativo su una RawUnit di una source inclusa deve produrre una
disposition terminale append-only. Per ogni coppia RawUnit/run deve esistere
esattamente una disposition attiva: quella del tentativo più recente.

Il ledger è gerarchico. Ogni unità child usa lo stesso contratto, un locator
più preciso e `parent_raw_unit_id` non nullo. La disposition top-level della
pagina non assorbe quella dei child: una pagina `processed` non può nascondere
una quinta tabella, una riga 61 o una regione OCR scartata.

```json
{
  "disposition_id": "disp_run_001_raw_000102_1",
  "run_id": "run_001",
  "raw_unit_id": "raw_src_logs_001_000102",
  "attempt": 1,
  "outcome": "processed",
  "reason_code": "SEMANTIC_PROCESSING_COMPLETED",
  "canonical_raw_unit_id": null,
  "evidence_ids": ["ev_001"],
  "checkpoint_id": "checkpoint_018",
  "retryability": "not_applicable",
  "error": null,
  "created_at": "2026-07-28T12:04:00Z"
}
```

Gli outcome sono esclusivamente:

- `processed`: la pipeline ha concluso il trattamento, anche quando non ha
  prodotto candidate; il `reason_code` distingue `CANDIDATE_EMITTED` e
  `NO_SUPPORTED_CLAIM`;
- `duplicate`: deve valorizzare `canonical_raw_unit_id`;
- `excluded`: deve riferire scope, mapping o decisione che l'ha esclusa;
- `quarantined`: il contenuto è preservato ma non può contribuire al candidate
  graph nel run;
- `failed`: deve contenere errore strutturato e `retryability`.

`retryability` è `same_run`, `new_run_required`, `not_retryable` oppure
`not_applicable`. Una disposition è terminale nel singolo tentativo e non
viene sovrascritta: un retry crea un nuovo tentativo, conserva il precedente e
diventa l'unica disposition attiva per quella coppia RawUnit/run.

Per ogni source approvata e run:

```text
RawUnit inventariate =
processed + duplicate + excluded + quarantined + failed
```

L'equazione deve essere verificata separatamente:

- sulle RawUnit top-level della source;
- sui child di ogni parent;
- sull'aggregato di tutti i child.

Il conteggio considera la disposition attiva più recente di ogni RawUnit.
Prima di ogni pruning, deduplica o filtro deve esistere la RawUnit e, a fine
run, il relativo outcome. Cap su numero di tabelle, righe, blocchi o token
limitano soltanto batching e payload modello: non possono troncare inventario,
child accounting o disposition.

### DC-PARSER-001 — Matrice normativa dei casi limite

| Caso | Comportamento obbligatorio |
|---|---|
| CSV quoted multiline | una RawUnit logica; locator con `line_start` e `line_end`; mai conteggio per linea fisica |
| BOM noto | rimosso dalla vista decodificata, preservato nel raw e registrato nel profilo |
| encoding incerto | preparazione `awaiting_operator`; vietata sostituzione silenziosa di byte |
| header duplicati | alias tecnici ordinali stabili per il mapping, per esempio `code#1` e `code#2`; approvazione obbligatoria; il raw resta invariato |
| righe vuote o commenti CSV | contatori strutturali separati, non RawUnit; la regola commento deve essere esplicita nel profilo |
| fogli XLSX nascosti | sempre inventariati, esclusi di default ma visibili; l'inclusione richiede decisione tracciata |
| celle unite | nessun forward-fill implicito; soltanto la cella anchor ha il valore salvo regola approvata |
| XLSX protetto da password | source `failed_terminal`; nessun tentativo di aggirare la protezione |
| formula senza cached value o cache stale rilevabile | valore formula preservato, flag e quarantena della RawUnit finché non viene scelta una policy |
| chiavi JSON duplicate | parsing bloccato per la struttura con errore, prima che un valore venga sovrascritto |
| precisione numerica JSON | valore raw preservato e parsing decimale lossless; vietato round-trip implicito via float |
| linea JSONL malformata | una RawUnit `failed`; le altre linee continuano e restano contabilizzate |
| JSONPath con caratteri speciali | sintassi bracket-quoted ed escaping deterministico; il path deve risolversi sul raw |
| più array indipendenti | ogni collection è inventariata e processata indipendentemente per default |
| array annidato uno-a-molti | nessuna esplosione implicita; preparazione bloccata finché non esiste strategia esplicita |

### DC-STATE-001 — Quattro state machine canoniche

I vocabolari sono distinti e non possono essere usati come sinonimi.

| Macchina a stati | Stati canonici |
|---|---|
| Source | `uploaded`, `assessing`, `accepted`, `quarantined`, `excluded`, `duplicate`, `failed_terminal` |
| Preparation | `not_started`, `profiling_or_scoping`, `awaiting_operator`, `ready`, `invalidated`, `excluded`, `duplicate`, `quarantined`, `failed_resumable`, `failed_terminal` |
| Run | `created`, `preflight`, `ready`, `processing`, `pausing`, `paused`, `awaiting_review`, `ready_to_publish`, `published`, `failed_resumable`, `failed_terminal`, `cancelled`, `superseded` |
| Workspace, derivata | `empty`, `sources_required`, `preparation_required`, `ready`, `processing`, `paused`, `failed_resumable`, `failed_terminal`, `awaiting_review`, `ready_to_publish`, `published` |

Il record Run espone sempre `state` e `resume_state`:

```json
{
  "run_id": "run_001",
  "state": "paused",
  "resume_state": "processing",
  "state_changed_at": "2026-07-28T12:04:00Z"
}
```

`resume_state` è `null` salvo quando `state` è `pausing`, `paused` o
`failed_resumable`. In tali stati deve contenere esattamente lo stato operativo
da riprendere fra `preflight`, `ready`, `processing`, `awaiting_review` e
`ready_to_publish`; non può puntare a uno stato terminale o a un altro stato
di sospensione. La transizione di Resume/Retry deve usare quel valore e
azzerare `resume_state` nella stessa transazione.

Transizioni ammesse:

- Source G1: `uploaded → assessing → accepted`; `accepted → excluded` quando
  l'operatore rimuove il file ed `excluded → accepted` quando lo ricarica. Gli
  stati legacy restano nello schema fisico ma non sono prodotti dal flusso;
- Preparation: `not_started → profiling_or_scoping →
  awaiting_operator|ready|failed_resumable|failed_terminal`; da
  `awaiting_operator` si torna a `profiling_or_scoping` o si conclude in
  `ready|excluded|quarantined`; `ready → invalidated →
  profiling_or_scoping`; `duplicate` ed `excluded` sono terminali per quella
  configurazione;
- Run: `created → preflight → ready → processing`; `processing →
  awaiting_review → ready_to_publish → published`; da qualunque stato
  operativo non terminale è ammesso `→ pausing → paused`, conservando in
  `resume_state` lo stato di origine; `paused → <resume_state>` è ammesso
  soltanto via Resume valido; un errore da uno stato operativo non terminale
  porta a `failed_resumable` o `failed_terminal`, e
  `failed_resumable → <resume_state>` soltanto via Resume/Retry valido;
  `awaiting_review → processing` è ammesso quando una decisione invalida
  output downstream, e `ready_to_publish → awaiting_review` quando la
  validazione riapre elementi; `cancelled` o `superseded` sono raggiungibili
  da ogni stato non terminale; `failed_terminal`, `cancelled`, `superseded` e
  `published` sono terminali.

Regole:

- lo stato Workspace è derivato da Asset, Source/Preparation, run attivo e
  ultima versione pubblicata; non è una seconda verità mutabile;
- Run `paused`, `failed_resumable` e `failed_terminal` mappano rispettivamente
  agli omonimi stati Workspace finché quel run resta attivo;
- una Source `accepted` può alimentare il run soltanto con Preparation `ready`;
- `paused` è riprendibile; `cancelled` è terminale e richiede un nuovo run;
- `failed_resumable` consente retry soltanto con identici input logici e
  configurazione; `failed_terminal` richiede correzione e nuovo run;
- cambiare identità macchina, scope, mapping o configurazione incompatibile
  porta gli oggetti dipendenti a `invalidated` o il run a `superseded`;
- le label italiane della UI mappano uno-a-uno a questi valori e non
  introducono nuovi stati.

Priorità della derivazione Workspace:

1. senza Asset confermato: `empty`;
2. con run attivo: `created|preflight|ready` mappano `ready`, `processing`
   mappa `processing`, `pausing` mappa lo stato Workspace corrispondente a
   `resume_state`, `paused` mappa `paused`, e
   `awaiting_review|ready_to_publish` mappano l'omonimo stato;
3. con run fallito: `failed_resumable` o `failed_terminal` mappano l'omonimo
   stato; `cancelled` e `superseded` non sono run attivi e si continua con le
   regole successive;
4. senza Source inclusa: `sources_required`;
5. con Source inclusa non `ready`: `preparation_required`;
6. con nuove Source tutte `ready`: `ready`;
7. senza nuovo lavoro e con bundle committed: `published`.

## 7. EvidenceUnit

```json
{
  "evidence_id": "ev_001",
  "workspace_id": "ws_machine_001",
  "asset_id": "asset_machine_001",
  "source_id": "src_logs_001",
  "source_kind": "csv",
  "authority": "observational",
  "locator": {
    "kind": "table_row",
    "table_id": "table_events",
    "table_name": "machine_logs",
    "record": 102,
    "line_start": 102,
    "line_end": 104,
    "columns": ["alarm_code", "description", "action"]
  },
  "provenance_refs": [
    {
      "role": "primary",
      "raw_unit_id": "raw_src_logs_001_000102",
      "source_id": "src_logs_001",
      "locator": {
        "kind": "table_row",
        "table_id": "table_events",
        "table_name": "machine_logs",
        "record": 102,
        "line_start": 102,
        "line_end": 104,
        "columns": ["alarm_code", "description", "action"]
      },
      "raw_hash": "..."
    }
  ],
  "language": {
    "detected": "en",
    "confidence": 0.99,
    "qualification": "qualified_en"
  },
  "record_role": "maintenance_event",
  "occurred_at": "2026-01-01T10:00:00Z",
  "content": {
    "title": "Brake release fault",
    "observation": "Axis 3 does not release",
    "cause": "",
    "action": "Replace brake relay",
    "outcome": "resolved",
    "semantic_texts": {
      "symptom": "Axis 3 does not release.",
      "corrective_action": "Replace brake relay."
    }
  },
  "hints": {
    "component_names": ["Axis 3 brake"],
    "error_codes": ["38001"],
    "source_record_id": "WO-123"
  },
  "measurements": [],
  "attributes": {},
  "quality_flags": [],
  "raw_ref": {
    "source_id": "src_logs_001",
    "raw_unit_id": "raw_src_logs_001_000102",
    "locator_hash": "..."
  },
  "ingestion": {
    "adapter_version": "structured-v1",
    "mapping_profile_id": "mapping_001"
  }
}
```

### DC-EV-005 — `record_role`

Valori iniziali:

- `maintenance_event`;
- `measurement`;
- `asset_master`;
- `component_master`;
- `error_catalog`;
- `generic_evidence`;
- `excluded`.

Il ruolo guida mapping e proposte, ma non introduce tipi ontologici.

### DC-EV-001 — Contenuto minimo

Sono obbligatori:

- `evidence_id`;
- `workspace_id`;
- `asset_id`;
- `source_id`;
- `source_kind`;
- `authority`;
- `locator`;
- `provenance_refs`;
- `language.detected`;
- `language.qualification`;
- `quality_flags`;
- `raw_ref`;
- `ingestion.adapter_version`.

Per l'elaborazione semantica deve esistere almeno uno tra:

- observation;
- cause;
- action;
- error code;
- measurement.

Un'evidence unit senza contenuto semantico resta tracciata ma non deve essere
inviata al modello.

Un nodo o una proprietà introdotti manualmente devono generare una evidence
unit `operator_input` o un riferimento equivalente risolvibile alla decisione
HITL. L'inserimento manuale non può diventare conoscenza senza provenance.

`source_id`, `source_kind`, `locator` e `raw_ref` rappresentano la provenienza
primaria e devono coincidere con l'unico elemento `role=primary` in
`provenance_refs`. Il core deve usare `provenance_refs`, non assumere che
l'evidenza provenga da una sola riga o source.

### DC-EV-002 — Raw

`raw_ref` deve permettere di recuperare il raw immutabile. Il raw non deve
essere duplicato nel grafo o nei log applicativi.

### DC-EV-003 — Informazioni inferite

Informazioni inferite devono essere distinte da valori sorgente e non possono
sovrascrivere il raw.

### DC-PROV-001 — Provenienza composita e trasformazioni

`provenance_refs` è un array non vuoto e ordinato per ruolo, source ID,
structure ID e locator. I ruoli ammessi sono:

- `primary`;
- `lookup`;
- `corroborating`;
- `contradicting`;
- `operator_assertion`.

Deve esistere esattamente un riferimento `primary`. Ogni riferimento deve
risolversi a una RawUnit immutabile. Un output derivato da join deve elencare
tutte le RawUnit partecipanti; non è ammesso conservare soltanto la riga
principale.

L'evidence index pubblicato deve inoltre rappresentare:

- evidence dell'esistenza del nodo;
- evidence di ogni proprietà pubblicata;
- evidence di ogni relazione;
- input, output, candidate e decisione di ogni merge o split;
- derivazione e sostituzione di una proprietà;
- tombstone di claim ritirati.

Questa lineage resta nel sidecar: non può essere aggiunta ai nodi o alle
relazioni dell'ontologia.

### DC-EV-004 — Quality flags

I flag sono codici strutturati. Set minimo:

- `MISSING_REQUIRED_SOURCE_FIELD`;
- `INVALID_DATE`;
- `INVALID_NUMBER`;
- `UNIT_MISMATCH`;
- `POSSIBLE_COLUMN_SHIFT`;
- `UNKNOWN_LANGUAGE`;
- `WRONG_ASSET_SUSPECTED`;
- `SEMANTIC_TEXT_RECONSTRUCTED`;
- `OCR_LOW_CONFIDENCE`;
- `MODEL_OUTPUT_REPAIRED`;
- `LOW_CONFIDENCE_LINK`;
- `UNMAPPED_FAILURE_MODE`.

### DC-ASSERT-001 — OperatorAssertion

Un valore manuale è evidenza soltanto attraverso un'asserzione append-only.

```json
{
  "assertion_id": "assert_001",
  "workspace_id": "ws_machine_001",
  "subject_ref": {
    "kind": "candidate",
    "candidate_id": "cand_001"
  },
  "field_path": "FailureMode:fm_brake_relay_failure.material_context",
  "asserted_value": "comp_axis_3_brake",
  "reason": "Confirmed from the inspected assembly and the cited work order.",
  "evidence_ids_seen": ["ev_001", "ev_manual_component_001"],
  "observation_basis": "direct_observation",
  "decision_id": "decision_assert_001",
  "operator": "local_operator",
  "supersedes": null,
  "created_at": "2026-07-28T12:04:30Z"
}
```

`subject_ref` è una discriminated union con esattamente una delle forme:

- `{"kind": "candidate", "candidate_id": "..."}`;
- `{"kind": "asset_identity", "asset_id": "...",
  "asset_identity_version": 1}`;
- `{"kind": "source_assessment", "assessment_id": "..."}`;
- `{"kind": "evidence", "evidence_id": "..."}`.

Il campo identificativo non pertinente alla variante è vietato. `field_path`
deve risolversi entro il subject indicato e non può trasformare l'asserzione
in un comando libero di modifica del grafo.

L'asserzione:

- può completare onboarding e proprietà di un candidato già contestuale;
- non può creare arbitrariamente un nodo o una relazione;
- non può usare placeholder come `unknown`, `n/a` o testo inventato;
- deve generare una EvidenceUnit `operator_input` con locator risolvibile;
- può sostenere una relazione causale o risolutiva soltanto se descrive
  un'osservazione diretta specifica con failure, azione e outcome espliciti.

Nella sequenza di esempio l'asserzione produce `ev_operator_001`, con locator
`operator_input` verso `assert_001` e `decision_assert_001`; per questo il
candidate `cand_001` e la review successiva possono risolvere quell'evidence
senza confonderla con `ev_manual_component_001`.

Se una proprietà obbligatoria non è presente nelle fonti e non può essere
attestata, il candidato non è pubblicabile: può essere escluso con decisione e
diventare un knowledge gap, senza creare valori fittizi.

Per `FailureMode.material_context` il vocabolario applicativo è:

- l'esatto `component_id` di un Component esistente, con `AFFECTS` supportata
  da evidence propria;
- `asset_level`, per un meccanismo realmente riferito all'intera macchina;

Stringhe vuote, `not_applicable` e categorie inventate non sono ammesse.
L'assenza di contesto produce un gap e impedisce la pubblicazione del
FailureMode. Il vocabolario è validato dall'applicazione e non modifica
`ontology_schema.JSON`.

Per una CorrectiveAction attestata direttamente dall'operatore, le proprietà
ontologiche obbligatorie usano valori risolvibili:

```text
source_type = operator_input
source_title = Operator assertion
source_reference = operator_input:<decision_id>
```

Non è ammesso simulare la provenienza da un manuale o rapporto inesistente.

### DC-CONTEXT-001 — Identità contestuale

I qualificatori di identità di Component ed ErrorCode restano nel sidecar di
candidate, evidence e identity index.

```json
{
  "context_id": "ctx_001",
  "asset_id": "asset_machine_001",
  "asset_model": "M-100",
  "component_path": ["comp_controller", "comp_power_supply"],
  "component_subsystem": "controller_power",
  "error_namespace": "main_controller",
  "firmware": {
    "min_inclusive": "3.2.0",
    "max_exclusive": "4.0.0"
  },
  "validity": {
    "from": "2025-01-01T00:00:00Z",
    "to": null
  },
  "unknown_qualifiers": []
}
```

Regole di linking:

- `asset_id` è sempre parte del contesto;
- alias uguale non basta per auto-link di Component: serve almeno component
  path, subsystem o part number stabile compatibile;
- codice uguale non basta per auto-link di ErrorCode: servono modello e
  namespace compatibili e almeno un qualificatore fra firmware, component
  path o scope normativo;
- un qualificatore noto incompatibile blocca auto-link e auto-merge;
- `unknown` può essere trattato come wildcard soltanto se non esiste alcuna
  definizione concorrente nello stesso asset/modello/namespace; in presenza di
  definizioni concorrenti o ambiguità la proposta va in review;
- intervalli firmware o temporali devono sovrapporsi per essere compatibili;
- lo stesso `code` può appartenere a ErrorCode distinti con ID diversi, perché
  l'ontologia rende unico `error_code_id`, non `code`.

Firmware, periodo, component path, alias e part number non possono diventare
proprietà extra dei nodi pubblicati.

### DC-OUTCOME-001 — OutcomeAssessment e supporto minimo

Ogni outcome normalizzato deve essere riferito a una specifica coppia
failure-action, non soltanto al record sorgente.

```json
{
  "outcome_assessment_id": "outcome_001",
  "evidence_id": "ev_001",
  "failure_claim_ref": "FailureMode:fm_brake_relay_failure",
  "action_claim_ref": "CorrectiveAction:action_replace_relay",
  "raw_value": "resolved",
  "normalized_outcome": "observed_success",
  "basis": "explicit_operational_record",
  "assessed_by": "deterministic_mapping",
  "decision_id": null
}
```

Valori ammessi:

- `documented_resolution`;
- `observed_success`;
- `failed`;
- `partially_resolved`;
- `monitoring`;
- `recurred`;
- `not_reported`;
- `unknown`.

Regole minime per le relazioni:

| Relazione | Supporto minimo |
|---|---|
| `MAY_INDICATE` | affermazione esplicita di possibile causa in una fonte compatibile, oppure diagnosi operativa specifica approvata; la sola co-occorrenza non basta |
| `INDICATES` | mapping esplicito codice-causa in una fonte normativa applicabile; un log isolato non basta |
| `RESOLVED_BY` | istruzione risolutiva normativa esplicita (`documented_resolution`) oppure azione e failure legate a `observed_success` |

`failed`, `partially_resolved`, `monitoring`, `recurred`, `not_reported` e
`unknown` non consentono auto-stage di `RESOLVED_BY`. La motivazione del
modello non è supporto. Un passo di sola ispezione, verifica o misura non è una
CorrectiveAction restaurativa; può restare evidence diagnostica ma non
autorizza `RESOLVED_BY`.

### DC-CONFLICT-001 — Conflict

```json
{
  "conflict_id": "conflict_001",
  "workspace_id": "ws_machine_001",
  "claim_refs": ["claim_manual_001", "claim_log_017"],
  "evidence_ids": ["ev_004", "ev_117"],
  "conflict_kind": "normative_observational",
  "context_id": "ctx_001",
  "blocking": true,
  "status": "open",
  "opened_in_revision": "cgrev_003",
  "resolution": null
}
```

La precedenza è deterministica:

1. applicabilità esatta a macchina, modello, firmware e componente prevale
   su una fonte più generica soltanto per quello scope;
2. una dichiarazione esplicita `supersedes` dello stesso emittente e scope
   prevale sulla versione sostituita;
3. una revisione più recente prevale nella stessa famiglia documentale,
   emittente e scope;
4. la recency da sola non sceglie fra famiglie o emittenti differenti;
5. a parità dei criteri precedenti, l'ordine di proposta è `normative`,
   `operational`, `observational`, `informal`;
6. una fonte osservazionale può corroborare o contraddire, ma non
   sovrascrive automaticamente una fonte normativa;
7. un pareggio o una contraddizione non risolvibile deterministicamente è un
   conflitto blocking.

Gli esiti di risoluzione sono:

- `coexist`, quando i claim valgono in scope disgiunti o condizionali;
- `superseded`, soltanto con lineage di sostituzione verificabile;
- `operator_selected`, con decisione e razionale.

Nessuna risoluzione elimina evidence: claim non selezionati restano
rintracciabili come `contradicting`.

### DC-GAP-001 — KnowledgeGap

```json
{
  "gap_id": "gap_001",
  "workspace_id": "ws_machine_001",
  "subject_ref": "FailureMode:fm_brake_relay_failure",
  "gap_kind": "missing_corrective_action",
  "evidence_ids": ["ev_001"],
  "blocking": false,
  "status": "open",
  "opened_in_graph_version": null,
  "opened_in_candidate_graph_revision_id": "cgrev_001",
  "closed_in_graph_version": null,
  "resolution_decision_id": null
}
```

L'origine è una `oneOf`: esattamente uno fra `opened_in_graph_version` e
`opened_in_candidate_graph_revision_id` deve essere non nullo. Il primo
identifica un gap scoperto su conoscenza già pubblicata; il secondo un gap
emerso prima del publish in una CandidateGraphRevision. La chiusura può
valorizzare `closed_in_graph_version` soltanto quando una versione pubblicata
risolve o registra definitivamente il gap.

I valori minimi di `gap_kind` sono:

- `missing_required_property`;
- `missing_relation_support`;
- `unknown_failure_mode`;
- `missing_corrective_action`;
- `ambiguous_identity`;
- `unqualified_language`;
- `unsupported_causality`.

Un gap che nasconde una violazione ontologica o una decisione necessaria è
blocking. L'assenza veritiera di una causa o azione può essere non blocking.
Conflict e KnowledgeGap sono contratti sidecar e non tipi di nodo.

## 8. MappingProfile

```json
{
  "mapping_profile_id": "mapping_001",
  "source_kind": "csv",
  "schema_fingerprint": "...",
  "role": "maintenance_event",
  "language": "en",
  "included_fields": ["alarm", "description", "action", "outcome"],
  "field_mapping": {
    "alarm": "hints.error_codes[]",
    "description": "content.observation",
    "action": "content.action",
    "outcome": "content.outcome"
  },
  "semantic_text_templates": {
    "symptom": "{description}",
    "failure_mode": "{cause}",
    "corrective_action": "{action}",
    "component": "{component}",
    "error_code_context": "{alarm}"
  },
  "joins": [],
  "version": 1,
  "approved_at": "2026-07-28T12:00:00Z"
}
```

Il fingerprint deve includere almeno:

- formato;
- struttura o foglio;
- nomi e ordine logico dei campi;
- tipi prevalenti;
- presenza delle colonne chiave.

Il profilo deve inoltre dichiarare:

- regole di normalizzazione;
- campi inclusi nei testi semantici per ruolo;
- campi esclusi;
- template;
- strategia per valori nulli;
- vocabolari di severità e outcome;
- versione del normalizzatore.

### DC-JOIN-001 — JoinSpec

Tabelle, fogli e collection vengono elaborate indipendentemente per default.
Un join è ammesso soltanto quando un singolo claim richiede campi presenti in
strutture differenti e deve essere approvato prima del run.

```json
{
  "join_spec_id": "join_001",
  "version": 1,
  "primary": {
    "source_id": "src_events_001",
    "structure_id": "events"
  },
  "lookups": [
    {
      "source_id": "src_components_001",
      "structure_id": "components",
      "role": "lookup"
    }
  ],
  "predicates": [
    {
      "primary_field": "component_code",
      "lookup_field": "code",
      "normalizer_version": "exact-code-v1"
    }
  ],
  "cardinality": "many_to_one",
  "join_type": "left",
  "unmatched_policy": "quarantine_primary",
  "multiple_match_policy": "quarantine_primary",
  "fan_out_policy": "forbid",
  "max_fan_out": 1,
  "approved_decision_id": "decision_join_001",
  "config_hash": "..."
}
```

Valori e regole:

- `cardinality`: `one_to_one`, `many_to_one`, `one_to_many`,
  `many_to_many`;
- `join_type`: `left` o `inner`;
- `unmatched_policy`: `keep_primary_with_flag`, `exclude_primary`,
  `quarantine_primary`, `fail_run`;
- `multiple_match_policy`: `quarantine_primary`, `fail_run`,
  `emit_multiple`;
- in assenza di una policy esplicita valgono `quarantine_primary`,
  `quarantine_primary` e `fan_out_policy=forbid`;
- `one_to_many` può usare `emit_multiple` soltanto con
  `max_fan_out > 1`; richiede approvazione manuale e superare il limite mette
  in quarantena la RawUnit primaria;
- `many_to_many` non può essere auto-approvato e richiede una strategia
  manuale `aggregate_then_join` oppure `emit_bounded_pairs`, chiavi d'ordine e
  fan-out massimo; un prodotto cartesiano implicito è vietato;
- un join `inner` deve produrre disposition `excluded` per le RawUnit primary
  senza match; non può farle scomparire;
- una RawUnit lookup usata da più output resta contata una sola volta, mentre
  ogni EvidenceUnit risultante la include in `provenance_refs`;
- ogni cambio a chiavi, normalizzatore, cardinalità o policy cambia versione e
  config hash e invalida gli output dipendenti.

## 9. Candidate

```json
{
  "candidate_id": "cand_001",
  "run_id": "run_001",
  "candidate_graph_revision_id": "cgrev_001",
  "candidate_kind": "node",
  "operation": "create",
  "target_type": "FailureMode",
  "target_id": "fm_brake_relay_failure",
  "base_claim_ref": null,
  "proposed_value": {
    "failure_mode_id": "fm_brake_relay_failure",
    "name": "Brake relay failure",
    "description": "The relay does not energize the release circuit.",
    "material_context": "comp_axis_3_brake"
  },
  "evidence_ids": ["ev_001", "ev_operator_001"],
  "score": 0.87,
  "score_kind": "uncalibrated_confidence",
  "calibration_profile_id": null,
  "feature_version": "candidate-features-v1",
  "status": "review_required",
  "blocking": true,
  "conflicts": [],
  "alternatives": []
}
```

### DC-CAND-001 — `candidate_kind`

- `node`;
- `relationship`;
- `entity_link`;
- `merge`;
- `split`;
- `property_update`;
- `conflict`.

### DC-CAND-002 — `operation`

- `create`;
- `link`;
- `merge`;
- `split`;
- `update`;
- `withdraw`;
- `supersede`;
- `no_change`.

`reject` è un verdetto di review, non un'operazione candidata.

`withdraw` punta a un claim già pubblicato mediante `base_claim_ref`. Può
riguardare un nodo, una relazione o una proprietà; la rimozione di una
proprietà obbligatoria deve includere una sostituzione valida oppure il ritiro
del nodo e delle dipendenze. `supersede` lega il ritiro a un claim sostitutivo.

### DC-CAND-003 — `status`

- `proposed`;
- `auto_staged`;
- `review_required`;
- `approved`;
- `rejected`;
- `deferred`;
- `quarantined`;
- `superseded`.

`calibration_profile_id` e `feature_version` sono sempre presenti. Un
`calibration_profile_id=null`, un profilo invalido o un mismatch di feature
impediscono `auto_staged`.

### DC-CALIBRATION-001 — CalibrationProfile

```json
{
  "calibration_profile_id": "calibration_entity_link_en_001",
  "status": "valid",
  "operation": "entity_link",
  "provider_config_id": "provider_config_001",
  "provider_config_hash": "...",
  "provider_qualifiers": {
    "generation": {
      "provider": "openai",
      "model": "gpt-5.6-terra",
      "config_version": 1,
      "prompt_hash": "...",
      "output_schema_hash": "..."
    },
    "embedding": {
      "provider": "openai",
      "model": "qualified-embedding-model",
      "config_version": 1,
      "model_version": "resolved-provider-version",
      "dimensions": null
    }
  },
  "non_applicable_qualifier_reasons": {
    "generation": null,
    "embedding": null
  },
  "language": "qualified_en",
  "feature_version": "entity-link-features-v1",
  "schema_hash": "...",
  "dataset_id": "ds_entity_link_heldout_001",
  "dataset_hash": "...",
  "thresholds": {
    "auto_stage_min": 0.95,
    "review_min": 0.7
  },
  "confusion_matrix": {
    "true_positive": 42,
    "false_positive": 1,
    "true_negative": 71,
    "false_negative": 6
  },
  "automation_coverage": {
    "numerator": {
      "count": 42,
      "definition": "gold positives correctly auto-staged"
    },
    "denominator": {
      "count": 48,
      "definition": "all gold positives for the operation"
    },
    "auto_staged_count": 43,
    "minimum_auto_staged_count": 20,
    "rate": 0.875,
    "minimum_required": 0.2,
    "symbolic_guard_false_auto_stages": 0,
    "reason": "GATES_SATISFIED"
  },
  "sample_counts": {
    "total": 120,
    "positive": 48,
    "negative": 72
  },
  "metrics": {
    "precision": 0.976744186,
    "recall": 0.875
  },
  "invalid_reason": null,
  "created_at": "2026-07-28T12:00:00Z"
}
```

Il profilo è specifico per operation, `provider_config_id` e relativo hash,
qualificatori completi sia di generation sia di embedding, lingua, feature
version, schema e dataset immutabile. Le chiavi `generation` ed `embedding`
sono sempre presenti in `provider_qualifiers`; ciascun valore è il qualifier
congelato oppure `null` soltanto quando l'operation è provatamente
indipendente da quello stage. In tal caso la chiave omonima di
`non_applicable_qualifier_reasons` deve contenere un reason non vuoto e
risolvibile al report held-out che dimostra che nessun input, feature o cache
dipende direttamente o transitivamente dallo stage. Un qualifier applicabile
richiede reason `null`.

Per l'uso di un CalibrationProfile devono coincidere esattamente tutti e soli
i qualifier applicabili, oltre a `provider_config_id`, config hash, operation,
lingua, feature/schema e dataset hash. Non è ammessa l'ereditarietà implicita
dal provider corrente, né un `null` usato per eludere un mismatch. `status` è
`valid` o `invalid`.

`invalid_reason`, quando applicabile, usa almeno:

- `MODEL_CHANGED`;
- `PROVIDER_CHANGED`;
- `LANGUAGE_CHANGED`;
- `FEATURE_VERSION_CHANGED`;
- `SCHEMA_CHANGED`;
- `DATASET_CHANGED`;
- `ZERO_DENOMINATOR`;
- `PRECISION_BELOW_GATE`;
- `COVERAGE_BELOW_MINIMUM`;
- `SAMPLE_BELOW_MINIMUM`;
- `SYMBOLIC_GUARD_VIOLATION`;
- `EXPIRED_OR_REVOKED`.

`automation_coverage.rate` è sempre
`numerator.count / denominator.count`: il numeratore contiene i gold positive
correttamente auto-staged e il denominatore tutti i gold positive
dell'operation. `reason` è obbligatorio e vale `GATES_SATISFIED` per un profilo
valido, altrimenti coincide con `invalid_reason`. Il gate fallisce con
denominatore zero, `auto_staged_count < minimum_auto_staged_count` (minimo MVP
`20`), coverage sotto `minimum_required`, precisione sotto la soglia
dell'operation o anche un solo false auto-stage contro una guard simbolica.
Nessun candidate può ereditare un profilo per similarità: tutti i
qualificatori devono coincidere esattamente. Un cambio rilevante invalida il
profilo senza cancellarlo e porta i candidate dipendenti a
`review_required`.

### DC-CGRAPH-001 — CandidateGraphRevision

Il candidate graph non è un oggetto mutabile in-place. Ogni output della
pipeline o decisione attiva produce una revisione immutabile derivata dalla
versione pubblicata di base.

La generation produce prima una revisione di sottografo per singola fonte:

```json
{
  "source_subgraph_revision_id": "sgrev_src_logs_001_001",
  "workspace_id": "ws_machine_001",
  "source_id": "src_logs_001",
  "preparation_fingerprint": "...",
  "input_config_hash": "...",
  "evidence_ids": ["ev_001"],
  "candidate_ids": ["cand_001"],
  "ontology_validation": {
    "status": "passed",
    "ontology_sha256": "81f2d894e8b4c3c0ba3bb2e7149941ae91b704ebd8a8b8dedef91b79bd1508db",
    "missing_required_properties": [],
    "extra_properties": [],
    "invalid_relations": [],
    "unresolved_mapping_columns": []
  },
  "status": "approved",
  "approval_decision_id": "decision_source_graph_001",
  "supersedes": null,
  "created_at": "2026-07-28T12:04:00Z"
}
```

Stati ammessi: `building`, `invalid`, `reviewing`, `approved`, `rejected`,
`superseded`. La chiave logica comprende `source_id`, preparation fingerprint
e input config hash. Ogni rigenerazione crea una nuova revisione; non modifica
quella approvata. Soltanto revisioni `approved` possono entrare nella barriera
di linking/merge cross-source. L'approvazione è source-scoped, append-only e
non autorizza automaticamente alcun merge.

Il payload `graph` della revisione deve serializzare i nodi con gli esatti
campi dichiarati da `ontology_schema.JSON`; label UI, conteggi, confidence,
outcome, measurement e provenance restano in view model o sidecar e non
diventano proprietà arbitrarie dei nodi. `ontology_validation.status` è
`passed` soltanto con proprietà obbligatorie presenti al `100%`, proprietà
extra `0`, domain/range errati `0`, endpoint mancanti `0`, ID duplicati `0` e
mapping diagnostici irrisolti `0`. In ogni altro caso lo stato della revisione
è `invalid` e nessuna decisione `approve_source_subgraph` è accettabile.

```json
{
  "candidate_graph_revision_id": "cgrev_001",
  "run_id": "run_001",
  "workspace_id": "ws_machine_001",
  "base_graph_version": null,
  "input_config_hash": "...",
  "source_subgraph_revision_ids": ["sgrev_src_logs_001_001"],
  "candidate_ids": ["cand_001"],
  "active_decision_ids": ["decision_assert_001"],
  "status": "reviewing",
  "supersedes": null,
  "created_at": "2026-07-28T12:05:00Z"
}
```

`base_graph_version` è `null` soltanto per la prima pubblicazione. Stati:

- `building`;
- `reviewing`;
- `validating`;
- `publishable`;
- `published`;
- `superseded`;
- `abandoned`.

Per un aggiornamento incrementale, `base_graph_version` identifica l'ultima
versione pubblicata e `source_subgraph_revision_ids` contiene soltanto le
fonti nuove o esplicitamente invalidate nel run corrente. I sottografi già
pubblicati non vengono rigenerati né riuniti in un nuovo input monolitico. Il
delta cross-source può proporre `add`, `link`, `merge`, `conflict`, `withdraw`
o `unchanged`; la base resta byte-invariata fino al publish della versione
successiva.

La pipeline può creare candidate e applicare transizioni deterministiche
registrate. Qualsiasi cambiamento semantico iniziato dall'operatore richiede
una ReviewDecision. Un claim ritirato resta nella versione base e viene omesso
soltanto dalla versione monotona successiva dopo approvazione; il sidecar conserva un tombstone con claim, evidence,
decisione, dipendenze ed eventuale sostituto.

## 10. ReviewDecision

```json
{
  "decision_id": "decision_001",
  "run_id": "run_001",
  "subject_ref": {
    "kind": "candidate",
    "candidate_id": "cand_001"
  },
  "candidate_graph_revision_before": "cgrev_001",
  "candidate_graph_revision_after": "cgrev_002",
  "action": "defer",
  "before": null,
  "after": {
    "status": "deferred",
    "blocking": false,
    "gap_id": "gap_001"
  },
  "evidence_ids_seen": ["ev_001", "ev_operator_001"],
  "operator": "local_operator",
  "note": "",
  "created_at": "2026-07-28T12:06:00Z",
  "context_hash": "...",
  "supersedes_decision_id": null
}
```

`subject_ref` è una discriminated union con esattamente una delle forme:

- `{"kind": "candidate", "candidate_id": "..."}`;
- `{"kind": "conflict", "conflict_id": "..."}`;
- `{"kind": "evidence", "evidence_id": "..."}`.

Il campo identificativo delle altre varianti è vietato. `resolve_conflict`
richiede `kind=conflict`, `exclude_evidence` richiede `kind=evidence`; le
azioni candidate usano `kind=candidate`.

Azioni minime:

- `approve`;
- `reject`;
- `edit`;
- `merge`;
- `split`;
- `select_existing`;
- `exclude_evidence`;
- `resolve_conflict`;
- `defer`;
- `reopen`;
- `revert`.

Una `ReviewDecision` deve sempre riferirsi tramite `subject_ref` a un
candidato, a un conflitto o a un'evidenza già registrata. Non costituisce un
comando generico di graph editing.

Il valore `after` deve:

- essere validato contro l'ontologia prima della persistenza;
- conservare almeno una evidence reference risolvibile, salvo un rifiuto;
- rimanere entro il perimetro della proposta revisionata;
- registrare esplicitamente eventuali cambi di identità dovuti a merge o
  split.

Non esiste nel contratto pubblico un payload `create_node`, `delete_node`,
`create_relationship`, `delete_relationship` o `save_graph` libero.

### DC-REVIEW-001 — Lifecycle, reversal e atomicità

ReviewDecision è append-only e non viene aggiornata o eliminata.

- `reopen` disattiva l'effetto della decisione precedente, ripristina
  `review_required` e produce una nuova CandidateGraphRevision;
- `revert` ripristina esplicitamente il `before` di una decisione non ancora
  pubblicata e deve riferirla con `supersedes_decision_id`;
- una nuova decisione sostitutiva riferisce quella precedente;
- `reopen` non equivale ad approvare il valore opposto;
- una decisione già inclusa in una versione pubblicata non può essere riaperta
  o revertita in-place: serve un nuovo run con candidate `withdraw`,
  `supersede` o `update` verso la versione monotona successiva;
- decisione, validazione ontologica, nuova revisione e audit event sono una
  sola transazione. Se una parte fallisce, nessuna diventa visibile.

Ogni candidate graph-affecting deve raggiungere uno stato terminale prima del
publish. `blocking=false` non autorizza a ignorare una proposta aperta: per
ometterla serve `rejected`, `deferred`, `quarantined` o `superseded` con
disposition/gap registrato.

Gli elementi `auto_staged` possono essere confermati insieme dalla conferma
finale di publish. La conferma crea decisioni aggregate risolvibili ai singoli
candidate prima della validazione; non pubblica candidate ancora nello stato
`auto_staged`.

## 11. Knowledge graph pubblicato

### DC-GRAPH-001 — Formato

Il formato preserva la struttura principale già usata dalla codebase:

```json
{
  "metadata": {
    "bundle_id": "bundle_kg_ws_machine_001_v001",
    "graph_id": "kg_ws_machine_001",
    "version": "V001",
    "status": "published",
    "created_at": "2026-07-28T12:10:00Z",
    "ontology_name": "Core_Ontology",
    "ontology_version": "2.0",
    "ontology_sha256": "81f2d894e8b4c3c0ba3bb2e7149941ae91b704ebd8a8b8dedef91b79bd1508db",
    "asset_id": "asset_machine_001",
    "contributing_source_ids": [
      "src_manual_accepted_002"
    ],
    "product_name": "Machine A",
    "product_short_name": "M-100",
    "product_type": "injection_molding_machine",
    "domain_topics": ["maintenance", "troubleshooting"],
    "total_nodes": 2,
    "total_relationships": 1
  },
  "nodes": {
    "Asset": [
      {
        "asset_id": "asset_machine_001",
        "name": "Machine A",
        "description": "Primary machine under maintenance",
        "brand": "Example",
        "model": "M-100",
        "asset_type": "injection_molding_machine"
      }
    ],
    "Component": [
      {
        "component_id": "comp_axis_3_brake",
        "name": "Axis 3 brake",
        "description": "Brake subsystem for axis 3",
        "category": "electromechanical"
      }
    ],
    "Symptom": [],
    "FailureMode": [],
    "CorrectiveAction": [],
    "ErrorCode": []
  },
  "relationships": [
    {
      "type": "HAS_COMPONENT",
      "from_id": "asset_machine_001",
      "to_id": "comp_axis_3_brake"
    }
  ]
}
```

### DC-GRAPH-002 — Nodi

Le sei chiavi di `nodes` devono essere sempre presenti.

Ogni oggetto nodo deve contenere soltanto le proprietà dichiarate
dall'ontologia per quel tipo. Non deve contenere:

- evidence;
- confidence;
- stato di review;
- embedding;
- prompt;
- raw;
- alias non ontologici.

Il contratto del grafo pubblicato è read-only. Ogni cambiamento successivo deve
partire da nuove fonti o candidate, attraversare la review e produrre una nuova
versione; non è ammesso un endpoint di aggiornamento in-place.

### DC-GRAPH-003 — Relazioni

Ogni relazione deve contenere soltanto:

- `type`;
- `from_id`;
- `to_id`.

Il tipo deve essere dichiarato dall'ontologia. Domain e range devono essere
validi e gli endpoint devono esistere.

### DC-GRAPH-004 — Cardinalità e completezza

- `Asset` contiene esattamente un elemento;
- gli altri tipi possono essere vuoti se le fonti non li supportano;
- un `Component` pubblicato deve avere almeno un `HAS_COMPONENT`;
- un `ErrorCode` pubblicato dovrebbe avere `GENERATES_ERROR`;
- un `FailureMode` deve partecipare ad almeno un percorso diagnostico tramite
  `MAY_INDICATE` o `INDICATES`;
- l'assenza documentata di una corrective action è un knowledge gap, non una
  violazione ontologica.

Il sistema non deve inventare nodi o relazioni per rendere tutte le collezioni
non vuote.

### DC-GRAPH-005 — Errori bloccanti e knowledge gap

Sono bloccanti:

- proprietà ontologiche obbligatorie mancanti;
- proprietà extra;
- ID duplicati;
- endpoint mancanti;
- domain/range errati;
- relazione senza evidenza nell'evidence index;
- secondo Asset;
- checksum ontologico errato.

Sono pubblicabili se esplicitamente dichiarati e non nascondono una violazione:

- failure mode senza corrective action documentata;
- componente senza failure mode noto;
- macchina senza error code;
- candidata informazione esclusa per insufficienza di evidenza.

## 12. Evidence index

```json
{
  "bundle_id": "bundle_kg_ws_machine_001_v001",
  "graph_id": "kg_ws_machine_001",
  "graph_version": "V001",
  "node_evidence": {
    "Asset:asset_machine_001": [
      {
        "evidence_id": "ev_manual_asset_001",
        "support_type": "explicit",
        "authority": "normative",
        "score": 1.0,
        "human_status": "approved"
      }
    ],
    "Component:comp_axis_3_brake": [
      {
        "evidence_id": "ev_manual_component_001",
        "support_type": "explicit",
        "authority": "normative",
        "score": 1.0,
        "human_status": "approved"
      }
    ]
  },
  "property_evidence": {
    "Asset:asset_machine_001.asset_id": [
      {
        "evidence_id": "ev_manual_asset_001",
        "support_type": "explicit",
        "authority": "normative",
        "score": 1.0,
        "human_status": "approved"
      }
    ],
    "Asset:asset_machine_001.name": [
      {
        "evidence_id": "ev_manual_asset_001",
        "support_type": "explicit",
        "authority": "normative",
        "score": 1.0,
        "human_status": "approved"
      }
    ],
    "Asset:asset_machine_001.description": [
      {
        "evidence_id": "ev_manual_asset_001",
        "support_type": "explicit",
        "authority": "normative",
        "score": 1.0,
        "human_status": "approved"
      }
    ],
    "Asset:asset_machine_001.brand": [
      {
        "evidence_id": "ev_manual_asset_001",
        "support_type": "explicit",
        "authority": "normative",
        "score": 1.0,
        "human_status": "approved"
      }
    ],
    "Asset:asset_machine_001.model": [
      {
        "evidence_id": "ev_manual_asset_001",
        "support_type": "explicit",
        "authority": "normative",
        "score": 1.0,
        "human_status": "approved"
      }
    ],
    "Asset:asset_machine_001.asset_type": [
      {
        "evidence_id": "ev_manual_asset_001",
        "support_type": "explicit",
        "authority": "normative",
        "score": 1.0,
        "human_status": "approved"
      }
    ],
    "Component:comp_axis_3_brake.component_id": [
      {
        "evidence_id": "ev_manual_component_001",
        "support_type": "explicit",
        "authority": "normative",
        "score": 1.0,
        "human_status": "approved"
      }
    ],
    "Component:comp_axis_3_brake.name": [
      {
        "evidence_id": "ev_manual_component_001",
        "support_type": "explicit",
        "authority": "normative",
        "score": 1.0,
        "human_status": "approved"
      }
    ],
    "Component:comp_axis_3_brake.description": [
      {
        "evidence_id": "ev_manual_component_001",
        "support_type": "explicit",
        "authority": "normative",
        "score": 1.0,
        "human_status": "approved"
      }
    ],
    "Component:comp_axis_3_brake.category": [
      {
        "evidence_id": "ev_manual_component_001",
        "support_type": "explicit",
        "authority": "normative",
        "score": 1.0,
        "human_status": "approved"
      }
    ]
  },
  "relationship_evidence": {
    "Asset:asset_machine_001|HAS_COMPONENT|Component:comp_axis_3_brake": [
      {
        "evidence_id": "ev_manual_component_001",
        "support_type": "explicit",
        "authority": "normative",
        "score": 1.0,
        "human_status": "approved"
      }
    ]
  },
  "evidence_units": {
    "ev_manual_asset_001": {
      "source_id": "src_manual_accepted_002",
      "provenance_refs": [
        {
          "role": "primary",
          "raw_unit_id": "raw_src_manual_accepted_002_page_001",
          "source_id": "src_manual_accepted_002",
          "locator": {
            "kind": "pdf",
            "page": 1,
            "section": "Cover",
            "quote": "M-100 Series Maintenance Manual",
            "extraction_method": "native_text"
          },
          "raw_hash": "..."
        }
      ]
    },
    "ev_manual_component_001": {
      "source_id": "src_manual_accepted_002",
      "provenance_refs": [
        {
          "role": "primary",
          "raw_unit_id": "raw_src_manual_accepted_002_page_022_block_003",
          "source_id": "src_manual_accepted_002",
          "locator": {
            "kind": "pdf",
            "page": 22,
            "section": "Axis 3 brake assembly",
            "quote": "The Axis 3 brake is an electromechanical subsystem.",
            "extraction_method": "native_text"
          },
          "raw_hash": "..."
        }
      ]
    }
  },
  "identity_lineage": [],
  "tombstones": [],
  "open_conflicts": [],
  "open_knowledge_gaps": ["gap_001"]
}
```

### DC-EIDX-001 — Support type

- `explicit`;
- `inferred`;
- `corroborating`;
- `contradicting`;
- `human_confirmed`.

### DC-EIDX-002 — Copertura

Ogni nodo, proprietà e relazione pubblicati devono avere almeno un riferimento
nell'evidence index. Ogni riferimento deve risolversi nella mappa
`evidence_units`, che contiene almeno source e provenance refs sufficienti a
ritrovare il raw mediante source hash e locator.

`identity_lineage` registra merge e split con claim di input/output,
candidate, decisione ed evidence. `tombstones` registra claim ritirati e
sostituti. Il bundle resta risolvibile senza consultare stato mutabile del run;
il raw originale può restare nello store locale, identificato da hash.

L'evidence index non estende l'ontologia e non è parte del graph payload usato
per validare nodi e relazioni.

## 13. Run manifest

```json
{
  "run_id": "run_001",
  "bundle_id": "bundle_kg_ws_machine_001_v001",
  "workspace_id": "ws_machine_001",
  "graph_id": "kg_ws_machine_001",
  "graph_version": "V001",
  "base_graph_version": null,
  "candidate_graph_revision_id": "cgrev_002",
  "state": "published",
  "resume_state": null,
  "asset_identity_version": 1,
  "run_input_source_ids": [
    "src_manual_accepted_002",
    "src_logs_001"
  ],
  "contributing_source_ids": [
    "src_manual_accepted_002"
  ],
  "source_hashes": {
    "src_manual_accepted_002": "...",
    "src_logs_001": "..."
  },
  "ontology": {
    "name": "Core_Ontology",
    "version": "2.0",
    "sha256": "..."
  },
  "pipeline_version": "...",
  "provider_config_id": "provider_config_001",
  "data_egress_policy_id": "egress_001",
  "provider": "openai",
  "models": {
    "generation": "...",
    "embedding": "..."
  },
  "prompt_hashes": {},
  "mapping_profile_ids": [],
  "scoping_profile_ids": [],
  "calibration_profiles": [
    {
      "operation": "entity_link",
      "calibration_profile_id": "calibration_entity_link_en_001",
      "profile_hash": "...",
      "provider_config_id": "provider_config_001",
      "provider_config_hash": "...",
      "provider_qualifiers": {
        "generation": {
          "provider": "openai",
          "model": "gpt-5.6-terra",
          "config_version": 1,
          "prompt_hash": "...",
          "output_schema_hash": "..."
        },
        "embedding": {
          "provider": "openai",
          "model": "qualified-embedding-model",
          "config_version": 1,
          "model_version": "resolved-provider-version",
          "dimensions": null
        }
      },
      "non_applicable_qualifier_reasons": {
        "generation": null,
        "embedding": null
      },
      "language": "qualified_en",
      "feature_version": "entity-link-features-v1",
      "schema_hash": "...",
      "dataset_id": "ds_entity_link_heldout_001",
      "dataset_hash": "..."
    }
  ],
  "step_execution": {
    "structured_selection": {
      "mode": "automatic",
      "delegated_by": "local_operator",
      "delegated_at": "2026-07-28T12:00:00Z",
      "status": "completed",
      "exception_count": 0
    },
    "nonblocking_review": {
      "mode": "exceptions_only",
      "delegated_by": "local_operator",
      "delegated_at": "2026-07-28T12:05:00Z",
      "status": "completed",
      "exception_count": 0
    }
  },
  "thresholds": {},
  "cache": {},
  "metrics": {},
  "raw_accounting": {
    "disposition_ledger_ref": "run_store:run_001/raw-disposition-ledger",
    "ledger_sha256": "...",
    "by_source": {
      "src_manual_accepted_002": {
        "source_id": "src_manual_accepted_002",
        "top_level": {
          "inventoried": 10,
          "terminal_outcomes": {
            "processed": 9,
            "duplicate": 0,
            "excluded": 1,
            "quarantined": 0,
            "failed": 0
          }
        },
        "child_aggregate": {
          "inventoried": 243,
          "terminal_outcomes": {
            "processed": 240,
            "duplicate": 1,
            "excluded": 1,
            "quarantined": 1,
            "failed": 0
          }
        },
        "parent_groups_checked": 10,
        "parent_groups_balanced": 10
      },
      "src_logs_001": {
        "source_id": "src_logs_001",
        "top_level": {
          "inventoried": 2,
          "terminal_outcomes": {
            "processed": 2,
            "duplicate": 0,
            "excluded": 0,
            "quarantined": 0,
            "failed": 0
          }
        },
        "child_aggregate": {
          "inventoried": 0,
          "terminal_outcomes": {
            "processed": 0,
            "duplicate": 0,
            "excluded": 0,
            "quarantined": 0,
            "failed": 0
          }
        },
        "parent_groups_checked": 0,
        "parent_groups_balanced": 0
      }
    }
  },
  "decision_ids": ["decision_assert_001", "decision_001"],
  "checkpoint_ids": ["checkpoint_001", "checkpoint_018"],
  "artifact_hashes": {
    "knowledge_graph_v001.json": "...",
    "evidence_index_v001.json": "..."
  },
  "started_at": "2026-07-28T12:00:00Z",
  "completed_at": "2026-07-28T12:10:00Z"
}
```

Il manifest non deve contenere:

- API key;
- segreti;
- prompt contenenti dati raw non necessari;
- interi file sorgente.

Per ogni step delegabile, `step_execution` deve registrare:

- `mode`: `manual`, `automatic` o `exceptions_only`;
- operatore e timestamp della scelta;
- configurazione o profilo applicato;
- stato ed eventuali eccezioni;
- checkpoint in cui l'automazione si è fermata.

L'assenza di una voce non equivale a una delega implicita.

`calibration_profiles` registra per operation ID e hash del profilo, ID e hash
del ProviderConfig, qualifier generation/embedding e relativa applicabilità,
lingua, feature/schema e ID/hash del dataset congelato; l'assenza o un mismatch
forza `review_required`.

`raw_accounting` riferisce il ledger append-only e deve dimostrare l'equazione
DC-DISPOSITION-001 separatamente per ogni `source_id` in `by_source`: top-level,
aggregato child e ogni parent tramite
`parent_groups_checked == parent_groups_balanced`. Per ogni sezione la somma
dei cinque `terminal_outcomes` deve coincidere con `inventoried`; i totali del
run sono la somma delle Source, non un contatore indipendente. Il ledger
append-only resta nel run store locale: il manifest ne conserva riferimento e
hash, ma non aggiunge un quarto file alla directory bundle definita da
DC-PUBLISH-001.

### DC-DELEGATION-001 — Delega append-only e step catalog

```json
{
  "delegation_id": "delegation_001",
  "run_id": "run_001",
  "step_id": "structured_selection",
  "scope": {
    "kind": "source",
    "source_id": "src_manual_accepted_002"
  },
  "mode": "exceptions_only",
  "config_hash": "...",
  "calibration_profile_id": null,
  "effective_checkpoint_id": "checkpoint_003",
  "exception_queue_limit": 100,
  "operator": "local_operator",
  "supersedes": null,
  "revokes": null,
  "created_at": "2026-07-28T12:00:00Z"
}
```

Catalogo stabile:

| `step_id` | Modalità ammesse | Condizioni |
|---|---|---|
| `structured_selection` | `manual`, `automatic`, `exceptions_only` | fogli, collection e colonne inventariati |
| `mapping_apply` | `manual`, `automatic`, `exceptions_only` | profilo compatibile o proposta completa; valori non inferibili restano manuali |
| `join_apply` | `manual`, `automatic`, `exceptions_only` | automatico o exceptions-only soltanto per JoinSpec già approvato e fingerprint compatibile; join nuovo, cambiato, many-to-many o oltre fan-out è manuale |
| `normalization_apply` | `manual`, `automatic`, `exceptions_only` | regole deterministiche versionate |
| `exact_deduplication` | `manual`, `automatic`, `exceptions_only` | soltanto chiavi esatte dichiarate |
| `candidate_auto_stage` | `manual`, `automatic`, `exceptions_only` | CalibrationProfile valido e nessuna guard |
| `nonblocking_review` | `manual`, `exceptions_only` | non può risolvere conflitti blocking |
| `advance_workflow` | `manual`, `automatic` | si arresta a ogni gate non delegabile |

Non sono delegabili:

- conferma dell'identità macchina;
- attribuzione dei file, eseguita dall'operatore tramite caricamento;
- preparazione PDF G1, che include sempre tutte le pagine;
- join nuovo o rischioso;
- conflitto blocking;
- override di guard simbolica;
- invenzione di proprietà obbligatoria;
- publish.

Semantica delle modalità:

- `manual`: si ferma prima di applicare la proposta;
- `automatic`: applica soltanto decisioni autorizzate e si ferma al primo
  elemento non autorizzabile del relativo scope;
- `exceptions_only`: completa gli elementi sicuri, accumula eccezioni
  non-blocking e sospende lo scope alla prima eccezione blocking.

Fonti indipendenti possono proseguire fino alla barriera di merge. Quando la
coda di uno scope raggiunge `exception_queue_limit`, si sospendono al
checkpoint successivo la source o la partizione coinvolta e gli stage che ne
dipendono; il default normativo è `100`. Le altre fonti indipendenti possono
proseguire fino alla barriera di merge. Dopo la risoluzione riprende soltanto
lo scope sospeso e gli stage dipendenti.

Una eccezione blocking locale ferma source o partizione coinvolta. Identità
macchina, conflitto globale blocking, guard ontologica e publish sono global
blocker e fermano il run al safe point.

Una modifica mid-run diventa efficace esclusivamente da un checkpoint
committed e non cambia retroattivamente output già committed. Revoca e cambio
di modalità sono nuovi eventi con `supersedes` o `revokes`; non cancellano la
storia. Output automatici restano reversibili tramite ReviewDecision fino al
publish.

### DC-CHECKPOINT-001 — Checkpoint, safe point e resume

```json
{
  "checkpoint_id": "checkpoint_018",
  "run_id": "run_001",
  "ordinal": 18,
  "stage_id": "semantic_generation",
  "scope": {
    "kind": "source",
    "source_id": "src_logs_001"
  },
  "work_unit_ids": ["ev_001", "ev_002", "ev_003"],
  "input_hash": "...",
  "stage_config_hash": "...",
  "model_call_ids": ["call_041"],
  "output_refs": ["candidate_batch_018"],
  "output_hashes": ["..."],
  "status": "committed",
  "prepared_at": "2026-07-28T12:03:58Z",
  "committed_at": "2026-07-28T12:04:00Z"
}
```

`scope` è una discriminated union con esattamente una forma:

- `{"kind": "source", "source_id": "..."}`;
- `{"kind": "partition", "source_id": "...", "partition_id": "..."}`;
- `{"kind": "run", "run_id": "..."}`;
- `{"kind": "bundle", "bundle_id": "..."}`.

Campi identificativi estranei alla variante sono vietati. Parsing,
normalizzazione, generation e approvazione del sottografo usano scope `source`
o `partition`; linking, merge e review multisource usano scope `run`; publish
usa scope `bundle`.

Una work unit atomica è:

- una source o chunk stabile durante parsing e normalizzazione;
- un insieme ordinato di EvidenceUnit durante generation;
- un candidate batch durante linking/merge;
- una decisione durante review;
- l'intero bundle durante publish.

Stati checkpoint:

- `prepared`;
- `committed`;
- `aborted`.

Un checkpoint è `committed` soltanto quando output, disposition, call
references, audit e checksum sono persistiti atomically. `prepared` non è un
safe point.

`Resume`:

- continua lo stesso run con identici input logici e config hash;
- salta ogni checkpoint `committed`;
- riusa una risposta modello già persistita;
- riparte dalla prima work unit senza checkpoint committed.

`Retry` ri-esegue soltanto una work unit fallita `same_run`; non autorizza
cambi di provider, modello, prompt, mapping, scope o input. Una modifica logica
crea un nuovo run e marca quello precedente `superseded`.

`Pause` richiede arresto cooperativo al safe point successivo ed è
riprendibile. `Cancel` è terminale. La UI `Interrompi` deve significare
`Pause`; `Cancel` è un'azione separata e confermata.

### DC-CALL-001 — Lifecycle delle chiamate modello

Prima dell'invio viene persistito un record con `call_id`, request hash,
idempotency key e stato `prepared`. Gli stati sono:

- `prepared`;
- `in_flight`;
- `response_persisted`;
- `consumed`;
- `failed`;
- `indeterminate`.

La risposta deve essere persistita localmente e hashata prima di costruire
candidate. Un crash dopo `response_persisted` deve riusare la risposta senza
una nuova chiamata. Un crash `in_flight` senza risposta persistita produce
`indeterminate`: l'adapter può riprovare con la stessa idempotency key, ma deve
registrare che il provider potrebbe aver contabilizzato due richieste.
Idempotenza semantica e deduplica degli output restano obbligatorie.

### DC-CACHE-001 — Matrice di invalidazione

| Modifica | Riutilizzabile | Invalidato |
|---|---|---|
| hash del file raw | nulla per la source cambiata | registrazione, parsing, EvidenceUnit, semantic text, cache e ogni downstream della source |
| identità/alias macchina | raw e attribuzione source | costanti di mapping, context, EvidenceUnit semantiche, semantic text, cache, candidate, merge, review e publish |
| versione adapter, encoding, header o opzioni parser | raw | RawUnit, EvidenceUnit e downstream della source |
| nuova versione della policy PDF all-pages | raw e pagine non cambiate | EvidenceUnit e downstream del documento interessato |
| mapping, join, normalizzatore o template | raw e profiling compatibile | EvidenceUnit, semantic text, embedding, candidate e downstream interessato |
| classe di autorità | raw, parsing e EvidenceUnit raw | support type, conflict, staging, merge, review e publish dipendenti |
| rimozione o ripristino operatore della Source | raw e parsing puro | eligibility della Source e downstream non committed |
| lingua qualificata | raw e parsing | semantic text, embedding, candidate e calibrazione |
| generation provider/model/prompt/schema o hash ProviderConfig | raw, mapping, semantic text ed embedding dimostrabilmente indipendente | model call, candidate generation, CalibrationProfile e downstream |
| embedding provider/model/version o hash ProviderConfig | raw, mapping e generation dimostrabilmente indipendente | embedding, linking, merge, CalibrationProfile e downstream |
| soglie o CalibrationProfile | embedding | staging, review e publish eligibility |
| decisione HITL | ingestion, semantic text ed embedding | CandidateGraphRevision, diff e publish |
| modalità di delega | tutti gli output committed | soltanto workflow dal checkpoint efficace |
| checksum ontologia differente | nulla è pubblicabile | run bloccato; non è ammessa migrazione implicita |

La cache key di ogni stage deve includere soltanto le dipendenze dichiarate
nella matrice. Un override deve mostrare prima del run quali righe invalida.

### DC-LANG-001 — Qualifica linguistica e grafo canonico

Ogni EvidenceUnit ha `detected`, confidence e `qualification`:

- `qualified_en`;
- `unqualified_it`;
- `unqualified_de`;
- `unknown`;
- `mixed`.

Input italiano, tedesco, unknown o mixed viene preservato, inventariato e
profilato. Non alimenta automaticamente campi canonici, embedding, linking,
merge o graph properties. In assenza di una traduzione approvata conclude il
trattamento con `NO_QUALIFIED_SEMANTIC_CLAIM` e apre un gap
`unqualified_language`; non scompare né viene dichiarato supportato.

Una traduzione è sempre un valore derivato e puntualmente revisionato.

```json
{
  "translation_id": "translation_001",
  "source_evidence_id": "ev_it_001",
  "source_language": "it",
  "target_language": "en",
  "original_text": "La pompa non si avvia.",
  "translated_text": "The pump does not start.",
  "provider_config_id": "provider_config_001",
  "model": "gpt-5.6-terra",
  "prompt_hash": "...",
  "locator_hash": "...",
  "status": "review_required",
  "decision_id": null
}
```

Stati: `review_required`, `approved`, `rejected`, `superseded`. Soltanto
`approved` può contribuire a semantic text e candidate, conservando il
riferimento al testo originale, provider, modello, prompt e locator. Poiché
IT/DE non ha calibrazione MVP, un candidate sostenuto dalla traduzione non può
essere auto-staged e resta soggetto a review. L'approvazione della singola
traduzione non cambia `unqualified_it` o `unqualified_de` e non equivale a
qualifica della lingua. Raw, quote, codici, ID, numeri e unità non vengono mai
tradotti.

Campi graph canonici in inglese:

- nomi, descrizioni e instruction text;
- categorie e vocabolari controllati;
- `asset_type`, `severity`, `action_kind`.

Restano invariati:

- tutti gli ID;
- brand e model;
- `ErrorCode.code`;
- `CorrectiveAction.source_title` e `source_reference`;
- raw, quote, unità e valori sorgente;
- i valori tecnici di `material_context`.

### DC-PROVIDER-001 — ProviderConfig canonico

```json
{
  "provider_config_id": "provider_config_001",
  "version": 1,
  "generation": {
    "provider": "openai",
    "model": "gpt-5.6-terra",
    "base_url": "https://api.openai.com/v1",
    "timeout_seconds": 120,
    "max_retries": 2
  },
  "embedding": {
    "provider": "openai",
    "model": "qualified-embedding-model",
    "base_url": "https://api.openai.com/v1",
    "dimensions": null
  },
  "required_capabilities": [
    "structured_output",
    "embedding",
    "usage_reporting"
  ],
  "secret_refs": {
    "openai": "OPENAI_API_KEY"
  },
  "data_egress_policy_id": "egress_001",
  "config_hash": "..."
}
```

I nomi modello nell'esempio rappresentano lo snapshot risolto della
configurazione, non un default hard-coded di dominio. Il record è versionato,
privo di secret e congelato nel run. Precedenza:

1. override esplicito del run;
2. environment;
3. configurazione applicativa;
4. default dichiarato.

Variabili canoniche:

- `KG_GENERATION_PROVIDER`, `KG_GENERATION_MODEL`,
  `KG_GENERATION_BASE_URL`;
- `KG_EMBEDDING_PROVIDER`, `KG_EMBEDDING_MODEL`,
  `KG_EMBEDDING_BASE_URL`;
- secret specifici del provider, fra cui `OPENAI_API_KEY`.

`MODEL_NAME` è soltanto fallback legacy per `KG_GENERATION_MODEL` quando la
variabile canonica è assente. Non può essere usato come embedding model. Due
valori canonici discordanti allo stesso livello sono errore di configurazione
e non una selezione implicita.

Il preflight verifica realmente per lo stage richiesto raggiungibilità,
modello, structured output, embedding, context limit e dimensione vettore.
Il semplice health HTTP non è sufficiente.

### DC-EGRESS-001 — Data egress per stage

Ogni endpoint non loopback è remoto. Il run congela una allowlist per stage e
la UI mostra il payload effettivo o una preview valore-per-valore prima del
primo invio remoto.

Il preflight verifica soltanto configurazione e capability e non invia alcun
contenuto sorgente.

| Stage | Contenuto remoto ammesso | Vietato di default |
|---|---|---|
| PDF semantic extraction | chunk necessari derivati dall'inventory all-pages, numero e heading | PDF o immagine completa |
| profiling/mapping | header, tipi, statistiche e campione limitato di campi inclusi | tabella completa, colonne escluse |
| translation | il solo testo selezionato, lingua sorgente/target, prompt versionato e locator opaco | altre righe, altre fonti, codici e unità da tradurre |
| generation | semantic text role-specific, codici esatti, contesto minimo, authority e locator opaco | raw record completo, join key, timestamp e campi esclusi |
| embedding | esattamente il semantic text mostrato in preview | raw, ID tecnici e metadata non selezionati |
| repair | output invalido, errori schema e lo stesso contesto minimo della call originaria | nuove parti della source |
| chat | query, sottografo della versione selezionata e snippet evidence necessari | candidate graph, versioni diverse, file raw interi |

Il fake provider dei contract test deve acquisire il payload e verificare che
contenga soltanto campi allowlisted. Log e manifest registrano hash, nomi dei
campi, dimensione, provider e call ID, non il payload raw né segreti.

## 14. Pubblicazione e versionamento

### DC-PUBLISH-001 — Truth table e bundle atomico

La pubblicabilità è calcolata con questa tabella; nessun implementatore può
reinterpretare `blocking` o uno stato aperto.

| Oggetto | Stato/verdetto | Entra nel delta | Blocca publish |
|---|---|---:|---:|
| Candidate | `proposed` | no | sì |
| Candidate | `review_required` | no | sì |
| Candidate | `auto_staged` senza decisione aggregata | no | sì |
| Candidate | `approved` | sì | no |
| Candidate | `rejected` | no | no |
| Candidate | `deferred` o `quarantined`, `blocking=false`, con disposition/gap | no | no |
| Candidate | `deferred` o `quarantined`, `blocking=true` | no | sì |
| Candidate | `superseded` | no | no |
| Conflict | `open`, `blocking=true` | no | sì |
| Conflict | `open`, `blocking=false` | no; resta sidecar | no |
| Conflict | `resolved` | secondo decisione | no |
| KnowledgeGap | `open`, `blocking=true` | no | sì |
| KnowledgeGap | `open`, `blocking=false` | no; resta sidecar | no |
| Validazione | qualunque errore DC-GRAPH-005 | no | sì |
| Gate umano | conferma publish assente | no | sì |

La conferma finale trasforma atomicamente gli `auto_staged` inclusi in
decisioni aggregate `approved`, quindi riesegue la truth table e il validatore.

L'unità pubblicata è una directory bundle contenente esattamente:

```text
knowledge_graph_v001.json
evidence_index_v001.json
run_manifest_v001.json
```

La prima versione è `V001`; il file stem è `v001`. Le versioni successive
incrementano monotonicamente e conservano almeno tre cifre (`V002`, `V010`,
`V999`, `V1000`). Non sono ammesse etichette non zero-padded, né riuso o
overwrite.

Protocollo obbligatorio:

1. acquisire un lock esclusivo per workspace;
2. materializzare i tre file in una staging directory dello stesso filesystem;
3. ordinare deterministicamente nodi, relazioni, mappe e lineage;
4. validare grafo, property evidence, riferimenti, base version e truth table;
5. calcolare gli SHA-256 di graph ed evidence index e registrarli nel manifest;
6. fsync di file e directory secondo le primitive disponibili;
7. rinominare atomicamente la directory di staging al nome finale;
8. aggiornare il puntatore `latest` soltanto dopo il rename;
9. registrare separatamente l'hash del manifest nel publication registry.

Graph, evidence index e manifest devono avere stessi `bundle_id`, `graph_id` e
versione. Una staging directory residua dopo crash è `aborted`, non
`published`, e può essere ispezionata o rimossa in modo recuperabile. Un lock
concorrente deve fallire o accodare la seconda pubblicazione; non può scegliere
la stessa versione.

### DC-VERSION-001

Ogni pubblicazione incrementa `VNNN` secondo DC-PUBLISH-001 senza
sovrascrivere versioni precedenti.

### DC-VERSION-002

Il diff tra due versioni deve distinguere:

- nodi creati, modificati, rimossi e invariati;
- relazioni create e rimosse;
- evidenze aggiunte o rimosse;
- merge e split;
- knowledge gap aperti o chiusi.

### DC-VERSION-003

La rimozione di conoscenza pubblicata richiede decisione esplicita e deve
restare visibile nell'audit. Una nuova versione è cumulativa rispetto a
`base_graph_version`: ogni perdita deve corrispondere a un candidate
`withdraw` o `supersede` approvato e a un tombstone.

`run_input_source_ids` elenca le fonti del run; `contributing_source_ids`
elenca quelle che sostengono almeno un claim nella versione. Entrambe devono
essere distinte da tutte le fonti storiche del workspace.
