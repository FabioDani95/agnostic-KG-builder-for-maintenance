from __future__ import annotations

import re

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


# Grammar words, not vocabulary: they are the part of a sentence that does not
# change with the subject, so a maintenance log about pumps and one about
# burners score the same way.  Tokens that exist in more than one of the three
# languages ("in", "a", "e", "no", "come", "per", "die" as an English verb) are
# left out of every set: they would add noise to all three scores at once and
# to none of them decisively.
_GRAMMAR_WORDS: dict[str, frozenset[str]] = {
    "en": frozenset({
        "the", "and", "or", "but", "not", "with", "without", "from", "this", "that",
        "these", "those", "after", "before", "during", "while", "when", "then", "than",
        "there", "they", "them", "their", "its", "it", "was", "were", "is", "are", "be",
        "been", "being", "has", "have", "had", "does", "did", "of", "to", "at", "by",
        "on", "for", "into", "out", "off", "over", "under", "again", "because", "about",
        "would", "could", "should", "may", "might", "must", "can", "will", "any", "each",
        "some", "such", "until", "only", "still", "all", "we", "you", "an",
    }),
    "it": frozenset({
        "il", "lo", "la", "gli", "le", "un", "uno", "una", "di", "del", "dello", "della",
        "dei", "degli", "delle", "dal", "dallo", "dalla", "dai", "dagli", "dalle", "nel",
        "nello", "nella", "nei", "negli", "nelle", "col", "sul", "sullo", "sulla", "sui",
        "sugli", "sulle", "al", "allo", "alla", "ai", "agli", "alle", "con", "su", "tra",
        "fra", "che", "chi", "non", "più", "meno", "quando", "dopo", "prima", "durante",
        "ma", "però", "anche", "ancora", "già", "sono", "era", "erano", "stato", "stata",
        "essere", "avere", "ha", "hanno", "aveva", "si", "ci", "se", "questo", "questa",
        "quello", "quella", "questi", "queste", "dove", "perché", "sia", "viene",
    }),
    "de": frozenset({
        "der", "das", "den", "dem", "des", "ein", "eine", "einen", "einem", "eines",
        "einer", "und", "oder", "aber", "nicht", "kein", "keine", "keinen", "ist",
        "sind", "waren", "wurde", "wurden", "wird", "werden", "sein",
        "haben", "hatte", "hatten", "mit", "ohne", "für", "von", "vom", "zum", "zur",
        "zu", "auf", "aus", "bei", "beim", "nach", "vor", "über", "unter", "durch",
        "sich", "nur", "noch", "schon", "auch", "wenn", "weil", "dass", "als", "wie",
        "es", "sie", "er", "ich", "wir", "diese", "dieser", "dieses",
    }),
}

# Letters that only one of the three languages writes.  They decide a sentence
# that has no grammar word at all — a caption, a two-word note.
_ALPHABET_MARKS = {"de": "äöüßÄÖÜ", "it": "àèéìòùÀÈÉÌÒÙ"}

_WORDS = re.compile(r"[^\W\d_]+", re.UNICODE)


def detect_language(text: str) -> str | None:
    """Which of the three supported languages a piece of text is written in.

    Returns ``None`` when the text does not say enough to tell — a serial
    number, a bare measurement, two words that belong to no language in
    particular.  Saying "unrecognised" is a fact about the text; saying English
    when the evidence is a single shared word would be a guess, and the
    operator reads that number to decide whether the file needs translating.

    Deterministic and dependency-free on purpose: the same row must qualify the
    same way on every re-read, or the mapping fingerprint would stop meaning
    what it says.
    """
    words = [word.casefold() for word in _WORDS.findall(text or "")]
    if not words:
        return None

    scores = {code: sum(1 for word in words if word in bag) for code, bag in _GRAMMAR_WORDS.items()}
    for code, marks in _ALPHABET_MARKS.items():
        # One accented letter is worth about one grammar word: both are a small
        # piece of evidence, and neither should win on its own.
        scores[code] += sum(1 for character in (text or "") if character in marks)

    ranking = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    best, best_score = ranking[0]
    second_score = ranking[1][1]
    # Twice the runner-up, or the only language with any evidence at all in a
    # phrase long enough to have some.  A sentence that scores two and two is
    # not English with an Italian word in it: it is a row nobody can qualify,
    # and that is what the operator has to be told.
    if best_score >= 2 and best_score >= 2 * second_score:
        return best
    if best_score == 1 and second_score == 0 and len(words) >= 3:
        return best
    return None
