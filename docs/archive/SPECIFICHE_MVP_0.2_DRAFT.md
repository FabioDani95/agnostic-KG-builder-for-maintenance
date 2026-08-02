# BOZZA ARCHIVIATA — Specifiche Maintenance Knowledge Graph Builder 0.2

> Documento non normativo, conservato esclusivamente come storico. Non deve
> essere usato per pianificare o implementare il prodotto. La specifica vigente
> è `/SPECIFICHE_MVP.md` e rimanda al pacchetto normativo in `docs/specs/`.

## 1. Informazioni sul documento

| Campo | Valore |
|---|---|
| Prodotto | Maintenance Knowledge Graph Builder |
| Tipo | MVP locale avanzato |
| Versione specifiche | 0.2 |
| Stato | Baseline funzionale da validare |
| Data | 2026-07-28 |
| Backend richiesto | FastAPI |
| Grafo pubblicato | JSON |
| Ontologia | `Core_Ontology`, versione `2.0` |

## 2. Obiettivo

L'applicazione deve trasformare documenti e dati operativi eterogenei relativi a una singola macchina in un unico knowledge graph di troubleshooting conforme all'ontologia fornita.

L'MVP deve:

- funzionare in locale con backend FastAPI e frontend web;
- importare più PDF, CSV, XLSX e JSON riferiti alla stessa macchina;
- gestire documenti, file, tabelle e schemi diversi senza dipendere da uno specifico tipo di macchina;
- far convergere tutte le fonti dello stesso workspace in un solo grafo;
- conservare integralmente e rendere tracciabili le evidenze originali;
- normalizzare, deduplicare, raggruppare e interpretare i record;
- estrarre conoscenza tramite una pipeline neurosimbolica;
- applicare vincoli simbolici rigidi derivati dall'ontologia;
- coinvolgere un operatore umano nei passaggi decisionali;
- pubblicare un grafo versionato in formato JSON;
- permettere di ispezionare il grafo e le evidenze che lo supportano;
- includere una chat diagnostica minima, read-only, usata soprattutto per testare la fruibilità del grafo.

Il focus principale dell'MVP è la robustezza e la misurabilità della trasformazione:

> fonti documentali e strutturate → evidenze canoniche → candidati ontologici → revisione umana → unico knowledge graph JSON della macchina.

## 3. Risultato atteso

Il risultato non è uno storico di singoli eventi rappresentati come nodi, ma una base di conoscenza generalizzata di troubleshooting.

Più documenti, pagine, tabelle e record possono quindi supportare la stessa conoscenza. Per esempio, un manuale e cento log simili possono consolidarsi in:

- un `Symptom`;
- un `FailureMode`;
- una o più `CorrectiveAction`;
- le relazioni ontologiche tra queste entità;
- un indice separato contenente tutte le evidenze documentali e strutturate di supporto.

I singoli documenti, log, incidenti, timestamp, punteggi di confidenza e decisioni umane non diventano nuovi tipi di nodo del grafo. Restano nello storage operativo e nell'indice delle evidenze.

Per il primo MVP il grafo contiene esattamente un `Asset`, che rappresenta la macchina oggetto del workspace. I suoi componenti e sottosistemi possono essere estratti e collegati usando l'ontologia invariata.

## 4. Perimetro MVP

### 4.1 Incluso

- Esecuzione locale.
- Backend FastAPI.
- Frontend web locale.
- Un singolo workspace locale.
- Esattamente una macchina, rappresentata da un unico nodo `Asset`.
- Import di uno o più file per batch.
- Più batch e più fonti incrementali riferiti alla stessa macchina.
- PDF nativi e PDF scansionati.
- Estrazione testo, tabelle e OCR selettivo dai PDF.
- CSV.
- XLSX con uno o più fogli.
- JSON e JSON Lines.
- Rilevamento e profiling delle tabelle.
- Mapping manuale assistito.
- Mapping riutilizzabili per strutture già approvate.
- Join espliciti tra tabelle.
- Modello canonico delle evidenze.
- Validazione strutturale e semantica dei record.
- Normalizzazione di date, numeri, unità e valori nulli.
- Deduplica esatta.
- Merge probabilistico e clustering.
- Estrazione semantica basata su modelli.
- Embedding e retrieval di entità esistenti.
- Validazione simbolica contro l'ontologia.
- Human in the Loop.
- Versionamento del grafo.
- Merge di tutte le fonti approvate in un unico grafo JSON della macchina.
- Export del grafo in JSON.
- Indice di provenienza ed evidenza separato dal grafo.
- Visualizzazione e ricerca del grafo.
- Chat diagnostica minima e read-only.
- Provider OpenAI come default.
- Architettura predisposta per provider e modelli locali.
- Inglese come lingua canonica e lingua validata dell'MVP.

### 4.2 Predisposto ma non richiesto per la prima release

- Input in italiano.
- Input in tedesco.
- Risposte diagnostiche in italiano o tedesco.
- Traduzione automatica controllata.
- Provider locali aggiuntivi.
- Calibrazione separata delle soglie per italiano e tedesco.

La predisposizione significa che lingua e provider non devono essere hard-coded nella logica di dominio. Non significa che italiano e tedesco debbano superare i criteri di accettazione della prima release.

### 4.3 Escluso

- DOCX e altri documenti Word.
- File e-mail nativi `.msg` e `.eml`.
- Collegamento diretto a caselle e-mail.
- Immagini standalone.
- Più macchine nello stesso workspace.
- Celle e linee come asset centrali nel primo MVP.
- Database a grafo come Neo4j.
- Account utente.
- Autenticazione e autorizzazione.
- Organizzazioni e multi-tenancy.
- Gestione di più workspace dall'interfaccia.
- Integrazioni live con CMMS, ERP, PLC o SCADA.
- Streaming real-time.
- Modifica automatica del grafo da parte della chat.
- Esecuzione automatica di interventi sulla macchina.
- Addestramento o fine-tuning di modelli.
- Agente diagnostico completo di produzione.

## 5. Principi vincolanti

### 5.1 Ontologia immutabile per il singolo run

Il file `ontology_schema.JSON` è il contratto del grafo.

La pipeline:

- deve caricarlo a runtime;
- deve verificarne validità e checksum;
- non deve introdurre tipi di nodo, proprietà o relazioni non dichiarati;
- deve registrare versione e checksum in ogni manifest di esecuzione e pubblicazione;
- deve bloccare la pubblicazione se il grafo non è conforme.

L'ontologia può essere aggiornata in futuro come decisione esplicita di prodotto, ma non può essere modificata implicitamente da un modello, da un mapping o da una revisione umana.

### 5.2 Agnosticità della sorgente

La pipeline non deve contenere regole applicative dipendenti da ABB IRC5, da una specifica macchina o da una specifica tipologia documentale.

Eventuali mapping specifici per una sorgente sono configurazioni salvate, non logica hard-coded.

L'agnosticità richiesta copre quattro livelli:

1. **Famiglia di sorgente:** documentale o strutturata.
2. **Formato:** PDF, CSV, XLSX o JSON.
3. **Struttura:** layout documentali e nomi, ordine, tipo e numero di colonne variabili.
4. **Dominio macchina:** robot, macchine utensili, impianti farmaceutici, medicali, presse a iniezione e altre apparecchiature.

### 5.3 Separazione tra evidenza e conoscenza

Le evidenze possono essere incomplete, rumorose o contraddittorie. Il grafo pubblicato deve invece essere coerente e completo rispetto all'ontologia.

Sono pertanto separati:

- raw input;
- record canonici;
- gruppi e cluster;
- candidati semantici;
- decisioni umane;
- grafo pubblicato;
- indice delle evidenze.

### 5.4 Nessuna perdita silenziosa

Nessuna riga o oggetto deve essere scartato senza:

- stato esplicito;
- motivazione;
- riferimento alla posizione originale;
- possibilità di ispezione.

### 5.5 Precisione prima della copertura

Un falso merge o una relazione causale errata sono più dannosi di un candidato non ancora collegato.

Le soglie e il workflow devono privilegiare:

- precisione;
- tracciabilità;
- reversibilità;
- revisione delle ambiguità.

### 5.6 Riproducibilità

