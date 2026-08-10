# Confronto delle strategie

## Raccomandazione

Adottare una strategia ibrida **relation-first + publication gate + proiezioni**, mantenendo Luna come modello principale. Le sei ipotesi non sono alternative mutuamente esclusive: risolvono difetti in stadi diversi. La combinazione raccomandata è:

1. scoping multi-ruolo;
2. estrazione diagnostica relation-first;
3. canonicalizzazione globale type-aware;
4. completion mirata con retrieval sul manuale intero;
5. publication gate deterministico;
6. proiezioni canonica, diagnostica e strutturale;
7. eventuale singolo batch di escalation soltanto per ambiguità residue.

Il gate resta obbligatorio anche con il nuovo contratto: un prompt riduce gli errori, ma non è un'invariante di pubblicazione.

## Lettura delle metriche

- **M** = misurato sulla revisione immutabile o da test offline eseguito.
- **S** = simulato deterministicamente sul grafo Luna esistente.
- **E** = stimato mediante sensitivity esplicita.
- **ND** = non disponibile prima dell'implementazione/replay; non viene inventato.

La baseline è 399 nodi, 369 relazioni, 33 isolati, 39/46 sintomi completi, 28/89 azioni scollegate, 195 componenti di cui 29 nei percorsi completi, 14 record gap aggregati, 250 item di review, 8/8 gold, 0/3 vietati, 96 chiamate, 832.562 token, 444,69 s e $0,320466.

## Matrice sintetica

| Strategia | Evidenza quantitativa disponibile | Copertura | Pulizia | Grounding | Costo | Decisione |
|---|---|---|---|---|---|---|
| 1. Chain/relation-first | topologia futura ND; proxy S: 174 nodi diagnostici, 175 relazioni, 0 isolati | da proteggere con retrieval; proxy 8/8 | alta a monte | progettato claim-first; da misurare | parte del combinato E: $0,131–$0,302 | adottare |
| 2. Estrazione attuale + gate | S: diagnostico 174/175; canonico 340/341 | S: 8/8, 0/3 | alta in pubblicazione, rumore resta nei candidati | ID 334/334, quote claim-specific ND | da sola conserva $0,320466 | adottare come safety net, non da sola |
| 3. Proiezioni separate | S: diagnostico 174; strutturale 196; unione 340 | S: 8/8 nella diagnostica | molto alta per la UI | eredita grounding canonico | zero chiamate addizionali | adottare |
| 4. Canonicalizzazione globale | M: 0 exact group, 40 candidati lessicali, ≥8 evidenti | deve preservare 8/8 | riduce varianti | deve unire provenance compatibile | locale + batch opzionale $0,048/$0,076 E | adottare con merge conservativo |
| 5. Scoping selettivo + retrieval | M: 30 pagine, inclusa una campata blueprint di 11 pagine; output futuro ND | retrieval protegge il richiamo | riduce componenti/procedure nel draft | unità più piccole favoriscono quote | incluso nel combinato E | adottare per ruoli, non con drop globale |
| 6. Escalation selettiva | nessun test reale; beneficio topologico ND | solo casi incerti | può ridurre review residua | advisory, poi gate | un batch $0,048 o $0,076 E | opzionale e budget-gated |

## 1. Estrazione chain-first o relation-first

### Variante proposta

Usare come unità di output primaria un bundle di claim grounded, non liste indipendenti di nodi. I pattern validi derivano dal dominio/range configurato:

- `Symptom → MAY_INDICATE → FailureMode → RESOLVED_BY → CorrectiveAction`;
- `ErrorCode → INDICATES → FailureMode → RESOLVED_BY → CorrectiveAction`, con `Asset → GENERATES_ERROR → ErrorCode`;
- `FailureMode → AFFECTS → Component` solo quando esplicito;
- `Asset → HAS_COMPONENT → Component` nella passata strutturale.

Ogni arco deve portare almeno una quote esatta e un anchor risolvibile. I nodi diagnostici vengono materializzati dal bundle, non estratti standalone. Una frase di ispezione, sicurezza, installazione o prevenzione non può quindi diventare una `CorrectiveAction` isolata; può diventarlo solo se la fonte sostiene che risolve una FailureMode esplicita.

### Benefici

- impedisce a monte le 28 azioni isolate osservate;
- riduce i cicli draft → relation → validator → re-extraction;
- rende provenance e semantica della relazione parte dello stesso contratto;
- è naturalmente coerente con l'ontologia.

### Rischio

Una tabella può enunciare sintomo, cause e rimedi in celle o pagine adiacenti. Una strategia rigidamente “tutto nella stessa frase” perderebbe informazione. Per questo la variante raccomandata usa EvidenceUnit contigue e righe di tabella, più retrieval mirato per completare bundle incompleti. Se il completamento non trova prova, il candidato diventa gap e non catena.

### Metriche disponibili

