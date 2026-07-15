"""Chat tool catalog (package).

Public surface of the former tools.py: schemas, per-phase availability and
the dispatch entrypoint. Tool implementations live in the phase modules
(scoping, ontology, extraction, review, export, inspect).
"""

from backend.services.conversation.tools.common import (
    _build_ontology_review_payload,
    _build_triplet_graph_payload,
    build_extraction_memory_snapshot,
)
from backend.services.conversation.tools.dispatch import dispatch
from backend.services.conversation.tools.inspect import _explain_decision
from backend.services.conversation.tools.schemas import TOOL_SCHEMAS, tools_for_phase
from backend.services.conversation.tools.scoping import _propose_cut_plan

__all__ = [
    "TOOL_SCHEMAS",
    "_build_ontology_review_payload",
    "_build_triplet_graph_payload",
    "_explain_decision",
    "_propose_cut_plan",
    "build_extraction_memory_snapshot",
    "dispatch",
    "tools_for_phase",
]
