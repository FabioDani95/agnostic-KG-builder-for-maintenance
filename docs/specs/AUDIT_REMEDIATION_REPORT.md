# Registro di remediation dell'audit pre-piano

## 1. Scopo e semantica degli stati

Questo registro chiude i 32 rilievi dell'audit del 29 luglio 2026 ai fini della
generazione del piano di sviluppo. Non dichiara implementate capacità che la
baseline non possiede.

| Stato | Significato |
|---|---|
| `CLOSED_NORMATIVE` | decisione o contratto congelato e testabile |
| `CLOSED_ACCEPTANCE` | quality gate e risultato osservabile definiti |
| `PLANNING_INPUT` | mismatch noto, trasformato in epic obbligatoria con acceptance congelata |
| `DEFERRED_GUARDRAIL` | capacità fuori MVP, dimensione contrattuale preservata |

Un finding `PLANNING_INPUT` non può essere marcato `implemented` nel futuro
indice finché test e artifact previsti non esistono. Il readiness pre-piano
richiede zero decisioni di prodotto aperte, non zero lavoro di sviluppo.

## 2. Decisioni conservative adottate

- una fonte è `compatible` soltanto con assessment risolvibile; `uncertain` e
  `incompatible` non contribuiscono;
- strutture indipendenti non vengono unite implicitamente;
- ogni unità raw riceve una disposition terminale prima di filtri o cap;
- una versione nuova è `apply(base, approved_delta)` e ogni perdita richiede
  withdrawal, merge o split approvato;
- causalità e rimedio richiedono supporto esplicito; inspection-only e stato
  ticket non provano `RESOLVED_BY`;
- IT/DE non qualificato è preservato ma non auto-pubblicato;
- generation, embedding, endpoint e data egress sono configurazioni distinte;
- mock prova il wiring; la qualità di release richiede un profilo reale
  congelato;
- il bundle pubblicato, non il singolo JSON o `latest`, è l'unità di lettura.

## 3. Chiusura dei finding

