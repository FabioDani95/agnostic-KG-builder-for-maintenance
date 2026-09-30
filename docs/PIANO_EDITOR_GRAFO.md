# Piano di integrazione dell'editor del grafo

Data: 30 settembre 2026. Stato: **specifica pronta per l'implementazione da parte di un agente AI;
funzionalità non ancora implementata**. Flusso aggiornato con la precisazione dell'utente:
pulsante dedicato, avanti/indietro, accettazione finale e perdita delle modifiche all'uscita.

Analisi della codebase corrente, commit `043f56b`, e della cartella locale
`/Users/fabio.daniele/Coding/kg-graph-editor_V1/` (`app.js`, `graph.js`, formato e documentazione).
La cartella di riferimento non contiene un repository Git consultabile: i riferimenti sotto
identificano file e funzioni, non una release del tool.

Le decisioni di questo documento sono il contratto del primo rilascio. La sezione 4 definisce
il percorso utente, la 9 i contratti applicativi e la 15 gli incarichi eseguibili dall'agente.
«Nuova versione» è il termine mostrato all'utente; «revisione» indica nel codice quella
versione creata accettando modifiche umane, distinta da una nuova estrazione.

## 1. Risultato da ottenere

Una persona deve poter aprire un grafo già prodotto, capirne il contenuto attraverso tabelle
leggibili, correggere nodi e relazioni, controllare le conseguenze e **salvare una nuova
revisione**. Deve poterlo fare subito dopo l'estrazione oppure tornando sul grafo in seguito.

L'editor diventa una modalità della schermata del grafo, dentro l'applicazione attuale:
stessa navigazione, stessi componenti, stessa estetica, stesso manuale e stessa cronologia.
Le tabelle sono lo strumento principale di lavoro; il grafo e le pagine del manuale aiutano
a capire e verificare ciò che si sta modificando.

Requisiti della richiesta:

- Riutilizzare le funzionalità migliori di `kg-graph-editor_V1`: tabelle editabili per tipo,
  filtri, ricerca, ordinamento, navigazione fra elementi e controlli con accesso alle righe.
- Consentire un intervento umano effettivo: modificare, aggiungere ed eliminare nodi e relazioni.
- Il pulsante dedicato si chiama sempre «Modifica grafo», subito dopo la generazione e in seguito.
- Il percorso ha passi espliciti e pulsanti «Indietro» e «Avanti»; navigare non salva.
- Solo «Accetta modifiche e crea nuova versione» pubblica una revisione distinta;
  l'originale resta disponibile. L'accettazione chiude il lavoro senza una seconda approvazione.
- Prima dell'accettazione le modifiche esistono solo in memoria. Uscendo senza salvarle
  vengono perse: nessun autosalvataggio, recupero di bozze o salvataggio implicito.
- Integrare l'intero percorso, dalla fine dell'estrazione alla libreria e alla riapertura.
- Predisporre un punto di estensione per suggerimenti AI, lasciando l'editor utilizzabile
  interamente a mano. La scelta delle funzioni AI viene dopo.

Le prescrizioni del progetto allegato, come «nessun backend», JavaScript vanilla e salvataggio
del file originale, descrivono quel prodotto. **Non sono requisiti di questa integrazione.**
Qui valgono React/TypeScript, FastAPI, persistenza nel workspace e creazione di revisioni.
Anche i vecchi prompt in `docs/` sono contesto storico; per l'integrazione prevalgono il codice
attuale, [DESIGN.md](DESIGN.md) e la richiesta presente.

## 2. Che cosa esiste già e dove intervenire

| Area | Riscontro nel codice | Conseguenza per il piano |
| --- | --- | --- |
| Vista del grafo | `frontend/src/screens/FinishedGraph.tsx`: filtro verificate/in dubbio, ricerca su sintomi e codici, selezione, pannello prove, cambio versione | Estenderla a uno spazio comune con viste Grafo, Nodi, Relazioni e Controlli |
| Informazioni di dettaglio | `components/EvidencePanel.tsx`: citazioni, condizioni delle occorrenze e collegamenti; non espone un form completo per `properties` | Riutilizzare la lettura delle prove e aggiungere editor tipizzati per i campi |
| Tabelle | `components/Table.tsx`: tabella su griglia di 12 colonne, ordinamento, righe cliccabili, nessun editing o filtro per colonna | Condividere stile e utilità; creare una tabella editor adatta a molte colonne, senza forzare input dentro righe che navigano al clic |
| Visualizzazione | `graph/Graph3D.tsx`: selezione, focus, layout, inquadratura; API imperativa con `relayout` e `fit` | Riutilizzare il renderer, aggiungendo focus su un elemento e conservazione della vista tra schede |
| Navigazione | `App.tsx`, `api/client.ts`, `screens/ManualScreen.tsx`, `screens/Library.tsx`, `screens/LiveRun.tsx` | Integrare ingresso all'editor, rientro dopo il salvataggio e revisione corrente |
| Prossimo passo | `flow/steps.ts`, `StatusProvider.tsx`: assumono versioni prodotte da esecuzioni e considerano soprattutto l'ultima versione | Aggiungere il caso revisione e non perdere esecuzioni o domande ancora aperte su un'altra versione |
| Catalogo | `backend/ui/catalog.py`: una versione è una cartella di esecuzione; contatori da `report.json`, replay da `state/` o eventi | Introdurre revisioni esplicite, con riepiloghi propri e senza simularle come esecuzioni |
| API | `backend/ui/api.py`: lettura del grafo; nessuna API per modificarne il contenuto | Aggiungere validazione, salvataggio revisioni, differenze e revisione umana |
| Risposte e approvazione | `backend/ui/jobs.py`: `copy_version` copia lo stato della campagna; `apply` e `approve` riprendono la pipeline | Non usare queste operazioni per salvare l'editor: potrebbero rigenerare il grafo e cancellare le correzioni |
| Formato | `backend/kg_v3/export.py`: `kg-v3-graph-2`, nodi piatti, archi con occorrenze e certificati, relazioni derivate, esclusioni e rapporto incorporato | L'editor lavora sul formato nativo, preservando tutti i dati non modificati |
| Ontologia | `ontology_schema.JSON`, `backend/kg_v3/ontology.py`, `GET /api/ontology` | Tipi, campi e compatibilità degli estremi vengono dallo schema dell'applicazione |
| Fonti | `backend/ui/evidence.py`, `components/PageDialog.tsx`: segmenti e pagine del PDF | Riutilizzare la visualizzazione; ancorare i riferimenti delle revisioni alla fonte effettiva |

Problemi concreti da anticipare:

1. Il formato del riferimento è `nodes: {tipo: [...]}` e `relationships` con `from_id/to_id`;
   qui è `nodes: [...]` e `edges` con `from/to`. Una conversione usata per risalvare rischierebbe
   di perdere certificati, occorrenze, condizioni, campi sconosciuti e rapporto.
2. `FinishedGraph` mostra soltanto nodi usati dagli archi visibili, oltre alla macchina.
   Un nodo appena aggiunto e ancora isolato scomparirebbe: nell'editor deve rimanere visibile.
3. `GraphNode.properties` è un dizionario generico e il tipo frontend `Graph` non comprende
   tutto il JSON salvato, per esempio `report`. Non si può ricostruire il file solo dai tipi UI.
4. La API dell'ontologia espone oggi nome e obbligatorietà dei campi, ma non `type`, `items`
   e `unique`, presenti nel file dello schema. Servono anche queste informazioni per i form.
5. Il certificato V3 richiede almeno un segmento; nessun testimone significa rosso, non giallo.
   Un contributo umano senza citazione non può essere camuffato da certificato V3 valido.
6. L'esportazione può contenere `not_stated`, `Unknown` e campi obbligatori mancanti sulla
   macchina. Una validazione nuova non deve rendere impossibile correggere un grafo esistente
   per carenze pregresse estranee alla modifica.
7. `LiveRun.tsx` apre automaticamente `graphRoute(...)` con `replace: true` quando termina
   il live. Un pulsante aggiunto soltanto al riquadro finale non garantisce un ingresso visibile.
8. `main.tsx` usa `BrowserRouter`; il `useBlocker` della versione installata richiede un
   data router, come verificato nel codice locale di React Router. Per proteggere anche
   avanti/indietro del browser serve la migrazione circoscritta descritta in sezione 9.
9. Le risposte non applicate esistono, ma non c'è un comando di scarto nel flusso attuale.
   L'editor deve indirizzare ad «Applica le risposte», senza promettere un'azione inesistente.

## 3. Riutilizzo concreto di kg-graph-editor_V1

Il riferimento viene usato come base funzionale e come sorgente di algoritmi da adattare.
Non viene incorporato come pagina separata o iframe. Si portano le funzioni indipendenti dal
DOM in moduli TypeScript, sostituendo il vecchio accesso ai dati con selettori sul grafo nativo.
Le interazioni vengono ricomposte usando i componenti dell'applicazione.

