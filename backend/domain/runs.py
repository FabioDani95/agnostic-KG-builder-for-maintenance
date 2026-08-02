"""Canonical run state and append-only RawUnit disposition contracts."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.domain.ids import OpaqueId, UtcTimestamp


class PreparationState(StrEnum):
    NOT_STARTED = "not_started"
    PROFILING_OR_SCOPING = "profiling_or_scoping"
    AWAITING_OPERATOR = "awaiting_operator"
    READY = "ready"
    INVALIDATED = "invalidated"
    EXCLUDED = "excluded"
    DUPLICATE = "duplicate"
    QUARANTINED = "quarantined"
    FAILED_RESUMABLE = "failed_resumable"
    FAILED_TERMINAL = "failed_terminal"


class RunState(StrEnum):
    CREATED = "created"
    PREFLIGHT = "preflight"
    READY = "ready"
    PROCESSING = "processing"
    PAUSING = "pausing"
    PAUSED = "paused"
    AWAITING_REVIEW = "awaiting_review"
    READY_TO_PUBLISH = "ready_to_publish"
    PUBLISHED = "published"
    FAILED_RESUMABLE = "failed_resumable"
    FAILED_TERMINAL = "failed_terminal"
    CANCELLED = "cancelled"
    SUPERSEDED = "superseded"


class DispositionOutcome(StrEnum):
    PROCESSED = "processed"
    DUPLICATE = "duplicate"
    EXCLUDED = "excluded"
    QUARANTINED = "quarantined"
    FAILED = "failed"


class Retryability(StrEnum):
    SAME_RUN = "same_run"
    NEW_RUN_REQUIRED = "new_run_required"
    NOT_RETRYABLE = "not_retryable"
    NOT_APPLICABLE = "not_applicable"


_RESUMABLE_STATES = {
    RunState.PREFLIGHT,
    RunState.READY,
    RunState.PROCESSING,
    RunState.AWAITING_REVIEW,
    RunState.READY_TO_PUBLISH,
}


class Run(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: OpaqueId
    workspace_id: OpaqueId
    state: RunState
    resume_state: RunState | None = None
    config_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    config: dict[str, Any]
    manifest: dict[str, Any]
    state_changed_at: UtcTimestamp
    created_at: UtcTimestamp
    updated_at: UtcTimestamp

    @model_validator(mode="after")
    def validate_resume_state(self) -> "Run":
        suspended = {
            RunState.PAUSING,
            RunState.PAUSED,
            RunState.FAILED_RESUMABLE,
        }
        if self.state in suspended and self.resume_state not in _RESUMABLE_STATES:
            raise ValueError("Suspended/resumable runs require an operational resume_state")
        if self.state not in suspended and self.resume_state is not None:
            raise ValueError("resume_state must be null outside suspended/resumable states")
        return self


class DispositionError(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(min_length=1)
    title: str = Field(min_length=1)
    object_ref: str = Field(min_length=1)
    cause: str = Field(min_length=1)
    preserved: str = Field(min_length=1)
    action: str = Field(min_length=1)
    technical_detail: str = Field(min_length=1)


class RawUnitDisposition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    disposition_id: OpaqueId
    run_id: OpaqueId
    raw_unit_id: OpaqueId
    attempt: int = Field(ge=1)
    outcome: DispositionOutcome
    reason_code: str = Field(min_length=1)
    canonical_raw_unit_id: OpaqueId | None = None
    evidence_ids: list[OpaqueId] = Field(default_factory=list)
    checkpoint_id: OpaqueId | None = None
    retryability: Retryability = Retryability.NOT_APPLICABLE
    error: DispositionError | None = None
    created_at: UtcTimestamp

    @model_validator(mode="after")
    def outcome_fields_are_consistent(self) -> "RawUnitDisposition":
        if self.outcome is DispositionOutcome.DUPLICATE and self.canonical_raw_unit_id is None:
            raise ValueError("duplicate dispositions require canonical_raw_unit_id")
        if self.outcome is not DispositionOutcome.DUPLICATE and self.canonical_raw_unit_id is not None:
            raise ValueError("canonical_raw_unit_id is valid only for duplicate dispositions")
        if self.outcome is DispositionOutcome.FAILED:
            if self.error is None or self.retryability is Retryability.NOT_APPLICABLE:
                raise ValueError("failed dispositions require structured error and retryability")
        elif self.error is not None or self.retryability is not Retryability.NOT_APPLICABLE:
            raise ValueError("non-failed dispositions use retryability=not_applicable and no error")
        return self


_DIRECT_RUN_TRANSITIONS: dict[RunState, set[RunState]] = {
    RunState.CREATED: {RunState.PREFLIGHT},
    RunState.PREFLIGHT: {RunState.READY},
    RunState.READY: {RunState.PROCESSING},
    RunState.PROCESSING: {RunState.AWAITING_REVIEW},
    RunState.AWAITING_REVIEW: {RunState.PROCESSING, RunState.READY_TO_PUBLISH},
    RunState.READY_TO_PUBLISH: {RunState.AWAITING_REVIEW, RunState.PUBLISHED},
}
_OPERATIONAL_NON_TERMINAL = {
    RunState.CREATED,
    RunState.PREFLIGHT,
    RunState.READY,
    RunState.PROCESSING,
    RunState.AWAITING_REVIEW,
    RunState.READY_TO_PUBLISH,
}


def validate_run_transition(
    current: RunState,
    target: RunState,
    *,
    current_resume_state: RunState | None = None,
    target_resume_state: RunState | None = None,
) -> None:
    """Mirror the DB transition guard so invalid calls fail before persistence."""
    if current in _OPERATIONAL_NON_TERMINAL and target in {
        RunState.CANCELLED,
        RunState.SUPERSEDED,
        RunState.FAILED_TERMINAL,
    }:
        return
    if current in _RESUMABLE_STATES and target is RunState.FAILED_RESUMABLE:
        if target_resume_state is current:
            return
    if current in _RESUMABLE_STATES and target is RunState.PAUSING:
        if target_resume_state is current:
            return
    if current is RunState.PAUSING and target is RunState.PAUSED:
        if target_resume_state is current_resume_state:
            return
    if current in {RunState.PAUSED, RunState.FAILED_RESUMABLE}:
        if target is current_resume_state and target_resume_state is None:
            return
        if target in {RunState.CANCELLED, RunState.SUPERSEDED, RunState.FAILED_TERMINAL}:
            return
    if target in _DIRECT_RUN_TRANSITIONS.get(current, set()) and target_resume_state is None:
        return
    raise ValueError(f"Invalid run transition: {current.value} -> {target.value}")
