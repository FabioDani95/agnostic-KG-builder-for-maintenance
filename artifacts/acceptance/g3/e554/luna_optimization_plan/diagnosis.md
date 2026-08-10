# Diagnosi verificata della pipeline PDF G3

## Esito decisionale

La run Luna ha raggiunto la copertura diagnostica richiesta, ma il grafo resta rumoroso perché la pipeline ottimizza il richiamo durante l'estrazione e verifica solo una parte delle proprietà necessarie alla pubblicazione. Gli 8/8 gold e gli 0/3 pairing vietati dimostrano che le catene desiderate sono presenti; non dimostrano che ogni nodo estratto sia diagnostico, connesso, distinto e precisamente grounded.

La causa dominante è quindi nella pipeline, non nella capacità generale del modello. Luna contribuisce a near-duplicate, classificazioni ambigue e due relazioni causalmente non grounded, ma nessun modello più forte può correggere da solo questi comportamenti deterministici:

- il prompt ordina di estrarre anche componenti e istruzioni standalone;
- le pagine di inventario componenti vengono reinserite deliberatamente nello scope;
- la normalizzazione crea relazioni strutturali e `AFFECTS` senza quote;
- la finalizzazione conserva nodi standalone anche se non completano una catena;
- la strict validation non vieta nodi isolati, azioni scollegate o catene incomplete;
- il payload finale perde la quote e l'anchor specifiche della relazione;
- gap e review queue non sono costruiti sul grafo effettivamente pubblicabile.

Non è stata effettuata alcuna chiamata OpenAI per questa diagnosi. La revisione `sgrev_OR8HyabEt7ntt0Z00LZEoA` è stata letta in modalità SQLite read-only, ha ancora zero decisioni e deriva ancora lo stato `reviewing`.

## Evidenze e perimetro

Sono stati letti integralmente i documenti di baseline richiesti, il payload immutabile della revisione e il codice effettivo di scoping, EvidenceUnit, chunking, estrazione, finalizzazione, canonicalizzazione, grounding, strict validation, gap, review queue, API e UI. Le misure complete riproducibili sono in `offline_graph_analysis.json`; lo script che le genera è `read_only_graph_analysis.py`.

Stato misurato dalla revisione immutabile:

| Metrica | Valore | Stato |
|---|---:|---|
| pagine totali / selezionate | 54 / 30 | misurato |
| pagine diagnostiche 37–39 | 3/3 presenti | misurato |
| sezioni / chunk | 32 / 19 | misurato |
| chiamate / token totali | 96 / 832.562 | misurato |
| durata / costo | 444,69 s / $0,320466 | misurato, costo persistito |
| nodi / relazioni / evidenze | 399 / 369 / 346 | misurato |
| nodi isolati | 33 | misurato |
| sintomi con percorso completo | 39/46 | misurato |
| FailureMode in percorso completo | 52/68 | misurato |
| CorrectiveAction senza FailureMode | 28/89 | misurato |
| componenti coinvolti in percorsi completi | 29/195 | misurato |
| relazioni core grounded nel controllo pre-adapter | 172/174 | misurato |
| item review queue | 250 | misurato, pre-adapter e non persistito |
| gold / pairing vietati | 8/8 / 0/3 | misurato, solo accettazione |

Sono presenti 35 FailureMode con almeno un `AFFECTS` nell'intero grafo. Il valore 26 è invece il numero di FailureMode che hanno sia un percorso diagnostico completo sia un componente: 26/52 tra quelle complete, non 26/68 nell'intera popolazione. La distinzione non cambia la diagnosi: `AFFECTS` è assente per metà delle FailureMode complete e resta correttamente opzionale secondo l'ontologia.

## Perché 8/8 gold convive con un grafo sporco

Il test gold è un test di richiamo su otto percorsi specifici. Il grafo può contenere tutte quelle catene e, contemporaneamente, contenere centinaia di elementi che il test non penalizza. La run corrente ne è una dimostrazione misurata:

- 33 nodi non hanno alcuna relazione;
- 7 sintomi non arrivano a un'azione;
- 11 FailureMode non hanno un sintomo in ingresso;
- 5 FailureMode non hanno un'azione in uscita;
- 28 azioni non risolvono alcuna FailureMode;
- 166 dei 195 componenti non sono coinvolti in un percorso diagnostico completo;
- almeno otto coppie/gruppi hanno una somiglianza lessicale o morfologica che richiede canonicalizzazione contestuale.

