# Implementazione: robustezza del grafo V3, fasi 1 e 2

Lavora nel repository agnostic-KG-builder-for-maintenance, branch `feat/cite-check-ask-v3`.
Prima leggi: `AGENTS.md`, `README.md`, `docs/PIANO_V3.md`, `campaign/results/REPORT.md`,
`paper/evaluation/PROTOCOLLO_V3.md`, e la revisione indipendente riassunta nella sezione 1.

## 0. Obiettivo

Oggi la pipeline ritrova l'81% dei rami del gold (732/900 su sei manuali, tre esecuzioni), ma una
revisione sui PDF ha mostrato che **alcuni archi verdi cambiano il significato del manuale**. Una
fusione sbagliata è peggio di un ramo mancante, perché un agente a valle la segue. Questo lavoro
non cerca più copertura: deve garantire **l'identità delle cause** e **il contesto delle azioni**,
e deve rendere misurabile la qualità del grafo oltre alla copertura del gold.

Obiettivi del sistema, in ordine: copertura dell'intero manuale; rami fedeli; robustezza tra
esecuzioni e produttori; al massimo circa 10 domande a una persona per manuale; grafo pulito,
connesso e navigabile; costo ragionevole. Non sono obiettivi la formulazione esatta dei nomi né
lo stile: un dettaglio non deve mai far buttare via un elemento.

## 1. Difetti verificati (con le prove)

1. **Fusioni di cause diverse.**
   - Lincoln r1: "Power switch is not ON", "Clogged cable liner or contact tip" e "Spool gun
     switch set to the wrong location" sono un solo nodo
     (`campaign/lincoln_powermig_215mp/runs/v3_r1/graph.json`).
   - Grundfos r3: "total head higher than rated" e "lower than rated" sono un solo nodo, anche se
     il giudice delle fusioni aveva risposto `different` proprio per quelle coppie (vedi
     `runs/v3_r3/state/merge_plan_*.json`).
   - Cause, in `backend/kg_v3/merger.py` (`assemble`) e `backend/kg_v3/checker.py` (`_end_matches`):
     - l'unione (union-find) è transitiva e non rispetta i verdetti `different`: basta un `same`
       sbagliato su una coppia intermedia;
     - le cause dedotte da un controllo (`stated=false` con un nome vero, scelta di Fabio) vengono
       trattate come il segnaposto "Unspecified cause of …": si abbinano a qualunque causa e si
       fondono quando hanno gli stessi rimedi. La propagazione della cella unita dà a molte cause
       lo stesso rimedio, quindi si fondono.
2. **Celle "ereditate" che non sono unite.** ABB p. 232: la riga del LED blu riceve il testo della
   riga del LED rosso (`[p232.t1.r5] column 3 (same as row above)` in
   `campaign/abb_acs580_01/gold/TESTO.md`). `backend/kg_v3/reader.py` (`_table_segments`) eredita
   una cella quando PyMuPDF non le dà un riquadro, e nel PDF la separazione è visibile. Il
   verificatore conferma perché legge lo stesso testo sbagliato.
3. **Contesto delle azioni instabile.**
   - Haas p. 144: "non spegnere il robot durante la sostituzione delle batterie" in r1 si perde,
     in r2 è una condizione, in r3 un'azione separata.
   - Haas p. 160: il risultato atteso di una prova ("suona e il LED diventa rosso") finisce tra le
     condizioni.
   - Graco pp. 8–9: il prerequisito di sezione (scaricare la pressione prima) non arriva ai rami.
4. **Rami non navigabili.** Haas: cause con azioni ma senza nessun problema in ingresso.
5. **Prova "stessa cella" troppo debole.** Atlas Copco p. 43: una cella elenca più cause e più
   rimedi; il rimedio di una voce vicina viene collegato alla causa sbagliata e diventa verde.
6. **Numeri scambiati per codici.** Grundfos r2: 40 nodi `ErrorCode` che sono i numeri delle cause
   della tabella. Il manuale cita una causa 41 che nell'elenco non esiste: va segnalata nel
   rapporto, non inventata.

## 2. Regole

- Solo regole **strutturali**, valide per ogni lingua e produttore. Niente parole di una lingua,
  niente casi scritti per un manuale.
- Il modello comprende e cita ID di segmento; il codice fa conti, prove e identificativi.
- **Un test per ogni correzione**, con un caso che senza la correzione fallisce.
- **Non cambiare gli ID dei segmenti**: i gold dei sei manuali li usano. Se una correzione del
  lettore cambia un ID, fermati e chiedi.