| Funzionalità del riferimento | Codice di partenza | Integrazione prevista |
| --- | --- | --- |
| Indici nodi/archi, campi per tipo | `app.js`: `getDerived`, `buildNodeIndex`, `buildFieldsByType`, `buildEdgesByNode` | Selettori puri indicizzati per ID; campi dallo schema più campi effettivamente presenti |
| Tabelle per tipo, ricerca, ordinamento | `renderNodeTable`, `sortableTh`, `keepScroll` | Scheda Nodi, selettore del tipo, ricerca su tutte le colonne, intestazioni fisse e posizione conservata |
| Filtri per colonna | `fieldValueState`, `makeColumnFilter`, `makeRelCountFilter` | Assente / Vuoto / Compilato, valore esatto, collegamenti 0 / 1 / 2+; aggiungere Non dichiarato |
| Form per tipo di dato | `fieldKind`, `editCell` | Testi, multilinea, numeri, booleani e liste; schema prima delle euristiche |
| Aggiunta e rimozione nodi | `addNode`, `deleteNode` | Tipi ammessi dallo schema, ID immutabili, anteprima delle relazioni rimosse a cascata |
| Tabella relazioni e selettori | `renderRelationshipsTable`, `makeNodeSelectCell`, `showAddRelationshipDialog` | Estremi cercabili per nome, vincolati a dominio/range, apertura diretta del nodo |
| Navigazione fra viste | `navigateToTarget`, `drillToNodes`, `drillToRelationships`; `graph.js`: `focusNode`, sidebar | Stessa selezione fra tabella, controlli e grafo; filtri visibili e rimovibili |
| Controlli strutturali | `validate`, `findDuplicateRelationships`, `computeQualityMetrics`, `buildDiagnosticMetrics` | Errori e avvisi navigabili, completamento campi, prove disponibili, isolamento e percorsi incompleti |
| Preservazione dei dati | `captureStructure`, `serialize`, `orderedNode`, `orderedRel` | Applicazione di operazioni mirate al documento originale e verifiche di round-trip |
| Posizioni del grafo | cache `positions` in `graph.js` | Conservare camera e posizioni nel renderer attuale quando si cambia scheda |

Adattamenti necessari, anche dove si riusa la logica:

- `setNodeField` del riferimento cancella la chiave quando riceve stringa vuota o `null`.
  Qui «Svuota» e «Rimuovi campo facoltativo» devono essere azioni diverse.
- `fieldKind` tratta i booleani come testo; qui serve un controllo booleano. Le liste non
  vengono spezzate automaticamente sulle virgole, che possono far parte di un valore.
- La percentuale del riferimento restituisce 100 quando il denominatore è zero: qui mostrare
  «Non applicabile». `not_stated` e `Unknown` non devono gonfiare la completezza utile.
- Gli outlier degli estremi nel riferimento sono dedotti dalla maggioranza. Qui lo schema
  dichiara già dominio e range: sono la regola da validare.
- Le relazioni usano ID stabili, non indici di array: filtri, eliminazioni e ordinamenti non
  devono cambiare l'elemento a cui punta una selezione.
- Nessun riuso di `saveFile` e della sovrascrittura in-place; nessun trasferimento di font,
  palette, toolbar globale o renderer Cytoscape. Il grafo 3D attuale rimane integrato.
- «+ Colonna» diventa inizialmente «Mostra campi» e compilazione delle proprietà consentite.
  Nuovi tipi e nuove proprietà fuori schema richiedono una futura funzione di gestione
  dell'ontologia; i campi sconosciuti già presenti restano conservati e ispezionabili.

## 4. Percorso utente dentro l'applicazione

### 4.1 Ingresso dedicato e riconoscibile

Il comando è un **pulsante con icona matita e testo «Modifica grafo»**, visibile senza aprire
menu, selezionare un nodo o scorrere una tabella. Stesso nome e stessa destinazione ovunque.

| Punto di ingresso | Comportamento obbligatorio |
| --- | --- |
| Fine generazione live | Conservare il passaggio automatico da `LiveRun` al grafo finito; nella barra della destinazione è già visibile «Modifica grafo». Non entrare automaticamente in editing |
| Fine replay/riquadro finale | Mostrare anche «Modifica grafo» riferito alla versione riprodotta, quando editabile; non dipendere da questo riquadro per il caso live |
| Grafo riaperto dalla libreria | Pulsante persistente nella barra della versione visualizzata, accanto alle sue azioni |
| Pagina del manuale | Pulsante dedicato nella card della versione attuale e azione etichettata nella riga di ciascuna versione editabile; target sempre quella versione |

Il pulsante porta a `/manuali/:manualId/versioni/:versionId/modifica`, all'interno della
stessa cornice. Il titolo mostra «Modifica grafo» e la base scelta, per esempio «Da Versione
modificata 3». Entrando si legge: **«Le modifiche saranno salvate solo quando le accetti.
Se esci prima, vengono perse.»**

Disponibilità fornita dal backend, senza dedurla soltanto da `status` sul client:

- Grafo presente e in formato supportato, processo fermo: pulsante abilitato anche prima
  dell'approvazione della fonte, su versioni storiche e della campagna.
- Processo in corso: pulsante disabilitato con «Disponibile al termine dell'estrazione».
- Risposte date ma non applicate: pulsante disabilitato con «Applica prima le risposte»
  e collegamento alla pagina delle domande. Non lanciare l'applicazione automaticamente.
- Grafo assente o non leggibile/formato non supportato: pulsante disabilitato con motivo;
  nessuna apertura di un editor vuoto. Nessun recupero automatico di run falliti nel primo rilascio.
- PDF o `state/` mancanti non impediscono di modificare un grafo supportato; soltanto i
  comandi che dipendono dalle fonti mancanti sono disabilitati con spiegazione.

### 4.2 Percorso guidato in tre passi

```text
Grafo generato o riaperto
    → [Modifica grafo]
    → 1. Modifica ⇄ 2. Controlla ⇄ 3. Riepilogo
    → [Accetta modifiche e crea nuova versione]
    → Nuova versione salvata, aperta in consultazione

Uscita prima dell'accettazione → modifiche scartate → nessuna nuova versione
```

La barra dei passi mostra sempre **1. Modifica · 2. Controlla · 3. Riepilogo** e il passo
attivo. «Indietro» torna al passo precedente, non esegue undo. «Avanti» prosegue, non salva.
I passi già raggiunti sono cliccabili; un passo futuro si raggiunge tramite l'azione Avanti
e le relative verifiche. Esiste un solo pulsante principale per passo, nella barra delle azioni.

| Passo | Contenuto | Pulsanti e condizioni |
| --- | --- | --- |
| 1. Modifica | Schede Nodi, Relazioni, Grafo; apertura iniziale su Nodi. Tutti i form, filtri e prove; undo/redo disponibili | «Indietro» disabilitato; «Avanti: controlla» conclude l'input attivo e apre i controlli. Un valore non interpretabile resta nella cella con errore e focus |
| 2. Controlla | Controlli strutturali, anomalie, impatto su prove/verifiche e riferimenti alle righe | «Indietro» torna a Modifica; «Avanti: riepilogo» abilitato quando la validazione server del contenuto attuale è completa e senza errori bloccanti |
| 3. Riepilogo | Base, diff prima/dopo, aggiunte/rimozioni, effetti derivati, dubbi residui e nota facoltativa; riepilogo non editabile | «Indietro» torna a Controlla; «Torna a modificare» apre la riga scelta; unico pulsante finale «Accetta modifiche e crea nuova versione» |

«Esci senza salvare» è sempre visibile come azione secondaria nei tre passi, salvo durante
la richiesta finale o la verifica del suo esito. Lo stato indica «Nessuna modifica» oppure
«N modifiche non salvate». L'input ancora aperto viene concluso o segnalato prima di ogni
cambio passo/tab; il dialogo di uscita considera anche quel testo se non ancora valido.

Al passo 3, accanto al pulsante, testo: «Crea una nuova versione. Quella di partenza rimane
invariata.» Se richiesto dalla sezione 8, includere qui il riconoscimento esplicito dei dubbi
residui. Non aggiungere un secondo dialogo di conferma dopo questo riepilogo.

La pagina in consultazione può mantenere le viste Grafo, Nodi, Relazioni, Controlli; dentro
il percorso guidato i Controlli sono il passo 2, non una seconda procedura di salvataggio.
Le azioni di approvazione/ripresa del run non compaiono nel percorso editor.
All'ingresso del percorso il selettore di versione indica soltanto la base: sceglierne
un'altra costituisce uscita e riapertura, mai sostituzione della base dentro la stessa bozza.

### 4.3 Navigazione senza perdita di contesto

- Avanti/indietro fra passi, cambio tabella/tipo, filtri e apertura delle prove mantengono
  tutte le modifiche **nella stessa sessione in memoria**. Undo/redo è un comando separato.
- Il browser può andare avanti/indietro fra le voci interne di quella sessione senza
  scartare il lavoro. Quando la destinazione lascia la sessione, si applica la sezione 4.5.
- «Vedi nel grafo», estremi cliccabili, «Vedi in tabella» e anomalie aprono l'elemento
  preciso. Un salto da Controlla/Riepilogo apre il passo Modifica con elemento e campo
  selezionati; conserva il passo di provenienza per il rientro dopo la correzione.
- Se un filtro nasconde l'elemento richiesto, mostrare l'eccezione e i filtri attivi,
  senza lasciare una selezione invisibile. Conservare scroll, camera e selezione fra viste.
- Nell'URL vanno passo e stato di visualizzazione, per esempio
  `?passo=modifica&vista=nodi&tipo=CorrectiveAction`; mai operazioni o valori modificati.
  Una ricerca cambia l'URL con replace, un cambio passo con push.
- Un URL diretto a Controlla/Riepilogo senza sessione attiva viene normalizzato a Modifica:
  l'URL non contiene una bozza e non autorizza l'accettazione di modifiche inesistenti.
