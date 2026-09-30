# Piano di integrazione dell'editor del grafo

Data: 30 settembre 2026. Stato: **proposta di implementazione; funzionalità non ancora implementata**.

Analisi della codebase corrente, commit `043f56b`, e della cartella locale
`/Users/fabio.daniele/Coding/kg-graph-editor_V1/` (`app.js`, `graph.js`, formato e documentazione).
La cartella di riferimento non contiene un repository Git consultabile: i riferimenti sotto
identificano file e funzioni, non una release del tool.

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
- Ogni salvataggio di modifiche effettive crea una revisione distinta; l'originale resta disponibile.
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

### 4.1 Due ingressi, un solo editor

**Subito dopo la creazione.** Il riquadro di fine estrazione conserva il prossimo passo già
previsto e aggiunge «Rivedi e modifica» quando è disponibile un grafo concluso. Lo stesso
comando è nella barra del grafo finito, anche se il grafo aspetta ancora l'approvazione.

**In seguito.** Libreria → manuale → versione/revisione → «Modifica grafo».
Si può partire anche da una versione storica o della campagna; il salvataggio finisce sempre
nel workspace e mostra esplicitamente da quale elemento si è partiti.

Disponibilità determinata dal backend attraverso capacità esplicite:

- Grafo presente, leggibile e processo sorgente fermo: ispezione ed editing disponibili.
- Esecuzione attiva: consultazione del flusso esistente; editing disabilitato fino alla fine.
- Risposte già date ma non applicate: prima applicarle o scartarle con il flusso esistente;
  evitare una revisione che ignori risposte in attesa senza dirlo.
- Esecuzione fallita senza un grafo utilizzabile: nessun editor. Un eventuale snapshot
  recuperabile deve superare i controlli strutturali prima di essere offerto come base.
- Mancanza di `state/` o del PDF: il JSON rimane ispezionabile e modificabile; i comandi che
  richiedono fonti non disponibili mostrano il motivo della loro indisponibilità.

### 4.2 Viste e azioni

La pagina del grafo comprende quattro viste: **Grafo · Nodi · Relazioni · Controlli**.
Sono disponibili anche in consultazione; «Modifica grafo» abilita i form e crea una bozza
locale, senza scrivere una revisione sul server.

Struttura indicativa, composta con la cornice attuale:

```text
Grafi › Manuale › Revisione 3          Modifiche non salvate   Salva nuova revisione
Grafo | Nodi | Relazioni | Controlli   Annulla modifica · Ripeti · Scarta modifiche

[Tipo: Azioni (24)] [Cerca in tutte le colonne…] [Mostra campi] [+ Aggiungi nodo]
[Filtri attivi e rimovibili]                                      8 di 24 righe

Nome             Istruzioni          Fonte          Collegamenti    Dettagli
…                …                   …              3               →

Pannello contestuale: proprietà, relazioni entranti/uscenti, prove e pagina PDF
Barra di stato: nodi · relazioni · modifiche · errori · avvisi
```

- In consultazione il pulsante principale resta quello del prossimo passo, per esempio
  «Approva»; durante l'editing diventa «Salva nuova revisione».
- Passare fra le quattro viste conserva bozza, selezione, filtri e posizione di scorrimento.
- «Vedi nel grafo», clic sugli estremi, «Vedi in tabella» e conteggi dei controlli aprono
  direttamente l'elemento richiesto. Se un filtro lo nasconde, mostrare l'eccezione e il
  filtro applicato, senza lasciare una selezione invisibile.
- Ricerca, tipo, ordinamento e filtri serializzabili stanno nell'URL; focus e scroll nello
  stato della pagina. Esempio: `?vista=nodi&tipo=CorrectiveAction&cerca=pompa`.
- Uscita dall'editor, cambio versione e navigazione indietro con modifiche pendenti offrono
  «Resta», «Salva nuova revisione», «Scarta». Un salvataggio fallito conserva la bozza.
- Recupero locale della bozza per manuale, base e hash, con messaggio «Bozza recuperata».
  L'autosalvataggio della bozza non crea revisioni; al rientro si verifica che la base coincida.

### 4.3 Salvataggio

