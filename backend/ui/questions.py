"""Questions of a run for a person, in plain Italian or English, written without a model.

The selection mirrors ``Pipeline._result``: questions still pending in the gate records,
most important first, up to the budget of the manual. The approval is the person's
button, not one of these questions. The sentences are fixed templates filled with the
data of each assertion; the technical statement stays available as ``proposal``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from backend.kg_v3.contracts import Question, QuestionKind

HUMAN_QUESTION_BUDGET = 10
GATE_ORDER = ("map", "doubts", "recovery", "approval")

LANGUAGES = ("it", "en")

# The fixed sentences of the questions, in each language of the interface.
TEXTS: dict[str, dict[str, Any]] = {
    "it": {
        "titles": {
            QuestionKind.RELATION_CHECK: "Il manuale dice questo?",
            QuestionKind.MERGE_CHECK: "Sono la stessa cosa?",
            QuestionKind.MAP_REVIEW: "La mappa delle pagine è giusta?",
            QuestionKind.GRAPH_APPROVAL: "Il grafo può essere usato?",
        },
        "unreadable_title": "La pagina {page} non si legge: la saltiamo?",
        "options": {
            "accept": "Sì, è giusto", "correct": "Solo in parte", "reject": "No",
            "same": "Sì, la stessa", "different": "No, diverse",
            "skip": "Sì, saltala", "transcribe": "La trascrivo",
            "confirm": "Sì, è giusta", "approve": "Approva",
        },
        "types": {"Symptom": "il sintomo", "ErrorCode": "il codice", "FailureMode": "la causa",
                  "CorrectiveAction": "l'azione", "Component": "il componente"},
        "actions": {"inspection": "un controllo", "repair": "una riparazione",
                    "escalation": "rivolgersi all'assistenza"},
        "conditions": {"if": "Vale se", "prerequisite": "Prima", "warning": "Attenzione",
                       "expected": "Risultato atteso", "order": "Ordine"},
        "unstated": "(causa non scritta nel manuale)",
        "MAY_INDICATE": "Se succede {source}, una causa possibile è {target}.",
        "INDICATES": "Il codice {source} indica {target}.",
        "RESOLVED_BY": "Se la causa è {source}, si interviene con {target}",
        "AFFECTS": "La causa {source} riguarda il componente {target}.",
        "other": "{source} è collegato a {target} ({kind}).",
        "merge": "{left} e {right}: il sistema li tiene come due nodi separati ({kind}).",
        "unreadable": "La pagina {page} è probabilmente una figura o una scansione: il sistema non è riuscito a leggerla.",
    },
    "en": {
        "titles": {
            QuestionKind.RELATION_CHECK: "Does the manual say this?",
            QuestionKind.MERGE_CHECK: "Are these the same thing?",
            QuestionKind.MAP_REVIEW: "Is the map of the pages right?",
            QuestionKind.GRAPH_APPROVAL: "Can the graph be used?",
        },
        "unreadable_title": "Page {page} cannot be read: skip it?",
        "options": {
            "accept": "Yes, it is right", "correct": "Only in part", "reject": "No",
            "same": "Yes, the same", "different": "No, different",
            "skip": "Yes, skip it", "transcribe": "I will transcribe it",
            "confirm": "Yes, it is right", "approve": "Approve",
        },
        "types": {"Symptom": "symptom", "ErrorCode": "code", "FailureMode": "cause",
                  "CorrectiveAction": "action", "Component": "component"},
        "actions": {"inspection": "a check", "repair": "a repair", "escalation": "call for service"},
        "conditions": {"if": "Applies if", "prerequisite": "First", "warning": "Warning",
                       "expected": "Expected result", "order": "Order"},
        "unstated": "(cause not written in the manual)",
        "MAY_INDICATE": "If {source} happens, a possible cause is {target}.",
        "INDICATES": "The code {source} indicates {target}.",
        "RESOLVED_BY": "If the cause is {source}, the fix is {target}",
        "AFFECTS": "The cause {source} concerns the component {target}.",
        "other": "{source} is linked to {target} ({kind}).",
        "merge": "{left} and {right}: the system keeps them as two separate nodes ({kind}).",
        "unreadable": "Page {page} is probably a figure or a scan: the system could not read it.",
    },
}
OPTION_ORDER = ("accept", "correct", "reject", "same", "different", "skip", "transcribe", "confirm", "approve")


def _texts(lang: str) -> dict[str, Any]:
    return TEXTS[lang if lang in TEXTS else "it"]


def _read(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def gate_records(run_dir: Path) -> dict[str, dict[str, Any]]:
    records = {}
    for gate in GATE_ORDER:
        record = _read(run_dir / "state" / f"gate_{gate}.json")
        if record is not None:
            records[gate] = record
    return records


def pending_questions(run_dir: Path, budget: int = HUMAN_QUESTION_BUDGET) -> tuple[list[Question], list[Question]]:
    """(offered, deferred) exactly as a run that asked no person publishes them."""

    pending = [Question.model_validate(question)
               for record in gate_records(run_dir).values()
               for question in record.get("questions", []) if question["question_id"] in record.get("pending", [])]
    ranked = sorted(pending, key=lambda question: -question.priority)
    return ranked[:budget], ranked[budget:]


def open_for_people(run_dir: Path, budget: int = HUMAN_QUESTION_BUDGET) -> tuple[list[Question], list[Question]]:
    """(open for the person, unverified beyond the budget), approval excluded."""

    offered, deferred = pending_questions(run_dir, budget)
    person = [question for question in offered if question.kind is not QuestionKind.GRAPH_APPROVAL]
    return person, [question for question in deferred if question.kind is not QuestionKind.GRAPH_APPROVAL]


# Plain sentences -------------------------------------------------------------


def relations_by_assertion(run_dir: Path) -> dict[str, dict[str, Any]]:
    """Latest saved version of every checked relation, by assertion ID."""

    found: dict[str, dict[str, Any]] = {}
    state = run_dir / "state"
    for prefix in ("checked_", "rechecked_", "navigation_", "recovery_"):
        for path in sorted(state.glob(f"{prefix}*.json")):
            for relation in _read(path) or []:
                found[relation["assertion"]["assertion_id"]] = relation
    return found


def _name(endpoint: dict[str, Any], lang: str = "it") -> str:
    # As in checker.statement: only a cause can be the system's own name for what the manual implies.
    text = f"«{endpoint['name']}»" if lang == "it" else f"“{endpoint['name']}”"
    if endpoint.get("type") == "FailureMode" and not endpoint.get("stated", True):
        return f"{text} {_texts(lang)['unstated']}"
    return text


def relation_sentence(relation: dict[str, Any], lang: str = "it") -> str:
    words = _texts(lang)
    assertion = relation["assertion"]
    lead = relation["proposals"][0] if relation.get("proposals") else None
    if lead is None:
        source = {"name": assertion["source_key"].split(":", 1)[-1]}
        target = {"name": assertion["target_key"].split(":", 1)[-1]}
    else:
        source, target = lead["source"], lead["target"]
    kind = assertion["relation_type"]
    names = {"source": _name(source, lang), "target": _name(target, lang), "kind": kind}
    if kind == "RESOLVED_BY":
        action = words["actions"].get(str(target.get("kind") or ""))
        sentence = words["RESOLVED_BY"].format(**names) + (f" ({action})." if action else ".")
    else:
        sentence = words.get(kind, words["other"]).format(**names)
    conditions = []
    for item in assertion.get("conditions") or []:
        prefix = words["conditions"].get(item.get("kind", "if"), words["conditions"]["if"])
        text = f"{prefix}: {item['text'].rstrip('.')}."
        if text not in conditions:
            conditions.append(text)
    return " ".join([sentence, *conditions])


def claims(question: Question, relations: dict[str, dict[str, Any]],
           merge_names: dict[tuple[str, str], tuple[str, str, str]], lang: str = "it") -> list[str]:
    words = _texts(lang)
    if question.kind is QuestionKind.RELATION_CHECK:
        ids = list(question.target.get("assertion_ids") or [])
        numbers = list(question.target.get("statement_of") or range(1, len(ids) + 1))
        by_number: dict[int, str] = {}
        for number, assertion_id in zip(numbers, ids):
            if number not in by_number and assertion_id in relations:
                by_number[number] = relation_sentence(relations[assertion_id], lang)
        # A statement whose assertion is not saved keeps the system's own wording.
        return [by_number.get(index + 1, text) for index, text in enumerate(question.proposal)]
    if question.kind is QuestionKind.MERGE_CHECK:
        left, right = question.target.get("left", ""), question.target.get("right", "")
        names = merge_names.get((left, right))
        if names:
            kind = words["types"].get(names[2], names[2])
            return [words["merge"].format(left=_name({"name": names[0]}, lang), right=_name({"name": names[1]}, lang),
                                          kind=kind)]
    if question.kind is QuestionKind.UNREADABLE_PAGE:
        page = question.target.get("page")
        return [words["unreadable"].format(page=page)]
    return list(question.proposal)


def title(question: Question, lang: str = "it") -> str:
    words = _texts(lang)
    if question.kind is QuestionKind.UNREADABLE_PAGE:
        return words["unreadable_title"].format(page=question.target.get("page"))
    return words["titles"].get(question.kind, question.title)


class OptionView(BaseModel):
    option_id: str
    label_it: str  # in the language asked for: the name stays for the clients that read it
    # "Solo in parte" asks which numbered statements to keep; "La trascrivo" asks for text.
    needs_statements: bool = False
    needs_text: bool = False


class QuestionView(BaseModel):
    question_id: str
    kind: str
    title_it: str
    source: list[dict[str, Any]]
    claims_it: list[str]
    proposal: list[str]
    options: list[OptionView]
    default_option_id: str
    priority: int


def question_views(run_dir: Path, questions: list[Question], lang: str = "it") -> list[QuestionView]:
    relations = relations_by_assertion(run_dir) if questions else {}
    merge_names: dict[tuple[str, str], tuple[str, str, str]] = {}
    for path in sorted((run_dir / "state").glob("merge_plan_*.json")):
        for pair in (_read(path) or {}).get("unsure", []):
            merge_names[(pair["left"], pair["right"])] = (pair["left_name"], pair["right_name"], pair["type"])
    views = []
    for question in questions:
        options = sorted(question.options, key=lambda option: OPTION_ORDER.index(option.option_id)
                         if option.option_id in OPTION_ORDER else len(OPTION_ORDER))
        views.append(QuestionView(
            question_id=question.question_id, kind=question.kind.value, title_it=title(question, lang),
            source=[item.model_dump(mode="json") for item in question.source],
            claims_it=claims(question, relations, merge_names, lang), proposal=list(question.proposal),
            options=[OptionView(option_id=option.option_id,
                                label_it=_texts(lang)["options"].get(option.option_id, option.label),
                                needs_statements=question.kind is QuestionKind.RELATION_CHECK
                                and option.option_id == "correct",
                                needs_text=option.option_id == "transcribe")
                     for option in options],
            default_option_id=question.default_option_id, priority=question.priority,
        ))
    return views
