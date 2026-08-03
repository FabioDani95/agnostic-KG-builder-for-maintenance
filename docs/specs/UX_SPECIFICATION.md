# Specifica UX — flusso unificato multi-formato

## 1. Scopo

Questo documento definisce l'esperienza utente normativa del frontend MVP.
L'interfaccia deve guidare un operatore tecnico dalla definizione della
macchina alla pubblicazione di un unico knowledge graph, indipendentemente dal
numero e dal formato delle fonti.

La UX non deve esporre l'architettura interna come sequenza di pagine
indipendenti. `Scoping`, profiling, mapping, review, quality e publish sono
capacità della pipeline, ma per l'operatore devono apparire come passi
coerenti di un solo lavoro.

## 2. Principi

### FR-UX-001 — Un solo percorso principale

Il percorso principale deve essere:

```text
Macchina → Caricamento → Controllo file → Struttura dati → Elaborazione → Revisione → Pubblicazione
```

Dopo almeno una pubblicazione deve essere disponibile `Esplora`, in sola
lettura. La chat diagnostica di test può essere raggiunta da `Esplora`.

In ogni schermata deve esistere:

- un solo invito all'azione primario;
- un'indicazione visibile del passo corrente;
- la condizione necessaria per proseguire;
- un riepilogo degli elementi completi, da verificare e bloccanti;
- salvataggio automatico delle modifiche persistibili.

La navigazione non deve permettere di aggirare i tre gate HITL definiti dalla
specifica master.

### FR-UX-002 — Linguaggio dell'operatore

Etichette, messaggi e azioni devono descrivere il lavoro dell'operatore, non
nomi di route, classi o stage interni.

I nomi dei checkpoint di sviluppo `G1`–`G5` e le espressioni `Gate 1`,
`Gate 2` e successive non devono comparire nell'interfaccia di prodotto.
Restano ammessi soltanto nella documentazione, negli artifact e nei test
interni.

Esempi:

- `Prepara le fonti`, non `Scoping/Mapping Engine`;
- `Costruisci il grafo candidato`, non `Run generation`;
- `Elementi da verificare`, non `Low-confidence triples`;
- `Pubblica versione`, non `Export ontology`.

Il dettaglio tecnico, gli identificativi e i payload devono restare
disponibili in una sezione espandibile.

### FR-UX-003 — Progressive disclosure e default sicuri

Le scelte tecniche non necessarie al flusso ordinario devono essere raccolte
in `Impostazioni avanzate`, chiuse di default. In particolare:

- provider e modello devono provenire dalla configurazione locale;
- soglie approvate devono essere prese dal profilo di pipeline;
- lingua canonica e template devono avere default espliciti;
- l'operatore non deve scegliere un modello per ogni stage nel flusso
  ordinario.

Ogni override deve mostrare l'impatto su cache, calibrazione e riprocessamento.

La progressive disclosure è un vincolo osservabile, non soltanto uno stile
grafico. Nella superficie ordinaria di ogni passo:

- deve essere presentato un solo compito o una sola decisione alla volta;
- gli esiti positivi devono comparire vicino all'elemento interessato, senza
  box riepilogativi che ripetano le stesse informazioni;
- preview complete, metriche di profiling, locator, hash e payload tecnici
  devono restare chiusi finché l'operatore non chiede `Mostra dettagli`;
- non deve essere richiesta una conferma per ogni pagina, riga o colonna
  quando il sistema non ha rilevato un'eccezione;
- quando non esistono blocchi, l'unico invito primario deve essere quello per
  proseguire al passo successivo.

Nel passo `Struttura dati` l'anteprima tabellare ordinaria mostra al massimo le
prime 5 righe. Ricerca, paginazione o dettaglio tecnico, quando introdotti,
consentono l'ispezione del resto senza caricare o presentare centinaia di
elementi insieme.

### FR-UX-018 — Scelta fra verifica manuale ed esecuzione automatica

Per ogni passo delegabile la UI deve permettere all'operatore di scegliere,
limitatamente alle modalità ammesse per quello step da `DC-DELEGATION-001`:

- `Lo verifico io`: apre i controlli e richiede l'approvazione puntuale;
- `Procedi automaticamente`: esegue lo stesso step usando configurazione,
  mapping, soglie e default approvati;
