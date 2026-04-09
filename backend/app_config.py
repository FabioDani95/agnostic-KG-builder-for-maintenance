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


def reload_config() -> dict:
    """Force-reload from disk (e.g. after user edits the file)."""
    _load_raw.cache_clear()
    return load_config()


# In-memory overrides applied by the frontend without touching config.yaml.
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
