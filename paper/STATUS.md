# Stato scientifico e registro delle evidenze

Baseline del codice: `4564d39af478ebc56e8126c06c0724de998e7a33`.
Questo documento distingue l'audit storico dagli esperimenti da eseguire sul nuovo
profilo GPT-6 Luna. Il codice locale è stato allineato al remoto preservando le
modifiche preesistenti a `docs/README.md` e `docs/PIPELINE_SPIEGAZIONE_IT.md`.

## Valutazione

L'approccio è una base credibile per un articolo, ma non è ancora una dimostrazione
scientifica completa. Il lavoro prioritario è rendere misurabili correttezza
semantica, trasferibilità, costo della revisione e utilità a valle. Una riscrittura
dell'architettura non è giustificata dall'evidenza disponibile. Servono componenti
separabili per esperimenti controllati e confini di pubblicazione verificabili.

| Affermazione | Evidenza disponibile | Stato per il paper |
| --- | --- | --- |
| Esiste una pipeline con estrazione LLM, record diagnostici tipizzati, compilazione e riferimenti alle fonti | Codice corrente, schemi e test | Descrivibile con riferimenti al codice congelato |
| La campagna v11 copre 33 dei 34 elementi gold secondo il suo criterio di accounting | `artifacts/acceptance/g3/diagnostic_benchmark_second_hardening_v11_20260813/campaign_results.json` | Risultato di sviluppo: 97,06% micro; non precisione semantica |
| 25 dei 34 elementi risultano autonomi nel gold v11 | Stessa campagna; Eastman 3/8, Danfoss 5/8, Graco 17/18 | 73,53% micro; macro corretto 64,81%. Evitare l'etichetta macro usata in alcuni documenti storici |
| Zero relazioni non supportate nell'intero output | Gold Eastman parziale e controlli non esaustivi | Non dimostrato; serve audit semantico dell'output completo nel perimetro valutato |
| Il codice v12 conserva i risultati v11 | v12 amplia il contesto semantico e rende advisory le finestre diagnostiche | Non verificato; confronto controllato da eseguire |
| Hypertherm dimostra generalizzazione blind | `benchmark_runs/hypertherm_holdout_v12_20260813/real_run_state_recovery.json` | Non utilizzabile come nuovo blind: osservato in sviluppo, gold assente, accounting incompleto |
| Il nuovo modello riduce il costo del sistema a pari qualità | Prezzi unitari inferiori; pilot reale completato, qualità insufficiente nel profilo provato | Ipotesi; misurare token, retry, qualità e revisione |
| Il grafo abilita interrogazioni deterministiche | Contratto proposto in `sections/02_maintenance_graph_rationale.md` | Motivazione fondata; executor e valutazione dedicata ancora da completare |
| Il sistema è ontology/provider/language agnostic | Schema diagnostico specifico e provider corrente | Non sostenibile; valutare esplicitamente il trasferimento tra produttori |
| Riduce tempi di riparazione o fermo impianto | Nessuno studio operativo | Fuori dalle conclusioni attuali |

## Materiale storico da mantenere distinto

La campagna v11 riporta 87 chiamate, costo stimato di 0,2374162 USD e 90 elementi
di revisione complessivi. Sono dati di quella configurazione, non del nuovo
modello. Il gold contiene 34 elementi selezionati: non equivale all'annotazione
esaustiva di tre manuali. Il campione Eastman è rappresentativo, gli altri due
coprono le tabelle selezionate. La media macro dell'accounting è 95,83%.

Le verifiche software nell'audit hanno coperto 559 test unici della versione
remota, includendo riesecuzioni con storia Git e accesso alla porta locale.
Non costituiscono una misura della qualità dell'estrazione. Gli artifact storici
riportano inoltre uno stato dirty: la ricostruzione esatta del run richiede il
manifest originario e non può essere presunta dal solo commit.

## Stato del pacchetto corrente

- Cartella paper, linee guida adattate e originale conservato: predisposti.
- Motivazione scientifica del grafo e fonti: prima sezione scritta.
- Protocollo gold e sperimentale: specificato, da congelare con gli annotatori.
- Integrazione GPT-6 Luna: primo incremento completato; 564 test offline superati e lint dei file modificati superato. Dettagli e limiti della verifica in `MODEL_DECISION.md`.
- Pilot reale GPT-6 Luna sui 4 manuali di sviluppo completato. Nuovi gold, confronto controllato tra modelli e studio downstream ancora da eseguire.
- Manoscritto: struttura e prima sezione; non ancora un draft completo circolabile.