Ogni risultato deve poter essere ricondotto a:

- input;
- mapping;
- configurazione della pipeline;
- ontologia;
- provider e modelli;
- versioni dei prompt;
- output dei modelli;
- decisioni umane.

## 6. Ontologia target

### 6.1 Tipi di nodo ammessi

| Tipo | Identificativo | Scopo |
|---|---|---|
| `Asset` | `asset_id` | Macchina o asset tecnico oggetto del troubleshooting |
| `Component` | `component_id` | Componente fisico, software o sottosistema |
| `Symptom` | `symptom_id` | Manifestazione osservabile |
| `FailureMode` | `failure_mode_id` | Causa o meccanismo tecnico sottostante |
| `CorrectiveAction` | `action_id` | Procedura o escalation correttiva |
| `ErrorCode` | `error_code_id` | Codice o allarme generato dalla macchina |

### 6.2 Relazioni ammesse

| Relazione | Dominio | Range |
|---|---|---|
| `HAS_COMPONENT` | `Asset` | `Component` |
| `MAY_INDICATE` | `Symptom` | `FailureMode` |
| `AFFECTS` | `FailureMode` | `Component` |
| `RESOLVED_BY` | `FailureMode` | `CorrectiveAction` |
| `GENERATES_ERROR` | `Asset` | `ErrorCode` |
| `INDICATES` | `ErrorCode` | `FailureMode` |

### 6.3 Macchina centrale e componenti

L'ontologia centrale viene utilizzata integralmente e senza modifiche.

Nel primo MVP:

- il workspace contiene un solo nodo `Asset`, corrispondente alla macchina;
- i nodi `Component` rappresentano parti, moduli o sottosistemi della macchina quando supportati dalle evidenze;
- `Asset HAS_COMPONENT Component` collega la macchina ai suoi componenti;
- `FailureMode AFFECTS Component` specifica dove agisce un guasto;
- nessun tipo di nodo, proprietà o relazione viene rimosso, disabilitato o aggiunto rispetto a `ontology_schema.JSON`;
- non è obbligatorio inventare componenti quando la sorgente non ne fornisce evidenza sufficiente.

### 6.4 Informazioni che non appartengono al grafo

Rimangono nello storage operativo o nell'indice delle evidenze:

- documento e pagina;
- singolo log;
- incidente;
- timestamp dell'evento;
- source system;
- file, foglio, tabella e riga;
- valore grezzo;
- confidence score;
- support count;
- stato di revisione;
- spiegazione del modello;
- annotazioni dell'operatore;
- embedding;
- alias multilingua.

## 7. Architettura logica

```mermaid
flowchart LR
    A["Workspace di una macchina"] --> B["Upload PDF / CSV / XLSX / JSON"]
    B --> C1["Document adapter<br/>testo, tabelle, OCR, scoping"]
    B --> C2["Structured adapter<br/>profiling, mapping, join"]
    C1 --> D["Evidence Unit canoniche"]
    C2 --> D
    D --> E["Deduplica, estrazione e entity linking"]
    E --> F["Merge cross-source"]
    F --> G["Validazione simbolica"]
    G --> H{"HITL: candidati e conflitti"}
    H --> I{"HITL: pubblicazione"}
    I --> J["Unico Knowledge Graph JSON della macchina"]
    J --> K["Explorer e chat di test"]
```

### 7.1 Componenti

#### Backend FastAPI

Responsabile di:

- upload;
- classificazione e inventario delle sorgenti;
- parsing documentale, OCR e scoping;
- profiling;
- mapping;
- esecuzione della pipeline;
- persistenza dello stato;
- integrazione con i model provider;
- validazione ontologica;
- revisione;
- pubblicazione;
- query sul grafo;
- chat diagnostica di test.

#### Frontend web

Responsabile di:

- onboarding della macchina;
- caricamento dei file;
- inventario delle sorgenti documentali e strutturate;
- scoping dei PDF;
- anteprima delle tabelle;
- configurazione dei mapping;
- visualizzazione degli errori;
- monitoraggio dei run;
- revisione dei candidati;
- pubblicazione;
- esplorazione del grafo;
- utilizzo della chat minima.

Il framework frontend viene deciso nel piano di sviluppo.

#### Storage locale

Per l'MVP:

- filesystem per file originali, export, manifest e cache;
- SQLite per stato operativo, record canonici, candidati e decisioni;
- file JSON per le versioni pubblicate del grafo e dell'indice delle evidenze.

SQLite non rappresenta il knowledge graph pubblico; serve solo a rendere la pipeline riprendibile e auditabile.

#### Model Provider Adapter

Interfaccia astratta per:

- estrazione strutturata;
- embedding;
- health check;
- batching;
- timeout;
- retry;
- reporting dell'utilizzo;
- identificazione di provider e modello.

Il provider predefinito è OpenAI.

La configurazione esistente comprende:

- `OPENAI_API_KEY`;
- `MODEL_NAME=gpt-5.6-terra`.

La chiave:

- deve essere letta solo dal backend;
- non deve essere restituita da endpoint;
- non deve apparire nei log;
- non deve essere inviata al frontend;
- non deve essere salvata nei manifest.

Il modello di embedding deve essere configurabile separatamente dal modello di estrazione.

## 8. Concetti operativi

### 8.1 Workspace

L'MVP gestisce un singolo workspace locale.

Il workspace contiene:

- un solo asset centrale, corrispondente alla macchina;
- documenti e file strutturati caricati;
- batch;
- mapping;
- record canonici;
- run;
- candidati;
- decisioni;
- versioni del grafo.

Non è prevista una UI per creare, selezionare o amministrare più workspace.

Tutti i contenuti ammessi nel workspace devono riferirsi alla stessa macchina. Una fonte relativa a un'altra macchina deve essere esclusa o caricata in un'istanza separata dell'applicazione.

### 8.2 Batch

Un batch è un insieme di uno o più file caricati insieme per uno stesso run logico e per la macchina del workspace.

Un batch:

- ha un identificativo univoco;
- conserva hash e metadati dei file;
- può essere riprocessato;
- può usare mapping già approvati;
- non modifica il grafo pubblicato fino all'approvazione finale.

### 8.3 Tabella sorgente

È un'unità tabellare scoperta in un file:

- un CSV corrisponde normalmente a una tabella;
- ogni foglio XLSX è una tabella candidata;
- ogni array omogeneo JSON è una tabella candidata;
- un flusso JSONL è una tabella.

### 8.4 Documento sorgente

È un PDF caricato nel workspace.

Un documento:

- conserva hash, nome e file originale;
- può contenere testo nativo, immagini, tabelle o pagine scansionate;
- viene suddiviso in evidence unit con locator di pagina e, quando disponibile, sezione;
- attraversa uno scoping documentale prima dell'estrazione semantica;
- contribuisce allo stesso grafo dei dati strutturati.

### 8.5 Mapping profile

È la configurazione approvata che associa una struttura sorgente al Canonical Evidence Model.

Il profilo è identificato da:

- formato;
- fingerprint dello schema;
- nomi e tipi delle colonne;
- mapping;
- ruoli delle tabelle;
- regole di join;
- colonne incluse ed escluse;
- campi usati per il testo semantico;
- lingua attesa.

Un profilo può essere riutilizzato solo se il fingerprint è compatibile. Differenze sostanziali richiedono nuova approvazione.

### 8.6 Evidence unit

È la rappresentazione canonica e tracciabile di un'unità informativa proveniente da qualsiasi sorgente.

Può rappresentare:

- un passaggio o una tabella di un PDF;
- una riga CSV;
- una riga o area di un foglio Excel;
- un oggetto o path JSON.

### 8.7 Evidence group

È un gruppo reversibile di record che sembrano rappresentare:

- lo stesso evento riportato da più fonti;
- eventi duplicati;
- occorrenze semanticamente equivalenti utili al consolidamento.

L'evidence group non è un nodo del grafo.

### 8.8 Candidate

È una proposta di:

- nuovo nodo;
- match con nodo esistente;
- nuova relazione;
- merge di entità;
- modifica di proprietà.

Un candidate può essere incompleto. Un nodo pubblicato non può esserlo.

### 8.9 Published graph

