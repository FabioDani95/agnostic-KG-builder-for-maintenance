# Piano incrementale di miglioramento frontend per demo enterprise

**Data analisi:** 15 luglio 2026  
**Perimetro:** `frontend/console.html`, `frontend/console.js`, `frontend/console.css`, verifica mirata di `frontend/editor/`  
**Vincoli assunti:** vanilla JS/CSS, nessun framework o dipendenza nuova, nessun endpoint nuovo, nessuna riscrittura di `console.js`.

## Metodo ed evidenze

Il piano deriva da un percorso realmente eseguito nell'app avviata con `./run.sh`, usando `manuals/LG_MICROWAVE.pdf`: nuova sessione, configurazione, scoping, approvazione, estrazione, quattro decisioni HITL, dashboard finale, grafo ed export. Per completare rapidamente tutte le schermate è stato usato `KG_LLM_MODE=mock`; layout, stato, polling, API e interazioni erano quelli reali. I risultati sono stati confrontati con il run LLM reale documentato in `docs/QA_DEMO_REPORT.md`.

Run visuale di questa analisi: `run_2ee138d8e0f74083b625bd90ecf30b79`, 49 pagine, 5 nodi, 4 relazioni, 4 item HITL gestiti. Sono stati inoltre riprodotti:

- refresh che torna alla lista e perde run/vista selezionati;
- flash iniziale “Nessuna sessione salvata” prima del caricamento della lista (D-08);
- errore di rete mostrato solo come toast temporaneo, senza recovery, mantenendo dati vecchi a schermo;
- inspector della review che si chiude dopo ogni decisione, obbligando a selezionare il prossimo item;
- stepper che evidenzia `Review` mentre la CTA chiede ancora “Avvia estrazione”;
- dashboard finale visivamente quasi identica a quella intermedia e priva di coverage, failure mode e bilancio delle decisioni umane.

I demo-blocker D-01…D-05 del report QA risultano già corretti e non sono oggetto di questo piano.

## (a) Scorecard

| Dimensione | Voto | Sintesi |
|---|---:|---|
| 1. Guida | **3/5** | Il “tocca a te” è forte e lo stepper esiste, ma vive solo nel dashboard, salta Impostazioni/KPI e può indicare Review prima dell'avvio dell'estrazione. |
| 2. Trasparenza / KPI | **3/5** | Buona base di KPI intermedi, ma il lavoro lungo è raccontato con testo generico; i KPI finali enterprise già disponibili nelle API non vengono esposti. |
| 3. Coda di review | **4/5** | Priorità, filtri, ricerca e inspector sono solidi; manca una modalità di smaltimento continuo con auto-avanzamento, shortcut e batch conservativi. |
| 4. Gestione sessioni | **2/5** | La lista è leggibile ma gli stati “attende operatore” non dicono quale azione serve; refresh e Back perdono il contesto, archived e live sono poco distinti. |
| 5. Robustezza + wow | **2/5** | Il linguaggio visivo è sobrio e coerente, ma errori e loading non hanno recovery persistente; manca un momento finale memorabile ma controllato. |

## Valutazione dettagliata delle cinque dimensioni

### 1. Guida — 3/5

**Evidenza osservata.** Il banner “Tocca a te” con CTA è molto visibile (`console.js:669-716`, `console.js:777-798`) e lo stepper del dashboard è chiaro (`console.js:642-667`). Tuttavia:

- lo stepper non appare in Nuova sessione, Scoping, Review o Grafo;
- non include lo step Impostazioni né un vero arrivo KPI;
- sul run testato, dopo la bozza, mostrava `Review` come corrente mentre il banner chiedeva ancora “Avvia estrazione”: `reviewActive` prevale sulla fase in `console.js:648-655`;
- fuori dal dashboard l'orientamento resta affidato alla sidebar e alla pill molto compatta nell'header (`console.js:391-424`).

**Intervento.** Estrarre lo stepper esistente in un `renderFlowRail()` persistente e compatto, visibile sopra ogni vista di sessione. La sorgente autorevole deve essere `status.current_phase`, `run_status` e `next_step`; la presenza anticipata della review queue deve aggiungere un badge “4 pronti”, non spostare il passo corrente. Ordine proposto: **Manuale → Impostazioni → Scoping → Ontologia → Estrazione → Review → KPI/Export**. Mantenere il banner contestuale come unica CTA primaria.

### 2. Trasparenza / KPI — 3/5

**Evidenza osservata.** Il dashboard presenta già nodi, relazioni, catene, classi di confidence, durata e costo (`console.js:719-757`). Durante una fase lunga, però, il messaggio resta “Il sistema sta lavorando” con la sola età dell'ultimo snapshot (`console.js:701-704`, `console.js:1670-1682`). A fine run la stessa griglia non mostra:

- numero di `FailureMode`;
- coverage end-to-end e coverage failure mode → corrective action;
- pagine selezionate sul totale;
- conferme, rifiuti e advisory riconosciuti dall'operatore;
- chiamate LLM/token, pur disponibili.

**Intervento.** Due componenti distinti e incrementali:

1. **Progress card live**, alimentata dallo stream già esistente e con polling come fallback; barra determinata solo quando l'evento porta numeri reali, mai percentuali inventate.
2. **Executive KPI strip finale**, aggiunto sopra le card correnti solo in fase `export/completed`.

#### Fonti dati verificate

| Dato UI | Endpoint reale | Campi verificati |
|---|---|---|
| Fase, stato e prossimo passo | `GET /api/runs/{run_id}` | `status.current_phase`, `run_status`, `next_step`, `progress_percent`, `updated_at`, `phase_history` |
| Pagine selezionate | `GET /api/runs/{run_id}` | `state.selected_pages`, `state.total_pages`, `state.cut_plan` |
| Entità e failure mode | `GET /api/runs/{run_id}` | `state.ontology_pipeline.ontology.nodes`; conteggio per tipo, incluso `FailureMode` |
| Relazioni, catene, confidence e coda | `GET /api/runs/{run_id}` | `ontology.relations`, `confidence_report.counts`, `review_queue`, `events` |
| Progresso live scoping | `GET /chat/stream/{pdf_id}` (SSE) | eventi `type=progress`, messaggi con pagine analizzate/selezionate e sezioni |
| Progresso live estrazione | stesso SSE | `current_chunk`, `total_chunks`, `triplets_in_chunk`, `total_triplets`; il messaggio include le pagine del chunk |
| Entità a fine ontologia | stesso SSE | `node_count`, `human_fields_count`, `schema_issues_count` |
| Errori asincroni | stesso SSE | eventi `type=error`, oggi non consumati dalla console |
| KPI finali completi | `GET /run-metrics/{pdf_id}` | `document`, `totals`, `nodes_by_type`, `graph_coverage`, `review`, `derived_kpis`, `ingestion` |
| Decisioni umane | `GET /api/runs/{run_id}` oppure `GET /api/runs/{run_id}/review-decisions` | `events[].decision.verdict`: `confirmed`, `rejected`, `acknowledged`, ecc. |
| Stato sintetico alternativo | `GET /multi-agent/status/{run_id}` | replica autorevole di fase, progresso, metriche e ledger; non serve chiamarlo se è già disponibile il payload run |

Nota: `/run-metrics/{pdf_id}` è disponibile solo per un PDF ancora live (`backend/routers/generate.py:575-579`). Per sessioni archiviate il componente deve degradare sui dati inclusi in `GET /api/runs/{run_id}`, senza mostrare zeri come se fossero metriche complete.

**KPI finali consigliati.** Sei valori principali: entità totali, failure mode, coverage end-to-end, failure mode con azione correttiva, pagine usate, tempo/costo. Sotto, una riga “Decisioni umane” con confermati, rifiutati, advisory riconosciuti e ancora aperti. Token e chiamate LLM restano secondari, espandibili.

### 3. Coda di review — 4/5

**Evidenza osservata.** La gerarchia è già buona: ordinamento esplicito, filtri con conteggi, ricerca e righe con score (`console.js:1099-1152`). L'inspector spiega motivo, intervento suggerito e componenti della confidence. Nel percorso reale, però, dopo ogni conferma l'inspector si è chiuso e la lista ha richiesto un nuovo click. Non esistono shortcut visibili né selezione multipla. Alcuni testi tecnici restano in inglese anche con UI italiana.

**Intervento.** Aggiungere una “review mode” senza cambiare `POST /review-decisions`:

- auto-selezione del prossimo item aperto dopo salvataggio riuscito;
- shortcut `A`/`Enter` conferma, `R` rifiuta, `J/K` precedente/successivo, `Esc` chiude; disabilitati quando il focus è in un input;
- footer sticky `3 di 18 gestiti · 15 restano`, con legenda shortcut;
- batch solo per azioni omogenee e a basso rischio, ad esempio “Prendi atto di tutti gli advisory”, effettuando le chiamate esistenti una alla volta e mostrando successo parziale. Nessun “Approva tutto” misto prima della demo;
- nel dettaglio, affiancare “Dato estratto” e “Evidenza manuale” quando la citazione esiste; quando non esiste, mantenere l'empty state attuale ma renderlo visivamente esplicito.

