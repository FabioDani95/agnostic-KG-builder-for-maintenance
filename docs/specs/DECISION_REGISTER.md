# Registro delle decisioni di prodotto

## Stato

Le decisioni con stato `ACCEPTED` sono vincolanti per specifica e futuro piano
di sviluppo. Possono essere cambiate soltanto con una nuova decisione esplicita
che indichi quale voce sostituisce.

`ACCEPTED` indica che la scelta è congelata nel pacchetto normativo; non
sostituisce l'owner approval del pacchetto, registrata separatamente in
`SPEC_INDEX.json`.

| ID | Stato | Decisione |
|---|---|---|
| DEC-001 | ACCEPTED | Il prodotto viene sviluppato in `log-kg-builder`; la repository originaria resta backup e riferimento |
| DEC-002 | ACCEPTED | Si evolve la pipeline esistente; non si costruisce una seconda pipeline semantica |
| DEC-003 | ACCEPTED | L'ontologia centrale rimane esattamente quella fornita |
| DEC-004 | ACCEPTED | Un workspace rappresenta una sola macchina |
| DEC-005 | ACCEPTED | `Component`, `HAS_COMPONENT` e `AFFECTS` restano supportati |
| DEC-006 | ACCEPTED | Tutte le fonti del workspace producono un unico grafo |
| DEC-007 | ACCEPTED | Il grafo pubblicato è JSON; Neo4j è fuori scope |
| DEC-008 | ACCEPTED | PDF, CSV, XLSX e JSON sono formati MVP |
| DEC-009 | ACCEPTED | Word ed e-mail native sono fuori scope iniziale |
| DEC-010 | ACCEPTED | L'applicazione è locale, senza utenti e organizzazioni |
| DEC-011 | ACCEPTED | OpenAI è il provider predefinito configurato da `.env` |
| DEC-012 | ACCEPTED | Il core deve supportare provider intercambiabili, incluso un endpoint locale generico |
| DEC-013 | ACCEPTED | Inglese è la lingua canonica e qualificata dell'MVP |
| DEC-014 | ACCEPTED | Italiano e tedesco richiedono una successiva qualifica, senza redesign |
| DEC-015 | ACCEPTED | La pipeline è neurosimbolica |
| DEC-016 | ACCEPTED | Human in the Loop è obbligatorio ai gate di input, review e pubblicazione |
| DEC-017 | ACCEPTED | L'agente diagnostico nell'MVP è minimale e read-only |
| DEC-018 | ACCEPTED | L'implementazione deve essere progressiva e verificata dall'utente per gate |
| DEC-019 | ACCEPTED | L'ontologia è centrale; le differenze cliente sono mapping e configurazioni, non ontologie separate |
| DEC-020 | ACCEPTED | Evidenze e knowledge graph sono artifact separati e collegati |
| DEC-021 | ACCEPTED | Il frontend usa un solo flusso guidato multi-formato, non pagine tecniche scollegate |
| DEC-022 | ACCEPTED | L'editor libero e tutte le graph mutation generiche vengono rimossi |
| DEC-023 | ACCEPTED | L'operatore può delegare gli step non bloccanti all'automazione senza ometterli |
| DEC-024 | SUPERSEDED | Sostituita da DEC-036: nessun gate contenutistico di appartenenza al caricamento |
| DEC-025 | ACCEPTED | Le strutture si elaborano indipendentemente per default; ogni join è esplicito e conserva lineage di tutte le RawUnit partecipanti |
| DEC-026 | ACCEPTED | Accounting e stati usano RawUnit, disposition terminali e quattro state machine canoniche; i casi limite parser hanno esito normativo |
| DEC-027 | ACCEPTED | Il candidate graph è revisionato contro una base pubblicata; withdrawal e reversal producono nuove revisioni e il publish è un bundle atomico |
| DEC-028 | ACCEPTED | Resume usa soltanto checkpoint committed con configurazione identica; retry, pause, cancel e invalidazione hanno semantica distinta |
| DEC-029 | ACCEPTED | I valori manuali richiedono OperatorAssertion; `material_context` usa il vocabolario applicativo fissato senza modificare l'ontologia |
| DEC-030 | ACCEPTED | Component ed ErrorCode hanno identità contestuale nel sidecar; alias o codice uguali non autorizzano auto-link |
| DEC-031 | ACCEPTED | Autorità, conflitti, outcome, causalità e knowledge gap seguono policy esplicite e non eliminano evidence |
| DEC-032 | ACCEPTED | Delega e revoca sono eventi append-only con step catalog, checkpoint di efficacia e backpressure |
| DEC-033 | ACCEPTED | IT/DE non qualificato è preservato e non contribuisce automaticamente; una traduzione derivata richiede approvazione puntuale |
| DEC-034 | ACCEPTED | Generation, embedding, endpoint, capability e data egress hanno configurazioni distinte; `MODEL_NAME` vale soltanto per generation |
| DEC-035 | ACCEPTED | Auto-stage richiede un CalibrationProfile valido, non vacuo e qualificato per operation, modelli, lingua, feature e dataset |
| DEC-036 | ACCEPTED | Il caricamento di un formato supportato è l'attribuzione operatore; nessuna conferma di associazione o quarantena contenutistica in G1 |
| DEC-037 | ACCEPTED | G1 prepara ogni PDF includendo automaticamente tutte le pagine, senza controllo pagina-per-pagina, in modo idempotente |
| DEC-038 | ACCEPTED | La route iniziale è una home minimale dei workspace persistiti, apribili per ID e creabili con un'azione + dedicata |
| DEC-039 | ACCEPTED | G2 usa una preparazione automatica con eccezioni, una decisione alla volta e dettagli tecnici chiusi; nessuna approvazione massiva o ripetitiva |
| DEC-040 | ACCEPTED | La UI usa soltanto nomi di attività, introduce `Struttura dati` con anteprima tabellare e mappa colonne→grafo, e rinvia la costruzione del grafo a `Elaborazione` |
| DEC-041 | ACCEPTED | `Struttura dati` richiede conferma per singola fonte e dimostra robustezza CSV e qualifica EN/IT/DE/mixed prima dell'avanzamento |
| DEC-042 | ACCEPTED | La generation crea e fa approvare un sottografo per fonte prima del merge; nuove fonti producono sottografo e delta incrementali senza rigenerare la base |
| DEC-043 | ACCEPTED | L'accettazione iniziale di Elaborazione è CSV-first e mostra per ogni fonte grafo navigabile, tabella nodi, tabella relazioni ed evidenze; il collaudo PDF segue sullo stesso contratto e sulla pipeline riusata |
| DEC-044 | ACCEPTED | G3 non è accettato: la UI è un prototipo verificato, mentre il motore deve superare hardening CSV eterogeneo e validazione ontologica strict prima del collaudo PDF |

