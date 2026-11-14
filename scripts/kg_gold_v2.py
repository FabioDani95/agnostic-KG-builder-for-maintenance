"""Gold v2 of the campaign manuals: an AI-made, exhaustive list of each manual's diagnostic knowledge.

    validate <manual>        schema, IDs, segments of the current reader, quotes, pages, references, questions
    stats [manuals]          branches by category and scope, actions by kind, components, questions
    export-claims <manual>   gold v2 in the claim format of gold v1 -> gold_v2/claims_v1_format.json
    render-pages <manual>    write gold_v2/PAGINE.md from the page map in gold.json
    iaa-pages <manual>       the 25% of diagnostic pages a second annotator redoes (fixed seed)
    review-sheet <manual>    write gold_v2/REVISIONE_FABIO.md: 30 items by category and 10 other pages

The gold lives in campaign/<manual>/gold_v2/gold.json. It is written by an AI annotator and says so in
its metadata; gold v1 (campaign/<manual>/gold/) stays frozen and is never read here. No model is called.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CAMPAIGN = ROOT / "campaign"
SEED = 20261113
SEGMENT_ID = r"^p[1-9]\d*\.(?:b\d+(?:\.\d+)?|t\d+\.r\d+|o\d+)$"
SCOPES = {"fault": "core", "error_code": "core", "flowchart": "core", "diagnostic_test": "extended",
          "condition_maintenance": "extended", "procedure": "extended", "safety_precaution": "context",
          "routine": "context"}
BRANCH_CATEGORIES = tuple(name for name in SCOPES if name != "procedure")
QUOTE_OVERLAP = 0.7
MIN_QUESTIONS, MAX_QUESTIONS = 15, 30
V1_KINDS = {"repair": "repair", "inspection": "inspection", "escalation": "escalation", "prohibition": "prohibition"}


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Annotator(Strict):
    kind: Literal["ai"]
    model: str = Field(min_length=1)
    human_review: bool


class Reader(Strict):
    segments_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    note: str = ""


class Page(Strict):
    page: int = Field(ge=1)
    content: list[str] = Field(min_length=1)
    diagnostic: bool
    note: str = Field(min_length=1)


class Problem(Strict):
    type: Literal["symptom", "code", "test", "inspection", "task", "hazard"]
    text: str = Field(min_length=1)
    code: str = ""
    segments: list[str] = []


class Cause(Strict):
    text: str = Field(min_length=1)
    stated: bool
    segments: list[str] = []


class Action(Strict):
    order: int = Field(ge=1)
    kind: Literal["repair", "inspection", "escalation", "prohibition"]
    text: str = Field(min_length=1)
    expected: str = ""
    condition: str = ""
    component: str = ""
    segments: list[str] = []


class Reference(Strict):
    text: str = Field(min_length=1)
    target_pages: list[int] = []
    target_items: list[str] = []
    external: str = ""


class Evidence(Strict):
    pages: list[int] = Field(min_length=1)
    section: str
    segments: list[str]
    quote: str = ""


class Branch(Strict):
    id: str = Field(pattern=r"^B\d{3,}$")
    category: Literal[BRANCH_CATEGORIES]
    scope: Literal["core", "extended", "context"]
    problem: Problem
    cause: Cause | None
    actions: list[Action]
    components: list[str] = []
    conditions: list[str] = []
    references: list[Reference] = []
    evidence: Evidence
    certainty: Literal["certain", "ambiguous"]
    note: str = ""
    added_after_v1_comparison: bool = False


class Procedure(Strict):
    id: str = Field(pattern=r"^P\d{3,}$")
    category: Literal["procedure", "routine"]
    scope: Literal["extended", "context"]
    title: str = Field(min_length=1)
    steps: list[str] = Field(min_length=1)
    components: list[str] = []
    conditions: list[str] = []
    references: list[Reference] = []
    evidence: Evidence
    certainty: Literal["certain", "ambiguous"]
    note: str = ""
    added_after_v1_comparison: bool = False


class Component(Strict):
    name: str = Field(min_length=1)
    aliases: list[str] = []
    part_of: str = ""
    part_number: str = ""
    pages: list[int] = []


class Named(Strict):
    name: str = Field(min_length=1)
    aliases: list[str] = []


class Code(Strict):
    code: str = Field(min_length=1)
    meaning: str = ""
    aliases: list[str] = []


class FalseFriends(Strict):
    a: str = Field(min_length=1)
    b: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class Synonyms(Strict):
    names: list[str] = Field(min_length=2)
    note: str = ""


class Entities(Strict):
    components: list[Component]
    symptoms: list[Named]
    codes: list[Code]
    false_friends: list[FalseFriends]
    synonyms: list[Synonyms]


class Question(Strict):
    id: str = Field(pattern=r"^Q\d{2,}$")
    type: Literal["symptom_causes_actions", "code_meaning_actions", "component_faults", "checks_before_replacing",
                  "test_expected_value", "procedure_steps", "maintenance_condition", "safety"]
    text: str = Field(min_length=1)
    answer_items: list[str] = Field(min_length=1)


class Verification(Strict):
    """Which scopes an independent verifier checked against the PDF; the others are annotated once."""

    independent_scopes: list[Literal["core", "extended", "context"]]
    note: str = ""


class Gold(Strict):
    schema_: Literal["kg-gold-2"] = Field(alias="schema")
    manual_id: str
    annotator: Annotator
    created: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    reader: Reader
    verification: Verification | None = None
    pages: list[Page]
    branches: list[Branch]
    procedures: list[Procedure]
    entities: Entities
    questions: list[Question]


# Reading ------------------------------------------------------------------

def folder(manual: str) -> Path:
    return CAMPAIGN / manual / "gold_v2"


def load_gold(manual: str) -> dict:
    return json.loads((folder(manual) / "gold.json").read_text(encoding="utf-8"))


def segments_digest(segments: dict[str, str]) -> str:
    """One hash for all segment IDs and texts, so a reader change is noticed."""

    return hashlib.sha256("\n".join(f"{key}\t{value}" for key, value in segments.items()).encode()).hexdigest()


def read_segments(manual: str) -> tuple[dict[str, str], int]:
    """Segment texts by ID and the page count, read as scripts/kg_build.py reads the manual."""

    from scripts.kg_build import read
    from scripts.kg_v3 import manual_source

    doc, _sections, _sha = read(*manual_source(manual))
    return {segment.segment_id: segment.text for segment in doc.segments()}, doc.page_count


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def quote_overlap(quote: str, text: str) -> float:
    """Share of the quote's words found in the text: meaning over characters."""

    wanted = words(quote)
    found = set(words(text))
    return sum(word in found for word in wanted) / len(wanted) if wanted else 0.0


