# Pipeline KG quality

> Questo profilo appartiene alla pipeline V3 ed è conservato come versione di confronto. Nel pilot del
> 1 ottobre 2026 ha misurato meno del profilo base e non è più stato rimisurato. Lo sviluppo continua
> nella pipeline a grafo connesso: vedi [Architecture](../architecture.md) e il
> [piano di test](../test-plan.md).

L'estensione usa la V3 esistente (`Pipeline`, `ModelClient`, `Checker`, `MergedGraph`). Il default è `base_safe`: applica P0 senza attivare le capacità avanzate. `quality_v1.json` attiva esplicitamente scope, revisione, retrieval, merge aggiuntivo e routing visuale. Nessuna estensione P2 è inclusa.

L'implementazione non costituisce una misura di qualità estrattiva. Le fixture offline controllano i contratti; precisione semantica, recall sui manuali e utilità dei recuperi richiedono la nuova campagna e adjudication. I risultati F restano storici e non sono trasferiti a questa versione.

## Preflight e test, senza API

Dalla root del repository:

```sh
.venv/bin/python scripts/test_offline.py -q
.venv/bin/python scripts/kg_v3.py \
  --manual grizzly_g0872 \
  --quality-config docs/kg_quality/quality_v1.json \
  --out experiments/my_quality_preflight \
  --preflight
```

Il preflight legge il PDF e verifica configurazione, ruoli, catalogo e manifest. Non richiede una chiave API e il suo provider rifiuta qualsiasi chiamata. Usare una directory nuova quando cambiano codice, PDF, parser/OCR, ontology, prompt, modello o configurazione semantica. Con input identici, il comando sul medesimo output riprende gli stage completati. Un run storico privo di manifest rimane leggibile e non viene aggiornato.

Per mantenere P1 disattivato, omettere `--quality-config` o usare `docs/kg_quality/base_safe.json`. Per esperimenti singoli si possono disattivare flag nel JSON quality, rispettando `branch_identity` come prerequisito. `max_review_rounds` è limitato a due; il default è 24 richieste logiche, due slot di audit riservati, 18.000 caratteri, sei immagini e quattro pagine per pacchetto. Gli split contabilizzano tutte le prove; i frammenti insufficienti restano nel backlog.

## Replay e run autorizzato

Un replay deve contenere le risposte archiviate alle richieste esatte di questa versione, compresi schema, modelli, effort e immagini:

```sh
.venv/bin/python scripts/kg_v3.py \
  --manual grizzly_g0872 \
  --quality-config docs/kg_quality/quality_v1.json \
  --out experiments/my_quality_replay \
  --replay /percorso/archivio_esatto \
  --gates auto
```

Un miss non raggiunge la rete: il lavoro fallito o differito viene conservato. `auto` approva il workflow, senza fornire un testimone semantico.

Solo dopo una distinta autorizzazione di spesa, un run reale richiede `--authorize-spend`, un `--budget` esplicito e un ledger nuovo, condiviso da tutti i suoi ruoli. Esempio, con il budget autorizzato fornito dall'operatore:

```sh
.venv/bin/python scripts/kg_v3.py \
  --manual grizzly_g0872 \
  --quality-config docs/kg_quality/quality_v1.json \
  --out experiments/my_authorized_quality_run \
  --authorize-spend --budget "$KG_QUALITY_AUTHORIZED_USD" \
  --ledger experiments/my_quality_budget.jsonl \
  --run-id quality_grizzly_r1 --gates interactive
```

Non riutilizzare il ledger storico della campagna. La richiesta di implementazione non autorizza chiamate a pagamento. I campi `review_model`, `verify_model`, `vision_model` e i rispettivi effort sono nel JSON; `null` riusa il modello primario con l'effort del ruolo e registra `same_model_review=true`. Non viene dichiarata indipendenza statistica dei verificatori. La disponibilità online del modello resta da accertare nel run autorizzato; configurazioni non note falliscono senza sostituzioni silenziose.

## Artefatti e query

`ingestion_quality.json`, versione `kg-ingestion-quality-1`, è la vista autorevole con scope, menzioni, istanze, prove, candidati respinti, lineage, copertura e validation. `graph.json` mantiene `kg-v3-graph-2` come proiezione compatibile. Le prove visuali non rappresentabili rimangono nella vista ricca; `not_projected` spiega l'omissione. Una proiezione `EMPTY` non viene pubblicata come `approved`, anche se contiene fatti canonici accettati.

`input_manifest.json`, `state_envelopes/`, `source_index_revisions/` e `artifact_index.json` legano input, cache, revisioni e file tramite hash. L'originale HEAD della cache rimane nel manifest. Modificare la proiezione rende il binding `STALE`; alterare sidecar, manifest, checkpoint o crop viene respinto. Un solo writer possiede il run per tutta l'esecuzione CLI e l'export.

Per leggere i risultati e percorrere solo le occorrenze pubbliche validate:

```python
from backend.kg_v3.export import load_quality, load_certified_graph
from backend.kg_v3.navigation import diagnostic_paths

loaded = load_quality("experiments/my_authorized_quality_run")
graph, index = load_certified_graph("experiments/my_authorized_quality_run")
for node in graph.nodes.values():
    if node.type in {"Symptom", "ErrorCode"}:
        print(diagnostic_paths(graph, index, node.node_id))
```

I grafi storici senza sidecar restituiscono `LEGACY_UNVERIFIED`, `LEGACY_UNKNOWN` e nessuna certificazione nuova. `load_certified_graph` rifiuta grafi legacy o stale. I percorsi non combinano occorrenze gialle con verdi e non trasferiscono rimedi fra guasti omonimi di rami diversi.

`coverage.json` distingue processing e inventario semantico osservato. `REPRESENTED` richiede ruolo, contenuto, prova e applicabilità; una riga citata non soddisfa automaticamente tutte le sue azioni. Inventari `PARTIAL` non certificano completezza globale. `NO_SUPPORTED_DELTA` conserva le lacune. `report.json` separa workflow, processing, validation e review, con consumo aggregato e per ruolo, provenance delle chiamate e backlog. `approved` non significa che tutto il manuale sia stato recuperato.

Domande solo visuali restano aperte quando il revisore disponibile riceve soltanto testo. `quality_review.md` e `questions_for_people.txt` riportano crop, pagina, bbox e hash. Una conferma vale sul fatto, sulle prove e sul ramo mostrati. Un rifiuto umano rimane nello storico; nuove prove dello stesso fatto richiedono una nuova domanda umana.

## Campagna e scorer

La campagna preparata è in `experiments/kg_quality_implementation/evaluation_plan_final/`. Ha otto manuali di sviluppo, tre repliche e B0/Bsafe/S/S+E/S+C/S+V/S+G/ALL e le quattro sottrazioni. La baseline B0 eseguibile è in `experiments/kg_quality_implementation/baseline_executable/`: sorgenti originali dello snapshot e moduli di supporto Python mancanti recuperati dallo stesso HEAD originale. Il wrapper replay rimane fuori dal checkout congelato.

Per preparare una nuova campagna dopo altri cambiamenti:

```sh
.venv/bin/python scripts/kg_v3_quality_campaign.py plan \
  --out experiments/new_quality_campaign \
  --baseline-source experiments/kg_quality_implementation/baseline_executable \
  --manuals abb_acs580_01 atlascopco_drb_booster graco_gtx_2000ex grizzly_g0872 \
            grundfos_paco_vl haas_mill_2023 lg_lmh2235st lincoln_powermig_215mp \
  --conditions B0 Bsafe S S+E S+C S+V S+G ALL ALL-E ALL-C ALL-V ALL-G
```

`plan` legge e congela hash di PDF, info, gold, codice, configurazioni e scorer; non spende. Le stime includono retry e immagini, non sono autorizzazioni o limiti garantiti; il ledger impone il cap reale. Il file `budget_authorization.example.json` è deliberatamente non autorizzato.

```sh
# Esecuzione reale solo con autorizzazione esterna esplicita:
.venv/bin/python scripts/kg_v3_quality_campaign.py run \
  --out experiments/new_quality_campaign \
  --budget-authorization /percorso/autorizzazione_esplicita.json

# Valutazione e report offline, dopo estrazioni e annotazioni:
.venv/bin/python scripts/kg_v3_quality_campaign.py score \
  --out experiments/new_quality_campaign --judgments /percorso/giudizi
.venv/bin/python scripts/kg_v3_quality_campaign.py report \
  --out experiments/new_quality_campaign
```

La campagna non resetta il ledger. `--resume` conserva gli output compatibili; `--score-out` scrive una rivalutazione in una nuova directory senza sovrascrivere giudizi precedenti. Per un singolo run:

```sh
.venv/bin/python scripts/kg_v3_quality_evaluate.py \
  --gold campaign/grizzly_g0872/gold/gold.json \
  --quality-run experiments/my_authorized_quality_run \
  --adjudication /percorso/adjudication.json \
  --judgments /percorso/giudizi.json \
  --out experiments/my_quality_score.json
```

Gold e `TESTO.md` rimangono in sola lettura. L'adjudication separata deve riportare `gold_sha256`; supporta `claim_overrides`, `split_claims` e `branch_alignment`. I mapping espliciti contengono `branch_ids`, `status` ed `evidence`. Senza allineamento verificato, gli obblighi gold rimangono insoddisfatti. Condizioni gold ambigue non vengono interpretate arbitrariamente: sono `NOT_ADJUDICATED`, con conteggi degli esclusi. `AFFECTS` richiede adjudication esplicita. Per B0/Bsafe, `legacy_fact_reviews` e `legacy_branch_alignment` permettono adjudication descrittiva separata, legata a `graph_sha256`, senza inventare certificati nel grafo storico.

Lo scorer usa fatti canonici e obblighi di applicabilità, matching bipartito che massimizza cardinalità e poi obblighi. Mantiene negazioni, codici con zeri, unità, kind e condizioni. Extra-gold non giudicati non sono FP automatici. Precisione con denominatore zero è `null`; output vuoto su gold non vuoto ha recall/F1 zero. P/F1 globali non vengono attribuiti a campioni incompleti o perimetri non esaustivi.

