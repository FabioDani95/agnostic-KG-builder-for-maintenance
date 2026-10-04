# Graph editor

Use the editor to inspect and correct a saved graph, then accept the changes as a
new version. Editing makes no model calls and does not modify the original graph.
This guide covers the implemented workflow; pipeline questions and extraction
approval are described in [Getting started](getting-started.md#use-the-interface).

## Edit, check and accept

1. Open a graph version and choose **Edit graph**. The same entry point is
   available after live execution/replay and from manual version history.
2. Work in the graph, node and relation views. Selection is shared across views.
   Filters, source excerpts and PDF pages help locate the record you want to change.
   Use undo/redo to review alternatives.
3. Continue to **Check**. Inspect both inherited issues and issues introduced by
   your changes. Structural errors can block acceptance; warnings may require
   acknowledgement. Checks describe structure and documentation, not technical
   correctness of maintenance advice.
4. Review the summary and accept the changes to create a new version. Acceptance
   is the persistence step; there is no separate approval button for that revision.

Moving between steps, changing a cell, or requesting validation does not save a
draft. Unsaved operations stay in the browser session's memory. Leaving the
editor discards them after the exit flow; re-entering starts from the saved base.
An acceptance request already sent can complete even if the browser closes.

An active extraction, unapplied answers or an unreadable graph format can prevent
editing. A missing PDF alone does not: embedded source excerpts remain available,
with restricted source operations.

## What can change

The editor supports typed node properties, new nodes, relation endpoints,
occurrences, conditions, evidence associations and explicit human decisions.
Domain/range checks constrain relation endpoints. Removing a node can remove
incident relations; undo restores the session operation. A relation with a triple
already present is represented through occurrences rather than an unrelated duplicate.

IDs, existing node types and the original source text are read-only. Field editing
preserves distinctions between a missing value, empty text, `null`, an empty list,
`not_stated`/`Unknown`, `0` and `false`. Unknown data fields are preserved rather
than silently discarded during a supported edit.

## Acceptance and trust

Three different decisions remain visible:

- **Version acceptance:** a person saved this revision after reviewing its summary.
- **Automatic verification:** a pipeline certificate describes its checks on an occurrence.
- **Human confirmation or rejection:** a person decided on the current content of an occurrence.

Changing a node invalidates verification on affected diagnostic occurrences;
changing an occurrence invalidates its previous certificate. Human confirmation
is bound to a content hash and expires when the content changes. A human-confirmed
relation can have `tier: null`; the editor does not invent a green certificate.
A rejected occurrence does not erase other active occurrences on the same edge.

A version may be accepted while acknowledged warnings or unverified content remain.
Read occurrence status, evidence and conditions before reusing a relation. Name
similarity is a suggestion, not an automatic merge. Condition compatibility checks
are conservative and do not implement general natural-language reasoning.

## Sources and provenance

When the original PDF can be verified against saved evidence, the editor exposes
its segment index and page images. Otherwise, embedded citations remain readable,
but new source associations and unverified PDF views are restricted. A revision
retains its source snapshot even when the originating run changes later.

Each accepted revision has an ID of the form `revision~<uuid>` and lives in
`workspace/<manual_id>/revisions/<uuid>/`:

| File | Purpose |
| --- | --- |
| `graph.json` | Accepted graph, format `kg-v3-graph-3` |
| `base-graph.json` | Exact parent graph bytes |
| `revision.json` | Parent/root identifiers, hashes, author, timestamp, note and request identity |
| `changes.json` | Applied operations and actual graph differences |
| `validation.json`, `acceptance.json` | Validated preview and human acceptance |
| `source-review.json`, `source-report.json` | Inherited review context and historical pipeline report |
| `ontology.json`, `source-segments.json` | Frozen schema and available verified evidence |
| `source.pdf` | Verified source PDF, when available |

The revision does not invent extraction time, model cost or new pipeline results.
**Download version and provenance** packages these available files as a ZIP.
A manual revision cannot be resumed as an extraction. Questions belonging to its
source run remain separately accessible in **Your turn**.

## API contract

All version endpoints below use the prefix
`/api/manuals/{manual_id}/versions/{version_id}`. Open `/api/docs` for schemas.

| Method and suffix | Behaviour |
| --- | --- |
| `GET /editor` | Graph document, typed schema, capabilities, sources and preconditions |
| `POST /validate-edits` | Preview operations, differences, checks and hashes without saving a revision |
| `POST /revisions` | Validate and atomically accept a new revision; 201 on creation, 200 for an identical retry |
| `GET /changes` | Stored revision operations and differences |
| `GET /provenance.zip` | Download an accepted revision and its provenance |
| `GET /source-segments` | Search/paginate the verified source index |
| `GET /pages/{page}.png` | View a page from that version's verified source |

`GET /api/manuals/{manual_id}/revision-requests/{request_id}` returns `saved`,
`in_progress` or `not_found` for an acceptance request. If a network response is
uncertain, the frontend retains the submitted payload and request key in memory
and checks that endpoint instead of creating another revision.

Validation and acceptance both check the base graph, schema, source and review
context. Stale previews or conflicting reuse of a request key return 409;
invalid operations or missing required acknowledgements return 422. An unchanged
document cannot create a revision. Publication uses a per-manual lock and atomic
directory rename; the catalogue ignores incomplete staging directories.

Implementation: `backend/ui/graph_document.py`, `graph_validation.py`,
`revisions.py`, `evidence.py`, and `frontend/src/editor/`. Regression checks and a
synthetic browser fixture are listed in [Development](development.md).