È una versione immutabile del singolo grafo della macchina, conforme all'ontologia e salvata come JSON.

## 9. Workflow e stati

### 9.1 Stati del batch

| Stato | Significato |
|---|---|
| `uploaded` | File memorizzati e verificati |
| `profiled` | Documenti, tabelle e statistiche disponibili |
| `mapping_required` | È necessaria una decisione umana |
| `mapped` | Mapping approvato |
| `processing` | Pipeline in esecuzione |
| `review_required` | Esistono candidati o conflitti da revisionare |
| `ready_to_publish` | Tutti i blocchi sono risolti |
| `published` | È stata creata una versione del grafo |
| `failed` | Errore tecnico non recuperato |
| `cancelled` | Run interrotto intenzionalmente |

### 9.2 Stati del record

| Stato | Significato |
|---|---|
| `accepted` | Record canonico valido |
| `accepted_with_warnings` | Valido ma con anomalie non bloccanti |
| `quarantined` | Richiede correzione o decisione |
| `duplicate` | Duplicato esatto di un record noto |
| `excluded` | Escluso esplicitamente dall'operatore |
| `failed` | Non elaborabile per errore tecnico |

### 9.3 Ripresa

La pipeline deve poter ripartire dall'ultimo step completato senza:

- ricaricare il file;
- ripetere chiamate modello già memorizzate in cache;
- perdere decisioni umane;
- duplicare candidati.

## 10. Ingestion

### 10.1 Upload

Il frontend deve permettere:

- selezione multipla di file;
- caricamento congiunto di PDF, CSV, XLSX e JSON;
- visualizzazione del tipo, dimensione, hash e stato di processamento;
- rimozione di un file prima dell'avvio;
- avvio del profiling o dello scoping coerente con la sorgente;
- rilevamento di un file già caricato.

### 10.2 Idempotenza

Ogni file deve avere un hash crittografico del contenuto.

Lo stesso file:

- non deve essere duplicato nello storage;
- può essere associato a un nuovo batch;
- non deve causare nuove elaborazioni semantiche se configurazione, ontologia, mapping e modelli non sono cambiati.

### 10.3 PDF

La pipeline PDF riutilizza le capacità già presenti nella base applicativa:

- estrazione del testo nativo;
- estrazione delle tabelle;
- OCR selettivo quando il testo non è disponibile o sufficiente;
- rilevamento delle pagine rilevanti;
- cut plan e chunking;
- preservazione del riferimento alla pagina;
- evidence grounding tramite citazione verificabile.

Il sistema deve:

- accettare più PDF nello stesso workspace;
- evitare di creare un grafo separato per documento;
- registrare per ogni evidence unit documento, pagina, sezione se disponibile e citazione;
- permettere all'operatore di includere o escludere pagine o sezioni;
- segnalare pagine non leggibili o con OCR incerto;
- conservare il testo estratto e il metodo di estrazione;
- alimentare lo stesso core semantico usato dalle sorgenti strutturate.

Non è richiesta la comprensione completa di schemi tecnici e diagrammi privi di testo.

### 10.4 CSV

Il parser deve:

- rilevare encoding;
- rilevare separatore tra almeno virgola, punto e virgola, tab e pipe;
- gestire campi quotati;
- gestire newline all'interno di campi quotati;
- preservare il numero di riga;
- segnalare righe con larghezza differente;
- non assumere che una riga con larghezza corretta sia semanticamente valida;
- permettere la scelta manuale di encoding, separatore e header.

### 10.5 XLSX

Il parser deve:

- elencare tutti i fogli;
- permettere inclusione o esclusione del foglio;
- rilevare la possibile riga di intestazione;
- individuare aree vuote;
- preservare numero di foglio, riga e colonna;
- gestire celle numeriche, testo, date, boolean e formule usando il valore disponibile;
- segnalare formule prive di valore calcolato.

Non è richiesto il supporto a macro, grafici o formattazione.

### 10.6 JSON

Sono supportati:

- array di oggetti;
- JSON Lines;
- oggetto con uno o più array di oggetti;
- oggetti annidati che possono essere appiattiti tramite mapping esplicito.

Il sistema deve:

- mostrare i path JSON;
- proporre gli array tabellari;
- preservare il JSON originale;
- impedire esplosioni uno-a-molti implicite;
- richiedere una decisione per array annidati.

### 10.7 File non supportati

Un file non supportato deve essere rifiutato prima del profiling con messaggio esplicito.

## 11. Table discovery e profiling

Per ogni tabella il sistema deve calcolare almeno:

- numero di record;
- numero di colonne;
- tipo inferito per colonna;
- percentuale di valori nulli;
- cardinalità;
- esempi;
- valori minimi e massimi per numeri e date;
- distribuzione dei valori per colonne a bassa cardinalità;
- percentuale di valori non conformi al tipo prevalente;
- possibili identificativi;
- possibili timestamp;
- possibili riferimenti ad asset;
- possibili colonne testuali;
- possibili codici errore;
- possibili valori e unità;
- possibili colonne di azione ed esito;
- lingua prevalente stimata.

Il profiler deve generare warning per:

- duplicati di chiavi candidate;
- date non interpretabili;
- numeri contenenti testo;
- unità incoerenti;
- valori fuori dominio;
- campi JSON non validi;
- valori apparentemente spostati;
- colonne che cambiano significato tra record;
- identificativi semanticamente incompatibili con la colonna.

Il CSV di esempio contiene record formalmente larghi 39 colonne ma semanticamente disallineati. Questo caso deve essere parte dei test di regressione.

Per ogni PDF il sistema deve rendere disponibili almeno:

- numero di pagine;
- presenza di testo nativo;
- pagine sottoposte a OCR;
- pagine o sezioni proposte per inclusione;
- qualità e quantità del testo estratto;
- tabelle individuate;
- lingua prevalente;
- warning di estrazione.

## 12. Mapping Human in the Loop

### 12.1 Gate documentale

Per i PDF l'operatore deve poter:

- verificare l'identità della macchina a cui il documento si riferisce;
- approvare o correggere lo scoping;
- includere o escludere pagine;
- ispezionare testo e tabelle estratti;
- vedere quali pagine richiedono OCR;
- bloccare una fonte errata o riferita a un'altra macchina.

### 12.2 Ruoli delle tabelle

L'operatore può assegnare uno o più ruoli:

- `event_log`;
- `measurement`;
- `maintenance_record`;
- `asset_master`;
- `component_master`;
- `error_catalog`;
- `generic_evidence`;
- `excluded`.

Il ruolo serve a migliorare le proposte, ma non crea nuovi tipi ontologici.

### 12.3 Funzioni della schermata

La schermata di mapping deve permettere:

- anteprima di almeno 100 record;
- selezione della riga header;
- correzione dei tipi;
- inclusione ed esclusione di colonne;
- mapping delle colonne;
- concatenazione controllata di campi testuali;
- configurazione della lingua;
- definizione di valori costanti;
- definizione di chiavi;
- definizione di join;
- anteprima del record canonico risultante;
- validazione prima del salvataggio;
- salvataggio del mapping profile.

### 12.4 Join

I join devono essere espliciti.

Devono essere definiti:

- tabella sinistra e destra;
- colonne chiave;
- cardinalità attesa;
- comportamento in caso di chiave mancante;
- comportamento in caso di più match.

Un join uno-a-molti non deve duplicare silenziosamente il record principale. Deve produrre una lista canonica o richiedere una strategia approvata.

## 13. Canonical Evidence Model

Il modello canonico è indipendente dall'ontologia e dal formato sorgente. La stessa struttura rappresenta evidenze documentali e strutturate tramite un locator tipizzato.

Una rappresentazione logica minima è:

```json
{
  "evidence_id": "ev_...",
  "batch_id": "batch_...",
  "source": {
    "source_id": "source_...",
    "source_kind": "csv",
    "file_id": "file_...",
    "file_name": "machine_logs.csv",
    "source_system": "IRC5_event_log",
    "source_record_id": "WO-..."
  },
  "locator": {
    "kind": "table_row",
    "table_id": "table_...",
    "table_name": "machine_logs",
    "row": 102,
    "columns": ["event_name", "description", "action"]
  },
  "language": {
    "detected": "en",
    "confidence": 0.99
  },
  "record_type": "event_log",
  "occurred_at": "2026-01-01T10:00:00Z",
  "observed_at": "2026-01-01T10:01:00Z",
  "asset_hints": {
    "asset_id": "asset_...",
    "name": "IRC5",
    "brand": "ABB",
    "model": "IRC5",
    "asset_type": "robot_controller"
  },
  "component_hints": [
    {
      "component_id": "comp_...",
      "name": "Axis 3 brake"
    }
  ],
  "event": {
    "name": "brake_release_fault",
    "category": "fault",
    "status": "closed",
    "severity": "ERROR"
  },
  "texts": {
    "title": "...",
    "observation": "...",
    "action": "...",
    "outcome": "...",
    "semantic_text": "..."
  },
  "error_codes": [
    {
      "code": "38001",
      "raw": "38001"
    }
  ],
  "measurements": [
    {
      "name": "brake_release_voltage",
      "value": 21.8,
      "unit": "VDC",
      "threshold_value": 24.0,
      "threshold_unit": "VDC"
    }
  ],
  "attributes": {},
  "quality_flags": [],
  "raw_payload": {}
}
```

Per un PDF, lo stesso contratto usa ad esempio:

```json
{
  "source": {
    "source_id": "source_manual_01",
    "source_kind": "pdf",
    "file_id": "file_manual_01",
    "file_name": "maintenance_manual.pdf"
  },
  "locator": {
    "kind": "pdf_page",
    "page": 42,
    "section": "Troubleshooting",
    "quote": "..."
  }
}
```

### 13.1 Requisiti

- `evidence_id` deve essere stabile e deterministico.
- `source.source_id`, `source.source_kind`, `source.file_id` e `locator.kind` sono obbligatori.
- Il locator deve identificare in modo deterministico la pagina, riga, cella o path originale coerente con la sorgente.
- `raw_payload` deve preservare il record originale.
- Almeno uno tra testo osservativo, errore, misura o azione deve essere presente perché il record sia semanticamente elaborabile.
- Un record privo di contenuto semantico può essere conservato ma non inviato al modello.
- I campi non mappati rimangono in `raw_payload`.
- Informazioni inferite non devono sovrascrivere i valori raw.

### 13.2 Autorità delle sorgenti

Ogni evidenza deve dichiarare una classe di autorità:

- `normative`: manuali e procedure ufficiali;
- `observational`: log ed eventi macchina;
- `operational`: rapporti di manutenzione e intervento;
- `informal`: comunicazioni tecniche non formalizzate, quando saranno supportate.

Le fonti possono corroborarsi o contraddirsi.

La pipeline:

- non deve sovrascrivere silenziosamente una conoscenza normativa con una osservazione;
- deve conservare separatamente le evidenze concordanti e discordanti;
- deve generare un conflitto revisionabile quando fonti autorevoli sono incompatibili;
- deve permettere di scegliere una fonte primaria per le proprietà che lo richiedono;
- deve registrare la decisione umana nell'evidence index.

## 14. Machine onboarding

Prima di caricare o processare le fonti deve essere definita la macchina del workspace. Prima della pubblicazione deve esistere esattamente un `Asset` completo.

La macchina può essere:

- creato da una tabella master;
- proposto dalla pipeline;
- completato manualmente tramite frontend.

Poiché l'ontologia richiede `name`, `description`, `brand` e `model`, la pubblicazione deve essere bloccata se questi campi mancano.

Ogni evidenza semanticamente utilizzata deve essere:

- associata all'unica macchina del workspace;
- oppure esplicitamente esclusa dalla pubblicazione.

Se una fonte sembra riferirsi a una macchina differente:

- il run non deve associarla automaticamente;
- la fonte entra in quarantena;
- l'operatore può escluderla o correggere l'onboarding;
- non è possibile creare un secondo `Asset` nello stesso workspace.

Non è richiesto un sistema di organizzazioni, siti o permessi.

## 15. Validazione e normalizzazione

### 15.1 Livelli di validazione

1. **File:** tipo, leggibilità, integrità.
2. **Tabella:** header, larghezza, schema.
3. **Record:** tipi e campi.
4. **Semantica:** compatibilità tra campo e valore.
5. **Ontologia:** candidate nodes e relations.

### 15.2 Date

- Il valore originale deve essere preservato.
- Se timezone e offset sono disponibili, la forma canonica è UTC ISO 8601.
- Una timezone mancante non deve essere inventata.
- Un valore ambiguo deve produrre un flag.
- L'imputazione richiede una regola visibile o una decisione umana.

### 15.3 Numeri

- Separatore decimale e migliaia devono essere rilevati.
- Un valore non interpretabile non deve diventare zero.
- Testo trovato in un campo numerico deve produrre errore o warning.
- Il raw value deve essere preservato.

### 15.4 Unità

- Le unità devono essere normalizzate tramite un dizionario configurabile.
- La conversione avviene solo se unità e dimensione sono certe.
- Unità incompatibili devono bloccare il confronto con la soglia.
- Valore, unità e soglia rimangono distinti.

### 15.5 Severità

Per l'MVP si usa il vocabolario canonico:

- `INFO`;
- `WARNING`;
- `ERROR`;
- `CRITICAL`.

Valori sorgente differenti richiedono una regola di mapping. In caso di evidenze contrastanti, la severità pubblicata è proposta dalla pipeline e revisionabile.

### 15.6 Valori nulli

Stringa vuota, `null`, `N/A`, `NA`, `-` e valori equivalenti possono essere normalizzati a null solo tramite regole visibili e configurabili.

### 15.7 Quality flags

I flag devono essere codici strutturati, non testo libero separato da virgole.

Esempi:

- `MISSING_REQUIRED_SOURCE_FIELD`;
- `INVALID_DATE`;
- `INVALID_NUMBER`;
- `UNIT_MISMATCH`;
- `POSSIBLE_COLUMN_SHIFT`;
- `UNKNOWN_LANGUAGE`;
- `AMBIGUOUS_ASSET`;
- `SEMANTIC_TEXT_RECONSTRUCTED`;
- `MODEL_OUTPUT_REPAIRED`;
- `LOW_CONFIDENCE_LINK`;
- `UNMAPPED_FAILURE_MODE`.

## 16. Deduplica e merge

### 16.1 Deduplica esatta

Un record è duplicato esatto quando soddisfa una regola deterministica, per esempio:

- stesso source system e source record ID;
- stesso file hash e row locator;
- stesso hash del payload canonico normalizzato.

La deduplica esatta può essere automatica.

### 16.2 Merge probabilistico di record

Il merge probabilistico deve usare una combinazione di:

- asset;
- componente;
- finestra temporale;
- source system;
- source record ID;
- error code;
- nome evento;
- misure;
- testo;
- similarità embedding;
- azione e outcome.

Vincoli incompatibili devono impedire il merge anche in presenza di alta similarità testuale.

Esempi di vincoli incompatibili:

- riferimenti a una macchina differente da quella del workspace;
- error code mutuamente esclusivi;
- componenti chiaramente distinti;
- eventi temporalmente incompatibili quando il cluster rappresenta lo stesso incidente.

### 16.3 Soglie

Il punteggio deve essere una probabilità calibrata, non il cosine score grezzo.

| Probabilità | Comportamento |
|---:|---|
| `>= 0.98` | Merge automatico nello staging |
| `>= 0.80` e `< 0.98` | Revisione obbligatoria |
| `< 0.80` | Nessun merge |

La pubblicazione finale rimane soggetta al gate umano.

### 16.4 Reversibilità

L'operatore deve poter:

- unire due gruppi;
- separare un record;
- rifiutare una proposta;
- vedere le feature che hanno contribuito al punteggio.

La decisione deve essere registrata e riutilizzata nei run successivi compatibili.

## 17. Preparazione del testo semantico

Il sistema non deve embeddare automaticamente l'intera riga.

Il mapping profile definisce quali campi partecipano a:

- osservazione;
- causa;
- componente;
- codice errore;
- azione;
- outcome.

Devono essere creati testi distinti per ruolo ontologico:

- testo sintomo;
- testo failure mode;
- testo corrective action;
- testo componente;
- testo error code.

