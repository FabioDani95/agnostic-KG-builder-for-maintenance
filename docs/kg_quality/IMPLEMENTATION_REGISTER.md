# Registro di implementazione K00–K11

Consegna software del 1 ottobre 2026. Registro storico conservato per tracciabilità. I piani di implementazione che lo precedevano sono stati rimossi dalla documentazione attiva; i comandi correnti sono in [README.md](README.md). Stato `DONE` significa implementazione integrata e accettazione offline; non significa beneficio estrattivo misurato. K12 non è incluso nella richiesta K00–K11 e non è stato eseguito. Nessuna chiamata API a pagamento; autorizzazione di spesa assente. P1 resta opt-in, default `base_safe`; P2 non implementato.

## Pacchetti e dipendenze

| Pacchetto | Stato | Dipendenze rispettate | Implementazione ed evidenza |
| --- | --- | --- | --- |
| K00 | DONE | — | Snapshot iniziale, versioni e stato concorrente in `baseline/baseline_manifest.json`, sorgenti in `baseline_source.tar.gz`, 202 test baseline; probe packaging/geometria; verifica degli input congelati e dei 24 grafi F. Checkout B0 completo con hash per file. |
| K01 | DONE | K00 | `reader.py`, adapter PDF, `extractor.py`, `checker.py`, `contracts.py`: bbox e origini celle, prove esatte, candidati senza prova conservati, AUTO escluso dai testimoni semantici. T01–T03, T12. |
| K02 | DONE | K00–K01 | `run_state.py`, `run.py`, `questions.py`, CLI: manifest, envelope con checksum, revisioni, lock unico, scritture atomiche, cache e decisioni sul contenuto. Legacy in sola lettura; costi e provenance cumulativi. T16–T20, T24, T27, T29–T30. |
| K03 | DONE | K01–K02 | `quality_contracts.py`, `source_index.py`, `coverage.py`, mapper: catalogo immutabile, prove atomiche, scope e ID documentali; menzioni isolate e inventari PARTIAL; ownership e contesto separati. T03–T08, T12, T24, T28. |
| K04 | DONE | K03 | Schema e prompt con catalogo consentito, binding per ruolo, epistemic status, azioni distinte, inferenze con premesse, verifica indipendente per chiamata. T01, T03, T07–T10, T15; controesempi checker esistenti. |
| K05 | DONE | K04 | Merge conservativo con prove di entrambi i lati, vincoli transitivi, concetti e istanze locali; `diagnostic_paths` su occorrenze pubbliche e scope compatibili. T05–T06, T10–T11, T23–T24, T27. |
| K06 | DONE | K03–K05 | `export.py`: sidecar `kg-ingestion-quality-1`, proiezione `kg-v3-graph-2`, hash aciclici e loader; visual-only, stale e `not_projected` espliciti. `load_certified_graph` filtra le occorrenze pubbliche. T13, T21, T23, T26; regressioni export/UI esistenti. |
| K07 | DONE | K04–K06 | `coverage.py`, `omissions.py`, orchestratore: coda unica, audit riservato, delta riverificati e atomici, due round massimi, idempotenza, failed/deferred e lineage. T04, T19–T20, T25, T29; end-to-end recupero e budget simulato. |
| K08 | DONE | K05–K07 | `references.py`, indice e navigation: resolver documentale, retrieval locale, contesto in sola lettura, richieste unificate da riferimenti e anomalie. Ambiguità conservate; nessuna riconnessione costituisce prova. T06, T14, T25, pagina stampata ambigua. |
| K09 | DONE | K01, K03–K08 | Inventario layout e router prima della mappa, regioni native con crop/hash, percorsi visuali, verifica sulle immagini. Risposte di routing/layout salvate prima del parsing. T09, T13–T15, T26, T29; domande visuali aperte per revisore solo testuale. |
| K10 | DONE | K02–K09 | `validation.py`, `run.py`, CLI: integrità finale e pubblicazione, approvazione del contenuto, profili validati e preflight senza provider; report separa processing, workflow, review e qualità. End-to-end tabella, prosa, OCR incerto, visual-only, resume e rifiuto umano. |
| K11 | DONE | K00, K06, K10 | Scorer nuovo separato, proiezione gold, obblighi, matching, campionamento pesato e bootstrap appaiato; runner con 12 condizioni × 8 manuali × 3 repliche = 288 run preparati. Budget esplicito e ledger assoluto comune anche a B0; fonti, configurazioni e runner verificati prima di eseguire. T22, T25 e test contrastivi scorer/campagna. |
| K12 | TODO | K00–K11, budget e giudizi | Nessuna estrazione reale di questa versione né promozione. Mancano autorizzazione di spesa, allineamenti/adjudication e giudizi di supporto. Non sono riportate misure di miglioramento. |

