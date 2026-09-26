# Implementazione e verifica della pipeline diagnostica

Stato: primo ciclo tecnico implementato e verificato; obiettivo complessivo di
qualità non ancora raggiunto. Autorizzazione: nuovo cap cumulativo di 20 USD.
Baseline: `528f0690c8a678dd94fe0e5e385203e4f0d0fbe7`. Versione finale del
generatore: `pdf-g3-structured-recovery-v17`, congelata in `source_c6.tar.gz`.
Questo rapporto riguarda sviluppo sui quattro manuali già esaminati, non un test
blind e non una validazione industriale.

## Esito

Il percorso conserva ora risposte originali e usage prima del parsing, recupera
record individuali, preserva meglio celle, rami, ispezioni e condizioni, e rende
più severi i controlli sui collegamenti. Sono state corrette anche perdite
successive alla compilazione che i soli test dell'estrattore non rilevavano.
I risultati documentali migliorano nettamente su Danfoss e Graco secondo il
probe storico. Eastman resta variabile; Hypertherm presenta una riduzione dei
rami autonomi e un carico di revisione ancora eccessivo. Non è corretto
dichiarare risolta l'estrazione diagnostica.

L'ontologia `ontology_schema.JSON` e il gold storico sono invariati, verificati
tramite hash. Preservati anche i due documenti locali dell'utente. Le condizioni
e le ispezioni sono metadati diagnostici tipizzati collegati ai rami; non sono
nuovi tipi ontologici o riparazioni inventate. I grafi prodotti restano bozze:
nessuno dei quattro soddisfa il gate di approvazione.

## Interventi effettivamente implementati

| Problema | Intervento e moduli | Verifica / limite |
|---|---|---|
| Risposte perse durante parsing, usage incompleto | `llm_gateway.py`, nuovo `llm_response_archive.py`: richiesta archiviata prima della chiamata, risposta/usage prima del parsing, errori e identificativi conservati | Trace disponibili per i nuovi tentativi; un errore di connessione senza risposta resta esplicitamente senza usage, contabilizzato al massimo prenotato |
| Un record invalido annulla i validi | Nuovo `diagnostic_response_parsing.py`, `ontology_pipeline.py`: validazione dell'envelope e di ogni record separatamente | Test con record invalidi e validi insieme; osservato recupero dei fratelli validi nel pacchetto Hypertherm |
| Output troncato, retry inefficace | Budget diagnostico 24k, nuovo `diagnostic_recovery.py`, workflow con retry di errori transitori e recupero limitato a pagine/finestre interessate | Nessuna accettazione di JSON troncato; massimo di tentativi e riserve conteggiati; riparazione mirata di tutti gli errori semantici ancora incompleta |
| Perdita del contesto di tabella o procedura | Adapter PDF con geometria/celle/intestazioni, inventario indipendente di finestre, contesto ibrido strutturale e semantico, overlap controllato | Test di righe, intestazioni e continuazioni; non presume che ogni paragrafo sia un ramo atomico |
| Citazioni vere associate al ramo sbagliato | Alias brevi reversibili degli anchor; binding deterministico solo per occorrenza univoca e contenuto consentito; prove per gli estremi delle relazioni | Test positivi e negativi tra celle/righe; non usa fuzzy matching per rendere valida una citazione sbagliata |
| Ispezioni convertite in sintomi/azioni | Compiler distingue imperativi di verifica, ispezioni e rimedi; conserva passi e condizioni nel record validato | Le ispezioni rimangono consultabili; diminuisce l'output Eastman quando un controllo era trattato come rimedio |
| Duplicati dello stesso ramo | Nuovo `diagnostic_reconciliation.py`: riconcilia solo stessa occorrenza e asserzioni normalizzate concordanti | Nessuna fusione tra condizioni, codici, ordine o componenti incompatibili; rimangono varianti non riconciliabili automaticamente |
| Rami compilati persi durante normalizzazione | `ontology_pipeline_coercion._relation_exists` include `branch_lineage_id` | Replay C2→C3: Graco passa da 20 a 22 rami nel grafo, senza nuovo campionamento LLM; zero rami compilati pubblicabili persi nei quattro replay finali |
| Citazioni dello stesso anchor sovrascritte nell'export | `PdfSourceSubgraphBuilder._to_revision` conserva `(evidence_id, quote)` e respinge la relazione se manca una prova richiesta | Test multipli span sul medesimo blocco e riferimento invalido tra riferimenti validi |
| UI ricostruisce false catene attorno a un guasto condiviso | `frontend/app/detail.js`, `graph.js`: raggruppamento per ramo, condizioni collegate al passo, ispezioni visibili | Test JavaScript e rendering locale con due rami, due azioni distinte e una condizione; screenshot `analysis/ui_branches.png` |
| Revisione inutile di una cella che dichiara soltanto controlli | Gap informativo solo per cella atomica di rimedio interamente verificata, composta da ispezioni, senza istruzioni riparative | Un elemento in meno nella coda Danfoss e uno Graco; casi parziali, misti e ambigui restano in revisione |
| “Completezza” confonde accounting e qualità | C6 distingue copertura input, elaborazione del contratto, record pendenti e completezza semantica non validata | Tutti i quattro replay dichiarano correttamente estrazione incompleta; nessun punteggio favorevole ottenuto respingendo tutto |

