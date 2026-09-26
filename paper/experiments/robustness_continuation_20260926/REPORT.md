# Continuazione C9–C12: recupero diagnostico e correzione per record

## Esito e limiti di accettazione

Implementazione verificata sui quattro manuali, con nuove estrazioni complete C11 e verifica incrementale C12 del codice finale `pdf-g3-structured-recovery-v22`. Il Test 9 Hypertherm recupera quattro associazioni causali e rimedi terminali documentati, conservando i 17 rami C11. **Non sono quattro catene operative complete**: restano prerequisiti, percorsi alternativi e rimandi da risolvere. Tutti i grafi restano non approvabili e con estrazione incompleta. L'obiettivo complessivo di correttezza/completamento e riduzione del lavoro umano non è ancora raggiunto.

La correzione del singolo record è ora operativa: campi e prove affiancate, nuova revisione, storia prima/dopo, ricompilazione e conservazione dei blocchi residui. Verificata via API e browser su copia del database. Non è annotazione di tecnici reali e non sostituisce il gold indipendente.

**Costo cumulativo: 1,644144695 USD su 20 USD**, inclusi retry, errori e prenotazioni prudenziali senza usage osservabile. Incremento di questa continuazione: 0,300356340 USD rispetto a 1,343788355. Tutti i 681 tentativi sono chiusi; nessuna prenotazione attiva. Fonte: [risultati finali](final_results.json) e ledger originale `../robustness_20260925/real_call_budget.jsonl`.

## Modifiche e prove associate

- Inventario completo delle 111 notifiche C8, collegamenti molti-a-molti a record, finestre, anchor, pagine e attributi, senza cancellare le segnalazioni. [Inventario iniziale](review_inventory_before.json), [mappa delle perdite](LOSS_MAP.md).
- Supporto deterministico delle introduzioni causali seguite da bullet consecutivi, senza abbinare causa/rimedio per posizione. Sugli stessi candidati Test 9 low C9 il probe passa da zero a quattro record pubblicabili. Il negativo con intestazione non causale resta bloccato.
- Recupero circoscritto dopo errori del compilatore; feedback tenuto separato dalla fonte. I candidati validi precedenti non sono sostituiti da un report che ne perde i rami, e duplicati non migliorano il punteggio di selezione. Non vengono ritentati come errori tecnici gli abbinamenti strutturalmente ambigui.
- Protezione contro la trasformazione di NO a una domanda congiunta in due negazioni con AND; nessun guasto inferito dal solo comando di sostituzione; severità Unknown conservata quando la fonte non la dichiara.
- Continuazioni di procedure numerate cercate nella fonte intera, anche su pagine classificate strutturali, con radice già diagnostica e limiti di pagine/caratteri. C12 recupera il pacchetto Test 9 pp96–100 che C11 non generava. I passaggi originali sono collegati al record come `procedure_context`; `procedure_path_verified=false` resta esplicito. Il riconoscitore limitato dei titoli Test non costituisce un interprete generale di procedure.
- Deduplicazione esatta delle istruzioni con/senza prefisso numerico, preservando occorrenza e condizioni. L'[audit delle 21 ambiguità](identity_21_audit.json) distingue 93 coppie con varianti lessicali, parte/tutto e rami differenti. Nessuna fusione per sola similarità; duplicati semantici residui documentati.
- Endpoint di correzione per record e interfaccia G3 con un modulo alla volta, fonti consultabili, motivazione/revisore, cronologia e nuova compilazione. Concorrenza controllata sulla revisione corrente; nessun override delle prove o approvazione implicita.

Ontologia e schema dei candidati del provider invariati. I metadati validati aggiuntivi non creano nuovi tipi ontologici. Baseline, gold storico e modifiche locali antecedenti sono preservati; [controllo finale](preservation_v22.json).

## Confronti di sviluppo e fallimenti conservati

[Protocollo](PROTOCOL.md) e archivi sorgente sono congelati prima delle rispettive chiamate. Il confronto low/medium usa lo stesso modello GPT-6 Luna e lo stesso limite di output 24k; misura l'effort, non una differenza tra modelli. Prezzi e tier sono registrati in [pricing_checked.md](pricing_checked.md).

| Pacchetto C10 | Candidati | Publish del compilatore | Irrisolti |
| --- | ---: | ---: | ---: |
| Hypertherm pp67–69 low | 9 | 0 | 9 |
| Hypertherm pp67–69 medium | 11 | 0 | 10 |
| Eastman pp37–39 low | 13 | 0 | 12 |
| Eastman pp37–39 medium | 14 | 1 | 12 |
| Test 9 low replica 1 | 6 | 4 | 2 |
| Test 9 low replica 2 | 5 | 3 | 2 |
| Test 9 medium replica 1 | 6 | 3 | 3 |
| Test 9 medium replica 2 | 6 | 0 | 6 |

Le eventuali differenze tra candidati e publish+irrisolti sono esclusioni esplicite. Tutte le repliche sono riportate: medium non offre un vantaggio uniforme. Il [source audit dei pacchetti](packet_source_audit.json) distingue esiti terminali supportati e completezza operativa, senza assegnare precisione/recall globali. Nessuna catena completa del Test 9 viene certificata da questi conteggi.

