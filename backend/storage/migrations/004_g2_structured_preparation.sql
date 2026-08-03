CREATE TABLE structured_profiles (
    profile_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    version INTEGER NOT NULL CHECK (version >= 1),
    fingerprint TEXT NOT NULL CHECK (length(fingerprint) = 64),
    state TEXT NOT NULL CHECK (state IN ('analyzing', 'needs_attention', 'prepared', 'failed')),
    profile_json TEXT NOT NULL,
    mapping_json TEXT NOT NULL,
    summary_json TEXT NOT NULL,
    run_id TEXT REFERENCES runs(run_id) ON DELETE RESTRICT,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    updated_at TEXT NOT NULL CHECK (substr(updated_at, -1) = 'Z'),
    UNIQUE (source_id, version)
);

CREATE TABLE structured_exceptions (
    exception_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    profile_id TEXT NOT NULL REFERENCES structured_profiles(profile_id) ON DELETE RESTRICT,
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    exception_kind TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('blocking', 'warning')),
    status TEXT NOT NULL CHECK (status IN ('open', 'resolved', 'acknowledged')),
    title TEXT NOT NULL,
    explanation TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    resolution_json TEXT,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    resolved_at TEXT CHECK (resolved_at IS NULL OR substr(resolved_at, -1) = 'Z')
);

CREATE TABLE structured_evidence (
    profile_id TEXT NOT NULL REFERENCES structured_profiles(profile_id) ON DELETE RESTRICT,
    evidence_id TEXT NOT NULL REFERENCES evidence_units(evidence_id) ON DELETE RESTRICT,
    PRIMARY KEY (profile_id, evidence_id)
);

CREATE TABLE join_specs (
    join_spec_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    version INTEGER NOT NULL CHECK (version >= 1),
    primary_profile_id TEXT NOT NULL REFERENCES structured_profiles(profile_id) ON DELETE RESTRICT,
    lookup_profile_id TEXT NOT NULL REFERENCES structured_profiles(profile_id) ON DELETE RESTRICT,
    status TEXT NOT NULL CHECK (status IN ('proposed', 'approved', 'rejected')),
    spec_json TEXT NOT NULL,
    preview_json TEXT NOT NULL,
    decision_json TEXT,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    decided_at TEXT CHECK (decided_at IS NULL OR substr(decided_at, -1) = 'Z'),
    UNIQUE (workspace_id, primary_profile_id, lookup_profile_id, version)
);

CREATE INDEX idx_structured_profiles_workspace ON structured_profiles(workspace_id, source_id, version);
CREATE INDEX idx_structured_exceptions_profile ON structured_exceptions(profile_id, status, created_at);
CREATE INDEX idx_join_specs_workspace ON join_specs(workspace_id, status, created_at);

CREATE TRIGGER structured_profiles_no_delete
BEFORE DELETE ON structured_profiles
BEGIN
    SELECT RAISE(ABORT, 'structured_profiles are versioned and cannot be deleted');
END;

CREATE TRIGGER structured_exceptions_no_delete
BEFORE DELETE ON structured_exceptions
BEGIN
    SELECT RAISE(ABORT, 'structured_exceptions are auditable and cannot be deleted');
END;

CREATE TRIGGER join_specs_no_delete
BEFORE DELETE ON join_specs
BEGIN
    SELECT RAISE(ABORT, 'join_specs are versioned and cannot be deleted');
END;
