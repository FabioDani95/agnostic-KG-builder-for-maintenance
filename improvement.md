# Improvement Plan — Analisi Estrazioni Batch Automatiche

**Input analizzato:** `output/bfp_a3729e/ontology.json` (Mitsubishi RV-5AS, 71 nodi / 84 relazioni) e `output/vb_series_fanuc_maintenance_manual_ver_1_0/ontology.json` (FANUC 0i MF, 51 nodi / 40 relazioni).
**Contesto:** run full-automatic via [`scripts/run_batch_export.py`](scripts/run_batch_export.py), nessun intervento umano (nessuna approvazione, nessuna validazione HITL).
**Target:** identificare **3 debolezze strutturali** e proporre interventi **mirati** (nuovi agent, modifiche di prompt, regole deterministiche aggiuntive) senza riprogettare la pipeline.

---

## Sommario esecutivo

| Manual | Triplet-only / Ontology-draft | Componenti | ErrorCode | Relazioni con evidence vuota | Problema principale |
|---|---|---|---|---|---|
| FANUC 0i MF | triplet-only (ontology-draft FALLITO: JSON parse error) | **0** | **0** | **40 / 40** (100%) | Fallback path non emette Components/ErrorCode/Evidence |
| Mitsubishi RV-5AS | ibrido (ontology-draft + triplet merge) | 22 | 5 | **21 / 84** (25%) | Nodi duplicati fra i due schemi di ID, FailureMode tautologici |

I due output mostrano **tre classi di errore ricorrenti** che si manifestano in modo aggravato quando si combinano i due percorsi estrattivi.

---

## Problema #1 — Confusione Symptom ⇄ FailureMode (duplicazione tautologica)

### Evidenza concreta

Nel FANUC, per ogni Symptom esiste un FailureMode che ne è solo una **riformulazione lessicale**, spesso con descrizione identica parola per parola:

| Symptom | FailureMode | Descrizione (identica) |
|---|---|---|
| SYM-001 "Damaged parts or tools present" | FM-001 "Tool part damage" | "A part of a tool is damaged." |
| SYM-002 "Window damaged or severely scratched" | FM-002 "Damaged or scratched window panel" | "The window/panel is damaged or severely scratched." |
| SYM-003 "Power problems develop" | FM-003 "Electrical power fault" | "Power problems develop." |
| SYM-010 "Alarm displayed" | FM-012 "Fault present in control" | "A fault occurs." (circolare) |
| SYM-013 "Tool changer gets hung up" | FM-015 "Tool changer pneumatic sequence hung up" | "The tool changer gets hung up." |
| SYM-016 "Arm does not complete grabbing the tool" | FM-017 "Arm did not complete grabbing the tool" | "It most likely had to do with movement of the arm." |

Questo è un fallimento del prompt di extraction ([backend/prompts/extraction_prompt.py:21-29](backend/prompts/extraction_prompt.py:21)): le "FailureMode Rules" definiscono il *cosa non fare* in astratto, ma l'LLM usa comunque la strategia "copia il symptom, cambia il tempo verbale / aggiungi 'fault'". Il validator non accorcia queste coppie perché sono perfettamente coerenti dal punto di vista della struttura.

### Intervento mirato

**1.1 — Nuovo agente advisory: `TypeConsistencyAgent`**

Piccolo LLM critic che per ogni coppia `(Symptom, FailureMode)` connessa da `MAY_INDICATE` valuta:

- **sim_score**: sentence similarity fra `symptom.description` e `failure_mode.description` (Jaccard + embedding opzionale).
- **cause_token_presence**: la description della FailureMode contiene token di causa (`loose`, `broken`, `misaligned`, `dead`, `worn`, `disconnected`, `out of adjustment`, `incorrect`, `dirty`, `saturated`, `depleted`, `cracked`, `overheated`, `obstructed`, `low`, `high`, `exceeds`, `phased incorrectly`, …)?
- **passive_verb_check**: la description della FailureMode contiene verbi che descrivono uno *stato* di un componente (predicato stativo) invece di un *evento osservato* (predicato eventivo)?

