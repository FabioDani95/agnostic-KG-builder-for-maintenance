# Criteri di accettazione MVP

## 1. Regole

Un requisito è completato soltanto quando:

1. il comportamento è implementato;
2. il test indicato è automatico, salvo i gate esplicitamente manuali;
3. il test produce un artifact o report riproducibile;
4. il risultato soddisfa la soglia;
5. l'utente ha eseguito il gate sostanziale previsto.

Una demo visuale senza assert, un benchmark esplorativo o un output “sembra
corretto” non costituiscono accettazione.

## 2. Dataset di accettazione

### DS-001 — Baseline PDF

Tutte le fixture golden versionate della pipeline importata devono restare
disponibili. La baseline target corrente contiene 9 fixture e 301 test Python.

Il numero può crescere; una riduzione richiede giustificazione esplicita.

### DS-002 — CSV sporco

`machine_logs.csv` deve essere incluso come regression dataset.

Il dataset deve coprire:

- record validi;
- campi mancanti;
- righe semanticamente disallineate pur avendo larghezza corretta;
- codici;
- timestamp;
- misure;
- azioni e outcome;
- duplicati e quasi duplicati;
- riferimenti a componenti.

Deve esistere una partizione annotata per calibrazione e una held-out.

La evaluation view usata da mapping, candidate generation, linking e modelli
DEVE escludere le colonne derivate o label-like:

- `semantic_text`;
- `event_signature_id`;
- `linked_failure_mode_id`;
- `linked_symptom_id`;
- `quality_flags`.

Il raw originale resta immutabile. Le colonne escluse possono essere lette
soltanto dall'evaluator dopo la predizione. Un test con adapter spy deve
dimostrare che non entrano in prompt, feature, embedding o lookup.

### DS-003 — Workspace multisource golden

Deve essere creato un workspace annotato riferito a una sola macchina con
almeno:

- 2 PDF;
- 1 CSV;
- 1 XLSX con almeno 2 fogli;
- 1 JSON o JSONL;
- 30 fatti o catene diagnostiche atomiche attese;
- evidenza duplicata fra almeno due fonti;
- evidenza complementare;
- un conflitto normativo-osservazionale;
- un componente con alias differenti;
- un error code con zeri o prefisso significativo;
- un'azione fallita o con outcome ambiguo;
- un knowledge gap legittimo.

Il risultato atteso è un solo grafo.

La fixture non è un elenco narrativo: deve includere un manifest
machine-readable validabile con
`tests/golden/workspaces/ds003_expected.schema.json`. Il manifest deve
dichiarare almeno:

- `schema_ref` e versione del contratto;
- hash e split (`calibration`/`held_out`) di ogni source;
- nodi, proprietà e relazioni attesi come claim atomici;
- `negative_claims` espliciti, inclusi i knowledge gap;
- locator di provenienza risolvibili per ciascun claim.

La ingestion view consegnata alla pipeline non contiene label, expected claim,
split o altri campi derivati dal gold. Il manifest completo è leggibile
soltanto dall'evaluator dopo la predizione.

### DS-004 — Scala strutturata

Il dataset di scala deve avere almeno:

- 10.000 righe;
- 3 tabelle logiche;
- 30 colonne in almeno una tabella;
- duplicati esatti;
- cluster ripetuti;
- valori nulli e anomalie controllate.

### DS-005 — Scala documentale

Il corpus di scala deve avere almeno:

- 5 PDF;
- 500 pagine complessive;
- almeno un PDF scansionato;
- almeno una tabella di troubleshooting;
- pagine irrilevanti sufficienti a testare lo scoping.

### DS-CHAT-001 — Query diagnostiche

Il dataset chat deve essere riferito a bundle pubblicati immutabili e
contenere almeno:

- 20 query supportate, con target claim, path e evidence attesi;
- 10 query non supportate, per cui l'esito atteso è insufficienza;
- 10 query ambigue, con chiarimento atteso o insieme di target accettabili;
- codici esatti, sinonimi, negazioni e descrizioni colloquiali;
- almeno una coppia di query la cui risposta cambia fra `V001` e `V002`.

Ogni query deve dichiarare `query_id`, `graph_version`, classe, target
accettabili ed evidence/path attesi. Graph, evidence index e manifest devono
provenire dallo stesso bundle.

## 3. Invarianti e ontologia

### AC-ONT-001 — Checksum

**Dato** un run o una pubblicazione  
**quando** viene caricato `ontology_schema.JSON`  
**allora** il checksum deve essere:

```text
81f2d894e8b4c3c0ba3bb2e7149941ae91b704ebd8a8b8dedef91b79bd1508db
```

