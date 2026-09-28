# Iterazione F: tappare i limiti emersi su Grizzly e LG

Lavora nel repository agnostic-KG-builder-for-maintenance, branch `feat/cite-check-ask-v3`.
Prima leggi: `AGENTS.md`, `README.md`, `docs/PIANO_V3.md`, `paper/evaluation/PROTOCOLLO_V3.md`
(sezione 1, valutazione a rotazione), `campaign/results/REPORT.md` (sezioni "Secondo primo
contatto: LG", "Primo manuale di test: Grizzly", "Iterazione E").

Sei un ingegnere molto forte di sistemi LLM e di estrazione della conoscenza da PDF. Il tuo compito
è **aumentare davvero la conoscenza estratta** da manuali come Grizzly e LG, trovando le soluzioni
migliori. Quelle suggerite qui sotto sono spunti, non ordini: puoi proporne e implementarne di
migliori. **Puoi aumentare moderatamente costo e tempo per manuale** se la qualità sale in modo
netto: è una scelta accettata, ma va misurata e giustificata.

## 0. Scopo dell'applicativo e perimetro di questo lavoro

L'applicativo ha **un solo scopo**: da un manuale tecnico in PDF produrre un grafo di conoscenza
diagnostica **completo, fedele al manuale, connesso e navigabile**, con prove citate per ogni
arco, a costo e tempo contenuti e con **poche domande a una persona** (al massimo circa 10 per
manuale). Il grafo serve a un agente di manutenzione a valle: deve poter partire da un sintomo o
da un codice e arrivare alle cause, ai controlli e alle azioni giuste, con le loro condizioni.
Conta il significato, non la formulazione esatta dei nomi.

Questo lavoro riguarda **solo la qualità dell'estrazione**. **Non** fare:
- nuove funzioni, API o interfaccia (il frontend verrà dopo, in un altro lavoro);
- cambi dell'ontologia, del modello o del fornitore;
- refactoring non necessari agli obiettivi;
- modifiche ai gold, ai manuali o al protocollo di valutazione;
- nuovi manuali o nuovi tag di congelamento;
- testo del paper (solo poche righe in `paper/STATUS.md`).

Se una soluzione richiede una di queste cose, fermati e proponila a Fabio.

## 1. Cosa fa il sistema

Da un manuale PDF costruisce un grafo di conoscenza diagnostica: sintomo o codice → causa →
azione (riparazione, controllo, assistenza) → componente, con ontologia fissa
(`ontology_schema.JSON`). Stazioni in `backend/kg_v3/`: lettura in segmenti con ID (`reader.py`),
mappa delle pagine diagnostiche (`mapper.py`), due letture di estrazione (`extractor.py`), verifica
con testimoni verde/giallo/rosso (`checker.py`), fusione (`merger.py`), domande a revisore agente o
persona (`questions.py`, `reviewers.py`). Orchestrazione in `run.py`. Modello: GPT-6 Luna, che
**accetta immagini** (verificato: `campaign/results/iteration_E/vision_probe.json`, circa 1.400
token per pagina).

## 2. I limiti misurati (primo contatto, codice del tag `v3-freeze-2026-09-28`)

**Grizzly G0872** (manuale di laser cutter, gold 66 rami): 29–32/62 rami per esecuzione.
- Tabelle di troubleshooting (pp. 51–52): 85–94%. Funziona.
- **Condizioni di guasto sparse** nel resto del manuale (codici macchina a p. 9, allarme del chiller
  a p. 32, amperometro a p. 37, condizioni "se succede X, fai Y" dentro le procedure di
  manutenzione pp. 46–64): 4–5 su 32. Il 58–79% delle perdite cade su **pagine che la mappa non
  sceglie**. La mappa riconosce le sezioni di troubleshooting, non la conoscenza diagnostica sparsa.

**LG LMH2235ST** (service manual di microonde, gold 74 rami): 22–25/74 rami per esecuzione.
- Controlli di base in tabella (p. 13): 5/5. Funziona.
- La mappa legge 21–22 delle 24 pagine gold: **qui il problema non è la mappa**.
- **Diagrammi di flusso** (pp. 14–24, domande sì/no su test di continuità, "No → Replace the fuse",
  "Go to No. N"): 12–13/35. I passi vengono estratti ma **non collegati al sintomo** del diagramma:
  37–50 cause orfane per esecuzione (Grizzly 1–5). Il sintomo che apre il diagramma sta in un
  riquadro o nell'immagine; il testo della pagina arriva spezzato in molti segmenti ("Yes", "No",
  "4", "Replace the").