- Qualunque modifica dopo una validazione rende obsoleti esito, diff e riconoscimento dei
  dubbi. Prima dell'accettazione occorre validarli nuovamente sul contenuto attuale.

### 4.4 Accettazione: unico punto di persistenza

1. Il pulsante finale è abilitato solo con differenze effettive, nessun input aperto/non
   valido, esito server aggiornato senza blocchi e riconoscimenti richiesti completati.
2. Il clic invia **una sola richiesta** con modifiche, hash del riepilogo e accettazione.
   Il pulsante diventa «Creazione della nuova versione…»; modifiche e navigazione interna
   restano bloccate finché l'esito non è noto.
3. Il server rivalida e crea atomicamente snapshot e registrazione dell'accettazione.
   L'originale non cambia; il nuovo elemento è già accettato dalla persona, senza un
   successivo comando obbligatorio «Approva». Vedi la distinzione dalle verifiche in sezione 8.
4. Solo alla risposta positiva l'app elimina la sessione e apre con replace la nuova
   versione in consultazione. Mostra «Nuova versione creata. Le modifiche sono state salvate.»
   Aggiorna catalogo, libreria, manuale e attività; il dettaglio contiene «Deriva da …».
5. Nuove modifiche richiedono nuovamente «Modifica grafo» e una nuova accettazione finale.

Diff vuoto, incluso modifica → undo completo: «Nessuna modifica da salvare», pulsante finale
disabilitato. La navigazione resta possibile; non si crea una versione identica.

Errore certo di validazione/precondizione: il server non pubblica nulla e il lavoro resta
in memoria, con collegamento al problema. Errore di rete/timeout dopo l'invio: l'esito può
essere incerto; mostrare «Verifica il salvataggio» e risolvere la stessa richiesta idempotente
prima di consentire altre modifiche o una nuova richiesta. Non dichiarare fallita una scrittura
che potrebbe essere riuscita. I dettagli sono in sezione 9.

### 4.5 Uscita senza salvare: comportamento vincolante

La sessione non usa `localStorage`, `sessionStorage`, IndexedDB, file, bozze server, cache
persistenti o valori di bozza in `history.state`. Nessun recupero dopo chiusura, ricaricamento
o crash. Filtri e preferenze di visualizzazione possono essere conservati separatamente.

| Situazione prima dell'accettazione | Risultato |
| --- | --- |
| «Esci senza salvare» senza differenze né input pendente | Tornare direttamente alla versione di partenza, senza scrivere |
| «Esci senza salvare» con modifiche/input pendente | Dialogo: «Uscire senza salvare? Le modifiche saranno perse.»; pulsanti «Continua a modificare» e «Esci e scarta» |
| Breadcrumb, sidebar, cambio versione, link alle domande, indietro/avanti del browser verso l'esterno | Stesso dialogo; «Continua» annulla la navigazione, «Esci e scarta» svuota lo stato e raggiunge la destinazione richiesta |
| Ricarica, chiusura scheda/finestra o navigazione fuori dall'app | `beforeunload` quando ci sono modifiche; il testo è gestito dal browser. Se l'uscita avviene, i valori si perdono |
| Crash/chiusura forzata, per cui il browser non mostra conferme | Nessun recupero: si riapre il grafo salvato, mai le modifiche precedenti |
| Rientro nell'editor dopo un'uscita confermata, anche con Avanti del browser o ripristino dalla bfcache | Nuova sessione dalla base salvata, senza reintegro dei vecchi valori |

Non offrire «Salva e esci» nel dialogo di abbandono: chi vuole salvare resta nell'editor e
raggiunge il riepilogo. «Esci e scarta» è distruttivo solo per la sessione in memoria;
non cancella versioni, file sorgente o domande. Nessuna richiesta di creazione viene inviata.

Un errore API non è un'uscita: i dati rimangono finché l'utente resta nell'editor. Dopo un
clic finale di accettazione, invece, il server potrebbe già stare creando la nuova versione:
chiudere il browser non annulla quella richiesta. Mostrare lo stato in corso senza offrire
un falso «Scarta»; al rientro il catalogo mostra l'eventuale versione effettivamente creata.

### 4.6 Macchina a stati da implementare

`dirty` deriva dal diff effettivo; `pendingInput` segnala anche testo ancora non confermato
o non valido. La protezione di uscita usa `dirty || pendingInput`, oltre allo stato di invio.

| Stato | Evento | Destinazione/effetto |
| --- | --- | --- |
| `loading` | Base caricata | `editing`, passo Modifica; errore → messaggio e Riprova, senza sessione fittizia |
| `editing` | Avanti, input attivo valido | `checking`; richiedere validazione senza persistenza |
| `checking` | Validazione valida sul contenuto corrente + Avanti | `summary`; errori o risposta vecchia impediscono di procedere |
| `checking` / `summary` | Indietro/salto a riga | Passo richiesto nella stessa sessione; nessuna scrittura |
| Qualunque passo prima dell'invio | Mutazione/undo/redo | Aggiornare diff, invalidare riepilogo e riconoscimenti; nuove risposte remote accettate solo se riferite alla generazione corrente |
| `summary` | Accettazione valida | `saving`, congelare payload e `request_id` |
| `saving` | Successo | `saved`, eliminare sessione, navigare alla nuova versione |
| `saving` | Rifiuto certo senza commit | Tornare a Controlla con errore; nessuna perdita in memoria |
| `saving` | Rete/esito ambiguo | `save_unknown`, verificare lo stesso `request_id`; nessun invio con un nuovo ID |
| Passi prima dell'invio | Uscita richiesta con modifiche | `confirm_exit`; Continua ripristina il passo, Esci azzera sessione e naviga |
| Sessione terminata | Rientro tramite cronologia/URL | Ripartire dalla base, passo Modifica |

Il reducer non invia richieste. La POST finale parte soltanto dall'handler del pulsante,
mai da mount, effetti, passaggio di step, blur, scorciatoia o cleanup del componente.
Un ritorno a Riepilogo tramite cronologia o click sul passo passa dalle stesse guardie di
Avanti: se una modifica ha invalidato l'anteprima, tornare a Controlla e aggiornarla.

## 5. Tabelle e operazioni

### 5.1 Nodi

Una tabella per tipo, raggiungibile dal selettore compatto con conteggi: Macchina, Sintomi,
Codici di errore, Cause, Azioni, Componenti. Lo schema determina i tipi, comprese le tabelle
vuote in cui aggiungere il primo nodo.

| Tipo | Colonne principali iniziali |
| --- | --- |
| Tutti | Nome, collegamenti, pagine/fonti, stato della modifica; ID nei dettagli o fra le colonne opzionali |
| Macchina | Marca, modello, descrizione, tipo macchina |
| Sintomo | Descrizione, gravità |
| Codice di errore | Codice, descrizione |
| Causa | Descrizione, contesto, misure associate |
| Azione | Istruzioni, tipo di azione, fonte e riferimento |
| Componente | Descrizione, categoria |

Tutti i campi consentiti restano raggiungibili tramite «Mostra campi» e pannello dettagli;
la selezione iniziale limita soltanto la larghezza. Etichette comprensibili nell'interfaccia,
chiavi tecniche consultabili nei dettagli.

Comportamento:

- Modifica diretta delle celle brevi; pannello o dialogo per istruzioni multilinea e liste.
  `Enter` conferma una cella, `Esc` la annulla, `Tab` passa al controllo successivo;
  `Enter` in un testo multilinea inserisce un a-capo.
- Filtri cumulativi: ricerca generale, stato del valore per colonna, valore esatto quando
  utile, numero di collegamenti, modificati/non modificati, con/senza fonte.
- «Assente» significa chiave non presente; «Vuoto» significa valore presente ma vuoto;
  «Non dichiarato» identifica i segnaposto riconosciuti per quel campo. Conservare `0`,
  `false`, `[]`, `null` e stringhe multilinea senza conversioni implicite.
- Contatori dei collegamenti distinguono conoscenza diagnostica e collegamenti aggiunti
  dal sistema: un arco alla macchina non deve nascondere un isolamento diagnostico.
- ID e tipo di un nodo esistente non sono celle liberamente modificabili. Nuovi nodi
  ricevono ID stabili generati dal servizio, indipendenti dal nome.
- Il nome canonico e `properties.name` sono sincronizzati con una sola operazione.
  La proprietà ID prevista dallo schema, per esempio `action_id`, coincide con `node.id`.
  Descrizione e istruzioni restano campi distinti, anche se l'export iniziale li ha duplicati.
- La modifica della macchina riguarda il suo snapshot nel grafo. Non riscrive `info.yaml`,
  l'identità del manuale o le altre versioni; il dettaglio distingue dati del manuale e del grafo.
- Eliminazione: anteprima con numero e nomi delle relazioni coinvolte, poi rimozione atomica
  del nodo e dei suoi archi. Anche questa operazione può essere annullata nella bozza.
- La macchina radice unica non si può eliminare o duplicare nella prima versione dell'editor.

### 5.2 Relazioni

Colonne principali: **Da · Relazione · A · Verifica/revisione · Condizioni · Prove · Origine**.
Gli estremi mostrano nome e tipo, con ID disponibile per disambiguare nomi uguali.

- Modifica e aggiunta con select cercabili, compatibili con dominio e range dello schema.
  Cambiare tipo segnala e richiede di correggere eventuali estremi divenuti incompatibili.
