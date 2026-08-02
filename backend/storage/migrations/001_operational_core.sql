CREATE TABLE operational_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL CHECK (substr(updated_at, -1) = 'Z')
);

CREATE TABLE entity_ids (
    entity_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z')
);

CREATE TABLE workspaces (
    workspace_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    asset_identity_version INTEGER NOT NULL DEFAULT 1 CHECK (asset_identity_version >= 1),
    ontology_version TEXT NOT NULL,
    ontology_sha256 TEXT NOT NULL CHECK (length(ontology_sha256) = 64),
    confirmed_at TEXT NOT NULL CHECK (substr(confirmed_at, -1) = 'Z'),
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    updated_at TEXT NOT NULL CHECK (substr(updated_at, -1) = 'Z')
);

CREATE TABLE assets (
    asset_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    workspace_id TEXT NOT NULL UNIQUE REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    description TEXT NOT NULL CHECK (length(trim(description)) > 0),
    brand TEXT NOT NULL CHECK (length(trim(brand)) > 0),
    model TEXT NOT NULL CHECK (length(trim(model)) > 0),
    asset_type TEXT,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z')
);

CREATE TABLE asset_identifiers (
    identifier_id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    namespace TEXT NOT NULL,
    value TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('serial', 'equipment_tag', 'customer_asset_id', 'alias')),
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    UNIQUE (workspace_id, namespace, value)
);

CREATE TABLE operator_assertions (
    assertion_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    subject_kind TEXT NOT NULL CHECK (subject_kind IN ('asset_identity')),
    subject_id TEXT NOT NULL,
    subject_version INTEGER NOT NULL CHECK (subject_version >= 1),
    field_path TEXT NOT NULL,
    asserted_value_json TEXT NOT NULL,
    reason TEXT NOT NULL,
    evidence_ids_seen_json TEXT NOT NULL,
    observation_basis TEXT NOT NULL CHECK (
        observation_basis IN ('direct_observation', 'nameplate', 'operator_record')
    ),
    decision_id TEXT NOT NULL UNIQUE REFERENCES entity_ids(entity_id),
    operator TEXT NOT NULL,
    supersedes TEXT REFERENCES operator_assertions(assertion_id),
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z')
);

CREATE TABLE audit_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    workspace_id TEXT REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    event_kind TEXT NOT NULL,
    subject_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z')
);

CREATE TRIGGER operator_assertions_no_update
BEFORE UPDATE ON operator_assertions
BEGIN
    SELECT RAISE(ABORT, 'operator_assertions are append-only');
END;

CREATE TRIGGER operator_assertions_no_delete
BEFORE DELETE ON operator_assertions
BEGIN
    SELECT RAISE(ABORT, 'operator_assertions are append-only');
END;

CREATE TRIGGER audit_events_no_update
BEFORE UPDATE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'audit_events are append-only');
END;

CREATE TRIGGER audit_events_no_delete
BEFORE DELETE ON audit_events
BEGIN
    SELECT RAISE(ABORT, 'audit_events are append-only');
END;

