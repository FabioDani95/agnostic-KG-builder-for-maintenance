# Frontend prototipale: libreria dei grafi, caricamento del PDF, grafo 3D che cresce

Lavora nel repository agnostic-KG-builder-for-maintenance, su un branch nuovo `feat/frontend-prototype`
creato da `feat/cite-check-ask-v3`. Prima leggi: `AGENTS.md`, `README.md`, `docs/PIANO_V3.md`
(sezioni 3–6: stazioni, cancelli, domande, stato salvato), `backend/kg_v3/run.py`,
`backend/kg_v3/contracts.py` (`Question`, `Answer`), `backend/kg_v3/export.py` (formato di `graph.json`),
una cartella di esecuzione completa, per esempio `campaign/lg_lmh2235st/runs/v3_r1/`
(`graph.json`, `report.json`, `state/`, `questions_for_people.txt`).

Prototipo visivo di riferimento (cliccabile, quattro schermate):
https://claude.ai/artifact/S4zBRjGb6iBs7FMYK4Zif3. Vale **solo per la struttura** (quali schermate,
che cosa contengono, come si passa dall'una all'altra). Il suo aspetto **non** va copiato: Fabio lo
ha bocciato proprio per i dettagli elencati nella sezione 4 (puntini separatori, scritte piccole sopra
i titoli, pallini colorati di stato, etichette in maiuscolo, riga di numeri grandi, alone dietro il
grafo). Le regole della sezione 4 prevalgono sul prototipo.

## 0. Scopo

Un'interfaccia **prototipale ma chiara e strutturata** sopra la pipeline V3, che oggi esiste solo
da riga di comando. Deve permettere a Fabio di:

1. vedere **tutti i grafi e le loro versioni** (una versione = un'esecuzione);
2. **caricare un manuale PDF** e avviare una nuova esecuzione;
3. seguire l'esecuzione dal vivo: al centro un **grafo 3D a pallini** (i nodi: è l'unico posto dove compaiono cerchi) che compaiono man mano che il
   sistema trova e verifica relazioni, con le stazioni e le relazioni trovate ai lati;
4. rispondere alle **poche domande per la persona** (cancello dei dubbi e approvazione);
5. aprire un grafo finito, navigarlo, vedere le prove di ogni arco (segmenti, pagine, semaforo).

Non è un prodotto: niente autenticazione, multiutente o deploy. Deve però essere pulito, con codice
che si possa far crescere.

## 1. Fase 0: domande a Fabio (prima di scrivere codice)

Fai queste domande in un solo messaggio, poche e con una proposta di default per ciascuna, poi
scrivi il piano (fase 1) e aspetta l'ok.

1. **Lingua dell'interfaccia:** italiano (proposta) o inglese? Il testo dei manuali resta originale.
2. **Stack:** proposta Vite + React + TypeScript per il frontend, FastAPI per le API (già usato in
   passato nel progetto), un solo comando per avviare entrambi. Alternative accettabili se motivate.
3. **Grafo 3D:** proposta `3d-force-graph` (three.js, forze fisiche, pallini e archi); alternativa
   react-three-fiber con layout proprio. Colori per tipo di nodo come nel prototipo?
4. **Esecuzioni reali o registrate:** per sviluppare e mostrare, proposta di una modalità
   **replay** che rigioca un'esecuzione già fatta (stato salvato in `runs/.../state/`) a velocità
   reale o accelerata, a costo zero. Le esecuzioni reali solo con un pulsante esplicito, sul registro
   di spesa e con tetto.
5. **Domande:** chi risponde nella UI (solo Fabio)? Tutte le domande pendenti o solo quelle entro il
   budget di 10 per manuale?
6. **Versioni:** che cosa distingue due versioni nella libreria (data, commit del codice, esito,
   rami)? Serve un confronto tra due versioni dello stesso manuale?
7. **Dove vivono i dati:** proposta di leggere direttamente `campaign/<manuale>/runs*/` e una
   cartella nuova `workspace/` per i manuali caricati dalla UI, senza database.

## 2. Che cosa c'è oggi, e che cosa manca

- **C'è:** `Pipeline` in `backend/kg_v3/run.py` con stato salvato dopo ogni stazione e ogni unità
  (`state/map.json`, `state/units.json`, `state/extract_<unità>.json`, `state/checked_*.json`, gate
  `gate_*.json`), `graph.json` e `report.json` alla fine, domande come oggetti `Question` con opzioni
  fisse, revisore umano via `QuestionStore` (`HumanReviewer`), CLI `scripts/kg_v3.py`.
- **Non c'è:** nessuna API web, nessun frontend (il vecchio è stato rimosso, tag `legacy-v22`), nessun
  flusso di eventi durante l'esecuzione.

Da costruire, **senza toccare la logica di estrazione**:

