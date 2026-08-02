# Specification Readiness Report

## 1. Esito

**READY FOR PLANNING**

La remediation tecnica e la semantic review del pacchetto versione `1.2` sono
complete. Il Product Owner ha approvato esplicitamente il seguente snapshot
e l'approvazione è registrata in `SPEC_INDEX.json`:

```text
sha256:66db17fbad207734889e6a671f218145f56b032034c15cbfcc656f1fe85fff28
```

Approvatore: `Product Owner`. Timestamp UTC:
`2026-07-29T12:13:44Z`.

Il checker deriva `READY_FOR_PLANNING` senza issue o blocker.

## 2. Snapshot verificato

| Voce | Risultato |
|---|---:|
| Requisiti normativi | 89 |
| Data contract | 47 |
| Obligation tracciate | 136 |
| Criteri di accettazione | 75 |
| Dataset di accettazione | 6 |
| Verification e artifact pianificati | 75 + 75 |
| Decisioni congelate | 35 |
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

## 3. Verifiche eseguite

| Verifica | Risultato osservato |
|---|---|
| Pytest | 325 raccolti, 325 superati |
| Test del consistency checker | 19 superati, inclusi 18 mutation test |
| Ruff sui file modificati Python | superato |
| Golden mock | 9/9 fixture schema-compliant |
| Golden mock recall media | 1.0 |
| Link Markdown | 41 file, tutti i target locali risolvibili |
| Blocchi JSON nei data contract | 30 validi |
| Playwright console E2E | 1/1 superato |
| Checker strutturale | zero errori di ID, schema, traceability, decisioni o finding |
| Readiness derivata | `READY_FOR_PLANNING`, zero issue e zero blocker |

Il valore `301` resta il floor storico riconciliato dopo la rimozione
dell'editor (`313 + 1 - 17 + 4`); non è il conteggio della suite corrente.

## 4. Decisioni e contratti chiusi

La versione `1.2` congela, fra gli altri:

- assessment di appartenenza della fonte alla macchina;
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

Il gate è stato completato il `2026-07-29T12:13:44Z`:

1. il proprietario ha approvato esplicitamente il digest indicato;
2. approvatore, timestamp e digest sono registrati in `SPEC_INDEX.json`;
3. il checker è stato rieseguito e deriva `READY_FOR_PLANNING`.

Qualsiasi modifica normativa successiva cambia il digest e invalida entrambe
le approvazioni.