### 4. Gestione sessioni — 2/5

**Evidenza osservata.** `viewRuns()` mostra manuale, data, modelli e pill di stato (`console.js:491-533`), ma molte righe LG risultano indistinguibili e “attende operatore” non dice se occorre approvare lo scoping, avviare l'estrazione o fare review. Il refresh ha riportato alla lista perdendo il run selezionato. È stato riprodotto anche il flash “Nessuna sessione salvata” prima della risposta: `S.runsList` nasce vuoto e `render()` precede `loadRuns()` (`console.js:32-41`, `console.js:1670-1685`).

**Intervento.** Rendere la lista un vero resume hub usando i campi già presenti in `GET /api/runs` (`last_phase`, `run_status`, `is_live`, `has_export`):

- `In elaborazione · Bozza ontologia`;
- `Azione richiesta · Approva pagine`;
- `Azione richiesta · Avvia estrazione`;
- `Azione richiesta · Review`;
- `Pronto all'export`;
- `Interrotta · consultabile` per `!is_live` non completato.

Memorizzare `run_id` e vista nell'URL/session storage, ripristinandoli al refresh. Per una sessione archived non promettere “riprendi”: usare “Apri snapshot” e una nota onesta. Aggiungere `runsLoading` e skeleton; l'empty state va mostrato solo dopo una risposta vuota. Questo risolve gratuitamente D-08 e, con `history.replaceState/popstate`, D-07; mitiga il copy fuorviante di D-06 senza fingere una resume backend che non esiste.

### 5. Robustezza + wow — 2/5

**Evidenza osservata.** Dopo arresto del backend e apertura Sessioni, l'app ha mantenuto la tabella precedente e mostrato per 3,5 secondi soltanto “Errore nel caricare le sessioni: Failed to fetch”. Nessuna CTA “Riprova” è rimasta a schermo. `refreshRun()` ignora deliberatamente ogni errore (`console.js:264-273`), mentre `loadRuns()` e `openRun()` usano solo toast (`console.js:219-262`). Gli empty state sono puliti, ma non distinguono sempre “loading”, “vuoto” ed “errore”.

**Intervento.** Introdurre piccoli state panel inline, non pagine nuove: icona, messaggio in linguaggio operativo, ultimo dato disponibile e CTA `Riprova`. Conservare il toast come feedback secondario. Per l'effetto wow a basso rischio:

- count-up dei sei KPI solo alla prima entrata in `export`, 350–500 ms;
- transizione opacity/translate di 140–180 ms tra le viste;
- halo singolo, non pulsante infinito, sul nuovo step corrente e sulla CTA “Tocca a te”;
- breve check sweep sul pannello finale, rispettando `prefers-reduced-motion`.

Sono effetti puramente presentazionali, senza timer che governano lo stato e senza animare il grafo durante la pipeline.

## (b) Interventi ordinati per impatto demo / rischio di rottura

Le stime includono markup template-string e CSS; non includono test Playwright consigliati.

| # | Intervento | Impatto / rischio | Righe stimate | File | Flag |
|---:|---|---|---:|---|---|
| 1 | **Flow rail persistente + unica next action autorevole** | Molto alto / basso | 70–100 JS, 40–60 CSS | `console.js`, `console.css` | **core** |
| 2 | **Session resume hub:** stati semantici, skeleton, URL/session restore | Molto alto / basso | 85–125 JS, 30–45 CSS | `console.js`, `console.css` | **core** |
| 3 | **Executive KPI strip finale** con coverage e decisioni umane | Alto / basso | 85–120 JS, 30–45 CSS | `console.js`, `console.css` | **core** |
| 4 | **Review accelerator:** auto-next, shortcut e footer sticky | Alto / medio-basso | 60–90 JS, 20–30 CSS | `console.js`, `console.css` | **core** |
| 5 | **Progress card live via SSE**, polling di fallback, nessuna percentuale finta | Molto alto / medio | 90–130 JS, 25–40 CSS | `console.js`, `console.css` | **core** |
| 6 | **Error panel persistente con Riprova** per lista, apertura run e polling | Alto / basso | 45–70 JS, 20–30 CSS | `console.js`, `console.css` | **core** |
| 7 | **Setup più esplicito:** “manuali disponibili” anziché upload, Avanzate richiudibili, riepilogo prima dell'avvio | Medio-alto / basso | 25–40 JS, 10–20 CSS | `console.js`, `console.css` | **core** |
| 8 | **Micro-motion controllata:** count-up KPI, view transition, check sweep e focus/hover coerenti | Medio / basso | 10–20 JS, 30–45 CSS | `console.js`, `console.css` | **core** |
| 9 | **Grafo demo-first:** CTA “Mostra prima catena diagnostica”, evidenzia percorso e attenua il resto | Medio / basso | 35–55 JS, 15–25 CSS | `console.js`, `console.css` | **core** |
| 10 | **Batch conservativo advisory** con conferma e resoconto parziale | Medio / medio | 45–70 JS, 10–20 CSS | `console.js`, `console.css` | **core**, dopo #4 |
| 11 | Collegamento “Editor avanzato” da advisory/grafo, aperto in nuova scheda e con warning | Medio / alto: editor visivamente divergente e `vis-network` arriva da CDN (`editor.html:6`) | 12–20 JS | `console.js` | **nice-to-have opzionale (alto rischio live)** |
| 12 | Grafo che si costruisce animato in tempo reale | Alto valore scenico / rischio molto alto di jank e stato parziale fuorviante | 120–180 JS/CSS | `console.js`, `console.css` | **nice-to-have opzionale (alto rischio live)** |
| 13 | Mappa animata degli agenti LLM e dei loro handoff | Medio valore informativo / alto rischio di rumore e desync | 80–120 JS/CSS | `console.js`, `console.css` | **nice-to-have opzionale (alto rischio live)** |
| 14 | “Approva tutto” su item review eterogenei | Alto risparmio tempo / rischio alto di decisioni errate e perdita di fiducia | 90–140 JS | `console.js` | **nice-to-have opzionale (alto rischio live)** — sconsigliato per la demo |