- Filtri per tipo, estremi, stato, origine, pagina, presenza di prove e modifiche pendenti.
- Condizioni e prove sono modificabili nel pannello dell'**occorrenza**, mantenendo distinte
  le diverse occorrenze di una relazione. Le condizioni comuni dell'arco sono ricalcolate
  come intersezione, secondo la semantica già usata in `merger.GraphEdge.conditions`.
- Non introdurre un secondo arco con la stessa tripla tipo/da/a: offrire l'aggiunta di
  un'occorrenza all'arco esistente. Conflitti fra condizioni non vengono appiattiti.
- Cambiare tipo o estremi sostituisce la relazione con una nuova identità, collegata a
  quella precedente nella cronologia. Un semplice ritocco di proprietà mantiene l'ID.
- Le relazioni `derived` sono identificate come «Aggiunte dal sistema», in sola lettura.
  Il servizio le aggiorna deterministicamente in base ai nodi e alle relazioni finali.
- L'elenco `excluded_relations` resta una sezione storica consultabile. Reinserire un fatto
  escluso richiede un'esplicita nuova proposta umana, senza cancellare l'esclusione originaria.

### 5.3 Controlli utili alla persona

Riprendere la dashboard del riferimento con contatori cliccabili, evitando un punteggio unico
che mescoli completezza e correttezza:

- Integrità: ID duplicati, estremi mancanti, tipi incompatibili, valori di tipo errato.
- Completezza: campi obbligatori assenti/vuoti/non dichiarati; separare facoltativi e richiesti.
- Collegamenti: nodi isolati, cause senza azioni, sintomi/codici senza cause raggiungibili.
- Fonti: occorrenze con citazioni, contributi umani senza citazioni, verifiche invalidate.
- Duplicati: archi duplicati; nomi simili solo come suggerimento da ispezionare.

I controlli dei percorsi rispettano tipo, direzione e condizioni: una catena presente non
dimostra che due passaggi con condizioni incompatibili siano applicabili insieme.
Gli indicatori descrivono il contenuto del grafo, non dimostrano la sua correttezza tecnica.

Il backend distingue difetti già presenti nella base da quelli introdotti. ID duplicati,
archi orfani e dati impossibili restano bloccanti; carenze documentali pregresse sono avvisi.
Un nuovo nodo deve soddisfare i vincoli minimi, ammettendo soltanto i valori «non dichiarato»
previsti dalla policy dei campi, senza riempimenti inventati.

## 6. Prove, verifiche e decisioni umane

**Salvare un testo modificato non certifica automaticamente che sia nel manuale.**
Questa distinzione deve essere nei dati e leggibile nell'interfaccia, non solo nella guida.

Implementare un contratto specifico per i grafi revisionati, `kg-v3-graph-3`, mantenendo lettura
del formato attuale `kg-v3-graph-2` e lasciando l'export della pipeline invariato. Il cambio
di versione è necessario per dichiarare gli stati editoriali che il formato attuale non ha.

| Situazione | Trattamento |
| --- | --- |
| Elemento non modificato | Conservare prove, certificati e significato delle verifiche |
| Modifica a nome, codice, istruzioni o proprietà di dominio di un nodo | Segnalare e invalidare le verifiche delle affermazioni incidenti interessate; prima implementazione prudente: tutte le occorrenze degli archi diagnostici incidenti |
| Modifica di tipo/estremi di un arco | Nuova relazione umana; vecchie verifiche consultabili nella base e nel diff |
| Modifica di condizioni o associazione delle prove | Invalidare la verifica dell'occorrenza interessata e ricalcolare l'arco |
| Nuovo contenuto umano | Origine umana, stato «Da verificare», nessun testimone automatico inventato |
| Conferma esplicita della persona | Decisione umana separata, datata e legata all'hash del contenuto confermato |
| Salvataggio o approvazione complessiva del grafo | Nessuna promozione automatica delle singole relazioni |

Dettagli del contratto:

- Conservare `tier` per la verifica V3 ancora valida; ammettere `null` quando non esiste una
  verifica applicabile al nuovo contenuto. Aggiungere `review` con stato, autore, data,
  motivazione e hash del contenuto, e `provenance` per origine e derivazione.
- Un contributo senza segmenti non istanzia `contracts.Certificate`. Il certificato può
  essere assente; la decisione editoriale umana è un record distinto. Nessuna modifica ai
  vincoli della pipeline necessaria per far passare artificialmente il nuovo caso.
- `trusted` viene calcolato dal servizio: verifica V3 verde ancora valida oppure conferma
  umana esplicita sul contenuto attuale. Una relazione rifiutata non è utilizzabile. Una
  conferma senza citazioni è etichettata «Confermata da una persona, senza fonte collegata».
- La valutazione avviene per occorrenza. L'arco è utilizzabile se almeno un'occorrenza attiva
  è utilizzabile; la UI continua a mostrare eventuali altre occorrenze da verificare, e il
  consumer deve applicare le condizioni dell'occorrenza utilizzata. I derivati ereditano
  lo stato calcolato dai contenuti collegati e restano identificati come derivati.
- Il colore e il testo distinguono «Verificata», «Confermata da una persona», «Da verificare»
  e «Rifiutata». `graph/style.ts` deve leggere anche la revisione umana: `tier: null` non
  può essere trattato automaticamente come un arco provvisorio di estrazione.
- Le vecchie decisioni non si cancellano: sono recuperabili nello snapshot base e nel
  registro delle modifiche. Una nuova modifica rende obsolete le conferme sul vecchio hash.
- Citazioni, testo estratto, segment ID, pagina e bounding box sono dati della fonte in
  sola lettura. Si modifica l'associazione fra occorrenza e segmento tramite selezione;
  annotazioni personali sono campi separati. Nessuna textarea JSON per falsificare prove.
- Riutilizzare le citazioni incorporate anche se manca il PDF. Per associare altri segmenti
  servono un indice della fonte verificabile e un selettore per pagina/ricerca, nuovo rispetto
  all'attuale endpoint che recupera soltanto un segmento già noto.

Prima del rilascio verificare tutti i lettori del grafo e aggiornare tipi/API/rendering per
entrambi i formati. Non etichettare un file revisionato come `graph-2` se contiene semantica
che i vecchi consumer non comprendono; nessun aggiornamento silenzioso dei file storici.

## 7. Revisioni: modello e persistenza

### 7.1 Esecuzione, revisione e bozza

- **Esecuzione:** processo che estrae un grafo; ha tempi, chiamate, costo, stato e replay.
- **Revisione:** snapshot salvato del grafo, con un padre, modifiche e autore; non avvia
  estrazione e non ha un replay della pipeline.
- **Bozza:** lavoro non ancora pubblicato, solo nella memoria della sessione editor;
  annullabile finché si rimane nella sessione e perso all'uscita senza accettazione.

Le revisioni sono visibili nella cronologia del manuale insieme alle versioni estratte,
con etichette distinte e relazione «deriva da». Il comando attuale «Nuova versione», che
avvia una nuova estrazione, diventa «Nuova estrazione» dove necessario per evitare ambiguità.

Una revisione usa l'ID opaco stabile `revision~<uuid>` e un numero leggibile
assegnato per manuale sotto lock. Il suo padre può essere un run o un'altra revisione.
Modificare una versione storica crea una derivazione esplicita, non cambia gli altri figli.

### 7.2 Struttura da implementare

```text
workspace/<manual_id>/
  runs/…                           # struttura esistente
  revisions/<revision_uuid>/
    revision.json                  # identità, padre, hash, fonte, autore, data, nota
    base-graph.json                # base esatta usata per il salvataggio
    graph.json                     # nuovo snapshot completo, formato revisionato
    changes.json                   # operazioni e differenze prima/dopo
    validation.json                # controlli sullo snapshot salvato
    acceptance.json                # accettazione finale, persona, hash, dubbi riconosciuti
    source-review.json             # domande/decisioni ereditate come contesto
    source-report.json             # rapporto della fonte, se presente, dichiarato storico
```

`revision.json` contiene almeno: `schema_version`, `revision_id`, `revision_number`,
`manual_id`, `parent_version_id`, `parent_graph_hash`, `root_run_id`, `created_at`,
`created_by`, `note`, `graph_hash`, `ontology_hash`, `source_document_hash`,
`source_review_hash`, `editor_code_commit`, `request_id`, `request_payload_hash` e riepilogo
delle operazioni. `acceptance.json` registra `decision: accept_changes`, identità umana,
data del server, `graph_hash`, `preview_hash` e ID degli avvisi/dubbi riconosciuti. Viene
scritto nella stessa pubblicazione atomica di `graph.json`, non con una POST successiva.

La fonte deve essere risolvibile rispetto a quella revisione: hash del PDF, snapshot dello
schema e indice dei segmenti usato per le nuove associazioni. Gli snapshot condivisibili
possono stare in un archivio del workspace indicizzato per hash, senza duplicare ogni PDF.
Se una fonte storica non è ricostruibile con certezza, registrare il limite e conservare le
citazioni incorporate: non attribuirle al risultato di una nuova lettura del PDF.

`base-graph.json` è necessario perché oggi un run nel workspace può cambiare quando si
applicano risposte o si approva. Un semplice link al padre non garantisce un diff storico
riproducibile. Le revisioni già salvate, invece, non cambiano più.