- `Decidi caso per caso`: applica automaticamente le decisioni sicure e porta
  all'operatore soltanto eccezioni, conflitti e valori sotto soglia.

La UI non deve offrire combinazioni vietate: `automatic` non è disponibile
per `nonblocking_review` e `exceptions_only` non è disponibile per
`advance_workflow`.

Nella microcopy può essere usato il termine `Salta`, ma deve essere sempre
accompagnato da `esegui automaticamente`. Saltare non significa omettere lo
step, perdere dati o disattivare validazioni.

La scelta deve essere disponibile, nelle fasi successive che la richiedono,
almeno per:

- mapping proposto quando esiste un profilo compatibile;
- inclusione proposta di fogli, tabelle e colonne;
- normalizzazioni deterministiche;
- deduplica esatta;
- auto-stage sopra soglia;
- revisione degli elementi non bloccanti;
- avanzamento automatico al passo successivo.

Il catalogo stabile degli step delegabili è:

```text
pdf_scope
structured_selection
mapping_apply
join_apply
normalization_apply
exact_deduplication
candidate_auto_stage
nonblocking_review
advance_workflow
```

`pdf_scope` resta un identificatore interno storico ma non è esposto nel gate
G1: il caricamento include sempre tutte le pagine e non richiede delega o
conferma separata.

`join_apply` è delegabile soltanto per `JoinSpec` già approvati con
fingerprint identico; un nuovo join uno-a-molti o molti-a-molti resta manuale.

Nel passo `Struttura dati` la modalità iniziale è `Decidi caso per caso`: profiling, proposta
di mapping, normalizzazioni deterministiche e strutture non ambigue avanzano
automaticamente, mentre la UI porta in primo piano soltanto eccezioni e
decisioni bloccanti. `Lo verifico io` e `Procedi automaticamente` restano
disponibili tramite una sola azione secondaria `Cambia modalità`; non devono
apparire come tre call to action concorrenti su ogni file o sotto-passo.

Quando viene scelta l'automazione, la UI deve mostrare prima dell'esecuzione:

- cosa verrà deciso automaticamente;
- configurazione e soglie applicate;
- elementi che resteranno comunque manuali;
- impatto su cache e riprocessamento;
- azione `Torna alla verifica manuale`.

Il sistema deve registrare la scelta per step e consentire di cambiarla per i
run successivi o durante un run. Ogni scelta, revoca o supersessione è
append-only, mostra lo scope e diventa efficace dal primo checkpoint successivo
per unità non ancora preparate. Un risultato automatico deve restare
ispezionabile e reversibile finché non viene pubblicato.

Non sono delegabili:

- conferma iniziale dell'identità della macchina;
- risoluzione di fonti attribuite a una macchina differente;
- conflitti bloccanti o guard simboliche fallite;
- override che inventerebbero un valore mancante;
- pubblicazione finale.

In `Decidi caso per caso`, gli elementi sicuri e le altre source indipendenti
continuano; le eccezioni vengono accodate fino al
`exception_queue_limit` della configurazione (default `100`). Raggiunto il
limite, la pipeline applica backpressure al checkpoint sicuro della sola
partizione coinvolta. Conferma macchina, conflitto globale bloccante, guard
ontologica fallita e publish fermano invece l'intero run. La UI deve mostrare
quale scope è fermo e quale continua.

## 3. Struttura globale

### FR-UX-004 — Application shell

La route iniziale deve aprire una home semplice dei workspace persistiti. Ogni
card mostra almeno macchina, marca/modello, stato derivato, numero di documenti
e ultimo aggiornamento; l'azione primaria apre il workspace tramite il suo ID.
Un'azione `+ Nuovo workspace` avvia un onboarding vuoto e salva una nuova
coppia Workspace/Asset con ID distinti, senza alterare quelli esistenti. La
home non introduce utenti, ruoli, eliminazione o amministrazione avanzata
multi-workspace. Un solo workspace è selezionato e operativo alla volta.

Il frontend deve avere una sola shell composta da:

1. header con nome macchina, stato workspace, versione pubblicata corrente,
   stato del provider e selettore lingua UI;
