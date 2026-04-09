from __future__ import annotations

SUPPORTED_LANGUAGE_CODES = {"en", "it", "de"}

_LANGUAGE_LABELS = {
    "en": "English",
    "it": "Italian",
    "de": "German",
}

_FREETEXT_FIELD_HINTS = {
    "en": "Write all human-readable field values in English.",
    "it": "Write all human-readable field values in Italian.",
    "de": "Write all human-readable field values in German.",
}


def normalize_language_code(value: str | None, default: str = "en") -> str:
    raw = (value or "").strip().lower()
    if raw in SUPPORTED_LANGUAGE_CODES:
        return raw

    aliases = {
        "english": "en",
        "inglese": "en",
        "italian": "it",
        "italiano": "it",
        "german": "de",
        "tedesco": "de",
        "deutsch": "de",
    }
    return aliases.get(raw, default)


def language_label(code: str) -> str:
    return _LANGUAGE_LABELS.get(normalize_language_code(code), _LANGUAGE_LABELS["en"])


def freetext_language_hint(code: str) -> str:
    return _FREETEXT_FIELD_HINTS.get(
        normalize_language_code(code),
        _FREETEXT_FIELD_HINTS["en"],
    )
