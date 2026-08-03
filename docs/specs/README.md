# Pacchetto normativo MVP

Questa directory contiene le specifiche che devono essere lette prima di
generare il piano di sviluppo.

La versione `2.1` incorpora le decisioni Product Owner `DEC-036`–`DEC-044`:
responsabilità dell'operatore nella scelta dei file, nessun gate contenutistico
di associazione, preparazione PDF G1 automatica su tutte le pagine, home
minimale dei workspace persistiti con creazione tramite azione `+` e corsia
G2 automatica con eccezioni, una decisione alla volta e dettagli tecnici
progressivi. La UI non espone i nomi dei gate di sviluppo: il quarto passo è
`Struttura dati`, con anteprima tabellare e mappa colonne→grafo; il grafo viene
costruito nel successivo passo `Elaborazione`.
La conferma avviene sulla card della singola fonte; la matrice di accettazione
copre inoltre varianti CSV, righe irregolari, payload non testuali e contenuti
EN/IT/DE/misti.
La generation produce inoltre un sottografo approvabile per ogni fonte prima
del merge cross-source; una fonte aggiunta dopo V1 genera soltanto il proprio
sottografo e il delta verso la versione pubblicata di base.
La prima accettazione di `Elaborazione` è CSV-first: ogni fonte espone grafo
navigabile, tabelle complete di nodi e relazioni e drill-down alle evidenze.
La visualizzazione G3 è una base UX, non prova di maturità del motore. Il
checkpoint non è accettato: prima si esegue hardening su CSV eterogenei con
mapping agnostico e validazione ontologica strict, poi il collaudo PDF segue
sullo stesso contratto source-scoped e sulla pipeline PDF riusata, senza
creare un secondo percorso semantico.

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
| [`../G3_ENGINE_HARDENING_HANDOFF.md`](../G3_ENGINE_HARDENING_HANDOFF.md) | Stato di fermo e piano operativo CSV→PDF prima di riproporre G3 |

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
