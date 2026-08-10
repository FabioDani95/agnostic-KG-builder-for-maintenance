# Piano di accettazione e soglie go/no-go

## Principio

L'implementazione è accettabile solo se migliora precisione topologica e provenance senza ridurre copertura. Gli 8 gold sono un test cieco post-run; le regole di produzione devono passare anche fixture eterogenee e casi sintetici che non contengono E-554.

Le soglie sono separate in:

- **hard gate:** un fallimento implica no-go;
- **operational target:** un superamento richiede analisi e approvazione esplicita, ma non rende falsa un'invariante ontologica;
- **osservazione:** metrica da registrare senza soglia inventata.

## Hard gate sul grafo pubblicabile

| Area | Soglia | Metodo |
|---|---:|---|
| gold E-554 | 8/8 | evaluator post-run, mai importato dalla produzione |
| pairing vietati | 0/3 | evaluator post-run |
| Asset canonico | 1/1, ID e proprietà esatti del workspace | confronto con repository Asset/operator assertion |
| tipi e proprietà | 100% schema-valid | strict validation |
| domain/range | 100% validi | schema runtime |
| endpoint | 100% esistenti e canonici | graph validation |
| nodi completamente isolati nel canonico | 0 | grado totale |
| Symptom pubblicati con percorso completo | 100% | reachability `MAY_INDICATE` + `RESOLVED_BY` |
| ErrorCode pubblicati con percorso completo | 100% | `GENERATES_ERROR` + `INDICATES` + `RESOLVED_BY` |
| FailureMode pubblicate con indicatore | 100% | ingresso da Symptom o ErrorCode |
| FailureMode pubblicate con azione | 100% | uscita `RESOLVED_BY` |
| CorrectiveAction senza FailureMode | 0 | ingresso `RESOLVED_BY` |
| relazioni con evidence ID risolvibile | 100% | lookup EvidenceRepository |
| relazioni con quote non vuota e verificata | 100% | normalized substring nell'EvidenceUnit |
| relazioni con anchor risolvibile | 100% | page/block/table-cell/offset resolver |
| relazioni causalmente/semanticamente sufficienti | 100% pubblicabili | validator deterministico + review solo per incerte |
| `AFFECTS` inferiti da sola co-occorrenza | 0 | provenance/support-role audit |
| duplicati esatti normalizzati | 0 | canonicalization audit |
| duplicati confermati ad alta confidenza | 0 | candidate adjudication audit |
| projection ID dangling | 0 | subset check sul canonico |
| componenti strutturali nella diagnostica senza `AFFECTS` | 0 | projection invariant |
| componenti canonici persi dalla vista strutturale | 0 | structural projection check |

Un candidato sintomo/causa/azione incompleto può esistere nell'envelope come gap target-specific, ma non può essere presentato come catena completa. Questo soddisfa il requisito senza creare nodi isolati nel grafo pubblicabile.

## Hard gate di provenance

La validazione deve distinguere quattro numeratori/denominatori per relation type:

1. evidence ID risolvibile;
2. quote presente;
3. quote trovata nella EvidenceUnit;
4. anchor risolvibile e coerente con la quote.

Tutti devono essere 100% per le relazioni pubblicate. Il rapporto storico 172/174 non è sufficiente e il rapporto 346/346 sugli ID non va riutilizzato come proxy del claim grounding.

Per `HAS_COMPONENT` e `GENERATES_ERROR`, una evidence ref `derived_structural` è valida soltanto se la quote sostiene direttamente che il componente/codice appartiene o si riferisce all'Asset. La sola unione dell'evidenza degli endpoint non vale.

## Hard gate delle proiezioni

### Diagnostica

- contiene soltanto nodi appartenenti a percorsi completi;
- include Component soltanto come endpoint di un `AFFECTS` pubblicato;
- tutte le catene visualizzate hanno origine e azione;
- mantiene 8/8 gold e 0/3 vietati;
- zero isolati.

### Strutturale

- contiene l'Asset canonico, tutti e soli i Component canonici grounded e le relative `HAS_COMPONENT`;
- zero duplicazioni fisiche dei payload: usa gli stessi ID del canonico;
- zero componenti orfani;
- non richiede `AFFECTS`.

