# Piano del prototipo frontend

Brief: [PROMPT_FRONTEND.md](PROMPT_FRONTEND.md). Decisioni visive: [DESIGN.md](DESIGN.md).
Branch: `feat/frontend-prototype`, creato da `feat/cite-check-ask-v3`.

## 0. In breve

Un server FastAPI legge le esecuzioni salvate e avvia quelle nuove. Un'app React le mostra:
libreria, nuovo grafo, esecuzione dal vivo con grafo 3D, domande per te, grafo finito.

Nella pipeline cambia una sola cosa: un hook opzionale che emette eventi. Tutto il resto
(estrazione, verifica, fusione, prompt, gold, ontologia, esecuzioni salvate) resta com'è.
Lo sviluppo usa il replay delle esecuzioni salvate, a costo zero. È prevista una sola
esecuzione reale, su Graco.

Si avvia con un comando:

```bash
.venv/bin/python scripts/ui.py
```

## Stato (29 settembre 2026)

Fasi 1–6 fatte, ciascuna con il suo commit. Differenze dal piano emerse lavorando:

- «Ferma» è `POST /manuals/{m}/versions/{v}/stop` invece di `/jobs/{job}/stop`.
- «Applica» e «Approva» rispondono quando la ripresa ha scritto il suo primo evento, e la vista
  segue solo l'ultimo tentativo di un'esecuzione: una ripresa ricarica tutto lo stato, quindi
  racconta l'intera storia.
- Terza anomalia della pipeline, **corretta** (ok di Fabio): la decisione di approvazione era la prima
  risposta nel registro del cancello, anche di una domanda vecchia; ora conta solo la risposta alla
  domanda del grafo attuale. Le copie della campagna continuano a non portare l'approvazione automatica.
- Esecuzione reale su Graco dall'interfaccia, in «Solo io»: 99 s, 31 chiamate, 0,0224 USD. Le sue
  10 domande sono per Fabio e non hanno risposta.

## 1. Decisioni prese (fase 0, 29 settembre 2026)

| # | Tema | Decisione |
| --- | --- | --- |
| 1 | Lingua | Interfaccia in italiano; nomi dei nodi e testo del manuale in originale. |
| 2 | Stack | Vite + React + TypeScript; FastAPI + SSE; un comando, `scripts/ui.py`. |
| 3 | Grafo 3D | `3d-force-graph`; sei colori per tipo con legenda scritta; archi verdi pieni, gialli tratteggiati, rossi nascosti. |
| 4 | Replay | Sviluppo e dimostrazioni in replay (1×, 4×, 16×). Esecuzioni reali solo da un pulsante esplicito. |
| 5 | Tetto di spesa | `--spend-ceiling 15.0` (alzato da Fabio). Per la UI resta il limite del brief: al massimo 0,5 USD in tutto. |
| 6 | Domande | Risponde solo Fabio. Si vedono le domande entro il budget di 10; le altre in sola lettura come «non verificate». |
| 7 | Esecuzioni della campagna | Mai modificate. Rispondere crea una copia in `workspace/`. |
| 8 | Frasi per una persona | Modelli di frase fissi per tipo di relazione, senza LLM; l'enunciato tecnico sotto «Dettagli». |
| 9 | Versioni | Una cartella `runs*/v3_rN` è una versione. `v22` esclusa; le fallite hanno esito «non riuscita». Nessun confronto tra versioni per ora. |
| 10 | Dati | Lettura diretta di `campaign/`; i nuovi manuali vanno in `workspace/` (ignorata da git). Niente database. |

## 2. Due problemi della pipeline e come si risolvono

Scrivendo il piano ho provato offline (fornitore finto dei test, nessuna chiamata reale) il
flusso «la persona risponde, poi l'esecuzione riprende». Ho trovato due problemi in `run.py`.
Non toccano le esecuzioni della campagna, che usano `--gates agent` e non hanno persone. Toccano
però proprio il flusso della fase 5.

**Problema A: l'agente può annullare la risposta della persona.** Con i dubbi in modalità
«agente, poi persona», la ripresa dopo le risposte rimanda all'agente le domande del cancello di
recupero. Queste domande hanno gli stessi ID di quelle a cui la persona ha appena risposto.

- Prova: la persona risponde «No» a due domande. Alla ripresa l'agente è sicuro e risponde «Sì».
  Risultato: 7 archi verdi su 7, cioè i «No» della persona sono persi e ci sono due chiamate in più.
- Con i dubbi solo alla persona, le risposte restano e la ripresa non fa nessuna chiamata.