Il gold non deve essere ampliato fino a diventare una regola di produzione. Deve rimanere un controllo cieco post-run, insieme a invarianti ontologiche e topologiche generiche.

## Root cause precise

### 1. Lo scope mescola tre ruoli diversi

`backend/prompts/scoping_prompt.py:83` e lo scoring di `backend/services/cutplan_service.py` privilegiano troubleshooting, manutenzione, ispezione, calibrazione, ricambi e diagrammi nello stesso insieme di pagine. `backend/services/scoping_workflow.py:556` reinserisce poi le pagine riconosciute come inventario componenti anche se il filtro linguistico le aveva escluse.

Questa politica massimizza il richiamo documentale, ma usa lo stesso scope per tre attività semanticamente diverse:

1. estrazione diagnostica;
2. inventario strutturale dei componenti;
3. retrieval di supporto per completare una catena già identificata.

Nella run, le pagine 40–50 di blueprint/inventario sono state ripristinate. Questo spiega una parte consistente dei 195 componenti e delle 195 `HAS_COMPONENT`, ma non è corretto eliminarle dal grafo canonico: devono alimentare la proiezione strutturale, non la vista diagnostica predefinita.

### 2. Il contratto è node-first e prescrive sovra-estrazione

`backend/prompts/ontology_prompt.py:1` richiede tutti i tipi ontologici e consente componenti ed errori standalone; include inoltre parti, installazione e manutenzione. Sebbene descriva una `CorrectiveAction` come restaurativa, non impone che nasca insieme a una `RESOLVED_BY` esplicita e grounded.

La conseguenza è visibile nei 28 nodi `CorrectiveAction` isolati. Tra gli esempi misurati vi sono controlli periodici, pulizia preventiva, calibrazioni generiche, installazione, sicurezza e lockout. Queste frasi possono essere istruzioni valide del manuale, ma non sono `CorrectiveAction` nell'ontologia corrente finché non esiste una FailureMode esplicita che esse risolvono e la relazione non è supportata dalla fonte.

Il problema non richiede un nuovo tipo ontologico. Le istruzioni non diagnostiche possono restare evidenze documentali o candidati esclusi; se in futuro si desiderasse rappresentarle come entità, servirebbe una proposta di estensione ontologica separata.

### 3. Il chunking moltiplica contesto e varianti

`backend/services/ontology_workflow.py:_split_pages_by_section` partiziona correttamente le pagine fisiche una sola volta, ma effettua un flush ogni volta che cambia la firma delle sezioni. Con 32 sezioni sovrapposte su 30 pagine produce 19 chunk. Ogni chunk passa attraverso draft, relazione, validation ed eventuale re-extraction.

La run ha effettuato:

- 2 chiamate di scoping;
- 19 draft;
- 18 estrazioni di relazioni;
- 29 validation;
- 10 re-extraction;
- 1 coverage completion;
- 17 resolution completion.

Il totale di 96 chiamate non è necessario per mantenere la copertura. La segmentazione per unità causale o riga di tabella e un contratto relation-first possono eliminare i passaggi generalizzati di relazione/validator/re-extraction, lasciando validation deterministica e completion mirata.

### 4. Il merge globale deduplica solo ID o nomi esatti

`backend/services/ontology_workflow.py:_merge_pipeline_results` non usa una canonicalizzazione semantica cross-chunk: unisce per ID e, in pratica, per normalizzazione esatta. Le funzioni type-specific già presenti in `backend/services/ontology_semantics.py` (`symptoms_match`, `failure_modes_match`, `corrective_actions_match`) non vengono applicate come fase globale del PDF.

Il controllo offline trova zero duplicati esatti normalizzati, ma molte coppie lessicali candidate. Non tutte vanno fuse: per esempio il contenimento tra un assieme e una sua parte è una relazione di specificità, non sinonimia. La canonicalizzazione deve quindi richiedere stesso tipo, compatibilità semantica, contesto materiale e vicinato/evidenza compatibili. I casi incerti vanno in un'unica adjudication batch o in review, mai fusi solo per token containment.

### 5. La normalizzazione e la closure creano relazioni senza claim evidence