- Non modificare gold (`campaign/*/gold/`), esecuzioni passate, `paper/` salvo `STATUS.md`.
- Non toccare l'interfaccia (non esiste più; verrà rifatta dopo).
- Chiamate reali al modello solo dove indicato, sul registro `campaign/real_call_budget.jsonl`.
  Spesa attuale circa 2,2 USD su 10. **Per tutto questo lavoro al massimo 2 USD**: controlla con
  `.venv/bin/python scripts/campaign.py status` prima e dopo ogni esecuzione, e fermati e chiedi
  se la stima non basta.
- Ruff e pytest verdi prima di ogni commit (`.venv/bin/ruff check .`,
  `.venv/bin/python -m pytest`). Commit piccoli, uno per correzione, messaggi chiari.
- Riporta anche i risultati negativi.

## 3. Fase 1: correzioni

**F1. Nessuna fusione contro un verdetto `different`.** L'unione dei nodi rispetta i vincoli: due
identità giudicate diverse non finiscono mai nello stesso gruppo, nemmeno per transitività. Vale
per tutte le vie di unione in `assemble`: coppie `same` del giudice, alias tra le letture,
segnaposto, rimedi comuni. Se un'unione violerebbe un vincolo, non si fa, e la coppia che l'avrebbe
causata va nel rapporto. Due nomi con numeri diversi restano sempre separati (già in `similarity`;
verifica che valga in ogni via).
*Test:* A~B `same`, B~C `same`, A~C `different` → A e C in nodi diversi.

**F2. Le cause dedotte sono cause con un nome.** Solo il segnaposto "Unspecified cause of …"
(costante `UNSPECIFIED_CAUSE` in `extractor.py`) si abbina a qualunque causa in `_end_matches` e
nella regola dei "partner" di `assemble`. La fusione per rimedi comuni vale solo per segnaposto
della stessa riga o voce di origine. Una causa dedotta si fonde solo come una causa scritta: nome
uguale dopo normalizzazione, oppure verdetto `same` del giudice.
*Test:* le tre cause dedotte di Lincoln della stessa tabella, con gli stessi rimedi ereditati,
restano tre nodi.

**F3. Celle unite confermate dalla geometria.** Una cella si eredita dalla riga sopra solo se nel
PDF non c'è una linea orizzontale che separa le due righe entro l'estensione orizzontale di quella
colonna (linee e rettangoli sottili da `page.get_drawings()`, con una tolleranza di pochi punti).
Il dato va calcolato in `backend/adapters/pdf.py`, dove c'è la pagina, e passato alla riga (per
esempio un flag per colonna); `reader.py` lo usa. Senza la conferma geometrica la cella resta vuota.
Gli ID dei segmenti non cambiano. La propagazione dei rimedi delle celle unite (`checker.py`,
`inherited_cell_proposals`) usa solo celle confermate.
*Test:* una tabella sintetica con celle vuote separate da una linea (non ereditate) e una cella
unita vera (ereditata). Controllo reale: dopo la correzione ABB `p232.t1.r5` non contiene più il
testo del LED rosso, e Lincoln `p28.t1.r4` continua a ereditare la terza colonna.

**F4. Navigabilità.** Dopo l'unione, controlla il grafo:
- ogni causa con azioni ha almeno un problema o codice in ingresso;
- ogni problema o codice raggiunge almeno un'azione.

Un pezzo scollegato viene prima ricollegato quando la struttura lo indica senza dubbi (stessa voce
di origine, stesso passo numerato con il problema che lo introduce, già noto a `DocumentText`).
Altrimenti diventa una domanda raggruppata per voce, entro il budget, o una riga del rapporto.
Riporta in `report.json` i conteggi `orphan_causes` e `problems_without_action`.
*Test:* una causa di una procedura numerata senza il problema viene ricollegata al problema che
introduce la sequenza.