1. **Eventi di avanzamento.** Un hook minimo e opzionale in `Pipeline` (callback o coda) che emette
   eventi tipizzati: stazione iniziata/finita, pagina mappata, unità estratta con le sue proposte,
   relazioni verificate con il semaforo, nodi e archi del grafo fuso, domanda aperta, domanda
   risposta, esecuzione finita. Senza hook il comportamento resta identico (i test lo verificano).
2. **API** (FastAPI): lista dei manuali e delle loro versioni; dettaglio di una versione (`graph.json`,
   `report.json`); caricamento PDF e avvio di un'esecuzione (in background, con `workdir`); flusso di
   eventi in **Server-Sent Events**; domande aperte e invio di una risposta (usando `Answer` e
   `validate_answer`); testo di un segmento e immagine di una pagina per le prove.
3. **Replay:** una sorgente di eventi che legge una cartella di esecuzione finita e ricostruisce la
   sequenza (ordine delle unità, proposte, verifiche, grafo finale) per animare la UI senza spendere.

## 3. Schermate

1. **Libreria.** Titolo, ricerca, filtro (tutti / da rivedere / approvati), tabella dei manuali
   (vedi sezione 4) e pulsante «Nuovo grafo». Aprendo un manuale: le sue versioni in ordine di data,
   ciascuna con codice usato, relazioni verificate, domande aperte, stato.
2. **Nuovo grafo.** Area di trascinamento del PDF, riga del file con pagine lette, campi macchina /
   marca / modello / tipo (come `info.yaml`), scelta di chi risponde ai dubbi (solo agente, agente
   poi io, solo io), stima di tempo e costo (dai dati delle esecuzioni passate, dichiarata come
   stima), «Avvia estrazione».
3. **Esecuzione dal vivo** (sfondo scuro, come una sala di controllo): a sinistra le sei stazioni con
   stato e dettaglio («unità 4 di 8»); al centro il **grafo 3D** che cresce, con contatori (nodi,
   relazioni, verificate); a destra l'elenco delle relazioni appena trovate. In alto tempo trascorso,
   costo finora, pausa, «N domande per te». Un nodo del grafo compare quando nasce; un arco
   diventa pieno quando è verificato (verde), tratteggiato se in dubbio, sparisce se scartato.
   Clic su un pallino: pannello con nome, tipo, segmenti citati e pagine.
4. **Domande per te.** Una domanda per volta, con avanzamento: le parole del manuale (con pagina,
   apribile), le affermazioni del sistema **scritte per una persona** (non l'enunciato tecnico del
   verificatore), tre pulsanti fissi (sì / solo in parte con scelta dei numeri / no).
5. **Grafo finito.** Il grafo 3D navigabile, ricerca per sintomo o codice, percorso sintomo → causa →
   azione evidenziato, pannello delle prove di ogni arco, filtro per semaforo, e cambio di versione.

## 4. Stile: sobrio, geometrico, alla Apple, senza segni da interfaccia generata

