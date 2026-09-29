# Frontend prototipale: libreria dei grafi, caricamento del PDF, grafo 3D che cresce

Lavora nel repository agnostic-KG-builder-for-maintenance, su un branch nuovo `feat/frontend-prototype`
creato da `feat/cite-check-ask-v3`. Prima leggi: `AGENTS.md`, `README.md`, `docs/PIANO_V3.md`
(sezioni 3–6: stazioni, cancelli, domande, stato salvato), `backend/kg_v3/run.py`,
`backend/kg_v3/contracts.py` (`Question`, `Answer`), `backend/kg_v3/export.py` (formato di `graph.json`),
una cartella di esecuzione completa, per esempio `campaign/lg_lmh2235st/runs/v3_r1/`
(`graph.json`, `report.json`, `state/`, `questions_for_people.txt`).

Prototipo visivo di riferimento (cliccabile, quattro schermate):
https://claude.ai/artifact/S4zBRjGb6iBs7FMYK4Zif3. È un'indicazione di struttura e di tono, non una
specifica al pixel.

## 0. Scopo

Un'interfaccia **prototipale ma chiara e strutturata** sopra la pipeline V3, che oggi esiste solo
da riga di comando. Deve permettere a Fabio di:

1. vedere **tutti i grafi e le loro versioni** (una versione = un'esecuzione);
2. **caricare un manuale PDF** e avviare una nuova esecuzione;
3. seguire l'esecuzione dal vivo: al centro un **grafo 3D a pallini** che compaiono man mano che il
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

1. **Libreria.** Titolo grande, ricerca, filtro (tutti / da rivedere / approvati), griglia di schede:
   una per manuale, con tipo di macchina, nome, pagine, nodi e relazioni verificate, stato
   («Approvato», «3 domande per te»), versioni come piccole pillole (l'ultima evidenziata). Pulsante
   «Nuovo grafo».
2. **Nuovo grafo.** Area di trascinamento del PDF, riga del file con pagine lette, campi macchina /
   marca / modello / tipo (come `info.yaml`), scelta di chi risponde ai dubbi (solo agente, agente
   poi io, solo io), stima di tempo e costo (dai dati delle esecuzioni passate, dichiarata come
   stima), «Avvia estrazione».
3. **Esecuzione dal vivo** (sfondo scuro, come una sala di controllo): a sinistra le sei stazioni con
   stato e dettaglio («unità 4 di 8»); al centro il **grafo 3D** che cresce, con contatori (nodi,
   relazioni, verificate); a destra l'elenco delle relazioni appena trovate. In alto tempo trascorso,
   costo finora, pausa, «N domande per te». Un pallino compare quando un nodo nasce; un arco
   diventa pieno quando è verificato (verde), tratteggiato se in dubbio, sparisce se scartato.
   Clic su un pallino: pannello con nome, tipo, segmenti citati e pagine.
4. **Domande per te.** Una domanda per volta, con avanzamento: le parole del manuale (con pagina,
   apribile), le affermazioni del sistema **scritte per una persona** (non l'enunciato tecnico del
   verificatore), tre pulsanti fissi (sì / solo in parte con scelta dei numeri / no).
5. **Grafo finito.** Il grafo 3D navigabile, ricerca per sintomo o codice, percorso sintomo → causa →
   azione evidenziato, pannello delle prove di ogni arco, filtro per semaforo, e cambio di versione.

## 4. Stile: Apple, nella versione attuale

Riferimenti: [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines),
[Liquid Glass](https://developer.apple.com/documentation/technologyoverviews/liquid-glass),
[Meet Liquid Glass, WWDC25](https://developer.apple.com/videos/play/wwdc2025/219/).

- **Principi:** chiarezza, deferenza (il contenuto, cioè il grafo, comanda; l'interfaccia si fa
  da parte), profondità (la gerarchia si legge dagli strati).
- **Materiale:** pannelli e barre in vetro traslucido che galleggiano sopra il contenuto
  (`backdrop-filter: blur(20–30px) saturate(160–180%)`, sfondo bianco o grigio scuro all'80–90%, bordo
  a 1 px quasi invisibile), angoli molto arrotondati (14–28 px), ombre morbide e larghe. Rispettare
  «riduci trasparenza» e «riduci movimento» del sistema (`prefers-reduced-transparency`,
  `prefers-reduced-motion`).
- **Tipografia:** font di sistema (`-apple-system, "SF Pro Display", "SF Pro Text"`), titoli grandi e
  pesanti con spaziatura negativa, testo 15–17 px, grigi secondari leggibili (contrasto ≥ 4,5:1).
- **Colore:** fondo chiaro `#f5f5f7` e testo `#1d1d1f`; schermata dal vivo scura (`#0b0b0f`); un solo
  accento blu (`#0071e3` chiaro, `#0a84ff` scuro); colori di sistema per i tipi di nodo (sintomo
  arancio, causa rosso, azione verde, componente azzurro, codice giallo), sempre con legenda.
- **Movimento:** animazioni brevi e fisiche (molle), mai decorative; i pallini «sbocciano» quando
  nascono, la scena 3D ruota piano e si ferma quando l'utente la tocca.
- **Controlli:** pulsanti a pillola, controlli segmentati, niente icone emoji, bersagli ≥ 44 px,
  elementi veri (`button`, `input`, `label`) e navigazione da tastiera.

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