Gli artefatti della tabella sono sotto `experiments/kg_quality_implementation/`. La campagna finale autorevole è `evaluation_plan_final/`; `evaluation_plan/` è un preflight di pianificazione precedente alla correzione del ledger e non è eseguibile contro i sorgenti finali. Nessun manifest precedente è stato riscritto per attribuirgli il codice nuovo.

## Accettazione T01–T30

Le fixture di modello sono risposte programmate. I casi LG/ABB/Lincoln di ramo, continuazione e codici sono controesempi equivalenti sintetici; non sono nuove estrazioni o annotazioni dei manuali. `test_kg_v3_quality_sources.py` aggiunge controlli locali sui PDF reali Grizzly/LG/Lincoln, con SHA congelati: verifica locator e testo letterale, senza misurare accuratezza estrattiva.

| Casi | Test/evidenza |
| --- | --- |
| T01 | `test_t01_empty_citations_never_gain_proof`, una/due letture e AUTO; motivo conservato. |
| T02 | `test_t02_real_adapter_geometry_reaches_crop`: PDF generato → adapter → reader → crop. |
| T03, T08 | `test_t03_t08_conditions_and_action_kinds_are_distinct`; locator reali Grizzly/Lincoln. |
| T04 | `test_t04_row_cite_is_not_three_actions_and_delta_is_idempotent`; run `table_primary_only`/`table_completeness`. |
| T05 | `test_t05_branch_local_failures_and_no_cross_branch_paths`; omonimi in rami diversi. |
| T06 | `test_t06_cross_page_context_requires_path`; titolo lontano non autorizza scope da solo. |
| T07 | `test_t07_expected_values_do_not_validate_an_invented_failure`; valori normali nel locator LG reale. |
| T09 | `test_t09_literal_conflict_quarantines_statement`; nessuna inversione di esito implicita. |
| T10 | `test_t10_codes_remain_distinct`, parametrizzato su codici e zeri. |
| T11 | `test_t11_merge_needs_sources_from_both_sides`; regressioni merger su differenze numeriche/transitive. |
| T12 | `test_t12_inherited_cells_have_origin`; aggiunta fixture numerata con indicatore condiviso. |
| T13, T15, T26 | `test_t13_t15_t26_visual_only_pipeline_and_projection`, verificatore supported/not_supported; PDF raster con zero testo nativo, rich/proiezione e resume. |
| T14 | `test_t14_all_seven_regions_split_or_explicitly_deferred`; nessuna regione scompare dal cap. |
| T16 | `test_t16_answers_are_bound_to_one_branch`; conferma applicata a una sola occorrenza. |
| T17, T27, T30 | `test_t17_t27_t30_approval_is_content_bound`; workflow stabile, contenuto cambiato invalida approvazione, identità originale dopo naming/concetto. |
| T18 | `test_t18_resume_rejects_semantic_dependencies`: PDF, modello, contesto, prompt, OCR; checksum alterato respinto. |
| T19 | Lock unico/audit cap; `test_t19_exhausted_budget_is_persisted_and_not_retried_identically`; regressioni gateway retry/timeout/budget. |
| T20 | `test_t20_repair_cannot_override_human_reject` e `test_t20_changed_proof_needs_a_new_exact_human_decision`; conferma agente insufficiente, precedente rifiuto preservato. |
| T21 | `test_t21_legacy_is_read_only_and_stale_projection_is_unverified`; loader preserva i byte storici. |
| T22 | Scorer `test_t22_common_fact_satisfies_two_verified_applicabilities`; un fatto/due obblighi e matching massimo. |
| T23 | `test_t23_path_uses_occurrence_not_aggregate_tier`; giallo escluso dal percorso certificato. |
| T24 | `test_t24_stable_ids_when_reads_reversed_or_labels_change`; ID indipendenti da ordine ed etichette. |
| T25 | `test_t25_no_delta_does_not_mean_complete`; scorer con output vuoto e campagna con run mancante. |
| T28 | Ownership atomica/contesto senza duplicati e `test_t28_context_action_cannot_be_emitted_from_cause_only_child`. |
| T29 | Revisioni/checksum, crash dopo commit delta e crash del catalogo visuale; risposte già completate non richieste di nuovo. |