Non è possibile simulare onestamente il numero di nuove entità che un estrattore diverso produrrà. La proiezione sui claim esistenti fornisce soltanto un proxy topologico: 174 nodi/175 relazioni nella diagnostica, zero isolati, 39/39 sintomi completi, 52 FailureMode complete, 53 azioni tutte collegate, 29 componenti, 8/8 gold e 0/3 vietati. Quote/anchor future, gap, review e dedup finale sono ND fino al replay.

## 2. Estrazione attuale seguita da gate deterministico

### Risultato simulato

Il gate sui claim Luna esistenti, selezionando soltanto componenti diagnostici e FailureMode che fanno parte di percorsi completi, produce:

| Metrica | Baseline M | Diagnostica S | Unione canonica S |
|---|---:|---:|---:|
| nodi | 399 | 174 | 340 |
| Asset | 1 | 1 | 1 |
| Component | 195 | 29 | 195 |
| Symptom | 46 | 39 | 39 |
| FailureMode | 68 | 52 | 52 |
| CorrectiveAction | 89 | 53 | 53 |
| relazioni | 369 | 175 | 341 |
| isolati | 33 | 0 | 0 |
| sintomi completi | 39/46 | 39/39 | 39/39 |
| FM senza sintomo/azione | 11/5 | 0/0 | 0/0 |
| azioni scollegate | 28 | 0 | 0 |
| gold / vietati | 8/8 · 0/3 | 8/8 · 0/3 | 8/8 · 0/3 |

Il pruning dei soli isolati è insufficiente: lascia 2 sintomi incompleti, 11 FailureMode senza sintomo, 5 senza azione e 166 componenti non diagnostici nella superficie principale.

### Vantaggi e limiti

È la migliore protezione deterministica e offre una migrazione incrementale. Da solo, però:

- non riduce le 96 chiamate upstream né il costo misurato di $0,320466;
- non recupera quote/anchor già perse;
- non evita che la review queue riceva rumore;
- rischia perdita silenziosa se gli esclusi non diventano gap target-specific.

Va quindi adottato come ultimo gate, non come unica modifica.

## 3. Separazione delle proiezioni

La separazione è una query sul medesimo grafo, non una seconda ontologia e non una copia delle entità.

### Proiezione diagnostica

Include:

- percorsi completi da Symptom o ErrorCode a FailureMode e CorrectiveAction;
- `AFFECTS` espliciti dei FailureMode inclusi;
- Component endpoint di tali `AFFECTS`;
- Asset e link strutturali necessari a contestualizzare quei componenti/codici.

Proxy Luna: 174 nodi e 175 relazioni, 29 componenti, zero isolati, 100% dei sintomi completi.

### Proiezione strutturale

Include Asset, Component e `HAS_COMPONENT` grounded. Proxy Luna: 196 nodi e 195 relazioni, zero isolati. Mantiene tutti i 195 componenti senza affollare la diagnosi.

### Unione canonica pubblicabile

Include gli ID delle due viste una volta sola. Proxy Luna: 340 nodi, 341 relazioni, zero isolati. I 166 componenti non diagnostici restano disponibili nella vista strutturale.

### Valutazione

È la misura con il minor rischio di perdita informativa. Non riduce da sola costo o errori di estrazione, ma corregge la rappresentazione e consente di definire invarianti per vista. Va adottata in ogni opzione.

## 4. Canonicalizzazione globale cross-chunk

Il confronto offline misura zero duplicati esatti normalizzati e 40 coppie lessicali candidate. Il numero 40 non è il numero di merge: include molti parent/child o concetti più specifici. Sono evidenti almeno otto famiglie da verificare, tra cui plurali, varianti lessicali di componenti e azioni quasi identiche.

### Politica sicura

1. Generare candidati solo all'interno dello stesso tipo.
2. Auto-unire varianti puramente ortografiche/morfologiche soltanto se proprietà, contesto ed evidenza sono compatibili.
3. Per Symptom, FailureMode e CorrectiveAction usare le funzioni type-specific e il vicinato relazionale.
4. Non auto-unire mai per solo token containment.
5. Trattare assieme/parte, generico/specifico, condizioni diverse e verbi opposti come non equivalenti.
6. Mandare gli incerti a un unico batch di adjudication o alla review.
7. Dopo un merge, rimappare relazioni, unire evidence ref senza duplicarle e rieseguire domain/range, grounding e gold acceptance.

### Valutazione

È necessaria, ma non si può dichiarare un nuovo conteggio nodi senza decidere semanticamente i candidati. Il rischio è basso con la politica conservativa; è alto con fuzzy merge aggressivo. L'escalation stimata costa $0,048 nel caso centrale o $0,076 in quello conservativo, ma può essere saltata lasciando gli incerti distinti.

## 5. Scoping più selettivo

Lo scoping non deve essere un singolo booleano “pagina selezionata”. Deve assegnare ruoli non esclusivi:

- `diagnostic_primary`: troubleshooting, fault table, error table, testo causale/remediativo;
- `structural_inventory`: parts list, diagramma, schema, nomenclatura componenti;
- `retrieval_only`: intero manuale indicizzato, interrogato solo per target incompleti.