Per ogni nuova campagna aggiungere un riferimento al manifest, all'output grezzo,
al gold versionato e al report generato. Non sovrascrivere questi risultati
storici e non riclassificare retroattivamente un campione di sviluppo come test.

## Preparazione del corpus

Creato `manuals/registry.json` con 4 documenti storici riconciliati ai PDF originali
e 12 slot nuovi da selezionare. Responsabilità e criteri in `manuals/README.md`.
Nessun nuovo manuale è stato acquisito o annotato in questo passaggio.

## Pilot reale registrato

[Report](experiments/dev_luna_20260925/REPORT.md) e
[osservazioni](experiments/dev_luna_20260925/OBSERVATIONS.md).
Codice del generatore: `528f069`; un run per documento, reasoning low,
escalation disabilitata. Cap cumulativo autorizzato: 15 USD.

Quattro output prodotti in 1.152,319 secondi di esecuzione della campagna
(19 minuti e 12 secondi), con 116 chiamate incluso il test API.
Costo contabilizzato prudenziale: 0,156349335 USD; quota stimabile dai token
osservati: 0,139875960 USD. Due tentativi mantengono la prenotazione massima
per assenza di uso osservabile. Tutte le prenotazioni sono chiuse, senza
superamenti del cap o degli envelope.

Il matching storico riconosce 3/8 casi autonomi per Eastman, 0/8 per Danfoss
e 0/18 per Graco. Danfoss ha inoltre un caso riconosciuto come lacuna esplicita.
Hypertherm non ha gold. Tutti i grafi hanno approval_eligible=false.
Il profilo corrente non supera la valutazione di sviluppo; i risultati non
consentono una conclusione isolata sulla qualità del modello rispetto a v11.

Prima della campagna finale servono interventi mirati su risposte troncate,
validazione dei record e associazione degli anchor, seguiti da un nuovo pilot
confrontabile. Nessuna modifica al generatore è stata applicata durante i run.

## Audit della pipeline antecedente all'implementazione

Completata l'[analisi con piano concreto](ANALISI_PIANO_ROBUSTEZZA_ESTRAZIONE.md)
del codice `528f069` e del pilot `dev_luna_20260925`. La baseline `4564d39`
indicata all'inizio di questo registro riguarda l'audit precedente, non il codice
del pilot. Nessuna implementazione del servizio, modifica al gold o nuova
chiamata API di estrazione è stata eseguita in questa fase.

L'[audit offline](analysis/pipeline_audit_20260925.json) verifica 47 hash degli
artifact e quattro PDF; riproduce le disposizioni di tutti i 141 candidati
tipizzati persistiti. Non recupera risposte originali non salvate e non attesta
la correttezza semantica dei candidati. Il runtime locale ha versioni PyMuPDF e
OpenAI diverse da quelle del pilot: il replay usa le evidenze SQLite congelate.

Riscontri aggiuntivi: Danfoss e Graco producono grafi esclusivamente strutturali;
56 occorrenze di passi di ispezione nei candidati non hanno una rappresentazione
di tipo Inspection nel grafo; pagine diagnostiche Hypertherm numeriche o con
testo corrotto possono essere escluse. Probe sintetici riproducono il rigetto
di un'intera risposta per un record invalido, il retry esterno non attivato da
errori catturati internamente e una relazione fra righe diverse che supera il
solo grounding letterale. Lo scorer storico accetta alcuni contrasti di
negazione e up/down-stroke: non può certificare precisione semantica.

Le questioni individuate nel gold tramite lettura dei PDF sono proposte di audit,
non correzioni già validate da tecnici. Il piano richiede gold versionato e
adjudication, incluso un perimetro esplicito Hypertherm, prima del confronto
decisivo. Il cap originariamente proposto era 40 USD. L'utente ha successivamente
approvato l'implementazione con un nuovo cap cumulativo di **20 USD**,
comprensivo di confronti, retry ed escalation. Il budget precedente è chiuso.

## Incremento di robustezza approvato

