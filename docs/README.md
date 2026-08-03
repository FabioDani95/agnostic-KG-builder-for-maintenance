# Documentation

This index separates current specifications from historical project records.
The distinction matters: dated plans describe decisions and old code shapes,
not work that is still pending.

## Current

- [MVP Specification](../SPECIFICHE_MVP.md) — authoritative target product
- [CSV Hardening Campaign](CSV_HARDENING_CAMPAIGN.md) — comportamento
  deterministico, risultati dei CSV reali, regressioni e prossimi casi.
- [G3 Engine Hardening Handoff](G3_ENGINE_HARDENING_HANDOFF.md) — stato del
  gate umano, limiti dichiarati e sequenza CSV→PDF senza approvazioni implicite.
- [Normative Specification Package](specs/README.md) — decisions, data
  contracts, codebase implications, and acceptance criteria.
- [UX Specification](specs/UX_SPECIFICATION.md) — unified multi-format
  frontend flow and controlled HITL interaction.
- [Project README](../README.md) — target pointer plus imported-baseline setup
  and behavior.
- [Architecture](ARCHITECTURE.md) — imported baseline runtime flow and module
  boundaries; it is not the target architecture specification.
- [Evaluation Protocol](EVALUATION_PROTOCOL.md) — normative golden-fixture and
  model-comparison procedure.
- [Test Suite Map](../tests/README.md) — correctness-test layers and commands.
- [Cleanup Audit](CLEANUP_AUDIT.md) — cleanup actions, retained items, and
  remaining release work as of 2026-07-28.

## Frozen evaluation records

These reports explain the annotations and gates for individual real-manual
fixtures. Keep them next to any corresponding frozen expected output:

- [ABB IRC5](ABB_IRC5_GOLDEN_EVAL.md)
- [FANUC VB Series](FANUC_VB_SERIES_GOLDEN_EVAL.md)
- [Haier LMA4120](HAIER_LMA4120_GOLDEN_EVAL.md)
- [LG LMH2235ST](LG_LMH2235ST_GOLDEN_EVAL.md)
- [Whirlpool W11187658](WHIRLPOOL_W11187658_GOLDEN_EVAL.md)

## Historical records

- [MVP Specification 0.2 Draft](archive/SPECIFICHE_MVP_0.2_DRAFT.md) —
  superseded and non-normative.
- [Stabilization Plan](archive/STABILIZATION_PLAN.md) — completed pre-refactor plan;
  paths and metrics in its body are obsolete.
- [Frontend Redesign Plan](archive/FRONTEND_REDESIGN_PLAN.md) — design rationale for
  the redesign completed in commit `6303abb`.
- [QA Demo Report](archive/QA_DEMO_REPORT.md) — pre-fix run evidence; its verdict is
  scoped to the recorded build and is not the current release verdict.

Historical records live under `docs/archive/` so they cannot be mistaken for
current specifications.
