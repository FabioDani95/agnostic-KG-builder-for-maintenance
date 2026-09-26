# Continuazione: tabelle diagnostiche e stato del gold Hypertherm

Autorizzazione invariata: continuazione dell'implementazione, con cap API
cumulativo di 20 USD nello stesso ledger del primo ciclo. Nessun nuovo budget
aggiuntivo. Il rapporto precedente rimane in `../robustness_20260925/REPORT.md`.

## Gold: cosa esiste e cosa manca

Il perimetro Hypertherm è definito: 37 pagine radice (65–77, 82–104, 228),
con 78–81 come contesto. I PDF e i moduli A/B sono disponibili in
`../../evaluation/gold_review_v1/hypertherm_powermax30_air/`.
I moduli sono ancora `unannotated`, con `branches: []`: **non esiste ancora
un gold tecnico validato**. Questo non impedisce le correzioni tecniche e
gli esperimenti di sviluppo; impedisce di attribuire loro precisione/recall
semantici certificati.

In questo incremento sono state aggiunte quattro note sorgente per
l'adjudicator, in `hypertherm_source_notes_for_adjudicator.json`, con 19 span
controllati letteralmente nel testo nativo del PDF. Sono proposte dell'assistente,
che ha già visto predizioni; non sono annotazioni indipendenti, non sono gold
e non vengono usate né dal generatore né dallo scorer. Vanno mostrate dopo
le annotazioni indipendenti dei tecnici. Non sostituiscono l'annotazione
esaustiva delle 37 pagine.

Le note riguardano il filtro ostruito e la sequenza iniziata nella pagina
precedente; le alternative caldo/freddo nella tabella di pagina 67; i tre guasti
possibili dichiarati all'inizio del Test 9; il ramo negativo del passo 13,
che collega le pagine 96 e 97. In quest'ultimo caso il “no” risponde a una
domanda congiunta e non va trasformato automaticamente in due negazioni distinte.

## C7: correggere il riconoscimento delle tabelle

Il confronto con le pagine renderizzate 67 e 69 ha confermato due cause
concrete della perdita di informazioni: il riconoscitore cercava l'intestazione
diagnostica nella prima riga, che contiene invece il titolo/sintomo esteso su
due colonne; inoltre non riconosceva le forme plurali “Possible causes” e
“Possible solutions”. Il successivo compilatore respingeva correttamente
citazioni separate, perché non disponeva della struttura che le collegava.

`diagnostic_record_windowing.py` riconosce ora il titolo come radice solo
quando le coordinate canoniche provano che occupa la larghezza della tabella
e la riga successiva contiene le colonne causa/soluzione. Le intestazioni sono
contesto, non nuove asserzioni. Nessuna regola contiene nomi di manuali,
codici del benchmark o risposte gold.

Gli elenchi puntati di alternative restano `ambiguous_pairing`. Una uguale
quantità di punti nelle due colonne non prova il loro abbinamento. Il compiler
mantiene esplicita questa ambiguità anche se tutte le citazioni sono letterali;
non trasforma la presenza delle parole nella stessa cella in prova della
relazione. La ricostruzione semantica dei rami in tali tabelle resta un limite.

L'analisi offline degli stessi candidati Hypertherm C6 conserva i dieci
pubblicabili e recupera il caso allarme compressore → filtro ostruito →
sostituzione del filtro. Due review diventano gap di sola ispezione; quattordici
gap diventano review perché la struttura contiene alternative non risolte.
Sono cambiamenti di disposizione del compiler, non risultati di una nuova
estrazione o una misura di correttezza semantica. Gli stessi probe sui candidati
Eastman, Danfoss e Graco non cambiano le disposizioni.

C7 è congelata in `source_c7.tar.gz` (`pdf-g3-structured-recovery-v18`).
Un nuovo run reale completo Hypertherm usa questa versione, stesso PDF,
GPT-6 Luna low/24k, escalation disabilitata, ledger cumulativo precedente.
L'ultima baseline completa comparabile è C2; C6 ne è il replay con i controlli
del primo ciclo. Una singola nuova estrazione non isola la variabilità LLM.

## C8: recuperare una citazione con locator locale errato

`ontology_pipeline._rebind_unique_window_spans` può correggere un riferimento
a un anchor noto ma sbagliato soltanto quando la citazione compare una volta
sola tra gli span consentiti della stessa finestra atomica verificata. Il testo
rimane identico; anchor e pagina corretti provengono dall'inventario sorgente.
Non cerca in altre righe, non sposta anchor ignoti o esterni e non interviene
su citazioni ripetute o finestre ambigue. Il compilatore applica successivamente
tutti i controlli canonici. Prima/dopo e campo interessato sono nel report del
chunk `evidence_anchor_rebindings`; la risposta raw resta intatta.

C8 è congelata in `source_c8.tar.gz` (`pdf-g3-structured-recovery-v19`).
Il confronto con C7 usa replay delle richieste originali, bloccando la rete;
quindi può isolare il recupero senza un nuovo campionamento del modello.
Eastman, Danfoss e Graco sono verificati con replay completo dei rispettivi
run C2. Il numero di correzioni e l'eventuale beneficio sui rami vanno letti
nelle misure, senza presumere che ogni recupero tecnico aumenti la copertura.

## Verifiche e provenienza