`backend/services/ontology_pipeline_coercion.py:_normalize_ontology_instance` deriva `HAS_COMPONENT` e `GENERATES_ERROR` e può inferire `AFFECTS` per corrispondenza semantica lasciando evidenza vuota. `backend/services/graph_closure_service.py:close_grounded_gaps` propone anch'esso `AFFECTS` da similarità/co-occorrenza e crea quote vuote.

Nella run, la closure ha segnato 52 `AFFECTS` applicate su 188 considerate, ma l'adapter elimina poi relazioni o endpoint non risolvibili. È lavoro costoso e semanticamente debole. `AFFECTS` deve essere pubblicato soltanto quando il testo dichiara il componente coinvolto; la sua assenza non deve invalidare una catena diagnostica completa.

### 6. Il grounding verificato prima dell'adapter non sopravvive nel contratto persistito

`backend/services/evidence_grounding_service.py:ground_relation_evidence` ha misurato 172/174 relazioni core grounded e due non grounded. Tuttavia `backend/domain/subgraphs.py:SourceGraphRelation` conserva soltanto `evidence_ids`. In `backend/services/pdf_source_subgraph_generation.py:PdfSourceSubgraphBuilder._to_revision` la quote e l'anchor specifiche prodotte dall'estrazione vengono scartate.

Inoltre l'adapter:

- assegna ai link derivati l'unione delle evidenze degli endpoint;
- propaga poi le evidenze delle relazioni incidenti nei nodi;
- usa fuzzy grounding per nodi standalone.

Effetto misurato: l'Asset canonico riferisce 319 delle 346 EvidenceUnit; i componenti hanno fino a 50 evidenze e le `HAS_COMPONENT` fino a 50. Tutti gli ID risultano risolvibili, ma molti non provano la singola affermazione. La validazione di risolvibilità referenziale è quindi necessaria ma non sufficiente per il requisito del 100% grounded.

La correzione è conservare per ogni relazione una `RelationEvidenceRef` operativa con `evidence_id`, quote esatta e anchor risolvibile. Questo è metadata di provenance, non un nuovo attributo ontologico. L'Asset deve usare l'EvidenceUnit di asserzione operatore già disponibile nel repository, non l'unione dell'intero manuale.

### 7. La strict validation verifica forma, non pubblicabilità diagnostica

`backend/services/source_subgraph_generation.py:_strict_validation` verifica tipi, proprietà, endpoint, unicità dell'Asset, ownership strutturale e risolvibilità degli ID. `backend/services/ontology_pipeline_validation.py:_validate_schema` emette soltanto un warning quando un'azione non è restaurativa.

Non esistono invarianti bloccanti per:

- zero nodi isolati;
- ogni sintomo pubblicato con percorso a un'azione;
- ogni codice errore pubblicato con percorso a un'azione;
- ogni `CorrectiveAction` con una `RESOLVED_BY` in ingresso;
- quote e anchor claim-specific per ogni relazione;
- separazione tra componenti strutturali e diagnostici.

Per questo la strict validation può passare formalmente su un grafo che non soddisfa gli obiettivi di pubblicazione.

### 8. Completion e reasoning lavorano su target troppo ampi

`backend/services/resolution_completion_service.py:build_resolution_targets` seleziona ogni FailureMode priva di azione, anche se non è raggiunta da un sintomo o da un ErrorCode. Nella run ha lanciato 17 chiamate separate e ne ha completate 11. Questo aumenta costo e tende a trasformare procedure generiche in rimedi.

La completion deve essere attivata solo per FailureMode raggiunte da `MAY_INDICATE` o `INDICATES`, raggruppare target che condividono contesto ed eseguire retrieval sull'intero manuale senza ampliare lo scope di estrazione primaria. Se non trova una quote causale/remediativa, deve produrre un gap target-specific e non una relazione.

### 9. Gap e review queue non rappresentano il risultato pubblicabile

`backend/services/pdf_source_subgraph_generation.py` aggrega i gap usando `(code, evidence_ids)`. Poiché molti problemi hanno `evidence_ids=[]`, più target collassano nello stesso record: `pdf_graph_orphan: 1` è infatti un record aggregato, non un nodo solo.

`backend/services/review_queue_service.py:build_review_queue` costruisce 250 item prima dell'adapter e del gate finale, ma la queue non è persistita nel contratto della revisione. La UI non può quindi mostrare in modo affidabile il target, la disposizione (`publish`, `gap`, `exclude`, `merge`) o la ragione finale.

