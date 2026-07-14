"""Post-extraction translation service.

Translates human-readable string fields in an ontology export payload and/or
a list of validated triplets from the source language into the requested
target language.

Design principles:
- Extraction and ontology drafting always operate in the source document language.
- Translation is a separate, final step applied only when target_language != source language.
- Only human-readable free-text fields are translated; IDs, codes, page references,
  relation names, and schema keys are never modified.
- All fields are sent in a single batched LLM call to keep cost minimal.
"""

from __future__ import annotations

import json
import logging
from copy import deepcopy
from typing import Any

from httpx import Timeout

from backend.config import settings
from backend.services.language_utils import language_label, normalize_language_code
from backend.services.llm_gateway import chat_temperature_kwargs, get_client
from backend.services.run_metrics import usage_from_response

logger = logging.getLogger(__name__)

# Fields to translate per ontology node type.
# Keys are node-type names (agnostic — works with any schema).
# Values are the property names containing free text.
_NODE_TEXT_FIELDS: dict[str, list[str]] = {
    "Asset": ["name", "description", "asset_type"],
    "Component": ["name", "description", "category"],
    "Symptom": ["name", "description"],
    "FailureMode": ["name", "description", "material_context"],
    "CorrectiveAction": ["name", "description", "instruction_text"],
    "ErrorCode": ["name", "description"],
}

# Fields to translate per triplet slot.
_TRIPLET_SYMPTOM_FIELDS = ["name", "description"]
_TRIPLET_FM_FIELDS = ["name", "description", "material_context"]
_TRIPLET_CA_FIELDS = ["name", "description", "instruction_text"]

_SYSTEM_PROMPT = """\
You are a technical translation assistant.
You will receive a JSON object whose values are human-readable text strings extracted
from a technical maintenance manual. Translate every value into {target_language_label}.

Rules:
- Translate ONLY the values, never the keys.
- Preserve technical terminology as close as possible to the original.
- Do NOT alter numeric values, codes, IDs, page references (e.g. "PAGE 12"), or units.
- If a value is already in the target language or is empty, keep it unchanged.
- Return valid JSON only. No markdown. No commentary.
"""


def _collect_node_fields(nodes: dict[str, list[dict]]) -> dict[str, str]:
    """Flatten translatable node fields into a flat key→value map."""
    flat: dict[str, str] = {}
    for node_type, node_list in nodes.items():
        text_fields = _NODE_TEXT_FIELDS.get(node_type, [])
        if not text_fields:
            # For unknown node types, translate any string field that looks like free text.
            # Exclude fields ending in _id, _page, _reference, _code.
            text_fields = [
                k for k in (node_list[0].keys() if node_list else [])
                if not any(k.endswith(suffix) for suffix in ("_id", "_page", "_reference", "_code", "_type"))
                and k not in ("source_type", "source_title", "language")
            ]
        for idx, node in enumerate(node_list):
            for field in text_fields:
                val = node.get(field)
                if val and isinstance(val, str) and val.strip():
                    flat[f"node__{node_type}__{idx}__{field}"] = val
    return flat


def _collect_triplet_fields(triplets: list[dict]) -> dict[str, str]:
    """Flatten translatable triplet fields into a flat key→value map."""
    flat: dict[str, str] = {}
    for t_idx, triplet in enumerate(triplets):
        sym = triplet.get("symptom", {})
        for field in _TRIPLET_SYMPTOM_FIELDS:
            val = sym.get(field)
            if val and isinstance(val, str) and val.strip():
                flat[f"triplet__{t_idx}__symptom__{field}"] = val

        for fm_idx, fm in enumerate(triplet.get("failure_modes", [])):
            for field in _TRIPLET_FM_FIELDS:
                val = fm.get(field)
                if val and isinstance(val, str) and val.strip():
                    flat[f"triplet__{t_idx}__fm__{fm_idx}__{field}"] = val

        for ca_idx, ca in enumerate(triplet.get("corrective_actions", [])):
            for field in _TRIPLET_CA_FIELDS:
                val = ca.get(field)
                if val and isinstance(val, str) and val.strip():
                    flat[f"triplet__{t_idx}__ca__{ca_idx}__{field}"] = val

    return flat