- **Test dei componenti con valori attesi** (pp. 25–33, per esempio "Primary winding 0.2 ~ 0.5
  Ohm"): 0–4/18.
- Codici d'errore (p. 12): 3/8.

**Limiti già noti sugli altri sei manuali** (`campaign/results/REPORT.md`, iterazione E): ABB,
diagnostica sparsa in 406 pagine con la mappa che ne trova solo una parte; cause orfane in
aumento (35 → 53); costo per esecuzione salito da circa 1,5 a 3–11 centesimi, perché la mappa per
sezioni spezza le tabelle in più unità e le letture ripetute portano tutto il contesto (Lincoln da
82 mila a 1,5 milioni di token).

## 3. Obiettivi

1. **Pagine calde:** trovare tutta la conoscenza diagnostica del manuale, anche sparsa (Grizzly,
   ABB), senza annegare l'estrazione in pagine inutili.
2. **Diagrammi di flusso e bivi:** ogni esito che prescrive un'azione diventa un ramo collegato al
   sintomo del diagramma, con l'esito del test come condizione (LG).
3. **Test con valori attesi:** una prova con un valore atteso è un'azione di controllo collegata al
   problema, con il valore come contesto `expected` e la conseguenza come azione (LG).
4. **Rami connessi:** meno cause orfane, nessuna causa senza problema quando la struttura lo dice.
5. **Senza regressioni:** fusioni vietate a zero, recall sui sei manuali di sviluppo non peggiore
   oltre il rumore del giudice (0–4 rami per manuale), domande a una persona ≤ 10 per manuale.
6. **Costo e tempo:** si possono alzare, ma riportali per manuale e per esecuzione. Riferimento
   accettabile: fino a circa 0,25 USD e 10 minuti per un manuale di 400 pagine. Se ti serve di
   più, motivalo. Correggi anche la regressione di token dell'iterazione E, se puoi.

## 4. Spunti (liberi di migliorarli)

- **Mappa per pagine calde con l'immagine:** oltre al testo, dare al modello l'immagine
  ridotta della pagina (o delle pagine incerte) per riconoscere tabelle diagnostiche, diagrammi,
  riquadri "se… allora…", codici. Unire con la mappa attuale; nel dubbio si include. In
  alternativa o in aggiunta: un recupero tipo ColPali (arXiv 2407.01449) con domande diagnostiche
  fisse sulle immagini delle pagine.
- **Diagrammi → grafo esplicito prima dell'estrazione:** leggere la pagina come immagine insieme ai
  segmenti con le loro coordinate e alle frecce del PDF (`page.get_drawings()`), costruire nodi
  domanda/esito/azione e archi sì/no, e poi estrarre i rami dal grafo. I modelli
  visione-linguaggio tendono a inventare collegamenti nei diagrammi (FlowPathAgent, EMNLP 2025):
  ogni arco deve avere una prova (segmenti o geometria) e passare dal checker.
- **Parser scritti dal modello per strutture ripetitive** (liste di codici, matrici, tabelle
  lunghe): il modello guarda poche righe e scrive una piccola funzione deterministica applicata a
  tutte (come Evaporate, PVLDB 17(2)). Il parser diventa un **testimone indipendente**: oggi i
  testimoni sono tutti lo stesso modello e sbagliano insieme.
- **Ricollegamento strutturale:** collegare cause e azioni al sintomo che introduce il diagramma o
  la procedura (titolo, riquadro iniziale, prima domanda), non solo ai passi numerati.
- **Unità di lettura:** unità per diagramma o procedura intera, contesto senza duplicazioni.

## 5. Regole

- Solo regole **strutturali**, valide per ogni lingua e produttore. Niente parole di una lingua,
  niente casi scritti per un manuale. Il gold serve solo a misurare.
- Il modello comprende e cita ID; il codice fa conti, prove e identificativi. Ogni relazione ha una
  prova citabile e passa dal checker, anche se nasce da un'immagine o da un parser.
- **Gli ID dei segmenti esistenti non devono cambiare**: tutti i gold li usano. Puoi **aggiungere**
  nuovi elementi citabili (per esempio regioni di immagine o nodi di diagramma) con ID nuovi, mai
  rinumerare quelli attuali. Verifica per ogni manuale che `gold/TESTO.md` coincida con il lettore.
- **Non modificare i gold** (`campaign/*/gold/`) né le esecuzioni passate.
- **Un test per ogni correzione**, con un caso che senza la correzione fallisce. Ruff e pytest verdi
  prima di ogni commit (`.venv/bin/ruff check .`, `.venv/bin/python -m pytest`). Commit piccoli.
- Chiamate reali solo dal registro `campaign/real_call_budget.jsonl` (tetto 20 USD; spesa attuale
  circa 7,1). **Tetto di questa iterazione: 5 USD**, cioè fino a circa 12,1 USD cumulativi, compresi
  esecuzioni, giudice ed esperimenti. Usa `--spend-ceiling`. Controlla `scripts/campaign.py status`
  prima e dopo; fermati e chiedi se non basta.
- Non toccare l'interfaccia (non c'è). Riporta anche i risultati negativi.

