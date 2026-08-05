"""Read-only projection of an operator's progress through one workspace."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.domain.ids import OpaqueId
from backend.domain.sources import SourceKind

JourneyPhaseId = Literal["machine", "documents", "structure", "graph"]


class JourneyState(StrEnum):
    LOCKED = "locked"
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    NEEDS_ATTENTION = "needs_attention"
    COMPLETE = "complete"
    DEFERRED = "deferred"


class JourneyActionCode(StrEnum):
    ADD_SOURCE = "add_source"
    PREPARE_SOURCE = "prepare_source"
    RESOLVE_STRUCTURE = "resolve_structure"
    CONFIRM_STRUCTURE = "confirm_structure"
    GENERATE_GRAPH = "generate_graph"
    REVIEW_GRAPH = "review_graph"
    REVISE_GRAPH = "revise_graph"
    WORKSPACE_READY = "workspace_ready"


class JourneyPhaseView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    phase: JourneyPhaseId
    state: JourneyState
    available: bool
    count: int = Field(default=0, ge=0)
    attention_count: int = Field(default=0, ge=0)


class JourneySourceView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: OpaqueId
    source_name: str
    source_kind: SourceKind
    lifecycle: Literal["active", "archived"]
    structure_state: Literal[
        "not_applicable",
        "not_started",
        "analyzing",
        "needs_attention",
        "ready",
        "confirmed",
        "archived",
    ]
    graph_state: Literal[
        "unavailable",
        "deferred",
        "waiting",
        "ready",
        "reviewing",
        "approved",
        "rejected",
        "archived",
    ]
    graph_revision_id: OpaqueId | None = None
    graph_revision_count: int = Field(default=0, ge=0)
    graph_node_count: int = Field(default=0, ge=0)
    graph_relation_count: int = Field(default=0, ge=0)


class JourneyNextAction(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: JourneyActionCode
    phase: JourneyPhaseId
    source_id: OpaqueId | None = None
    source_name: str | None = None


class WorkspaceJourney(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workspace_id: OpaqueId
    phases: list[JourneyPhaseView]
    sources: list[JourneySourceView]
    next_action: JourneyNextAction