C9→C10 sugli stessi candidati è un probe limitato del compilatore, non un replay end-to-end. I pacchetti C10 sono nuove estrazioni dirette, senza il recupero completo del workflow. Due avvii C10 con risorse runtime incomplete sono preservati. Il run completo Eastman C10 è escluso dall'accettazione: il test di integrazione ha rilevato contaminazione dell'inventario sorgente con il feedback. La correzione C11 separa il feedback; il test negativo dimostra che una predizione di recupero non può diventare prova. Il log della prima suite fallita resta disponibile.

C11 riesegue realmente tutti e quattro i manuali con nuova sorgente congelata. La verifica mostra un altro difetto: pagine 98–99 del Test 9 classificate strutturali non entravano nel pacchetto diagnostico. C12 corregge questo confine. Riusa solo richieste C11 identiche a quelle effettivamente inviate al provider, errori inclusi; sono consentite nuove chiamate solo sul pacchetto 96–100. I primi avvii incrementali falliscono per il fingerprint che ometteva `service_tier`; una chiamata Hypertherm già fatta è contabilizzata e non scelta come risultato. Runner corretto congelato separatamente in `incremental_runner_r1.py/json`.

C12r1 completa i quattro workflow: Eastman 33, Danfoss 18, Graco 24, Hypertherm 79 scambi riutilizzati; **due sole nuove chiamate Hypertherm**, 0,004476065 USD. Zero richieste bloccate o scambi inutilizzati. Sugli altri tre manuali nodi e relazioni sono identici a C11. C12 è una verifica incrementale con chiamate nuove, **non un replay interamente offline né una seconda estrazione indipendente**. Non si attribuisce di nuovo il costo degli usage riutilizzati.

## Verifica documentale dei grafi finali

| Manuale | Candidati | Rami nel grafo | Record irrisolti | Notifiche review (bloccanti) | Riferimenti canonici letterali |
| --- | ---: | ---: | ---: | ---: | ---: |
| Eastman | 96 | 9 | 57 | 75 (52) | 715/715 |
| Danfoss | 19 | 8 | 9 | 26 (8) | 461/461 |
| Graco | 73 | 19 | 36 | 64 (36) | 471/471 |
| Hypertherm | 184 | 21 | 145 | 157 (121) | 3425/3425 |

Rami, candidati e notifiche sono unità distinte. Nessun fallimento nel controllo letterale dei locator; tale controllo **non certifica il supporto semantico**. Tutti gli `approval_eligible` sono false. Fonte riproducibile: [final_results.json](final_results.json).

L'[audit dei tre manuali](full_three_source_audit.json) esamina tutti i 36 record pubblicati C11 di Eastman, Danfoss e Graco; il trasferimento a C12 è giustificato dall'identità verificata di nodi e relazioni, non assunto tra versioni:

- Eastman: nove record corrispondono a sette casi sorgente dopo raggruppamento manuale; sei casi locali supportati e un caso RF con conflitto nel documento (70 piedi nella prosa, 75 nella tabella e altrove). Calibrazione touchscreen conserva i sei passi e il controllo di riavvio; non si certifica la completezza di tutte le dipendenze operative. Duplicati di lente e ugello restano.
- Danfoss: otto record rappresentano cinque casi sorgente, con duplicati di ventole/prese d'aria. Ispezioni e rinvio al servizio tecnico devono restare distinti; la ripetizione del numero1 non è prova di pairing.
- Graco: diciannove record rappresentano diciassette casi sorgente, con associazioni problema/causa/rimedio sostenute dalle righe. Mancano prerequisiti comuni di depressurizzazione e risoluzione dei rimandi; la nota Clear* e il manuale separato del motore non diventano procedure verificate.

Per Hypertherm l'[audit finale](hypertherm_c12_source_audit.json) controlla i quattro nuovi esiti del Test 9 e i casi prioritari pp67–69/96–104; elenca esplicitamente come non giudicati esaustivamente gli altri record. Il Test 9 ha sei esiti terminali individuati nella fonte: 13b,21a,22a,28a,28b,28c. Sono pubblicati quattro esiti locali distinti: 21a,28a,28b,28c. La causa è esplicita nell'introduzione di p96 e il rimedio è verificato in pp99–100. Restano:

- zero catene operative complete verificate, pur avendo 111 span ordinati di contesto per ciascuno dei quattro nuovi record;
- perdita di preparazione, isolamento dei connettori, passi OFF/ON, rimandi di sostituzione e percorsi alternativi; 28b restringe l'ingresso al percorso 20b senza rappresentare anche 22b;
- 13b senza ramo pubblicato; 22a dichiara una sostituzione ma non un guasto dei fili esplicito: non inventarlo per completare il grafo;
- il filtro p69 appare in due record senza il requisito esplicito di blocco totale del flusso e senza i controlli precedenti; p67 conserva il raffreddamento di tre minuti ma perde circostanze scatenanti e prevenzione;
- pagina 228 resa e letta visivamente, ma nessuna copertura della topologia delle frecce certificata dall'OCR.