## Dettaglio e razionale

### DEC-001 — Repository di sviluppo e backup

La baseline versionata al commit
`54c1234e33f2bab09c69df22d9404afb79702224` è stata copiata in
`log-kg-builder`.

La repository `agnostic-KG-builder-for-maintenance`:

- non deve essere modificata dal nuovo progetto;
- conserva le proprie modifiche locali;
- è configurata nel nuovo repository come riferimento di fetch
  `upstream-backup`;
- ha push disabilitato dal nuovo repository;
- non è il luogo di sviluppo del prodotto unificato.

Non è richiesto mantenere sincronizzate automaticamente le due codebase.

### DEC-002 — Una pipeline semantica

I formati hanno ingestion differenti:

- PDF: estrazione, OCR, tabelle, scoping e chunking;
- CSV/XLSX/JSON: profiling, mapping, join e normalizzazione.

Dopo l'ingestion devono convergere in `EvidenceUnit`. Candidate mining,
estrazione, grounding, entity linking, merge, validazione e review devono
essere condivisi.

### DEC-003 — Ontologia immutabile

La flessibilità commerciale deriva da:

- mapping profile;
- alias;
- dizionari e normalizzazioni;
- configurazioni di fonte;
- evidenze e regole di merge.

Non deriva da un'ontologia per cliente.

### DEC-004 e DEC-005 — Macchina e componenti