Codice e dati baseline congelati prima delle modifiche in
`experiments/robustness_20260925/baseline_manifest.json` e `baseline_source.tar.gz`.
Il [report operativo](experiments/robustness_20260925/REPORT.md) distingue
baseline B1, pacchetti P1, candidato C1 e candidato C2, ciascuno con sorgente,
configurazione, ledger e output conservati. Le [misure generate](experiments/robustness_20260925/analysis/MEASUREMENTS.md)
non sono metriche di qualità validate da tecnici.

L'ontologia resta invariata. Ispezioni ordinate e condizioni vengono conservate
come metadati diagnostici tipizzati, collegati ai rami e consultabili nella UI;
non sono nuovi tipi dell'ontologia e non sono trasformate in riparazioni.
Il nuovo percorso conserva risposta e usage prima del parsing, valida e recupera
i singoli record, mantiene layout/celle/continuazioni e controlla il supporto
dei collegamenti oltre alla presenza letterale delle citazioni.

Il gold originale è immutato. I [pacchetti per i tecnici](evaluation/gold_review_v1/README.md)
sono preparati senza predizioni e comprendono Hypertherm su un perimetro esplicito.
Nessuna annotazione è ancora certificata come gold tecnico. La qualità semantica
finale, la completezza dei rami e il carico umano restano da verificare sui PDF;
i risultati negativi e i duplicati residui sono riportati nel report operativo.

## Esito del primo ciclo implementato

[Rapporto finale di sviluppo](experiments/robustness_20260925/REPORT.md):
599 test Python superati e quattro replay esatti C6 completati senza rete.
Probe storico finale: Eastman 4/8, Danfoss 5/8 più 3 gap, Graco 17/18 più
1 gap; Hypertherm senza gold. La nuova baseline B1 dava rispettivamente
5/8, 0/8 e 0/18. Non sono metriche semantiche validate. Hypertherm passa
da 25 a 10 rami nel grafo e da 89 a 117 review; regressione quantitativa
aperta. Tutti i grafi restano non approvabili e con estrazione incompleta.
Costo prudenziale cumulativo 1,261482795 USD su 20 USD, 414 tentativi chiusi.
Il gold tecnico, la completezza dei rami e la riduzione del carico umano
restano necessari prima di dichiarare raggiunto l'obiettivo.

## Continuazione sulle tabelle Hypertherm

[Rapporto C7/C8](experiments/robustness_followup_20260926/REPORT.md): riconoscimento
dei titoli diagnostici estesi sopra intestazioni causa/soluzione e gestione
esplicita degli elenchi non abbinati. Nuovo run completo Hypertherm: 17 rami
nel grafo contro 10 nel precedente C6; review 111 contro 117, ma record irrisolti
93 contro 89 e condizioni conservate 29 contro 35. Restano duplicati e limiti
semantici: non è un risultato di accettazione. C8 recupera locator errati solo
entro finestre atomiche verificate; zero casi applicabili nei quattro replay,
quindi nessun beneficio empirico attribuibile a quel recupero.
605 test superati, quattro replay esatti senza rete. Costo cumulativo
1,343788355 USD su 20 USD, 482 tentativi chiusi. Gold Hypertherm ancora
non annotato tecnicamente; aggiunte quattro note proposte per l'adjudicator,
separate dai moduli A/B e non usate per generazione o scoring. Anche il flusso
G3 di correzione/ricompilazione umana dei singoli record resta da completare.


## Continuazione C9–C12: verifica documentale e gate per record

[Rapporto di continuazione](experiments/robustness_continuation_20260926/REPORT.md):
quattro nuove estrazioni complete C11, quindi verifica incrementale C12 del
generatore `pdf-g3-structured-recovery-v22`. C12 riusa richieste identiche C11 e
aggiunge due chiamate sul Test 9 Hypertherm, recuperando il contesto delle pagine
strutturali 98–99. Non è una nuova estrazione indipendente. Hypertherm conserva
tutti i 17 rami C11 e ne aggiunge quattro con causa/rimedio terminale sostenuti
dalla fonte; nessuna delle quattro catene operative è certificata completa.
Restano prerequisiti, ordine e percorsi alternativi non risolti. Sugli altri tre
manuali nodi e relazioni C12 sono identici a C11.