## 6. Misura

Il gruppo di sviluppo è ora di otto manuali: ABB, Atlas Copco, Graco GTX, Grundfos, Haas, Lincoln,
Grizzly, LG.

1. **Prima:** le esecuzioni attuali in `campaign/<manuale>/runs/` (per Grizzly e LG sono quelle del
   primo contatto). I KPI esistenti sono `campaign/results/kpi_E.json`,
   `kpi_test_grizzly.json` e `kpi_first_contact_lg.json`, con lo stesso valutatore.
2. Dove possibile, verifica **offline** sullo stato salvato prima di spendere.
3. Sposta le esecuzioni attuali in `runs_E/` (per i sei) e `runs_first_contact/` (per Grizzly e LG),
   poi riesegui gli otto manuali, 3 esecuzioni ciascuno, uno alla volta:
   `scripts/campaign.py run <id> --run-prefix campaign_F --spend-ceiling 12.1`.
4. `scripts/campaign.py kpi --v3-only --out campaign/results/kpi_F.json` e
   `scripts/campaign.py quality --out campaign/results/quality_F.json`.
5. Tabella prima e dopo per manuale: rami (r1, r2, r3), asserzioni, pagine gold lette, cause
   orfane, fusioni vietate, domande a persona, **costo e tempo per esecuzione**. Per Grizzly e LG
   aggiungi la scomposizione per zona (tabelle, pagine sparse; diagrammi, test, codici).
6. Se i risultati tengono, proponi a Fabio il nuovo tag di congelamento: il prossimo manuale nuovo
   ne misurerà il primo contatto. **Non** creare il tag senza il suo ok.

## 7. Cosa consegnare

- Commit sul branch, uno per soluzione, con i test.
- Una sezione nuova in `campaign/results/REPORT.md`: cosa hai fatto e perché, tabella prima e dopo,
  costo e tempo, esempi verificati sul PDF di rami recuperati, limiti rimasti, risultati negativi.
  Poche righe in `paper/STATUS.md`.
- In chat, in italiano e in modo semplice: soluzioni adottate, tabella finale, costo e tempo per
  manuale, cosa resta aperto.