Il riepilogo della revisione è calcolato dal suo grafo. Il rapporto originale, compreso
quello incorporato in `graph.report`, viene archiviato come rapporto della fonte: nel nuovo
formato non viene ripresentato come rapporto aggiornato. Non inventare `state/`, eventi,
tempi di estrazione o costi copiando quelli del padre. Nella UI: «Revisione manuale», costo
AI dell'operazione zero, durata di estrazione non applicabile; dati originali in «Estrazione
di origine». L'identità iniziale dell'operatore può restare `human:operator`, già usata
dall'app, senza introdurre un sistema utenti in questo lavoro.

### 7.3 Scrittura affidabile

Il server applica operazioni ammesse a una copia del documento completo della base. Non
accetta un nuovo JSON completo dal browser come autorità per certificati, contatori o autore.

Sequenza di commit della revisione:

1. Risolvere manuale e `request_id`. Sotto lock del manuale, cercare prima un commit già
   completato: stesso payload restituisce quel risultato anche se nel frattempo cambia la base.
2. Per una richiesta nuova, verificare capacità e precondizioni di base/schema/fonte/domande,
   e che il processo sorgente sia fermo.
3. Applicare le operazioni, aggiornare derivati e fiducia, validare il risultato completo;
   verificare corrispondenza con il riepilogo accettato e riconoscimenti richiesti.
4. Scrivere i file in una directory temporanea nascosta sullo stesso filesystem; completare
   le scritture prima della pubblicazione con rename atomico.
5. Pubblicare insieme snapshot e accettazione, rendere la nuova revisione visibile al
   catalogo e restituire ID/hash/riepilogo.

- Il catalogo ignora directory temporanee e revisioni incomplete. Un crash non deve far
  apparire una revisione parziale o rimuovere la versione sorgente.
- Doppio clic e retry dopo timeout con lo stesso `request_id` restituiscono la stessa
  revisione; stesso ID con contenuto diverso produce un conflitto.
- Se la base muta durante l'editing, risposta `409`: conservare la bozza in memoria e mostrare
  il confronto. «Riapri sulla nuova base» è un'uscita dalla sessione, con conferma di scarto
  se necessario. Nessuna fusione automatica o ripristino della vecchia bozza nel primo rilascio.
- Due bozze della stessa revisione immutabile possono creare due figli, con numeri diversi;
  mostrare che una revisione più recente esiste, senza riscrivere il padre scelto.
- Coordinare il lock anche con l'avvio di `apply`/`approve`/ripresa della base: controllare
  soltanto `process_alive` fuori dal lock lascerebbe una finestra di gara.
- Conservare i campi sconosciuti e l'ordine degli array non modificati. Nessuna pulizia
  globale, fusione di nodi o eliminazione degli isolati durante il salvataggio.

## 8. Integrazione con domande, approvazione e cronologia

Le correzioni manuali non devono passare da `Jobs.copy_version`, `Jobs.apply` o `Jobs.approve`.
La modifica di una revisione non riavvia il CLI e non richiede chiamate LLM.

**Domande dell'estrazione.** All'apertura della bozza si mostra se la fonte ha domande aperte.
Al salvataggio se ne conserva il contesto in `source-review.json`, con ID e link alla versione
originaria. Non si presentano come domande risolte dalla semplice modifica di un campo.
Si mantengono separati «Domande della fonte» e «Contenuti della revisione da verificare».
Rispondere sul run originale rimane possibile con il flusso esistente, ma il risultato non
riscrive una revisione salvata: va scelto esplicitamente come nuova base.

**Accettazione finale della nuova versione.** Il pulsante del riepilogo accetta le modifiche
e crea la versione in una sola operazione. Per le revisioni umane lo snapshot nasce con
`status: approved`, `decided_by: human` nel catalogo e decisione in `acceptance.json`.
La UI lo descrive come «Modifiche accettate». Non eredita l'approvazione del padre: registra
quella appena espressa sulla nuova versione. Non introdurre lo stato intermedio «Salvata,
ora da approvare» e non chiedere una seconda conferma dopo il riepilogo.

Le domande residue della fonte e i contenuti non verificati sono elencati al passo Riepilogo.
Se presenti, richiedere la casella non preselezionata «Accetto la nuova versione con i dubbi
residui elencati»; registrare gli ID riconosciuti. La nota è facoltativa. Una modifica del
contenuto o dei dubbi azzera la casella. Gli errori strutturali restano bloccanti.

Accettare lo snapshot non risponde alle domande del run e non conferma tutte le relazioni:
`trusted`, certificati e conferme sulle occorrenze seguono la sezione 6. Il comando «Approva»
già presente sui run rimane relativo all'estrazione e fuori dalla sessione editor. Il nuovo
flusso non chiama quell'endpoint. Snapshot e decisione sono scaricabili anche in un pacchetto
con la provenienza, senza riscrivere gli artefatti salvati.

**Navigazione e contatori.**

- `Version` diventa una unione discriminata con `kind: run | revision`,
  padre, riepilogo e capacità (`can_edit`, `can_approve`, `can_replay`, `can_resume`).
- La libreria apre per default l'elemento salvato più recente, con etichetta «Versione modificata N».
  Il manuale rende raggiungibile anche l'ultima revisione approvata e l'esecuzione di origine.
- Le revisioni compaiono nella tabella delle versioni; in «Esecuzioni» restano i processi,
  con eventuale collegamento alle revisioni generate a valle, senza duplicare costi e tempi.
- «Tocca a te» considera le attività aperte per versione, non solo `manual.latest`: creare
  una revisione non deve nascondere un run attivo o domande ancora pendenti sul padre.
- `flow/steps.ts` mostra per una revisione salvata «Modifiche accettate» e il collegamento
  alla fonte; `nextStep` apre il grafo. I passi Modifica/Controlla/Riepilogo appartengono
  soltanto alla sessione prima dell'accettazione, non sono attività pendenti dopo il salvataggio.
- Una revisione appena accettata non viene messa in «Tocca a te» per essere nuovamente
  approvata. Dubbi residui e domande della fonte rimangono consultabili nelle categorie
  appropriate senza duplicare la stessa domanda come un nuovo incarico della revisione.
- Gli endpoint di job rifiutano esplicitamente gli ID delle revisioni; quelli di lettura
  risolvono sia run sia revisioni attraverso un resolver comune.

## 9. Contratti e architettura da implementare

### Frontend

Un contenitore comune del grafo tiene caricamento, selezione e bozza, indipendentemente
dalla vista visibile. La bozza comprende base immutabile, operazioni, valori correnti,
validazione e pila undo/redo. Vive solo in React e viene distrutta all'uscita dalla sessione.
I selettori calcolano indici, collegamenti e filtri. Il polling di `StatusProvider` non
ricarica la base dentro una bozza attiva; un cambiamento esterno è un conflitto esplicito.

Creare un `EditorSessionProvider` montato una volta per manuale/base sotto la route editor;
non rimontarlo cambiando `passo`, `vista`, filtri o lingua. Il reducer gestisce gli stati della
sezione 4.6. Mantenere un contatore `draft_generation`: validazioni fuori ordine vengono
ignorate se non coincidono con la generazione corrente. Nessuna richiesta in background
pubblica dati modificati. Le richieste di anteprima non archiviano payload o bozze sul server.

**Router e guardia d'uscita.** Migrare `main.tsx` e la configurazione in `App.tsx` a
`createBrowserRouter` + `RouterProvider`, mantenendo tutte le route, lazy import e provider
esistenti. Estrarre un layout con `StatusProvider` e `Outlet`; tenere `LanguageProvider`
e `StrictMode` attorno al router. Usare `useBlocker` per le navigazioni SPA in uscita dalla
sessione, inclusi POP del browser, con `proceed/reset` per il dialogo. I cambi interni alla
stessa sessione non lo attivano. Non limitarsi a intercettare il clic sulla sidebar.

Usare anche `beforeunload` per le uscite dal documento, senza promettere testo personalizzato
o un blocco infallibile della chiusura. Su `pagehide` invalidare lo stato della sessione; su
`pageshow` con `persisted: true` ripartire dalla base per non recuperare modifiche dalla bfcache.
Il cleanup React non salva e non simula un'uscita utente durante i controlli di `StrictMode`.
Nei test dei percorsi usare `createMemoryRouter`, così il blocker usa lo stesso contratto.

Il renderer 3D riceve proiezioni del documento e mantiene separati i propri oggetti mutabili
di simulazione: coordinate e riferimenti Three.js non entrano mai nel grafo da salvare.
I nodi isolati rimangono nella vista editor; filtri e navigazione conservano la selezione.

