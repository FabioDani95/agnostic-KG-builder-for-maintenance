# Prompt per proseguire la robustezza dell'estrazione

Documento di passaggio operativo, basato sugli artifact C7/C8 del 26 settembre
2026. Le priorità seguenti sono lavoro proposto; i numeri descrivono gli artifact
indicati e vanno ricontrollati se il repository è cambiato.

## Richiesta da eseguire

Lavora nella repository:
`/Users/fabio.daniele/Coding/agnostic-KG-builder-for-maintenance`.

Prosegui l'implementazione già autorizzata. L'obiettivo è estrarre conoscenza
diagnostica corretta e completa, con un grafo leggibile e catene che conservino
sintomi/codici, componenti, possibili guasti, condizioni, ispezioni, azioni e prove
documentali. L'ontologia in `ontology_schema.JSON` deve restare invariata.
Le informazioni diagnostiche tipizzate che il contratto conserva nei metadati
devono rimanere collegate ai rami e consultabili. Non inventare anelli mancanti:
una catena è completa rispetto a ciò che il documento dichiara.

Sono accettabili casi dubbi da sottoporre a tecnici. La revisione deve avvenire
dopo i controlli e i tentativi automatici di recupero pertinenti, prima della
pubblicazione del contenuto dubbio. Errori di parsing, locator recuperabili e
duplicazioni non devono diventare sistematicamente lavoro umano. Il tecnico
deve poter correggere un singolo caso, con nuova revisione tracciata e nuova
validazione. Nessuna approvazione deve eludere il contratto ontologico o le prove.

Accetto più tempo e costo per migliorare la qualità. Il cap API già autorizzato
è **20 USD cumulativi**, inclusi confronti, retry, fallimenti ed escalation.
Non è un nuovo budget: usa lo stesso ledger
`paper/experiments/robustness_20260925/real_call_budget.jsonl`.
L'ultima contabilizzazione prudenziale è 1,343788355 USD, con 482 tentativi
chiusi; controlla il ledger effettivo e le prenotazioni prima di spendere.
Prepara e congela ciascun confronto prima delle chiamate. Non occorre una nuova
approvazione per proseguire entro questo perimetro già autorizzato.

Non fermarti a un altro piano o al superamento dei test unitari. Procedi per
incrementi verificabili, documenta anche insuccessi e regressioni. La validazione
del gold da parte di tecnici resta un'attività umana: non dichiararla completata
da un agente e non usarne l'assenza per rimandare le correzioni tecniche possibili.

## Prima di modificare

Leggi AGENTS.md e le istruzioni applicabili, poi:

- `paper/WRITING_GUIDELINES.md`, `paper/STATUS.md`, `paper/AGENTS.md`;
- `paper/evaluation/PROTOCOL.md`;
- `paper/ANALISI_PIANO_ROBUSTEZZA_ESTRAZIONE.md`;
- `paper/experiments/robustness_20260925/REPORT.md`;
- `paper/experiments/robustness_followup_20260926/REPORT.md` e
  `analysis/MEASUREMENTS.md`, `analysis/results.json` nella stessa cartella;
- `paper/evaluation/gold_review_v1/README.md`;
- `paper/manuals/registry.json` e i PDF pertinenti.

Verifica Git: HEAD era `528f069`, ma la pipeline attuale è nel working tree con
molte modifiche e file nuovi non committati. **HEAD non rappresenta lo stato
attuale.** Preserva tutto, in particolare `docs/README.md` e
`docs/PIPELINE_SPIEGAZIONE_IT.md`. Congela anche file non tracciati necessari,
configurazione e dipendenze. Non cancellare artifact o gold; non mescolare
refactoring cosmetico e correzioni funzionali. Verifica che nessun altro processo
stia modificando la stessa checkout prima di avviare una campagna.

L'ultima sorgente congelata è
`paper/experiments/robustness_followup_20260926/source_c8.tar.gz`, versione
`pdf-g3-structured-recovery-v19`. Confrontala con il working tree, senza
sovrascriverlo. I documenti storici sono evidenze da valutare, non specifiche
automaticamente corrette.

## Stato reale da cui partire

Hypertherm C8 è un replay delle risposte del nuovo run C7; non una seconda
estrazione indipendente. Il grafo è in
`paper/experiments/robustness_20260925/replays/c8r1_hypertherm_powermax30_air/graph.json`.
Il run reale sorgente è `runs/c7_hypertherm_powermax30_air/` nella stessa campagna.