def items_of(gold: dict) -> list[dict]:
    return [*gold.get("branches", []), *gold.get("procedures", [])]


def pages_in_sheet(text: str) -> set[int]:
    return {int(number) for number in re.findall(r"^\|\s*(\d+)\s*\|", text, re.M)}


# Validation ---------------------------------------------------------------

def check(gold: dict, segments: dict[str, str], page_count: int, pages_sheet: str | None = None) -> list[str]:
    """Every problem of a gold file; an empty list means it is valid."""

    try:
        gold = Gold.model_validate(gold).model_dump(by_alias=True)  # optional fields get their defaults
    except ValidationError as error:
        return [f"schema: {'.'.join(map(str, item['loc']))}: {item['msg']}" for item in error.errors()]

    errors: list[str] = []
    items = items_of(gold)
    ids = [item["id"] for item in items] + [question["id"] for question in gold["questions"]]
    errors += [f"{key}: ID used {count} times" for key, count in Counter(ids).items() if count > 1]
    known = {item["id"] for item in items}

    if gold["reader"]["segments_sha256"] != segments_digest(segments):
        errors.append("reader: segments_sha256 differs from the current reader")

    listed = [page["page"] for page in gold["pages"]]
    errors += [f"pages: page {page} listed {count} times" for page, count in Counter(listed).items() if count > 1]
    missing = sorted(set(range(1, page_count + 1)) - set(listed))
    extra = sorted(set(listed) - set(range(1, page_count + 1)))
    if missing:
        errors.append(f"pages: missing from the page map: {missing}")
    if extra:
        errors.append(f"pages: not in the PDF: {extra}")
    if pages_sheet is not None:
        unseen = sorted(set(range(1, page_count + 1)) - pages_in_sheet(pages_sheet))
        if unseen:
            errors.append(f"PAGINE.md: missing pages: {unseen}")
    diagnostic = {page["page"] for page in gold["pages"] if page["diagnostic"]}

    names = set()
    for component in gold["entities"]["components"]:
        for name in [component["name"], *component["aliases"]]:
            names.add(name.casefold())
    canonical = [component["name"].casefold() for component in gold["entities"]["components"]]
    errors += [f"entities: component '{name}' listed {count} times"
               for name, count in Counter(canonical).items() if count > 1]
    for component in gold["entities"]["components"]:
        if component["part_of"] and component["part_of"].casefold() not in canonical:
            errors.append(f"entities: '{component['name']}' is part of unknown '{component['part_of']}'")
        errors += [f"entities: '{component['name']}' on page {page} outside the PDF"
                   for page in component["pages"] if not 1 <= page <= page_count]

    cited_pages: set[int] = set()
    for item in items:
        key, evidence = item["id"], item["evidence"]
        category, scope = item["category"], item["scope"]
        if SCOPES[category] != scope:
            errors.append(f"{key}: category {category} has scope {SCOPES[category]}, not {scope}")
        if item["certainty"] == "ambiguous" and not item["note"].strip():
            errors.append(f"{key}: ambiguous without the reason in note")
        cited_pages.update(evidence["pages"])
        errors += [f"{key}: evidence page {page} outside the PDF" for page in evidence["pages"]
                   if not 1 <= page <= page_count]
        if scope != "context":
            errors += [f"{key}: page {page} holds a {scope} item but is not marked diagnostic"
                       for page in evidence["pages"] if 1 <= page <= page_count and page not in diagnostic]
        actions = item.get("actions", [])
        parts = [item.get("problem") or {}, item.get("cause") or {}, *actions]
        cited = list(evidence["segments"]) + [value for part in parts for value in part.get("segments", [])]
        for value in dict.fromkeys(cited):
            if not re.match(SEGMENT_ID, value) or value not in segments:
                errors.append(f"{key}: segment {value} is not in the current reader")
            elif int(value[1:].split(".")[0]) not in evidence["pages"]:
                errors.append(f"{key}: segment {value} is on a page missing from evidence.pages")
        present = [value for value in evidence["segments"] if value in segments]
        if scope == "core" and not evidence["segments"]:
            errors.append(f"{key}: core item without segments")
        if evidence["segments"] and not evidence["quote"].strip():
            errors.append(f"{key}: evidence without a quote")
        if present and evidence["quote"].strip():
            overlap = quote_overlap(evidence["quote"], " ".join(segments[value] for value in present))
            if overlap < QUOTE_OVERLAP:
                errors.append(f"{key}: quote not found in its segments (overlap {overlap:.2f})")
        if "actions" in item:
            if not actions and category != "error_code":
                errors.append(f"{key}: no action")
            if [action["order"] for action in actions] != list(range(1, len(actions) + 1)):
                errors.append(f"{key}: action order is not 1..{len(actions)}")
            if item["cause"] and not item["cause"]["stated"] and not item["note"].strip():
                errors.append(f"{key}: cause not stated by the manual needs the reason in note")
            if category == "error_code" and not item["problem"]["code"].strip():
                errors.append(f"{key}: error code without the code")
        used = list(item.get("components", [])) + [action["component"] for action in actions if action["component"]]
        errors += [f"{key}: component '{name}' is not in the inventory"
                   for name in dict.fromkeys(used) if name.casefold() not in names]
        for reference in item.get("references", []):
            if not (reference["target_pages"] or reference["target_items"] or reference["external"].strip()):
                errors.append(f"{key}: reference '{reference['text']}' points nowhere")
            errors += [f"{key}: reference to page {page} outside the PDF" for page in reference["target_pages"]
                       if not 1 <= page <= page_count]
            errors += [f"{key}: reference to unknown item {target}" for target in reference["target_items"]
                       if target not in known]
    errors += [f"pages: page {page} is marked diagnostic but no item cites it" for page in sorted(diagnostic - cited_pages)]

    count = len(gold["questions"])
    if not MIN_QUESTIONS <= count <= MAX_QUESTIONS:
        errors.append(f"questions: {count}, expected {MIN_QUESTIONS} to {MAX_QUESTIONS}")
    category_of = {item["id"]: item["category"] for item in items}
    answered: set[str] = set()
    for question in gold["questions"]:
        errors += [f"{question['id']}: answer item {target} does not exist" for target in question["answer_items"]
                   if target not in known]
        answered.update(category_of[target] for target in question["answer_items"] if target in known)
    wanted = {category for category in category_of.values() if SCOPES[category] != "context"}
    errors += [f"questions: no question about category {category}" for category in sorted(wanted - answered)]
    return errors