Identificativi, timestamp e valori numerici rimangono feature strutturate. Possono essere inclusi nel testo solo tramite template controllati.

La ricostruzione del testo deve essere:

- deterministica;
- visibile in UI;
- versionata;
- tracciata con quality flag.

## 18. Pipeline neurosimbolica

### 18.1 Responsabilità neurali

I modelli possono:

- rilevare e normalizzare formulazioni semantiche;
- estrarre candidati per i sei tipi di nodo dichiarati dall'ontologia;
- estrarre possibili relazioni;
- proporre descrizioni canoniche in inglese;
- recuperare entità esistenti tramite embedding;
- classificare il ruolo di una frase;
- proporre merge semantici;
- fornire confidence ed evidence span.

I modelli non possono:

- modificare l'ontologia;
- pubblicare;
- creare tipi o relazioni arbitrarie;
- sovrascrivere il raw input;
- trasformare un'ipotesi in fatto senza tracciamento;
- eseguire azioni sulla macchina.

### 18.2 Responsabilità simboliche

Le regole devono:

- validare gli output strutturati;
- accettare solo i tipi ontologici;
- verificare proprietà obbligatorie;
- verificare unicità degli ID;
- verificare domain e range;
- verificare integrità referenziale;
- verificare vocabolari controllati;
- impedire relazioni prive di supporto;
- impedire pubblicazioni incomplete;
- identificare conflitti;
- calcolare lo stato di revisione.

### 18.3 Structured output

Ogni chiamata di estrazione deve richiedere un output JSON conforme a uno schema.

Se l'output è invalido:

1. viene eseguita validazione locale;
2. può essere effettuato un numero limitato di tentativi di repair;
3. ogni repair viene tracciato;
4. dopo il limite il candidato viene quarantinato;
5. non viene mai interpretato tramite parsing fragile di testo libero.

### 18.4 Grounding

Prima di proporre una nuova entità, la pipeline deve recuperare entità esistenti compatibili.

Il modello deve scegliere tra:

- match con entità esistente;
- nuovo candidato;
- informazione insufficiente.

Ogni scelta deve contenere:

- evidence span;
- motivazione strutturata breve;
- confidence;
- alternative principali.

La motivazione non è considerata prova; serve all'operatore per la revisione.

## 19. Regole di creazione della conoscenza

### 19.1 Asset

Un `Asset` può essere pubblicato solo con tutti i campi obbligatori. Ogni versione del grafo deve contenerne esattamente uno.

L'identità non deve dipendere esclusivamente dal nome libero. Devono essere considerati:

- identificativo sorgente;
- brand;
- model;
- equipment tag;
- eventuale seriale o device ID conservato nel sidecar.

### 19.2 Component

Un componente deve rappresentare un elemento fisico, software o sottosistema.

Non devono diventare componenti:

- sintomi;
- azioni;
- valori di misura;
- intere frasi di evento.

`description` e `category` sono obbligatorie. L'associazione alla macchina avviene con `HAS_COMPONENT`; i failure mode possono essere collegati tramite `AFFECTS`.

### 19.3 Symptom

Un sintomo deve essere osservabile dall'operatore o dal sistema.

Esempi validi:

- rumore anomalo;
- temperatura elevata;
- perdita di comunicazione;
- movimento irregolare.

Una causa tecnica non deve essere modellata come sintomo.

La severità deve usare il vocabolario canonico.

### 19.4 FailureMode

Un failure mode deve rappresentare una causa o un meccanismo plausibile, non la mera ripetizione dell'evento.

Deve essere distinta la provenienza:

- `explicit`: causa dichiarata nella sorgente;
- `inferred`: causa inferita;
- `human_confirmed`: causa confermata durante la revisione.

Questa provenienza resta nell'indice delle evidenze.

`material_context` è obbligatorio. Se non applicabile, può essere usato il valore controllato `not_applicable` solo dopo approvazione umana.

### 19.5 CorrectiveAction

Un'azione osservata in un log non diventa automaticamente conoscenza correttiva.

Regole:

- esito esplicitamente positivo: candidata;
- esito `monitoring`, vuoto o ambiguo: solo evidenza, salvo approvazione;
- azione fallita: non collegabile con `RESOLVED_BY`;
- istruzione pericolosa o incompleta: revisione obbligatoria;
- escalation: `action_kind=escalation`;
- procedura operativa: `action_kind=procedure`.

Poiché l'ontologia prevede una singola fonte primaria, il nodo pubblicato usa una fonte primaria approvata. Tutte le altre fonti rimangono nell'indice delle evidenze.

Per azioni derivate da log:

- `source_type` indica il tipo di sorgente;
- `source_title` identifica il record o il titolo originale;
- `source_reference` punta all'evidence ID o al riferimento sorgente.

### 19.6 ErrorCode

Il codice deve essere preservato esattamente.

Non devono essere tradotti o alterati:

- codice;
- prefissi;
- zeri iniziali;
- separatori significativi.

Lo stesso valore può appartenere a asset differenti e avere significato diverso. Il matching deve considerare l'asset.

## 20. Entity linking

### 20.1 Feature

Il matching verso entità esistenti considera:

- tipo ontologico;
- nome normalizzato;
- descrizione;
- asset e modello;
- componente;
- codici;
- misure correlate;
- material context;
- similarità embedding;
- alias presenti nell'indice.

### 20.2 Soglie

| Probabilità calibrata | Comportamento |
|---:|---|
| `>= 0.95` | Match automatico nel candidate set, se non esistono conflitti simbolici |
| `>= 0.70` e `< 0.95` | Revisione obbligatoria |
| `< 0.70` | Nessun match; possibile nuovo candidato |

Un nuovo nodo o una nuova relazione richiedono sempre approvazione, indipendentemente dal punteggio.

### 20.3 Stabilità degli ID

Gli ID devono essere:

- univoci;
- stabili tra run;
- indipendenti dalla formulazione superficiale;
- generati in modo deterministico quando non forniti;
- modificabili solo tramite decisione esplicita.

La strategia esatta di generazione viene definita nel piano tecnico, ma deve includere tipo, contesto e contenuto canonico sufficiente a evitare collisioni.

## 21. Human in the Loop

### 21.1 Gate 1 — Identità, scoping e mapping

Obbligatorio per:

- conferma della macchina;
- nuove fonti PDF;
- scoping documentale nuovo o modificato;
- nuovo schema;
- schema modificato;
- join;
- ricostruzione di testo;
- correzioni di tipo;
- regole di imputazione.

Un mapping già approvato può essere riutilizzato automaticamente se il fingerprint è compatibile.

### 21.2 Gate 2 — Revisione semantica

La review queue contiene:

- nuovi nodi;
- nuove relazioni;
- match ambigui;
- merge ambigui;
- conflitti;
- proprietà obbligatorie mancanti;
- azioni con esito incerto;
- inferenze a bassa confidenza;
- record in quarantena.

La revisione deve essere aggregata per candidato o cluster, non per singolo record, quando possibile.

### 21.3 Azioni di revisione

L'operatore può:

- approvare;
- rifiutare;
- modificare proprietà;
- scegliere un'entità esistente;
- creare un nuovo candidato;
- unire candidati;
- separare candidati;
- risolvere un conflitto;
- escludere evidenze;
- indicare la fonte primaria;
- aggiungere una nota.

### 21.4 Gate 3 — Pubblicazione

Prima della pubblicazione l'interfaccia mostra:

- numero di nodi nuovi, modificati e invariati;
- numero di relazioni nuove e rimosse;
- candidati rifiutati;
- record esclusi o quarantinati;
- errori bloccanti;
- metriche di qualità;
- configurazione e modelli;
- differenza rispetto alla versione precedente.

La pubblicazione richiede una conferma esplicita.

### 21.5 Persistenza delle decisioni

Le decisioni umane devono essere salvate e riapplicate quando:

- input semantico;
- mapping;
- ontologia;
- modello;
- configurazione rilevante

sono compatibili.

Una decisione non deve essere riapplicata automaticamente se il contesto è cambiato in modo sostanziale.

## 22. Formato del Knowledge Graph JSON

### 22.1 Requisiti

Il file pubblicato deve:

