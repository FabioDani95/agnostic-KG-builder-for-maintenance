-- EvidenceUnits are immutable claims, not mutable row slots. A new structured
-- mapping of the same raw row creates a new evidence revision, while the
-- active structured profile selects which revision is visible to generation.
CREATE TABLE scope_evidence_backup AS
SELECT scope_id, evidence_id FROM scope_evidence;

CREATE TABLE structured_evidence_backup AS
SELECT profile_id, evidence_id FROM structured_evidence;

DROP TABLE scope_evidence;
DROP TABLE structured_evidence;
DROP TRIGGER evidence_units_no_update;
DROP TRIGGER evidence_units_no_delete;
DROP INDEX idx_evidence_workspace;

ALTER TABLE evidence_units RENAME TO evidence_units_legacy;

CREATE TABLE evidence_units (
    evidence_id TEXT PRIMARY KEY REFERENCES entity_ids(entity_id),
    workspace_id TEXT NOT NULL REFERENCES workspaces(workspace_id) ON DELETE RESTRICT,
    asset_id TEXT NOT NULL REFERENCES assets(asset_id) ON DELETE RESTRICT,
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE RESTRICT,
    raw_unit_id TEXT NOT NULL,
    locator_hash TEXT NOT NULL CHECK (length(locator_hash) = 64),
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL CHECK (substr(created_at, -1) = 'Z')
);

INSERT INTO evidence_units(
    evidence_id, workspace_id, asset_id, source_id, raw_unit_id,
    locator_hash, payload_json, created_at
)
SELECT
    evidence_id, workspace_id, asset_id, source_id, raw_unit_id,
    locator_hash, payload_json, created_at
FROM evidence_units_legacy;

DROP TABLE evidence_units_legacy;

CREATE INDEX idx_evidence_workspace ON evidence_units(workspace_id, source_id);

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

CREATE TABLE scope_evidence (
    scope_id TEXT NOT NULL REFERENCES pdf_scopes(scope_id) ON DELETE RESTRICT,
    evidence_id TEXT NOT NULL REFERENCES evidence_units(evidence_id) ON DELETE RESTRICT,
    PRIMARY KEY (scope_id, evidence_id)
);

INSERT INTO scope_evidence(scope_id, evidence_id)
SELECT scope_id, evidence_id FROM scope_evidence_backup;

DROP TABLE scope_evidence_backup;

CREATE TABLE structured_evidence (
    profile_id TEXT NOT NULL REFERENCES structured_profiles(profile_id) ON DELETE RESTRICT,
    evidence_id TEXT NOT NULL REFERENCES evidence_units(evidence_id) ON DELETE RESTRICT,
    PRIMARY KEY (profile_id, evidence_id)
);

INSERT INTO structured_evidence(profile_id, evidence_id)
SELECT profile_id, evidence_id FROM structured_evidence_backup;

DROP TABLE structured_evidence_backup;