# Statistics and exports ----------------------------------------------------

def statistics(gold: dict) -> dict:
    items = items_of(gold)
    return {
        "pages": len(gold["pages"]),
        "diagnostic_pages": sum(page["diagnostic"] for page in gold["pages"]),
        "branches": len(gold["branches"]),
        "procedures": len(gold["procedures"]),
        "by_category": dict(Counter(item["category"] for item in items)),
        "by_scope": dict(Counter(item["scope"] for item in items)),
        "actions_by_kind": dict(Counter(action["kind"] for branch in gold["branches"] for action in branch["actions"])),
        "components": len(gold["entities"]["components"]),
        "codes": len(gold["entities"]["codes"]),
        "questions": len(gold["questions"]),
        "ambiguous": sum(item["certainty"] == "ambiguous" for item in items),
        "added_after_v1_comparison": sum(item.get("added_after_v1_comparison", False) for item in items),
        "independently_verified_scopes": (gold.get("verification") or {}).get("independent_scopes", []),
    }


def export_claims(gold: dict) -> dict:
    """One claim per action, as gold v1 has them; procedures stay out."""

    claims = []
    for branch in gold["branches"]:
        evidence = branch["evidence"]["segments"]
        problem, cause = branch["problem"], branch["cause"]
        stated = bool(cause and cause["stated"])
        base = {
            "branch_id": branch["id"], "category": branch["category"], "scope": branch["scope"],
            "indicator": problem["text"], "code": problem["code"],
            "failure": cause["text"] if stated else "", "failure_stated": stated,
            "indicator_segments": problem.get("segments") or evidence,
            "failure_segments": (cause.get("segments") or evidence) if stated else [],
            "component": ", ".join(branch.get("components", [])),
            "component_segments": evidence if branch.get("components") else [],
        }
        for action in branch["actions"] or [None]:
            conditions = [*branch.get("conditions", []), *([action["condition"]] if action and action["condition"] else [])]
            claims.append({
                **base, "claim_id": f"{branch['id']}.{action['order'] if action else 1}",
                "action": action["text"] if action else "",
                "action_kind": V1_KINDS[action["kind"]] if action else "",
                "action_segments": ((action.get("segments") or evidence) if action else []),
                "conditions": "; ".join(conditions),
            })
    pages = sorted({page for branch in gold["branches"] for page in branch["evidence"]["pages"]})
    return {"annotator": f"AI ({gold['annotator']['model']}), gold v2", "date": gold["created"], "minutes": "",
            "pages": pages, "branches": len(gold["branches"]), "claims": claims, "manual_id": gold["manual_id"],
            "status": "annotated", "source": "gold_v2/gold.json", "human_review": gold["annotator"]["human_review"]}