| Finding | Stato | Risoluzione normativa o acceptance | Conseguenza per il piano |
|---|---|---|---|
| AUD-001 | `CLOSED_NORMATIVE` | FR-WS-IDENTITY-001; DC-SRC-ASSESS-001; AC-WS-005 | source registry e gate identità |
| AUD-002 | `CLOSED_NORMATIVE` | FR-TAB-005; DC-JOIN-001; DC-PROV-001; AC-JOIN-001 | lineage join-aware e property evidence |
| AUD-003 | `CLOSED_NORMATIVE` | INV-005; DC-DISPOSITION-001; DC-STATE-001; AC-EV-001 | ledger raw prima dei filtri |
| AUD-004 | `CLOSED_NORMATIVE` | FR-MERGE-005; DC-CGRAPH-001; DC-REVIEW-001; DC-PUBLISH-001 | write path transazionale e withdrawal |
| AUD-005 | `CLOSED_NORMATIVE` | FR-004; DC-CHECKPOINT-001; DC-CACHE-001; AC-RES-002 | checkpoint committed e failure injection |
| AUD-006 | `CLOSED_NORMATIVE` | FR-ONTO-001; FR-ONTO-002; FR-ONTO-003; FR-ONTO-004; FR-ONTO-005; DC-ASSERT-001; AC-ONT-004 | operator assertion, nessun default inventato |
| AUD-007 | `CLOSED_NORMATIVE` | FR-MERGE-002; DC-CONTEXT-001; AC-MERGE-001; AC-MERGE-003 | guard di contesto e collision test |
| AUD-008 | `CLOSED_NORMATIVE` | FR-EV-003; FR-NS-004; DC-CONFLICT-001; DC-GAP-001; DC-OUTCOME-001; AC-SEM-002 | policy di authority, outcome e causalità |
| AUD-009 | `CLOSED_NORMATIVE` | FR-HITL-005; DC-DELEGATION-001; FR-UX-018; AC-UX-013 | event log di delega e backpressure |
| AUD-010 | `CLOSED_NORMATIVE` | FR-LANG-002; DC-LANG-001; AC-LANG-002 | ingest preserve, translation review-only |
| AUD-011 | `CLOSED_NORMATIVE` | FR-LLM-001; FR-LLM-002; FR-LLM-003; DC-PROVIDER-001; DC-EGRESS-001; AC-LLM-001; AC-LLM-002; AC-SEC-002 | adapter, preflight ed egress allowlist |
| AUD-012 | `CLOSED_ACCEPTANCE` | SPEC_INDEX.json/schema; checker; mutation test; Readiness derivato | indice normativo è il gate, non la presenza globale |
| AUD-013 | `CLOSED_NORMATIVE` | FR-NORM-002; semantic_texts/templates role-specific; AC-NORM-002 | cache e payload separati per ruolo |
| AUD-014 | `CLOSED_NORMATIVE` | equazione baseline 313 + 1 - 17 + 4 = 301; AC-REG-002 | report di collection con commit/comando |
| AUD-015 | `CLOSED_ACCEPTANCE` | AC-SEM-002; AC-REG-001; expected gap vincolanti nel protocollo di valutazione | golden lint e negative relation check |
| AUD-016 | `CLOSED_ACCEPTANCE` | DS-003 blindato; AC-SEM-001 | golden workspace ed evaluator multisource |
| AUD-017 | `CLOSED_ACCEPTANCE` | DC-CALIBRATION-001; AC-CAL-001 | precisione più copertura, zero denominator fail |
| AUD-018 | `CLOSED_ACCEPTANCE` | DC-CGRAPH-001; AC-REG-001; obligation source → AC → verification → artifact in SPEC_INDEX.json | trace review legata al package digest |
| AUD-019 | `CLOSED_ACCEPTANCE` | FR-MERGE-005; DC-CGRAPH-001; AC-NONREG-001 | test di conservazione claim Vn |
| AUD-020 | `CLOSED_ACCEPTANCE` | DS-CHAT-001; AC-CHAT-004; hash bundle | query supported non può rispondere sempre vuoto |
| AUD-021 | `PLANNING_INPUT` | BOUND-001; BOUND-002; BOUND-003; BOUND-004; AC-WS-002 | nuovo boundary workspace/source/evidence |
| AUD-022 | `PLANNING_INPUT` | GAP-011; DC-DISPOSITION-001; AC-EV-001 | rimuovere drop e troncamenti silenziosi |
| AUD-023 | `PLANNING_INPUT` | GAP-014; DC-GRAPH-001; DC-GRAPH-002; DC-GRAPH-003; DC-GRAPH-004; DC-GRAPH-005; AC-PUB-002 | publisher strict derivato dall'ontologia |
| AUD-024 | `PLANNING_INPUT` | GAP-012; DC-REVIEW-001; AC-HITL-002; AC-HITL-005; AC-UX-006 | sostituire endpoint review legacy |
| AUD-025 | `PLANNING_INPUT` | GAP-013; DC-CHECKPOINT-001; AC-RES-002 | run store riavviabile |
| AUD-026 | `PLANNING_INPUT` | GAP-015; DC-PROVIDER-001; AC-LLM-002 | provider adapter e capability preflight |
| AUD-027 | `PLANNING_INPUT` | GAP-016; FR-UX-001; FR-UX-002; FR-UX-003; FR-UX-004; FR-UX-005; FR-UX-006; FR-UX-007; FR-UX-008; FR-UX-009; FR-UX-010; FR-UX-011; FR-UX-012; FR-UX-013; FR-UX-014; FR-UX-015; FR-UX-016; FR-UX-017; FR-UX-018; AC-UX-001; AC-UX-002; AC-UX-003; AC-UX-004; AC-UX-005; AC-UX-006; AC-UX-007; AC-UX-008; AC-UX-009; AC-UX-010; AC-UX-011; AC-UX-012; AC-UX-013 | nuovo E2E del flusso completo |
| AUD-028 | `PLANNING_INPUT` | NFR-005; GAP-017; AC-SEC-003 | containment, same-origin e request limits |
| AUD-029 | `PLANNING_INPUT` | NFR-PERF-001; NFR-PERF-003; AC-PERF-001 | capacity gate, RSS/call ceiling, tempo informativo |
| AUD-030 | `PLANNING_INPUT` | DC-PARSER-001; AC-TAB-005 | contract-test matrix dei parser |
| AUD-031 | `PLANNING_INPUT` | FR-OUT-001; DC-PUBLISH-001; AC-PUB-005 | staging, lock, CAS e atomic commit |
| AUD-032 | `DEFERRED_GUARDRAIL` | FR-LANG-002; DC-LANG-001; FR-LLM-001; DC-PROVIDER-001; DC-CACHE-001; DC-CHECKPOINT-001; FR-CHAT-001; DC-PUBLISH-001 | nessuna feature extra, nessun hard-code |

## 4. Regola di handoff

Il piano di sviluppo deve:

1. usare i finding `PLANNING_INPUT` come epiche o guardrail, senza riaprire le
   decisioni chiuse;
2. citare obligation, requirement, contract e acceptance ID;
3. trasformare le verification `specified` dell'indice in `implemented` con
   target reale e artifact di esito;
4. mantenere visibili i mismatch finché il relativo test non passa;
5. rigenerare digest e readiness a ogni modifica normativa.

Qualsiasi scelta che cambi una decisione della sezione 2 richiede una nuova
versione del pacchetto, aggiornamento dell'indice e nuova semantic review.