La macchina è l'`Asset` centrale e unico del workspace.

“Partire per macchina” non significa eliminare i componenti:

- i componenti sono nodi `Component`;
- sono collegati con `HAS_COMPONENT`;
- i failure mode possono usare `AFFECTS`;
- non possono essere promossi a secondo `Asset` nello stesso workspace.

### DEC-006 — Un solo grafo

Batch e file sono unità operative, non confini del knowledge graph.

Nuove fonti producono un delta candidato verso lo stesso grafo versionato.

### DEC-008 e DEC-009 — Formati

PDF è stato incluso dopo l'emersione del caso cliente che richiede manuali,
report e documentazione tecnica oltre ai log.

Nell'MVP:

- un report è accettato se fornito in PDF o in uno dei formati strutturati;
- il contenuto di un'e-mail può essere accettato soltanto se esportato in un
  formato supportato;
- `.docx`, `.msg`, `.eml` e connessioni mailbox non sono implementati.

### DEC-011 e DEC-012 — Modelli

Il modello generation predefinito è quello indicato da
`KG_GENERATION_MODEL` nel `.env` locale; `MODEL_NAME` resta soltanto fallback
legacy se la variabile canonica è assente. Alla data della specifica il valore
è `gpt-5.6-terra`.
Il provider non deve essere hard-coded nel dominio.

Supportare provider intercambiabili significa mantenere un contratto comune;
non significa ottimizzare l'MVP per ogni runtime locale esistente.

### DEC-013 e DEC-014 — Lingue

Inglese è la sola lingua con criteri di accettazione completi nella prima
release.

Italiano e tedesco devono essere possibili senza cambiare contratti, ma non
possono essere descritti come “supportati” finché non esistono golden dataset
e soglie calibrate specifiche.

### DEC-016 — Human in the Loop

L'umano:

- conferma la macchina e sceglie i file da caricare;
- nelle fasi successive sceglie per mapping e join se verificare manualmente o
  delegare le sole decisioni autorizzabili;
- risolve ambiguità e conflitti;
- approva la pubblicazione.

Non deve approvare individualmente ogni elemento ad alta confidence. Gli
elementi auto-staged restano visibili nel diff finale. Una delega esplicita
mantiene l'umano nel controllo della pipeline anche quando lo step viene
eseguito automaticamente.

### DEC-017 — Agente

L'agente serve a verificare che il grafo supporti:

- ricerca di casi analoghi;
- associazione sintomo-causa;
- suggerimento di azioni correttive;
- spiegazione basata su evidenze.

La qualità del grafo ha precedenza sullo sviluppo dell'agente.

### DEC-021 — Esperienza unificata

La varietà dei formati deve essere assorbita dal passo `Preparazione`:

- in G1 PDF include automaticamente tutte le pagine senza preview massiva;
- in G1 CSV, XLSX e JSON sono caricati integralmente senza selezione di righe;
- profiling, mapping, semantic text e join entrano nelle fasi successive;
- tutte le fonti condividono inventory, stati, gate, elaborazione, review e
  pubblicazione;
- le aree tecniche `Qualità` e `Campi richiesti` diventano filtri della stessa
  inbox di review.

Il percorso dell'operatore è
`Macchina → Caricamento → Controllo file → Struttura dati → Elaborazione → Revisione → Pubblicazione`.
Il dettaglio completo è in `UX_SPECIFICATION.md`.

### DEC-022 — Nessun editor libero

Il prodotto non espone un canvas o workspace per modificare arbitrariamente il
grafo. La scelta vale sia per il candidate graph sia per le versioni
pubblicate.

Il candidate graph può essere corretto soltanto tramite decisioni HITL
contestuali, evidence-backed e ontologicamente validate. Il grafo pubblicato è
immutabile e può essere soltanto esplorato, confrontato, interrogato o
scaricato.

Devono essere rimossi dalla baseline:

- pagina e asset del graph editor;
- route `/modify` e relativi endpoint;
- servizi di sessione e validazione dell'editor;
- tool chat di creazione, aggiornamento o cancellazione;
- configurazioni, fixture e test esclusivamente dedicati all'editor libero.

