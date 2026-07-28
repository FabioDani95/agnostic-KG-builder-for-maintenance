# QA demo readiness report

> **Snapshot storico, non verdetto corrente.** Il report descrive il build
> testato prima delle correzioni D-01…D-05 e del redesign completato nel commit
> `6303abb` del 15 luglio 2026. I test di regressione aggiunti in seguito sono
> verdi; D-06…D-08 restano osservazioni da riesercitare in una nuova sessione
> manuale con modello reale. Il verdetto sotto vale esclusivamente per il build
> e il run indicati. Vedi [Cleanup Audit](../CLEANUP_AUDIT.md) per la verifica
> automatica corrente.

**Data esecuzione:** 15 luglio 2026  
**Verdetto:** **NON PRONTA per una demo enterprise end-to-end**  
**Build testata:** worktree locale, avvio con `./run.sh`, UI `http://127.0.0.1:8000/`  
**Manuale:** `manuals/LG_MICROWAVE.pdf` (49 pagine)  
**Run principale:** `run_a7534172fee14effab8b6090e34a38cf`  
**Secondo run concorrente:** `run_92b35c6537294f0cbb4f8ec0788b0b5a`

## Sintesi esecutiva

Il flusso reale completa caricamento, scoping, generazione dell'ontologia, estrazione, visualizzazione del grafo e registrazione delle decisioni della coda HITL. Non raggiunge però la fase `export`: l'azione `run_extraction` avvia correttamente l'estrazione, poi la catena asincrona fallisce nella costruzione del primo widget di review triplet per un'incompatibilità Pydantic. L'endpoint aveva già risposto HTTP 200 e la console non consuma lo stream SSE, quindi l'utente non riceve alcun errore.

Dopo aver gestito via UI tutti i 18 elementi HITL, il dashboard dichiara comunque “Run completo — pronto per l'export”, mentre lo stato autorevole resta `phase=extraction`, `run_status=awaiting_operator`, `next_step=review`, l'export è disabilitato e non esiste una CTA per proseguire. Inoltre, “Rifiuta il nodo” registra solo un evento di audit: il nodo rimane nel grafo, in contrasto con il testo UI.

Il run ha prodotto 20 triplet, 149 nodi e 215 relazioni visualizzati dalla console; 18/18 decisioni di coda sono state salvate. Dopo riavvio del server, l'API ha confermato `is_live=false`, `has_export=false`, `export_files=[]`, fase `extraction` e 18 eventi `review_decision`.

## 1. Bug verificati, ordinati per severità