603 test Python superati dopo C7; 605 dopo C8, senza fallimenti o skip.
I nuovi casi coprono geometria del titolo, intestazioni plurali, tabelle non
diagnostiche, elenchi senza abbinamento, recupero univoco, ripetizioni e
riferimenti esterni. Il lint dei moduli interessati passa. I risultati JUnit
sono in `offline_tests.xml` e `offline_tests_c8.xml`.

`scripts/recompile_diagnostic_candidates.py` apre le EvidenceUnit SQLite
in sola lettura e produce probe separati; non modifica grafi o predizioni
originali. L'analyzer ora accetta `--output` per scrivere le misure di questa
continuazione senza sovrascrivere le tabelle del primo ciclo.
Il checkpoint `budget_before.jsonl` conserva il ledger prima del nuovo run;
il ledger operativo resta quello unico autorizzato. Gli archivi C7/C8,
i profili dei run e i manifest identificano le versioni anche con working tree
non committato.

L'ontologia, il gold storico e i documenti locali dell'utente sono preservati.
La validazione del gold resta riservata ai tecnici. Persistono lavoro sui
percorsi multipagina, abbinamenti semantici nelle tabelle, deduplicazione e
riduzione della revisione umana. Nessun numero di test sostituisce la verifica
dei grafi sui manuali.

## Misure finali

Run C7 concluso in 603,940 secondi, 68 chiamate, 372.798 token di input e
90.021 di completion: **0,082305560 USD**. Tutte le 68 risposte e il relativo
usage sono archiviati; nessun tentativo fallito o senza usage in questo run.
Costo prudenziale cumulativo **1,343788355 USD su 20 USD**, 482 tentativi
chiusi, nessuna prenotazione pendente o superamento. Il totale stimabile dai
token osservati è 0,941769730 USD; rimangono i 28 tentativi senza usage del
ciclo precedente, contabilizzati prudenzialmente. Non sono importi di fattura.

| Hypertherm | C6 (risposte C2) | C7, nuova estrazione | C8, replay C7 |
|---|---:|---:|---:|
| Nodi/relazioni | 139/139 | 153/154 | 153/154 |
| Rami nel grafo | 10 | 17 | 17 |
| Elementi di revisione | 117 | 111 | 111 |
| Record irrisolti nel ledger | 89 | 93 | 93 |
| Occorrenze di ispezioni nei record validati | 24 | 28 | 28 |
| Occorrenze di condizioni nei record validati | 35 | 29 | 29 |
| Rami compilati pubblicabili persi nel grafo | 0 | 0 | 0 |
| Gold tecnico disponibile | no | no | no |

Il numero di irrisolti aumenta nonostante la coda di revisione diminuisca:
sono unità diverse e il nuovo inventario copre più finestre. Le condizioni
conservate diminuiscono; serve confronto documentale per distinguere omissioni,
diversa granularità e variabilità LLM. Le occorrenze non sono conoscenze
deduplicate. Due record pubblicabili descrivono ancora il filtro ostruito,
e alcune alternative della tabella dei codici sono rappresentate sia come
procedura aggregata sia come esito separato. I 17 rami non equivalgono a 17
catene uniche, complete e corrette.

Il controllo canonico C8 verifica 3.604 riferimenti Hypertherm senza errori
letterali o di localizzazione. Il numero di rigetti nei candidati per
quote/anchor incoerenti passa però da 15 a 30 e quello per supporto degli
estremi non stabilito da 47 a 38. I motivi si sovrappongono e i candidati
provengono da campionamenti diversi. Non si può dedurre una precisione
semantica da queste quantità.

Il recupero C8 registra **zero ricollocazioni** nei quattro replay: è coperto
dai test ma non mostra beneficio empirico in questi scambi. Le metriche C7
e C8 Hypertherm coincidono. Tutti i replay completano con zero chiamate API,
zero tentativi di rete e zero scambi inutilizzati. Sui tre altri manuali,
il replay C8 delle risposte C2 mantiene nodi, relazioni, review e probe storico
di C6: Eastman 4/8, Danfoss 5/8, Graco 17/18. Nessuno di questi conteggi è
una metrica semantica validata.

Tutti i grafi finali conservano `approval_eligible=false` e
`diagnostic_extraction_complete=false`. Il nuovo run Hypertherm mostra un
recupero quantitativo rispetto a C6, ma resta sotto i 25 rami della baseline B1
e con più review dei suoi 89 item. Le differenze tra B1 e C7 includono controlli
più forti e nuova estrazione; non sono una prova isolata di regressione o
miglioramento semantico.

Un ulteriore limite applicativo è verificato in `backend/routers/subgraphs.py`
e `frontend/app/graph.js`: il gate G3 espone approvazione/rifiuto della revisione
complessiva, non ancora un percorso completo di correzione e ricompilazione
dei singoli record diagnostici da parte del tecnico. La visibilità delle
evidenze è migliorata, ma il lavoro per rendere la revisione pienamente
operativa resta aperto. Non è sufficiente rimuovere i blocchi di approvazione.

Misure complete e pacchetti delle predizioni: [analysis/MEASUREMENTS.md](analysis/MEASUREMENTS.md)
e `analysis/results.json`. Il prossimo criterio decisivo resta la verifica dei
rami sui PDF, con speciale attenzione ai Test 9 multipagina, alle alternative
condizionate e ai duplicati; il gold tecnico è ancora da annotare e adjudicare.