## (c) Mockup e punti d'innesto dei primi cinque interventi core

### 1. Flow rail persistente + next action

**Mockup testuale**

```text
Manuale ✓ ─ Impostazioni ✓ ─ Scoping ✓ ─ Ontologia ● ─ Estrazione ○ ─ Review ○ ─ KPI/Export ○
                              Bozza in corso · il sistema sta lavorando

oppure, in handoff:

Manuale ✓ ─ Impostazioni ✓ ─ Scoping ● ─ Ontologia ○ ─ Estrazione ○ ─ Review ○ ─ KPI/Export ○
[ Azione richiesta ] Controlla 29/49 pagine selezionate             [Vai allo Scoping]
```

**Punto d'innesto.** Creare `renderFlowRail(st)` subito dopo `phaseLabel()` (`console.js:436-445`). In `render()` inserirlo dentro `<main class="c-main">` prima della vista (`console.js:424`), senza cambiare le funzioni di vista. Riutilizzare le regole di `stageDefs/stageState` oggi locali al dashboard (`console.js:642-667`), correggendo la precedenza: `current_phase/next_step` determinano il passo, la queue produce solo un badge. Nel dashboard rimuovere solo il duplicato visivo, non la logica di stato o le CTA (`console.js:669-798`).

### 2. Session resume hub

**Mockup testuale**

```text
LG_MICROWAVE.pdf                                      Azione richiesta
run_2ee138d8 · oggi 13:34 · GPT-5.4                   Review · 4 item
Ultimo passo: Estrazione completata                   [Continua]

LG_MICROWAVE.pdf                                      Interrotta
run_965ed99e · oggi 12:33                             Snapshot consultabile
Ultimo passo: Bozza ontologia                         [Apri snapshot]
```

Durante il fetch, 6 righe skeleton con le stesse colonne; mai “nessuna sessione” finché `loadRuns()` non ha risposto.

**Punto d'innesto.** Aggiungere `runsLoading`, `runsError` e `lastContext` nello stato (`console.js:32-41`). Impostare loading/error in `loadRuns()` (`console.js:219-222`). In `viewRuns()` (`console.js:491-533`) derivare la pill da `run_status + last_phase + is_live + has_export`, tutti già restituiti da `GET /api/runs`. In `openRun()` (`console.js:247-262`) salvare `run_id/view` in query string e session storage; al boot (`console.js:1670-1685`) ripristinare il contesto solo dopo aver validato che il run esista. Aggiungere `popstate` per Back/Forward.

### 3. Executive KPI strip finale

**Mockup testuale**

```text
RUN VERIFICATO                                      49/49 pagine usate
5 Entità   1 Failure mode   100% Coverage E2E   100% FM con rimedio   0.47 s   $0.00

Decisioni umane: 3 confermati · 0 rifiutati · 1 advisory preso in carico · 0 aperti
[Esplora il grafo]  [Vai all'export]
```

Sul run reale i valori saranno quelli del payload, senza sostituire assenze con `0`; usare `—` e tooltip “metrica non disponibile per snapshot archiviato”.

