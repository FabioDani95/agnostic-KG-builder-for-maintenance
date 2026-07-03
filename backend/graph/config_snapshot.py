from __future__ import annotations

from copy import deepcopy
from typing import Any

from backend.app_config import (
    get_agents_config,
    get_checkpointing_config,
    get_effective_reflective_loop_config,
    get_extraction_config,
    get_ontology_config,
    get_pipeline_config,
    get_runtime_overrides,
    get_scoping_config,
    get_style_cleanup_config,
    get_supervisor_config,
    get_validation_config,
)


def default_selected_models() -> dict[str, str | None]:
    return {
        "scoping": None,
        "ontology_draft": None,
        "extraction": None,
    }


def build_config_snapshot() -> dict[str, Any]:
    return {
        "pipeline": deepcopy(get_pipeline_config()),
        "agents": deepcopy(get_agents_config()),
        "scoping": deepcopy(get_scoping_config()),
        "extraction": deepcopy(get_extraction_config()),
        "ontology": deepcopy(get_ontology_config()),
        "validation": deepcopy(get_validation_config()),
        "style_cleanup": deepcopy(get_style_cleanup_config()),
        "supervisor": deepcopy(get_supervisor_config()),
        "checkpointing": deepcopy(get_checkpointing_config()),
        "reflective_loop": deepcopy(get_effective_reflective_loop_config()),
        "runtime_overrides": deepcopy(get_runtime_overrides()),
    }