Le utility puramente visuali necessarie all'esplorazione read-only possono
essere ricollocate in un servizio neutro.

### DEC-023 — Step manuale o automatico

Per ogni step delegabile l'operatore può scegliere, limitatamente alle
modalità ammesse per quello step da `DC-DELEGATION-001`, se:

- controllare e approvare manualmente;
- far applicare automaticamente la proposta;
- ricevere soltanto eccezioni e casi sotto soglia.

`automatic` non è ammesso per `nonblocking_review`;
`exceptions_only` non è ammesso per `advance_workflow`.

Nell'interfaccia `Salta` significa `esegui automaticamente`. Lo step continua
a produrre artifact, validazioni, contatori e audit.

La delega non può approvare automaticamente l'identità della macchina,
risolvere conflitti bloccanti, superare guard simboliche o pubblicare. In questi
casi la pipeline deve fermarsi al checkpoint e richiedere l'intervento umano.

### DEC-024 — Appartenenza fonte-macchina

**Stato:** `SUPERSEDED` da `DEC-036`.

Ogni Source riceve un `SourceAssetAssessment` append-only con outcome
`compatible`, `uncertain` o `incompatible`.

- un identificativo forte uguale e senza conflitti consente `compatible`;
- un identificativo forte esplicitamente differente produce `incompatible`;
- modello, famiglia, sito o work order senza identificativo forte restano
  `uncertain`;
- `uncertain` e `incompatible` sono `quarantined` e non alimentano il core.

L'operatore può confermare una fonte incerta o correggere claim/identità, ma
non può forzare direttamente una fonte incompatibile nel grafo. La semantica
completa è `DC-SRC-ASSESS-001`.

### DEC-025 — Join espliciti e lineage composita

Fogli, tabelle e collection indipendenti non vengono uniti implicitamente.
Ogni join dichiara primary e lookup, chiavi, cardinalità, policy unmatched e
multiple, fan-out massimo e decisione di approvazione.

One-to-many e many-to-many non sono auto-approvabili. Many-to-many richiede
aggregazione oppure emissione bounded-pairs esplicita, ordine deterministico e
fan-out massimo; il prodotto cartesiano implicito è vietato. Ogni EvidenceUnit
derivata conserva tutte le `provenance_refs`; l'evidence index copre nodo,
proprietà, relazione, merge, split e tombstone. Riferimenti: `DC-JOIN-001` e
`DC-PROV-001`.

### DEC-026 — Accounting, stati e parser

La RawUnit nasce durante l'inventario, prima dei filtri. Ogni tentativo
produce una disposition terminale append-only fra `processed`, `duplicate`,
`excluded`, `quarantined` e `failed`; per ogni coppia RawUnit/run è attiva
esattamente quella del tentativo più recente.

PDF conta pagine fisiche; CSV record logici; XLSX righe dati; JSON elementi di
collection inventariate; JSONL linee non vuote. Record quoted multiline,
formula senza cache, chiavi JSON duplicate, precisione numerica, fogli nascosti
e gli altri casi limite hanno la policy vincolante di `DC-PARSER-001`.

Source, Preparation, Run e Workspace non condividono lo stesso vocabolario.
Workspace è derivato, non una seconda verità mutabile. Riferimenti:
`DC-DISPOSITION-001` e `DC-STATE-001`.

### DEC-027 — Candidate lifecycle, ritiro e bundle pubblicato

Ogni CandidateGraphRevision dichiara la versione base. `reject` è una
decisione, non una candidate operation; le operazioni includono `withdraw` e
`supersede`.

Il ritiro non cancella VNNN: omette il claim soltanto dalla versione monotona
successiva dopo decisione umana, dipendenze validate e tombstone. Reopen e
revert sono eventi append-only prima del publish; dopo il publish richiedono
un nuovo delta.

Ogni graph-affecting candidate deve avere disposition terminale. La truth
table di `DC-PUBLISH-001` decide senza eccezioni la pubblicabilità.

