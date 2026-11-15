"""Entity names: one canonical form for equal names, and the differences that keep names apart.

Two names are merged without asking only when their canonical forms are equal: same words in the
same order after removing case, punctuation, articles and plural endings and writing number words
as digits. Anything looser is a candidate for the resolver. A pair whose names differ by a number,
an axis, a side, a direction or a negation is a false friend and is never merged.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher

_ARTICLES = {"a", "an", "the"}
_NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12",
    "first": "1st", "second": "2nd", "third": "3rd",
}
# Words that do not take a plural "s" although they end like one.
_KEEP_S = {"gas", "bus", "bias", "chassis", "always", "loss", "pass", "glass", "class", "press", "access",
           "process", "excess", "stress", "brass", "gross", "less", "across", "lens", "series", "status",
           "axis", "basis", "analysis", "diagnosis", "apparatus", "thermos", "plus", "minus", "this", "is",
           "its", "has", "was", "does", "as", "us", "yes", "focus", "radius", "chips"}
# Members of one group name alternatives of the same kind: a pair of names that differ by them
# denotes two things (door open / door closed, inner ring / outer ring).
_OPPOSITES = (
    ("open", "opened", "closed", "close", "shut"), ("increase", "decrease", "raise", "reduce", "lower"),
    ("inner", "outer"), ("internal", "external"), ("inside", "outside"), ("upper", "lower", "middle"),
    ("top", "bottom"), ("left", "right"), ("front", "rear", "back"), ("high", "low"), ("in", "out"),
    ("on", "off"), ("positive", "negative"), ("primary", "secondary", "tertiary"), ("input", "output"),
    ("inlet", "outlet"), ("intake", "exhaust"), ("suction", "discharge"), ("supply", "return"),
    ("maximum", "minimum", "max", "min"), ("clockwise", "counterclockwise", "anticlockwise", "cw", "ccw"),
    ("loose", "tight"), ("over", "under"), ("above", "below"), ("hot", "cold"), ("start", "stop"),
    ("before", "after"), ("push", "pull"), ("male", "female"), ("forward", "reverse", "backward"),
    ("up", "down"), ("excessive", "insufficient", "too much", "too little"), ("fast", "slow"),
    ("long", "short"), ("large", "small"), ("wet", "dry"), ("full", "empty"), ("ac", "dc"),
    ("horizontal", "vertical"), ("install", "remove"), ("connect", "disconnect"), ("tighten", "loosen"),
    ("enable", "disable"), ("lock", "unlock"), ("engage", "disengage"), ("add", "drain"),
    ("overheat", "overcool"), ("overvoltage", "undervoltage"), ("overcurrent", "undercurrent"),
    ("north", "south", "east", "west"), ("master", "slave"), ("drive", "driven"), ("with", "without"),
    ("open", "short"), ("thicken", "thin"), ("coarse", "fine"), ("heat", "cool"), ("heating", "cooling"),
    ("charge", "discharge"), ("fill", "drain"), ("early", "late"), ("near", "far"), ("light", "heavy", "dark"),
)
_OPPOSITE_GROUPS: dict[str, set[int]] = {}
for _index, _group in enumerate(_OPPOSITES):
    for _word in _group:
        if " " not in _word:
            _OPPOSITE_GROUPS.setdefault(_word, set()).add(_index)
_NEGATIONS = {"not", "no", "never", "non", "without", "cannot", "won't", "doesn't", "isn't", "fails", "failed"}
_NEGATING_PREFIXES = ("un", "dis", "non", "de", "in", "im", "mis")
_AXIS = re.compile(r"^[a-z]$")
_DIGITS = re.compile(r"\d+(?:[.,]\d+)?")


def _fold(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text or "")).casefold()
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)  # hyphenation across a line break
    text = text.replace("&", " and ")
    return re.sub(r"[^\w\s./-]", " ", text)


def lemma(word: str) -> str:
    """Singular form of a plural noun; other words unchanged. Deliberately small and predictable."""

    if word in _KEEP_S or len(word) <= 3 or not word.isalpha():
        return word
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith(("ches", "shes", "sses", "xes", "zes")):
        return word[:-2]
    if word.endswith("ses"):  # lenses -> lens, fuses -> fuse
        return word[:-2] if word[:-2] in _KEEP_S else word[:-1]
    if word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def tokens(name: str) -> list[str]:
    """Canonical words of a name, in order."""

    words = []
    for raw in re.split(r"[\s/]+", _fold(name)):
        raw = raw.strip(".-")
        if not raw or raw in _ARTICLES:
            continue
        # "3-phase" and "3 phase" read the same; a code such as "E-12" stays one token.
        parts = raw.split("-") if re.fullmatch(r"\d+-[a-z]+|[a-z]+-[a-z]+(?:-[a-z]+)*", raw) else [raw]
        words.extend(lemma(_NUMBER_WORDS.get(part, part)) for part in parts if part and part not in _ARTICLES)
    return words


def canonical(name: str) -> str:
    """Names with the same canonical form are the same name."""

    return " ".join(tokens(name))


def code_key(code: str) -> str:
    """Printed codes compare without case, spaces or punctuation; leading zeros are kept."""

    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKC", str(code or "")).casefold())


def _only(a: list[str], b: list[str]) -> tuple[list[str], list[str]]:
    """Words of each name the other lacks, counting repeats ("open or short ... door open")."""

    left, right = Counter(a), Counter(b)
    return list((left - right).elements()), list((right - left).elements())


def _negates(word: str, other: str) -> bool:
    return any(word == prefix + other and len(other) > 3 for prefix in _NEGATING_PREFIXES)


def distinguishing_difference(left: str, right: str) -> str:
    """Why two similar names denote different things, or '' when nothing certain tells them apart.

    The reasons are differences of kind (a number, a single-letter axis, an opposite, a negation),
    not of wording: they hold whatever a similarity score or a model says, so such a pair is
    never merged.
    """

    a, b = tokens(left), tokens(right)
    if a == b:
        return ""
    only_a, only_b = _only(a, b)
    if set(_DIGITS.findall(" ".join(a))) != set(_DIGITS.findall(" ".join(b))):
        return "different numbers"
    if any(_AXIS.match(w) for w in only_a) and any(_AXIS.match(w) for w in only_b):
        return "different axis or letter"
    groups_a = set().union(*(_OPPOSITE_GROUPS.get(w, set()) for w in only_a))
    groups_b = set().union(*(_OPPOSITE_GROUPS.get(w, set()) for w in only_b))
    if groups_a & groups_b:
        return "opposite or alternative terms"
    if any(_negates(x, y) or _negates(y, x) for x in only_a for y in only_b):
        return "negated term"
    if bool(set(only_a) & _NEGATIONS) != bool(set(only_b) & _NEGATIONS):
        return "negation"
    return ""


def contrast(left: str, right: str) -> str:
    """A difference that often, but not always, separates two things: the resolver must look.

    One word replaced in otherwise equal names is how manuals write parallel entries
    ("tool probe" / "work probe", "open circuit" / "short circuit"); the same words in another
    order can name another thing ("air in water line" / "water in air line").
    """

    a, b = tokens(left), tokens(right)
    if a == b:
        return ""
    only_a, only_b = _only(a, b)
    if len(only_a) == 1 and len(only_b) == 1 and len(a) == len(b) > 1:
        return f"one word differs: {only_a[0]} / {only_b[0]}"
    if not only_a and not only_b:
        return "same words in a different order"
    return ""


def similarity(left: str, right: str) -> float:
    """Lexical closeness of two names in [0, 1], used only to propose pairs to the resolver."""

    a, b = tokens(left), tokens(right)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    text_a, text_b = " ".join(a), " ".join(b)
    in_order = SequenceMatcher(None, text_a, text_b).ratio()
    any_order = SequenceMatcher(None, " ".join(sorted(a)), " ".join(sorted(b))).ratio()
    shared = len(set(a) & set(b))
    overlap = shared / min(len(set(a)), len(set(b)))
    jaccard = shared / len(set(a) | set(b))
    # Containment ("liner" in "cable liner") is a reason to ask, weighted by how much is shared.
    return round(max(in_order, any_order, 0.5 * overlap + 0.5 * jaccard), 4)


_GENERIC = re.compile(r"\b(unspecified|unknown|not stated|not specified|generic|other causes?|placeholder|"
                      r"miscellaneous|various|n/?a)\b", re.I)
_NOISE = re.compile(r"(\.{3,}|\s{2,}|[|_]{2,}|\bpage \d+\b|^\W+|\b(?:fig(?:ure)?|table)\s*\d+\s*$)", re.I)
_OPEN_END = re.compile(r"\b(of|the|a|an|and|or|to|for|with|in|on|at|by|from|is|are)$", re.I)


def name_defects(name: str) -> list[str]:
    """Reasons a node name is not a clean, self-contained label."""

    defects = []
    text = str(name or "").strip()
    if not text:
        return ["empty"]
    if _GENERIC.search(text):
        defects.append("generic")
    if _NOISE.search(text):
        defects.append("layout_noise")
    if _OPEN_END.search(text) or text.endswith(("-", ",", "(", ":")):
        defects.append("truncated")
    if len(text) > 120:
        defects.append("too_long")
    return defects


_ABOUT_THE_MANUAL = re.compile(
    r"\b(the manual|the passage|this (symptom|cause|action|component|outcome|node|entry)|is listed|are listed|"
    r"listed (in|as|for|alongside)|troubleshooting table|on page \d+|in section)\b", re.I)
_POINTER = re.compile(r"\(?\b(see|refer to|page|pages|section)\b[^.;)]*\)?", re.I)


def about_the_manual(text: str) -> bool:
    """A description that talks about the manual (its tables, pages, lists) instead of the thing."""

    return bool(_ABOUT_THE_MANUAL.search(str(text or "")))


def adds_to_name(name: str, text: str, *, words: int = 2) -> bool:
    """Whether a text (an instruction) says more than its name, a printed pointer aside."""

    extra = set(tokens(_POINTER.sub(" ", str(text or "")))) - set(tokens(name))
    return len(extra) > words


def compound_action(name: str) -> bool:
    """An action name that joins two actions with a slash ("Adjust/replace belts")."""

    return bool(re.match(r"^\s*[A-Za-z]+/[A-Za-z]+\b", str(name or "")))


def display_name(name: str) -> str:
    """A name as people read it: first letter upper case, unless the word is written in mixed case (pH, eMC)."""

    text = str(name or "").strip()
    if len(text) > 1 and text[0].islower() and not text[1].isupper():
        return text[0].upper() + text[1:]
    return text