2. stepper persistente con i sei passi del flusso;
3. area di lavoro centrale;
4. pannello contestuale per riepilogo, blocchi e aiuto;
5. indicatore di autosave e ultimo salvataggio.

Le vecchie destinazioni tecniche devono essere consolidate:

| Destinazione corrente | Destinazione target |
|---|---|
| `Nuova sessione` | avvio o ripresa del workspace macchina |
| `Dashboard` | riepilogo del passo corrente |
| `Scoping` | `Preparazione`, adattiva per formato |
| `Review Center` | `Revisione` |
| `Qualità` e `Campi richiesti` | filtri e code dentro `Revisione` |
| `Export` | `Pubblicazione` |
| `Grafo` | `Esplora`, sola lettura e solo dopo publish |

`Sessioni` può restare come cronologia dei run e diagnostica operativa, ma non
deve essere un passo obbligatorio né il confine del knowledge graph.

## 4. Passo 1 — Macchina

### FR-UX-005 — Onboarding macchina

La prima schermata deve:

- creare o mostrare l'unico `Asset` del workspace;
- distinguere campi obbligatori e opzionali secondo ontologia;
- accettare alias e identificativi sorgente nel sidecar;
- spiegare che tutte le fonti successive devono riferirsi alla stessa
  macchina;
- mostrare una preview compatta della scheda risultante;
- richiedere conferma esplicita per chiudere la parte identità del Gate 1.

Se il workspace contiene già una macchina, la schermata deve proporre la
ripresa. Cambiare l'identità confermata deve invalidare le preparazioni
dipendenti e richiedere una conferma con impatto visibile.

## 5. Passi 2 e 3 — Caricamento e controllo file

### FR-UX-006 — Upload e source inventory

La schermata deve accettare insieme e in caricamenti successivi:

- più PDF;
- CSV;
- XLSX;
- JSON e JSONL.

L'upload deve supportare drag-and-drop e file picker. Ogni file deve apparire
immediatamente come card o riga con:

- nome, formato, dimensione e hash abbreviato;
- classe di autorità scelta;
- stato di caricamento e preparazione;
- azione di rimozione con una × rossa nell'angolo e conferma esplicita prima
  di procedere.

Duplicati esatti già attivi devono essere riconosciuti dall'impronta prima
dell'invio, segnalati chiaramente e non ammessi; la API applica lo stesso
vincolo con `409`. Se la fonte era stata rimossa, lo stesso contenuto può
ripristinarla senza duplicare il raw. File non supportati devono essere
rifiutati già alla selezione, con elenco dei formati ammessi, e dalla API con
`415` come difesa. L'app non deve analizzare il
contenuto per confermare o negare l'appartenenza: l'operatore è responsabile
della scelta dei documenti.

L'inventory deve poter essere filtrato per formato, stato e necessità di
intervento. L'operatore deve poter aggiungere nuove fonti senza creare un
nuovo grafo.

Se il workspace possiede già una versione pubblicata, una nuova fonte deve
essere marcata `Nuova` e percorrere i passi successivi soltanto per il proprio
scope. Le fonti già incluse e il grafo pubblicato restano consultabili e
immutati; la UI mostra che il nuovo sottografo verrà confrontato con la
versione di base e che una nuova versione nascerà soltanto dopo review e
pubblicazione.

Non deve esistere una sezione di conferma/esclusione dell'associazione alla
macchina. La rimozione del file è l'unica correzione necessaria a G1.
Non deve esistere neppure un box riepilogativo finale: lo stato `Caricato`
appare accanto alla × di ogni documento. Lo stepper separa il caricamento dal
suo esito leggibile `Controllo file`; questo controllo non apre una nuova
matrice di conferme e risulta completato automaticamente quando tutti i file
accettati sono integri e pronti.

## 6. Passo 4 — Struttura dati

### FR-UX-007 — Coda di preparazione comune

La schermata G1 mostra un unico inventory compatto. Il sistema completa la
preparazione di intake automaticamente senza aprire pannelli tecnici per
formato.

Ogni fonte deve terminare in uno stato esplicito:

```text
ready | excluded | duplicate | quarantined | failed_resumable | failed_terminal
```