Regola: se `sim_score > 0.85` **e** `cause_token_presence == False`, emette issue `severity="error", code="symptom_failure_duplicate"` con `fix_hint` che **propone la riscrittura della FailureMode in forma causale** (o la fusione con un altra FailureMode già presente).

Punti di inserzione: estende [`backend/agents/validation_agent.py`](backend/agents/validation_agent.py) — si aggancia al supervisor dopo `VALIDATION` ma prima di `REFINEMENT`, riutilizzando il reflective loop esistente. Niente nuovo nodo nella phase enum.

**1.2 — Rinforzo del prompt di extraction**

Aggiungere a [`backend/prompts/extraction_prompt.py`](backend/prompts/extraction_prompt.py) una regola esplicita con **due esempi contrastivi** (ne abbondano nei dati reali):

```
### CONTRAST EXAMPLES (how a FailureMode differs from a Symptom)
- Symptom (observable event):  "The tool changer gets hung up."
  FailureMode (stative cause): "Pneumatic solenoid valve stuck open on ATC circuit."  ← NOT "Tool changer hung up"

- Symptom (observable event):  "An alarm is displayed."
  FailureMode (stative cause): "Spindle orient parameter P4031 misconfigured after control reload."  ← NOT "A fault occurs"

A FailureMode MUST name (a) a component or subsystem AND (b) a stative condition (worn, loose, misaligned, dead, disconnected, out of adjustment, phased incorrectly, ...).
If the only failure you can find is a restatement of the symptom in past tense, OMIT it — do not invent one.
```

**1.3 — Rinforzo del re-extraction prompt**

Aggiungere in [`backend/prompts/ontology_prompt.py:190`](backend/prompts/ontology_prompt.py:190) `RE_EXTRACTION_PROMPT_TEMPLATE` l'istruzione esplicita di **non rigenerare coppie tautologiche quando una viene segnalata**: se `issue.code == "symptom_failure_duplicate"`, nella passata successiva la FailureMode deve riformularsi in forma causale **oppure essere eliminata**, mai semplicemente rinominata.

### Metrica di successo

Numero di coppie `sim_score > 0.85 ∧ cause_token_presence = False` → atteso **da ~35% a <5%** delle MAY_INDICATE dopo la modifica.

---

## Problema #2 — Doppio schema di ID e merge non-semantico fra ontology-draft e triplet-extractor

### Evidenza concreta

Nel bfp_a3729e coesistono **due schemi di identificatori non riconciliati**:
- `ontology_draft_agent` → `sym_<descriptive>`, `fm_<descriptive>`, `comp_<descriptive>`, `err_<descriptive>`
- `extraction_agent` → `SYM-001`, `FM-001`, `CA-001`, ...

Risultato: duplicati concettuali che la pipeline non fonde.

| Concetto | ID ontology-draft | ID triplet | Relazione emessa |
|---|---|---|---|
| "Hand conditions not set" | `fm_undefined_hand_condition` | `FM-002` | Entrambi riferiti da MAY_INDICATE separate |
| "Movement across operation range" | `fm_operation_range_limit_reached` | `FM-004` | SYM-tb_buzzer... punta a **entrambi** |
| "Positional deviation" | `sym_movement_points_deviated` | `SYM-001` | Entrambi presenti come nodi distinti |
| "Wear/service life" | — (non estratto) | `FM-005`, `FM-006` | Aggiunti solo dal triplet path, nessuna evidenza |

Inoltre **tutte le 21 relazioni provenienti dal triplet path hanno `"evidence": []`** (sono quelle da riga 1389 in poi di `bfp_a3729e/ontology.json`). Questo rende la Knowledge Graph non-groundable per ~25% delle relazioni.

Nel FANUC il problema è **amplificato**: l'ontology-draft è crashato (`ontology_error: Expecting ',' delimiter: line 1628 column 6`) e il sistema è caduto sul `minimal_fallback` (vedi [metrics.json:199-200](output/vb_series_fanuc_maintenance_manual_ver_1_0/metrics.json:199) → `"export_base": "minimal_fallback"`, `"used_clean_ontology_draft": false`). Il risultato è un'ontologia **senza Component, senza ErrorCode, senza HAS_COMPONENT/AFFECTS/INDICATES/GENERATES_ERROR, con evidence vuota per tutte e 40 le relazioni**.

