from __future__ import annotations

SUPPORTED_LANGUAGE_CODES = {"en", "it", "de"}

_LANGUAGE_LABELS = {
    "en": "English",
    "it": "Italian",
    "de": "German",
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