| ID | Severità | File:riga | Repro realmente eseguito ed evidenza | Fallimento concreto in demo | Fix proposto |
|---|---|---|---|---|---|
| D-01 | **demo-blocker** | `backend/services/conversation/tools/common.py:430-483`; `backend/schemas/widgets.py:43-49`; `backend/services/conversation/tools/review.py:118-125`; `backend/services/conversation/actions.py:114-132` | Sul run principale, dopo click singolo su **Avvia estrazione**, il backend ha estratto 20 triplet. La catena automatica `run_extraction -> get_next_triplet` ha poi sollevato `ValidationError: triplet.logic_assessment Input should be a valid dictionary`, perché `_triplet_logic_assessment()` restituisce `list[str]` mentre lo schema richiede `dict[str, Any]`. Stack osservato nei log su `_emit_result(next_result)`/`validate_widget_payload`. | La review dei triplet non parte e il run non può transitare a `export`. L'azione HTTP risponde comunque 200 e la UI mostra un toast di avvio riuscito. | Allineare il contratto a un solo tipo (preferibilmente uno schema strutturato, oppure `list[str]` se quello è il payload voluto); aggiungere un test di contratto sul risultato reale di `_get_next_triplet`, non solo fixture statiche; propagare il fallimento asincrono nello stato persistito del run. |
| D-02 | **demo-blocker** | `frontend/console.js:293-310`, `frontend/console.js:703-714`, `frontend/console.js:1288-1340`; `backend/routers/runs.py:149-177`; `backend/services/conversation/tools/review.py:80-105` | Sono stati gestiti dalla UI tutti i **18/18** item: gap, ambiguità, low confidence e advisory. Gli eventi sono presenti in `events.jsonl`, ma `review_index` non avanza e nessuna decisione chiama `approve_triplet`/`skip_triplet`. Il dashboard è passato a “Run completo — pronto per l'export”; aprendo Export compariva “Estrazione non completata” con pulsante disabilitato. Stato API: `extraction / awaiting_operator / review`, nessun file export. | Contraddizione bloccante fra dashboard ed export; l'utente non ha alcun comando per completare il run. Anche correggendo D-01, le decisioni della coda console restano scollegate dalla macchina a stati della review triplet. | Unificare la coda della console con il workflow autorevole: ogni decisione deve mutare lo stato previsto e avanzare l'indice, oppure introdurre una CTA atomica “Concludi review” che valida la coda e porta a `EXPORT`. Il banner “completo” deve dipendere dalla fase backend, non solo dalla coda locale. |
| D-03 | **demo-blocker** | `frontend/console.js:295-310`, `frontend/console.js:1538-1543`; `backend/routers/runs.py:161-177` | Nel Review Center è stato rifiutato **Power Supply**. Dopo refresh e lettura API, l'evento `verdict=rejected` era salvato, ma `comp_power_supply` e la sua relazione erano ancora presenti nel grafo/snapshot. Lo stesso test è stato ripetuto con **Relay 2**. | La UI promette “Il rifiuto esclude il nodo dal grafo”, ma l'output mostrato al cliente contiene ancora entità rifiutate: problema di integrità e fiducia, non solo cosmetico. | Rendere l'endpoint di decisione transazionale sullo stato del grafo (o applicare un filtro autorevole in proiezione/export), restituire il grafo aggiornato e fare rollback dell'ottimismo UI se il salvataggio fallisce. |
| D-04 | **demo-blocker** | `frontend/console.js:551-565`; `backend/routers/chat.py:43-48`; `backend/services/conversation/events.py:32-42` | Un solo click su **Carica il PDF e avvia** ha lanciato due scoping concorrenti: `/chat/start` ha avviato l'auto-start e subito dopo il frontend ha inviato esplicitamente `propose_cut_plan`. Nei log erano presenti due workflow Scoping simultanei; `trace.jsonl` contiene due righe `ScopingAgent` quasi identiche (09:32:20.726Z e 09:32:20.763Z), entrambe da 4.653 token / $0,024683. Riprodotto anche nel secondo run. | Raddoppia chiamate/costo LLM e crea una race sullo stesso store. Il KPI UI di stage può mostrare solo l'ultimo valore e sottostimare il costo reale. | Scegliere un unico owner dell'avvio scoping: o auto-start backend o azione esplicita frontend. Aggiungere idempotency key/per-run action lock; il lock creato nell'event bus deve essere realmente usato attorno alle transizioni. |
| D-05 | **demo-blocker** | `frontend/console.js:668-681`, `frontend/console.js:829-835`; `backend/services/conversation/tools/scoping.py:187-190` | Dopo approvazione scoping, durante il draft ontologia (35 chiamate LLM, circa 1m56s), è stato fatto refresh. La pagina è tornata alla lista; riaprendo il run, `phase=scoping`, `run_status=in_progress`, `next_step=draft_ontology`, ma il controllo strutturale `cutPlan && !ontology` ha prevalso e il dashboard ha mostrato **“Tocca a te: approva la selezione”**. Il pulsante di approvazione era ancora attivo. `updated_at` è rimasto fermo per oltre un minuto durante lavoro effettivo. | Un utente può credere che il run sia fermo e riapprovare, avviando altro lavoro concorrente/costoso. Non esiste progresso persistito per i chunk in corso e il refresh perde la sessione selezionata. | Dare priorità a `run_status=in_progress`/`next_step=draft_ontology` rispetto agli indizi strutturali; persistere la fase `ontology_draft` prima della chiamata lunga e heartbeat/chunk progress; disabilitare l'approvazione appena accettata e renderla idempotente. |
| D-06 | **degrada UX** | `frontend/console.js:524`, `frontend/console.js:668-714`; `backend/routers/runs.py:107-136` | Con due run attivi è stato arrestato e riavviato `./run.sh`. I run erano consultabili ma `is_live=false`. Il run principale, fermo in `extraction/awaiting_operator`, è stato mostrato nel dashboard come **“Run completo — pronto per l'export”**; l'export restava disabilitato. Un run più vecchio in handoff scoping mostrava correttamente “Sessione non più attiva — run incompleto”, ma non era realmente riprendibile nonostante la promessa “puoi ... riprendere da dove eri”. | Dopo un riavvio o una demo interrotta, lo stesso stato archived viene classificato in modo diverso in base alla fase. Non esiste ripresa operativa dei run persistiti; si possono solo consultare. | Gestire `!is_live && phase != completed` come stato interrotto generale, prima del fallback “completo”. O reidratare esplicitamente lo store per la resume, oppure cambiare copy e offrire “clona/riavvia da snapshot”. |
| D-07 | **degrada UX** | `frontend/console.js:247-258`, `frontend/console.js:1666-1681` | Dal grafo è stato premuto **Back** del browser. Essendo l'app sempre su `/` senza history interna, il browser è tornato a `about:blank`; Forward ha riaperto l'app ma sulla lista sessioni, perdendo run e vista selezionati. | Durante una demo un gesto browser normale fa uscire dall'app; il rientro non ripristina il contesto. | Sincronizzare vista e `run_id` in URL/history (`pushState`/`popstate`) e ripristinare almeno l'ultimo run da URL o storage. |
| D-08 | **minore** | `frontend/console.js:1666-1681` | Alla riapertura dopo restart, prima che `loadRuns()` completasse la UI ha mostrato brevemente “Nessuna sessione salvata”; pochi istanti dopo sono comparse le sessioni persistite. | Flash di empty state fuorviante, particolarmente visibile se la rete è lenta. | Introdurre stato `loading` distinto da lista vuota e skeleton/spinner fino alla risposta. |

