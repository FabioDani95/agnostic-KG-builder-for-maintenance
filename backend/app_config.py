"""Load and expose application configuration from config.yaml."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from functools import lru_cache

import yaml

from backend.config import settings

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


@lru_cache(maxsize=1)
def _load_raw() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_config() -> dict:
    """Return the full config dict (cached)."""
    return _load_raw()


def get_scoping_config() -> dict:
    return _normalized_section("scoping")


def get_extraction_config() -> dict:
    return _normalized_section("extraction")


def get_ontology_config() -> dict:
    return load_config().get("ontology", {})


def get_reflective_loop_config() -> dict:
    return load_config().get("reflective_loop", {})


def get_confidence_config() -> dict:
    """Return the Step 3 confidence-scoring configuration with safe defaults.

    The confidence layer is schema-aware: weights and penalties are documented in
    config.yaml and the scorer reads them at runtime, so tweaking this section
    never requires a code change.
    """
    raw = deepcopy(load_config().get("confidence", {}) or {})
    raw.setdefault("enabled", True)
    raw.setdefault("theta_high", 0.80)
    raw.setdefault("theta_low", 0.45)
    raw.setdefault("auto_reject_enabled", False)
    weights = raw.setdefault("weights", {})
    weights.setdefault("evidence_present", 0.25)
    weights.setdefault("corroboration", 0.15)
    weights.setdefault("required_props_complete", 0.25)
    weights.setdefault("chain_participation", 0.20)
    weights.setdefault("clean_extraction", 0.15)
    penalties = raw.setdefault("penalties", {})
    penalties.setdefault("human_binding_required", 0.20)
    penalties.setdefault("per_retry", 0.05)
    return raw


def get_pipeline_config() -> dict:
    cfg = deepcopy(load_config().get("pipeline", {}) or {})
    cfg["mode"] = "multi_agent"
    return cfg


def get_pdf_ingestion_config() -> dict:
    cfg = deepcopy(load_config().get("pdf_ingestion", {}) or {})
    cfg.setdefault("preserve_all_pages", True)
    ocr = cfg.setdefault("ocr", {})
    ocr.setdefault("enabled", True)
    ocr.setdefault("language", "eng")
    ocr.setdefault("dpi", 200)
    ocr.setdefault("min_native_chars", 80)
    ocr.setdefault("bootstrap_pages", 15)
    ocr.setdefault("bootstrap_max_pages", 5)
    ocr.setdefault("selected_max_pages", 24)
    return cfg


def get_agents_config() -> dict:
    return deepcopy(load_config().get("agents", {}))


def get_agent_config(agent_name: str) -> dict:
    return deepcopy((load_config().get("agents", {}) or {}).get(agent_name, {}))


def get_supervisor_config() -> dict:
    return deepcopy(load_config().get("supervisor", {}))


def get_checkpointing_config() -> dict:
    return deepcopy(load_config().get("checkpointing", {}))


def get_validation_config() -> dict:
    cfg = deepcopy(load_config().get("validation", {}))
    cfg.setdefault("grounding_accept_threshold", 0.8)
    cfg.setdefault("grounding_refine_threshold", 0.5)
    cfg.setdefault("check_ontology_chain", True)
    cfg.setdefault("check_page_attribution", True)
    return cfg


def get_resolution_completion_config() -> dict:
    cfg = deepcopy(load_config().get("resolution_completion", {}) or {})
    cfg.setdefault("enabled", True)
    cfg.setdefault("timeout_seconds", 90)
    cfg.setdefault("max_input_chars", 50000)
    cfg.setdefault("estimated_max_input_tokens", 12500)
    cfg.setdefault("max_output_tokens", 2500)
    cfg.setdefault("max_targets", 0)
    cfg.setdefault("top_pages_per_target", 6)
    cfg.setdefault("context_window_pages", 1)
    cfg.setdefault("search_full_manual", True)
    return cfg


def get_coverage_completion_config() -> dict:
    cfg = deepcopy(load_config().get("coverage_completion", {}) or {})
    cfg.setdefault("enabled", True)
    cfg.setdefault("timeout_seconds", 120)
    cfg.setdefault("max_input_chars", 120000)
    cfg.setdefault("estimated_max_input_tokens", 30000)
    cfg.setdefault("max_output_tokens", 6000)
    cfg.setdefault("max_chains", 12)
    return cfg


def get_chat_config() -> dict:
    cfg = deepcopy(load_config().get("chat", {}) or {})
    cfg.setdefault("model", "gpt-4o-mini")
    cfg.setdefault("timeout", 30)
    cfg.setdefault("max_output_tokens", 1500)
    cfg.setdefault("critic_model", cfg["model"])
    cfg.setdefault("critic_enabled", True)
    cfg.setdefault("idle_reminder_seconds", 60)
    return cfg


def get_graph_cocreator_config() -> dict:
    cfg = deepcopy(load_config().get("graph_cocreator", {}) or {})
    chat_cfg = get_chat_config()
    cfg.setdefault("llm_enabled", True)
    cfg.setdefault("model", chat_cfg.get("model", "gpt-4o-mini"))
    cfg.setdefault("timeout_seconds", 12)
    cfg.setdefault("max_output_tokens", 1200)
    cfg.setdefault("temperature", 0.1)
    cfg.setdefault("relationship_candidate_limit", 30)
    cfg.setdefault("relationship_llm_top_k", 12)
    return cfg


def get_style_cleanup_config() -> dict:
    cfg = deepcopy(load_config().get("style_cleanup", {}))
    cfg.setdefault("enabled", True)
    cfg.setdefault("deterministic_enabled", True)
    cfg.setdefault("llm_enabled", True)
    cfg.setdefault("timeout_seconds", 120)
    cfg.setdefault("max_output_tokens", 6000)
    cfg.setdefault("preserve_numbers_units_codes", True)
    cfg.setdefault("preserve_page_refs", True)
    cfg.setdefault("reject_on_semantic_drift", True)
    cfg.setdefault("max_name_tokens", 10)
    cfg.setdefault("max_description_sentences", 2)
    editable_fields = cfg.setdefault("editable_fields", {})
    editable_fields.setdefault("Asset", ["name", "description"])
    editable_fields.setdefault("Component", ["name", "description", "category"])
    editable_fields.setdefault("Symptom", ["name", "description"])
    editable_fields.setdefault("FailureMode", ["name", "description", "material_context"])
    editable_fields.setdefault("CorrectiveAction", ["name", "description", "instruction_text"])
    editable_fields.setdefault("ErrorCode", ["name", "description"])
    return cfg


def reload_config() -> dict:
    """Force-reload from disk (e.g. after user edits the file)."""
    _load_raw.cache_clear()
    return load_config()


_runtime_overrides: dict = {}


def get_runtime_overrides() -> dict:
    return dict(_runtime_overrides)


def apply_runtime_overrides(overrides: dict) -> None:
    """Merge caller-supplied overrides into the runtime overlay."""
    _runtime_overrides.update(overrides)


def get_effective_small_doc_threshold() -> int:
    if "small_doc_threshold" in _runtime_overrides:
        return int(_runtime_overrides["small_doc_threshold"])
    return int(get_scoping_config().get("small_doc_threshold", 15))


def get_effective_reflective_loop_config() -> dict:
    cfg = dict(get_reflective_loop_config())
    if "max_retries" in _runtime_overrides:
        cfg["max_retries"] = int(_runtime_overrides["max_retries"])
    if "retry_on_severity" in _runtime_overrides:
        cfg["retry_on_severity"] = str(_runtime_overrides["retry_on_severity"])
    return cfg


def _normalized_section(section_name: str) -> dict:
    section = deepcopy(load_config().get(section_name, {}))
    models = section.get("models", [])
    if not isinstance(models, list):
        return section

    default_id = settings.MODEL_NAME
    has_explicit_default = any(model.get("default") for model in models if isinstance(model, dict))
    selected_default = None
    if has_explicit_default:
        selected_default = next(
            (model.get("id") for model in models if isinstance(model, dict) and model.get("default")),
            None,
        )
    elif any(isinstance(model, dict) and model.get("id") == default_id for model in models):
        selected_default = default_id
    elif models and isinstance(models[0], dict):
        selected_default = models[0].get("id")

    normalized_models = []
    for model in models:
        if not isinstance(model, dict):
            continue
        item = dict(model)
        item["default"] = item.get("id") == selected_default
        normalized_models.append(item)
    section["models"] = normalized_models
    return section