### Intervento mirato

**2.1 — Upgrade di `ontology_merge_service` con semantic dedup cross-schema**

Modifica in [`backend/services/ontology_merge_service.py`](backend/services/ontology_merge_service.py): prima di inserire un triplet-node con ID sequenziale (pattern `^(SYM|FM|CA)-\d+$`), eseguire una passata di matching contro i nodi già presenti nell'ontology draft:

- normalizzazione lessicale su `name` e `description` (riuso di `backend/services/ontology_semantics.py`)
- se `similarity > 0.82` → **non creare nodo nuovo**, invece **rimap del triplet-ID** al descriptive-ID già presente; propagare il rimap a tutte le relazioni che lo referenziano.
- se `similarity ∈ [0.65, 0.82]` → emettere issue `severity="warning", code="possible_duplicate_merge"` e tenere entrambi (lasciare decisione all'umano in modalità review; in batch automatico: accettare il merge).

Così la coerenza ID è preservata e le relazioni dal triplet path ereditano anche l'evidence del draft.

**2.2 — Allineare il triplet extractor al sistema di ID descrittivo**

Sostituire in [`backend/prompts/extraction_prompt.py:47-51`](backend/prompts/extraction_prompt.py:47) il blocco:

```
### ID Format
- Symptom IDs: SYM-001, SYM-002, ...
```

con lo **stesso schema descrittivo** già documentato in [`backend/prompts/ontology_prompt.py:72-84`](backend/prompts/ontology_prompt.py:72). In parallelo, iniettare nel system-prompt di extraction un **catalogo di ID già esistenti** (dall'ontology draft) in modo che l'LLM possa riutilizzarli invece di crearne di nuovi:

```
## EXISTING ENTITY IDS (reuse these when the concept matches)
{ontology_draft_id_catalog}
```

Questo riduce la creazione di duplicati *alla fonte* invece che in post-merge.

**2.3 — Rendere il triplet extractor produttore di evidence**

Oggi il prompt in extraction_prompt.py richiede `source_page` solo per CorrectiveAction (rigo 34-35). Estenderlo a **ogni riga delle tre tabelle**: aggiungere una colonna `evidence_page` per Symptom e FailureMode, e farla confluire in `evidence` dell'ontology finale. Risolve il bug `evidence: []` sistematico delle 21 relazioni triplet-path.

**2.4 — Hardening del parsing JSON dell'ontology-draft**

Il crash FANUC è dovuto a un output LLM non-JSON-strict (virgola mancante). Aggiungere in [`backend/services/ontology_workflow.py`](backend/services/ontology_workflow.py) (o nel service di parsing chiamato) un fallback:

- primo tentativo: `json.loads`
- secondo tentativo: `json_repair` (libreria) o regex di ripristino (aggiungi virgole mancanti, chiudi parentesi)
- logging dell'evento come `parse_repair` nel `run_metrics` / `supervisor_log` per visibilità

Obiettivo: **nessun run deve cadere sul `minimal_fallback`** per un errore sintattico dell'LLM. Solo per errori semantici irrisolti.

### Metrica di successo

- Percentuale di relazioni con `evidence = []` nell'export finale → da ~25% (bfp) / 100% (fanuc) a **<5%**.
- Numero di duplicati cross-schema (coppie `SYM-NNN` ↔ `sym_*` che descrivono lo stesso concetto) → **0** dopo merge.
- Tasso di `export_base == "minimal_fallback"` su batch 10+ manuali → da ~50% a **<10%**.

---

## Problema #3 — Copertura relazionale insufficiente su Component, ErrorCode e AFFECTS

### Evidenza concreta

Copertura cross-manual:

| Tipo | bfp (atteso) | bfp (estratto) | fanuc (atteso) | fanuc (estratto) |
|---|---|---|---|---|
| Component | ~15-25 | 22 ✓ | ~20-30 (ATC arm, spindle, ballscrew, waycover, encoder, battery, solenoid...) | **0** ❌ |
| ErrorCode | ~5-10 (C0330, H0216, H0712, H0090, H0212, ...) | 5 ✓ | ~5-10 (timeout, low-air, encoder-loss alarms citati esplicitamente) | **0** ❌ |
| HAS_COMPONENT | N_components | 22 ✓ | 20-30 | **0** ❌ |
| AFFECTS | ≥ N_failure_modes | 12 / 16 failure modes (75%) | ≥ 19 | **0** ❌ |
| INDICATES | N_error_codes | 2 / 5 (40%) | — | **0** ❌ |

Problemi specifici anche dove l'estrazione "riesce":

- **AFFECTS generici**: in bfp, `fm_current_sensor_failure` AFFECTS `comp_robot_arm` — invece il sensore non è stato estratto come Component dedicato, quindi la relazione cade sull'ascendente più grosso disponibile. Risultato: `comp_robot_arm` accumula link generici (5 AFFECTS diversi) che perdono significato diagnostico.
- **`material_context` vs Component duplicato**: ogni FailureMode ha già un `material_context` in formato testo (`"Robot arm"`, `"Cover"`, `"Gasket"`) che rappresenta lo stesso dato dell'AFFECTS relation. Due rappresentazioni non-normalizzate della stessa informazione → drift.
- **ErrorCode in fanuc scomparsi**: il manuale menziona esplicitamente `"timeout in spindle sequence"` (SYM-014) e `"low air alarm"` (SYM-012) come alarm codes, ma il triplet extractor (schema 3-entità) non ha il concetto di ErrorCode e l'ontology-draft è crashato → persi.

### Intervento mirato

**3.1 — Passata deterministica di "Component & ErrorCode mining" pre-draft**

Prima della chiamata LLM in [`backend/services/ontology_pipeline.py`](backend/services/ontology_pipeline.py) fase `extract`, aggiungere un **mining-pass deterministico** sul testo selezionato:

- **Component inventory**: regex + noun-phrase extraction (POS tagging leggero con spaCy o semplicemente n-gram + filtro lessicale) su termini nella tassonomia meccanica/elettrica (`valve`, `motor`, `encoder`, `arm`, `ballscrew`, `waycover`, `spindle`, `pump`, `sensor`, `connector`, `cable`, `bearing`, …).
- **ErrorCode inventory**: regex `[A-Z]\d{3,4}`, `E\d{2,4}`, `Alarm \d+`, + pattern "timeout in", "low air alarm", "<substantive> alarm".

Il risultato viene iniettato nel prompt principale come:

```
## DETECTED CANDIDATES (include these in the ontology if supported)
### Components mined from text
- Ballscrew (mentions: 4, pages: [22, 23])
- Waycover (mentions: 3, pages: [23])
- ATC arm (mentions: 6, pages: [33, 34, 35])
- Absolute encoder (mentions: 5, pages: [21])
...
### Error codes / alarm signatures mined from text
- "Timeout in spindle sequence" (page 33)
- "Low air alarm" (page 34)
```

L'LLM non parte più da zero; ha un "checklist floor" che aumenta recall senza rinunciare a precision (ogni elemento va confermato dal testo).

**3.2 — Vincolo prompt su AFFECTS specifico**

Nel prompt di ontology draft ([`backend/prompts/ontology_prompt.py:55-56`](backend/prompts/ontology_prompt.py:55)) sostituire:

```
- AFFECTS: FailureMode → Component (link failure modes to the component they affect)
```

con:

```
- AFFECTS: FailureMode → Component (link failure modes to the MOST SPECIFIC Component named
  in the failure context — never fall back to the root asset or the highest-level assembly
  unless the text explicitly names only that level. If the specific component is not in the
  Component list, add it as a new Component BEFORE emitting the AFFECTS relation.)
```

Rimuove il fenomeno "tutto affetta `comp_robot_arm`".

**3.3 — Normalizzare `material_context` come reference**

Modificare lo schema-side hint nel prompt: `material_context` **deve essere l'ID di un Component esistente** (o stringa vuota se non applicabile), non un'etichetta testuale libera. Aggiungere nel validator di [`backend/services/ontology_pipeline.py`](backend/services/ontology_pipeline.py) `schema_validate` una regola:

```
if failure_mode.material_context and not is_component_id(failure_mode.material_context):
    issue(severity="warning", code="material_context_not_linked",
          fix_hint="Set material_context to a Component ID or emit an AFFECTS relation.")
```

Questo elimina la duplicazione rappresentazionale ed espone la mancanza di Component quando il `material_context` esiste come testo ma non come nodo.

**3.4 — ErrorCode mandatory extraction quando ci sono alarm tokens**

Aggiungere nel prompt di ontology draft una regola condizionale:

```
19. If the text contains alphanumeric patterns matching alarm/error conventions
    (e.g. "C0330", "H0216", "Alarm 215", "E504") or phrases of the form
    "<adjective> alarm is set", "alarm '<text>' is displayed", "error <code>
    occurs", you MUST produce an ErrorCode node AND a corresponding INDICATES
    relation (ErrorCode → FailureMode) whenever the text links the code to
    a specific failure.
```

Applicarla anche al re-extraction prompt.

### Metrica di successo

- Coverage Component / ErrorCode su manuale con alarm table → **≥ 80%** dei codici citati diventano nodi ErrorCode.
- Numero di AFFECTS che puntano a `comp_<asset_root>` / `comp_robot_arm` (fallback generico) → **<10%** del totale AFFECTS.
- Zero FailureMode con `material_context` non-vuoto e senza AFFECTS relation associata.

---

## Piano di implementazione (ordine consigliato)

L'ordine massimizza ROI tenendo gli interventi indipendenti (ogni step è eseguibile e testabile da solo).

### Sprint 1 — Robustezza (1-2 giorni)
- **[2.4]** JSON repair fallback sulla parse dell'ontology draft. Motivazione: elimina la causa del peggior output (FANUC → 0 Component). Bassissimo rischio, isolato in un service.
- **[2.3]** Aggiunta di `evidence_page` al prompt del triplet extractor e propagazione in ontology finale. Elimina 100% delle `evidence: []` dal path triplet.

### Sprint 2 — Coverage (2-3 giorni)
- **[3.1]** Mining deterministico Component + ErrorCode iniettato nel prompt.
- **[3.4]** Regola di estrazione obbligatoria di ErrorCode quando ci sono alarm tokens.
- **[3.2]** + **[3.3]** Vincoli su AFFECTS specifico e `material_context` → Component-ID.

### Sprint 3 — Qualità semantica (3-4 giorni)
- **[1.1]** Nuovo `TypeConsistencyAgent` integrato nel reflective loop.
- **[1.2]** + **[1.3]** Rinforzo dei prompt extraction e re-extraction con esempi contrastivi.
- **[2.1]** + **[2.2]** Semantic dedup cross-schema in merge service + catalogo ID esistenti iniettato nel triplet extractor.

### Testing
Ciascuno step va validato rieseguendo `scripts/run_batch_export.py` sul medesimo batch (i 4 manuali in `manuals/batch_manuals/`) e misurando le tre KPI introdotte:
1. `type_consistency_score` = 1 − (coppie sym/fm tautologiche) / (totale MAY_INDICATE)
2. `evidence_coverage` = relazioni con evidence non-vuoto / totale relazioni
3. `component_coverage` = Component mined and confirmed / Component candidates from deterministic mining

Target post-intervento: tutte e tre > 0.80 nel batch automatico senza HITL.

---

## Note

- **Nessuna modifica al GraphState né alla supervisor decision table.** Tutti gli interventi si iscrivono nei punti di estensione esistenti (reflective loop, advisory agents, prompt templates, services).
- **Nessun cambio di contratto sul JSON finale.** Le modifiche sono additive (catalogo ID, evidence sempre presente) o interne (mining pass deterministico a monte del prompt LLM).
- L'ordine proposto prioritizza gli interventi che **eliminano modalità catastrofiche** (crash JSON → fallback minimale → 0 Component) prima di quelli che alzano la qualità media.