**Problema B: il budget di 10 domande non vale tra una ripresa e l'altra.** L'elenco delle domande
già mostrate vive solo nella memoria del processo. Ogni ripresa può pubblicare altre 10 domande.
Inoltre la domanda di approvazione condivide lo stesso budget e può restare esclusa.

**Decisione (Fabio, 29 settembre 2026): le risposte della persona si applicano per ultime e
vincono sempre.**

- **A.** Correggo `run.py`: il cancello di recupero riusa le risposte già date da una persona a
  domande con lo stesso ID, invece di chiederle di nuovo all'agente. Su una domanda a cui ha
  risposto una persona l'agente non interviene più. Aggiungo un test. Per le
  esecuzioni con `--gates agent` il risultato non cambia; lo verifico rigiocando lo stato salvato
  di due manuali e confrontando i grafi.
- **B.** Nessuna modifica alla pipeline. Il budget lo tiene lo store persistente della UI (sezione 7.3):
  pubblica al massimo 10 domande per esecuzione, contate su tutte le riprese. L'approvazione
  passa dal pulsante «Approva» e non consuma budget, come prevede `PIANO_V3.md`
  («l'approvazione resta al pulsante del workspace»).

La correzione A va oltre l'hook degli eventi, che per il brief è l'unica modifica ammessa alla
pipeline: Fabio l'ha autorizzata esplicitamente. È un commit a parte, all'inizio della fase 5.

## 3. Architettura

```text
              ┌──────────────────────── browser ────────────────────────┐
              │ React: Libreria · Manuale · Nuovo grafo · Esecuzione ·   │
              │        Domande · Grafo finito (3d-force-graph)           │
              └───────────────▲──────────────────────▲──────────────────┘
                     REST JSON│                  SSE │ eventi
              ┌───────────────┴──────────────────────┴──────────────────┐
              │ FastAPI  backend/ui/api.py                               │
              │  catalog · questions · evidence · jobs · replay          │
              └──────┬─────────────────────┬──────────────────▲─────────┘
                     │ legge                │ avvia            │ legge events.jsonl
        campaign/<m>/runs*/v3_rN     scripts/kg_v3.py  ──scrive──┘
        workspace/<m>/runs/v3_rN     (processo separato, registro di spesa)
                                            │
                                     Pipeline(on_event=…)   ← unico cambiamento in run.py
```

Scelte:

- **Esecuzioni reali in un processo separato.** Il server lancia `scripts/kg_v3.py`, lo stesso
  comando della campagna, con tre opzioni nuove. Il gateway configura spesa e archivio con
  variabili d'ambiente di processo, quindi un processo per esecuzione le tiene separate. Se
  l'esecuzione si blocca, il server non cade. Una sola esecuzione reale alla volta.
- **Un traduttore di eventi, due sorgenti.** L'hook produce eventi grezzi («stato salvato»,
  «passo iniziato»). Il traduttore li trasforma in eventi per la UI. Il replay ricostruisce gli
  stessi eventi grezzi dai file di stato di un'esecuzione finita e usa lo stesso traduttore.
  Così dal vivo e in replay la UI riceve eventi identici.
- **Eventi salvati.** Un'esecuzione avviata dalla UI scrive `events.jsonl` nella sua cartella.
  Il flusso SSE legge quel file, quindi ci si può ricollegare e rigiocare esattamente quanto è successo.

### File nuovi e file toccati

| Percorso | Che cosa |
| --- | --- |
| `backend/kg_v3/run.py` | **solo** il parametro `on_event` e tre punti di emissione (sezione 4.1) |
| `scripts/kg_v3.py` | opzioni `--info`, `--events`, `--human-store`, tre preset `ui-*`; senza le opzioni nuove resta tutto uguale |
| `backend/ui/__init__.py` | pacchetto nuovo |
| `backend/ui/events.py` | modelli degli eventi UI e `EventTranslator` |
| `backend/ui/replay.py` | eventi grezzi ricostruiti da una cartella di esecuzione, con i tempi |
| `backend/ui/catalog.py` | manuali e versioni da `campaign/` e `workspace/` |
| `backend/ui/questions.py` | domande aperte di una versione e frasi in italiano |
| `backend/ui/store.py` | `FileQuestionStore`, persistente, che tiene il budget |
| `backend/ui/jobs.py` | avvio, ripresa, arresto, copia di una versione della campagna, approvazione |
| `backend/ui/evidence.py` | testo dei segmenti e immagine delle pagine (PyMuPDF) |
| `backend/ui/budget.py` | lettura del registro di spesa e stime da esecuzioni passate |
| `backend/ui/api.py` | app FastAPI con le rotte |
| `scripts/ui.py` | un comando: installa e compila il frontend se serve, poi avvia il server |
| `frontend/` | app Vite + React + TypeScript |
| `tests/test_ui_*.py` | test pytest |
| `requirements.txt` | `fastapi`, `uvicorn`, `python-multipart` |
| `requirements-dev.txt` | `httpx` (per il `TestClient` di FastAPI) |
| `.gitignore` | `workspace/`, `frontend/node_modules/`, `frontend/dist/` |
| `README.md` | sezione «Interfaccia» con il comando di avvio |