1. «Salva nuova revisione» apre un riepilogo: elementi aggiunti, modificati e rimossi,
   impatto sulle relazioni e sulle verifiche, errori e avvisi; nota facoltativa della persona.
2. Gli errori strutturali impediscono il salvataggio; gli avvisi sono consultabili e non
   obbligano a inventare valori assenti nel manuale.
3. «Crea revisione» conferma il salvataggio. Il server valida e pubblica un nuovo snapshot.
4. L'app apre la nuova revisione in consultazione, mantenendo la vista utile, e aggiorna
   libreria, manuale, selettore delle versioni e «Tocca a te».
5. Una modifica successiva parte da questa revisione e produce un'altra revisione.

«Salva» è disabilitato se non esiste una differenza effettiva. Modificare e poi riportare il
valore all'originale non crea rumore nella cronologia. L'approvazione è un'azione distinta.

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

Si propone un contratto specifico per i grafi revisionati, `kg-v3-graph-3`, mantenendo lettura
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

Dettagli del contratto proposto:

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
- **Bozza:** lavoro non ancora pubblicato; può essere recuperato localmente e annullato.

Le revisioni sono visibili nella cronologia del manuale insieme alle versioni estratte,
con etichette distinte e relazione «deriva da». Il comando attuale «Nuova versione», che
avvia una nuova estrazione, diventa «Nuova estrazione» dove necessario per evitare ambiguità.

Una revisione usa un ID opaco stabile, per esempio `revision~<uuid>`, e un numero leggibile
assegnato per manuale sotto lock. Il suo padre può essere un run o un'altra revisione.
Modificare una versione storica crea una derivazione esplicita, non cambia gli altri figli.

### 7.2 Struttura proposta

```text
workspace/<manual_id>/
  runs/…                           # struttura esistente
  revisions/<revision_uuid>/
    revision.json                  # identità, padre, hash, fonte, autore, data, nota
    base-graph.json                # base esatta usata per il salvataggio
    graph.json                     # nuovo snapshot completo, formato revisionato
    changes.json                   # operazioni e differenze prima/dopo
    validation.json                # controlli sullo snapshot salvato
    source-review.json             # domande/decisioni ereditate come contesto
    source-report.json             # rapporto della fonte, se presente, dichiarato storico
  revision-decisions/<revision_uuid>/
    <decision_uuid>.json           # eventuale approvazione/rifiuto del contenuto salvato
```

`revision.json` contiene almeno: `schema_version`, `revision_id`, `revision_number`,
`manual_id`, `parent_version_id`, `parent_graph_hash`, `root_run_id`, `created_at`,
`created_by`, `note`, `graph_hash`, `ontology_hash`, `source_document_hash`,
`editor_code_commit`, `request_id` e riepilogo delle operazioni.

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

1. Risolvere manuale/base e capacità; verificare hash della base, schema e riferimenti alla
   fonte, e che il processo sorgente sia fermo.
2. Sotto lock del manuale, ricontrollare precondizioni e chiave di idempotenza.
3. Applicare le operazioni, aggiornare derivati e fiducia, validare il risultato completo.
4. Scrivere i file in una directory temporanea nascosta sullo stesso filesystem; completare
   le scritture prima della pubblicazione con rename atomico.
5. Rendere la nuova revisione visibile al catalogo e restituire ID/hash/riepilogo.

- Il catalogo ignora directory temporanee e revisioni incomplete. Un crash non deve far
  apparire una revisione parziale o rimuovere la versione sorgente.
- Doppio clic e retry dopo timeout con lo stesso `request_id` restituiscono la stessa
  revisione; stesso ID con contenuto diverso produce un conflitto.
- Se la base muta durante l'editing, risposta `409`: conservare la bozza e offrire confronto
  e riapertura sulla nuova base. Nessuna fusione automatica delle correzioni.
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

**Approvazione della revisione.** Il primo salvataggio produce uno snapshot «Da approvare»,
anche se il padre era approvato. «Approva questa revisione» registra una decisione separata
legata a `graph_hash`, senza avviare la pipeline e senza modificare `graph.json`. L'API della
versione espone lo stato effettivo; il `status` dentro lo snapshot descrive il momento del
salvataggio. In download, la decisione è disponibile come metadato allegato o in un pacchetto
esplicito: non riscrivere il file congelato per cambiare una targhetta.