- essere JSON valido;
- contenere metadati di versione;
- dichiarare ontologia e checksum;
- contenere solo nodi conformi;
- contenere solo relazioni conformi;
- avere riferimenti validi;
- essere ordinato deterministicamente;
- non contenere confidence, prompt o raw payload nei nodi;
- essere immutabile una volta pubblicato.

### 22.2 Struttura

```json
{
  "graph": {
    "graph_id": "log-kg",
    "version": 1,
    "created_at": "2026-07-28T12:00:00Z",
    "ontology": {
      "name": "Core_Ontology",
      "version": "2.0",
      "sha256": "..."
    }
  },
  "nodes": [
    {
      "type": "Asset",
      "id": "asset_irc5",
      "properties": {
        "asset_id": "asset_irc5",
        "name": "IRC5",
        "description": "...",
        "brand": "ABB",
        "model": "IRC5",
        "asset_type": "robot_controller"
      }
    },
    {
      "type": "ErrorCode",
      "id": "error_38001",
      "properties": {
        "error_code_id": "error_38001",
        "name": "Brake release fault",
        "description": "...",
        "code": "38001"
      }
    }
  ],
  "relations": [
    {
      "type": "GENERATES_ERROR",
      "source": {
        "type": "Asset",
        "id": "asset_irc5"
      },
      "target": {
        "type": "ErrorCode",
        "id": "error_38001"
      }
    }
  ]
}
```

`type`, `id`, `source` e `target` sono campi di serializzazione. Le proprietà ontologiche rimangono dentro `properties`.

### 22.3 Integrità

Devono valere:

- nessun nodo duplicato per tipo e ID;
- proprietà obbligatorie presenti e non vuote;
- proprietà non dichiarate assenti;
- nessuna relazione duplicata;
- source e target esistenti;
- domain e range corretti;
- array del tipo previsto;
- stringhe non sostituite da valori numerici impliciti.

## 23. Evidence Index JSON

Per ogni versione del grafo deve essere prodotto un file separato.

Esempio:

```json
{
  "graph_version": 1,
  "node_evidence": {
    "FailureMode:fm_example": [
      {
        "evidence_id": "ev_...",
        "support_type": "explicit",
        "confidence": 0.97,
        "source_field": "body",
        "source_excerpt": "...",
        "human_status": "approved"
      }
    ]
  },
  "relation_evidence": {
    "Symptom:sym_example|MAY_INDICATE|FailureMode:fm_example": [
      {
        "evidence_id": "ev_...",
        "support_type": "inferred",
        "confidence": 0.84,
        "human_status": "approved"
      }
    ]
  }
}
```

L'indice:

- non estende l'ontologia;
- permette audit e UI;
- contiene confidence e provenienza;
- può contenere alias e riferimenti agli embedding;
- non viene usato come sostituto del grafo.

## 24. Versionamento

Ogni pubblicazione produce almeno:

- `knowledge_graph_vNNN.json`;
- `evidence_index_vNNN.json`;
- `run_manifest_vNNN.json`.

Il manifest contiene:

- hash degli input;
- mapping profile;
- versione della pipeline;
- ontology checksum;
- provider;
- nomi e versioni dei modelli;
- prompt hash;
- configurazione;
- soglie;
- statistiche;
- riferimenti alle decisioni umane;
- timestamp.

Non contiene:

- API key;
- segreti;
- contenuti raw non necessari.

Una nuova pubblicazione non sovrascrive file precedenti.

## 25. Configurazione della pipeline

La configurazione deve essere salvata per run.

Deve comprendere almeno:

- provider LLM;
- modello LLM;
- provider embedding;
- modello embedding;
- endpoint locale opzionale;
- lingua canonica;
- lingue accettate;
- dimensione dei batch;
- concorrenza;
- timeout;
- numero massimo di retry;
- soglie di merge;
- soglie di entity linking;
- regole di normalizzazione;
- campi da embeddare;
- template del semantic text;
- policy di cache;
- ontology path.

Le soglie non devono essere sparse nel codice. Devono essere centralizzate e versionate.

## 26. Provider e modelli

### 26.1 Provider OpenAI

È il default dell'MVP.

Requisiti:

- lettura della chiave da environment;
- modello di estrazione letto da `MODEL_NAME`;
- gestione degli errori transitori;
- retry con backoff limitato;
- timeout;
- contabilizzazione di richieste e utilizzo;
- cache;
- nessun segreto nei log.

### 26.2 Provider locali

La pipeline deve includere un adapter locale generico configurabile tramite:

- base URL;
- identificativo del modello;
- eventuale chiave locale;
- timeout;
- capacità disponibili.

L'adapter deve permettere di usare un server di inferenza locale compatibile con il contratto applicativo, senza dipendere da un prodotto locale specifico.

L'uso del provider locale non deve richiedere modifiche a:

- Canonical Evidence Model;
- modelli di dominio;
- validatore ontologico;
- review workflow;
- formato del grafo.

L'adapter locale deve poter dichiarare le proprie capacità, per esempio:

- structured output;
- embedding;
- context length;
- batching.

Se una capacità obbligatoria manca, il preflight deve fallire con un messaggio esplicito.

Non è necessario implementare adapter distinti per diversi prodotti locali. È sufficiente un adapter generico e un fake provider deterministico per i test offline.

### 26.3 Modelli distinti

Devono essere separati logicamente:

- modello di estrazione/generazione;
- modello di embedding.

Un singolo provider può erogare entrambi, ma cache, configurazione e manifest devono distinguerli.

### 26.4 Cambio modello

Il cambio di modello invalida:

- cache dipendenti dal modello;
- calibrazione delle confidence;
- benchmark associati.

Il sistema deve richiedere una nuova valutazione prima di considerare affidabili le soglie esistenti.

## 27. Lingue

### 27.1 MVP

- Lingua canonica del grafo: inglese.
- Lingua di input validata: inglese.
- UI: può essere in inglese.
- Codici, ID, valori e unità: preservati.

### 27.2 Rilevamento

La lingua deve essere rilevata per singolo evidence record o campo testuale significativo.

Un file può contenere più lingue.

Per lingua non supportata:

- il testo viene preservato;
- il record riceve un quality flag;
- l'elaborazione semantica può essere bloccata o inviata a revisione;
- non viene tradotto silenziosamente.

### 27.3 Evoluzione italiano e tedesco

L'abilitazione futura richiede:

- modello o embedding multilingua validato;
- dataset annotato per lingua;
- calibrazione dedicata;
- test di equivalenza cross-lingua;
- alias nell'evidence index;
- output canonico inglese;
- eventuale risposta chat nella lingua dell'utente.

## 28. Performance e scalabilità

### 28.1 Target

L'MVP deve supportare:

- più documenti e file strutturati nello stesso workspace;
- elaborazione incrementale delle nuove fonti nello stesso grafo;
- profiling strutturale fino a 100.000 record per batch;
- elaborazione semantica di almeno 10.000 record per batch;
- più tabelle nello stesso batch;
- esecuzione a chunk;
- ripresa dopo interruzione;
- aggiornamento incrementale.

Il tempo assoluto dipende da hardware e provider. I test devono comunque registrare:

- record al secondo per gli step locali;
- durata per stage;
- numero di chiamate modello;
- token o unità di utilizzo;
- cache hit rate;
- memoria massima osservata.

### 28.2 Ottimizzazioni obbligatorie

- Deduplica prima delle chiamate costose.
- Cache per contenuto, modello, prompt, ontologia e configurazione.
- Embedding in batch.
- Elaborazione dei cluster quando semanticamente sicuro.
- Nessuna chiamata modello per record senza contenuto semantico.
- Persistenza progressiva.
- Concorrenza configurabile.

### 28.3 Job

I run devono essere asincroni rispetto alla richiesta HTTP.

Il frontend deve mostrare:

- stage corrente;
- percentuale o contatori;
- record processati;
- warning;
- errori;
- stima basata sul progresso, se disponibile;
- possibilità di annullamento controllato.

Non è necessario introdurre un broker distribuito nell'MVP. È sufficiente un job runner locale persistente e riprendibile.

## 29. Privacy e sicurezza

