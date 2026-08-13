# PDF G3 diagnostic benchmark - KPI protocol

Prepared before any real benchmark generation on 2026-08-12.

## Decision model

The benchmark reports three independent verdicts. They must not be averaged
into a score that could hide a safety failure.

1. **Semantic usefulness**: recovery of the frozen manual claims.
2. **Publication integrity**: schema, provenance, topology, identity and
   candidate accounting.
3. **Operational efficiency**: measured calls, tokens, duration and cost.

## Content-aware semantic metrics

- `gold_claim_recall`: a complete grounded published chain counts when the
  manual states a restorative or escalation action. When the manual supplies
  inspection-only guidance, the correct outcome is a traceable explicit gap;
  inventing a repair is a violation.
- `autonomous_path_recall`: complete published diagnostic paths only. This is
  reported separately because a safe review/gap disposition can be correct but
  is not yet usable autonomously by a troubleshooting agent.
- `forbidden_pairings`: frozen cross-row/cross-column contaminations. Gate 0.
- `unsupported_published_rate`: published diagnostic paths not semantically
  supported by the manual. Gate 0.
- `gold_page_retention`: all pages supporting a frozen claim must be retained
  by diagnostic discovery. Gate 100%.

The recall floor is content-dependent:

| Manual | Gold scope | Semantic floor |
|---|---|---:|
| Eastman E-554 | frozen representative sample, 8 chains | 6/8 (0.75) |
| Danfoss APF | exhaustive table, 8 atomic branches | 6/8 (0.75) |
| Graco Check-Mate 200 | exhaustive table, 18 atomic branches | 15/18 (0.8333) |

Campaign macro recall is the unweighted mean of the three per-manual recalls;
its floor is 0.78. The macro is secondary to each per-manual floor.

There is no universal critical-chain gate: these manuals do not provide a
comparable severity ranking for the annotated troubleshooting rows. Review
load is reported by reason and severity, not gated, because legitimate layout
ambiguity and inspection-only instructions differ by manual.

## Publication-integrity gates

These are independent of how much diagnostic material a manual contains:

- strict validation passes with zero schema/domain/range/endpoint errors;
- every published relation has an exact resolvable EvidenceRef;
- zero isolated published diagnostic nodes;
- every published CorrectiveAction has an incoming `RESOLVED_BY`;
- exactly one operator-canonical Asset with the original Asset ID;
- every detected diagnostic candidate has a publish/gap/review/exclude
  disposition, or the revision remains explicitly non-approvable;
- no approval, rejection, merge or structured-source processing is performed.

## Budget gate

The user-authorized campaign ceiling is USD 3.00. At most one real generation
is started per PDF. A conservative per-run ceiling may be raised to USD 0.90,
which reserves at most USD 2.70 across the three runs and leaves USD 0.30
campaign headroom. Measured cost and the conservative preflight are both
persisted. A failed or blocked run is not retried.