Il publish è una transazione per workspace su un bundle di tre file. La prima
versione è `V001`, con stem `v001`; l'incremento è monotono, zero-padded per
almeno tre cifre. Staging, validazione, checksum, fsync, atomic rename e lock
precedono l'aggiornamento di `latest`.

### DEC-028 — Checkpoint, resume e invalidazione

Un checkpoint è safe soltanto nello stato `committed`, dopo persistenza atomica
di output, disposition, call references, audit e hash.

- Resume continua lo stesso run/config dall'ultimo committed;
- Retry ripete soltanto una work unit `same_run`;
- Pause si arresta al safe point ed è riprendibile;
- Cancel è terminale;
- una modifica logica crea un nuovo run e rende il precedente `superseded`.

Le risposte modello vengono persistite prima del consumo. Una risposta già
persistita non viene richiesta di nuovo; una call `in_flight` senza risposta è
`indeterminate` e conserva la stessa idempotency key. La matrice
`DC-CACHE-001` è normativa per invalidare cache, mapping, candidate e
calibrazione.

### DEC-029 — OperatorAssertion e `material_context`

Un input manuale è evidence soltanto con campo target, valore, reason,
evidenze viste, operatore, timestamp, decisione e locator `operator_input`.
Non autorizza placeholder né graph editing libero.

Il vocabolario applicativo di `FailureMode.material_context` è:

- l'esatto `component_id` di un Component esistente;
- `asset_level`;

`not_applicable`, stringhe vuote e categorie inventate non sono ammessi. Se
una proprietà obbligatoria non può essere attestata, il candidato viene
escluso o resta blocking e il gap rimane nel sidecar. CorrectiveAction
operator-originated usa le proprietà ontologiche di provenienza con
riferimento risolvibile `operator_input:<decision_id>`.

### DEC-030 — Identità contestuale

Alias e codici identici non bastano per auto-link.

- Component richiede component path, subsystem o part number stabile
  compatibile;
- ErrorCode richiede modello e namespace compatibili e almeno firmware,
  component path o scope normativo;
- `unknown` può essere wildcard soltanto in assenza di definizioni concorrenti
  nello stesso contesto; altrimenti richiede review;
- intervalli noti incompatibili bloccano auto-link;
- lo stesso `code` può appartenere a ErrorCode distinti.

Firmware, validità, component path, alias e part number sono sidecar
`DC-CONTEXT-001` e non proprietà aggiuntive dell'ontologia.

### DEC-031 — Autorità, conflitto, outcome e causalità

Applicabilità esatta ed esplicita supersessione prevalgono; recency da sola
non basta. Un log non sovrascrive automaticamente una fonte normativa.

I conflitti si risolvono come `coexist`, `superseded` o
`operator_selected`, conservando tutte le evidence.
KnowledgeGap resta un sidecar con stato e blocking espliciti.

`MAY_INDICATE`, `INDICATES` e `RESOLVED_BY` richiedono il supporto minimo di
`DC-OUTCOME-001`. Co-occorrenza e rationale del modello non provano causalità.
Outcome `failed`, `partially_resolved`, `monitoring`, `recurred`,
`not_reported` o `unknown` non autorizzano auto-stage di `RESOLVED_BY`.

### DEC-032 — Delega, revoca ed eccezioni

Questa decisione precisa DEC-023. Ogni delega è un evento append-only con step
ID, scope, mode, config hash, checkpoint efficace e riferimenti di
supersessione/revoca.

`automatic` si ferma al primo elemento non autorizzabile dello scope;
`exceptions_only` accumula non-blocking e sospende lo scope alla prima
eccezione blocking. Le fonti indipendenti possono proseguire fino alla barriera
di merge. La coda è limitata a 100 per default; a saturazione il run si ferma
al checkpoint successivo per la sola source o partizione coinvolta e per gli
stage dipendenti. Soltanto identità macchina, conflitti globali blocking,
guard ontologiche e publish fermano globalmente il run.

Un cambio mid-run vale soltanto dai checkpoint successivi. Output già
committed restano auditabili e reversibili prima del publish.

### DEC-033 — Input non qualificato e inglese canonico

