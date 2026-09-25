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
| Il nuovo modello riduce il costo del sistema a pari qualità | Prezzi unitari ufficiali inferiori; nessuna nuova campagna | Ipotesi; misurare token, retry, qualità e revisione |
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
- Nuova estrazione reale, nuovi gold, risultati comparativi e studio downstream: non eseguiti.
- Manoscritto: struttura e prima sezione; non ancora un draft completo circolabile.

Per ogni nuova campagna aggiungere un riferimento al manifest, all'output grezzo,
al gold versionato e al report generato. Non sovrascrivere questi risultati
storici e non riclassificare retroattivamente un campione di sviluppo come test.

## Preparazione del corpus

Creato `manuals/registry.json` con 4 documenti storici da riconciliare ai PDF
e 12 slot nuovi da selezionare. Responsabilità e criteri in `manuals/README.md`.
Nessun nuovo manuale è stato acquisito o annotato in questo passaggio.