Il contesto semantico ampio di v12 resta utile per collegamenti e continuazioni.
Le finestre strutturali vengono usate per righe riconoscibili, senza ridurre
l'intero manuale all'inventario euristico. Non è un ritorno indiscriminato a v11.
Il generatore non importa gold, scorer o regole per nomi di questi manuali.

## Esperimenti e provenienza

`baseline_manifest.json` conserva stato Git iniziale, hash e versioni.
`baseline_source.tar.gz` congela il codice originale. Le varianti P1/C1/C2 e
C3–C6 hanno archivi separati. Ogni run conserva profilo, configurazione,
generazione, grafo, timing, log e, per i nuovi percorsi, scambi provider.

- **B1:** una nuova esecuzione completa per manuale con codice baseline,
  GPT-6 Luna, reasoning low, 8k, escalation disabilitata.
- **P1:** quattro pacchetti sorgente, quattro profili ciascuno, una replica:
  Luna low/8k, low/24k, none/24k e Sol medium/24k. Stesso codice P1 e stesse
  pagine entro ciascun confronto. È un confronto preliminare di 16 run utili.
- **C1:** quattro manuali completi dopo il primo incremento, fino a due manuali
  contemporaneamente. Hypertherm subisce numerosi errori di connessione.
- **C2:** quattro manuali completi, in sequenza, Luna low/24k e escalation
  disabilitata, con codice congelato prima della campagna.
- **C3–C6:** replay offline delle richieste esatte C2, attraverso il generatore
  congelato di ciascuna variante. Nessun accesso alla rete, nessuna nuova
  chiamata API, nessuno scambio inutilizzato nei quattro replay finali.
  Isolano correzioni successive di compilazione/export/gate/metriche.

I replay non sono repliche LLM indipendenti né nuove misure di tempo end-to-end.
La baseline non viene modificata per aggiungere retroattivamente l'archivio
raw: dispone del ledger della campagna, non dello stesso replay completo.
Tre avvii locali falliti prima delle API sono conservati con costo zero.
Le differenze B1→C2 cambiano più fattori e non attribuiscono causalmente il
risultato al solo modello o al solo budget di token.

La matrice più ampia proposta nel piano non è completata: mancano repliche
sistematiche e confronto decisivo su gold tecnico. Il residuo economico non
è il vincolo attuale; ripetere molte chiamate prima di risolvere criteri
semantici e copertura del gold non dimostrerebbe il raggiungimento dell'obiettivo.

## Risultati sui quattro manuali

I valori “autonomi” seguenti sono il **probe lessicale storico con soglia 0,55**,
non recall o precisione semantici validati. Anche il probe uno-a-uno con pagina
e ramo restituisce gli stessi conteggi finali, ma non risolve la semantica.

| Manuale | B1: autonomi storici | Finale C6: autonomi storici | Gap storici riconosciuti C6 | Rami nel grafo B1→C6 | Review B1→C6 | Nodi/relazioni C6 |
|---|---:|---:|---:|---:|---:|---:|
| Eastman E-554 | 5/8 | 4/8 | 0 | 11→9 | 54→80 | 153/157 |
| Danfoss APF | 0/8 | 5/8 | 3 | 0→5 | 24→28 | 40/43 |
| Graco Check-Mate 200 | 0/18 | 17/18 | 1 | 0→22 | 16→39 | 86/88 |
| Hypertherm Powermax30 AIR | assente | assente | non valutabile | 25→10 | 89→117 | 139/139 |

Il pilot precedente riportava 3/34 autonomi, la nuova B1 5/34, C1 27/34 e
il finale C6 26/34. Questa variabilità impedisce di scegliere il risultato
migliore come prestazione rappresentativa. I 26 casi sono conteggi su un gold
storico parziale e contestabile, non una certificazione di 26 catene corrette.

Il controllo canonico finale verifica 4.309 riferimenti a evidenze (620 Eastman,
265 Danfoss, 312 Graco, 3.112 Hypertherm): nessun anchor sconosciuto, pagina
incoerente o citazione assente dalla EvidenceUnit per questi riferimenti
pubblicati. Questo prova la corrispondenza letterale e la localizzazione,
non che ogni relazione sia semanticamente sostenuta dall'intero ramo.