Il pulsante `Continua all'elaborazione` deve restare disabilitato finché tutte
le fonti incluse non sono pronte e deve elencare i blocchi rimanenti.
Questi sono stati interni di preparazione; non introducono un gate di
attribuzione della fonte.

Entrando in `Struttura dati`, l'inventory già controllato non deve essere duplicato
né richiedere un nuovo caricamento. Ogni card conserva nome e stato del file e
aggiunge soltanto l'esito utile del nuovo passo: `Preparato`, `Da correggere`
oppure `Non utilizzabile`, con causa e azione disponibili nello stesso
contesto.

### FR-UX-008 — Preparazione PDF

Per un PDF la UI G1 deve mostrare soltanto che:

- il file è stato caricato;
- la preparazione automatica è completata;
- tutte le pagine fisiche sono incluse;
- non è richiesta alcuna azione pagina-per-pagina.

Il sistema conserva internamente numerazione, testo, tabelle, OCR, quality
flag e accounting per le fasi successive. Nessuna preview massiva o checkbox
per pagina deve essere caricata nel DOM del gate G1.

### FR-UX-009 — Preparazione CSV, XLSX e JSON

Nel caricamento una fonte strutturata viene mostrata come pronta; righe e
record restano integralmente disponibili e non richiedono selezione umana. Le
capacità seguenti appartengono al passo `Struttura dati`:

Il percorso deve restare lineare e usare la modalità automatica con
eccezioni:

1. il sistema profila tutte le fonti e propone mapping e semantic text;
2. la UI mostra una card compatta per fonte e apre soltanto la prima eccezione
   bloccante;
3. risolta un'eccezione, porta alla successiva senza mostrare una matrice
   completa da approvare campo per campo;
4. un join compare soltanto quando esiste una proposta esplicita da valutare;
   nessun join è il default valido;
5. quando tutte le fonti hanno un esito, un'unica azione
   `Conferma` sulla card di ciascuna fonte registra l'accettazione puntuale;
   non deve esistere una conferma globale separata in fondo alla pagina.

Una fonte senza anomalie non richiede interazione puntuale. La sua card mostra
in linguaggio semplice strutture trovate, record preparati ed eventuali
avvisi; il mapping completo, il profiling e i locator restano in
`Dettagli tecnici`.

Per una fonte strutturata la UI deve mostrare:

- nella superficie ordinaria, un riepilogo delle strutture trovate, dei record
  preparati e delle sole anomalie che richiedono intervento;
- una tabella semantica compatta con le prime 5 righe e intestazioni leggibili,
  ottenuta dai dati realmente profilati;
- una mappa leggibile dalle colonne sorgente alle famiglie di concetti del
  grafo (`Componente`, `Sintomo/osservazione`, `Causa`, `Azione`,
  `Codice errore`), dichiarando che nodi e collegamenti saranno proposti nel
  successivo passo `Elaborazione`;
- un riepilogo delle lingue rilevate che distingua inglese qualificato da
  italiano, tedesco, mixed o unknown conservati ma non ancora idonei
  all'alimentazione automatica del grafo;
- l'azione `Conferma` nella stessa card, disponibile soltanto dopo la
  risoluzione delle eccezioni della fonte e persistita per il suo fingerprint;
- su richiesta, inventario di tabelle, fogli o array/path e preview paginata
  del campione;
- nei dettagli, header rilevato, tipi, null rate, cardinalità, esempi e
  anomalie;
- quando serve una correzione, inclusione o esclusione di tabelle e colonne,
  header, tipo e ruolo semantico proposto nello stesso pannello;
- preview separate dei semantic text per sintomo, causa, azione, componente e
  codice, senza una tabella massiva;
- soltanto per un join esplicito, chiavi, cardinalità attesa e confronto
  leggibile prima/dopo;
- nei dettagli, lingua, autorità, costanti e mapping profile applicato.

Il mapping proposto deve essere modificabile prima dell'approvazione. Gli
override devono essere validati inline. Join molti-a-molti, array uno-a-molti
e colonne chiave instabili devono essere bloccanti finché non viene scelta una
strategia esplicita.

Ogni eccezione deve spiegare in quest'ordine: che cosa è stato trovato, perché
serve una decisione, quale scelta è consigliata e che effetto avrà. Termini
come fingerprint, cardinalità, JSONPath e null rate non devono essere necessari
per completare il percorso ordinario; restano disponibili nel dettaglio.