- Tutti i file originali rimangono locali.
- Il backend invia al provider remoto solo i campi necessari allo step.
- La UI deve rendere visibile quali campi partecipano al semantic text.
- La chiave API rimane server-side.
- I log applicativi devono redigere segreti.
- Raw payload sensibili non devono comparire nei log tecnici.
- Una configurazione local-only deve impedire chiamate esterne.
- L'applicazione deve effettuare un preflight del provider prima di un run.
- Gli output del modello sono dati non affidabili finché non validati.

## 30. Osservabilità

Ogni run deve produrre:

- log strutturati;
- stato per stage;
- contatori di input/output;
- record in warning e quarantena;
- errori del provider;
- retry;
- cache hit/miss;
- durata;
- metriche di qualità;
- manifest finale.

Ogni errore mostrato in UI deve includere:

- stage;
- oggetto coinvolto;
- messaggio comprensibile;
- dettaglio tecnico consultabile;
- azione suggerita;
- indicazione se il run può riprendere.

## 31. Frontend

### 31.1 Schermate minime

#### A. Upload e batch

- scheda della macchina centrale;
- selezione file;
- elenco file;
- classificazione documentale o strutturata;
- hash e dimensione;
- stato;
- avvio profiling o scoping.

#### B. Source inventory e data quality

- elenco documenti;
- pagine, scoping, OCR e warning dei PDF;
- elenco tabelle/fogli;
- numero righe/colonne;
- metriche;
- warning;
- anteprima.

#### C. Mapping

- ruolo della tabella;
- mapping colonne;
- inclusione/esclusione;
- join;
- semantic text preview;
- canonical record preview;
- salvataggio.

#### D. Run

- configurazione;
- provider e modello;
- preflight;
- progresso;
- contatori;
- costi/utilizzo se disponibili;
- errori;
- cancel e resume.

#### E. Review queue

- filtri per tipo e rischio;
- confronto tra evidenze e candidato;
- alternative;
- confidence;
- azioni di revisione;
- navigazione per cluster.

#### F. Publish

- diff;
- validazione;
- metriche;
- conferma;
- download degli artifact JSON.

#### G. Graph explorer

- ricerca per ID e testo;
- filtro per tipo di nodo;
- filtro per relazione;
- navigazione dei vicini;
- vista tabellare;
- vista grafica semplice;
- pannello proprietà;
- pannello evidenze;
- selezione versione.

#### H. Diagnostic test chat

- macchina del workspace mostrata come contesto fisso;
- input testuale;
- ipotesi;
- percorsi;
- evidenze;
- confidence;
- domande di chiarimento.

### 31.2 Nessuna gestione utenti

Non devono essere implementati:

- login;
- ruoli;
- permessi;
- profili;
- organizzazioni.

Le decisioni vengono attribuite genericamente all'operatore locale.

## 32. Graph explorer

L'explorer deve caricare il JSON pubblicato.

Funzioni:

- cercare nodi per nome, descrizione, codice e ID;
- selezionare un nodo;
- mostrare proprietà;
- mostrare relazioni entranti e uscenti;
- aprire il dettaglio delle evidenze;
- passare tra versioni;
- mostrare il delta rispetto alla versione precedente.

Non deve modificare direttamente il file pubblicato.

## 33. Chat diagnostica minima

### 33.1 Scopo

Verificare che il grafo sia navigabile e utile per troubleshooting.

Non è l'agente definitivo.

### 33.2 Comportamento

Dato un input testuale, la chat:

1. usa la macchina del workspace come asset;
2. estrae osservazioni e codici;
3. recupera fino a tre `Symptom` compatibili;
4. naviga relazioni valide;
5. classifica fino a tre `FailureMode`;
6. mostra i `Component` interessati quando presenti;
7. mostra eventuali `CorrectiveAction`;
8. può porre fino a tre domande di chiarimento;
9. cita i percorsi e le evidenze;
10. dichiara quando il grafo è insufficiente.

### 33.3 Vincoli

- Read-only.
- Usa solo l'ultima versione pubblicata selezionata.
- Non crea nodi o relazioni.
- Non aggiorna confidence del grafo.
- Non esegue azioni.
- Non presenta ipotesi come fatti.
- Non propone relazioni fuori ontologia.
- Se non esiste un percorso supportato, risponde con insufficienza di conoscenza.

### 33.4 Output minimo

Per ogni ipotesi:

- failure mode;
- confidence diagnostica;
- sintomi matched;
- componenti interessati;
- percorso nel grafo;
- corrective actions disponibili;
- evidenze principali;
- eventuale domanda successiva.

### 33.5 Memoria di sessione

La chat può mantenere il contesto della sessione corrente, ma:

- non modifica il grafo;
- non crea memoria persistente di conoscenza;
- non alimenta automaticamente la pipeline.

L'eventuale feedback loop è fuori scope.

## 34. API funzionali

Gli endpoint definitivi vengono precisati nel piano tecnico. L'MVP deve coprire logicamente:

### 34.1 Workspace, fonti e upload

- leggere e configurare la macchina centrale;
- creare un batch di fonti;
- caricare file;
- elencare batch, documenti e file;
- ottenere stato e statistiche;
- avviare profiling o scoping.

### 34.2 Documenti, tabelle e mapping

- leggere il profilo e lo scoping di un PDF;
- approvare o correggere lo scoping;
- elencare tabelle;
- leggere profilo e preview;
- salvare mapping;
- validare mapping;
- configurare join.

### 34.3 Run

- creare un run;
- eseguire preflight;
- avviare;
- leggere stato;
- leggere metriche;
- annullare;
- riprendere.

### 34.4 Review

- elencare review item;
- leggere dettaglio ed evidenze;
- approvare;
- rifiutare;
- modificare;
- merge;
- split.

### 34.5 Graph

- validare candidate set;
- ottenere diff;
- pubblicare;
- elencare versioni;
- scaricare graph, evidence index e manifest;
- cercare e navigare nodi.

### 34.6 Chat

- inviare query;
- inviare risposta a una domanda di chiarimento;
- azzerare la sessione.

## 35. Testing

### 35.1 Strategia

Il testing è una funzione primaria dell'MVP.

Sono richiesti:

- unit test;
- integration test;
- contract test;
- golden dataset test;
- regression test;
- property-based test per parser e normalizzatori dove utile;
- test end-to-end;
- test di idempotenza;
- test di carico;
- test dei provider tramite fake deterministico;
- test del provider OpenAI separabili dai test offline.

### 35.2 Golden dataset

Deve essere creato un sottoinsieme annotato del CSV esistente contenente:

- record puliti;
- record incompleti;
- record semanticamente disallineati;
- duplicati o quasi duplicati;
- componenti con alias;
- error code;
- misure e soglie;
- azioni risolutive;
- azioni in monitoring;
- failure mode espliciti;
- failure mode inferiti;
- record senza link.

Per ogni elemento annotato devono essere definiti:

- canonical evidence atteso;
- quality flags attesi;
- gruppo atteso;
- nodi attesi;
- relazioni attese;
- entità da non creare;
- decisione HITL attesa.

Il golden dataset deve essere separato in:

- calibrazione;
- test held-out.

Deve inoltre essere creato almeno un golden workspace multi-sorgente riferito alla stessa macchina, contenente:

- almeno due PDF;
- almeno un CSV;
- evidenze duplicate tra manuale e log;
- evidenze complementari;
- almeno un conflitto tra fonte normativa e osservazionale;
- un unico grafo atteso.

### 35.3 Test parser

Devono coprire:

- PDF testuale;
- PDF scansionato;
- PDF con pagine irrilevanti;
- due PDF che contribuiscono allo stesso nodo;
- CSV con separatori diversi;
- encoding diversi;
- campi multilinea;
- quote;
- righe corte e lunghe;
- righe semanticamente spostate ma formalmente valide;
- XLSX con più fogli;
- header non in prima riga;
- fogli vuoti;
- JSON array;
- JSONL;
- JSON annidato;
- array uno-a-molti.

### 35.4 Test neurosimbolici

Devono verificare:

- output modello invalido;
- proprietà mancanti;
- tipo di nodo non ammesso;
- relazione non ammessa;
- domain/range errati;
- match ambiguo;
- nuovo candidato;
- conflitto tra evidenze;
- failure mode scambiato con symptom;
- azione fallita proposta come risolutiva;
- codice alterato;
- descrizione inventata senza evidenza.