Sono conservate nei record validati 80 occorrenze di passi di ispezione e 64
condizioni, incluse quelle dei record da revisionare. Sono occorrenze, non
conteggi deduplicati di conoscenze corrette. Il finale mantiene tutti i rami
pubblicabili compilati; rimangono duplicati/varianti candidati, per esempio
22 rami Graco a fronte di 17 casi storici autonomi. Non vanno confusi con
cinque nuove conoscenze verificate.

`approval_eligible=false` e `diagnostic_extraction_complete=false` in tutti i
grafi. I record pendenti dopo aver distinto i gap sorgente verificati sono
55, 12, 5 e 89 rispettivamente per Eastman, Danfoss, Graco e Hypertherm.
La revisione comprende anche problemi di canonicalizzazione/provenienza e
può avere più elementi per ramo: non è una percentuale di errori semantici.

## Risultati negativi e limiti aperti

Eastman C1 raggiungeva 7/8 nel probe, C2/C6 4/8. Una parte del cambiamento
finale rimuove controlli erroneamente interpretati come azioni: ad esempio
toccare lo schermo per vedere se si accende resta un'ispezione. Restano casi
di calibrazione/procedura senza guasto esplicito e citazioni non correttamente
associate. Il probe lessicale può inoltre non riconoscere parafrasi valide.
Non si modifica il gold per premiare queste predizioni.

Hypertherm è il limite più importante: i 47 motivi di rigetto per supporto
non stabilito degli estremi, 25 per azioni mancanti, 19 per evidenza di
risoluzione mancante e 15 per quote/anchor incoerenti indicano ancora perdita
di rami multipagina. I motivi si sovrappongono, non sono 106 rami distinti.
La diminuzione 25→10 rami rispetto a B1 va considerata una regressione
quantitativa da adjudicare, non automaticamente un miglioramento di precisione.
Non esiste gold tecnico Hypertherm per risolvere questa incertezza.

Il rilevamento di testo corrotto può richiedere OCR, ma in questo ambiente
mancano risorse Tesseract adatte; il diagramma di pagina fisica 228 non è
dimostrato recuperato. Non è stata implementata una comprensione visuale
generale dei diagrammi. Il recupero dei rinvii multipagina e degli errori
semantici di compilazione non copre ancora tutti i casi.

Il modello più capace e il reasoning disabilitato non migliorano uniformemente
i quattro pacchetti. Per esempio, Sol rende più conservativa la disposizione
Danfoss e non supera Luna low/24k sul pacchetto Graco. L'escalation resta
selettiva e disabilitata nei confronti completi; il suo beneficio non è
dimostrato. Non si aggiungono agenti o chiamate sistematiche senza tale prova.

Un vecchio fixture Eastman che attendeva otto pubblicazioni passa ora a otto
review perché non contiene prove sufficienti per i collegamenti sotto i nuovi
controlli. Il test è stato aggiornato per verificare tale rigetto, conservando
gli artifact originali. È un cambiamento di comportamento esplicito, non un
miglioramento della copertura da nascondere nel numero dei test superati.

## Gold, scorer e ruolo umano

Preparati [pacchetti indipendenti per i tecnici](../../evaluation/gold_review_v1/README.md),
senza caricare predizioni: PDF di pagine selezionate, inventario delle fonti,
moduli A/B separati e proposte storiche per l'adjudicator. Hypertherm comprende
37 pagine radice (65–77, 82–104, 228), con 78–81 come contesto. Questo è
materiale per creare il gold; non è gold già annotato o validato.

Il nuovo scorer separa codice/testo, negazione, condizioni, ordine,
ispezioni/azioni, identità dell'occorrenza e scope parziale; usa assegnazione
uno-a-uno ed equivalenze esplicitamente annotate. Rifiuta di produrre metriche
di qualità validata da annotazioni proposte o prive di validatore tecnico.
La corrispondenza esatta resta un limite inferiore, non un giudice semantico.

L'umano interviene in due attività distinte. Prima, per costruire il riferimento
indipendente dai PDF e adjudicare i disaccordi. Nel servizio, dopo estrazione,
controlli e recuperi automatici, decide su ambiguità residue e approvazione
del grafo. Una cella di sola ispezione interamente verificata resta informativa
senza richiedere una riparazione inventata. Approvare il gold non approva il
grafo, e approvare il grafo non valida il gold. L'attuale gate rimane troppo
carico; la riduzione a soli casi utilmente ambigui è un criterio ancora aperto.

## Costi, tempi e verifiche

414 tentativi prenotati e chiusi, nessuna prenotazione pendente e nessun
superamento: **1,261482795 USD prudenziali su 20 USD**. Quota stimabile dai
token osservati: 0,859464170 USD. Per 28 tentativi senza usage osservabile si
mantiene la prenotazione massima. Sono stime, non una fattura del provider.