## 7. Passo 5 — Elaborazione

### FR-UX-010 — Avvio, progresso e recupero

La schermata deve offrire un'unica azione primaria:
`Costruisci il grafo candidato`.

Prima dell'avvio deve mostrare:

- macchina;
- fonti incluse, escluse e in quarantena;
- conteggio pagine, righe e tabelle;
- provider e modello, in forma compatta;
- destinazione locale/remota e preview esatto dei campi o testi inviati per
  ogni stage;
- esito del preflight;
- configurazioni che invalidano cache o calibrazione.

Durante il run deve mostrare:

- stage corrente in linguaggio comprensibile;
- avanzamento complessivo e per fonte basato su contatori reali;
- processati, duplicati, esclusi, quarantinati e falliti;
- cache hit, chiamate e retry in dettaglio espandibile;
- azioni coerenti con lo stato: `Interrompi`, `Riprendi`, `Riprova`;
- indicazione chiara che chiudere il browser non cancella il lavoro
  checkpointato.

La generazione procede per fonte, non come grafo multisource monolitico. Per
ogni fonte approvata in `Struttura dati`, la UI deve mostrare una card con:

- stato `In attesa`, `Generazione`, `Da verificare`, `Approvato` o `Da
  correggere`;
- conteggio di nodi, relazioni, evidenze e duplicati consolidati nel
  sottografo della fonte;
- preview leggibile del sottografo e accesso alle evidenze originali;
- unica azione primaria `Approva sottografo` quando non esistono blocchi;
- azione secondaria `Segnala da correggere` quando il risultato non è
  accettabile.

La preview non può essere un elenco statico o una rappresentazione soltanto
decorativa. Deve offrire tre viste coerenti dello stesso sottografo:

- un grafo navigabile in cui selezionare un nodo, evidenziare le relazioni
  dirette e aprire le evidenze con locator alla riga o pagina originale;
- una tabella completa dei nodi, ricercabile e filtrabile per tipo, con
  conteggi di relazioni ed evidenze;
- una tabella completa delle relazioni, con nodo di partenza, relazione, nodo
  di arrivo ed evidenze.

Le liste lunghe devono restare in contenitori scorrevoli e la UI deve partire
da una vista sintetica, senza costringere l'operatore a controllare centinaia
di righe una per una. La decisione resta unica e source-scoped: il dettaglio
serve a ispezionare il risultato, non a trasformare il grafo in un editor.

La prima visualizzazione implementata può essere usata per collaudare
navigazione e progressive disclosure, ma non costituisce accettazione del
motore. Prima di abilitare `Approva sottografo`, la card deve mostrare
`Ontologia valida` e `Mapping completo`, derivati da controlli backend reali.
Con proprietà obbligatorie mancanti, proprietà extra, domain/range errati,
colonne diagnostiche non mappate o output parziale non classificato, la card
resta `Da correggere`, spiega il primo blocco e non offre l'approvazione.

L'hardening procede prima su una matrice eterogenea di CSV e soltanto dopo sui
PDF. I PDF restano visibili come `Seconda fase`: conservano preparazione ed
evidenze e confluiranno nello stesso contratto `SourceSubgraphRevision`, senza
creare una pipeline semantica parallela.

Il sistema non deve avviare entity linking o merge cross-source finché ogni
sottografo incluso non è stato approvato. L'approvazione della struttura dati
autorizza la generazione; l'approvazione del sottografo autorizza il merge.
Sono decisioni diverse e persistite separatamente.

Una percentuale non determinabile non deve essere simulata. In quel caso la UI
deve mostrare contatori e attività corrente.

`Riprendi` continua lo stesso run, stessa configurazione e ultimo checkpoint
`committed`. `Riprova` riesegue soltanto l'unità fallita e riusa una risposta
provider già persistita per lo stesso request hash. Se mapping, join,
semantic template, provider/modello, prompt, lingua, soglia o asset identity
cambiano, la UI deve offrire `Avvia nuovo run`, mostrando cosa viene
invalidato; non deve presentarlo come resume.

## 8. Passo 6 — Revisione

