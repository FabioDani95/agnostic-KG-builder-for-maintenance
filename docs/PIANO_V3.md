# Piano V3: architettura del costruttore di grafi da PDF

Stato: **implementato (2026-09-26)**. Le sei stazioni, i tre cancelli, lo stato
salvato, la CLI e il builder per l'applicazione sono in [backend/kg_v3](../backend/kg_v3/);
`kg_v3.pdf_generator: v3` in `config.yaml` lo rende il generatore PDF del workspace.
Risultati della campagna di valutazione in [campaign/results/REPORT.md](../campaign/results/REPORT.md).
La v22, l'applicazione web e la vecchia interfaccia sono state rimosse il 2026-09-27 (tag `legacy-v22`). Restano: API per rispondere alle domande e nuova interfaccia.

## 1. Perché cambiare

Il modello capisce i manuali; il sistema attuale (v22) butta via il suo lavoro.
Sui quattro manuali di sviluppo, dei 304 record diagnostici non esclusi solo 57
entrano nel grafo; 156 sono bloccati da motivi meccanici e 67 perché il manuale
dice solo una parte della catena ([analisi](../paper/analysis/record_block_causes_20260926.py)).
Le cause principali:

1. il modello deve ricopiare ogni frase carattere per carattere, e un carattere
   sbagliato manda in revisione un record intero;
2. la stessa pagina viene letta fino a 7 volte e le copie generano falsi problemi;
3. il controllore usa parole inglesi fisse, quindi ogni manuale nuovo richiede
   regole nuove;
4. all'umano arrivano log di sistema invece di domande.

La V3 si distacca dalla v22: tiene il codice che funziona (lettura PDF e OCR,
chiamate al modello, archivio, budget, database) e riscrive il resto.

## 2. Sette principi

1. **Il modello capisce, il codice fa i conti.** Il modello scrive nomi brevi con
   parole sue e indica *dove* li ha letti con un ID; ID, prove, conteggi e
   identificativi del grafo li gestisce il codice.
2. **Conta il significato, non i caratteri.** Nessun confronto carattere per
   carattere. Una parafrasi con la stessa logica va bene. Un dettaglio sbagliato
   non butta via un elemento, un'unità o un grafo: si annota e si prosegue.
3. **Ogni parte del manuale si legge in un solo posto:** due letture indipendenti
   della stessa unità, mai letture sovrapposte e casuali.
4. **Nessuna regola di lingua o di produttore.** Decidono la struttura (tabelle,
   righe, blocchi, codici, numeri) e il modello.
5. **Pulito e completo.** I duplicati si fondono da soli; il codice verifica che
   ogni riga delle tabelle diagnostiche sia stata usata o spiegata.
6. **All'umano solo domande chiare con una risposta attesa**, raggruppate per
   ramo e poche. Tutto il resto finisce in un rapporto, non in una coda.
7. **Ogni cancello può essere gestito da una persona, da un agente o da uno
   script**, con lo stesso contratto. Si può lavorare tutto in automatico per test
   ed estrazioni in serie, oppure lasciare alla persona solo i dubbi veri e
   l'approvazione.

## 3. Il percorso

```text
PDF
 1 LEGGI      ogni blocco o riga di tabella riceve un ID corto (p11.t1.r3)     codice
 2 MAPPA      etichetta di ogni pagina, poi unità di lettura                   1 chiamata LLM
              CANCELLO 1  «La mappa è giusta?»            agente e/o persona
 3 ESTRAI     entità e relazioni dell'ontologia, con gli ID dove sono scritte  LLM, 2 letture
 4 CONTROLLA  testimoni: verde / giallo / rosso, più un certificato           codice, LLM sui dubbi
 5 UNISCI     duplicati fusi, nomi puliti, ID di sistema                       codice, LLM sui quasi-duplicati
 6 CHIEDI     CANCELLO 2  domande sui gialli              prima l'agente, poi la persona
              CANCELLO 3  «Il grafo può essere usato?»    persona (agente nei test)
GRAFO         ogni arco: pagina, testo della fonte, semaforo, certificato, chi ha deciso
```

Il flusso è lineare: ogni cancello riceve una risposta sola per esecuzione e non
si torna indietro. Una modifica dopo l'approvazione crea una nuova revisione.

## 4. Le stazioni

### 1. Leggi (`reader.py`, nessun LLM)

