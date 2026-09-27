"""Configuration from config.yaml: how PDF manuals are read."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


@lru_cache(maxsize=1)
def load_config() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


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
    ocr.setdefault("inventory_max_pages", ocr["selected_max_pages"])
    ocr.setdefault("min_confidence", 0.80)
    return cfg