### Canonica

- è l'unione per ID delle due viste più eventuali catene ErrorCode complete;
- zero isolati;
- ogni ID delle proiezioni appartiene al canonico;
- nessun nodo viene copiato con ID diverso per apparire in due viste.

Il proxy offline Luna da usare come regression oracle topologico è:

| Vista | Nodi | Relazioni | Isolati | Sintomi completi | Azioni scollegate | Gold/vietati |
|---|---:|---:|---:|---:|---:|---:|
| diagnostica simulata | 174 | 175 | 0 | 39/39 | 0 | 8/8 · 0/3 |
| strutturale simulata | 196 | 195 | 0 | n/a | n/a | n/a |
| canonica simulata | 340 | 341 | 0 | 39/39 | 0 | 8/8 · 0/3 |

Questi numeri non sono soglie rigide per una nuova estrazione: un estrattore corretto può trovare più o meno claim. Sono un oracle di non-regressione per il gate applicato esattamente al payload Luna congelato.

## Knowledge gap e review queue

### Hard gate

- zero gap bloccanti riferiti a un nodo o arco pubblicato;
- zero gap senza `target_kind`/`target_id`, salvo un summary esplicitamente marcato come aggregato;
- zero collisioni di target causate da `evidence_ids=[]`;
- zero item `open` senza evidence/disposition verificabile;
- zero item della queue che si riferiscono a entità eliminate o ID pre-canonicalizzazione;
- queue persistita e ricostruibile dal payload.

### Codici minimi da testare

- `diagnostic_missing_failure_mode`;
- `diagnostic_missing_corrective_action`;
- `diagnostic_indicator_missing`;
- `unlinked_or_noncorrective_action`;
- `relation_quote_missing`;
- `relation_quote_not_found`;
- `relation_anchor_unresolved`;
- `canonicalization_ambiguous`;
- `schema_or_domain_range_invalid`.

I nomi possono essere adeguati alle convenzioni del progetto, ma devono rimanere generici e target-specific.

### Operational target

La review queue finale deve avere **≤30 item target-specific**, nessuno bloccante. Il valore è un target operativo, non una previsione misurata: la baseline di 250 è pre-adapter e include warning ripetitivi; il grafo Luna contiene 51 target topologici unici prima delle disposition deterministiche. Se il risultato è >30, fermare l'approvazione e produrre il breakdown per stage/reason prima di decidere.

Registrare sempre gap per codice e disposition, anche quando il totale è zero.

## Deduplica

### Test obbligatori

1. plurale/singolare con stesso contesto: merge;
2. differenza solo di casing/punteggiatura: merge;
3. alias compatibile con stesso vicinato: merge o adjudication;
4. assieme vs sua parte: non merge;
5. generico vs specifico non provato: non merge;
6. azioni con verbi opposti: non merge;
7. FailureMode con condizioni operative diverse: non merge;
8. stesso testo ma material context incompatibile: non merge;
9. merge che produce self-loop/domain error: reject;
10. rimappatura che tocca una catena gold: catena ancora presente.

### Soglie

- exact normalized duplicate groups: 0;
- confirmed safe candidates lasciati separati: 0;
- uncertain candidates: consentiti solo come `canonicalization_ambiguous` in queue;
- false merge nei test contrastivi: 0.

Non fissare come soglia “fondere almeno otto gruppi”: gli otto osservati sono candidati di accettazione/manual audit, non verità di produzione.

## Test offline prima di qualsiasi API reale

### Suite esistenti e nuove

Eseguire in ordine:

1. unit test domain/repository e backward compatibility;
2. scoping multi-ruolo;
3. EvidenceUnit batching/table row/anchor;
4. relation-first prompt contract con mock;
5. canonicalizzazione e property tests;
6. retrieval/completion found/not-found;
7. grounding per ogni relation type;
8. publication gate e proiezioni;
9. gap/review queue target-specific;
10. API serialization;
11. UI unit/e2e;
12. replay mock delle fixture;
13. replay offline del payload Luna congelato;
14. gold E-554 solo nell'evaluator.