Qualsiasi differenza deve bloccare il run prima dell'estrazione.

### AC-ONT-002 — Tipi e proprietà

Per ogni artifact pubblicato:

- tipi di nodo ammessi: esattamente i 6 dell'ontologia;
- relazioni ammesse: esattamente le 6 dell'ontologia;
- proprietà obbligatorie presenti: `100%`;
- proprietà extra nei nodi: `0`;
- endpoint mancanti: `0`;
- domain/range errati: `0`;
- ID duplicati: `0`.

### AC-ONT-003 — Asset e componenti

Ogni versione pubblicata deve avere:

- esattamente 1 `Asset`;
- 0 o più `Component` supportati dalle fonti;
- ogni `Component` pubblicato collegato con almeno un `HAS_COMPONENT`;
- ogni `AFFECTS` diretto da `FailureMode` a `Component`.

Il test deve fallire se i componenti vengono disabilitati o rimossi dal
contratto.

### AC-ONT-004 — Nessuna invenzione di completezza

Un corpus senza error code o senza corrective action non deve causare la
creazione di nodi fittizi. Il knowledge gap deve essere tracciato nel sidecar e
il grafo deve restare ontologicamente valido.

## 4. Workspace e sorgenti

### AC-WS-001 — Una macchina

Tentare di approvare una fonte attribuita a una macchina differente deve:

- mettere la fonte in quarantena;
- non creare un secondo `Asset`;
- produrre un elemento di review.

### AC-WS-002 — Un grafo multisource

**Dato** il dataset DS-003  
**quando** tutte le fonti vengono approvate e processate  
**allora**:

- deve esistere un solo `graph_id`;
- il manifest deve elencare tutte le source approvate;
- non devono esistere export per singolo documento;
- evidenze equivalenti devono supportare gli stessi nodi o relazioni;
- il graph diff deve riferirsi allo stesso workspace.

### AC-WS-003 — Incrementalità

Dopo la pubblicazione `V001`, aggiungere una nuova fonte deve:

- lasciare `V001` byte-invariata;
- produrre un candidate delta;
- creare `V002` soltanto dopo approvazione;
- elencare nuova fonte e decisioni nel manifest `V002`.

### AC-WS-004 — Idempotenza

Ricaricare lo stesso file con configurazione compatibile deve:

- riutilizzare il raw;
- non duplicare evidence unit;
- non duplicare nodi o relazioni;
- mostrare cache hit;
- produrre lo stesso candidate result deterministico, salvo output modello
  esplicitamente non deterministico.

### AC-WS-005 — Attribuzione fonte–macchina

Su una fixture per ciascun esito `compatible`, `uncertain` e `incompatible`:

- segnali osservati e locator devono essere registrati;
- soltanto `compatible` può contribuire automaticamente al candidate graph;
- `uncertain` e `incompatible` devono restare fuori dal candidate graph;
- la risoluzione di `uncertain` richiede una decisione operatore tracciata;
- un override non può creare un secondo Asset;
- riaprire la decisione deve ripristinare lo stato precedente.

## 5. Ingestion PDF

### AC-PDF-001 — Regressione

La suite PDF baseline deve restare verde:

- testo nativo;
- OCR selettivo;
- page offset;
- scoping;
- tabelle;
- grounding;
- review controllata e publish.

### AC-PDF-002 — Locator

Ogni evidenza derivata da PDF deve avere:

- source ID;
- pagina fisica;
- extraction method;
- quote verificabile.

Copertura locator sulle evidenze PDF usate dal grafo: `100%`.

### AC-PDF-003 — Scoping HITL

L'operatore deve poter modificare lo scope. Dopo l'approvazione:

- pagine escluse non alimentano l'estrazione ordinaria;
- modifiche sono registrate;
- ripetere il run riusa lo scope approvato compatibile.

### AC-PDF-004 — OCR incerto

Una pagina con OCR sotto la soglia configurata deve:

- essere conservata;
- produrre `OCR_LOW_CONFIDENCE`;
- essere visibile;
- non generare conoscenza pubblicata senza evidenza verificabile.

Una fixture con almeno cinque tabelle deve contenere un marker univoco nella
quinta tabella, riga 61. Il test deve dimostrare che:

- pagina, block, tabella, ogni table row e ogni regione OCR sono inventariati
  come extraction unit gerarchiche con locator padre/figlio;
- il marker della quinta tabella/riga 61 è recuperabile;
- eventuali cap di estrazione sono applicati soltanto dopo l'inventario e
  producono disposition esplicite, mai truncation silenziosa;