**Punto d'innesto.** Aggiungere `runMetrics` nello stato (`console.js:32-41`) e una funzione `loadRunMetrics(pdfId)` accanto ai loader (`console.js:218-246`), chiamata soltanto quando `current_phase` entra in `export/completed`. In `viewDashboard()` inserire `renderExecutiveKpis()` tra il banner e la griglia esistente (`console.js:798-800`). Entità/failure mode vengono dal `run` già derivato; coverage, tempi e costi da `/run-metrics/{pdf_id}`; bilancio umano da `run.serverDecisions`/`events`. Le card attuali restano sotto come dettaglio.

### 4. Review accelerator

**Mockup testuale**

```text
Review Center                       3/18 gestiti · 15 restano
[Bloccanti 2] [Lacune 4] [Bassa conf. 9] [Advisory 3]      Cerca…

┌ Lista ──────────────────────────┬ Decisione ─────────────────────────┐
│ prossimo item già selezionato   │ Evidenza manuale / dato estratto   │
│ ...                             │ [A Conferma] [R Rifiuta]           │
└─────────────────────────────────┴────────────────────────────────────┘
J/K cambia item · Enter/A conferma · R rifiuta · Esc chiude
```

**Punto d'innesto.** Conservare filtri, sort e righe esistenti (`console.js:1099-1152`). Dopo una decisione riuscita, `decide()/persistDecision()` (`console.js:293-311`) selezionano il primo item ancora aperto nella lista ordinata, invece di lasciare `S.selected` nullo. Inserire contatore e shortcut hint nel toolbar di `viewReview()` (`console.js:1154-1168`). Aggiungere un solo listener `keydown` vicino agli altri listener globali, prima del boot (`console.js:1640-1670`), con guard su `INPUT/TEXTAREA`, vista corrente e inspector aperto. Le azioni continuano a usare lo stesso endpoint una per volta.

### 5. Progress card live via SSE

**Mockup testuale**

```text
ESTRAZIONE · IN CORSO                                     6 / 16 chunk
Pagine 18–23 analizzate · +3 triplette                  38%
████████████████░░░░░░░░░░░░
Finora: 12 triplette · ultimo aggiornamento 2 s fa

Se l'evento non ha numeri:
ONTOLOGIA · IN CORSO
Pre-mining completato: 13 componenti candidati, 0 codici errore
────────────────────────────  (barra indeterminata, non “45%” inventato)
```

**Punto d'innesto.** Aggiungere `liveProgress` e il riferimento `EventSource` nello stato/modulo (`console.js:32-46`). Creare `connectProgressStream(pdfId)` accanto a `schedulePoll()` (`console.js:264-290`) e invocarlo dopo `openRun()` (`console.js:247-258`); chiuderlo al cambio run e dopo stati terminali. Consumare solo `progress`, `error` e `done`, normalizzando i campi verificati. Nel banner running di `viewDashboard()` (`console.js:701-704`, `console.js:779-785`) sostituire il solo ticker con `renderLiveProgress()`. Il polling esistente resta fallback e sorgente autorevole dello stato; una disconnessione SSE non deve interrompere il run né mostrare errore bloccante.

## Sequenza consigliata prima della demo

1. Implementare #1, #2 e #6: massima chiarezza e recovery con rischio basso.
2. Implementare #3: dà una conclusione enterprise al percorso già funzionante.
3. Implementare #4 con test Playwright su shortcut, focus input, auto-next e ultimo item.
4. Implementare #5 dietro un piccolo feature flag locale (`const ENABLE_LIVE_PROGRESS = true`) per poter tornare al polling durante le prove generali.
5. Aggiungere #7 e #8 solo dopo un E2E completo LG; #9 se resta tempo.
6. Non portare in demo #11–#14 senza una prova generale separata e un fallback immediato.

## Criteri di accettazione visuali

- Da qualsiasi vista, in meno di due secondi un utente nuovo sa fase corrente e prossima azione.
- Nessuna barra avanza su una percentuale sintetica quando l'API non fornisce un denominatore reale.
- Refresh durante un run live riapre lo stesso run e la stessa vista; un archived è dichiarato consultabile, non riprendibile.
- La lista non mostra mai l'empty state prima della fine del caricamento.
- Un errore di rete lascia una CTA persistente `Riprova` e identifica se i dati mostrati sono l'ultimo snapshot disponibile.
- Dopo una decisione HITL, il prossimo item aperto è pronto senza click aggiuntivo; le shortcut non si attivano mentre si scrive.
- La schermata finale mostra almeno entità, failure mode, coverage, tempo/costo e bilancio delle decisioni umane.
- Tutte le animazioni rispettano `prefers-reduced-motion` e non governano mai lo stato applicativo.

