-- Product Owner simplification: uploading a supported file is the acceptance decision.
-- Existing quarantined uploads become active; removal remains recoverable by re-upload.
UPDATE sources SET status = 'assessing' WHERE status = 'quarantined';
UPDATE sources SET status = 'accepted' WHERE status = 'assessing';

DROP TRIGGER source_state_transition_guard;

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
        (OLD.status = 'accepted' AND NEW.status IN ('assessing', 'excluded'))
        OR
        (OLD.status = 'excluded' AND NEW.status = 'accepted')
    ) THEN RAISE(ABORT, 'invalid Source state transition') END;
END;