## 4. Eventi

### 4.1 L'hook nella pipeline

```python
EventSink = Callable[[str, dict[str, Any]], None]

class Pipeline:
    def __init__(..., on_event: EventSink | None = None) -> None: ...

    def _emit(self, kind: str, **data) -> None:
        if self.on_event is None:
            return
        try:
            self.on_event(kind, {**data, "cost_usd": <llm + agente>})
        except Exception:
            logger.exception("event sink failed")  # la UI non ferma mai l'esecuzione
```

Tre punti di emissione, nessun altro:

| Dove | Evento grezzo | Dati |
| --- | --- | --- |
| `_timed`, prima e dopo | `step_started`, `step_finished` | `step` (`map`, `scan`, `gate_map`, `extract`, `check`, `merge`, `split_recheck`, `navigation`, `gate_doubts`, `action_reduction`, `gate_recovery`, `gate_approval`…), `seconds` |
| `_save` | `state_saved` | `name` (`map`, `units`, `extract_<unità>`, `checked_<stamp>`, `gate_doubts`…), `value` in JSON |
| `_load`, quando trova un file | `state_loaded` | come sopra; serve alle riprese |

Il CLI aggiunge `step_started`/`step_finished` per `pdf_read` e, alla fine, `run_finished` con
`graph.json`.

**Prova che non cambia nulla.** Un test esegue la pipeline con il fornitore finto due volte,
con e senza hook, e confronta `RunResult` (tempi esclusi), `graph.json` e i file di stato: devono
essere identici. Un secondo test usa un hook che solleva un'eccezione: l'esecuzione finisce
comunque con lo stesso risultato.

### 4.2 Eventi per la UI

Ogni riga di `events.jsonl`, e ogni messaggio SSE, ha la stessa busta:

```json
{"seq": 17, "t": 42.8, "cost_usd": 0.0123, "kind": "unit_extracted", "data": {}}
```

`t` sono i secondi dall'inizio; `seq` serve per ricollegarsi (`Last-Event-ID`).