Rispetto a C6: rami nel grafo 10 → 17; review 117 → 111; record irrisolti
89 → 93; occorrenze di condizioni 35 → 29. Restano duplicati: 17 rami non
significa 17 catene uniche, complete e corrette. Tutti i grafi rimangono non
approvabili. La baseline B1 aveva 25 rami e 89 review, ma controlli ed estrazione
sono diversi: nessuno di questi confronti misura da solo la qualità semantica.

Le 111 voci Hypertherm comprendono 70 review di record diagnostici, 21 ambiguità
di canonicalizzazione, 7 gap, 6 guasti senza componente e 7 altre segnalazioni.
79 sono bloccanti. Voci di review, candidati e rami sono unità diverse.
Tra i motivi di rigetto del compilatore figurano 38 supporti degli estremi non
stabiliti, 30 citazioni incompatibili con l'anchor, 29 abbinamenti strutturalmente
ambigui e 17 candidati senza disposizione. Questi motivi si sovrappongono:
non sommarli come casi indipendenti.

605 test passano e 3.604 riferimenti Hypertherm superano il controllo letterale
canonico. Questo non certifica il significato dei collegamenti o la completezza.
Il recupero locale degli anchor aggiunto in C8 si applica a zero casi nei quattro
replay: non ha mostrato un beneficio empirico in questa campagna.

Sono già presenti archivio raw/usage, validazione per record, recupero di errori
strutturati, prove degli estremi, conservazione di layout e metadati diagnostici.
Studia questi meccanismi prima di duplicarli. Restano soprattutto problemi di
ricostruzione semantica, completezza, identità e recupero dopo il compilatore.

## Interventi in ordine di dipendenza

1. **Rendere misurabile la perdita.** Produci un inventario delle 111 voci con
   collegamenti a record, occorrenze sorgente, rami e pagine. Distingui errori
   tecnici, contesto mancante, omissioni, duplicati, informazione non dichiarata
   e ambiguità reale. Conserva le voci originali e i collegamenti molti-a-molti;
   fornisci anche conteggi di casi unici senza sovrapposizioni. Per ciascuna
   famiglia rilevante identifica causa verificata, esempio PDF, funzione,
   informazione persa e controllo che ne dimostri il recupero.

2. **Ricostruire contesto e rami verificabili.** Concentrati su tabelle con
   intestazioni ereditate, alternative causa/soluzione, continuazioni e procedure
   multipagina. Parti dai casi Hypertherm delle pagine fisiche 67–69 e Test 9
   nelle pagine 96–104, verificando i riferimenti e la pagina 228 ove pertinente.
   Conserva prerequisiti, ordine dei passi, rimandi, condizioni AND/OR e polarità.
   Il “no” a una domanda congiunta non equivale automaticamente a negare ogni
   sua parte. Il numero uguale di punti elenco non prova il loro abbinamento.
   Valuta se la struttura serve al recupero ma il compilatore non riesce ancora
   a rappresentarne la prova: non ridurre il problema a cambiare il prompt.
   La pagina 228 ha ancora un limite di lettura del diagramma; verifica rendering
   e risorse OCR/visive prima di attribuirle copertura.

3. **Recupero semantico mirato ed escalation.** Per i candidati recuperabili
   prepara pacchetti con contesto sorgente, errore preciso e schema immutato.
   Confronta configurazioni/modelli sugli stessi pacchetti; congela il confronto
   e verifica prezzi/documentazione ufficiale prima di nuove chiamate. Confronti
   precedenti non hanno mostrato un vantaggio uniforme del modello più capace.
   Riesegui soltanto ciò che richiede nuove risposte. Ogni recupero passa gli
   stessi controlli e conserva provenienza e rami validi precedenti.
   Esamina `_diagnostic_report_score` e `_prefer_escalated_diagnostic_report`
   in `backend/services/ontology_workflow.py`: la preferenza per più record
   pubblicabili è un'euristica, non una verifica semantica. Una sostituzione non
   deve perdere rami corretti o vincere producendo duplicati.

4. **Identità e duplicati.** Affronta le 21 ambiguità distinguendo varianti
   lessicali, componenti diversi, rami diversi e duplicati della stessa
   occorrenza. Conserva codici, condizioni e provenienza. Accorpare notifiche
   duplicate è utile per la UI, ma va misurato separatamente dal recupero di
   conoscenza. Non fondere alternative per somiglianza del testo.