Le domande residue della fonte e i contenuti non verificati devono essere visibili durante
l'approvazione, con una scelta esplicita di accettare i dubbi residui e una nota registrata.
Questa è un'approvazione manuale dello snapshot, non una risposta retroattiva alle domande
del run e non una conferma di tutte le relazioni. Gli errori strutturali restano bloccanti.

**Navigazione e contatori.**

- `Version` diventa una unione discriminata o un contratto con `kind: run | revision`,
  padre, riepilogo e capacità (`can_edit`, `can_approve`, `can_replay`, `can_resume`).
- La libreria apre per default l'elemento salvato più recente, con etichetta «Revisione N».
  Il manuale rende raggiungibile anche l'ultima revisione approvata e l'esecuzione di origine.
- Le revisioni compaiono nella tabella delle versioni; in «Esecuzioni» restano i processi,
  con eventuale collegamento alle revisioni generate a valle, senza duplicare costi e tempi.
- «Tocca a te» considera le attività aperte per versione, non solo `manual.latest`: creare
  una revisione non deve nascondere un run attivo o domande ancora pendenti sul padre.
- `flow/steps.ts` usa, per una revisione, «Modifiche salvate → Controllo → Approvazione».
  `nextStep` porta al controllo della revisione, mai a una finta esecuzione.
- Gli endpoint di job rifiutano esplicitamente gli ID delle revisioni; quelli di lettura
  risolvono sia run sia revisioni attraverso un resolver comune.

## 9. Architettura applicativa proposta

### Frontend

Un contenitore comune del grafo tiene caricamento, selezione e bozza, indipendentemente
dalla vista visibile. La bozza comprende base immutabile, operazioni, valori correnti,
validazione e pila undo/redo. I selettori calcolano indici, collegamenti e filtri.

Il renderer 3D riceve proiezioni del documento e mantiene separati i propri oggetti mutabili
di simulazione: coordinate e riferimenti Three.js non entrano mai nel grafo da salvare.
I nodi isolati rimangono nella vista editor; filtri e navigazione conservano la selezione.

| File/area | Lavoro previsto |
| --- | --- |
| `screens/FinishedGraph.tsx` e nuovo contenitore `screens/GraphWorkspace.tsx` | Estrarre lo spazio condiviso senza duplicare caricamento, barra e pannelli |
| Nuovi `editor/model.ts`, `editor/reducer.ts`, `editor/selectors.ts` | Operazioni, bozza, undo/redo, indici adattati dal riferimento e diff |
| Nuovi `editor/EditableTable.tsx`, `editor/NodeTable.tsx`, `editor/RelationTable.tsx` | Tabelle, editor di celle, filtri e navigazione per ID |
| Nuovi `editor/ReviewPanel.tsx`, `editor/SaveRevisionDialog.tsx` | Controlli navigabili, anteprima delle conseguenze e riepilogo salvataggio |
| `components/Table.tsx`, `Controls.tsx`, `EvidencePanel.tsx`, `PageDialog.tsx` | Riutilizzo delle parti comuni; editor fonti e controlli accessibili |
| `graph/Graph3D.tsx`, `graph/style.ts` | Focus su ID, isolamento visibile, conservazione camera/posizioni, nuovi stati |
| `api/types.ts`, `api/client.ts`, `App.tsx` | Contratti run/revisione, operazioni, errori strutturati e route editor |
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

### Contratto API indicativo

I percorsi sono una proposta da implementare, non endpoint già disponibili.

| Metodo e percorso, sotto `/api/manuals/{m}` | Responsabilità |
| --- | --- |
| `GET /versions/{v}/editor` | Documento originale, hash/precondizioni, schema, fonte, capacità e contesto di review |
| `POST /versions/{v}/validate-edits` | Applicare in memoria le operazioni; restituire errori per cella, avvisi e impatto |
| `POST /versions/{v}/revisions` | Salvare un nuovo figlio; accettare `base_hash`, token schema/fonte, `request_id`, operazioni e nota |
| `GET /versions/{revision}/changes` | Diff rispetto allo snapshot base, con link agli elementi |
| `POST /versions/{revision}/review-decisions` | Approvare/rifiutare lo snapshot mediante hash e decisione esplicita |
| `GET /versions/{v}/source-segments?page=…&q=…` | Cercare nella fonte verificata, con paginazione e riferimenti risolvibili |
| `GET /versions/{v}/graph` e letture esistenti | Risoluzione uniforme; rapporto della revisione distinto dal rapporto della fonte |

