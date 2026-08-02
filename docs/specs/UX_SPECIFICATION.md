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
Macchina → Fonti → Preparazione → Elaborazione → Revisione → Pubblicazione
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

La scelta deve essere disponibile almeno per:

- scope proposto dei PDF;
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

`join_apply` è delegabile soltanto per `JoinSpec` già approvati con
fingerprint identico; un nuovo join uno-a-molti o molti-a-molti resta manuale.

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

## 5. Passo 2 — Fonti

### FR-UX-006 — Upload e source inventory

La schermata deve accettare insieme e in caricamenti successivi:

- più PDF;
- CSV;
- XLSX;
- JSON e JSONL.

L'upload deve supportare drag-and-drop e file picker. Ogni file deve apparire
immediatamente come card o riga con:

- nome, formato, dimensione e hash abbreviato;
- lingua stimata;
- classe di autorità proposta;
- stato di upload, analisi e preparazione;
- numero di unità fisiche rilevate, quando disponibile;
- anomalie e azione richiesta;
- azioni `Anteprima`, `Configura`, `Escludi`.

Duplicati esatti devono essere riconosciuti prima dell'elaborazione costosa e
non devono generare una seconda copia. File non supportati devono essere
rifiutati con elenco dei formati ammessi. Una probabile macchina differente
deve produrre quarantena visibile, non un errore generico.

L'inventory deve poter essere filtrato per formato, stato e necessità di
intervento. L'operatore deve poter aggiungere nuove fonti senza creare un
nuovo grafo.

Per ogni fonte deve essere visibile l'assessment `compatible`, `uncertain` o
`incompatible`, con segnali, locator e motivazione. `uncertain` e
`incompatible` non possono apparire come semplici warning: restano fuori
dall'elaborazione finché non viene registrata l'azione consentita dal
contratto.

## 6. Passo 3 — Preparazione adattiva

### FR-UX-007 — Coda di preparazione comune

La schermata deve mostrare un'unica coda di fonti, ordinata mettendo prima i
blocchi. La UI apre il pannello adatto al formato senza cambiare il modello
mentale dell'operatore.

Ogni fonte deve terminare in uno stato esplicito:

```text
ready | excluded | duplicate | quarantined | failed_resumable | failed_terminal
```

Il pulsante `Continua all'elaborazione` deve restare disabilitato finché tutte
le fonti incluse non sono pronte e deve elencare i blocchi rimanenti.
Questi sono stati di preparazione; la Source conserva separatamente il proprio
stato di inventory e il relativo `SourceAssetAssessment`.

### FR-UX-008 — Preparazione PDF

Per un PDF la UI deve mostrare:

- elenco o miniature delle pagine con numero fisico;
- stato testo nativo, OCR, tabella o pagina illeggibile;
- sezioni e pagine proposte come rilevanti;
- preview sincronizzata di pagina, testo e tabelle estratte;
- include/exclude per pagina e selezione multipla;
- warning OCR a bassa confidence;
- verifica di appartenenza alla macchina;
- riepilogo dello scope prima dell'approvazione.

La conferma deve registrare esattamente pagine incluse, escluse e motivazioni.

### FR-UX-009 — Preparazione CSV, XLSX e JSON

Per una fonte strutturata la UI deve mostrare:

- inventario di tabelle, fogli o array/path;
- preview paginata di un campione, senza caricare migliaia di righe nel DOM;
- header rilevato, tipi, null rate, cardinalità, esempi e anomalie;
- inclusione ed esclusione di tabelle e colonne;
- correzione di header e tipi;
- ruolo semantico proposto per i campi;
- preview separata dei semantic text per sintomo, causa, azione, componente e
  codice;
- chiavi e join, con cardinalità attesa e preview del risultato;
- lingua, autorità e costanti applicate;
- confronto con un mapping profile riutilizzabile.

Il mapping proposto deve essere modificabile prima dell'approvazione. Gli
override devono essere validati inline. Join molti-a-molti, array uno-a-molti
e colonne chiave instabili devono essere bloccanti finché non viene scelta una
strategia esplicita.

## 7. Passo 4 — Elaborazione

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

Una percentuale non determinabile non deve essere simulata. In quel caso la UI
deve mostrare contatori e attività corrente.

`Riprendi` continua lo stesso run, stessa configurazione e ultimo checkpoint
`committed`. `Riprova` riesegue soltanto l'unità fallita e riusa una risposta
provider già persistita per lo stesso request hash. Se mapping, join,
semantic template, provider/modello, prompt, lingua, soglia o asset identity
cambiano, la UI deve offrire `Avvia nuovo run`, mostrando cosa viene
invalidato; non deve presentarlo come resume.

## 8. Passo 5 — Revisione

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

## 9. Passo 6 — Pubblicazione

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
| `sources_required` | Fonti | `Aggiungi fonti` |
| `preparation_required` | Preparazione | `Completa preparazione` |
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