### FR-UX-011 — Inbox di review

La review deve essere una coda operativa con categorie:

1. `Bloccanti`;
2. `Ambigui`;
3. `Conflitti`;
4. `Informativi`;
5. `Auto-staged`.

Ogni elemento deve mostrare tipo di decisione, confidence, guard simboliche,
fonti coinvolte e motivo della review. Filtri e contatori devono sostituire le
schermate separate `Qualità` e `Campi richiesti`.

La coda multisource si apre soltanto dopo la barriera di approvazione dei
sottografi. Deve distinguere chiaramente:

- deduplica e merge interni già applicati alla singola fonte;
- link o merge proposti fra fonti diverse;
- link o merge proposti verso nodi della versione pubblicata di base;
- conflitti e claim che devono coesistere senza merge.

L'elemento selezionato deve presentare nello stesso contesto:

- evidenza originale con locator e preview;
- proposta candidata e impatto sul grafo;
- entità esistenti o alternative;
- motivi del punteggio e vincoli;
- azioni permesse.

### FR-UX-012 — Modifica controllata, non editor libero

Le sole operazioni che possono cambiare il candidate graph sono decisioni
HITL legate a un candidato o conflitto:

- approvare;
- rifiutare;
- correggere proprietà proposte;
- selezionare un'entità esistente;
- confermare o rifiutare un merge;
- separare una proposta;
- approvare o rifiutare un withdrawal;
- escludere un'evidenza;
- risolvere un conflitto;
- riaprire una decisione.

Ogni modifica deve:

- restare entro tipi, proprietà e relazioni ontologiche;
- conservare almeno una evidenza verificabile;
- essere validata prima del salvataggio;
- registrare before/after e decisione operatore;
- aggiornare immediatamente stato e impatto sul publish.

Non devono esistere:

- canvas o pagina di graph editing;
- creazione arbitraria di nodi o relazioni;
- eliminazione diretta dal grafo;
- modifica di JSON pubblicati;
- route, tool chat o API generiche di graph mutation;
- collegamento “Apri editor”.

`Modifica` nella review significa correggere la proposta corrente, non
manipolare liberamente il grafo.

`Riapri` deve mostrare quale decisione viene superata e quale delta staged sarà
invertito. L'azione è disponibile soltanto prima del publish e l'inversione è
atomica nella revisione corrente. Dopo il publish occorre avviare un nuovo run
basato sulla versione pubblicata e sottoporre a review un candidate `withdraw`,
`supersede` o `update`: la decisione pubblicata non viene riaperta in-place.
Non è un semplice cambio di badge. `Rimuovi` non è un'azione generica: compare
soltanto come approval di un candidate `withdraw`.

### FR-UX-013 — Revisione aggregata

Gli elementi auto-staged possono essere confermati in forma aggregata solo
dopo che la UI ha mostrato:

- numero e distribuzione per tipo;
- campione ispezionabile;
- soglie applicate;
- assenza di guard o conflitti;
- effetto complessivo sul delta.

Le azioni bulk non devono essere disponibili per bloccanti, conflitti o
elementi sotto soglia.

## 9. Passo 7 — Pubblicazione

### FR-UX-014 — Gate di publish

La schermata deve mostrare prima della conferma:

- versione sorgente e nuova versione;
- diff di nodi, relazioni, merge e nuove evidenze;
- copertura per fonte;
- qualità e validazione ontologica;
- decisioni aperte;
- fonti escluse, fallite o in quarantena;
- artifact che verranno creati;
- impatto della nuova versione sulla chat.

Il riepilogo deve distinguere:

- già inclusi nel delta: candidate `approved`;
- proposti per approvazione aggregata al click finale: candidate
  `auto_staged` con calibrazione valida; fino alla creazione atomica delle
  decisioni aggregate restano bloccanti;
- esclusi risolti: `rejected` e non bloccanti esplicitamente esclusi;
- bloccanti: review aperte, conflitti bloccanti, withdrawal non decisi,
  calibration profile invalido o violazioni;
- invariati dalla base;
- rimossi soltanto tramite withdrawal, merge o split approvati.

Se esiste un blocco, la UI deve disabilitare `Pubblica versione` e offrire un
collegamento al punto esatto da risolvere. Con gate superato deve richiedere
una conferma esplicita che riporti numero di versione e macchina.

