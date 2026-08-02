CREATE TABLE runs (
    run_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    state TEXT NOT NULL CHECK (
        state IN (
            'created', 'preflight', 'ready', 'processing', 'pausing', 'paused',
            'awaiting_review', 'ready_to_publish', 'published',
            'failed_resumable', 'failed_terminal', 'cancelled', 'superseded'
        )
    ),
    resume_state TEXT CHECK (
        resume_state IS NULL OR resume_state IN (
            'preflight', 'ready', 'processing', 'awaiting_review', 'ready_to_publish'
        )
    ),
    config_hash TEXT NOT NULL CHECK (length(config_hash) = 64),
    config_json TEXT NOT NULL,
    manifest_json TEXT NOT NULL,
    state_changed_at TEXT NOT NULL CHECK (substr(state_changed_at, -1) = 'Z'),
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    updated_at TEXT NOT NULL CHECK (substr(updated_at, -1) = 'Z'),
    CHECK (
        (state IN ('pausing', 'paused', 'failed_resumable') AND resume_state IS NOT NULL)
        OR
        (state NOT IN ('pausing', 'paused', 'failed_resumable') AND resume_state IS NULL)
    )
);

CREATE TABLE run_sources (
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE RESTRICT,
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    PRIMARY KEY (run_id, source_id)
);

CREATE TABLE raw_units (
    raw_unit_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    parent_raw_unit_id TEXT REFERENCES raw_units(raw_unit_id) ON DELETE RESTRICT,
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    unit_kind TEXT NOT NULL,
    structure_id TEXT,
    locator_json TEXT NOT NULL,
    locator_hash TEXT NOT NULL CHECK (length(locator_hash) = 64),
    raw_hash TEXT NOT NULL CHECK (length(raw_hash) = 64),
    adapter_version TEXT NOT NULL,
    quality_flags_json TEXT NOT NULL,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z')
);

CREATE TABLE raw_unit_dispositions (
    disposition_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    run_id TEXT NOT NULL REFERENCES runs(run_id) ON DELETE RESTRICT,
    raw_unit_id TEXT NOT NULL REFERENCES raw_units(raw_unit_id) ON DELETE RESTRICT,
    attempt INTEGER NOT NULL CHECK (attempt >= 1),
    outcome TEXT NOT NULL CHECK (
        outcome IN ('processed', 'duplicate', 'excluded', 'quarantined', 'failed')
    ),
    reason_code TEXT NOT NULL CHECK (length(trim(reason_code)) > 0),
    canonical_raw_unit_id TEXT REFERENCES raw_units(raw_unit_id) ON DELETE RESTRICT,
    evidence_ids_json TEXT NOT NULL,
    checkpoint_id TEXT,
    retryability TEXT NOT NULL CHECK (
        retryability IN ('same_run', 'new_run_required', 'not_retryable', 'not_applicable')
    ),
    error_json TEXT,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    UNIQUE (run_id, raw_unit_id, attempt),
    CHECK (
        (outcome = 'duplicate' AND canonical_raw_unit_id IS NOT NULL)
        OR (outcome != 'duplicate' AND canonical_raw_unit_id IS NULL)
    ),
    CHECK (
        (outcome = 'failed' AND error_json IS NOT NULL AND retryability != 'not_applicable')
        OR
        (outcome != 'failed' AND error_json IS NULL AND retryability = 'not_applicable')
    )
);

CREATE VIEW active_raw_unit_dispositions AS
SELECT d.*
FROM raw_unit_dispositions d
WHERE d.attempt = (
    SELECT MAX(candidate.attempt)
    FROM raw_unit_dispositions candidate
    WHERE candidate.run_id = d.run_id AND candidate.raw_unit_id = d.raw_unit_id
);

CREATE INDEX idx_runs_workspace ON runs(workspace_id, created_at);
CREATE INDEX idx_run_sources_source ON run_sources(source_id, run_id);
CREATE INDEX idx_raw_units_source_parent ON raw_units(source_id, parent_raw_unit_id);
CREATE INDEX idx_dispositions_run_raw ON raw_unit_dispositions(run_id, raw_unit_id, attempt);

CREATE TRIGGER raw_units_no_update
BEFORE UPDATE ON raw_units
BEGIN
    SELECT RAISE(ABORT, 'raw_units are immutable');
END;