L'output prepara un campione stratificato con probabilità di inclusione per precisione di supporto, distinto dal matching gold. `source_support_sample` contiene i giudizi per fact ID; i rapporti sono pesati con `1/probabilità` e includono limiti per ambigui. `merge_reviews` è separato. `paired_bootstrap` usa cluster documentali, resampling entro strato, seed 1729 e 10.000 repliche predefinite. Minuti umani, accuratezza router, errori semantici di merge/split e altre misure prive di annotazioni restano `null`/non misurate. Il vecchio scorer rimane separato come `historical_branch_score` e non parte implicitamente.

I criteri di promozione appartengono a K12. Quality rimane opt-in finché non sono disponibili estrazioni autorizzate, adjudication, misure di supporto e confronti riproducibili.

Il registro di implementazione, la matrice T01–T30 e i limiti sono in [IMPLEMENTATION_REGISTER.md](IMPLEMENTATION_REGISTER.md). I modelli di annotazione legati agli hash gold sono in `evaluation_plan_final/annotation_templates/`; seguire [ANNOTATION_PROTOCOL.md](ANNOTATION_PROTOCOL.md). Gli esempi in `experiments/kg_quality_implementation/offline_examples/` usano risposte simulate: dimostrano i contratti e non misurano qualità sui manuali.

## Correzioni dopo il pilot del 1 ottobre 2026

Il pilot reale (`experiments/kg_quality_pilot_20261001`) ha mostrato che `quality_v1` perdeva quasi
tutti i rami per difetti di implementazione, non per le idee del piano. Correzioni applicate:

- **Lettura:** le unità di `quality_v1` sono quelle di `base_safe` (stesso raggruppamento, titoli tra
  pagine, immagini delle pagine a diagramma); il modello legge il passaggio in ordine di lettura e cita gli
  ID dei segmenti. In più riceve gli ID delle voci numerate nelle celle (`p51.t1.r2/2.3`) e, solo per le
  pagine senza testo, delle regioni immagine. Prima vedeva frammenti in ordine di hash.
- **Recuperi della V3** di nuovo attivi anche in `quality_v1`: lettura C delle righe scoperte, riferimenti
  numerici, celle unite, riconnessione, nuova lettura delle unità strutturate vuote.
- **Verifica:** stesso prompt di `base_safe` più i campi `scope_verdict` e `source_conflict`; lotti da 10,
  16.000 token in uscita, lotto troncato rifatto a metà invece di perso. Le note libere del verificatore non
  bloccano più il fatto. Il verificatore di `quality_v1.json` usa reasoning `low`, come `base_safe`.
- **Ambito:** prosa, procedure e diagrammi hanno un ambito provvisorio per unità e sezione, verificato dal
  verificatore; tabelle e percorsi visivi conservano ramo per riga/voce. Rifiutati senza appello solo i
  rimedi di un'altra riga di tabella verificata o di un'altra voce numerata allineata.
- **Conflitti della fonte:** solo contraddizioni stampate legate a regioni precise; le ambiguità del lettore
  visivo restano note e non mettono più in quarantena l'intera pagina.
- **Revisore agente:** riceve i ritagli delle domande con immagini; la sua conferma, con citazione del testo
  mostrato, vale come verifica semantica. Le cause segnaposto sono giudicate su problema e rimedio.
- **Revisione di completezza:** una chiamata per unità di lettura con passaggio leggibile, fatti presenti ed
  elementi mancanti; priorità alle azioni mancanti; inventario solo sulle pagine lette.
- **Misura:** lo scorer storico raggruppa i rimedi di una causa per `branch_id`; `record_key` torna a essere
  la provenienza della lettura.

Regressioni in `tests/test_kg_v3_quality_fixes.py`. La qualità estrattiva delle correzioni non è ancora
misurata con nuove esecuzioni reali.

## Mappa del codice del profilo qualità

| Modulo | Ruolo |
| --- | --- |
| `run.py` | Sequenza delle stazioni V3, comune ai due profili; chiama `quality_run` nei punti fissi. |
| `quality_run.py` | Fasi del profilo qualità: client per ruolo, catalogo delle prove, catalogo visivo, copertura, revisione, validazione finale. |
| `source_index.py` | Catalogo delle prove (segmenti, voci di cella, regioni) e collegamento di ogni proposta a prove, ramo e ambito. |
| `visual_catalog.py` | Pagine da leggere come immagine, regioni verificate e percorsi dei diagrammi senza testo. |
| `vision.py` | Immagini di pagina usate da entrambi i profili; verifica visiva opzionale delle tabelle. |
| `coverage.py` | Elementi osservati nelle pagine lette e richieste di revisione, con priorità. |
| `omissions.py` | Revisione di completezza: base (opzionale) e qualità (una chiamata per unità). |
| `validation.py` | Controlli finali obbligatori; definisce le occorrenze pubbliche. |
| `export.py` | `graph.json` storico, file ricco `ingestion_quality.json`, caricatori. |
| `quality_contracts.py`, `run_state.py` | Contratti dati e stato del run con impronte e ripresa. |