Baseline già eseguita in questa attività:

- 79/79 pytest mirati passati, 0 failure/error/skip (`pytest_offline.xml`);
- 9/9 fixture mock schema-compliant, recall medio 1,0 (`golden_mock_replay/.../report.json`);
- 5/5 casi sintetici del publication gate passati (`synthetic_publication_gate_results.json`).

Dopo l'implementazione, tutte queste suite devono restare verdi e le nuove suite devono avere 0 failure.

### Casi sintetici manual-agnostic

Mantenere almeno:

- pompa con catena e componente;
- macchina con istruzioni preventive/safety/installazione non correttive;
- conveyor con sintomo/cause senza rimedio trasformati in gap;
- controller con ErrorCode e catena completa;
- sistema con catena valida e `AFFECTS` assente.

Aggiungere:

- catena distribuita tra celle di tabella;
- rimedio su pagina diversa trovato via retrieval;
- quote presente ma anchor errato;
- componente parent/child vicino lessicalmente;
- due manuali con vocaboli diversi ma stesso pattern ontologico.

## Audit di ontologia

Hard gate:

1. diff di `ontology_schema.JSON` vuoto, salvo proposta separata esplicitamente approvata;
2. set dei node type prodotti sottoinsieme dei type configurati;
3. set delle relation type prodotte sottoinsieme delle relazioni configurate;
4. ogni domain/range letto dallo schema runtime, non duplicato in euristiche produttive;
5. `AFFECTS` opzionale nei test;
6. metadata di proiezione/provenance/gap non copiati nelle proprietà ontologiche;
7. una `CorrectiveAction` esiste soltanto come range di `RESOLVED_BY` nel pubblicabile.

Se si desidera in futuro rappresentare manutenzione preventiva, sicurezza o installazione, aprire una ADR/proposta ontologica distinta con migrazione e acceptance dedicate. Non è parte del presente go-live.

## Audit di agnosticismo e gold blindness

### Static audit hard gate

Nei file di produzione modificati non devono comparire:

- `E-554` o varianti;
- `Eastman`, `Eagle S3L` o l'asset ID;
- numeri di pagina della baseline come condizioni;
- label/termini delle otto catene gold;
- mapping speciali per produttore, modello, macchina o dominio.

Sono consentiti soltanto nei test/evaluator e negli artefatti di acceptance.

### Dynamic audit hard gate

- 5/5 casi sintetici verdi;
- 9/9 fixture mock schema-compliant;
- recall medio fixture non inferiore a 1,0 della baseline mock, oppure ogni eventuale differenza spiegata da un oracle aggiornato e approvato prima del test reale;
- 0 violazioni forbidden definite dalle fixture;
- stesso publication gate eseguito senza branch per fixture/manuale.

### Code review checklist

- le regole leggono dominio/range dallo schema;
- classificano il ruolo dell'evidenza, non vocaboli di una macchina;
- i retrieval query sono costruiti dal target estratto, non da termini gold;
- il modello forte riceve soltanto candidati/evidenze, non risposte attese;
- l'evaluator gold non è importato da package di produzione.

## Budget, chiamate e durata

### Hard cost gate per la nuova pipeline

- forecast conservativo prima della run ≤ $0,35;
- costo effettivo della generation completa ≤ $0,35;
- nessuna chiamata opzionale se il suo ceiling porta il forecast oltre $0,35;
- ledger completo senza chiamate non attribuite;
- nessun retry manuale;
- durante il benchmark di accettazione, chiamate seriali;
- al massimo un batch Terra;
- al massimo una full generation reale.

### Operational targets

| Metrica | Target | Sensitivity corrente |
|---|---:|---:|
| costo atteso | vicino a $0,30 e preferibilmente ≤$0,35 | $0,226350 centrale; $0,301724 conservativo |
| chiamate | ≤28 | 21–28 E |
| token totali | ≤610.000 | 339.458–609.010 E |
| durata | ≤365 s | 187,276–360,392 s E |