CREATE TRIGGER raw_units_no_delete
BEFORE DELETE ON raw_units
BEGIN
    SELECT RAISE(ABORT, 'raw_units are immutable');
END;

CREATE TRIGGER raw_unit_dispositions_no_update
BEFORE UPDATE ON raw_unit_dispositions
BEGIN
    SELECT RAISE(ABORT, 'raw_unit_dispositions are append-only');
END;

CREATE TRIGGER raw_unit_dispositions_no_delete
BEFORE DELETE ON raw_unit_dispositions
BEGIN
    SELECT RAISE(ABORT, 'raw_unit_dispositions are append-only');
END;

CREATE TRIGGER runs_immutable_inputs
BEFORE UPDATE OF workspace_id, config_hash, config_json, created_at ON runs
BEGIN
    SELECT RAISE(ABORT, 'run logical inputs are immutable');
END;

CREATE TRIGGER source_state_transition_guard
BEFORE UPDATE OF status ON sources
WHEN NEW.status != OLD.status
BEGIN
    SELECT CASE WHEN NOT (
        (OLD.status = 'uploaded' AND NEW.status = 'assessing')
        OR
        (OLD.status = 'assessing' AND NEW.status IN (
            'accepted', 'quarantined', 'excluded', 'duplicate', 'failed_terminal'
        ))
        OR
        (OLD.status = 'quarantined' AND NEW.status IN ('assessing', 'excluded'))
        OR
        (OLD.status = 'accepted' AND NEW.status = 'assessing')
    ) THEN RAISE(ABORT, 'invalid Source state transition') END;
END;

CREATE TRIGGER preparation_state_transition_guard
BEFORE UPDATE OF state ON preparations
WHEN NEW.state != OLD.state
BEGIN
    SELECT CASE WHEN NOT (
        (OLD.state = 'not_started' AND NEW.state = 'profiling_or_scoping')
        OR
        (OLD.state = 'profiling_or_scoping' AND NEW.state IN (
            'awaiting_operator', 'ready', 'failed_resumable', 'failed_terminal'
        ))
        OR
        (OLD.state = 'awaiting_operator' AND NEW.state IN (
            'profiling_or_scoping', 'ready', 'excluded', 'quarantined'
        ))
        OR
        (OLD.state = 'ready' AND NEW.state = 'invalidated')
        OR
        (OLD.state = 'invalidated' AND NEW.state = 'profiling_or_scoping')
    ) THEN RAISE(ABORT, 'invalid Preparation state transition') END;
END;

CREATE TRIGGER run_state_transition_guard
BEFORE UPDATE OF state, resume_state ON runs
WHEN NEW.state != OLD.state OR NEW.resume_state IS NOT OLD.resume_state
BEGIN
    SELECT CASE WHEN NOT (
        (OLD.state = 'created' AND NEW.state = 'preflight' AND NEW.resume_state IS NULL)
        OR (OLD.state = 'preflight' AND NEW.state = 'ready' AND NEW.resume_state IS NULL)
        OR (OLD.state = 'ready' AND NEW.state = 'processing' AND NEW.resume_state IS NULL)
        OR (OLD.state = 'processing' AND NEW.state = 'awaiting_review' AND NEW.resume_state IS NULL)
        OR (OLD.state = 'awaiting_review' AND NEW.state IN ('processing', 'ready_to_publish') AND NEW.resume_state IS NULL)
        OR (OLD.state = 'ready_to_publish' AND NEW.state IN ('awaiting_review', 'published') AND NEW.resume_state IS NULL)
        OR (
            OLD.state IN ('preflight', 'ready', 'processing', 'awaiting_review', 'ready_to_publish')
            AND NEW.state IN ('pausing', 'failed_resumable')
            AND NEW.resume_state = OLD.state
        )
        OR (OLD.state = 'pausing' AND NEW.state = 'paused' AND NEW.resume_state = OLD.resume_state)
        OR (
            OLD.state IN ('paused', 'failed_resumable')
            AND NEW.state = OLD.resume_state
            AND NEW.resume_state IS NULL
        )
        OR (
            OLD.state IN (
                'created', 'preflight', 'ready', 'processing', 'pausing', 'paused',
                'awaiting_review', 'ready_to_publish', 'failed_resumable'
            )
            AND NEW.state IN ('cancelled', 'superseded', 'failed_terminal')
            AND NEW.resume_state IS NULL
        )
    ) THEN RAISE(ABORT, 'invalid Run state transition') END;
END;