La pubblicazione non deve essere chiamata `export`: il download dei JSON è
un'azione secondaria successiva.

Durante la scrittura la UI mostra `Pubblicazione in corso`; la versione diventa
selezionabile soltanto dopo il commit atomico del bundle. Un fallimento
intermedio non deve mostrare graph o evidence index parziali e deve offrire
retry sullo stesso publication attempt.

## 10. Esplora e chat

### FR-UX-015 — Esplorazione sola lettura

Dopo la pubblicazione la UI deve offrire:

- versione selezionabile;
- ricerca per nome, codice e tipo;
- vista grafo e vista tabellare;
- filtri per tipo, fonte e confidence;
- pannello di proprietà, relazioni e provenienza;
- apertura dell'evidenza originale;
- confronto tra due versioni;
- download di graph, evidence index e manifest;
- accesso alla chat diagnostica minima.

La visualizzazione deve essere sola lettura. Non deve contenere azioni per
aggiungere, modificare, collegare o cancellare nodi e relazioni.

## 11. Stati UX e disponibilità delle azioni

| Stato workspace | Destinazione proposta | Azione primaria |
|---|---|---|
| `empty` | Macchina | `Conferma macchina` |
| `sources_required` | Caricamento | `Aggiungi documenti` |
| `preparation_required` | Struttura dati | `Conferma fonte` sulla card |
| `ready` | Elaborazione | `Costruisci il grafo candidato` |
| `processing` | Elaborazione | nessuna; mostra avanzamento |
| `paused` | Elaborazione | `Riprendi` |
| `failed_resumable` | Elaborazione | `Riprendi` o `Riprova` secondo l'errore |
| `failed_terminal` | Elaborazione | `Avvia nuovo run` |
| `awaiting_review` | Revisione | `Risolvi elemento` |
| `ready_to_publish` | Pubblicazione | `Pubblica versione` |
| `published` | Esplora | `Esplora grafo` |

Una URL aperta direttamente deve risolvere lo stato corrente e reindirizzare
al primo blocco precedente, spiegandone il motivo.

## 12. Errori, feedback e sicurezza

### FR-UX-016 — Errori azionabili

Ogni errore mostrato deve avere:

- titolo comprensibile;
- fonte o oggetto coinvolto;
- causa sintetica;
- cosa è stato preservato;
- azione consigliata;
- possibilità di dettaglio tecnico copiabile;
- indicazione `riprendibile` o `richiede nuova elaborazione`.

Gli errori di un file non devono nascondere lo stato delle altre fonti. Un
errore non bloccante deve permettere esclusione o quarantena esplicita.

### FR-UX-017 — Accessibilità e robustezza

Il flusso deve essere utilizzabile da tastiera e deve:

- avere focus visibile e ordine logico;
- non usare il colore come unico indicatore;
- associare label e messaggi di errore ai campi;
- annunciare cambi di stato e avanzamento;
- preservare il contesto dopo refresh;
- chiedere conferma soltanto per publish, invalidazioni ampie o esclusioni con
  lavoro già eseguito;
- evitare modali annidati;
- gestire correttamente almeno viewport desktop da `1024px` in su.

L'MVP è desktop-first; una UI mobile completa è fuori perimetro.

## 13. Lingua dell'interfaccia

La lingua della UI e la lingua delle fonti sono concetti separati.

- la shell deve mantenere italiano e inglese selezionabili;
- la scelta UI non deve tradurre raw, codici, unità o citazioni;
- il tedesco dell'interfaccia non è richiesto nell'MVP;
- warning e badge devono distinguere una lingua rilevata da una lingua
  qualificata semanticamente.

## 14. Criterio di non regressione UX

La trasformazione del frontend è completa soltanto quando:

- un operatore può attraversare il flusso senza conoscere la pipeline interna;
- PDF e fonti strutturate sono visibili nello stesso source inventory;
- la preparazione si adatta al formato ma usa gli stessi stati e gate;
- quality, required fields e review sono un'unica inbox;
- publish è distinto da download;
- il grafo pubblicato è esplorabile ma non modificabile;
- nessun link, route o tool espone l'editor libero rimosso.