### Nota sui test automatici esistenti

Sono stati eseguiti:

```text
pytest -q tests/test_widget_contract.py tests/test_chat_actions_service.py \
  tests/test_runs_router.py tests/test_chat_tools_state.py
17 passed
```

La suite passa nonostante D-01/D-02: manca un test integrato che faccia realmente `run_extraction -> get_next_triplet -> validate_widget_payload` e verifichi la transizione finale dopo le decisioni della console.

## 2. Trascrizione del percorso utente

### Percorso principale

| Step utente | Risultato osservato | Chiarezza/feedback/errori |
|---|---|---|
| Avvio `./run.sh` e apertura `/` | App caricata, lista delle sessioni leggibile. | Nessun errore console rilevante; richiesta favicon 404 ignorabile. |
| Nuova sessione, scelta `LG_MICROWAVE.pdf`, impostazioni predefinite `gpt-5.4`, lingua italiana | Manuale trovato e caricato: 49 pagine. | La UI dice “Carica PDF” ma non offre file picker: consente solo di scegliere PDF già presenti in `manuals/`. Per un utente nuovo non è evidente. |
| Click singolo “Carica il PDF e avvia” | Bottone disabilitato con “Avvio in corso…”, creato un solo run. | Il doppio click è protetto da `S.starting` (**pass**), ma il singolo avvio genera due workflow scoping (D-04). |
| Attesa scoping | Selezionate 29/49 pagine, 16 sezioni visibili. | Selezione e motivazioni sono leggibili. Il testo invita ad “approvare o correggere”, ma non c'è un editor: solo approvazione; la modifica diventa disponibile solo come pulsante disabilitato dopo l'approvazione. |
| Click “Approva selezione e continua” | Draft ontologia partito; 35 chiamate ontology, 280.889 token. | Il pulsante resta azionabile mentre il task asincrono lavora; feedback di avanzamento limitato all'età di `updated_at`, che non si aggiorna durante la lunga fase. |
| Refresh a metà draft e riapertura del run | Run persistito e ritrovato. | Selezione del run persa; falso handoff “approva la selezione” mentre il backend sta lavorando (D-05). Nessun dettaglio chunk/progresso. |
| Fine draft ontologia | Dashboard: circa $1,44, 285k token, 37 chiamate; 149 nodi, 215 relazioni; coda 18. | KPI e categorie sono utili. Il costo totale osservato dall'API è poi $1,461433 / 290.178 token / 39 call; il doppio scoping rende la lettura per-stage ambigua. |
| Click singolo “Avvia estrazione” | Proiezione di 20 triplet; Review Center accessibile. | Toast positivo, nessun errore browser/network visibile. In realtà la catena successiva è fallita lato server con D-01; l'HTTP era già 200. |
| Review HITL manuale | Gestiti realmente 18/18 elementi: 4 gap (3 lasciati aperti, 1 gestito), 8 ambiguità confermate, 4 low-confidence (2 confermati, 2 rifiutati), 2 advisory presi in carico. | I controlli sono comprensibili. Le decisioni persistono dopo refresh/riapertura. Il rifiuto non modifica il grafo (D-03). “Lascia aperta (dichiarata nell'export)” promette un export che il workflow non riesce a raggiungere. |
| Fine review | Header: “Coda gestita — pipeline da completare”; dashboard: “Run completo — pronto per l'export”. | Messaggi tra loro contraddittori; nessuna CTA per completare la pipeline (D-02). |
| Esplorazione grafo | Grafo visualizzato: 149 nodi, 215 relazioni, 20 catene diagnostiche, 8 complete. Filtri e pannello di dettaglio funzionano. | Funzione consultabile; i nodi rifiutati restano presenti. Nessun errore console. |
| Apertura Export | “Estrazione non completata”; pulsante “Esporta grafo” disabilitato. | Nessun file generato e nessun KPI finale/export mostrato. Percorso happy-path **fallito**. |

### Percorsi “cattivi”

| Scenario | Esito | Evidenza/attrito |
|---|---|---|
| Refresh a metà run | **FAIL** | Persistenza presente, ma run selezionato perso e stato UI falso durante draft (D-05). |
| Tornare indietro | **FAIL** | Back porta a `about:blank`; Forward riparte dalla lista (D-07). |
| Doppio click su avvio | **PASS parziale** | Un solo run creato grazie a `S.starting`; il singolo flusso produce comunque doppio scoping (D-04). |
| Seconda sessione mentre la prima gira | **PASS funzionale, rischio UX** | Secondo run creato e lavorazione concorrente possibile. Le due sessioni omonime sono distinguibili quasi solo da run id/data; anche il secondo run ha riprodotto il doppio scoping. |
| Riprendere una sessione vecchia | **FAIL** | I dati persisted sono consultabili, ma dopo restart `is_live=false` e le azioni richiedono lo store live. La promessa di “riprendere” non corrisponde a una resume operativa (D-06). |
| File non-PDF | **PASS sul backend / percorso UI assente** | Chiamata reale `POST /api/load-manual` con `README.md` -> HTTP 404 JSON `Manual not found: README.md`; nessun 500. La UI non permette upload locale, quindi non è possibile tentare il file non-PDF dal percorso utente. |
| Chiudere e riaprire il browser, server ancora vivo | **PASS parziale** | Sessioni conservate e ricaricate; run/vista selezionati non conservati, serve riapertura manuale. |
| Riavvio server con run attivi | **FAIL** | Sessioni persistono ma diventano read-only; classificazione errata del run extraction come completo (D-06). |

### Console, rete e backend

- **Console browser:** nessun errore JavaScript durante il percorso principale e i test negativi.
- **Network:** le azioni asincrone, incluso `run_extraction`, rispondono HTTP 200 prima del completamento. Il fallimento D-01 non è rappresentato come errore HTTP.
- **SSE:** il backend indirizza progress/errori terminali al canale eventi, ma `frontend/console.js` non apre `/chat/stream/{pdf_id}`; la console usa solo polling dello snapshot. L'errore D-01 è quindi rimasto esclusivamente nel log server.
- **Input reali:** nessun endpoint sincrono ha restituito 500 nel percorso testato. Il file non-PDF è stato rifiutato con 404 controllato.
- **Timeout LLM:** non si è verificato un timeout nel run reale; le chiamate, inclusa la fase ontologia di circa 1m56s, sono terminate. Il comportamento UI in caso di timeout non è quindi marcato come bug riprodotto.

## 3. Checklist “pronto per demo”

| Voce | Esito | Nota |
|---|---|---|
| Avvio pulito con `./run.sh` | **PASS** | Backend e console raggiungibili. |
| Caricamento del manuale LG | **PASS** | 49 pagine caricate senza 500. |
| Upload locale comprensibile a un nuovo utente | **FAIL** | Nessun file picker; solo catalogo `manuals/`. |
| Protezione da doppio click sul pulsante iniziale | **PASS** | Creato un solo run. |
| Idempotenza dell'avvio pipeline | **FAIL** | Singolo click -> due scoping concorrenti. |
| Scoping e selezione pagine leggibili | **PASS** | 29/49 pagine, 16 sezioni. |
| Correzione manuale della selezione promessa dalla UI | **FAIL** | Nessun controllo di modifica operativo. |
| Feedback continuo durante chiamate LLM lunghe | **FAIL** | `updated_at` fermo, nessun chunk progress/SSE nella console. |
| Refresh a metà run senza stato UI incoerente | **FAIL** | Falso handoff e run selezionato perso. |
| Esecuzione estrazione completa | **FAIL** | Estrazione dati fatta, catena review triplet fallita. |
| Errori asincroni visibili e azionabili | **FAIL** | HTTP 200 + nessun feedback UI per D-01. |
| Review HITL usabile | **PASS parziale** | 18/18 decisioni registrate e ripristinate. |
| Decisioni HITL applicate al grafo | **FAIL** | Nodi rifiutati ancora presenti. |
| Transizione automatica review -> export | **FAIL** | Stato fermo in `extraction/awaiting_operator`. |
| KPI intermedi leggibili | **PASS** | Tempi/costi/token/nodi/relazioni visibili. |
| KPI finali dopo completamento | **FAIL** | Run mai completato. |
| Esplorazione grafo | **PASS parziale** | Vista funzionante, ma include nodi rifiutati. |
| Export e download artefatti | **FAIL** | `has_export=false`, lista file vuota, pulsante disabilitato. |
| Due sessioni contemporanee | **PASS parziale** | Funzionano, ma entrambe subiscono D-04 e sono poco distinguibili. |
| Resume dopo chiusura browser | **PASS parziale** | Dati presenti finché il server resta live; contesto UI perso. |
| Resume dopo riavvio backend | **FAIL** | Run persistito solo consultabile, non riattivabile. |
| Back/Forward del browser | **FAIL** | Uscita dall'app e perdita del contesto. |
| Rifiuto file non-PDF senza 500 | **PASS** | 404 controllato dall'API. |
| Gestione timeout LLM verificata E2E | **FAIL (non esercitata)** | Nessun timeout reale durante questa sessione; non si attribuisce un bug non riprodotto. |
| Suite mirata intercetta i blocker | **FAIL** | 17 test passano pur lasciando scoperti D-01/D-02. |

## Gate consigliato prima della demo

La demo può essere considerata candidata solo dopo verifica E2E di almeno questi criteri: singolo scoping per run; primo widget triplet validato e visibile; decisioni HITL che modificano davvero lo stato/grafo; transizione certa a `export`; errore asincrono mostrato in UI; refresh e restart classificati senza falsi “completo”. Va poi ripetuto lo stesso percorso LG fino alla generazione e download effettivo degli artefatti.