| File/area | Lavoro previsto |
| --- | --- |
| `screens/FinishedGraph.tsx` e nuovo contenitore `screens/GraphWorkspace.tsx` | Estrarre lo spazio condiviso senza duplicare caricamento, barra e pannelli |
| Nuovi `editor/EditorSessionProvider.tsx`, `editor/EditorFlow.tsx`, `editor/useEditorExitGuard.tsx` | Sessione in memoria, tre passi, guardia SPA/unload/bfcache e azzeramento all'uscita |
| Nuovi `editor/model.ts`, `editor/reducer.ts`, `editor/selectors.ts` | Operazioni, bozza, undo/redo, indici adattati dal riferimento e diff |
| Nuovi `editor/EditableTable.tsx`, `editor/NodeTable.tsx`, `editor/RelationTable.tsx` | Tabelle, editor di celle, filtri e navigazione per ID |
| Nuovi `editor/ReviewPanel.tsx`, `editor/RevisionSummary.tsx` | Controlli, diff del passo finale e unica accettazione; nessun secondo dialogo di salvataggio |
| `components/Table.tsx`, `Controls.tsx`, `EvidencePanel.tsx`, `PageDialog.tsx` | Riutilizzo delle parti comuni; editor fonti e controlli accessibili |
| `graph/Graph3D.tsx`, `graph/style.ts` | Focus su ID, isolamento visibile, conservazione camera/posizioni, nuovi stati |
| `api/types.ts`, `api/client.ts`, `main.tsx`, `App.tsx` | Contratti, errori strutturati, data router e helper `editGraphRoute` |
| `screens/LiveRun.tsx`, `ManualScreen.tsx`, `Library.tsx`, `Inbox.tsx`, `Runs.tsx` | Ingressi, cronologia, azioni corrette per tipo, tempi/costi e attività pendenti |
| `flow/steps.ts`, `status/StatusProvider.tsx`, `text/it.ts` | Prossimo passo, aggiornamento globale, etichette revisioni |
| `i18n/en.ts`, `help/guide.ts`, `help/guide.en.ts`, `styles/`, `docs/DESIGN.md` | Traduzioni, guida e componenti coerenti con il sistema esistente |

### Backend

| File/area | Lavoro previsto |
| --- | --- |
| Nuovo `backend/ui/graph_document.py` | Lettura compatibile dei formati, snapshot completo, operazioni, ID e derivati |
| Nuovo `backend/ui/graph_validation.py` | Integrità, schema, completezza, controlli e differenze rispetto alla base |
| Nuovo `backend/ui/revisions.py` | Metadati, salvataggio atomico, lock, idempotenza, diff e decisioni umane |
| `backend/ui/catalog.py` | Resolver di run/revisioni, riepiloghi, cache e cronologia ordinata |
| `backend/ui/api.py` | Endpoint nuovi, capacità, errori di validazione e guardie sui job |
| `backend/ui/evidence.py` | Risoluzione della fonte per revisione e selettore segmenti con fonte verificata |
| `backend/ui/jobs.py` | Coordinamento delle mutazioni dei run con i lock; nessuna esecuzione per salvare revisioni |
| `backend/kg_v3/ontology.py` / endpoint ontologia | Esporre descrittori completi dei campi senza cambiare schema o comportamento estrattivo |

Rimane la persistenza su filesystem. Non occorrono database, collaborazione simultanea,
un nuovo servizio web o una seconda libreria di rendering per realizzare il primo rilascio.

### Contratto API del primo rilascio

Implementare i seguenti percorsi; non sono ancora disponibili. Le operazioni di lettura e
anteprima non creano revisioni. La POST di creazione è l'unica scrittura del percorso editor.

| Metodo e percorso, sotto `/api/manuals/{m}` | Responsabilità |
| --- | --- |
| `GET /versions/{v}/editor` | Documento originale, precondizioni, schema, capacità, fonte e contesto di review |
| `POST /versions/{v}/validate-edits` | Anteprima senza scritture: esito, diff, avvisi e hash del riepilogo |
| `POST /versions/{v}/revisions` | Unica accettazione e creazione atomica del figlio; `201` al primo commit, `200` al retry già completato |
| `GET /revision-requests/{request_id}` | Risolvere un esito incerto: `saved` con versione creata, `in_progress` oppure `not_found`; nessun contenuto di bozza |
| `GET /versions/{revision}/changes` | Diff rispetto allo snapshot base, con link agli elementi |
| `GET /versions/{v}/source-segments?page=…&q=…` | Cercare nella fonte verificata, con paginazione e riferimenti risolvibili |
| `GET /versions/{v}/graph` e letture esistenti | Risoluzione uniforme; rapporto della revisione distinto dal rapporto della fonte |

DTO da dichiarare in Pydantic e TypeScript, con i medesimi nomi di campo:

```typescript
type Preconditions = {
  base_hash: string;
  ontology_hash: string;
  source_token: string;       // Identità della fonte e sua disponibilità, anche senza PDF.
  source_review_hash: string;
};
type EditInput = {
  preconditions: Preconditions;
  operations: EditOperation[];
  draft_generation: number;
};
type Issue = {
  id: string;
  code: string;
  severity: "error" | "warning";
  target: { kind: "graph" | "node" | "edge" | "occurrence"; id?: string; field?: string };
  introduced: boolean;
  message_key: string;
  message_params: Record<string, string | number>;
};
type EditPreview = {
  draft_generation: number;
  preview_hash: string;
  has_changes: boolean;
  can_accept: boolean;       // Integrità e capacità; il client verifica anche i riconoscimenti.
  diff: GraphDiff;
  issues: Issue[];
  required_acknowledgements: string[];
};
type AcceptRevision = EditInput & {
  request_id: string;
  preview_hash: string;
  note: string;
  acceptance: { decision: "accept_changes"; acknowledged_issue_ids: string[] };
};
type RevisionCreated = {
  version: RevisionVersion;  // kind: "revision", status: "approved", decided_by: "human".
  parent_version_id: string;
  graph_hash: string;
  request_id: string;
  id_map: Record<string, string>;
};
```

Il GET editor restituisce `{graph, preconditions, ontology, capabilities, source, source_review}`.
Le capacità sono `can_edit`, `can_approve`, `can_replay`, `can_resume` con motivi traducibili
per quelle disabilitate. Sulle revisioni salvate: edit vero, approve/replay/resume falsi.
`RevisionVersion` estende i dati del catalogo con padre, numero e accettazione; `GraphDiff`
separa added/removed/updated per nodi e archi, prima/dopo per campo, modifiche di occorrenze
e conseguenze calcolate dal sistema. Nessuna modifica invisibile fuori dal riepilogo.

`EditOperation` è una unione discriminata con allowlist, non JSON Patch libero:

| Operazione | Payload e regola |
| --- | --- |
| `node.add` | `temp_id`, `node_type`, `name`, `properties`; ID riservato `tmp_node_<uuid>` |
| `node.set_name` | `node_id`, `value`; sincronizza anche `properties.name` |
| `node.set_property` / `node.remove_property` | `node_id`, `field`, eventuale `value`; vietati ID, nome e metadati riservati; rimozione solo facoltativi |
| `node.set_aliases` | `node_id`, `values: string[]`; origine umana, invalidazione prudente come per il nodo |
| `node.delete` | `node_id`; rimuove gli archi incidenti come un'unica operazione annullabile |
| `edge.add` | `temp_id`, `relation_type`, `from`, `to`, `occurrences`; schema e unicità della tripla |
| `edge.replace_endpoints` | `edge_id`, `replacement_temp_id`, `relation_type`, `from`, `to`; include cambio tipo; successive operazioni puntano alla nuova identità temporanea |
| `edge.delete` | `edge_id`; rifiutata se relazione derivata |
| `occurrence.add` / `occurrence.update` / `occurrence.delete` | `edge_id`, `occurrence_id`, dati ammessi: condizioni, riferimenti ai segmenti, annotazione umana; vietata la riscrittura delle citazioni |
| `occurrence.confirm` / `occurrence.reject` | `edge_id`, `occurrence_id`, hash del contenuto, motivazione; decisione in memoria fino all'accettazione finale |

Le occorrenze hanno ID stabili nello schema revisionato: per quelle importate derivarli da
ID arco, indice originale e hash del contenuto; per quelle nuove usare ID temporanei.
Anche i payload delle condizioni usano i campi esistenti `kind`, `text`, `cite`, `scope`,
con enum e vincoli di `ContextItem`. Tutti gli altri dati sono preservati o calcolati dal server.
La rimozione dell'ultima occorrenza rimuove anche la relazione, con la stessa anteprima e
possibilità di undo della cancellazione dell'arco. Non salvare archi diagnostici senza occorrenze.

Il server calcola `preview_hash` sul risultato normalizzato e sul diff/contesto di review,
prima di assegnare ID definitivi e date di creazione. Usa serializzazione canonica JSON
(chiavi ordinate, separatori compatti, UTF-8, nessun NaN; ordine degli array conservato).
Il client riusa l'hash ricevuto, non reimplementa la canonicalizzazione. Nella POST finale
si ripete lo stesso calcolo, si confronta l'hash, poi si assegnano gli ID definitivi e si
registra `id_map`: il riepilogo deve corrispondere al grafo salvato a meno di ID e metadati.

Validare nuovamente tutto nel salvataggio: la validazione di anteprima non è un'autorizzazione
riutilizzabile su dati cambiati. `422` restituisce codice del problema, elemento, campo e
messaggio traducibile; `409` indica una precondizione superata, un hash di riepilogo obsoleto
o riuso non valido della chiave. Esito senza differenze: `422` con `NO_CHANGES`.
Estendere `ApiError`: oggi conserva solo una stringa di dettaglio.

Un errore dopo l'invio può avere esito incerto anche se presentato come errore di I/O.
Conservare payload e `request_id` congelati **solo in memoria** e interrogare lo stato della
richiesta. `saved` apre la versione già creata; `in_progress` attende con indicatore;
`not_found` consente «Riprova» con lo stesso identico payload/ID, senza dedurre che una
prima richiesta ancora in arrivo sia stata annullata. Il server deduplica sotto lock e
ricostruisce gli esiti riusciti dai manifest salvati anche dopo il riavvio.

## 10. Coerenza visiva e semplicità

