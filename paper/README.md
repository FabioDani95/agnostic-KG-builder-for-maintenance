# Maintenance knowledge graph paper

Questa cartella è la sede di lavoro del paper nella repository. I documenti sono
versionabili con il codice; gli output delle campagne restano separati e vengono
richiamati attraverso manifest con hash e configurazioni. Nessun risultato nuovo
è implicito nella creazione del manoscritto.

## Percorso di lettura

1. [Linee guida](WRITING_GUIDELINES.md): regole permanenti per scrittura e revisione.
2. [Stato ed evidenze](STATUS.md): cosa possiamo sostenere e cosa manca.
3. [Piano per deliverable](WORKPLAN.md): dipendenze e criteri di completamento.
4. [Protocollo sperimentale](evaluation/PROTOCOL.md): gold, confronti e metriche.
5. [Manoscritto](manuscript.md): struttura del primo draft.
6. [Perché un grafo](sections/02_maintenance_graph_rationale.md): prima sezione in prosa con fonti.
7. [Bibliografia](references.bib) e [mappa delle fonti](SOURCES.md).
8. [Migrazione modello](MODEL_DECISION.md): GPT-6 Luna, compatibilità e verifiche.

Le istruzioni per gli assistenti sono in [AGENTS.md](AGENTS.md), richiamate anche
dalla radice della repository. Funzionano nei client che supportano AGENTS.md;
negli altri ambienti occorre fornire esplicitamente le linee guida al contesto.

Il file originale fornito dall'autore è conservato senza modifiche in
[reference_material](reference_material/EU_proposal_writing_guidelines.original.md).
È un riferimento storico, non una seconda serie di regole attive.

## Decisione editoriale di lavoro

Articolo metodologico con valutazione industriale della costruzione di grafi
per la diagnosi documentale. *Computers in Industry* è un candidato da discutere
con i coautori, non una destinazione già decisa. Il contributo proposto riguarda
la conservazione delle relazioni diagnostiche e delle evidenze, la gestione delle
lacune e il costo di ottenere un grafo verificabile. La sola combinazione LLM e KG
non è sufficiente come novità.

Il primo draft circolabile richiede metodo stabilizzato, risultati verificabili,
limiti espliciti e una discussione dell'utilità a valle. Si può scrivere subito
l'introduzione e il metodo; abstract quantitativo e conclusioni seguiranno le misure.

## Corpus e assegnazioni

Il [registro dei manuali](manuals/README.md) propone 4 manuali di sviluppo e
12 nuovi documenti per il test, con responsabilità e stato di selezione.

## Evidenze correnti

La [continuazione C9–C12](experiments/robustness_continuation_20260926/REPORT.md)
documenta v22, quattro manuali verificati, gate di correzione per record e replay.
La [riproduzione](experiments/robustness_continuation_20260926/REPRODUCE.md) distingue
run completi, verifiche incrementali e prove offline. Qualità semantica globale,
completezza e riduzione del lavoro umano restano non dimostrate; i moduli gold
A/B sono ancora non annotati. Per l'uso applicativo partire dallo
[stato PDF corrente](../docs/PDF_DIAGNOSTIC_STATUS.md).

## Prima campagna reale, conservata come storico

[Report delle quattro estrazioni](experiments/dev_luna_20260925/REPORT.md) e
[problemi osservati](experiments/dev_luna_20260925/OBSERVATIONS.md).
