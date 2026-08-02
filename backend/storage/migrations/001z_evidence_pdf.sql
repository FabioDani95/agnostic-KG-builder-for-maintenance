CREATE TABLE preparations (
    preparation_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    source_id TEXT NOT NULL UNIQUE REFERENCES sources(source_id) ON DELETE RESTRICT,
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    state TEXT NOT NULL CHECK (
        state IN (
            'not_started', 'profiling_or_scoping', 'awaiting_operator', 'ready',
            'invalidated', 'excluded', 'duplicate', 'quarantined',
            'failed_resumable', 'failed_terminal'
        )
    ),
    active_config_id TEXT,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    updated_at TEXT NOT NULL CHECK (substr(updated_at, -1) = 'Z')
);

CREATE TABLE pdf_scopes (
    scope_id TEXT PRIMARY KEY,
    preparation_id TEXT NOT NULL REFERENCES preparations(preparation_id) ON DELETE RESTRICT,
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    version INTEGER NOT NULL CHECK (version >= 1),
    included_pages_json TEXT NOT NULL,
    excluded_pages_json TEXT NOT NULL,
    operator TEXT NOT NULL,
    supersedes TEXT REFERENCES pdf_scopes(scope_id),
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    UNIQUE (source_id, version)
);

CREATE TABLE evidence_units (
    evidence_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    asset_id TEXT NOT NULL REFERENCES assets(asset_id) ON DELETE RESTRICT,
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    raw_unit_id TEXT NOT NULL,
    locator_hash TEXT NOT NULL CHECK (length(locator_hash) = 64),
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    UNIQUE (source_id, raw_unit_id)
);

CREATE TABLE scope_evidence (
    scope_id TEXT NOT NULL REFERENCES pdf_scopes(scope_id) ON DELETE RESTRICT,
    evidence_id TEXT NOT NULL REFERENCES evidence_units(evidence_id) ON DELETE RESTRICT,
    PRIMARY KEY (scope_id, evidence_id)
);

CREATE INDEX idx_evidence_workspace ON evidence_units(workspace_id, source_id);

CREATE TRIGGER pdf_scopes_no_update
BEFORE UPDATE ON pdf_scopes
BEGIN
    SELECT RAISE(ABORT, 'pdf_scopes are append-only');
END;

CREATE TRIGGER pdf_scopes_no_delete
BEFORE DELETE ON pdf_scopes
BEGIN
    SELECT RAISE(ABORT, 'pdf_scopes are append-only');
END;

CREATE TRIGGER evidence_units_no_update
BEFORE UPDATE ON evidence_units
BEGIN
    SELECT RAISE(ABORT, 'evidence_units are immutable');
END;

CREATE TRIGGER evidence_units_no_delete
BEFORE DELETE ON evidence_units
BEGIN
    SELECT RAISE(ABORT, 'evidence_units are immutable');
END;

CREATE TRIGGER scope_evidence_no_update
BEFORE UPDATE ON scope_evidence
BEGIN
    SELECT RAISE(ABORT, 'scope_evidence is immutable');
END;

CREATE TRIGGER scope_evidence_no_delete
BEFORE DELETE ON scope_evidence
BEGIN
    SELECT RAISE(ABORT, 'scope_evidence is immutable');
END;