Risultati finali: Eastman 9 rami/75 review; Danfoss 8/26; Graco 19/64;
Hypertherm 21/157, con 145 record irrisolti. Il confronto Hypertherm C8→C12
(17→21 rami, 111→157 review, 93→145 irrisolti) non dimostra una riduzione del
carico umano. Graco regredisce quantitativamente rispetto a C8. Tutti i grafi
restano non approvabili. I riferimenti canonici sono letterali, ma tale verifica
non certifica la semantica. Gli audit separano casi locali supportati,
incompletezze e record non giudicati; precisione/recall globali non disponibili.

Implementata correzione del singolo record G3 con prove affiancate, storia,
nuova revisione, ricompilazione e controllo di concorrenza. Verificata via API
e browser su copia: 152 relazioni estranee preservate, citazione inventata
bloccata e approvazione residua rifiutata. Nessuna annotazione tecnica umana è
attribuita a queste prove. Suite finale: 612 test Python superati e test
frontend superato. Ontologia, gold storico e documenti locali protetti invariati.

Audit di tutti i 34 casi storici e delle 21 ambiguità di identità conservati come
proposte dell'agente esposto alle predizioni; moduli A/B ancora unannotated e
vuoti. Preparata la procedura concreta per annotazione indipendente e adjudication.
Costo prudenziale cumulativo **1,644144695 USD su 20 USD**, 681 tentativi chiusi,
nessuna prenotazione attiva. Snapshot di consegna `source_final_v22.tar.gz`;
C10 fallito e snapshot intermedi restano distinti e preservati.

Quattro replay offline finali della composizione C11+C12 completati con richieste
esatte e rete bloccata: nodi, relazioni, record e review identici ai risultati C12.
Le sole differenze sono identificatori/tempi e registrazione raw/telemetria;
nessuna ulteriore chiamata reale o spesa.

## Allineamento della documentazione per il commit

README principale, indice docs, architettura, mappa dei test e guida italiana
sono allineati a v22 e ai limiti C9–C12. La guida italiana precedente è conservata
in `docs/PIPELINE_SPIEGAZIONE_IT_20260728.md`; i report v11 sono etichettati come
storici. Questo aggiornamento documentale successivo al freeze non modifica
risultati, gold, codice del generatore o ledger. I controlli di conservazione
negli artifact descrivono lo stato alla chiusura della campagna, prima di questo
aggiornamento esplicitamente richiesto ai documenti generali.

## Diagnosi architetturale e proposta V3

Analisi offline in sola lettura dei quattro grafi finali C12
([script](analysis/record_block_causes_20260926.py), [dati](analysis/record_block_causes_20260926.json)),
commit `a699f6f`. Dei 304 record non esclusi del ledger, duplicati inclusi,
57 sono pubblicati; 156 sono bloccati da motivi meccanici del compilatore
(citazione non identica, anchor, regole lessicali, accounting ridondante, schema),
67 da catene parziali dichiarate dalla fonte e 24 da contenuto dubbio. Sono i
motivi dichiarati dal compilatore, non un giudizio semantico. Graco p. 11 è letta
da 7 chiamate di estrazione. Da B1 a C12 le review crescono su tutti i manuali.

La nuova architettura V3 ([docs/PIANO_V3.md](../docs/PIANO_V3.md)) è implementata
in `backend/kg_v3/` ed è il generatore PDF predefinito. Due esecuzioni per manuale
sui quattro manuali di sviluppo ([risultati](../docs/V3_RISULTATI_SVILUPPO.md),
[artifact](experiments/v3_dev_20260926/)): gold storico lessicale Eastman 4 e 5/8
contro 4/8 della v22, Danfoss 8/8 contro 5/8, Graco 16/18 contro 16/18; domande
rimaste per una persona 0–1 per manuale contro 26–157 segnalazioni; tempi da 5 a
13 volte inferiori. Sono misure di sviluppo sui manuali usati per costruire il
sistema, con gold non validato da tecnici: non sono risultati per il paper. Costo
cumulativo del registro: 2,0138 USD su 20.