5. **Rendere operativo il gate umano.** Attualmente
   `backend/routers/subgraphs.py` e `frontend/app/graph.js` espongono soprattutto
   approvazione/rifiuto complessivi. Implementa correzione/disposizione del
   singolo record, fonti affiancate, cronologia e ricompilazione in nuova
   revisione. Mantieni i blocchi residui. Distingui lacune dichiarate dalla fonte,
   problemi tecnici ed effettive decisioni interpretative. Il tecnico deve
   poter decidere con evidenze sufficienti, senza ricostruire errori del backend.

Moduli principali da esaminare oltre a quelli citati: `backend/adapters/pdf.py`,
`diagnostic_record_windowing.py`, `ontology_pipeline.py`,
`diagnostic_bundle_compiler.py`, `diagnostic_reconciliation.py`,
`diagnostic_recovery.py`, `diagnostic_publication_service.py` nei servizi,
e lo schema dei record in `backend/domain/diagnostic_bundles.py`.

## Gold e coinvolgimento dei tecnici

Per Hypertherm esiste **soltanto il perimetro preparato**, non un gold annotato e
validato: 37 pagine radice 65–77, 82–104 e 228, con 78–81 come contesto.
I moduli A/B sono `unannotated`, con `branches: []`. Non chiamarli gold pronto.
Le quattro note in
`paper/experiments/robustness_followup_20260926/hypertherm_source_notes_for_adjudicator.json`
sono proposte di un agente già esposto alle predizioni: non indipendenti, non
gold, non input per generatore/scorer.

Prepara una procedura concreta per i tecnici: annotazioni indipendenti delle
sezioni selezionate, decisione sui disaccordi, versioni e motivazioni.
Puoi produrre proposte sorgente per agevolare il lavoro, ma separale dai moduli
indipendenti e dichiara l'esposizione alle predizioni. Non certificare lavoro
umano non svolto. Verifica criticamente anche i 34 casi storici contro i PDF;
eventuali correzioni devono essere motivate dalla fonte, mai dalla predizione.
Il gold storico originale va preservato.

## Verifica e criteri di completamento

Definisci prima dei nuovi run perimetro, denominatori e criteri locali di
accettazione. Non fissare un obiettivo arbitrario “111 → N” né chiamare robusto
un sistema che respinge tutto. Per ogni incremento riporta:

- rami unici autonomi corretti e completi rispetto alla fonte, con stati non
  ancora giudicati separati;
- relazioni non supportate, mescolamenti tra rami e perdita di condizioni,
  ispezioni o ordine dei passi;
- correttezza letterale dei locator e supporto semantico, misurati separatamente;
- casi unici rimasti all'uomo, motivo, azione richiesta e utilità della review;
- costo totale inclusi retry/escalation, tempi e confronti con la baseline.

Per i casi auditati, ogni “recupero riuscito” deve avere prova sul PDF e nessuna
relazione inventata. Conserva i rami già giudicati corretti; documenta eventuali
regressioni. Precisione e recall globali restano non disponibili finché manca
un riferimento adeguatamente validato. Non confondere match lessicali, record
contabilizzati e catene autonomamente corrette.

Esegui test significativi e confronti prima/dopo sugli stessi candidati quando
possibile. Usa `scripts/recompile_diagnostic_candidates.py` per probe limitati;
non chiamarli replay end-to-end. Usa `scripts/replay_extraction_experiment.py`
soltanto quando le richieste originali coincidono, con rete bloccata. Cambi di
prompt, schema o contesto richiedono nuove estrazioni per una verifica reale.
Usa runner/ledger esistenti e output nuovi, senza sovrascrivere le baseline.

Dopo aver dimostrato un beneficio sui pacchetti, riesegui tutti e quattro i
manuali con sorgente/configurazione congelate e budget disponibile; controlla
anche Eastman, oggi 4/8 nel probe storico contro 5/8 della baseline B1.
Separa effetto del codice, del modello e variabilità tra esecuzioni. Prevedi
repliche mirate invece di scegliere la risposta migliore come risultato.

Consegna implementazione, test, artifact riproducibili, analisi dei risultati
negativi e positivi, aggiornamento di STATUS/WORKPLAN e una spiegazione semplice
di cosa è migliorato e cosa resta ai tecnici. Il successo è documentale e
semantico: non il solo numero dei test, dei nodi o delle voci eliminate.