- l'accounting di AC-EV-001 è verificato sia sulla pagina sia su ogni child
  extraction unit.

## 6. Ingestion strutturata

### AC-TAB-001 — CSV

Sul CSV di regressione:

- righe lette più righe esplicitamente fallite deve equivalere alle righe
  fisiche di dati;
- perdita silenziosa: `0`;
- ogni riga deve avere locator;
- righe semanticamente spostate devono ricevere flag o quarantena;
- testo in un campo numerico non deve diventare `0`.

### AC-TAB-002 — XLSX

Il test deve verificare:

- più fogli;
- header non sulla prima riga;
- foglio vuoto;
- formule con e senza cached value;
- locator di foglio, riga e cella;
- join senza duplicazione silenziosa.

### AC-TAB-003 — JSON

Il test deve verificare:

- array di oggetti;
- JSONL;
- oggetto con array;
- JSON annidato;
- JSONPath stabile;
- array uno-a-molti bloccato finché non viene scelta una strategia.

### AC-TAB-004 — Mapping profile

Un mapping approvato deve essere riutilizzato con fingerprint compatibile.

Una modifica a nome, tipo o presenza di una colonna chiave deve richiedere
nuova approvazione.

### AC-JOIN-001 — Join esplicito e lineage composito

Una fixture con tabelle indipendenti, join `1:1`, `1:n` e chiavi mancanti o
multiple deve verificare che:

- l'assenza di `JoinSpec` elabori le tabelle indipendentemente;
- primary, lookup, chiavi, cardinalità e policy siano registrati;
- il massimo fan-out venga applicato prima della materializzazione;
- unmatched e multiple key seguano la policy dichiarata;
- ogni output conservi i locator di tutti i record partecipanti;
- una proprietà derivata dal lookup abbia evidence di proprietà risolvibile;
- duplicazione o perdita silenziosa del record primary sia `0`.

### AC-TAB-005 — Matrice edge policy dei parser

Contract test parametrizzati devono fissare almeno questi esiti:

| Caso | Esito obbligatorio |
|---|---|
| BOM | rimosso dal boundary di decoding, raw bytes preservati |
| encoding incerto | Preparation `awaiting_operator`; nessuna sostituzione silenziosa di byte |
| header duplicato | ID colonna posizionale, mai overwrite |
| riga blank/commento | contatore strutturale separato; non è una RawUnit e non riceve disposition |
| CSV quoted multiline | una raw unit logica con range di linee fisiche |
| foglio hidden/very-hidden | inventariato, non incluso implicitamente |
| celle unite | nessun forward-fill implicito |
| XLSX protetto | Source `failed_terminal` con errore azionabile |
| formula senza cached value | quarantena della cella/unità |
| chiavi JSON duplicate | parsing bloccato per la struttura prima di ogni overwrite; mai last-write-wins |
| numero JSON ad alta precisione | valore lessicale recuperabile |
| linea JSONL malformata | fallisce la sola linea, le altre proseguono |
| path con escaping | locator deterministico e round-trip |

Per ogni caso l'equazione di accounting deve restare esatta.

### AC-NORM-001 — Valori

Il test di normalizzazione deve verificare:

- data ambigua preservata con flag;
- timezone mancante non inventata;
- numero invalido preservato e non trasformato in zero;
- unità compatibili convertite secondo mapping;
- unità incompatibili non confrontate;
- null normalization applicata soltanto se configurata;
- valore raw sempre recuperabile.

### AC-NORM-002 — Semantic text

Dato un record con timestamp, ID, misura, osservazione e azione:

- timestamp e ID non devono comparire nel semantic text di default;
- osservazione e azione devono produrre testi role-specific distinti;
- il testo deve essere visibile in preview;
- stesso mapping e input devono produrre lo stesso testo;
- cambiare il template deve cambiare versione e invalidare la cache dipendente.

## 7. Evidence e provenienza

### AC-EV-001 — Accounting

Per ogni source approvata:

```text
unità raw =
processate + duplicate + escluse + quarantinate + fallite
```

Scarto non classificato: `0`.

Per PDF/OCR l'equazione si applica gerarchicamente alla pagina e a ogni
extraction unit figlia inventariata (`block`, `table`, `table_row`,
`ocr_region`). Ogni child conserva `parent_raw_unit_id` e locator; limiti o cap
successivi all'inventario devono classificare le unità non processate con una
disposition esplicita. Non è ammesso fermare l'inventario alla prima tabella o
al primo limite di righe.

### AC-EV-002 — Copertura

Per ogni versione pubblicata:

- nodi con almeno una evidence reference: `100%`;
- relazioni con almeno una evidence reference: `100%`;
- evidence reference risolvibili a source e locator: `100%`.

### AC-EV-003 — Autorità e conflitto

Una relazione normativa contraddetta da un log deve:

- conservare entrambe le evidenze;
- creare un conflitto;
- impedire auto-stage del cambiamento incompatibile;
- richiedere decisione umana;
- registrare la risoluzione.

### AC-SEM-001 — Qualità semantica multisource

Su DS-003, usando la evaluation view blindata di DS-002:

- numero di claim predetti: `> 0`;
- precisione micro su nodi, proprietà e relazioni: `>= 0.95`;
- recall micro aggregata: `>= 0.85`;
- recall per ciascuna source: `>= 0.70`;
- evidence reference risolvibili: `100%`;
- correttezza claim-to-evidence: `>= 0.95`;
- relazioni causali o risolutive unsupported: `0`;
- negative claim violate: `0`.

Il report deve separare risultato per source, tipo di claim e aggregato. Il
mock certifica soltanto wiring e determinismo; il release gate richiede un run
con provider/modello reale e profilo congelato.

### AC-SEM-002 — Outcome, causalità e knowledge gap

Fixture positive e negative devono verificare che:

- outcome `failed`, `monitoring`, `partially_resolved` o assente non produca
  auto-stage di `RESOLVED_BY`;
- un check puramente ispettivo non diventi `CorrectiveAction`;
- una failure mode priva di rimedio produca
  `failure_mode_without_action`;
- una expected gap fallisca se compare una `RESOLVED_BY` per lo stesso claim;
- una relazione causale richieda evidence dello specifico collegamento, non la
  sola co-occorrenza dei nodi.

## 8. Merge ed entity linking

### AC-MERGE-001 — Set annotato

La held-out deve contenere almeno:

- 100 coppie candidate per entity linking;
- 100 coppie candidate per merge;
- almeno 20 positivi reali per ciascun set;
- esempi facili e ambigui;
- conflitti simbolici.

I negativi obbligatori comprendono:

- due `Component` con lo stesso alias ma `component_path` incompatibili;
- lo stesso `ErrorCode` osservato su firmware o modelli incompatibili.

In entrambi i casi l'atteso è `auto_link = 0`.

### AC-MERGE-002 — Auto-merge

Sulle sole decisioni auto-staged:

- precisione merge: `>= 98%`;
- falsi merge con guard incompatibile: `0`;
- decisioni reversibili: `100%`.

Se la soglia non è raggiunta, l'auto-stage deve essere disabilitato o la soglia
alzata; non si abbassa il quality gate.

### AC-MERGE-003 — Entity linking

Sulle sole decisioni auto-staged:

- precisione entity linking: `>= 95%`;
- link cross-tipo: `0`;
- collisioni di ID: `0`.

I due negativi incompatibili definiti in AC-MERGE-001 devono produrre
esattamente `0` auto-link, indipendentemente dalla similarità lessicale.

### AC-MERGE-004 — Fasce

Test di confine devono verificare esattamente:

- merge `0.979` → review;
- merge `0.980` → auto-stage se nessun conflitto;
- linking `0.949` → review;
- linking `0.950` → auto-stage se nessun conflitto;
- qualunque score con conflict guard → review.

### AC-MERGE-005 — Cambio modello

Cambiare modello o versione dell'embedding deve:

- invalidare cache dipendente;
- marcare la calibrazione come non valida;
- impedire auto-stage finché i quality gate non sono rieseguiti.

### AC-CAL-001 — Calibrazione non vacua

Per ciascuna operation `merge` ed `entity_link`, il report held-out deve
registrare provider/modello, lingua, feature version, dataset hash, soglia e
confusion matrix. Valgono contemporaneamente:

- precisione merge auto-staged: `>= 0.98`;
- precisione entity linking auto-staged: `>= 0.95`;
- `automation_coverage`, definita come gold positive correttamente
  auto-staged diviso tutti i gold positive: `>= 0.20`;
- decisioni auto-staged valutate per operation: `>= 20`;
- falsi auto-stage contro una guard simbolica: `0`.

Denominatore zero, campione sotto il minimo o profilo scaduto sono failure.
Mandare tutto in review non soddisfa il criterio. Se la calibrazione fallisce,
l'operation automatica resta disabilitata e AC-UX-013 non può essere
dichiarato superato.

### AC-EMB-001 — Selezione

Il test deve verificare che:

- l'intera riga raw non venga embeddato automaticamente;
- campi esclusi dal mapping non compaiano nel testo;
- codici esatti conservino un matcher deterministico;
- testi di sintomo, causa, azione e componente siano distinguibili;
- la preview corrisponda al payload inviato all'adapter.

### AC-EMB-002 — Cache

A parità di testo, ruolo, lingua, modello, template e normalizzatore deve
esistere cache hit.

Cambiare uno di tali elementi deve produrre cache miss senza cambiare l'ID del
nodo già pubblicato.

## 9. Human in the Loop

### AC-HITL-001 — Gate 1

Non deve essere possibile avviare l'estrazione semantica se esiste:

- macchina non confermata;
- PDF senza scope approvato;
- tabella inclusa senza mapping approvato;
- join non validato.

Uno scope o mapping completato automaticamente conta come approvato soltanto
se esiste una delega operatore registrata, non presenta eccezioni bloccanti e
riporta configurazione e soglie applicate.

### AC-HITL-002 — Review

Per ogni candidate ambiguo l'operatore deve poter:

- approvare;
- rifiutare;
- modificare;
- selezionare un esistente;
- merge o split;
- vedere evidenze e alternative.

### AC-HITL-003 — Carico aggregato

Gli elementi auto-staged possono essere approvati in forma aggregata al gate
finale. La UI deve comunque permettere sample inspection e drill-down.

### AC-HITL-004 — Persistenza

Dopo restart:

- decisioni prese prima del restart ancora presenti: `100%`;
- chiamate modello già checkpointate ripetute: `0`;
- stato ripreso dal checkpoint completato più recente.

### AC-HITL-005 — Pubblicazione

Con review blocking aperta il pulsante o endpoint di publish deve fallire.

Con review blocking chiusa deve mostrare il diff e richiedere conferma
esplicita.

## 10. Publisher e versioni

### AC-PUB-001 — Artifact

Ogni publish deve creare esattamente:

- graph;
- evidence index;
- manifest;

con stesso graph ID e versione.

### AC-PUB-002 — Strictness

Inserendo intenzionalmente:

- nodo con proprietà extra;
- proprietà obbligatoria mancante;
- relazione dangling;
- domain/range errato;
- relazione senza evidence;
- secondo Asset;

il publish deve fallire e non deve creare un artifact marcato `published`.

### AC-PUB-003 — Determinismo

A parità di candidate graph, decisioni e configurazione:

- ordine di nodi e relazioni stabile;
- contenuto semantico del graph artifact identico;
- differenze ammesse soltanto nei timestamp dichiarati non deterministici.

### AC-PUB-004 — Immutabilità

Nessuna API o funzione deve modificare direttamente una versione pubblicata.
Ogni aggiornamento deve produrre candidate, decisioni tracciate e una nuova
versione.

### AC-NONREG-001 — Conservazione dei claim fra versioni

Dato un `V001` controllato e una nuova source che produce `V002`, ogni claim di
`V001` deve:

- essere ancora presente in `V002`; oppure
- essere trasformato da un delta approvato `withdraw`, `merge`, `split` o
  `update`, con decisione ed evidence risolvibili.

Una sparizione non spiegata deve bloccare publish. Il test deve verificare
l'equazione `V002 = apply(V001, approved_delta)`, la byte-immutabilità di
`V001` e la ricostruibilità completa del diff.

### AC-PUB-005 — Bundle atomico e concorrenza

Graph, evidence index e manifest costituiscono una sola unità atomica. Test con
failure injection dopo ogni write e prima/dopo il rename devono verificare:

- nessuna versione parziale è selezionabile;
- la versione precedente resta current in caso di errore;
- il manifest contiene hash e size di graph ed evidence index;
- un hash alterato blocca apertura e chat;
- due publish concorrenti sullo stesso `base_graph_version` non
  sovrascrivono: uno completa e l'altro fallisce `stale_base`;
- il primo publish è `V001` e un retry idempotente non crea una seconda
  versione.

## 11. Provider, segreti e lingue

### AC-LLM-001 — Provider

Devono superare lo stesso contract test:

- fake deterministico;
- OpenAI adapter;
- adapter endpoint locale generico tramite server fake compatibile.

Il test non richiede che un modello locale reale raggiunga i quality gate
semantici dell'MVP.

### AC-LLM-002 — Preflight

Provider non raggiungibile o privo di structured output deve fallire prima di
creare candidate parziali.

### AC-SEC-001 — Segreti

La scansione di:

- response API;
- frontend bundle;
- log;
- graph;
- evidence index;
- manifest;

deve trovare `0` API key o secret.

### AC-SEC-002 — Payload remoto e data egress

Per ogni stage un fake provider spy deve verificare che:

- il payload contenga soltanto i campi allowlisted;
- preview UI e payload effettivo siano byte-equivalenti dopo serializzazione
  canonica;
- raw file, colonne escluse e segreti non vengano inviati implicitamente;
- provider, endpoint, capability e policy egress siano registrati senza
  segreti;
- una policy non approvata blocchi la chiamata prima dell'invio.

### AC-SEC-003 — Confine locale browser-safe

Test API devono rifiutare con `4xx`:

- `../` e traversal percent-encoded;
- symlink che esce dalla directory inventariata;
- collisione di prefisso fra directory;
- Origin non autorizzata;
- file o request oltre il limite configurato.

L'app deve usare source ID inventariati, containment canonico, CORS
same-origin e bind loopback di default. Non è ammesso `allow_origins=["*"]`.

### AC-LANG-001 — Inglese

Il golden multisource inglese deve superare tutti i quality gate.

### AC-LANG-002 — Italiano e tedesco

Input italiano e tedesco non qualificato deve:

- essere rilevato e preservato;
- produrre stato o warning esplicito;
- non essere dichiarato validato;
- non contribuire automaticamente al candidate graph;
- non alterare raw, quote, codici, numeri o unità.

Un'eventuale traduzione derivata deve registrare testo originale, provider,
modello, versione del prompt e locator; resta `review_required`, non viene mai
auto-staged e può contribuire al grafo soltanto dopo approvazione puntuale.
Non sostituisce mai l'evidenza originale e non qualifica italiano o tedesco
come lingua validata.

## 12. Performance e resilienza

### AC-PERF-001 — 10.000 righe

Su DS-004 la pipeline deve:

- completare senza perdita;
- elaborare in chunk;
- usare batching;
- effettuare al massimo
  `ceil(unique_semantic_units / 20)` chiamate generation (`<= 500` su 10.000
  unità semantiche uniche);
- distinguere le chiamate di retry nel report e giustificarle per errore
  transitorio, senza includerle silenziosamente nel budget ordinario;
- mantenere il picco RSS `<= 2 GiB`;
- registrare memoria, durata, chiamate e cache;
- poter essere interrotta e ripresa.

Il wall-clock è informativo finché non è definito l'hardware di riferimento;
conteggio chiamate, memoria e accounting sono gate funzionali.

### AC-PERF-002 — Corpus PDF

Su DS-005 la pipeline deve:

- preservare tutte le pagine;
- completare scoping;
- applicare OCR selettivamente;
- non caricare l'intero corpus in una singola richiesta modello;
- produrre metriche per documento e aggregate.

### AC-RES-001 — Errore provider

Un timeout o errore transitorio deve:

- rispettare retry limitato;
- registrare il tentativo;
- non duplicare candidate;
- permettere resume.

Un errore provider permanente deve portare il Run a `failed_terminal` e
richiedere una correzione più un nuovo run. `failed_resumable` è ammesso
soltanto per un errore con `retryability=same_run`; una RawUnit preservata può
ricevere disposition `quarantined`, ma questo non sostituisce lo stato
canonico del Run.

### AC-RES-002 — Checkpoint e failure injection

Con la stessa configurazione immutabile:

- crash dopo risposta provider e prima del commit deve riusare la response
  persistita e ripetere `0` chiamate provider;
- crash dopo commit deve duplicare `0` candidate o disposition;
- resume parte dall'ultimo checkpoint `committed`, mai da `prepared`;
- una modifica a input, mapping, soglia, modello o prompt hash crea un nuovo
  run invece di riprendere il precedente;
- pause, cancel, retry e resume producono stati e audit distinti.

## 13. Esperienza utente

### AC-UX-001 — Flusso unico

Un test E2E deve attraversare:

```text
Macchina → Fonti → Preparazione → Elaborazione → Revisione → Pubblicazione
```

con un solo workspace e senza dover usare schermate tecniche esterne al
percorso. Lo stepper deve mostrare passo corrente, passi completati e primo
blocco. Una URL non consentita dallo stato deve riportare al blocco precedente
con spiegazione.

### AC-UX-002 — Upload misto

Nello stesso source inventory deve essere possibile caricare almeno:

- 2 PDF;
- 1 CSV;
- 1 XLSX;
- 1 JSON o JSONL.

Ogni fonte deve mostrare formato, hash, lingua, autorità e stato. Il test deve
verificare duplicate detection, rifiuto di un formato non supportato e
quarantena per macchina incompatibile senza creare un altro grafo.

### AC-UX-003 — Preparazione adattiva