Trasforma le `EvidenceUnit` di [pdf.py](../backend/adapters/pdf.py) in segmenti con
ID leggibili: blocco `p38.b4`, frase di un blocco lungo `p38.b4.2`, riga di
tabella `p11.t1.r3`, testo OCR `p7.o1`. Ogni tabella sta nel suo punto della pagina;
ogni cella porta il nome della colonna; le celle unite sono ripetute sulle righe
sotto e marcate come ereditate. Le pagine illeggibili o con testo corrotto passano
dall'OCR esistente e restano marcate.

### 2. Mappa (`mapper.py`, una chiamata LLM)

Un indice compatto per pagina (inizio della pagina, righe brevi come titoli ed
etichette da tutta la pagina, intestazioni di tabella) va al modello, a blocchi di
60 pagine, che etichetta ogni pagina: `diagnostic`, `procedure`, `parts`, `other`;
le pagine senza testo sono `unreadable`. Nel dubbio si include e la pagina resta
incerta. Rete di sicurezza strutturale: una pagina tra due pagine diagnostiche, o
una procedura attaccata a una di esse, si legge comunque. Le unità di lettura sono
pagine diagnostiche consecutive, tabelle intere quando possibile, tagli solo tra
segmenti. Ogni segmento ha una sola unità; i due segmenti precedenti e
l'intestazione di una tabella spezzata sono contesto in sola lettura. Cancello 1:
una domanda `map_review`; se nessuno risponde si usa la mappa del modello.

### 3. Estrai (`extractor.py`)

Lo schema di risposta si genera da [ontology_schema.JSON](../ontology_schema.JSON),
che resta rigida. Per ogni unità il modello restituisce entità (tipo, nome inglese
breve, proprietà dichiarate, ID dove sono scritte), relazioni (tipo, estremi,
record di provenienza, condizioni) e passaggi che non ha capito.

- Controlli e verifiche senza riparazione diventano `CorrectiveAction` con
  `action_kind="inspection"`; «contattare l'assistenza» diventa `action_kind="escalation"`.
  Condizioni e ordine dei passi sono attributi della relazione.
- Due letture indipendenti per unità: l'unione riduce le perdite, l'accordo dà fiducia.
- Tolleranza: un elemento malformato si ripara o si annota, gli altri restano.
  Un ID sbagliato o mancante prende le citazioni del suo record, oppure dell'unità
  con una nota «prova approssimata». Nulla si butta per un dettaglio.
- Risposta troncata: l'unità si divide in due e si ripete. Errore di rete: nuovo
  tentativo con attesa.
- Copertura: se una riga di tabella diagnostica non è usata da nessuna delle due
  letture, una chiamata mirata la rilegge. Ciò che resta va nel rapporto.

### 4. Controlla (`checker.py`)

Ogni relazione cerca testimoni indipendenti:

- **struttura:** i due estremi sono scritti nella stessa riga, nello stesso blocco
  o nello stesso record;
- **accordo:** entrambe le letture la trovano, con lo stesso tipo e citazioni vicine;
- **verificatore:** quando mancano gli altri due, un modello legge solo il testo
  citato e risponde se ne esprime il *significato*, anche con parole diverse.

| Testimoni | Semaforo | Cosa succede |
| --- | --- | --- |
| Due o più | verde | entra nel grafo |
| Uno, oppure testimoni in disaccordo | giallo | diventa una domanda |
| Nessuno | rosso | resta fuori, elencata nel rapporto e recuperabile |

Una conferma o un rifiuto del revisore prevalgono sui testimoni automatici.
La regola è già in `assign_tier`. Codici e numeri nei nomi si confrontano con il
testo citato dopo una normalizzazione (`E-01` = `E01`); una differenza produce una
nota, non uno scarto. Ogni arco riceve un **certificato**: segmenti, testimoni,
verdetto, modello, eventuale decisione e chi l'ha presa.

### 5. Unisci (`merger.py`)

Normalizza maiuscole, punteggiatura, spazi e trattini a capo. Stesso tipo e stesso
nome normalizzato: stesso nodo. I quasi-duplicati vanno a un giudice LLM che li
fonde quando indicano la stessa cosa; codici o numeri diversi non si fondono mai.
Solo i casi davvero incerti diventano una domanda `merge_check`. Gli alias restano
registrati, quindi ogni fusione si può annullare.

Gli ID li assegna il codice; l'identità del ramo è l'occorrenza nella fonte (unità,
record, primo segmento). Le relazioni dell'Asset (`HAS_COMPONENT`, `GENERATES_ERROR`)
sono aggiunte dal codice; i componenti entrano solo se collegati alla diagnostica.
Le proprietà obbligatorie non dichiarate valgono `not_stated`, senza invenzioni né
domande. L'uscita è lo stesso `SourceSubgraphRevision` di oggi, con `attributes`
sulle relazioni per certificato e condizioni, più un export JSON per l'agente a valle.