Questa decisione precisa DEC-013 e DEC-014. Italiano, tedesco, mixed e unknown
vengono rilevati, preservati, inventariati e profilati. Non alimentano
automaticamente generation del grafo, embedding, merge o proprietà canoniche.

Una traduzione può contribuire soltanto come valore derivato con testo
originale, provider, modello, prompt, locator e approvazione puntuale
dell'operatore. Senza calibrazione IT/DE, i candidate risultanti non vengono
auto-staged. Raw, quote, codici, ID, numeri, unità, brand, model e riferimenti
sorgente restano invariati. Nomi, descrizioni, instruction text e vocabolari
graph sono inglesi.

### DEC-034 — ProviderConfig e data egress

Questa decisione precisa DEC-011 e DEC-012. Generation ed embedding hanno
provider, modello e base URL distinti. Le variabili canoniche sono
`KG_GENERATION_PROVIDER`, `KG_GENERATION_MODEL`, `KG_GENERATION_BASE_URL`,
`KG_EMBEDDING_PROVIDER`, `KG_EMBEDDING_MODEL` e
`KG_EMBEDDING_BASE_URL`. `MODEL_NAME` è soltanto fallback legacy generation
quando `KG_GENERATION_MODEL` è assente. La precedenza è run override,
environment, configurazione applicativa, default; conflitti allo stesso
livello sono errori.

ProviderConfig è versionato e privo di secret. Il preflight prova le capability
effettive richieste, non soltanto un health endpoint.

Ogni endpoint non loopback è remoto. Una allowlist per stage limita il payload
e la UI ne mostra il contenuto effettivo prima del primo invio. Full file,
path locali, colonne escluse, raw record completi e join key restano vietati di
default. I contract test catturano il payload con fake provider.

### DEC-035 — Calibrazione non vacua

Ogni Candidate registra `calibration_profile_id` e `feature_version`; un
profilo assente, invalido o incompatibile forza `review_required`.

CalibrationProfile è specifico per operation, provider/modelli, lingua,
feature/schema e dataset hash. Registra soglie, confusion matrix, sample
counts, precisione e automation coverage. Denominatore zero, zero elementi
auto-staged, precisione insufficiente o coverage sotto il minimo approvato
rendono il profilo `invalid`; mandare tutto in review non soddisfa il gate di
automazione.

### DEC-036 — Attribuzione operatore al caricamento

La selezione di un file supportato è la decisione esplicita con cui
l'operatore lo attribuisce alla macchina confermata. L'app non esamina il
contenuto per richiedere conferma, proporre esclusione o produrre quarantena.
Ogni file appare subito nell'inventory e può essere rimosso con la × rossa;
prima della rimozione l'app richiede una conferma esplicita.
Lo stato sufficiente è `Caricato`, mostrato accanto alla ×: G1 non espone un
box riepilogativo finale né una quarta fase `Controllo` nello stepper.

Formati non supportati e duplicati esatti già attivi sono bloccati alla
selezione prima dell'invio. La API mantiene rispettivamente le difese `415` e
`409`; una Source rimossa può invece essere ripristinata dallo stesso hash.

Questa decisione sostituisce `DEC-024` per il prodotto corrente. Il record
tecnico legacy `SourceAssetAssessment` può restare temporaneamente come
compatibility artifact con esito fisso `compatible`, ma non costituisce un
gate e non deve essere esposto all'utente.

### DEC-037 — Preparazione PDF completa e idempotente in G1

Il caricamento di un PDF prepara automaticamente tutte le pagine fisiche.
Non esistono a G1 preview pagina-per-pagina, checkbox, motivazioni di esclusione
o approvazione dello scope. L'interfaccia comunica soltanto caricamento e
inclusione completa; l'operatore può rimuovere il documento intero.

Un duplicato attivo non è ammesso; un doppio click è prevenuto dalla UI e la
API risponde `409` senza produrre una seconda Source. Dopo una rimozione, la
ricarica deve riusare source, scope e run compatibili e non produrre HTTP 500.
OCR, tabelle, locator, quality flag e accounting restano persistiti
internamente per le fasi successive.

### DEC-038 — Home minimale dei workspace