Selezionare un PDF deve mostrare preview pagina/testo/tabella e controllo dello
scope. Selezionare una fonte strutturata deve mostrare profiling, mapping,
semantic text e join.

Entrambe devono usare gli stessi stati finali e la stessa coda. Il proseguimento
deve essere bloccato finché ogni fonte inclusa non è `pronta`.

### AC-UX-004 — Azione primaria e progressive disclosure

Su ciascuno dei sei passi:

- deve esistere al massimo un'azione primaria;
- il motivo di un'azione disabilitata deve essere visibile;
- impostazioni di provider, modello e soglia devono essere chiuse di default;
- il modello configurato da environment deve essere già selezionato;
- un override deve dichiarare invalidazioni di cache o calibrazione.

### AC-UX-005 — Elaborazione e resume

Durante un run la UI deve mostrare stage e contatori reali complessivi e per
fonte. Se la percentuale non è calcolabile non deve mostrare una percentuale
simulata.

Dopo refresh e restart devono essere ripristinati stato, decisioni e ultimo
checkpoint. Un errore riprendibile deve offrire `Riprendi` o `Riprova` senza
duplicare candidate.

### AC-UX-006 — Review contestuale

Per un campione contenente conflitto, merge ambiguo, proprietà mancante e
auto-stage, la review deve:

- raggruppare e filtrare tutti gli elementi nella stessa inbox;
- mostrare evidenza originale, locator, proposta, alternative e guard;
- limitare le azioni a quelle definite da `ReviewDecision`;
- validare una correzione prima del salvataggio;
- registrare before/after ed evidenze viste;
- impedire azioni bulk sui bloccanti;
- permettere sample inspection prima della conferma aggregata.

### AC-UX-007 — Assenza di editor e mutation generiche

Il test deve verificare con applicazione avviata che:

- non esistano link o pulsanti `Apri editor`;
- gli asset `frontend/editor` non esistano;
- il package top-level `modify` non esista;
- `GET /modify`, `GET /modify/latest` e le vecchie route di modifica
  restituiscano `404`;
- lo schema OpenAPI non contenga endpoint generici per creare, aggiornare,
  cancellare o salvare direttamente nodi e relazioni;
- il catalogo tool della chat non contenga graph mutation;
- il candidate graph possa cambiare soltanto tramite una `ReviewDecision`
  valida.

### AC-UX-008 — Publish ed explorer read-only

Con review bloccante aperta, `Pubblica versione` deve essere disabilitato e
portare all'elemento da risolvere. Con gate superato deve mostrare diff,
copertura, fonti escluse/quarantinate, validazione e nuova versione prima della
conferma.

Dopo publish, `Esplora` deve permettere ricerca, filtri, provenienza, confronto
versioni e download senza mostrare azioni di modifica. Cambiare versione
selezionata non deve cambiare alcun artifact.

### AC-UX-009 — Errori azionabili

Errori di upload, parsing, provider e validazione devono mostrare fonte, causa,
stato preservato, azione consigliata, dettaglio tecnico espandibile e
riprendibilità. L'errore di una fonte non deve far scomparire le altre.

### AC-UX-010 — Persistenza dell'interfaccia

Mapping, scope, filtri di review e decisioni devono mostrare stato di autosave.
Dopo refresh devono risultare invariati. La UI deve chiedere conferma per
publish e invalidazioni ampie, non per la navigazione ordinaria.

### AC-UX-011 — Accessibilità desktop

Il percorso principale deve superare un test automatico di accessibilità senza
violazioni critiche e un test manuale che verifichi:

- navigazione completa da tastiera;
- focus visibile;
- label ed errori associati;
- stati non distinti dal solo colore;
- annunci dei cambi di stato;
- assenza di modali annidati;
- usabilità a viewport `1024×768`.

### AC-UX-012 — Lingua UI e fonte

Cambiando UI fra italiano e inglese:

- raw, quote, codici e unità devono restare invariati;
- la lingua rilevata della fonte deve restare visibile;
- un input italiano o tedesco non qualificato deve mantenere il warning;
- il tedesco non deve essere proposto come lingua UI dell'MVP.

### AC-UX-013 — Delega automatica dello step

Un test E2E deve eseguire lo stesso workspace in tre modalità:

1. verifica manuale;
2. esecuzione automatica;
3. automatica con eccezione sotto soglia.

Il test deve verificare che:

- `Salta ed esegui automaticamente` completi realmente lo step;
- artifact, contatori e audit dello step esistano anche in modalità automatica;
- configurazione e soglie usate siano mostrate e registrate;
- il risultato automatico sia ispezionabile e reversibile prima del publish;
- un elemento sicuro sopra soglia non richieda interazione puntuale;
- un conflitto o una guard fallita arresti l'avanzamento al checkpoint;
- l'operatore venga portato direttamente all'eccezione;
- sia possibile tornare alla verifica manuale;
- identità macchina e publish richiedano sempre conferma esplicita;
- nessun valore mancante venga inventato per completare automaticamente lo
  step.

## 14. Chat diagnostica

### AC-CHAT-001 — Grounded answer

Su almeno 10 query annotate:

- massimo 3 ipotesi;
- percorsi composti soltanto da relazioni presenti nel graph;
- evidence reference valida per ogni ipotesi;
- nessuna modifica agli artifact;
- componenti mostrati quando il path li include.

### AC-CHAT-002 — Insufficienza

Su query senza supporto nel grafo, la chat deve dichiarare insufficienza e non
inventare cause o azioni.

### AC-CHAT-003 — Versione

Selezionando `V001` dopo la pubblicazione di `V002`, la chat deve usare
esclusivamente nodi e relazioni di `V001`.

### AC-CHAT-004 — Accuracy non vacua e coerenza bundle

Su DS-CHAT-001:

- ogni query supportata deve restituire almeno una ipotesi;
- target recall@3 sulle query supportate: `>= 0.90`;
- path composti da relazioni presenti nel graph: `100%`;
- evidence reference corrette e risolvibili: `100%`;
- abstention sulle query non supportate: `100%`;
- massimo tre ipotesi e massimo tre domande di chiarimento;
- artifact hash/version mismatch deve fallire chiuso prima della query.

Una risposta sempre vuota o sempre “informazioni insufficienti” non supera il
gate.

## 15. Regressione tecnica

### AC-REG-001

Ogni gate tecnico deve includere:

- pytest;
- Ruff;
- contract test;
- golden mock;
- test E2E della console quando la UI è coinvolta.

### AC-REG-002

Il report di regressione deve distinguere:

- `313` test della baseline importata;
- `+1` test del checker, `-17` test dell'editor rimosso e `+4` test
  read-only/no-mutation, per un checkpoint storico riconciliato di `301`;
- 9 golden fixture mock conformi;
- recall mock media `1.0`;
- link Markdown validi.

Il conteggio corrente può crescere e non deve essere etichettato
automaticamente come `301`. Ogni baseline citata deve registrare comando
eseguito, commit, timestamp e path dell'artifact di test.

Un test può essere sostituito soltanto da copertura equivalente o superiore.
Non può essere eliminato perché rende più semplice il refactoring.

La riconciliazione storica è
`313 + 1 - 17 + 4 = 301`: i 17 test verificavano l'editor libero rimosso da
`DEC-022`; i 4 nuovi test verificavano assenza di route e tool di mutation,
immutabilità e visualizzazione read-only.

## 16. Definition of Done

L'MVP è pronto soltanto quando:

- tutti gli AC obbligatori sono verdi;
- l'ontologia ha il checksum fissato;
- PDF, CSV, XLSX e JSON confluiscono nello stesso grafo;
- una macchina produce un solo Asset e conserva i Component;
- il candidate graph è separato dalle versioni pubblicate;
- graph, evidence index e manifest rispettano i contratti;
- publish è strict;
- il processo è riprendibile;
- i gate HITL sono verificati dall'utente;
- i quality gate di merge e linking sono calibrati;
- il corpus multisource golden supera la valutazione;
- la evaluation view multisource è blindata;
- il gate semantico non vuoto e i negative claim sono verdi;
- ogni perdita fra versioni è spiegata da un delta approvato;
- il bundle pubblicato è atomico e verificato tramite hash;
- la chat è read-only e grounded;
- il flusso frontend è unico e multi-formato;
- non esistono editor libero o endpoint generici di graph mutation;
- nessun segreto è esposto;
- documentazione e runbook locale sono aggiornati;
- non esistono blocker o decisioni di prodotto implicite aperte.

## 17. Evidenze da consegnare

Il completamento deve produrre:

- report test;
- report golden;
- report del dataset di scala;
- metriche merge/linking;
- report di calibrazione con copertura e confusion matrix;
- report semantico multisource per source e tipo di claim;
- report chat supported/unsupported/ambiguous;
- report di failure injection, atomicità e concorrenza publish;
- screenshot o registrazione dei gate UI;
- artifact JSON di esempio;
- manifest di riproducibilità;
- elenco dei requisiti coperti.

Questi artifact saranno richiesti dal futuro piano di sviluppo, ma il presente
documento non ne stabilisce l'ordine.
