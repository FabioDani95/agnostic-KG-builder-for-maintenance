CREATE TABLE sources (
    source_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    source_kind TEXT NOT NULL CHECK (
        source_kind IN ('pdf', 'csv', 'xlsx', 'json', 'jsonl', 'operator_input')
    ),
    authority TEXT NOT NULL CHECK (
        authority IN ('normative', 'observational', 'operational', 'informal')
    ),
    file_name TEXT,
    media_type TEXT,
    size_bytes INTEGER CHECK (size_bytes IS NULL OR size_bytes >= 0),
    sha256 TEXT CHECK (sha256 IS NULL OR length(sha256) = 64),
    raw_relpath TEXT,
    language_hints_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL CHECK (
        status IN (
            'uploaded', 'assessing', 'accepted', 'quarantined',
            'excluded', 'duplicate', 'failed_terminal'
        )
    ),
    active_assessment_id TEXT,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    UNIQUE (workspace_id, sha256),
    CHECK (
        source_kind = 'operator_input'
        OR (
            file_name IS NOT NULL AND media_type IS NOT NULL
            AND size_bytes IS NOT NULL AND sha256 IS NOT NULL AND raw_relpath IS NOT NULL
        )
    )
);

CREATE TABLE source_assessments (
    assessment_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    asset_identity_version INTEGER NOT NULL CHECK (asset_identity_version >= 1),
    observed_claims_json TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('compatible', 'uncertain', 'incompatible')),
    reason_codes_json TEXT NOT NULL,
    decided_by_kind TEXT NOT NULL CHECK (
        decided_by_kind IN ('deterministic_rule', 'operator_assertion', 'reopened')
    ),
    decision_id TEXT REFERENCES entity_ids(entity_id),
    operator_assertion_id TEXT REFERENCES entity_ids(entity_id),
    supersedes TEXT REFERENCES source_assessments(assessment_id),
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z')
);

CREATE TABLE source_assessment_assertions (
    assertion_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    assessment_id TEXT NOT NULL REFERENCES source_assessments(assessment_id) ON DELETE RESTRICT,
    asserted_value_json TEXT NOT NULL,
    reason TEXT NOT NULL,
    evidence_seen_json TEXT NOT NULL,
    observation_basis TEXT NOT NULL CHECK (
        observation_basis IN ('direct_observation', 'nameplate', 'operator_record')
    ),
    decision_id TEXT NOT NULL UNIQUE REFERENCES entity_ids(entity_id),
    operator TEXT NOT NULL,
    supersedes TEXT REFERENCES source_assessment_assertions(assertion_id),
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z')
);

CREATE INDEX idx_sources_workspace ON sources(workspace_id, created_at);
CREATE INDEX idx_assessments_source ON source_assessments(source_id, created_at);

CREATE TRIGGER source_assessments_no_update
BEFORE UPDATE ON source_assessments
BEGIN
    SELECT RAISE(ABORT, 'source_assessments are append-only');
END;

CREATE TRIGGER source_assessments_no_delete
BEFORE DELETE ON source_assessments
BEGIN
    SELECT RAISE(ABORT, 'source_assessments are append-only');
END;

CREATE TRIGGER source_assessment_assertions_no_update
BEFORE UPDATE ON source_assessment_assertions
BEGIN
    SELECT RAISE(ABORT, 'source assessment assertions are append-only');
END;

CREATE TRIGGER source_assessment_assertions_no_delete
BEFORE DELETE ON source_assessment_assertions
BEGIN
    SELECT RAISE(ABORT, 'source assessment assertions are append-only');
END;