### 6. Chiedi (`questions.py`)

I gialli dello stesso record diventano **una domanda sola**. Poi i cancelli:

| Tipo | Esempio | Opzioni fisse | Revisore tipico |
| --- | --- | --- | --- |
| `map_review` | «Queste pagine vanno lette come diagnostica: è giusto?» | `confirm`, `correct` con le pagine da cambiare | agente, persona se incerto |
| `relation_check` | «A p. 11 il manuale dice …; il sistema propone …: è corretto?» | `accept`, `reject`, `correct` | agente, persona se incerto |
| `merge_check` | «"Worn seals" e "Seal wear" sono la stessa cosa?» | `same`, `different` | agente |
| `unreadable_page` | «P. 228 è un diagramma illeggibile: la saltiamo o la trascrivi?» | `skip`, `transcribe` | persona |
| `graph_approval` | «Il grafo può essere usato?» con riepilogo | `approve`, `reject` | persona, agente nei test |

Ogni domanda contiene le parole del manuale, la proposta del sistema e l'effetto
di ogni opzione, quindi si risponde senza cercare altrove. Le opzioni sono fisse
per tipo: una risposta si applica allo stesso modo chiunque l'abbia data.
Le persone ricevono al massimo K domande per manuale (15, configurabile); oltre
il budget i gialli restano «non verificati», visibili ma fuori dalla vista affidabile.

## 5. Persona o agente ai cancelli

Già implementato in [reviewers.py](../backend/kg_v3/reviewers.py):

- `HumanReviewer` pubblica le domande e restituisce le risposte date tramite API o UI;
- `AgentReviewer` risponde alle stesse domande con istruzioni proprie
  ([prompts.py](../backend/kg_v3/prompts.py)): vede esattamente il testo che vedrebbe
  una persona (`render_question`), cita i segmenti, motiva, e se non è sicuro passa
  la domanda al revisore successivo; ogni risposta registra modello e hash delle istruzioni;
- `ScriptedReviewer` e `AutoReviewer` rispondono da fixture o con la proposta, per i test;
- `ReviewerChain` prova i revisori in ordine: la persona vede solo ciò che l'agente
  non ha deciso.

Configurazione prevista:

```yaml
kg_v3:
  gates:
    map: [agent]              # oppure [agent, human] o [human]
    doubts: [agent, human]
    approval: [human]         # [agent] per test ed estrazioni in serie
  human_question_budget: 15
  agent_model: gpt-6-luna
  agent_reasoning_effort: medium
  wait_for_map: false         # true: fermarsi finché la mappa non è confermata
  max_units: 150              # oltre, l'esecuzione si ferma con un messaggio chiaro
```

Nell'applicazione `approval: []`: l'approvazione resta al pulsante del workspace.

Con `[agent]` o `[auto]` su tutti i cancelli l'intero percorso gira senza persone:
`scripts/kg_v3.py --pdf <file> --gates agent` produce grafo e rapporto.

## 6. Robustezza

- Stato dell'esecuzione salvato dopo ogni stazione e ogni cancello: dopo un crash si
  riprende dal punto giusto senza ripetere le chiamate già fatte. Gli ID delle unità e
  i salvataggi successivi dipendono dal contenuto: se la mappa cambia, nulla di vecchio
  viene riusato per sbaglio. Un grafo cambiato richiede una nuova approvazione.
- Tetto esplicito di unità per esecuzione (`max_units`); nuovi tentativi automatici
  sugli errori di rete del fornitore.
- Ogni chiamata al modello è archiviata ([llm_response_archive.py](../backend/services/llm_response_archive.py))
  e contabilizzata ([real_call_budget_ledger.py](../backend/services/real_call_budget_ledger.py));
  i test rigiocano le risposte archiviate senza rete.
- Unità elaborate in parallelo con un limite; nessun errore di un'unità ferma le altre.
- Un rapporto per esecuzione: pagine, unità, chiamate, costo, tempo, verdi, gialli
  e rossi, domande e chi ha risposto, righe non usate, pagine non lette.

## 7. Codice

Nuovo pacchetto `backend/kg_v3/`, moduli piccoli e senza framework di orchestrazione:

| Modulo | Compito |
| --- | --- |
| `contracts.py` | tipi condivisi, regola del semaforo, domande e risposte |
| `reviewers.py`, `prompts.py` | revisori intercambiabili e istruzioni dei modelli |
| `reader.py`, `mapper.py`, `extractor.py`, `checker.py`, `merger.py`, `questions.py` | le sei stazioni |
| `ontology.py` | schema di risposta e testo del prompt ricavati da `ontology_schema.JSON` |
| `llm.py` | adattatore unico sul gateway con archivio, budget, nuovi tentativi |
| `run.py` | esecuzione con stato salvato, stazioni e cancelli |
| `export.py` | export JSON per l'agente a valle |

