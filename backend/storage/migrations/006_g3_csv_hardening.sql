-- Queue blocking mapping decisions so the operator receives one actionable
-- exception at a time. SQLite cannot alter a CHECK constraint in place.
DROP TRIGGER structured_exceptions_no_delete;
DROP INDEX idx_structured_exceptions_profile;

ALTER TABLE structured_exceptions RENAME TO structured_exceptions_legacy;

CREATE TABLE structured_exceptions (
    exception_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    profile_id TEXT NOT NULL REFERENCES structured_profiles(profile_id) ON DELETE RESTRICT,
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    exception_kind TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('blocking', 'warning')),
    status TEXT NOT NULL CHECK (status IN ('open', 'queued', 'resolved', 'acknowledged')),
    title TEXT NOT NULL,
    explanation TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    resolution_json TEXT,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z'),
    resolved_at TEXT CHECK (resolved_at IS NULL OR substr(resolved_at, -1) = 'Z')
);

INSERT INTO structured_exceptions(
    exception_id, profile_id, source_id, exception_kind, severity, status,
    title, explanation, payload_json, resolution_json, created_at, resolved_at
)
SELECT
    exception_id, profile_id, source_id, exception_kind, severity, status,
    title, explanation, payload_json, resolution_json, created_at, resolved_at
FROM structured_exceptions_legacy;

DROP TABLE structured_exceptions_legacy;

CREATE INDEX idx_structured_exceptions_profile
ON structured_exceptions(profile_id, status, created_at);

CREATE TRIGGER structured_exceptions_no_delete
BEFORE DELETE ON structured_exceptions
BEGIN
    SELECT RAISE(ABORT, 'structured_exceptions are auditable and cannot be deleted');
END;