La route iniziale apre una home semplice che elenca i workspace persistiti.
Ogni card mostra macchina, marca/modello, stato derivato, numero di documenti e
ultimo aggiornamento; `Apri workspace` riprende per ID la stessa macchina e il
suo source inventory. La schermata G1 espone un collegamento per tornare alla
home.

Questa home è parte di G1 ed è già implementata. Non autorizza eliminazione o
amministrazione avanzata multi-workspace. L'azione
`+ Nuovo workspace` crea invece un Workspace/Asset separato tramite onboarding;
un solo workspace è selezionato e operativo alla volta.

### DEC-039 — Corsia semplice e progressiva per G2

Le lezioni del Gate 1 diventano vincolanti per la preparazione multisource.
G2 parte dall'inventory già accettato, profila e propone automaticamente
mapping, semantic text e normalizzazioni, quindi porta all'operatore soltanto
le eccezioni che richiedono davvero una scelta.

La UI mostra una decisione alla volta e una sola azione primaria. Non richiede
approvazioni per ogni riga, pagina, foglio o colonna e non ripete gli esiti
positivi in un box separato. Preview, profiling, locator, fingerprint e
contratti completi restano nei dettagli chiusi di default. Il percorso felice
si conclude con una sola conferma della preparazione risultante.

Nessun join è il default. Un join compare soltanto quando esiste una proposta
esplicita, con spiegazione operativa e confronto prima/dopo. Errori isolabili
restano associati alla fonte o RawUnit coinvolta e non fermano né nascondono le
altre fonti. Il criterio osservabile è `AC-UX-014`.

### DEC-040 — Linguaggio di prodotto e confine della struttura dati

I checkpoint `G1`–`G5` appartengono al piano di sviluppo e non devono essere
esposti all'operatore. Il percorso visibile usa i nomi delle attività:
`Macchina`, `Caricamento`, `Controllo file`, `Struttura dati`, quindi
`Elaborazione`, `Revisione` e `Pubblicazione` quando disponibili.

`Struttura dati` deve dare un risultato comprensibile già nel frontend: per
ogni fonte strutturata mostra le prime cinque righe in una tabella semantica e
la corrispondenza tra colonne sorgente e famiglie di concetti del grafo. Non
mostra un grafo fittizio: nodi e relazioni vengono proposti soltanto nel passo
successivo `Elaborazione`, dopo l'estrazione. Il criterio osservabile è
`AC-UX-014`.

### DEC-041 — Conferma per fonte e matrice di robustezza

L'accettazione della struttura avviene sulla card della singola fonte, accanto
al suo stato. Non esiste una conferma globale separata: quando tutte le fonti
strutturate pronte risultano `Confermata`, il passo è concluso automaticamente.
La decisione è idempotente e legata al profilo/fingerprint corrente.

Prima dell'avanzamento devono essere provati CSV con separatori e codifiche
diverse, record multilinea, righe corte e lunghe e un payload non testuale. Le
unità irregolari isolabili non fermano le righe valide e non alimentano il
grafo; un file non decodificabile blocca soltanto la propria fonte con errore
leggibile. Una fixture EN/IT/DE/mixed deve inoltre dimostrare conservazione del
testo originale e qualifica automatica del solo inglese. I criteri osservabili
sono `AC-TAB-001`, `AC-LANG-002` e `AC-UX-014`.

### DEC-042 — Sottografi source-scoped e aggiornamento incrementale

La pipeline non genera direttamente un grafo multisource monolitico. Dopo la
conferma della struttura, ogni fonte produce una SourceSubgraphRevision
immutabile. Deduplica e consolidamento intra-source avvengono prima della sua
review; l'operatore deve approvare quel sottografo prima che linking, merge o
conflitti cross-source possano essere calcolati. Approvare la fonte prima della
generation e approvare il sottografo dopo la generation sono due decisioni
distinte.