def _apply_node_translations(
    nodes: dict[str, list[dict]], translations: dict[str, str]
) -> dict[str, list[dict]]:
    result = deepcopy(nodes)
    for node_type, node_list in result.items():
        for idx, node in enumerate(node_list):
            text_fields = _NODE_TEXT_FIELDS.get(node_type, list(node.keys()))
            for field in text_fields:
                key = f"node__{node_type}__{idx}__{field}"
                if key in translations:
                    node[field] = translations[key]
    return result


def _apply_triplet_translations(
    triplets: list[dict], translations: dict[str, str]
) -> list[dict]:
    result = deepcopy(triplets)
    for t_idx, triplet in enumerate(result):
        sym = triplet.get("symptom", {})
        for field in _TRIPLET_SYMPTOM_FIELDS:
            key = f"triplet__{t_idx}__symptom__{field}"
            if key in translations:
                sym[field] = translations[key]

        for fm_idx, fm in enumerate(triplet.get("failure_modes", [])):
            for field in _TRIPLET_FM_FIELDS:
                key = f"triplet__{t_idx}__fm__{fm_idx}__{field}"
                if key in translations:
                    fm[field] = translations[key]

        for ca_idx, ca in enumerate(triplet.get("corrective_actions", [])):
            for field in _TRIPLET_CA_FIELDS:
                key = f"triplet__{t_idx}__ca__{ca_idx}__{field}"
                if key in translations:
                    ca[field] = translations[key]

    return result


def translate_extraction(
    nodes: dict[str, list[dict]],
    triplets: list[dict],
    target_language: str,
    model_name: str | None = None,
) -> tuple[dict[str, list[dict]], list[dict], dict]:
    """Translate nodes and triplets into target_language.

    Returns (translated_nodes, translated_triplets, usage_dict).
    If target_language is 'en' or no translatable content is found, returns originals unchanged.
    """
    target_lang = normalize_language_code(target_language)
    if target_lang == "en":
        return nodes, triplets, {}

    flat_nodes = _collect_node_fields(nodes)
    flat_triplets = _collect_triplet_fields(triplets)
    flat_all = {**flat_nodes, **flat_triplets}

    if not flat_all:
        return nodes, triplets, {}

    target_label = language_label(target_lang)
    system_prompt = _SYSTEM_PROMPT.format(target_language_label=target_label)
    user_payload = json.dumps(flat_all, ensure_ascii=False)

    client = get_client(timeout=Timeout(120.0, connect=10.0))
    model = model_name or settings.MODEL_NAME
    logger.info(
        "[translation] Translating %d fields to %s using %s",
        len(flat_all), target_label, model,
    )
    try:
        response = client.chat.completions.create(
            model=model,
            **chat_temperature_kwargs(model, 0.0),
            max_completion_tokens=8000,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload},
            ],
        )
    except Exception as exc:
        logger.warning("[translation] Translation call failed: %s — returning originals", exc)
        return nodes, triplets, {}

    raw = response.choices[0].message.content or "{}"
    usage = usage_from_response(response, "translation")

    try:
        translations: dict[str, str] = json.loads(raw)
    except Exception:
        # Try to extract JSON from response
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                translations = json.loads(match.group(0))
            except Exception:
                logger.warning("[translation] Could not parse translation response — returning originals")
                return nodes, triplets, {}
        else:
            logger.warning("[translation] No JSON found in translation response — returning originals")
            return nodes, triplets, {}

    translated_nodes = _apply_node_translations(nodes, translations)
    translated_triplets = _apply_triplet_translations(triplets, translations)
    logger.info("[translation] Translation complete: %d fields translated", len(translations))
    return translated_nodes, translated_triplets, usage