Una pagina può avere più ruoli. Questo evita una regola fragile che elimina globalmente installazione, manutenzione o diagrammi: una procedura in quelle sezioni può davvero risolvere un guasto citato altrove. La differenza è che non viene estratta preventivamente come azione standalone.

La run corrente ha 30 pagine selezionate e include la campata blueprint 40–50. Questo fatto spiega il rumore, ma i numeri di pagina non devono comparire nella produzione. Il nuovo risultato end-to-end è ND; viene valutato solo dopo implementazione. La protezione contro la perdita è il retrieval sull'intero manuale, non il mantenimento di tutto nel prompt primario.

## 6. Escalation selettiva

Luna resta il modello principale per scoping, bundle extraction e completion. Terra può ricevere al massimo un batch contenente esclusivamente:

- coppie di canonicalizzazione davvero ambigue;
- grounding semanticamente ambiguo con quote disponibile;
- target indicator-reachable non risolti dopo retrieval;
- conflitti di disposition che il gate non può decidere.

L'output del modello forte è advisory: non può pubblicare un arco privo di quote/anchor e passa comunque dal gate deterministico.

Non sono state fatte chiamate reali, quindi il beneficio è ND. Il costo stimato di un batch è:

- centrale: 12.000 input + 2.000 output Terra = $0,048;
- conservativo: 20.000 input + 3.000 output Terra = $0,076.

La chiamata viene saltata se il suo ceiling porta la previsione della run oltre $0,35; gli item restano gap/review. Non è giustificata una sostituzione globale Luna→Terra.

## Confronto costo/prestazioni

La ricostruzione aggregata del prezzo baseline produce $0,320471 contro $0,320466 persistiti; la differenza di $0,000005 deriva dall'arrotondamento per chiamata. Il valore autoritativo resta quello persistito.

Per la pipeline combinata, la sensitivity usa lo scoping misurato e assume che relation-first elimini i passaggi separati generalizzati. Poiché i bucket token per singola operazione non sono persistiti, sono stime, non misure:

| Scenario | Chiamate E | Token E | Durata E | Costo E |
|---|---:|---:|---:|---:|
| basso, nessuna escalation | 21 | 339.458 | 187,276 s | $0,130977 |
| centrale, un batch | 25 | 476.734 | 281,334 s | $0,226350 |
| conservativo, batch maggiore | 28 | 609.010 | 360,392 s | $0,301724 |

La stima centrale è circa $0,23 e quella conservativa circa $0,302: entrambe coerenti con l'obiettivo “vicino a $0,30”, con stop preflight a $0,35. Non ha senso consumare budget per avvicinarsi artificialmente a $0,30.

## Rischio di perdita di informazione

| Rischio | Mitigazione obbligatoria |
|---|---|
| una catena è distribuita su celle/pagine | EvidenceUnit contigue + retrieval target-specific sull'intero manuale |
| una procedura generica è in realtà un rimedio citato altrove | non eliminarla dal corpus; promuoverla solo con `RESOLVED_BY` grounded |
| componenti strutturali scompaiono | conservarli nella proiezione strutturale dello stesso grafo |
| canonicalizzazione fonde parte e assieme | stesso tipo + semantica + contesto + vicinato + evidenza; default “non fondere” |
| gate nasconde incompletezza | gap target-specific persistito con disposition e motivo |
| escalation inventa un link | quote/anchor obbligatorie e gate deterministico dopo il modello |

## Perché la combinazione è ontologicamente corretta

Non viene aggiunto alcun tipo o arco. La completezza è definita percorrendo le relazioni già configurate e rispettandone dominio e range. `AFFECTS` resta opzionale perché l'ontologia non lo rende requisito di `RESOLVED_BY`. I ruoli di pagina, le proiezioni, le evidence ref e le disposition di review sono metadata operativi, non proprietà del grafo ontologico.

## Perché la combinazione è agnostica

Le regole di produzione dipendono esclusivamente da:

- schema caricato a runtime;
- dominio e range;
- semantica del tipo;
- quote e anchor della fonte;
- topologia e completezza;
- ruolo discorsivo/strutturale dell'EvidenceUnit.

Non dipendono da E-554, Eastman, pagine fisse, termini gold, produttore, macchina o dominio. La prova offline include cinque casi sintetici su pompa, macchina generica, conveyor, controller e sistema termico, oltre a nove fixture golden eterogenee. Il gold E-554 viene letto solo dall'evaluator post-run.

## Decisione finale

Procedere con la combinazione completa. Non approvare un piano ridotto a solo pruning, sole proiezioni o modello più costoso:

- solo pruning non corregge l'upstream né i costi;
- sole proiezioni non garantiscono grounding claim-specific;
- solo chain-first senza gate non garantisce invarianti;
- solo modello forte non corregge i difetti deterministici;
- scoping aggressivo senza retrieval mette a rischio la copertura.