**F5. Contesto tipizzato.** Le condizioni delle relazioni diventano oggetti
`{"kind": ..., "text": ...}` con `kind` in `if` (se, solo quando, soglie),
`prerequisite` (da fare prima), `warning` (avvertenze e divieti durante l'azione), `expected`
(risultato atteso di una prova) e `order` (posizione nella sequenza).
- Aggiorna schema di estrazione e istruzioni (`ontology.py`, `prompts.py`, `extractor.py`),
  `statement()` del checker, export ed evaluator. Mantieni la lettura dei vecchi `graph.json`,
  dove le condizioni sono stringhe (per esempio `kind="if"`).
- Un prerequisito o un'avvertenza scritti in un blocco di sezione che precede la tabella o la
  procedura (contesto di sola lettura dell'unità) va attaccato alle azioni della sezione, citando
  il suo segmento.

*Test:* parsing ed export di ogni tipo; retrocompatibilità; il vincolo "non spegnere" e il
risultato atteso di Haas restano distinti nei dati di prova.

**F6. Prova strutturale nelle celle con elenchi.** Quando una cella contiene più voci (righe,
punti o numeri) e la colonna accanto ha voci allineate, il testimone `structure` vale solo se causa
e rimedio stanno nella stessa posizione dell'elenco. Altrimenti la relazione ha bisogno di un altro
testimone. Non cambiare gli ID: calcola l'allineamento dentro il testo della riga, nel checker.
*Test:* una riga con due cause e due rimedi allineati: le coppie incrociate non ricevono la prova
strutturale.

**F7. Codici solo se il manuale li mostra come codici.** Un numero che indicizza un elenco dello
stesso documento (cause numerate richiamate da una matrice) non è un `ErrorCode`. Regola
strutturale: se il "codice" coincide con il numero di una voce di un elenco numerato citato nella
stessa unità, non si crea un `ErrorCode`, e la relazione si lega alla voce. I riferimenti a voci
inesistenti (causa 41) vanno nel rapporto come `unresolved_references`.
*Test:* matrice sintetica con cause numerate → nessun `ErrorCode`, riferimento mancante riportato.

## 4. Fase 2: misurare la qualità oltre il gold

**M1. `scripts/kg_v3_quality.py`**, senza gold e senza chiamate al modello, per ogni esecuzione e
per manuale:
- `fusion_violations`: nodi che contengono due nomi giudicati `different` o con numeri diversi
  (deve essere 0 dopo F1);
- `orphan_causes`, `problems_without_action`;
- `duplicate_nodes`: stesso tipo, nomi uguali dopo normalizzazione, nodi diversi;
- `edges_without_evidence`;
- `derived_causes`;
- **stabilità**: sovrapposizione (Jaccard) delle relazioni normalizzate tra r1, r2 e r3.

Collegalo a `scripts/campaign.py` come passo `quality`, con uscita in
`campaign/results/quality.json` e `quality.md`.

**M2. Domande contrastive.**
- Da ogni gold ricava in automatico le coppie di voci quasi uguali ma diverse (per esempio due
  cause o due problemi con parole quasi identiche e significato diverso). Salvale in
  `campaign/<manuale>/gold/contrastive.json` perché Fabio possa rivederle.
- Per ogni coppia verifica sul grafo che i due lati siano nodi distinti e che ciascuno porti alle
  proprie azioni (riusa il giudice e i candidati di `kg_v3_evaluate.py`).
- Riporta `contrastive_pairs_kept` / totale nei KPI (`kg_v3_kpi.py`). Queste domande costano
  chiamate al giudice: stimale prima.

**M3. Precisione oltre il gold.** Estendi `scripts/kg_v3_precision_sheet.py` perché il campione
cieco includa anche archi con prove solo su pagine fuori dal perimetro del gold, marcati nella
chiave, non nel foglio. Non sovrascrivere `campaign/results/precision/REVISIONE_PRECISIONE.md`, che
può contenere risposte: scrivi un nuovo foglio `REVISIONE_PRECISIONE_2.md`. Non compilarlo tu.

## 5. Misura prima e dopo

1. Prima di ogni correzione: `campaign.py quality` sulle esecuzioni attuali (`runs/`, che sono il
   "prima"). Nessuna chiamata al modello.
2. Implementa F1–F7 con i test. F1 e F2 si possono verificare **offline** ricostruendo l'unione
   dallo stato salvato (`state/checked_*.json`, `merge_plan_*.json`) delle esecuzioni attuali:
   fallo e riporta quante fusioni sbagliate spariscono prima di spendere.
3. Sposta le esecuzioni attuali in `campaign/<manuale>/runs_C/` (come per `runs_B`) e riesegui i
   sei manuali: `scripts/campaign.py run <id>`, uno alla volta, 3 esecuzioni V3 ciascuno.
4. Poi `campaign.py kpi` (tutti i manuali), `campaign.py quality`, le domande contrastive, e il
   nuovo foglio di precisione.

Criteri di accettazione:
- `fusion_violations` = 0 in tutte le esecuzioni;
- nessun `ErrorCode` fatto di numeri di un elenco;
- cause orfane e problemi senza azione ridotti e riportati;
- domande a una persona ≤ 10 per manuale;
- stabilità riportata;
- recall dei rami non peggiore del "prima" oltre il rumore del giudice (0–4 rami per manuale);
  se peggiora, spiega dove e perché.

## 6. Cosa consegnare

- I commit sul branch, uno per correzione, con ruff e pytest verdi.
- Una sezione nuova in `campaign/results/REPORT.md`: tabella prima e dopo per manuale (rami,
  asserzioni, `fusion_violations`, cause orfane, stabilità, domande a persona, costo), le fusioni
  sbagliate eliminate con esempi, i limiti rimasti e i risultati negativi. Aggiorna
  `paper/STATUS.md` con poche righe.
- In chat, in italiano e in modo semplice: cosa hai fatto, la tabella prima e dopo, cosa resta
  aperto e cosa deve fare Fabio (rivedere `contrastive.json`, compilare i fogli della precisione).