Se un workspace possiede già una versione pubblicata e riceve una nuova fonte,
la versione base e i sottografi preesistenti non vengono rigenerati. La nuova
fonte produce il proprio sottografo, viene approvata, quindi genera un delta di
linking/merge verso `base_graph_version`. La pubblicazione crea una nuova
versione monotona; non modifica quella precedente. Riferimenti osservabili:
`AC-WS-002`, `AC-WS-003`, `AC-HITL-002`, `AC-UX-005` e
`DC-CGRAPH-001`.

### DEC-043 — Ispezione source-scoped e sequenza CSV-first

Il sottografo della singola fonte deve essere realmente controllabile senza
esporre un editor libero. La stessa revisione viene rappresentata come grafo
navigabile, tabella completa e filtrabile dei nodi e tabella completa delle
relazioni; selezionare un nodo apre le evidence originali con locator. Liste e
dettagli lunghi sono scorrevoli e chiusi nella card della fonte.

La prima verifica Product Owner usa CSV sintetici multilingua per separare la
qualità della rappresentazione del grafo dalla variabilità dell'estrazione
documentale. I PDF rimangono preparati e visibili come seconda fase. Il loro
estrattore continua a riusare i servizi PDF e ontology workflow della pipeline
originaria e dovrà produrre lo stesso `SourceSubgraphRevision`; non è ammessa
una pipeline semantica parallela. Riferimenti osservabili: `AC-HITL-002` e
`AC-UX-005`.

### DEC-044 — Stop G3 e hardening del cuore semantico

Il Product Owner non accetta G3 sulla base dei soli CSV sintetici iniziali.
L'interfaccia di ispezione rimane una base valida, ma non dimostra che il
motore di costruzione del grafo sia maturo o agnostico.

L'audit del `2026-08-03` ha dimostrato che intestazioni inglesi canoniche e
alcuni sinonimi funzionano, mentre intestazioni italiane possono fallire e
nomi aziendali possono produrre grafi parziali senza blocco sufficiente. Sul
sottografo del workspace di prova le relazioni rispettavano domain/range, ma
36 nodi mancavano di almeno una proprietà obbligatoria, per 90 occorrenze
mancanti complessive, e comparivano 36 attributi non dichiarati dallo schema.

Prima di una nuova richiesta di accettazione devono essere completati, in
quest'ordine:

1. matrice CSV eterogenea e casi negativi fail-closed;
2. mapping configurabile e multilingua senza perdita semantica silenziosa;
3. generazione tramite il core neurosimbolico condiviso, non tramite un mapper
   parallelo limitato alle intestazioni note;
4. serializzazione e validazione strict di ogni `SourceSubgraphRevision`
   contro `ontology_schema.JSON` prima dell'approvazione;
5. misure di qualità per nodi, proprietà, relazioni, deduplica e provenance;
6. seconda campagna sui PDF riusando la pipeline esistente e lo stesso
   contratto source-scoped.

`DEC-043` resta valida per UX e ordine CSV→PDF, ma non costituisce evidenza di
readiness. Riferimenti osservabili: `AC-ONT-002`, `AC-TAB-004`, `AC-HITL-002`
e `AC-UX-005`.

### Guardrail comune — Ontologia invariata

`SourceAssetAssessment`, RawUnit, JoinSpec, OperatorAssertion,
ContextQualifier, OutcomeAssessment, Conflict, KnowledgeGap,
CandidateGraphRevision, tombstone, DelegationDecision, Checkpoint,
CalibrationProfile, ProviderConfig e metadata linguistici sono sidecar
operativi.

Non possono diventare:

- nuovi tipi di nodo;
- proprietà extra di nodi esistenti;
- nuovi tipi o proprietà di relazione;
- confidence, firmware, outcome o provenance dentro il graph payload.

`property_evidence`, merge/split lineage e tombstone appartengono
all'evidence index. `withdraw` produce una nuova versione, mai una delete
in-place. Le sole eccezioni sono proprietà già previste
dall'ontologia, incluse `material_context` e le proprietà source di
CorrectiveAction.

## Decisioni non di prodotto rinviate

Le seguenti possono essere prese nel futuro piano:

- librerie e struttura fisica dei moduli;
- schema SQLite;
- job runner;
- strategia esatta degli ID;
- framework frontend;
- packaging.

Non possono alterare le decisioni accettate sopra.