| `kind` | Quando | `data` |
| --- | --- | --- |
| `run_started` | inizio o ripresa | `manual_id`, `version_id`, `mode` (`live`, `replay`, `resume`), `speed`, `pages` |
| `station` | una stazione cambia stato | `station` (`read`, `map`, `extract`, `check`, `merge`, `ask`), `state` (`running`, `done`), `detail` |
| `pages_mapped` | mappa salvata | `pages`: `[{page, label, unsure}]` |
| `units_planned` | unità calcolate | `units`: `[{unit_id, pages, section}]` |
| `unit_extracted` | un'unità letta | `unit_id`, `index`, `total`, `nodes`, `edges` provvisori |
| `relations_checked` | verifica, nuova verifica, recupero | `edges`: `[{id, tier}]`, `removed`: `[id]` |
| `merged` | piano di fusione salvato | `same`: `[[id, id]]`, `unsure` |
| `questions` | un cancello salvato | `gate`, `answered`: `[{question_id, option_id, by}]`, `for_person` |
| `graph_final` | fine | `nodes`, `edges` finali, `merged_into`: `{id_provvisorio: id_finale}` |
| `run_finished` | fine | `status`, `verified`, `doubtful`, `excluded`, `open_questions` |
| `run_failed` | errore | `message` (testo dell'errore, per esempio tetto di spesa superato) |

Stazioni e passi: `read` ← `pdf_read`; `map` ← `map`, `scan`, `gate_map`; `extract` ← `extract`;
`check` ← `check`, `split_recheck`, `navigation`, `action_reduction`; `merge` ← `merge`;
`ask` ← `gate_doubts`, `gate_recovery`, `gate_approval`. «Controlla» si riapre dopo «Unisci»
per la nuova verifica: la UI lo scrive («Controlla: nuova verifica dopo l'unione»).

Esempio di `unit_extracted` (Graco, unità 2):

```json
{"seq": 9, "t": 49.1, "cost_usd": 0.0071, "kind": "unit_extracted",
 "data": {"unit_id": "u002-18c3ef", "index": 2, "total": 2,
  "nodes": [{"id": "v3n_…", "type": "Symptom", "name": "No material output from pump", "pages": [8]}],
  "edges": [{"id": "v3e_…", "type": "MAY_INDICATE", "from": "v3n_…", "to": "v3n_…", "pages": [8]}]}}
```

**Come combaciano gli ID.** Un nodo provvisorio ha ID `node_id(identity(endpoint))` e un arco
provvisorio `v3e_` + hash di (tipo, sorgente, destinazione): sono le stesse formule di `merger.py`,
importate in sola lettura. Quindi un nodo che non viene fuso ha già il suo ID finale. Per i nodi
fusi, `graph_final.merged_into` dice dove confluiscono: la UI li fa confluire nel nodo finale.

## 5. Replay

`backend/ui/replay.py` legge una cartella di esecuzione finita e produce la sequenza di eventi
grezzi, poi la passa a `EventTranslator`.

- **Ordine e tempi.** I file di `state/` si ordinano per data di modifica. Il tempo di ogni
  evento è quella data, relativa alla prima. Se le date mancano o sono incoerenti con
  `report.json` (ordine diverso da quello della pipeline, durata totale oltre il doppio), i tempi
  si ricostruiscono dai secondi per passo di `report.json`.
- **Costo nel tempo.** Si prende l'ID dell'esecuzione dagli archivi `provider_responses/` e si
  cercano le chiamate chiuse nel registro di spesa, con il loro costo e la loro ora. L'indice si
  calcola una volta sola e si salva in `workspace/.cache/`. Se gli archivi mancano, il costo
  totale del rapporto si distribuisce sul tempo e la UI scrive «Costo stimato».
- **Velocità.** 1×, 4× (predefinita), 16×, e «Vai alla fine». Pausa e ripresa.
- **Esecuzioni avviate dalla UI.** Il replay rilegge `events.jsonl` con i suoi tempi.
- **Esecuzioni senza `state/`** (per esempio su un clone senza file locali): niente replay; la
  versione si apre solo come grafo finito e la UI lo dice.

Controllo: per Graco r1 il replay termina con un `graph_final` uguale a nodi e archi di
`graph.json`.

## 6. API

Base `http://127.0.0.1:8765/api`. Solo localhost, nessuna autenticazione.
`version_id` = `<cartella di iterazione>~<ripetizione>`, per esempio `runs_E~v3_r1`.

| Metodo e percorso | Che cosa |
| --- | --- |
| `GET /manuals` | tabella della libreria |
| `GET /manuals/{m}` | scheda del manuale e sue versioni |
| `GET /manuals/{m}/versions/{v}/graph` | `graph.json` (compresso con gzip) |
| `GET /manuals/{m}/versions/{v}/report` | `report.json` |
| `GET /manuals/{m}/versions/{v}/events?speed=4&from=0` | SSE: replay, oppure diretta se l'esecuzione è in corso |
| `GET /manuals/{m}/versions/{v}/questions` | domande aperte per te, risposte date, domande non verificate |
| `POST /manuals/{m}/versions/{v}/questions/{q}/answer` | salva una risposta (su una versione della campagna crea prima la copia) |
| `POST /manuals/{m}/versions/{v}/apply` | riprende l'esecuzione con le risposte |
| `POST /manuals/{m}/versions/{v}/approve` | `{"decision": "approve" \| "reject"}` |
| `GET /manuals/{m}/segments/{segment_id}` | testo, pagina e riquadro di un segmento |
| `GET /manuals/{m}/pages/{n}.png?scale=2` | immagine di una pagina |
| `POST /uploads` | carica un PDF: pagine, dimensione, sha256, eventuale duplicato |
| `POST /manuals` | crea un manuale in `workspace/` da un caricamento e dai campi |
| `POST /manuals/{m}/runs` | avvia un'esecuzione reale |
| `POST /manuals/{m}/versions/{v}/stop` | ferma l'esecuzione; lo stato resta e si può riprendere |
| `GET /jobs/active` | l'esecuzione reale in corso, se c'è |
| `GET /budget` | spesa dal registro e tetto |
| `GET /estimate?pages=18` | stima di tempo e costo |

Esempi di risposta (valori da `campaign/`):

```json
// GET /manuals
[{"id": "graco_gtx_2000ex", "origin": "campaign",
  "machine": {"name": "Graco GTX 2000EX texture sprayer", "brand": "Graco", "model": "GTX 2000EX", "type": "texture sprayer"},
  "pages": 18,
  "latest": {"version_id": "runs~v3_r1", "label": "attuale r1", "date": "2026-09-28T19:45:28+02:00",
             "verified": 62, "open_questions": 0, "status": "approved"}}]
```

```json
// GET /manuals/graco_gtx_2000ex
{"id": "graco_gtx_2000ex", "machine": {}, "pages": 18, "origin": "campaign",
 "versions": [{"version_id": "runs~v3_r1", "iteration": "attuale", "repetition": 1,
   "date": "2026-09-28T19:45:28+02:00", "commit": "3ed84f5", "verified": 62, "doubtful": 0,
   "excluded": 12, "open_questions": 0, "status": "approved", "cost_usd": 0.0201,
   "seconds": 137.8, "replay": true}]}
```

```json
// GET /manuals/lg_lmh2235st/versions/runs~v3_r1/questions
{"budget": 10, "editable": false, "copy_needed": true,
 "open": [{"question_id": "rel:u005-43f0c6:B.R12", "kind": "relation_check",
   "title_it": "Il manuale dice questo?",
   "source": [{"segment_id": "p19.b1", "page": 19, "text": "After power on, does the product operate?"}],
   "claims_it": ["Se succede «Product does not operate after power on», una causa possibile è «High-voltage diode resistance out of range» (nome non scritto nel manuale). Vale se: The high-voltage diode resistance is out of range."],
   "proposal": ["1. Symptom 'Product does not operate after power on' -> MAY_INDICATE -> …"],
   "options": [{"option_id": "accept", "label_it": "Sì, è giusto"},
               {"option_id": "correct", "label_it": "Solo in parte"},
               {"option_id": "reject", "label_it": "No"}]}],
 "answered": [], "unverified": 0}
```

```json
// POST …/questions/rel:u005-43f0c6:B.R12/answer
{"option_id": "correct", "keep": [1]}
// → 200 {"version_id": "risposte-1~v3_r1", "answered": 1, "open": 9}
// → 422 {"detail": "option 'correct' needs a correction"}   (da validate_answer)
```

```json
// GET /budget
{"committed_usd": 12.8114, "ceiling_usd": 15.0, "budget_usd": 20.0, "ui_limit_usd": 0.5, "ui_spent_usd": 0.0}
```

```json
// GET /estimate?pages=18
{"seconds": [138, 237], "cost_usd": [0.020, 0.060], "based_on": ["graco_gtx_2000ex", "grundfos_paco_vl"],
 "note": "stima dalle due esecuzioni attuali con numero di pagine più vicino"}
```

La stima somma il costo dell'estrazione e quello dell'agente (`usage` + `agent_usage`).

## 7. Domande, risposte, approvazione

### 7.1 Quali domande

Per una versione si ricostruiscono dai file `state/gate_*.json`, come fa `_result`: domande in
sospeso, in ordine di priorità, fino al budget di 10. Il resto sono domande «non verificate»,
visibili in sola lettura.

Test: per LG r1 le domande scelte, stampate con `render_question`, coincidono con
`questions_for_people.txt`.

### 7.2 Frasi per una persona

Le frasi si costruiscono dai dati dell'asserzione (tipo, estremi, nome scritto o no, tipo di
azione, condizioni), letti dai file di stato. Nessun LLM.

| Relazione | Frase |
| --- | --- |
| `MAY_INDICATE` | Se succede «S», una causa possibile è «F». |
| `INDICATES` | Il codice «E» indica «F». |
| `RESOLVED_BY` | Se la causa è «F», si interviene con «A» (un controllo / una riparazione / rivolgersi all'assistenza). |
| `AFFECTS` | La causa «F» riguarda il componente «C». |

Aggiunte:

- a un nome non scritto nel manuale si aggiunge «(nome non scritto nel manuale)»;
- le condizioni si aggiungono come «Vale se:», «Prima:», «Attenzione:», «Risultato atteso:» o
  «Ordine:», seguite dal testo originale.

Altri tipi di domanda:

- `merge_check`: «Sono la stessa cosa: «X» e «Y»?», con i pulsanti «Sì, la stessa» e «No, diverse».
- `unreadable_page`: «La pagina N non si legge: la saltiamo?», con «Sì, saltala» e «La trascrivo»
  (campo di testo).
- La domanda sulla mappa non arriva alle persone, perché nella UI la mappa la conferma sempre l'agente.

### 7.3 Risposte e ripresa

- `FileQuestionStore` implementa il protocollo `QuestionStore` di `reviewers.py` e salva in
  `<esecuzione>/people.json`. Pubblica al massimo 10 domande per esecuzione, contate su tutte le
  riprese (problema B). Ignora la domanda di approvazione.
- Ogni risposta passa da `Answer` e `validate_answer`. «Solo in parte» diventa
  `option_id="correct"` con `edits={"keep": [1, 3]}`, come le risposte dell'agente.
- «Applica le risposte» è attivo quando tutte le domande pubblicate hanno una risposta. Riprende
  l'esecuzione (stesso comando, stessa cartella). Lo stato salvato evita le chiamate già fatte;
  per sicurezza la ripresa gira con il tetto al valore speso più 0,05 USD, e la UI mostra le
  chiamate fatte.
- **Copia di una versione della campagna.** Alla prima risposta si copia la versione (`state/`,
  `graph.json`, `report.json`) in `workspace/<manuale>/runs/risposte-<n>~v3_rN/`, con `origin.json`
  che dice da dove viene. Prima di copiarla si controlla che il codice attuale produca le stesse
  unità di lettura salvate in `units.json`. Se non le produce, la ripresa rifarebbe l'estrazione
  e pagherebbe: la UI rifiuta con «Questa versione è stata prodotta da un codice diverso: per
  rispondere serve una nuova esecuzione». Il rapporto della copia registra entrambi i commit.
  Una copia non è un risultato della campagna e non va nel paper.

### 7.4 Approvazione

Decisione (Fabio, 29 settembre 2026): **il grafo si approva solo dopo le risposte**. L'ordine è:

1. l'esecuzione finisce e il grafo resta «Da approvare», mai approvato in automatico;
2. Fabio risponde alle domande (al massimo 10);
3. «Applica le risposte»: il grafo si aggiorna, senza chiamate;
4. solo ora «Approva» è attivo. Finché restano domande aperte, al suo posto c'è
   «Rispondi prima alle N domande».

Le domande oltre il budget non bloccano: restano «non verificate». In «Solo agente» non ci sono
domande per la persona, quindi «Approva» è subito attivo. L'API rifiuta l'approvazione (409) se
ci sono domande aperte o risposte non ancora applicate.

Le esecuzioni della UI usano `approval: []`. Il pulsante aggiunge una risposta umana
(`ReviewerKind.HUMAN`, convalidata con `validate_answer`) al registro `state/gate_approval.json`
e riprende l'esecuzione. La ripresa non fa chiamate: rigenera stato, `report.json` e `graph.json`.

Se le risposte cambiano il grafo, l'ID della domanda di approvazione cambia (dipende dal
riepilogo) e serve una nuova approvazione, come prevede la pipeline.

### 7.5 Chi risponde ai dubbi: i preset

| Scelta nella UI | Preset CLI | `map` | `doubts` | `approval` |
| --- | --- | --- | --- | --- |
| Solo agente | `ui-agent` | agent | agent | nessuno (pulsante) |
| Agente, poi io | `ui-interactive` | agent | agent, human | nessuno (pulsante) |
| Solo io | `ui-human` | agent | human | nessuno (pulsante) |

## 8. Dati

```text
campaign/<m>/info.yaml, manual.pdf, manual.json, runs*/v3_rN/…   (sola lettura)
workspace/                                                       (ignorata da git)
  .cache/                         indice dei costi del replay, immagini delle pagine
  uploads/<sha256>.pdf            PDF caricati, in attesa dei campi
  <m>/info.yaml                   stesso formato della campagna (solo per manuali nuovi)
  <m>/manual.pdf                  (solo per manuali nuovi)
  <m>/runs/v3_rN/                 esecuzioni della UI: state/, events.jsonl, people.json, job.json,
                                  graph.json, report.json, provider_responses/
  <m>/runs/risposte-<n>~v3_rN/    copie di versioni della campagna, con origin.json
```

Regole del catalogo:

- **Manuali:** una cartella con `info.yaml` in `campaign/` o in `workspace/`; se lo stesso ID è in
  entrambe, le versioni si uniscono.
- **Pagine:** da `manual.json`, altrimenti da `report.json`.
- **Versioni:** `runs*/v3_rN` con `report.json` o almeno `state/`. Si escludono `v22` e
  `results/`.
- **Iterazione:** il nome della cartella senza `runs_` (`runs` diventa «attuale»). Esempi:
  `runs_F_budget_failed` diventa «F budget failed», `runs_first_contact` diventa «first contact».
- **Data:** l'ultima risposta registrata nei cancelli; se manca, la data di modifica di
  `report.json`.
- **Esito:** `approved` Approvato, `awaiting_approval` Da approvare, `incomplete` Incompleto,
  `rejected` Rifiutato, nessun rapporto Non riuscita, `events.jsonl` senza fine In corso.
- **Stato del manuale** in libreria = esito della versione più recente. Il filtro «Da rivedere»
  prende le versioni da approvare o con domande aperte; «Approvati» le versioni approvate.

## 9. Frontend

### 9.1 Cartelle

```text
frontend/
  index.html  package.json  tsconfig.json  vite.config.ts   (proxy /api → 127.0.0.1:8765)
  src/
    main.tsx  App.tsx                 rotte
    styles/tokens.css                 tutti i valori di DESIGN.md come variabili CSS
    styles/base.css                   reset, font, focus, riduzione di movimento e trasparenza
    text/it.ts                        tutte le stringhe, nomi di tipi, relazioni, stazioni, esiti
    api/types.ts  api/client.ts       tipi delle risposte e funzioni fetch
    live/events.ts                    tipi degli eventi UI
    live/reducer.ts                   stato dell'esecuzione costruito dagli eventi
    live/useRunStream.ts              EventSource, ricollegamento con Last-Event-ID
    graph/Graph3D.tsx                 involucro di 3d-force-graph, aggiornamenti incrementali
    graph/style.ts                    colori e raggi per tipo, resa degli archi per stato
    components/                       TopBar, Button, SegmentedControl, Field, Table, Panel,
                                      List, ProgressBar, Icon, PageImage, Legend
    screens/                          Library, Manual, NewGraph, LiveRun, Questions, FinishedGraph
  tests/                              reducer.test.ts, it.test.ts, Library.test.tsx
```

### 9.2 Rotte

| Rotta | Schermata |
| --- | --- |
| `/` | Libreria |
| `/manuali/:m` | Manuale e versioni |
| `/nuovo` | Nuovo grafo |
| `/manuali/:m/versioni/:v/esecuzione` | Esecuzione dal vivo o replay |
| `/manuali/:m/versioni/:v/domande` | Domande per te |
| `/manuali/:m/versioni/:v` | Grafo finito |

### 9.3 Stato

- Dati del server: un piccolo hook `useApi(url)` con cache per URL e ricarica esplicita, senza
  librerie di stato.
- Esecuzione: `useReducer(runReducer)` alimentato da `useRunStream`. Lo stato contiene stazioni,
  nodi e archi provvisori, relazioni recenti (ultime 200), contatori, costo, domande per te.
  Il reducer è una funzione pura, testata con sequenze di eventi registrate.
- Grafo 3D: un'istanza sola creata una volta. Gli aggiornamenti aggiungono o cambiano oggetti
  senza ricrearli, così i nodi non saltano. Gli archi tratteggiati usano un materiale lineare
  tratteggiato di three.js. Al primo tocco della scena la simulazione fisica si ferma.

### 9.4 Dipendenze

- Runtime: `react`, `react-dom`, `react-router-dom`, `3d-force-graph`, `three`.
- Sviluppo: `vite`, `@vitejs/plugin-react`, `typescript`, `vitest`, `@testing-library/react`, `jsdom`.
- Niente librerie di componenti né framework CSS: i valori di DESIGN.md bastano.
- Le icone sono sei tracciati Lucide copiati in un file.

### 9.5 Un comando

`scripts/ui.py`:

1. se manca `frontend/node_modules` esegue `npm ci`;
2. se `frontend/dist` è più vecchio dei sorgenti esegue `npm run build`;
3. avvia uvicorn su `127.0.0.1:8765`, che serve API e app.

`--dev` avvia invece Vite con ricarica automatica accanto a uvicorn.

## 10. Test

| Test | Che cosa prova |
| --- | --- |
| `test_ui_hook.py` | risultato, stato e grafo identici con e senza hook; un hook che fallisce non ferma l'esecuzione; un evento `extract_` per unità |
| `test_ui_events.py` | traduzione degli eventi del fornitore finto; ID provvisori uguali ai finali per i nodi non fusi; `merged_into` corretto |
| `test_ui_replay.py` | replay di un'esecuzione finta: `graph_final` uguale a `graph.json`; tempi crescenti; velocità; ricostruzione dei tempi senza date; su Graco r1 se `state/` c'è, altrimenti saltato |
| `test_ui_catalog.py` | albero finto di campagna e workspace: etichette, `v22` esclusa, esiti, unione per ID |
| `test_ui_questions.py` | selezione uguale a `questions_for_people.txt` (LG r1, saltato se manca); una frase per ciascuno dei quattro tipi; condizioni e nomi non scritti |
| `test_ui_store.py` | persistenza; budget di 10 su più riprese; `validate_answer` applicato |
| `test_ui_jobs.py` | copia di una versione con controllo delle unità; approvazione scritta nel registro del cancello; ripresa con fornitore che fallisce se chiamato, cioè zero chiamate |
| `test_ui_api.py` | `TestClient`: libreria, dettaglio, grafo, domande, risposta valida e non valida (422), SSE di replay con i primi eventi, caricamento di un file non PDF rifiutato, avvio rifiutato oltre il tetto |
| frontend (vitest) | reducer su una sequenza registrata; frasi e formati italiani (numeri, date); la Libreria mostra una riga per manuale |

Prima di ogni commit: `ruff check .`, `pytest`, e per il frontend `npm test` e `npm run build`.

## 11. Fasi

Ogni fase finisce con test verdi, un commit piccolo, e un messaggio a Fabio che dice che cosa
funziona. Le fasi dalla 3 in poi includono gli screenshot controllati con DESIGN.md, sezione 10.

| Fase | Contenuto | Fatta quando |
| --- | --- | --- |
| **1. Eventi e replay** | hook in `run.py`; `events.py`, `replay.py`; opzioni del CLI | test dell'hook verdi (risultati identici); il replay di Graco r1 dà un `graph_final` uguale a `graph.json`; test della campagna invariati |
| **2. API e SSE** | `catalog`, `questions` (lettura), `evidence`, `budget`, `api`; `scripts/ui.py` | `test_ui_api.py` verde; `curl` sul flusso SSE mostra gli eventi di un replay; `/budget` legge il registro senza scriverlo |
| **3. Libreria e grafo finito** | Libreria, Manuale, Grafo finito con prove, pagine e ricerca | gli 8 manuali in tabella con numeri uguali ai `report.json`; clic su un arco, prove con immagine della pagina e riquadro; screenshot conformi |
| **4. Esecuzione dal vivo** | replay di LG a 4×, poi Nuovo grafo e **una** esecuzione reale su Graco in modalità «Solo io» | replay completo e fluido; l'esecuzione reale finisce, spende al massimo 0,5 USD (previsti circa 0,02), `events.jsonl` salvato e rigiocabile; screenshot conformi |
| **5. Domande e approvazione** | correzione A in `run.py` (commit a parte, con test); Domande per te, store, ripresa, copia, approvazione | test: una risposta della persona non viene mai cambiata dall'agente, e con `--gates agent` i grafi salvati di due manuali restano identici; rispondo alle domande dell'esecuzione Graco; dopo «Applica» gli archi cambiano come risposto, con zero chiamate; «Approva» attivo solo dopo le risposte e porta l'esito ad Approvato; lo stesso su una copia di LG r1 |
| **6. Rifinitura** | accessibilità, stati vuoti ed errori, movimento e trasparenza ridotti, README | tastiera su tutte le schermate; contrasto controllato; controllo di DESIGN.md superato su tutte le schermate a 1440 e a 1280 |

## 12. Spesa

- Registro `campaign/real_call_budget.jsonl`: circa 12,81 USD spesi su 20. Tetto `--spend-ceiling 15.0`.
- Chiamate reali previste in tutto il lavoro:
  - una esecuzione su Graco in «Solo io»: circa 0,02 USD. L'esecuzione F costava 0,020 USD di
    estrazione più 0,004 USD di agente (13 risposte); in «Solo io» l'agente risponde solo alla
    domanda sulla mappa;
  - le riprese dopo le risposte: zero chiamate, con tetto stretto (speso più 0,05 USD).
- Il server rifiuta l'avvio se la stima massima porta la spesa oltre il tetto, o se la spesa
  della UI supera 0,5 USD. Tutto il resto dello sviluppo gira in replay.

## 13. Fuori da questo prototipo

- Confronto tra due versioni dello stesso manuale.
- Modifica del grafo a mano, oltre le risposte alle domande.
- Revisione della mappa da parte di una persona.
- Più utenti, autenticazione, messa in rete.

## 14. Rischi

| Rischio | Contromisura |
| --- | --- |
| Grafi grandi (LG: 330 nodi, 372 archi) lenti nel 3D | una sola istanza, aggiornamenti incrementali, simulazione fermata dopo l'assestamento; prova su LG e ABB in fase 3 |
| Date dei file di stato alterate da copie | ricostruzione dei tempi da `report.json` (sezione 5) |
| Registro di spesa grande (34 MB) | indice per esecuzione calcolato una volta e messo in cache |
| Copie di versioni vecchie con il codice nuovo | controllo delle unità prima di copiare; commit di entrambi nel rapporto; mai usate come risultati |
| Lettura del PDF lenta (LG circa 7 s) per le prove | testo dei segmenti in cache per manuale; le prove degli archi arrivano già da `graph.json` |