def pages_sheet(gold: dict) -> str:
    lines = [f"# Pagine del manuale: {gold['manual_id']} (gold v2, fatto da un'AI)", "",
             "Ogni pagina del file PDF, che cosa contiene e se è diagnostica. Generato da `gold.json`",
             "con `scripts/kg_gold_v2.py render-pages`: non modificarlo a mano.", "",
             "| Pagina | Contenuto | Diagnostica | Perché |", "| ---: | --- | :---: | --- |"]
    for page in sorted(gold["pages"], key=lambda item: item["page"]):
        note = page["note"].replace("|", "/")
        lines.append(f"| {page['page']} | {', '.join(page['content'])} | {'sì' if page['diagnostic'] else 'no'} | {note} |")
    return "\n".join(lines) + "\n"


def iaa_pages(gold: dict, seed: int = SEED, share: float = 0.25) -> list[int]:
    diagnostic = sorted(page["page"] for page in gold["pages"] if page["diagnostic"])
    return sorted(random.Random(seed).sample(diagnostic, math.ceil(len(diagnostic) * share))) if diagnostic else []


def review_sample(gold: dict, seed: int = SEED, size: int = 30, other_pages: int = 10) -> tuple[list[dict], list[dict]]:
    """Items drawn by category in proportion (at least one each), and pages marked not diagnostic."""

    rng = random.Random(seed)
    groups: dict[str, list[dict]] = {}
    for item in items_of(gold):
        groups.setdefault(item["category"], []).append(item)
    total = sum(map(len, groups.values()))
    size = min(size, total)
    quota = {name: max(1, round(size * len(group) / total)) for name, group in groups.items()} if total else {}
    while sum(quota.values()) > size:
        largest = max((name for name in quota if quota[name] > 1), key=lambda name: quota[name], default=None)
        if largest is None:
            break
        quota[largest] -= 1
    while sum(quota.values()) < size:
        room = [name for name in quota if quota[name] < len(groups[name])]
        quota[max(room, key=lambda name: len(groups[name]) - quota[name])] += 1
    chosen = [item for name in sorted(groups) for item in rng.sample(groups[name], min(quota[name], len(groups[name])))]
    others = [page for page in gold["pages"] if not page["diagnostic"]]
    return chosen, sorted(rng.sample(others, min(other_pages, len(others))), key=lambda page: page["page"])


