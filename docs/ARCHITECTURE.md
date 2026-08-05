# Architecture

## Scope

This document describes the current repository. The target product contract is
[SPECIFICHE_MVP.md](../SPECIFICHE_MVP.md); detailed logical contracts and
acceptance obligations live under [docs/specs](specs/README.md).

The codebase currently contains two explicit runtime paths:

1. the MVP workspace path for machine identity, multi-source ingestion,
   structured preparation and source-scoped graph review;
2. the retained one-PDF pipeline, kept as a regression surface until its useful
   services have migrated to the shared target contracts.

They share a FastAPI process and selected domain services. They do not share
browser state or pretend to be one completed workflow.

## Runtime entry points

scripts/dev_server.mjs is the development launcher used by run.sh and
Playwright. It creates the Python environment when necessary, verifies the
runtime import set and starts:

~~~text
uvicorn backend.main:app
~~~

backend/main.py:

- initializes the operational database and migrations;
- installs the trusted-local security and request-limit middleware;
- mounts the active routers;
- redirects / to /home.html;
- serves frontend/ as static files.

The generated OpenAPI description at /docs is the authoritative inventory of
mounted HTTP operations.

## MVP workspace flow

~~~text
machine identity
    -> workspace + operator-input evidence
    -> source inventory + content-addressed raw bytes
    -> PDF automatic page preparation
       or structured inspection and mapping
    -> immutable RawUnit ledger
    -> canonical EvidenceUnit records
    -> source-scoped graph revision
    -> strict ontology/provenance validation
    -> explicit source decision
~~~

Current implementation stops at the G3 source decision. Cross-source entity
resolution, candidate revision, publication and verified-bundle reading remain
target stages; no current endpoint silently performs them.

### Persistence

The MVP path uses:

- SQLite, configured by KG_OPERATIONAL_DB, for workspaces, sources, raw-unit
  accounting, evidence, structured profiles and graph revisions;
- a content-addressed raw store, configured by KG_RAW_DIR;
- an incoming-file staging area, configured by KG_INCOMING_DIR.

Schema changes are ordered SQL migrations under backend/storage/migrations.
Repositories own SQL access; routers should not introduce domain rules.

### Structured-source invariants

- Parsing identity, evidence-derivation identity and graph-generator identity
  are separate versioned concepts.
- Raw units are append-only source observations.
- Mapping revision creates new evidence and invalidates derived revisions.
- Exact consolidation combines claims while preserving all evidence IDs.
- Validation fails closed on required properties, extra properties,
  domain/range, endpoints, provenance, unresolved mapping and knowledge gaps.

## Retained PDF flow

~~~text
manuals/*.pdf
    -> /api/load-manual
    -> scoping and operator approval
    -> ontology draft
    -> extraction, grounding and review
    -> best-effort legacy export
~~~

Run state is mirrored under data/runs/<run_id> as manifests, append-only events,
traces and snapshots. Persisted runs can be inspected after restart but are not
resumed for in-flight model actions.

The retained console is available at /console.html without the foundation
query parameter. Its mutation and export behavior is legacy behavior, not
evidence that target publication is implemented.

## Module boundaries

| Area | Responsibility |
|---|---|
| backend/domain | stable IDs, domain records, locators and invariants |
| backend/storage | database lifecycle, migrations, raw store and repositories |
| backend/adapters | PDF compatibility projection and deterministic structured parsers |
| backend/services | preparation, evidence derivation, graph generation, validation and retained pipeline workflows |
| backend/routers | HTTP/SSE translation and response contracts |
| backend/security | trusted-local boundary, containment and request limits |
| backend/agents, backend/graph | retained multi-agent orchestration and live PDF state |
| backend/runstore | retained append-only PDF run persistence |
| frontend/app | current workspace application modules |
| frontend/console.js | retained PDF console, mounted only when foundation=1 is absent |
| tests | correctness, contract, acceptance, evaluation and browser gates |

Compatibility modules are retained only where production or characterization
tests still import them. The standalone graph editor and /modify API are
intentionally absent.

## Frontend composition

home.html loads the lightweight workspace list. console.html loads both module
sets, then console.js selects exactly one:

- foundation=1 calls KGFoundation.mount and returns immediately;
- otherwise the retained PDF console boots.

The workspace application has four modules aligned with its phases
(machine, sources/documents, structure and graph), a shared state model, a
single selection model and a force-directed SVG explorer. It uses no frontend
framework and has no build step.

## Configuration

- .env: ignored local secrets and environment overrides;
- config.yaml: retained PDF pipeline/model behavior;
- backend/app_config.py: configuration loading and runtime overrides;
- environment variables: test isolation, local paths and model mode;
- KG_LLM_MODE=mock: deterministic, no-paid-call test behavior.

## Verification boundary

No single green suite proves product acceptance:

- Ruff checks static Python issues and import order.
- pytest checks unit, contract, integration and executable acceptance tests.
- the specification checker checks normative-package structure and digest.
- the golden harness checks deterministic extraction-quality gates.
- Playwright checks both browser applications against the real FastAPI app.
- Product Owner artifacts record checkpoint decisions separately.

Commands and suite ownership are in [tests/README.md](../tests/README.md).