Seguire [DESIGN.md](DESIGN.md) e `frontend/src/styles/tokens.css`:

- Cornice industriale, rail da 56 px, barra percorso da 48 px, palette grafite calda.
- Onest per il testo, JetBrains Mono per ID, conteggi e dati; controlli da 32 px, righe
  compatte da 36 px, bordi da 1 px, raggi da 4 px, griglia da 4 px.
- Tabelle e pannelli chiari; fondo scuro per il grafo. I colori dei tipi restano quelli attuali.
- Nessuna voce «Editor» nella sidebar: si lavora sul grafo già selezionato.
- Pulsanti con testo, non sole icone, per Modifica grafo, Indietro, Avanti, accettazione e
  uscita. In Controlla/Riepilogo togliere dalla barra le ricerche inutili per lasciare spazio
  alle azioni; a 1024 px l'etichetta finale deve essere leggibile integralmente. Nessun menu
  nascosto per accettare o abbandonare, né salvataggio associato a una scorciatoia implicita.
- Testi lunghi espandibili nel pannello o nella cella attiva; non comprimere l'intera tabella
  per mostrare ogni campo. Intestazioni e colonna identificativa fisse, scorrimento orizzontale.
- A 1024 px il pannello dettagli può diventare sovrapposto/richiudibile; conservare spazio
  per leggere la tabella. Verifica visiva a 1440×900 e 1024×768.
- IT/EN anche per controlli, errori e nuove sezioni della guida; contenuti del manuale invariati.
- Focus visibile, etichette dei controlli e navigazione da tastiera. Preferire una tabella
  semantica con controlli nelle celle; usare un ruolo `grid` soltanto implementandone davvero
  la navigazione. Il clic su un input non apre accidentalmente il dettaglio della riga.

## 11. Sequenza di realizzazione

Ogni fase deve terminare con un risultato verificabile. Le fasi 1–5 costituiscono il primo
rilascio completo; le tabelle editabili, i filtri e le revisioni non sono demandati a estensioni.

| Fase | Consegna | Criterio di uscita |
| --- | --- | --- |
| 1. Contratti e persistenza | Modello run/revisione, formato revisionato, policy prove/fiducia, operazioni, validazione e scrittura atomica | Un test offline crea due revisioni consecutive preservando tutte le basi; nessun job/LLM |
| 2. Tabelle integrate | Nodi e Relazioni in consultazione nello spazio del grafo; port dei selettori e filtri del riferimento; collegamenti ai dettagli | Si trova un nodo da ogni tipo, si filtrano campi e collegamenti, si passa a grafo e prove senza perdere il contesto |
| 3. Editing completo | Celle tipizzate, CRUD nodi/relazioni/occorrenze, selezione fonti, invalidazione verifiche, undo/redo nella sessione | Le correzioni si vedono in tutte le viste; cancellazioni annullabili finché la sessione resta aperta |
| 4. Percorso e accettazione | Data router, pulsante dedicato, tre passi, diff, scarto in uscita, accettazione atomica e cronologia | Generazione → Modifica → avanti/indietro → accetta → nuova versione; uscita senza accettazione → nessuna scrittura e perdita dei valori |
| 5. Controlli e rifinitura | Dashboard navigabile, contatori coerenti, gestione anomalie/conflitti, IT/EN, guida e QA visiva | Tutti i criteri della sezione 12 verificati e nessuna regressione dei flussi esistenti |
| Successiva, opzionale | Suggerimenti AI, eventuale vista 2D locale, merge/split di nodi, operazioni massive | Scope deciso su casi d'uso reali; indipendente dal completamento del primo rilascio |

Non occorre migrare in scrittura i grafi già presenti. Si aggiungono lettori compatibili,
si lavora su copie e si introduce il nuovo formato soltanto per le revisioni salvate.

## 12. Verifiche e criteri di accettazione

Test offline con fixture piccole e mirate, inclusi casi derivati dalla logica del riferimento
e adattati al formato nativo. Nessuna nuova estrazione reale necessaria.

1. Dopo il redirect di fine generazione e riaprendo un grafo storico è visibile il pulsante
   «Modifica grafo»; entrambi aprono lo stesso percorso, senza file intermedi o menu nascosti.
2. Ogni tipo ha la sua tabella, anche vuota; ricerca, filtro per colonna, ordinamento,
   conteggio collegamenti e stato dei valori funzionano insieme.
3. Una modifica testuale, un numero, `false`, una lista vuota, `null`, un campo assente e
   istruzioni multilinea mantengono tipo e significato dopo salvataggio e riapertura.
4. I campi sconosciuti e le occorrenze non toccate sono preservati. Nome e ID duplicati
   nelle proprietà non divergono dalle chiavi canoniche.
5. Un nodo aggiunto senza archi è visibile e segnalato; eliminarlo o eliminare un nodo
   con archi produce il diff corretto. Undo ripristina anche relazioni, prove e selezione.
6. Estremi incompatibili, ID duplicati e archi orfani vengono rifiutati dal server anche
   quando una richiesta aggira l'interfaccia. Stessa tripla non produce archi duplicati.
7. Modificare un nodo/occorrenza invalida le verifiche interessate; salvare o approvare
   non le ripristina. Una conferma umana resta distinguibile da una verifica automatica.
8. Fonti mancanti non bloccano la lettura del grafo; fonti cambiate non vengono associate
   silenziosamente alle citazioni storiche. Il pannello non consente di alterare il testo fonte.
9. Ogni salvataggio effettivo produce un nuovo ID e un padre corretto. Due salvataggi
   successivi lasciano consultabili originale, revisione 1 e revisione 2; nessun no-op crea revisioni.
10. Parent/base e sorgenti restano byte-identici; se il run cambia in seguito, il diff della
    revisione si ricostruisce ancora dalla base congelata. Hash di schema e fonte conservati.
11. Retry idempotente, due schede, conflitto della base, processo che riparte e crash del
    server non causano sovrascritture o revisioni parziali. Finché il documento browser
    rimane aperto, gli errori mantengono la sessione; chiusura/ricarica la scartano.
12. Il catalogo e i suoi dati in cache riflettono il nuovo contenuto. Il rapporto originale
    non appare come rapporto della revisione; tempi/costi non vengono duplicati in Esecuzioni.
13. L'accettazione finale crea insieme versione e decisione senza usare la pipeline o
    richiedere un secondo Approva; le domande della fonte restano riconoscibili e le
    attività aperte su altri elementi non scompaiono da «Tocca a te».
14. Passaggi controlli → riga → relazione → nodo → grafo → pagina PDF conservano contesto;
    Avanti/Indietro interni conservano la sessione, l'uscita confermata la distrugge.
15. UI verificata nelle due dimensioni previste, in IT e EN, con tastiera, testi lunghi,
    filtri senza risultati, caricamenti, errori API e manuale non disponibile.

### Scenari obbligatori del percorso, da automatizzare

| ID | Azioni | Esito da asserire |
| --- | --- | --- |
| FLOW-01 | Concludere un live tramite eventi finti e seguire il redirect | Il grafo destinazione mostra Modifica grafo, che apre il passo 1 della stessa versione |
| FLOW-02 | Aprire dalla libreria un grafo già esistente, scegliere una versione storica e modificare | Base e breadcrumb coincidono con la scelta; nessun cambio silenzioso all'ultima versione |
| FLOW-03 | Cambiare due celle, Avanti → Controlla → Riepilogo, poi Indietro e ritorno a Modifica | I valori e l'undo restano; conteggio versioni invariato e zero POST di creazione |
| FLOW-04 | Dal riepilogo correggere una riga, poi tornare avanti anche con il browser | Vecchia validazione e vecchi riconoscimenti scadono; accettazione solo sul nuovo hash |
| FLOW-05 | Clic finale, doppio clic e retry dopo una risposta persa | Una sola versione con snapshot, acceptance e padre corretto; apertura della destinazione, nessun secondo Approva |
| FLOW-06 | Modificare, Esci senza salvare, Continua a modificare | Dialogo chiuso, valori invariati, nessuna POST di creazione |
| FLOW-07 | Modificare, uscire e confermare lo scarto, poi rientrare anche con Avanti del browser | Valori originali, nessuna nuova versione, nessun payload recuperato da storage o history |
| FLOW-08 | Ripetere lo scarto passando da logo, breadcrumb, sidebar, altra versione e POP esterno | Ogni percorso applica la stessa guardia, raggiunge la destinazione scelta e azzera lo stato |
| FLOW-09 | Modificare e ricaricare/chiudere prima dell'accettazione; simulare `pagehide/pageshow` della bfcache | Nessuna revisione e nessun recupero; verifica del dialogo nativo nel browser dove supportato |
| FLOW-10 | Input numerico non valido ancora aperto; Avanti oppure uscita | Avanti evidenzia la cella; uscita avverte della perdita anche se il diff confermato è vuoto |
| FLOW-11 | Cambiare e fare undo completo; raggiungere Riepilogo | Pulsante finale disabilitato; zero versioni identiche create |
| FLOW-12 | Risposte di validazione invertite, `409`, `422`, offline o timeout dopo commit | Nessun risultato vecchio abilita l'accettazione; bozze in memoria conservate, esito incerto risolto sullo stesso ID |
| FLOW-13 | Ricaricare direttamente l'URL del riepilogo, con `StrictMode` e polling attivi | Ripartenza al passo 1 dalla base; nessuna POST, nessun vecchio valore e nessun reset causato dai normali re-render |
| FLOW-14 | Accettare una versione con modifiche prive di verifica automatica | Versione accettata; stato delle singole relazioni rimane quello della policy, senza diventare verde per effetto del salvataggio |

