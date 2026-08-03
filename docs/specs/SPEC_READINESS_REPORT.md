# Specification Readiness Report

## 1. Esito

**READY FOR PLANNING**

La remediation tecnica e la semantic review del pacchetto versione `2.1` sono
complete. Il Product Owner ha approvato esplicitamente il seguente snapshot
e l'approvazione è registrata in `SPEC_INDEX.json`:

```text
sha256:fd41a66b9d2b0eeaef53e0cd8840a31c2daa09ed0fdbd27a53451a5ccc8e57d2
```

Approvatore: `Product Owner`. Timestamp UTC:
`2026-08-03T09:20:43Z`.

Il checker deriva `READY_FOR_PLANNING` senza issue o blocker.

## 2. Snapshot verificato

| Voce | Risultato |
|---|---:|
| Requisiti normativi | 89 |
| Data contract | 47 |
| Obligation tracciate | 136 |
| Criteri di accettazione | 76 |
| Dataset di accettazione | 6 |
| Verification e artifact pianificati | 76 + 76 |
| Decisioni registrate | 44 (43 accettate, 1 sostituita) |
| Finding audit classificati | 32 |
| Finding senza disposition | 0 |
| Errori strutturali o semantici P1 residui | 0 |

Le 32 disposition comprendono:

- 13 finding chiusi normativamente;
- 7 finding chiusi tramite acceptance;
- 11 mismatch della codebase trasformati in `PLANNING_INPUT`;
- 1 guardrail differito senza hard-code.

`PLANNING_INPUT` significa lavoro obbligatorio per il futuro piano, non
capacità già implementata.

`READY_FOR_PLANNING` descrive la coerenza della specifica, non la readiness del
checkpoint applicativo. Per decisione `DEC-044`, l'implementazione resta ferma
a G3 non accettato e G4 è bloccato.

## 3. Verifiche eseguite

| Verifica | Risultato osservato |
|---|---|
| Pytest | 384 raccolti, 384 superati |
| Test del consistency checker | 19 superati, inclusi 18 mutation test |
| Ruff sui file modificati Python | superato |
| Golden mock | 9/9 fixture schema-compliant |
| Golden mock recall media | 1.0 |
| Link Markdown | 41 file, tutti i target locali risolvibili |
| Blocchi JSON nei data contract | 30 validi |
| Playwright console E2E | 3/3 superati |
| Audit diagnostico G3 CSV | 6 schemi provati; 2 completi, 1 fallito, 3 parziali/non sufficientemente bloccati |
| Audit ontologico sottografo PO | domain/range 0 errori; 36 nodi incompleti, 90 proprietà obbligatorie mancanti, 36 attributi extra |
| Checker strutturale | zero errori di ID, schema, traceability, decisioni o finding |
| Readiness derivata | `READY_FOR_PLANNING`, zero issue e zero blocker |

Il valore `301` resta il floor storico riconciliato dopo la rimozione
dell'editor (`313 + 1 - 17 + 4`); non è il conteggio della suite corrente.

## 4. Decisioni e contratti chiusi

La versione `2.1` congela, fra gli altri:

- attribuzione dei file affidata all'operatore, senza gate contenutistico;
- preparazione PDF G1 automatica e idempotente su tutte le pagine;
- preparazione G2 automatica con eccezioni, una decisione alla volta, preview
  limitate e dettagli tecnici chiusi di default;
- linguaggio UI basato sulle attività, senza nomi dei checkpoint di sviluppo,
  con tabella semantica e mappa colonne→grafo nel passo `Struttura dati`;
- conferma per singola fonte e matrice CSV/lingue prima dell'avanzamento;
- generation source-scoped, approvazione di ogni sottografo prima del merge e
  aggiornamento incrementale senza rigenerare la base pubblicata;
- ispezione di ogni sottografo tramite grafo navigabile, tabella nodi, tabella
  relazioni ed evidenze;
- separazione esplicita fra UX verificata e maturità del motore: G3 non è
  accettato; hardening CSV eterogeneo e validazione ontologica strict precedono
  il collaudo PDF sullo stesso contratto;
- accounting gerarchico di ogni RawUnit e disposition per tentativo;
- join espliciti con lineage composito;
- CandidateGraphRevision, withdrawal e non-regressione fra versioni;
- checkpoint committed, retry/resume e scope multisource;
- assertion operatore, authority, conflitti, causalità e knowledge gap;
- delega append-only con backpressure locale;
- CalibrationProfile non vacuo, qualificato e invalidabile;
- provider generation/embedding distinti e data-egress allowlist;
- bundle atomico `graph + evidence index + manifest`;
- confine locale browser-safe e capacity gate misurabile.

## 5. Handoff al piano

Il piano deve usare `SPEC_INDEX.json` e `TRACEABILITY_MATRIX.md` come input
machine-readable e human-readable. Ogni incremento deve citare obligation,
requirement, contract, acceptance, verification e artifact pertinenti.

I mismatch `AUD-021`–`AUD-031` devono diventare epiche o guardrail e restare
visibili finché i test associati non sono implementati e superati. Il piano
non può dichiarare già conformi publisher, resume, provider abstraction,
dataset multisource, UX target o boundary di sicurezza.

## 6. Ultimo gate completato

Il gate è stato aggiornato il `2026-08-03T08:20:18Z`:

1. il proprietario ha approvato esplicitamente il digest indicato;
2. approvatore, timestamp e digest sono registrati in `SPEC_INDEX.json`;
3. il checker è stato rieseguito e deriva `READY_FOR_PLANNING`.

Qualsiasi modifica normativa successiva cambia il digest e invalida entrambe
le approvazioni.