| Gruppo | USD prudenziali |
|---|---:|
| B1 | 0,151846920 |
| P1, inclusi tentativi locali a costo zero | 0,414525420 |
| C1 | 0,540527185 |
| C2 | 0,154583270 |
| Replay C3–C6 | 0 |

Prezzi e documentazione ufficiale consultata sono in `pricing_source.md`.
Retry, confronti e usage ignoto sono nello stesso `real_call_budget.jsonl`.
Il vecchio cap 15 USD non è stato riutilizzato. Tutti i gruppi restano entro
le allocazioni iniziali; non è stato necessario trasferire sottobudget.

B1 richiede in totale 1.311,563 secondi; C2 1.514,901 secondi, circa 25 minuti
e 15 secondi. C2 per documento: 392,863 / 147,180 / 170,338 / 804,520 secondi
(Eastman/Danfoss/Graco/Hypertherm). I tempi sono monotonic elapsed; C1 ha
concorrenza diversa e gli orologi UTC dell'ambiente hanno mostrato discontinuità.
Singole esecuzioni non stimano stabilmente la velocità o la variabilità.

Verifica finale: **599 test Python superati**, nessun fallimento o skip;
test JavaScript di separazione rami superato; sintassi JS e lint controllati.
UI verificata sul rendering locale dell'ispettore con dati sintetici, non un
test E2E completo dell'app autenticata. Evidenze in `analysis/verification.json`
e `analysis/offline_tests.xml`. La correzione finale del contatore UI è
successiva all'archivio C6 e non cambia il generatore; lo snapshot di consegna
la conserva separatamente. I test provano contratti software, non correttezza
diagnostica sui manuali.

## Pulizia e riproducibilità

Runner, analyzer e replay nuovi sono separati dai runner storici; dipendenza
OpenAI fissata a 2.54.0 perché il parsing strutturato usa helper SDK specifici.
Gli esperimenti usano PyMuPDF 1.27.1, a differenza del runtime locale iniziale.
Database operativi/cache dei run sono ignorati da Git ma conservati localmente;
gli archivi portabili delle evidenze e il manifest consentono di verificarli.
Le risposte raw non sono cancellate. I file privati `.env` non sono inclusi
negli archivi e le credenziali non sono riportate nei trace.

La sola cache legacy `modify/__pycache__` è stata conservata fuori dal percorso
di import in `/tmp/kg-legacy-editor-cache-preserved-20260925`; non conteneva
sorgenti. Nessun artifact sperimentale, gold o PDF storico è stato cancellato.
Il vecchio percorso `/generate`, i moduli monolitici e ulteriore documentazione
storica richiedono refactoring/archiviazione successivi; non sono stati riscritti
insieme alle correzioni per evitare di perdere la tracciabilità degli effetti.

## Stato del piano e prossimo criterio di completamento

| Deliverable | Stato reale | Condizione ancora necessaria |
|---|---|---|
| P0 baseline, trace, budget e replay | Completato per questo ciclo | Mantenere manifest e isolamento delle varianti |
| P1 gold e scorer | Scorer e pacchetti pronti; gold tecnico aperto | Annotazioni indipendenti, correzioni versionate e adjudication |
| P2 parsing e recovery | Implementato e testato per errori strutturali/transitori | Recupero mirato dei rigetti semantici ancora incompleto |
| P3 layout e contesto | Incremento ibrido implementato | Diagrammi/OCR e alcuni rinvii multipagina da risolvere |
| P4 contratto e compilazione | Controlli e metadati implementati | Dimostrare precisione e copertura insieme sui PDF |
| P5 identità, export e revisione | Perdite corrette e UI aggiornata | Duplicati residui e carico umano ancora oltre l'obiettivo |
| P6 confronti controllati | Pilot su pacchetti e replay di ablation eseguiti | Repliche e selezione finale su criteri semantici validati |
| P7 quattro manuali e accettazione | Riesecuzioni complete effettuate | Accettazione documentale non superata |

Le soglie proposte nel piano restano criteri da verificare, non risultati
conseguiti. Prima del confronto decisivo servono tecnici identificati e gold
congelato; prima di chiamare la pipeline pronta servono inoltre recupero dei
rami Hypertherm, stabilità Eastman e riduzione misurata del carico di revisione.
L'autorizzazione all'implementazione e il cap 20 USD restano registrati; questo
rapporto non richiede una nuova approvazione per gli stessi interventi già
autorizzati e non presenta come completate le attività umane mancanti.

Le tabelle complete, disposizioni, witness del probe storico e pacchetti delle
predizioni sono in [analysis/MEASUREMENTS.md](analysis/MEASUREMENTS.md) e
`analysis/results.json`, prodotti da `scripts/analyze_extraction_experiment.py`.