Sono incluse anche quattro combinazioni end-to-end prosa/OCR × verifier supported/not_supported con export e resume senza chiamate; test di replay esatto, configurazioni e congelamento runner/B0, e budget comune con subprocess simulati.

## Verifiche e conservazione

- Suite iniziale offline: **202 passed**; checkout B0 isolato: **35 passed** sui test pipeline/reader/checker. La baseline è stata eseguita con import dal checkout congelato e configurazione pytest separata.
- Suite di consegna offline: **289 passed, zero failed/error/skipped**; dettagli `delivery_tests.xml` e `delivery_tests.txt`. Cinque warning preesistenti delle classi SWIG PyMuPDF.
- Ruff sui file backend/CLI/test interessati: `lint_delivery.txt`; controllo whitespace del diff autorizzato.
- Preflight finale del PDF Grizzly con `quality_v1`: `preflight_final/`, esito READY, provider che rifiuta ogni chiamata.
- Conservazione: `preservation_delivery.json`, **25.716 file protetti senza differenze** e **24/24 grafi F** conformi; nuovo manifest di consegna con hash. Nessuna scrittura di questa implementazione su frontend/help/editor, backend UI, gold, `TESTO.md`, paper o artefatti storici. Le modifiche concorrenti restano di proprietà del loro autore.

## Esempi prima/dopo dei contratti

`offline_examples/examples_manifest.json` raccoglie grafi e manifest nuovi. Sono **simulazioni**, con zero chiamate API e `quality_measured=false`; “prima” indica il medesimo generatore simulato prima della revisione opzionale, non la baseline F.

| Caso | Prima/assenza della capacità | Risultato della fixture |
| --- | --- | --- |
| Completezza/tabella | La lettura simulata emette solo inspection dalla cella con tre azioni. | La revisione simulata aggiunge repair/escalation, controllate separatamente; tre fatti pubblici, nessun duplicato. Budget review simulato esaurito conserva un fatto e lacune. |
| Ramo | Due cause omonime in righe diverse. | Due istanze locali; i rimedi esclusivi non diventano collegamenti fra rami. |
| Geometria | Probe iniziale: bbox adapter presente, bbox reader assente. | Test PDF nativo propagato fino al crop; origini delle celle unite conservate. |
| Visual-only | Zero segmenti testuali nel PDF raster. | Verificatore simulato positivo: due fatti ricchi, zero archi storici e proiezione EMPTY/incomplete. Verificatore negativo: zero fatti pubblici. La simulazione non prova che un modello reale interpreti correttamente l'immagine. |
| Inferenza | Proposta di causa non letterale, con premessa documentale. | Conserva status/premesse; verificatore negativo impedisce pubblicazione, positivo simulato non diventa una misura di precisione. |

## Scelte conservative e limiti residui

L'inventario semantico è osservato/PARTIAL; liste e clausole riconosciute strutturalmente non equivalgono a tutti i fatti della fonte. Scope e continuazioni non verificati restano provvisori. Limiti di pagine/immagini, ambiguità del resolver, OCR incerto, immagini mancanti e modelli non disponibili producono gap/backlog; non si allentano i vincoli per aumentare i verdi.

Il modello del ruolo può riusare il primario: le chiamate sono distinte, l'indipendenza statistica non è dimostrata. Non è stata verificata la disponibilità online dei modelli. La stima di campagna è cautelativa, non un cap o un'autorizzazione. Run reali richiedono budget valido e ledger comune; il replay accetta soltanto richieste esatte e non passa alla rete su miss.

Per i gold con condizioni testuali ambigue o componenti non adjudicati, la proiezione segnala esclusioni e mantiene gli originali intatti. Le predizioni extra-gold non giudicate sono UNJUDGED. Metriche di supporto, router, merge/split, minuti umani e promozione restano non misurate; sono necessari nuovi run e annotazioni separate. Nessun risultato F è trasferito al codice nuovo. Gli scorer storici e i loro test sono preservati.

Il supplemento è un'estensione della V3, non un secondo orchestratore. Le domande visuali sono disponibili negli artefatti backend senza modifiche del frontend. Il checkout B0 ha recuperato i soli moduli di supporto mancanti dal medesimo HEAD originale, registrandone hash e provenienza; non contiene patch della nuova pipeline. P2 (embedding, parsing generale delle frecce, consenso, estensione ontologica, cache tra run) resta fuori dal perimetro.

I file effettivamente toccati da questa implementazione sono elencati con hash in `delivery_manifest.json`; i comandi validati sono in [README.md](README.md).