Il gap deve avere almeno un riferimento operativo target-specific (`target_kind`, `target_id`, `stage`, `blocking`, `disposition`) fuori dall'ontologia. La queue va ricostruita dopo canonicalizzazione, grounding e publication gate, deduplicata per problema effettivo e persistita con la revisione.

### 10. API e UI espongono un solo grafo e confondono incompletezza con catena

`backend/routers/subgraphs.py` espone snapshot, generazione e decisione, ma non proiezioni. `frontend/app/graph.js` costruisce una sola mappa. La vista catene mostra anche FailureMode senza origine o azione come placeholder; `TIPI_TOCCATI` conosce solo vecchi codici gap, perciò i nuovi `pdf_*` con evidenza vuota non attivano il filtro; alcuni redraw tornano sempre alla mappa invece di rispettare la vista attiva.

La UI deve usare set di ID di proiezione del medesimo grafo canonico:

- `diagnostic`: soltanto catene complete e i componenti esplicitamente coinvolti;
- `structural`: Asset, Component e `HAS_COMPONENT` grounded;
- `canonical`: unione pubblicabile senza duplicazione delle entità.

Le catene incomplete vanno mostrate nella vista gap/review, non come catene complete.

## Quanto dipende dal modello

Non è metodologicamente corretto assegnare una percentuale senza un'ablation controllata sullo stesso input e contratto. Le prove consentono però una separazione causale netta.

**Responsabilità dimostrata della pipeline:** scoping promiscuo, obbligo di estrarre standalone, chunk fragmentation, merge exact-only, inferenza `AFFECTS` senza quote, completion troppo ampia, perdita della relation evidence, validazione topologica incompleta, aggregazione dei gap e presentazione UI. Questi risultati sono deterministici o contrattuali.

**Responsabilità osservata del modello:** varianti lessicali cross-chunk, classificazione di alcune ispezioni/procedure come azioni, due relazioni core non grounded, 10 re-extraction richieste. Questi errori vanno ridotti con un contratto più vincolante e una canonicalizzazione globale; solo le ambiguità residue giustificano escalation selettiva.

Gli 8/8 gold, gli 0/3 pairing vietati e i replay fixture con recall 1,0 indicano che Luna è adeguato come modello principale. Sostituirlo globalmente con un modello dieci volte più costoso non risolverebbe i difetti deterministici e non è giustificato da una prova quantitativa.

## Prova offline della direzione proposta

Una proiezione deterministica dei soli claim esistenti che partecipano a percorsi completi produce:

| Proiezione simulata | Nodi | Relazioni | Isolati | Sintomi completi | Azioni scollegate | Componenti | Gold | Vietati |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diagnostica completa | 174 | 175 | 0 | 39/39 | 0 | 29 | 8/8 | 0/3 |
| strutturale | 196 | 195 | 0 | n/a | n/a | 195 | n/a | n/a |
| unione canonica pubblicabile | 340 | 341 | 0 | 39/39 | 0 | 195 | 8/8 | 0/3 |

Queste sono simulazioni sul grafo Luna esistente, non previsioni del numero di nodi che una nuova estrazione produrrà. Dimostrano però che la separazione in proiezioni e il gate di completezza possono rimuovere il rumore dalla vista diagnostica senza perdere nessuna catena gold. Tutte le 334 EvidenceUnit referenziate dall'unione sono risolvibili; il 100% di grounding claim-specific resta **non dimostrabile sul payload esistente** perché quote e anchor delle relazioni non sono persistite.

Il gate sintetico manual-agnostic è passato in 5/5 casi: catena valida, esclusione di sicurezza/preventiva/installazione, catena incompleta trasformata in gap, percorso via ErrorCode e `AFFECTS` opzionale. I test di regressione offline sono 79/79 passati; il replay mock delle nove fixture golden mantiene recall medio 1,0 e schema 9/9.

## Conclusione

La direzione corretta non è un pruning cieco né un cambio globale di modello. È un'architettura ibrida:

1. scope a ruoli distinti;
2. estrazione diagnostica relation-first;
3. canonicalizzazione globale type-aware;
4. retrieval/completion mirato solo per catene avviate;
5. gate deterministico che pubblica solo claim completi e grounded oppure li trasforma in gap;
6. tre proiezioni dello stesso grafo ontologico;
7. escalation forte solo per un batch di ambiguità residue, entro preflight di costo.

Questa diagnosi non ha modificato codice applicativo, revisioni, decisioni, CSV o merge.