Non sono state identificate relazioni causali o rimedi terminali inventati nei quattro nuovi esiti auditati. È invece osservata incompletezza del percorso. Questo giudizio locale non si estende ai record non giudicati o all'intero manuale.

Il probe storico finale restituisce Eastman5/8, Danfoss5/8+3 gap, Graco17/18+1 gap. È matching lessicale, non qualità validata: ad esempio può mancare il ramo esplicito degli specchi Eastman. L'[audit di tutti i 34 casi storici](historical_34_source_audit.json) propone correzioni motivate dalla fonte, comprese inferenza del guasto dai filtri, cause alternative dell'ugello e prerequisiti Graco. L'originale non viene modificato. Precisione e recall semantiche globali restano non disponibili.

## Carico umano e regressioni

L'inventario disgiunto finale Hypertherm ha 157 notifiche e 157 target esatti: 28 evidenza tecnica, 43 contenuto da auditare, 47 pairing/identità, 38 contesto mancante, 1 omissione. **Non sono 157 catene uniche o decisioni umane indipendenti**; il numero deduplicato di decisioni interpretative resta da misurare. I collegamenti molti-a-molti e le azioni residue sono disponibili in [review_inventory_c12.json](review_inventory_c12.json) e [LOSS_MAP.md](LOSS_MAP.md).

Rispetto a C8: Hypertherm 17→21 rami, 111→157 notifiche, 93→145 record irrisolti. C11 prima del recupero mirato aveva 17 rami, 151 notifiche e 142 irrisolti. C12 preserva tutti i 17 rami C11, ma aggiunge anche sei notifiche. Il recupero automatico evita localmente di dover ricostruire manualmente quattro associazioni causali; non dimostra una riduzione netta del lavoro.

Sugli altri manuali, C8→C12: Eastman 9→9 rami e 80→75 review; Danfoss 5→8 e 28→26; Graco 22→19 e 39→64. Queste sono variazioni quantitative tra estrazioni/versioni differenti, non effetti causali isolati del codice. La regressione Graco e l'aumento degli irrisolti restano aperti. Nessuna cancellazione di notifiche è usata per rivendicare miglioramento.

La UI riduce il perimetro della singola correzione: il tecnico può intervenire su un record e vedere la fonte senza rigenerare il manuale. Tempo risparmiato, numero di decisioni e qualità dopo la revisione **non sono ancora misurati con persone**. [Procedura per i tecnici](PROCEDURA_TECNICI.md): annotazione A/B indipendente, congelamento, adjudication separata, versioni e motivazioni. Tutti i moduli A/B sono ancora `unannotated` e `branches: []`. Gli audit dell'agente sono esposti alle predizioni, separati dal gold e non input del generatore/scorer.

## Verifica tecnica, tempi e riproduzione

Suite finale: **612 test Python superati**, nessun fallimento o skip, 66,455 secondi nel report JUnit C12. Test frontend dei rami superato; controllo sintassi JavaScript e controlli statici mirati superati. I test tecnici non certificano la qualità semantica.

[Verifica API v22](human_api_v22_verification.json): correzione valida 200, 152 relazioni estranee preservate; revisione obsoleta 409; approvazione con blocchi residui 409; citazione inventata salvata come review senza pubblicazione; due voci di cronologia; hash database originale invariato. [Verifica browser](browser_verification.json) e [schermata finale](review_ui_final.png): modifica di una citazione su copia, nuova revisione e storia consultabile. Nessuna chiamata modello né annotazione umana attribuita a queste prove.

Tempi runner C11: Eastman 1013,237s; Danfoss 110,729s; Graco 161,615s; Hypertherm 1615,165s. Sono tempi trascorsi del runner, includono attese/retry e possibili sospensioni dell'host; non sono un benchmark di latenza del modello né tempo umano. C12 incrementale: 3,764s/0,815s/0,807s/57,955s rispettivamente; non confrontarli ai tempi delle estrazioni complete.

[REPRODUCE.md](REPRODUCE.md) distingue sorgenti, runner reali, probe e cache incrementale. `source_before.tar.gz` preserva lo stato dirty iniziale; `source_c9/c10/c11/c12.tar.gz` identificano gli incrementi. `source_final.tar.gz` e `preservation_check.json` sono snapshot intermedi v21; **lo snapshot di consegna è `source_final_v22.tar.gz` con `final_v22_manifest.json` e `preservation_v22.json`**. Nessun risultato viene trasferito automaticamente a modifiche future del generatore.

Riproduzione offline finale completata su tutti e quattro i manuali con il runner esistente esteso a leggere gli scambi supplementari C12: 33/18/24/81 scambi esatti rispettivamente, nessuna richiesta mancante, nessuno scambio inutilizzato e zero tentativi di rete. [replay_verification.json](replay_verification.json) conferma identità di nodi, relazioni, candidati/record validati e review rispetto a C12. Le sole differenze osservate riguardano identificatori/tempi di revisione, durata e registrazione di testo raw/path degli archivi. È una prova di riproducibilità, non una replica stocastica indipendente.
