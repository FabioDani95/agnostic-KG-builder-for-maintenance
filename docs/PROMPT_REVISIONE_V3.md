# Revisione indipendente della pipeline V3

Sei un ingegnere senior di sistemi LLM e di estrazione della conoscenza da documenti. Devi fare
una **revisione critica** della pipeline in questo repository: trovare bug, punti fragili e
miglioramenti che aumentino davvero la qualità del grafo. **Non modificare il codice**: il tuo
risultato è un rapporto con proposte che verranno valutate e poi implementate in un secondo
momento.

## 1. Cosa fa il sistema

Da un manuale di manutenzione in PDF costruisce un grafo della conoscenza diagnostica: sintomo o
codice di errore → causa → azione correttiva (riparazione, controllo, assistenza) → componente,
secondo l'ontologia fissa `ontology_schema.JSON`. Ogni relazione porta i segmenti del manuale da
cui viene e un certificato (testimoni: struttura della pagina, accordo tra due letture,
verificatore LLM, revisore) che la classifica verde, gialla o rossa. I dubbi diventano domande:
prima risponde un agente, a una persona arriva solo ciò che l'agente non risolve.

Percorso: `backend/kg_v3/` legge (reader) → mappa le pagine (mapper) → estrae con due letture
indipendenti (extractor) → controlla (checker) → unisce (merger) → chiede (questions, reviewers)
→ esporta (export). Orchestrazione con stato salvato in `run.py`. Modello: GPT-6 Luna.

## 2. Gli obiettivi, in ordine di importanza

Giudica tutto rispetto a questi obiettivi, non rispetto a un'estrazione perfetta.

1. **Copertura dell'intero manuale.** Ogni voce diagnostica presente (riga di tabella, codice di
   allarme, problema con i suoi passi) deve diventare un ramo. Nessuna pagina diagnostica persa.
2. **Fedeltà dei rami.** Cause e azioni collegate al problema giusto (non a quello della riga
   accanto), niente cause inventate presentate come scritte; le cause dedotte da un controllo
   sono ammesse solo se marcate `stated_in_source: false`.
3. **Robustezza e stabilità.** Risultati simili tra esecuzioni ripetute e tra produttori diversi;
   nessun singolo punto di rottura che faccia crollare un'esecuzione (è successo: una mappa ha
   tolto un'intera sezione troubleshooting).
4. **Poche domande a una persona.** Al massimo circa 10 per manuale, e solo dubbi veri, con una
   risposta attesa chiara.
5. **Grafo pulito, connesso e navigabile.** Niente doppioni, niente nodi isolati, niente fusioni
   di cose diverse (per esempio "la valvola non si apre" con "non si chiude"), nomi coerenti,
   ogni arco con la sua prova. Deve poter essere usato da un agente di manutenzione a valle.
6. **Costo e tempo ragionevoli** (oggi circa 1–4 centesimi e 1–2 minuti per esecuzione).

**Non sono obiettivi:** la fedeltà carattere per carattere, la formulazione esatta dei nomi, le
avvertenze di stile. Un dettaglio sbagliato non deve mai far buttare via un elemento o un ramo.

## 3. Regole che ogni proposta deve rispettare

- Solo regole **strutturali**, valide per ogni lingua e produttore (tabelle, righe, celle unite,
  passi numerati, codici, numeri). Niente regole scritte per un manuale o per parole inglesi.
- Il modello comprende e cita ID di segmento; il codice fa conti, prove e identificativi.
- Ogni correzione proposta deve avere un test che la dimostra.
- Nessun manuale va usato per "tarare" un numero. Se una proposta nasce dagli errori di un
  manuale specifico, dillo: quel manuale diventa di sviluppo.
- Distingui sempre fatti verificati nel codice o negli artifact da ipotesi.

## 4. Cosa leggere

- `README.md`, `docs/PIANO_V3.md` (architettura e principi), `AGENTS.md`.
- `campaign/results/REPORT.md`: risultati, analisi delle perdite, limiti noti.
- `paper/evaluation/PROTOCOLLO_V3.md`: KPI e regole della valutazione.
- Il codice: `backend/kg_v3/*.py`, `backend/adapters/pdf.py`, `scripts/campaign.py`,
  `scripts/kg_v3_kpi.py`, `scripts/kg_v3_evaluate.py`, `tests/`.