### 35.5 Test di versione

- una pubblicazione crea file nuovi;
- la versione precedente rimane invariata;
- il diff è corretto;
- il rollback logico seleziona una versione precedente senza cancellare dati;
- stesso input con cache e decisioni uguali produce gli stessi artifact ordinati.

### 35.6 Test della chat

Deve esistere un set minimo di query diagnostiche con:

- asset;
- testo;
- sintomi attesi;
- failure mode attesi;
- percorso atteso;
- azioni ammesse;
- risposte da rifiutare.

La stessa query ripetuta non deve modificare il grafo.

## 36. Metriche e criteri quantitativi

### 36.1 Metriche core

| Metrica | Target MVP |
|---|---:|
| Conformità del grafo all'ontologia | `100%` |
| Integrità referenziale | `100%` |
| Nodi e relazioni pubblicati con evidenza tracciabile | `100%` |
| Record sorgente preservati o esplicitamente classificati | `100%` |
| Versioni pubblicate con esattamente un Asset | `100%` |
| Component pubblicati con `HAS_COMPONENT` valido | `100%` |
| Fonti approvate confluite nello stesso grafo della macchina | `100%` |
| Precisione del merge probabilistico sul test set | `>= 98%` |
| Precisione entity linking sul test set | `>= 95%` |
| Precisione delle relazioni pubblicate sul test set | `>= 95%` |
| Perdita silenziosa di record | `0` |
| Segreti presenti in log o manifest | `0` |

### 36.2 Recall

La recall deve essere misurata ma non deve essere ottimizzata sacrificando le soglie di precisione.

I candidati non collegati devono rimanere visibili nella review queue.

### 36.3 Calibrazione

Le soglie:

- sono specifiche per operazione;
- sono associate a provider e modello;
- vengono valutate sul held-out set;
- devono essere ricalibrate quando cambia il modello;
- non devono essere ricavate direttamente dal cosine score.

## 37. Scenari di accettazione

### Scenario 1 — Workspace e macchina

Data una macchina configurata, il sistema:

- crea esattamente un `Asset`;
- associa tutte le fonti approvate a quel workspace;
- impedisce la creazione di un secondo Asset;
- può pubblicare i `Component` supportati dalle evidenze e collegarli alla macchina.

### Scenario 2 — PDF multipli e log nello stesso grafo

Dati due PDF e un CSV riferiti alla stessa macchina:

- i PDF vengono estratti e sottoposti a scoping;
- il CSV viene profilato e mappato;
- tutte le fonti generano evidence unit con locator coerenti;
- nodi equivalenti vengono collegati o proposti per merge;
- la pubblicazione produce un solo grafo;
- l'evidence index conserva tutte le provenienze.

### Scenario 3 — CSV valido

Dato un CSV con header e record validi, il sistema:

- rileva la tabella;
- mostra il profiling;
- permette il mapping;
- crea evidence record;
- completa il run senza perdita di righe.

### Scenario 4 — Record semanticamente disallineato

Dato un record con numero corretto di colonne ma testo in campi numerici o ID:

- il parser lo preserva;
- la validazione genera quality flags;
- il record viene quarantinato o revisionato;
- nessun collegamento errato viene pubblicato automaticamente.

### Scenario 5 — XLSX multi-sheet

Dato un XLSX con eventi e componenti su fogli separati:

- entrambi i fogli vengono scoperti;
- l'operatore definisce il join;
- i componenti vengono associati senza duplicare eventi.

### Scenario 6 — JSON annidato

Dato un JSON con eventi e array di misure:

- le strutture sono mostrate;
- nessuna esplosione viene eseguita implicitamente;
- il mapping produce una lista di misure canoniche.

### Scenario 7 — Doppio upload

Dato lo stesso file caricato due volte:

- viene riconosciuto l'hash;
- il raw file non viene duplicato;
- le chiamate modello già compatibili vengono recuperate dalla cache.

### Scenario 8 — Merge ambiguo

Dato un gruppo con probabilità 0.90:

- non viene unito automaticamente;
- appare nella review queue;
- l'operatore può unire o separare;
- la decisione è tracciata.

### Scenario 9 — Corrective action non confermata

Dato un log con azione e outcome `monitoring`:

- l'azione rimane evidenza;
- non viene creata automaticamente una relazione `RESOLVED_BY`;
- la review può promuoverla solo con decisione esplicita.

### Scenario 10 — Violazione ontologica

Dato un output modello con nodo `Incident`:

- l'output viene rifiutato;
- il nodo non entra nel candidate graph pubblicabile;
- l'errore viene registrato.

### Scenario 11 — Pubblicazione

Dato un candidate set completo e approvato:

- la validazione raggiunge il 100%;
- vengono creati graph, evidence index e manifest;
- la versione precedente resta immutata.

### Scenario 12 — Chat

Dato un input diagnostico:

- la chat restituisce al massimo tre ipotesi;
- mostra percorsi esistenti nel JSON;
- non modifica alcun artifact;
- dichiara insufficienza se non esiste conoscenza supportata.

### Scenario 13 — Cambio modello

Dato un nuovo provider o modello:

- il preflight verifica le capacità;
- la cache incompatibile non viene riusata;
- il manifest registra il cambiamento;
- le soglie sono marcate come da ricalibrare.

### Scenario 14 — Scala

Dato un batch di 10.000 record semanticamente elaborabili:

- il run avanza per chunk;
- il progresso è visibile;
- può essere interrotto e ripreso;
- non perde record;
- non ripete chiamate già completate.

## 38. Definition of Done

L'MVP è completato quando:

- PDF, CSV, XLSX e JSON sono importabili;
- più documenti e file della stessa macchina confluiscono in un unico grafo;
- ogni workspace contiene esattamente un Asset;
- tutti i tipi di nodo e relazione dell'ontologia, inclusi `Component`, `HAS_COMPONENT` e `AFFECTS`, restano supportati;
- estrazione PDF, OCR, tabelle e scoping ereditati dalla base restano coperti dai test;
- il CSV esistente è processabile senza perdita silenziosa;
- mapping e join sono configurabili da UI;
- il Canonical Evidence Model è implementato e validato;
- la pipeline è riprendibile;
- deduplica e merge rispettano le soglie;
- il provider OpenAI funziona tramite configurazione environment;
- l'interfaccia provider comprende un adapter locale generico e un fake deterministico;
- ogni candidate è tracciabile alle evidenze;
- tutti i nuovi nodi e relazioni passano da HITL;
- il grafo pubblicato è JSON e conforme al 100% all'ontologia;
- versioni precedenti non vengono sovrascritte;
- graph explorer ed evidence panel funzionano;
- la chat minima naviga il JSON in read-only;
- golden test e regression test superano i target;
- nessun segreto compare in frontend, log o manifest;
- documenti o formati fuori scope non vengono accettati.

## 39. Decisioni rinviate al piano di sviluppo

Le seguenti sono scelte implementative e non modificano il perimetro funzionale:

- framework frontend;
- libreria di visualizzazione del grafo;
- job runner locale;
- struttura esatta delle tabelle SQLite;
- modello di embedding predefinito;
- primo adapter per modello locale;
- librerie di parsing XLSX;
- formato esatto del file di configurazione;
- strategia definitiva di generazione degli ID;
- packaging e comando di avvio locale;
- supporto futuro a cella o linea come scope centrale;
- adapter futuri per e-mail e Word.

## 40. Sintesi delle priorità

Ordine di priorità del prodotto:

1. preservare e comprendere correttamente tutte le fonti;
2. garantire che appartengano alla stessa macchina;
3. rendere espliciti e verificabili scoping e mapping;
4. identificare problemi di qualità;
5. consolidare evidenze cross-source senza falsi merge;
6. estrarre candidati tracciabili;
7. imporre integralmente l'ontologia centrale senza modificarla;
8. rendere efficace la revisione umana;
9. pubblicare un unico JSON riproducibile e versionato;
10. misurare la qualità con golden test;
11. verificare la fruibilità tramite explorer e chat minima.

La chat diagnostica è intenzionalmente subordinata alla qualità della pipeline e del grafo.