Il costo è il gate hard; chiamate/token/durata sono target operativi perché dipendono da cache, layout e provider. Qualsiasi superamento deve essere spiegato per fase.

## Protocollo per l'unica eventuale run reale post-implementazione

Nessuna run reale va eseguita durante la fase di piano. Dopo approvazione e implementazione:

1. completare tutti i test offline;
2. creare workspace/source/output sperimentali separati;
3. non leggere/scrivere decisioni della revisione Luna baseline;
4. preparare ledger con budget residuo, pricing, max input/output, retry massimi e ceiling per ogni fase;
5. impostare retry manuali a zero e includere ogni retry automatico consentito nel ceiling; preferibilmente disattivarli per il benchmark;
6. verificare che il worst-case dell'intera run sia entro il budget residuo e il preflight di $0,35;
7. eseguire chiamate seriali;
8. aggiornare ledger dopo ogni chiamata con token/costo effettivi;
9. prima di ogni chiamata opzionale, ricalcolare worst-case residuo;
10. se il ceiling non è garantibile, non chiamare e conservare i target come gap;
11. non fare retry manuali, CSV, merge, approve/reject o rigenerazione della baseline;
12. generare il report completo delle metriche richieste.

Il budget di questa attività è attualmente intatto: $0,00 consumati e $0,50 residui.

## Report obbligatorio della run di accettazione

Per baseline, nuovo canonico e ogni proiezione registrare:

- nodi totali e per tipo;
- relazioni totali e per tipo;
- isolati per tipo;
- sintomi completi/incompleti;
- ErrorCode completi/incompleti;
- FailureMode senza indicatore, azione o componente;
- CorrectiveAction senza FailureMode;
- componenti strutturali e diagnostici;
- grounding per relation type e per ciascuno dei quattro check;
- exact e near-duplicate, inclusi merge/reject/uncertain;
- gap per code, blocking state e disposition;
- review queue per severity/reason;
- 8/8 gold e 0/3 forbidden;
- chiamate per operation/model/effort;
- input, cached input e output token;
- costo per fase e totale;
- durata per fase e totale;
- differenze informative rispetto alla baseline, con evidence witness per ogni catena persa o nuova.

Non riportare un valore se il sistema non lo misura; usare `not_available` e aprire il relativo instrumentation bug.

## Go/no-go per autorizzare l'implementazione

### Go sul piano

Autorizzare l'implementazione se si approvano esplicitamente questi quattro punti:

1. i candidati incompleti possono essere esclusi dal grafo pubblicabile purché persistiti come gap target-specific;
2. i componenti non diagnostici rimangono nella proiezione strutturale dello stesso grafo;
3. provenance/proiezioni/gap/review sono metadata operativi e non estensioni ontologiche;
4. Terra è opzionale, massimo un batch, e viene saltato oltre il preflight.

### No-go sul piano

Non iniziare l'implementazione se si richiede una delle seguenti condizioni incompatibili:

- pubblicare ogni istruzione del manuale come `CorrectiveAction` senza FailureMode;
- considerare “evidence ID risolvibile” equivalente a claim grounding;
- fondere near-duplicate con sola similarità lessicale;
- rimuovere i componenti strutturali dal grafo canonico;
- usare gold, pagine o termini E-554 in produzione;
- affidare a un modello più costoso la sostituzione del gate deterministico.

## Go/no-go dopo l'implementazione

**Go alla singola run reale:** tutte le suite offline verdi, static/dynamic agnosticism audit verde, strict/projection invariants verdi sul replay congelato, forecast worst-case ≤$0,35.

**Go alla proposta di approvazione della nuova revisione sperimentale:** tutti gli hard gate del grafo/provenance/ontologia passano; 8/8 e 0/3; costo effettivo ≤$0,35; zero item bloccanti; queue finale ≤30 oppure eccezione analizzata e approvata; report completo.

**No-go immediato:** perdita di una catena gold, pairing vietato, relazione pubblicata non grounded, Asset alterato, nodo isolato, azione scollegata, schema/domain-range failure, leakage gold/manual-specifico, costo forecast/effettivo oltre soglia o ledger incompleto.
