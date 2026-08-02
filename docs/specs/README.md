# Pacchetto normativo MVP

Questa directory contiene le specifiche che devono essere lette prima di
generare il piano di sviluppo.

## Documenti

| Documento | Scopo |
|---|---|
| [`/SPECIFICHE_MVP.md`](../../SPECIFICHE_MVP.md) | Requisiti di prodotto e invarianti |
| [`DECISION_REGISTER.md`](DECISION_REGISTER.md) | Decisioni approvate e razionale |
| [`UX_SPECIFICATION.md`](UX_SPECIFICATION.md) | Flusso frontend, stati e interazioni HITL |
| [`DATA_CONTRACTS.md`](DATA_CONTRACTS.md) | Contratti logici e artifact JSON |
| [`BASELINE_AND_CODEBASE_IMPACT.md`](BASELINE_AND_CODEBASE_IMPACT.md) | Riuso e implicazioni della pipeline esistente |
| [`ACCEPTANCE_CRITERIA.md`](ACCEPTANCE_CRITERIA.md) | Scenari, metriche e Definition of Done |
| [`TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md) | Copertura requisiti → test e gate |
| [`SPEC_INDEX.json`](SPEC_INDEX.json) | Indice machine-readable di ID, obligation, verification, artifact, decisioni e finding |
| [`SPEC_INDEX.schema.json`](SPEC_INDEX.schema.json) | Schema dell'indice normativo |
| [`AUDIT_REMEDIATION_REPORT.md`](AUDIT_REMEDIATION_REPORT.md) | Chiusura puntuale di AUD-001..032 e handoff al piano |
| [`SPEC_READINESS_REPORT.md`](SPEC_READINESS_REPORT.md) | Esito dell'audit pre-piano |

## Regola di utilizzo

Il piano di sviluppo futuro deve:

1. citare gli ID dei requisiti e dei criteri di accettazione;
2. distinguere fra capacità già esistenti, refactoring e funzionalità nuove;
3. includere un gate utente verificabile per ogni incremento;
4. non introdurre requisiti di prodotto non presenti nel pacchetto;
5. segnalare un conflitto invece di reinterpretare l'ontologia o i vincoli.

`scripts/check_spec_consistency.py` verifica l'indice, i documenti dichiarati,
la tracciabilità requirement/contract → acceptance → verification → artifact,
le decisioni, i finding e lo stato readiness. Un checker verde dimostra
completezza strutturale; la pertinenza semantica delle obligation è attestata
separatamente e legata al digest del pacchetto.

Gli stati `PLANNING_INPUT` nel registro audit descrivono lavoro da implementare:
non riducono il readiness della specifica e non autorizzano a dichiarare la
codebase conforme prima dei test corrispondenti.

La bozza `docs/archive/SPECIFICHE_MVP_0.2_DRAFT.md` è storica e non normativa.
