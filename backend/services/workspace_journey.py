"""Compute one compact, read-only workflow projection for the UI."""

from __future__ import annotations

from backend.domain.journey import (
    JourneyActionCode,
    JourneyNextAction,
    JourneyPhaseView,
    JourneySourceView,
    JourneyState,
    WorkspaceJourney,
)
from backend.domain.sources import SourceKind
from backend.services.source_subgraph_generation import SourceSubgraphGenerationService
from backend.services.structured_preparation import STRUCTURED_KINDS, StructuredPreparationService
from backend.storage.repositories.sources import SourceRepository
from backend.storage.repositories.subgraphs import SourceSubgraphRepository
from backend.storage.repositories.workspaces import WorkspaceRepository


class WorkspaceJourneyService:
    """Project domain state without starting preparation or changing data."""

    def __init__(self) -> None:
        self.workspaces = WorkspaceRepository()
        self.sources = SourceRepository()
        self.subgraphs = SourceSubgraphRepository()

    def snapshot(self, workspace_id: str) -> WorkspaceJourney:
        if self.workspaces.get_by_id(workspace_id) is None:
            raise LookupError(workspace_id)

        active = [
            source for source in self.sources.list_for_workspace(workspace_id)
            if source.source_kind is not SourceKind.OPERATOR_INPUT
        ]
        archived = self.sources.list_archived_for_workspace(workspace_id)
        structure = StructuredPreparationService().snapshot(workspace_id)
        graph = SourceSubgraphGenerationService().snapshot(workspace_id)
        profiles = {item.source_id: item for item in structure.profiles}
        graph_views = {item.source_id: item for item in graph.sources}
        current_revisions = self.subgraphs.current_for_workspace(workspace_id)
        revision_counts = self.subgraphs.revision_counts_for_workspace(workspace_id)

        sources: list[JourneySourceView] = []
        for source in active:
            profile = profiles.get(source.source_id)
            graph_view = graph_views.get(source.source_id)
            revision = graph_view.subgraph if graph_view else None
            sources.append(JourneySourceView(
                source_id=source.source_id,
                source_name=source.file_name or "Fonte",
                source_kind=source.source_kind,
                lifecycle="active",
                structure_state=self._structure_state(source.source_kind, profile),
                graph_state=graph_view.state if graph_view else "unavailable",
                graph_revision_id=(revision.source_subgraph_revision_id if revision else None),
                graph_revision_count=revision_counts.get(source.source_id, 0),
                graph_node_count=(len(revision.nodes) if revision else 0),
                graph_relation_count=(len(revision.relations) if revision else 0),
            ))

        for source in archived:
            revision = current_revisions.get(source.source_id)
            sources.append(JourneySourceView(
                source_id=source.source_id,
                source_name=source.file_name or "Fonte",
                source_kind=source.source_kind,
                lifecycle="archived",
                structure_state="archived",
                graph_state="archived",
                graph_revision_id=(revision.source_subgraph_revision_id if revision else None),
                graph_revision_count=revision_counts.get(source.source_id, 0),
                graph_node_count=(len(revision.nodes) if revision else 0),
                graph_relation_count=(len(revision.relations) if revision else 0),
            ))

        next_action = self._next_action(sources)
        active_sources = [item for item in sources if item.lifecycle == "active"]
        structured_sources = [item for item in active_sources if item.source_kind in STRUCTURED_KINDS]
        incomplete_structure = [item for item in structured_sources if item.structure_state != "confirmed"]
        graph_built = [item for item in active_sources if item.graph_revision_id]
        graph_attention = [
            item for item in active_sources
            if item.graph_state in {"ready", "reviewing", "rejected"}
        ]

        if not active_sources:
            document_state = JourneyState.NEEDS_ATTENTION
            structure_state = JourneyState.LOCKED
            graph_state = JourneyState.LOCKED
        else:
            document_state = JourneyState.COMPLETE
            if not structured_sources:
                structure_state = JourneyState.COMPLETE
            elif incomplete_structure:
                structure_state = (
                    JourneyState.NEEDS_ATTENTION
                    if any(item.structure_state in {"needs_attention", "ready"} for item in incomplete_structure)
                    else JourneyState.IN_PROGRESS
                )
            else:
                structure_state = JourneyState.COMPLETE

            if not structured_sources:
                graph_state = JourneyState.DEFERRED
            elif graph_attention:
                graph_state = JourneyState.NEEDS_ATTENTION
            elif incomplete_structure:
                graph_state = JourneyState.IN_PROGRESS if graph_built else JourneyState.LOCKED
            elif all(item.graph_state == "approved" for item in structured_sources):
                graph_state = JourneyState.COMPLETE
            else:
                graph_state = JourneyState.AVAILABLE

        graph_available = bool(active_sources) and (
            not structured_sources
            or bool(graph_built)
            or not incomplete_structure
        )
        phases = [
            JourneyPhaseView(
                phase="machine", state=JourneyState.COMPLETE, available=True,
            ),
            JourneyPhaseView(
                phase="documents", state=document_state, available=True,
                count=len(active_sources), attention_count=0 if active_sources else 1,
            ),
            JourneyPhaseView(
                phase="structure", state=structure_state, available=bool(active_sources),
                count=sum(
                    int((profiles.get(item.source_id).summary if profiles.get(item.source_id) else {}).get("record_count", 0))
                    for item in structured_sources
                ),
                attention_count=len(incomplete_structure),
            ),
            JourneyPhaseView(
                phase="graph", state=graph_state, available=graph_available,
                count=sum(item.graph_node_count for item in active_sources),
                attention_count=len(graph_attention),
            ),
        ]
        return WorkspaceJourney(
            workspace_id=workspace_id,
            phases=phases,
            sources=sources,
            next_action=next_action,
        )

    @staticmethod
    def _structure_state(source_kind: SourceKind, profile) -> str:
        if source_kind not in STRUCTURED_KINDS:
            return "not_applicable"
        if profile is None:
            return "not_started"
        if profile.state == "analyzing":
            return "analyzing"
        if profile.state in {"needs_attention", "failed"}:
            return "needs_attention"
        return "confirmed" if profile.confirmed else "ready"

    @staticmethod
    def _next_action(sources: list[JourneySourceView]) -> JourneyNextAction:
        active = [item for item in sources if item.lifecycle == "active"]
        if not active:
            return JourneyNextAction(code=JourneyActionCode.ADD_SOURCE, phase="documents")

        priorities = (
            ({"not_started", "analyzing"}, JourneyActionCode.PREPARE_SOURCE),
            ({"needs_attention"}, JourneyActionCode.RESOLVE_STRUCTURE),
            ({"ready"}, JourneyActionCode.CONFIRM_STRUCTURE),
        )
        for states, action in priorities:
            source = next((item for item in active if item.structure_state in states), None)
            if source:
                return JourneyNextAction(
                    code=action, phase="structure", source_id=source.source_id,
                    source_name=source.source_name,
                )

        graph_priorities = (
            ("ready", JourneyActionCode.GENERATE_GRAPH),
            ("reviewing", JourneyActionCode.REVIEW_GRAPH),
            ("rejected", JourneyActionCode.REVISE_GRAPH),
        )
        for state, action in graph_priorities:
            source = next((item for item in active if item.graph_state == state), None)
            if source:
                return JourneyNextAction(
                    code=action, phase="graph", source_id=source.source_id,
                    source_name=source.source_name,
                )

        source = next((item for item in active if item.graph_state == "approved"), None)
        return JourneyNextAction(
            code=JourneyActionCode.WORKSPACE_READY,
            phase="graph" if source else "documents",
            source_id=(source.source_id if source else None),
            source_name=(source.source_name if source else None),
        )