Misura rivista per posizione e significato (giudice LLM a tre voti, gold storico
riscritto come segmenti e controllato dall'agente, non da tecnici): v22 contro V3
con codice corretto (r3, r4) Eastman 6 contro 7/8, Danfoss 5 contro 8/8, Graco 17
contro 18/18. Corretto un bug di fusione dei nodi che in r2 faceva perdere azioni.
Preparata la revisione cieca della precisione in `evaluation/v3_precision_review/`
e il foglio di conferma dei 34 casi in `evaluation/gold_segments_v1/CONFERMA_GOLD.md`.

Gold dei 34 casi rivisto da Fabio Daniele (revisore unico, autore del sistema).
Dopo le correzioni sulle procedure numerate, per significato: v22 24–26/34, V3
r5 34/34 e r6 33/34 (Eastman 8 e 7/8, Danfoss 8/8, Graco 18/18). Misure di
sviluppo sugli stessi quattro manuali: non trasferibili a manuali nuovi. Questa analisi non modifica codice del generatore, gold o
ledger e non effettua chiamate API.

## Stato dell'arte e posizionamento

Nota critica in [STATO_ARTE_E_POSIZIONAMENTO.md](STATO_ARTE_E_POSIZIONAMENTO.md), basata
sull'analisi completa [state_of_the_art_maintenance_kg.md](state_of_the_art_maintenance_kg.md):
i componenti della V3 hanno precedenti (Fonduer, CoAnnotating, AEVS, FlowExtract e altri);
il contributo difendibile è empirico: preservazione dei rami a parità di copertura, sforzo
umano reale a parità di qualità, trasferimento tra produttori. Da ottenere prima della
scrittura: Liu e Lu 2024 e gli alberi di troubleshooting ICPHM 2024/2025. Protocollo della
campagna approvato: [evaluation/PROTOCOLLO_V3.md](evaluation/PROTOCOLLO_V3.md), un solo
annotatore, tetto di 10 USD. Solo i numeri della fase di test potranno entrare nel paper.

## Campagna V3, fase A (sviluppo esteso)

[Rapporto](../campaign/results/REPORT.md). Gold annotati a mano da Fabio Daniele per sette
manuali; gli ID del gold Trane (test) sono stati ricollegati e verificati riga per riga dopo
una lettura del PDF fatta fuori flusso. Tre manuali di sviluppo (ABB ACS580, Grundfos Paco,
Lincoln POWER MIG), tre esecuzioni V3 e una v22 per manuale, due correzioni strutturali con
test. Recall micro dei rami con il codice finale: V3 446/561 (IC95 0,760–0,826), v22 1/187;
per manuale ABB 2–8/19, Grundfos 136–141/146, Lincoln 2–7/22. Nessun manuale raggiunge il
90% e ABB resta instabile per la mappa. Misure di sviluppo, non trasferibili ai manuali di
test. Precisione non ancora misurata: foglio cieco in attesa di Fabio. Costo del registro
della campagna 0,876 USD su 10. Codice congelato con il tag `v3-freeze-2026-09-27` per la
fase C; nessuna esecuzione sui quattro manuali di test.

Decisione di Fabio: Trane eliminato; Atlas Copco, Graco GTX e Haas diventano di sviluppo.
Sei manuali con il codice del tag: recall micro dei rami V3 682/900 (IC95 0,729–0,785),
v22 19/300. Atlas Copco, Graco GTX e Haas sono stati eseguiti per la prima volta con il codice
già congelato e nessuna correzione deriva da loro: su questi tre V3 239/339 = 70,5% (IC95
0,654–0,751), v22 18/113. Sono la prova su manuali mai visti disponibile oggi; da ora sono
di sviluppo, quindi solo queste prime esecuzioni restano valide come tali. Tabelle stabili
al 70–95%; mappa instabile (Haas r2 1/45). Spesa 1,231 USD.

Livello 1 (commit `5f94c6a`): mappa letta due volte con pagine confermate protette, separazione
delle relazioni con nomi giudicati diversi, rimedi delle celle unite verificati riga per riga,
cause dedotte ammesse ma marcate come non scritte (scelta di Fabio). Sei manuali, tre esecuzioni:
V3 da 682 a 732/900 rami (81,3%, IC95 0,787–0,837). Numeri di sviluppo: le correzioni derivano
da tutti e sei i manuali. Spesa 2,196 USD su 10.

Pulizia del codice (2026-09-27, richiesta di Fabio): rimossi la pipeline v22, l'applicazione web e
il frontend; resta la sola pipeline V3 con gli strumenti della campagna. Ultimo commit con il
codice precedente: tag `legacy-v22`. I grafi v22 già salvati nella campagna restano come confronto;
non si possono più generare nuove esecuzioni v22 senza tornare a quel tag. Le versioni fissate in
`requirements.txt` (PyMuPDF 1.28.0, openai 2.44.0) sono ora quelle usate per gold ed esecuzioni.

## Robustezza V3, fasi 1–2

[Report C→D](../campaign/results/REPORT.md): F1–F7 e metriche oltre il gold implementati;
18 run congelati a `8abec90`, originali preservati in `runs_C`. Con lo stesso giudice
aggiornato: 733→684/900 rami; fusioni vietate 8→0, cause orfane 34→35. Sui soli rami
con azioni: 260→209/396. Il controllo dei PDF trova ancora fusioni semantiche e contesti
errati: accettazione non raggiunta. Tutti i manuali sono sviluppo; precisione cieca
ancora non misurata, 61 contrasti da rivedere e nuovo foglio di 108 voci non compilato.
Atlas D/r3 è vuoto ma automaticamente approvato: correzione successiva `bec1e7c`,
verificata su replay controllato delle stesse risposte (34/49 rami), distinta dal confronto
D e non sostituita al fallimento. Spesa aggiuntiva 1,113197 USD entro 5 autorizzati;
116 test e Ruff verdi. Nessun risultato trasferito al codice finale o al test indipendente.

Iterazione E (2026-09-28): completezza dei rami con quattro correzioni dopo la code review. Stesso
valutatore prima e dopo: rami 669 → 736/900 (81,8%, IC95 0,791–0,842), nessuna esecuzione vuota,
fusioni vietate 0; cause orfane in aumento (35 → 53) e costo per esecuzione da circa 1,5 a 3–11
centesimi. Numeri di sviluppo. Primo manuale di test in preparazione: Grizzly G0872 (gold da
annotare prima di qualsiasi esecuzione). Spesa 5,929 USD su 10.

Primo manuale di test, Grizzly G0872 (tag `v3-freeze-2026-09-28`, gold chiuso prima delle esecuzioni):
91/186 rami (48,9%, IC95 0,418–0,561) su tre esecuzioni. Tabelle di troubleshooting 85–94%; i rami
sparsi nelle pagine di manutenzione restano quasi tutti fuori perché la mappa non sceglie quelle
pagine. 0,07–0,10 USD e 3–4 minuti per esecuzione. Spesa 6,342 USD su 10.

Protocollo aggiornato (decisione di Fabio): valutazione a rotazione. Ogni manuale nuovo si misura una
volta con il codice congelato (primo contatto) e poi diventa di sviluppo; nel paper la qualità su
manuali nuovi si dichiara solo con i numeri di primo contatto, più una verifica finale su 3–5
manuali tenuti da parte. Grizzly G0872 è il primo della serie.

Secondo primo contatto, LG LMH2235ST (stesso tag): 69/222 rami (31,1%, IC95 0,254–0,374). La mappa legge
quasi tutte le pagine; perdite sui diagrammi di flusso (12–13/35) e sui test dei componenti (0–4/18),
con molte cause scollegate dal sintomo. Spesa 7,075 USD su 20.

Iterazione F (2026-09-28/29): scansione del testo intero per le pagine con conoscenza diagnostica,
unità per diagramma, verificatore che legge il passaggio (con immagini delle pagine a diagramma),
regole per bivi e test. Stesso valutatore, sei manuali giudicati: rami 351 → 390/723 (48,5% → 53,9%,
IC95 0,503–0,575); pagine gold lette Grizzly 6–8 → 18/20, ABB 7–8 → 11/11; cause orfane LG 37–50 →
10–16 ma in aumento sugli altri; fusioni vietate 0. Costo per esecuzione ×2–3,5 (ABB 0,25 USD).
Atlas Copco e Grundfos non giudicati per il tetto di spesa. Da ora Grizzly e LG sono di sviluppo;
restano validi i loro numeri di primo contatto. Precisione dei collegamenti nuovi non misurata:
foglio cieco 3 da compilare. Spesa 12,813 USD su 20 (tetto dell'iterazione alzato da Fabio a 13,0).
