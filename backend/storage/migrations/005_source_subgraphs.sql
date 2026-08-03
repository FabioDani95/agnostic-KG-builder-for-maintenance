CREATE TABLE source_subgraph_revisions (
    source_subgraph_revision_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    preparation_fingerprint TEXT NOT NULL CHECK (length(preparation_fingerprint) = 64),
    input_config_hash TEXT NOT NULL CHECK (length(input_config_hash) = 64),
    payload_json TEXT NOT NULL,
    supersedes TEXT REFERENCES source_subgraph_revisions(source_subgraph_revision_id),
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    UNIQUE (source_id, preparation_fingerprint, input_config_hash)
);

CREATE TABLE source_subgraph_decisions (
    decision_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    source_subgraph_revision_id TEXT NOT NULL REFERENCES source_subgraph_revisions(source_subgraph_revision_id) ON DELETE RESTRICT,
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    action TEXT NOT NULL CHECK (action IN ('approve', 'reject')),
    note TEXT,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z')
);

CREATE INDEX idx_source_subgraphs_workspace
ON source_subgraph_revisions(workspace_id, source_id, created_at);

CREATE INDEX idx_source_subgraph_decisions_revision
ON source_subgraph_decisions(source_subgraph_revision_id, created_at);

CREATE TRIGGER source_subgraph_revisions_no_update
BEFORE UPDATE ON source_subgraph_revisions
BEGIN
    SELECT RAISE(ABORT, 'source subgraph revisions are immutable');
END;

CREATE TRIGGER source_subgraph_revisions_no_delete
BEFORE DELETE ON source_subgraph_revisions
BEGIN
    SELECT RAISE(ABORT, 'source subgraph revisions are immutable');
END;

CREATE TRIGGER source_subgraph_decisions_no_update
BEFORE UPDATE ON source_subgraph_decisions
BEGIN
    SELECT RAISE(ABORT, 'source subgraph decisions are append-only');
END;

CREATE TRIGGER source_subgraph_decisions_no_delete
BEFORE DELETE ON source_subgraph_decisions
BEGIN
    SELECT RAISE(ABORT, 'source subgraph decisions are append-only');
END;