Strumenti:

- [scripts/kg_v3.py](../scripts/kg_v3.py) esegue un PDF da riga di comando;
- [scripts/campaign.py](../scripts/campaign.py) gestisce la campagna di valutazione (gold, esecuzioni,
  KPI, qualità, precisione);
- [scripts/kg_v3_kpi.py](../scripts/kg_v3_kpi.py) e [scripts/kg_v3_evaluate.py](../scripts/kg_v3_evaluate.py)
  confrontano i grafi con il gold per posizione e significato;
- [scripts/kg_v3_quality.py](../scripts/kg_v3_quality.py) misura la pulizia del grafo senza gold;
- [scripts/kg_v3_precision_sheet.py](../scripts/kg_v3_precision_sheet.py) prepara e valuta la
  revisione cieca della precisione.

Un router minimo espone esecuzioni, domande aperte e risposte; una CLI esegue il
percorso da riga di comando. Il builder si sceglie in [source_subgraph_generation.py](../backend/services/source_subgraph_generation.py)
con `pdf_generator: v3`.

**Si riusa**, ripulendo dove serve: adapter PDF e OCR, gateway, archivio, budget,
controllo costi, storage e repository, modelli di workspace, fonti, evidenze e sottografi.

**Si toglie** dopo che la V3 funziona sui quattro manuali di sviluppo, con OK di Fabio
e un tag git `legacy-v22`: il percorso PDF v22 (`pdf_source_subgraph_generation.py`,
`ontology_workflow.py`, `ontology_pipeline*.py`, `diagnostic_*.py`, `cutplan_service.py`,
`scoping_workflow.py`, mining, confidence, completion, style cleanup), la console
precedente e le parti di `agents/`, `graph/` e `runstore/` usate solo da lei.

## 8. Ordine dei lavori

Stato: passi 0–8 fatti, tranne le API per rispondere dall'interfaccia (passo 6); passo 9 aperto.

0. Contratti e revisori con test.
1. Leggi: segmenti corretti sulle pagine note (Graco p. 11, Danfoss p. 64, Eastman
   pp. 37–39) con intestazioni e celle unite.
2. Mappa e cancello 1 con agente reale: Hypertherm pp. 65–77, 82–104 e p. 85 sono
   in mappa; p. 228 è segnalata come illeggibile.
3. Estrai: due letture per unità, nessuna unità persa, replay offline identico.
4. Controlla: citazione vera su riga sbagliata, negazione, codice diverso e
   up-stroke/down-stroke non diventano mai verdi.
5. Unisci ed export: niente duplicati «con e senza punto»; certificati conservati
   nel round-trip; switch `pdf_generator: v3`.
6. Chiedi, cancelli 2 e 3, API minime.
7. Stato salvato, ripresa dopo crash, CLI completamente automatica.
8. Prova sui quattro manuali di sviluppo con revisori agente: ogni riga delle
   tabelle diagnostiche usata o spiegata, domande per la persona entro il budget,
   meno di 10 minuti e 0,25 USD per un manuale di circa 230 pagine. Sono obiettivi,
   non risultati: se mancano si riporta e si analizza senza togliere controlli.
9. Rimozione del codice v22, con OK: fatta il 2026-09-27 (tag `legacy-v22`).

Dopo ogni passo: ruff e test verdi, rapporto breve dei risultati, anche negativi.

## 9. Regole per chi implementa

- Mai scartare per differenze di testo: annotare e proseguire.
- Il modello cita ID; le citazioni testuali le ricava il codice.
- Un segmento ha una sola unità; ogni unità si legge due volte.
- Nessuna regola basata su parole di una lingua o di un produttore per decidere
  cosa è vero.
- All'umano solo `Question` valide; avvisi e conteggi vanno nel rapporto.
- Le stazioni non sanno chi risponde: l'unica differenza è il budget K per le persone.
- Ogni chiamata passa dall'archivio e dal budget; test con `FakeLLM`, `ScriptedReviewer`
  e risposte archiviate.
- Moduli piccoli e leggibili; nessuna nuova dipendenza di orchestrazione.
- Chiedere prima di spendere oltre il budget approvato.

## 10. Fuori da questo piano

- **Interfaccia:** sarà rifatta da zero, lineare, sopra le API dei cancelli.
- **Campagna e confronti per il paper:** dopo che l'architettura funziona.