- Gli artifact: per ogni manuale `campaign/<manuale>/gold/` (gold annotato a mano, `TESTO.md` con
  gli ID dei segmenti), `runs/v3_r1..r3/` (ultima versione: `graph.json`, `report.json`,
  `questions_for_people.txt`, `state/` con mappa, letture, controlli e fusioni), `runs_B/`
  (versione precedente), `campaign/results/kpi_B.json` e `kpi_C.json` (prima e dopo le ultime
  correzioni).

## 5. Dove siamo (sei manuali, tre esecuzioni ciascuno)

Rami ritrovati sul gold, per significato: da 682 a **732 su 900 (81%)** dopo l'ultimo giro di
correzioni. Per manuale: Grundfos 140–143/146, Atlas Copco 41–44/49, Graco GTX 17/19, Haas
28–35/45, Lincoln 3–5/22, ABB 4–7/19. La versione precedente del sistema (v22) era al 6%.
Domande a una persona: 0–1 per esecuzione.

Problemi noti, con i dettagli in `REPORT.md`:

- il revisore agente del cancello della mappa può togliere pagine diagnostiche giuste quando solo
  una delle due letture della mappa le ha segnate (Haas r2, pp. 141–142);
- ABB: la diagnostica è sparsa in 406 pagine e la mappa ne trova 3–7 su 11;
- Lincoln: due azioni simili ("contatta l'assistenza" e "se persiste, contatta l'assistenza")
  diventano una sola con condizione; il giudice dei KPI non vede le condizioni;
- i nodi causa sono condivisi tra righe diverse, quindi il rimedio di una riga può comparire sotto
  il sintomo di un'altra;
- il giudice dei KPI è un LLM a tre voti e cambia di 0–4 rami tra una valutazione e l'altra;
- le due letture e il verificatore usano lo stesso modello e possono sbagliare insieme.

## 6. Cosa fare

1. Leggi architettura, rapporto e codice. Ricostruisci il flusso dei dati da PDF a `graph.json`.
2. Cerca **bug** (logica sbagliata, casi limite, stato salvato incoerente in caso di ripresa,
   errori silenziosi, concorrenza, dati persi tra stazioni) e **punti fragili** rispetto agli
   obiettivi della sezione 2.
3. Verifica sugli artifact: prendi rami persi dal gold e seguili stazione per stazione in
   `state/` per capire dove si perdono. Controlla la pulizia dei grafi: doppioni, nodi isolati,
   fusioni sbagliate, archi senza prova.
4. Valuta anche la **misura**: il KPI misura davvero gli obiettivi? Dove è ingiusto, in un senso
   o nell'altro?
5. Puoi eseguire lint e test offline (`.venv/bin/ruff check .`, `.venv/bin/python -m pytest`). Le
   chiamate reali al modello costano e passano da un registro con tetto
   (`campaign/real_call_budget.jsonl`): non farne senza chiedere; se servono, proponi quali e
   con quale costo stimato.
6. Non modificare codice, gold, esecuzioni o documenti.

## 7. Formato del rapporto

1. **Sintesi** in dieci righe: i tre problemi più gravi e le tre proposte con il miglior rapporto
   beneficio/rischio.
2. **Problemi trovati**, dal più grave, ciascuno con: obiettivo colpito (sezione 2), gravità
   (alta, media, bassa), prova (`file:riga` o artifact e ID), scenario concreto di errore, se è un
   fatto verificato o un'ipotesi.
3. **Proposte**, ciascuna con: problema che risolve, soluzione strutturale, test che la dimostra,
   effetto atteso sui KPI (stima dichiarata come tale), costo e rischio (per esempio più domande
   o più chiamate), manuali da cui nasce.
4. **Proposte più ambiziose** (per esempio un secondo testimone indipendente dal modello, una
   lettura dell'immagine della pagina, un controllo di completezza con domande simulate), con i
   precedenti in letteratura che conosci, indicati come da verificare se non sei sicuro.
5. **Cose che non cambieresti** e perché.

Scrivi in italiano, in modo semplice e diretto.