def review_sheet(gold: dict, seed: int = SEED) -> str:
    chosen, others = review_sample(gold, seed)
    lines = [f"# Revisione di Fabio: {gold['manual_id']} (gold v2, fatto da un'AI)", "",
             f"Campione casuale (seme {seed}), stratificato per categoria. Per ogni elemento apri la pagina del PDF",
             "e scrivi una X: serve a stimare l'errore del gold. Finché non è compilato, `human_review` resta `false`.",
             "", "## Elementi", ""]
    for number, item in enumerate(chosen, start=1):
        evidence = item["evidence"]
        lines += [f"### {number}. {item['id']} · {item['category']} · pagina {', '.join(map(str, evidence['pages']))}", ""]
        if "problem" in item:
            cause = item["cause"]["text"] if item["cause"] else "non indicata nel manuale"
            lines += [f"- problema: {item['problem']['text']}" + (f" (codice {item['problem']['code']})"
                                                                  if item["problem"]["code"] else ""),
                      f"- causa: {cause}"]
            lines += [f"- azione {action['order']} ({action['kind']}): {action['text']}"
                      + (f" — atteso: {action['expected']}" if action["expected"] else "")
                      + (f" — condizione: {action['condition']}" if action["condition"] else "")
                      for action in item["actions"]]
        else:
            lines += [f"- procedura: {item['title']}", f"- passi: {len(item['steps'])}"]
            lines += [f"  {index}. {step}" for index, step in enumerate(item["steps"], start=1)]
        lines += [f"- citazione: «{evidence['quote']}»", f"- sezione: {evidence['section']}",
                  "- giudizio: [ ] corretto   [ ] da correggere   [ ] sbagliato", "- commento:", ""]
    lines += ["## Pagine marcate non diagnostiche", "",
              "Guarda la pagina: contiene guasti, codici, test o rimedi che mancano nel gold?", ""]
    for page in others:
        lines += [f"- pagina {page['page']} ({', '.join(page['content'])}: {page['note']}) — "
                  "[ ] niente da aggiungere   [ ] manca qualcosa:"]
    return "\n".join(lines) + "\n"