Per FLOW-03/06/07/08/11 controllare sia le richieste client sia il filesystem del workspace:
prima del clic finale non devono apparire directory di revisione, neppure temporanee,
o file contenenti modifiche della sessione. La validazione è un'anteprima senza persistenza.
La chiusura durante FLOW-05 avviene dopo un'accettazione: verificare il possibile commit
completato, senza aspettarsi che l'abbandono del browser annulli una richiesta già inviata.

Copertura prevista: nuovi test backend per documento, validazione e revisioni; estensione di
`tests/test_ui_catalog.py`, `test_ui_api.py`, `test_ui_jobs.py`, `test_ui_answers.py` e
`test_ui_replay.py` per la compatibilità. Frontend: reducer dell'editor, filtri e tipi di dato,
interazioni delle tabelle, salvataggio/conflitti, lifecycle e integrazione della navigazione.
Eseguire i test mirati durante ogni fase, poi lint/backend suite, `npm test` e `npm run build`
prima del rilascio; verificare nel browser i percorsi e le dimensioni indicati.

Per la reattività usare anche una fixture sintetica più grande, dichiarata tale: l'editing
di una cella non deve ricostruire inutilmente tutta la scena 3D. Introdurre paginazione o
virtualizzazione solo se la verifica ne mostra la necessità, mantenendo selezione e filtri.

## 13. Estensione AI, dopo l'editor umano

Il punto di estensione è il contratto delle operazioni, non un secondo sistema di salvataggio.
Una futura AI può proporre correzioni di testo, relazioni mancanti o possibili duplicati,
accompagnandoli con motivazione e citazioni verificabili.

Le proposte si vedono come differenze nella bozza e la persona le accetta o rifiuta; poi usa
gli stessi passi e «Accetta modifiche e crea nuova versione». Provenienza della proposta e decisione umana
rimangono distinte. Nessun suggerimento cambia automaticamente un certificato, un grafo
approvato o la versione corrente. Eventuali chiamate passano dal gateway e dai controlli
di spesa già presenti. Nessun modello o comportamento AI è necessario per il primo rilascio.

## 14. Confini di questo documento

Questo piano deriva dall'ispezione statica di codice, schema e documentazione delle due
codebase. Non attesta che l'editor sia già implementato, eseguito o validato nel browser.
La realizzazione richiede in particolare il contratto delle revisioni, l'adattamento delle
funzioni del riferimento e la verifica dei flussi completi descritti sopra.

I risultati e gli artefatti delle estrazioni esistenti restano fonti di provenienza; una
revisione manuale è un nuovo prodotto tracciato e non sostituisce retroattivamente la fonte.

## 15. Consegna operativa per l'agente AI implementatore

### 15.1 Mandato e decisioni già prese

Quando viene richiesta l'implementazione, realizzare le fasi 1–5 fino ai criteri della
sezione 12. Questo documento è una specifica di lavoro, non una richiesta di produrre
un altro piano. Non cambiare il percorso o reintrodurre persistenza delle bozze per comodità.

Decisioni vincolanti:

1. Un comando «Modifica grafo», stessa esperienza subito dopo generazione e in seguito.
2. Tre passi con avanti/indietro; tabelle e filtri del riferimento adattati, dentro l'app.
3. Stato solo in memoria; uscita confermata o effettiva prima dell'accettazione = perdita.
4. Un solo atto finale accetta il contenuto e crea una nuova versione; niente autosave,
   salvataggio su Avanti o approvazione obbligatoria successiva.
5. Persistenza append-only nel workspace, base invariata, idempotenza e diff verificabile.
6. Verifiche delle relazioni distinte dall'accettazione complessiva; nessun certificato inventato.
7. React/TypeScript, FastAPI, design esistente, compatibilità dei run; niente iframe o editor separato.
8. AI suggeritrice, editing dell'ontologia, merge/split e operazioni massive fuori dal primo rilascio.

Rileggere `AGENTS.md`, questo file, `docs/DESIGN.md` e le implementazioni citate prima di
modificare. Se il codice nel frattempo è cambiato, adattare i punti d'integrazione conservando
le decisioni sopra. I documenti dell'editor allegato restano riferimento funzionale: non
eseguirne i vecchi vincoli architetturali. Non modificare quella cartella per l'integrazione.

### 15.2 Ordine degli incarichi e verifica di uscita

Gli incarichi sono sequenziali per dipendenze; non richiedono più agenti. I nomi dei moduli
nuovi possono essere accorpati se il comportamento e le responsabilità restano chiari.

Due dettagli di integrazione da non tralasciare: `Icon.tsx` deve offrire l'icona matita nel
set esistente; la colonna azioni di `Table.tsx` è oggi larga 32 px. Per il pulsante testuale
nella cronologia rendere quella larghezza configurabile, preservando il default delle
altre tabelle e la mancata propagazione del clic alla navigazione della riga.

| Incarico | Input / file principali | Risultato da consegnare prima di proseguire |
| --- | --- | --- |
| A. Documento e operazioni | `export.py`, `contracts.py`, `ontology.py`, formato del riferimento; nuovi `graph_document.py`, `graph_validation.py` | Lettura graph-2/graph-3, descrittori di schema, operazioni tipizzate, ID e round-trip; test di integrità e invalidazione |
| B. Accettazione atomica | A; nuovi `revisions.py`, estensioni `api.py`, `catalog.py`, coordinamento `jobs.py` | Preview senza scritture, commit snapshot+acceptance, idempotenza, esito richiesta, resolver e guardie; test di crash/retry/concorrenza |
| C. Router e sessione | Contratti B; `main.tsx`, `App.tsx`, `api/*`, nuovi provider/reducer/guardia | Route editor con sessione in memoria e passi, guardia POP/unload/bfcache; test FLOW-06/07/08/09/10/13 |
| D. Tabelle e navigazione | C; port delle funzioni elencate in sezione 3, componenti UI e renderer esistenti | CRUD completo, filtri combinabili, celle tipizzate, fonti/occorrenze, undo/redo e salti alle righe senza perdita di contesto |
| E. Riepilogo e accettazione | B+C+D; `ReviewPanel`, `RevisionSummary`, `api/client.ts` | Validazione per generazione, diff aggiornato, pulsante finale unico, gestione esiti certi/incerti; FLOW-03/04/05/11/12/14 |
| F. Ingressi e ciclo di vita | E; `LiveRun`, `FinishedGraph`, `ManualScreen`, `Library`, `Inbox`, `Runs`, `flow/steps`, `StatusProvider` | Pulsante dedicato in tutti gli ingressi; redirect live corretto, versioni/attività/costi coerenti, nessuna seconda approvazione; FLOW-01/02 |
| G. Chiusura | A–F; traduzioni, guida, `DESIGN.md`, test | Intero percorso verificato in IT/EN, QA alle due risoluzioni, suite/build verdi e resoconto delle prove |

In A/B usare directory temporanee dei test e fixture artificiali; non risalvare gli
artefatti originali. I mock LLM devono fallire se invocati da anteprima o accettazione:
queste operazioni non richiedono modelli. Riutilizzare `tests/ui_support.py` e i fixture
esistenti per verificare la compatibilità delle vecchie API.

File di test nuovi previsti:

- `tests/test_ui_graph_document.py`: operazioni, tipi di dato, conservazione campi,
  occorrenze, invalidazioni e derivati.
- `tests/test_ui_revisions.py`: accettazione, idempotenza, precondizioni, snapshot,
  scrittura atomica, catalogo ed esiti dopo risposta persa/riavvio.
- `frontend/tests/editor-reducer.test.ts`: stato, diff, undo/redo, generazioni di validazione.
- `frontend/tests/editor-flow.test.tsx`: passi, guardie, riepilogo, unica POST e scarto.
- `frontend/tests/editor-tables.test.tsx`: filtri, editor di celle e selezione fra viste.
- Estendere i test API/catalogo/job/flow/shell/i18n già presenti; usare il data router nei
  test che attraversano il blocker, senza sostituirlo con un mock che nasconda i POP reali.

### 15.3 Verifica finale e definizione di completamento

Eseguire i test pertinenti a ogni incarico. Alla chiusura usare i comandi già previsti
dalla repository, dalla radice:

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest
npm --prefix frontend test
npm --prefix frontend run build
git diff --check
```

Avviare l'interfaccia locale con `scripts/ui.py` o i server di sviluppo già disponibili,
senza lanciare estrazioni reali a pagamento; usare un run finto/replay e un workspace di
prova per il percorso completo. Nel browser verificare i pulsanti reali, avanti/indietro,
scarto, riapertura e accettazione, oltre alla leggibilità a 1440×900 e 1024×768. Test jsdom
da soli non dimostrano il comportamento di chiusura, dialogo nativo o bfcache.

Il lavoro è completato quando tutti gli ingressi e FLOW-01–14 sono coperti, i criteri
generali della sezione 12 sono rispettati e l'utente può accettare oppure abbandonare
il lavoro senza dubbi su cosa è stato salvato. Riportare nel risultato finale file/commit,
verifiche effettivamente eseguite ed eventuali limiti osservati; non dichiarare verifiche
browser o test non effettuati. Una UI finta con soli dati locali non completa l'incarico.