Riferimenti: [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines),
[Liquid Glass](https://developer.apple.com/documentation/technologyoverviews/liquid-glass). Segni tipici di
un'interfaccia "vibe coded", da evitare:
[Fountain Institute](https://www.thefountaininstitute.com/blog/signs-vibe-coded-ui),
[Developers Digest](https://www.developersdigest.tech/blog/ai-design-slop-and-how-to-spot-it).

Prima di scrivere componenti, fissa le decisioni una volta sola in `docs/DESIGN.md` (griglia,
spaziature, scala tipografica, colori, raggi, ombre, movimento, componenti) e fallo approvare da
Fabio insieme al piano. Ogni schermata usa solo quei valori.

**Principi.** Chiarezza, deferenza (il grafo e i dati comandano, l'interfaccia si fa da parte),
profondità data dagli strati, non dagli effetti. Ogni elemento deve avere una funzione: se toglierlo
non fa perdere informazione né un'azione, si toglie.

**Geometria e allineamento.**
- Griglia a 8 px per tutte le misure; colonne fisse per pagina; margini uguali a sinistra e a destra.
- Tutto allineato: bordi sinistri su poche linee verticali, testi su linee di base comuni, stesse
  altezze per gli elementi dello stesso livello (righe di tabella, pulsanti, campi).
- Forme semplici e coerenti: rettangoli con un solo raggio per livello (per esempio 12 px per i
  pannelli, 8 px per i controlli), bordi a 1 px o nessun bordo, niente forme decorative.
- Liste e tabelle allineate in colonne, numeri allineati a destra con cifre tabulari
  (`font-variant-numeric: tabular-nums`).

**Tipografia.** Font di sistema (`-apple-system, "SF Pro Text", "SF Pro Display"`), scala corta
(per esempio 13, 15, 17, 22, 34 px), due pesi (regular e semibold). Maiuscole normali ovunque.
Contrasto del testo almeno 4,5:1, anche per il testo secondario.

**Colore.** Neutri (bianco, `#f5f5f7`, grigi, `#1d1d1f`) più **un solo** colore d'accento per le
azioni principali. Il colore porta significato solo nel grafo (un colore per tipo di nodo, con
legenda a testo) e negli stati di verifica degli archi. Fuori dal grafo, niente colore decorativo.

**Materiale.** Il vetro traslucido solo per barre e pannelli che galleggiano sopra il grafo, per
tenerlo visibile; altrove superfici piene. Rispettare `prefers-reduced-transparency` e
`prefers-reduced-motion`.

**Movimento.** Transizioni brevi (150–250 ms) che spiegano un cambiamento di stato; nel grafo i nodi
appaiono quando nascono e la scena resta ferma se l'utente la tocca. Niente animazioni decorative o
in loop fuori dal grafo.

**Vietato (Fabio lo ha escluso esplicitamente, o è un segno di interfaccia generata):**
- puntini o altri caratteri usati come separatori nel testo («49 pagine · 330 nodi»): usa colonne,
  etichette o righe separate;
- scritte piccole e inutili sopra o sotto i titoli (occhielli, sottotitoli di contorno come «8 manuali
  · 24 domande aspettano una risposta»): un titolo dice che cosa è la pagina, i dati stanno nel
  contenuto;
- pallini colorati di stato («● 10 domande per te»): lo stato si scrive a parole, per esempio una
  colonna «Domande aperte» con il numero;
- etichette tutto maiuscolo, badge sopra i titoli, righe di numeri grandi come «banner» di
  statistiche;
- gradienti, aloni, bagliori, ombre colorate, sfondi con macchie di colore;
- schede dentro schede, bordi colorati sul lato sinistro, griglie di schede identiche con un'icona in
  cima quando una tabella basta;
- emoji e icone decorative; le icone solo dove sostituiscono una parola nota (chiudi, cerca, indietro),
  tutte della stessa famiglia (per esempio SF Symbols o un set lineare unico);
- testi segnaposto, numeri inventati, frasi di marketing.

**Controlli.** Pulsanti con testo chiaro, un solo pulsante principale per schermata, controlli
segmentati per le scelte esclusive, bersagli di almeno 44 px, elementi veri (`button`, `input`,
`label`), navigazione da tastiera e focus visibile.

**Libreria (esempio di applicazione).** Una tabella, non una griglia di schede: colonne Manuale,
Macchina, Pagine, Versione, Relazioni verificate, Domande aperte, Stato; righe della stessa altezza;
un clic sulla riga apre il grafo; le versioni si vedono aprendo il manuale.

**Controllo prima di ogni consegna.** Fai uno screenshot di ogni schermata e confrontalo con questo
elenco, voce per voce; correggi prima di mostrarlo a Fabio.

## 5. Piano (da proporre a Fabio dopo la fase 0, con tutti i dettagli)

Scrivi il piano in `docs/PIANO_FRONTEND.md`: moduli, contratti delle API e degli eventi (con esempi
JSON), struttura delle cartelle, componenti React, gestione dello stato, test, fasi con criteri di
completamento. Fasi suggerite:

1. Eventi e replay nel backend, con test (nessun cambiamento dei risultati della pipeline).
2. API minime e flusso SSE, con test.
3. Libreria e dettaglio di un grafo finito (dati reali della campagna).
4. Esecuzione dal vivo in replay, poi con un'esecuzione reale su un manuale piccolo (Graco, 18 pagine,
   circa 0,02 USD).
5. Domande per te e approvazione, collegate a `HumanReviewer`.
6. Rifinitura dello stile, accessibilità, stati vuoti ed errori.

## 6. Regole

- **Non cambiare** estrazione, verifica, fusione, prompt, gold, esecuzioni salvate, ontologia,
  modello o protocollo di valutazione. L'hook degli eventi è l'unica modifica alla pipeline e va
  provato con un test che mostra risultati identici con e senza.
- Chiamate reali solo dal registro `campaign/real_call_budget.jsonl` (spesa attuale circa 12,8 su 20
  USD): per la UI al massimo 0,5 USD, sempre con `--spend-ceiling`; per tutto il resto il replay.
- Test per API ed eventi (pytest), test essenziali per il frontend; `ruff` e `pytest` verdi prima di
  ogni commit; commit piccoli; nessuna dipendenza pesante non motivata.
- Niente dati inventati nella UI: numeri e testi vengono dalle esecuzioni o sono segnaposto espliciti.
- Riporta a Fabio in italiano, in modo semplice: che cosa funziona, che cosa manca, come avviarlo
  (un comando).