# Commands -----------------------------------------------------------------

def manuals(names: list[str]) -> list[str]:
    return names or sorted(path.parent.parent.name for path in CAMPAIGN.glob("*/gold_v2/gold.json"))


def cmd_validate(args) -> int:
    failed = 0
    for manual in manuals(args.manuals):
        gold = load_gold(manual)
        segments, page_count = read_segments(manual)
        sheet = folder(manual) / "PAGINE.md"
        errors = check(gold, segments, page_count, sheet.read_text(encoding="utf-8") if sheet.exists() else "")
        if gold.get("manual_id") != manual:
            errors.append(f"manual_id is {gold.get('manual_id')!r}, the folder is {manual!r}")
        print(f"{manual}: {len(errors)} errors")
        for error in errors:
            print("  -", error)
        failed += bool(errors)
    return 1 if failed else 0


def cmd_stats(args) -> int:
    for manual in manuals(args.manuals):
        print(json.dumps({"manual": manual, **statistics(load_gold(manual))}, ensure_ascii=False))
    return 0


def cmd_export_claims(args) -> int:
    for manual in manuals(args.manuals):
        target = folder(manual) / "claims_v1_format.json"
        data = export_claims(load_gold(manual))
        target.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{manual}: {data['branches']} branches, {len(data['claims'])} claims -> {target.relative_to(ROOT)}")
    return 0


def cmd_render_pages(args) -> int:
    for manual in manuals(args.manuals):
        (folder(manual) / "PAGINE.md").write_text(pages_sheet(load_gold(manual)), encoding="utf-8")
        print(f"{manual}: PAGINE.md written")
    return 0


def cmd_iaa_pages(args) -> int:
    for manual in manuals(args.manuals):
        print(manual, iaa_pages(load_gold(manual), args.seed))
    return 0


def cmd_review_sheet(args) -> int:
    for manual in manuals(args.manuals):
        target = folder(manual) / "REVISIONE_FABIO.md"
        if target.exists() and not args.force:
            print(f"{manual}: kept existing {target.relative_to(ROOT)} (use --force to rewrite it)")
            continue
        target.write_text(review_sheet(load_gold(manual), args.seed), encoding="utf-8")
        print(f"{manual}: REVISIONE_FABIO.md written")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    for name, function in (("validate", cmd_validate), ("stats", cmd_stats), ("export-claims", cmd_export_claims),
                           ("render-pages", cmd_render_pages), ("iaa-pages", cmd_iaa_pages),
                           ("review-sheet", cmd_review_sheet)):
        command = commands.add_parser(name)
        command.add_argument("manuals", nargs="*", help="manual IDs; default: every manual with a gold v2")
        if name in {"iaa-pages", "review-sheet"}:
            command.add_argument("--seed", type=int, default=SEED)
        if name == "review-sheet":
            command.add_argument("--force", action="store_true")
        command.set_defaults(function=function)
    args = parser.parse_args()
    return args.function(args)


if __name__ == "__main__":
    raise SystemExit(main())