Operazioni tipizzate, per esempio `node.add`, `node.set_property`, `node.remove_property`,
`node.delete`, `edge.add`, `edge.replace_endpoints`, `edge.delete`, `occurrence.update`,
`occurrence.confirm`, con allowlist dei campi modificabili. Le ID provvisorie di elementi
nuovi vengono rimappate dal server e restituite al client.

Validare nuovamente tutto nel salvataggio: la validazione di anteprima non è un'autorizzazione
riutilizzabile su dati cambiati. `422` restituisce codice del problema, elemento, campo e
messaggio traducibile; `409` indica una precondizione superata; errori di I/O lasciano la
bozza intatta. Estendere `ApiError`: oggi conserva solo una stringa di dettaglio.

## 10. Coerenza visiva e semplicità

Seguire [DESIGN.md](DESIGN.md) e `frontend/src/styles/tokens.css`:

- Cornice industriale, rail da 56 px, barra percorso da 48 px, palette grafite calda.
- Onest per il testo, JetBrains Mono per ID, conteggi e dati; controlli da 32 px, righe
  compatte da 36 px, bordi da 1 px, raggi da 4 px, griglia da 4 px.
- Tabelle e pannelli chiari; fondo scuro per il grafo. I colori dei tipi restano quelli attuali.
- Nessuna voce «Editor» nella sidebar: si lavora sul grafo già selezionato.
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
| 3. Editing completo | Celle tipizzate, CRUD nodi/relazioni/occorrenze, selezione fonti, invalidazione verifiche, undo/redo e bozza | Le correzioni si vedono in tutte le viste; cancellazioni e annullamenti sono atomici e recuperabili |
| 4. Salvataggio e flusso | Anteprima diff, nuova revisione, cronologia, approvazione dedicata, ingressi dalla fine esecuzione e libreria | Percorso completo creazione → modifica → salva → riapri → modifica → seconda revisione |
| 5. Controlli e rifinitura | Dashboard navigabile, contatori coerenti, gestione anomalie/conflitti, IT/EN, guida e QA visiva | Tutti i criteri della sezione 12 verificati e nessuna regressione dei flussi esistenti |
| Successiva, opzionale | Suggerimenti AI, eventuale vista 2D locale, merge/split di nodi, operazioni massive | Scope deciso su casi d'uso reali; indipendente dal completamento del primo rilascio |

Non occorre migrare in scrittura i grafi già presenti. Si aggiungono lettori compatibili,
si lavora su copie e si introduce il nuovo formato soltanto per le revisioni salvate.

## 12. Verifiche e criteri di accettazione

Test offline con fixture piccole e mirate, inclusi casi derivati dalla logica del riferimento
e adattati al formato nativo. Nessuna nuova estrazione reale necessaria.

1. Da un grafo appena creato e da uno storico si arriva allo stesso editor, con lo stesso
   aspetto dell'applicazione e senza caricamento/esportazione manuale di file intermedi.
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
11. Retry idempotente, due schede, conflitto della base, processo che riparte e crash durante
    scrittura non causano sovrascritture, revisioni parziali o perdita della bozza.
12. Il catalogo e i suoi dati in cache riflettono il nuovo contenuto. Il rapporto originale
    non appare come rapporto della revisione; tempi/costi non vengono duplicati in Esecuzioni.
13. L'approvazione di una revisione non usa la pipeline; le domande della fonte restano
    riconoscibili e le attività aperte su altri elementi non scompaiono da «Tocca a te».
14. Passaggi controlli → riga → relazione → nodo → grafo → pagina PDF conservano contesto;
    navigazione indietro, cambio versione e uscita proteggono la bozza.
15. UI verificata nelle due dimensioni previste, in IT e EN, con tastiera, testi lunghi,
    filtri senza risultati, caricamenti, errori API e manuale non disponibile.

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
gli stessi controlli e «Salva nuova revisione». Provenienza della proposta e decisione umana
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
