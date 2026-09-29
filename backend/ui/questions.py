"""Questions of a run for a person, written in plain Italian without a model.

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

TITLES = {
    QuestionKind.RELATION_CHECK: "Il manuale dice questo?",
    QuestionKind.MERGE_CHECK: "Sono la stessa cosa?",
    QuestionKind.MAP_REVIEW: "La mappa delle pagine è giusta?",
    QuestionKind.GRAPH_APPROVAL: "Il grafo può essere usato?",
}
OPTION_LABELS = {
    "accept": "Sì, è giusto", "correct": "Solo in parte", "reject": "No",
    "same": "Sì, la stessa", "different": "No, diverse",
    "skip": "Sì, saltala", "transcribe": "La trascrivo",
    "confirm": "Sì, è giusta", "approve": "Approva",
}
OPTION_ORDER = ("accept", "correct", "reject", "same", "different", "skip", "transcribe", "confirm", "approve")
TYPE_NAMES = {"Symptom": "il sintomo", "ErrorCode": "il codice", "FailureMode": "la causa",
              "CorrectiveAction": "l'azione", "Component": "il componente"}
ACTION_KINDS = {"inspection": "un controllo", "repair": "una riparazione",
                "escalation": "rivolgersi all'assistenza"}
CONDITION_PREFIXES = {"if": "Vale se", "prerequisite": "Prima", "warning": "Attenzione",
                      "expected": "Risultato atteso", "order": "Ordine"}


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


def _name(endpoint: dict[str, Any]) -> str:
    # As in checker.statement: only a cause can be the system's own name for what the manual implies.
    text = f"«{endpoint['name']}»"
    if endpoint.get("type") == "FailureMode" and not endpoint.get("stated", True):
        return f"{text} (causa non scritta nel manuale)"
    return text


def relation_sentence(relation: dict[str, Any]) -> str:
    assertion = relation["assertion"]
    lead = relation["proposals"][0] if relation.get("proposals") else None
    if lead is None:
        source = {"name": assertion["source_key"].split(":", 1)[-1]}
        target = {"name": assertion["target_key"].split(":", 1)[-1]}
    else:
        source, target = lead["source"], lead["target"]
    kind = assertion["relation_type"]
    if kind == "MAY_INDICATE":
        sentence = f"Se succede {_name(source)}, una causa possibile è {_name(target)}."
    elif kind == "INDICATES":
        sentence = f"Il codice {_name(source)} indica {_name(target)}."
    elif kind == "RESOLVED_BY":
        action = ACTION_KINDS.get(str(target.get("kind") or ""))
        sentence = f"Se la causa è {_name(source)}, si interviene con {_name(target)}"
        sentence += f" ({action})." if action else "."
    elif kind == "AFFECTS":
        sentence = f"La causa {_name(source)} riguarda il componente {_name(target)}."
    else:
        sentence = f"{_name(source)} è collegato a {_name(target)} ({kind})."
    conditions = []
    for item in assertion.get("conditions") or []:
        text = f"{CONDITION_PREFIXES.get(item.get('kind', 'if'), 'Vale se')}: {item['text'].rstrip('.')}."
        if text not in conditions:
            conditions.append(text)
    return " ".join([sentence, *conditions])


def claims(question: Question, relations: dict[str, dict[str, Any]],
           merge_names: dict[tuple[str, str], tuple[str, str, str]]) -> list[str]:
    if question.kind is QuestionKind.RELATION_CHECK:
        ids = list(question.target.get("assertion_ids") or [])
        numbers = list(question.target.get("statement_of") or range(1, len(ids) + 1))
        by_number: dict[int, str] = {}
        for number, assertion_id in zip(numbers, ids):
            if number not in by_number and assertion_id in relations:
                by_number[number] = relation_sentence(relations[assertion_id])
        # A statement whose assertion is not saved keeps the system's own wording.
        return [by_number.get(index + 1, text) for index, text in enumerate(question.proposal)]
    if question.kind is QuestionKind.MERGE_CHECK:
        left, right = question.target.get("left", ""), question.target.get("right", "")
        names = merge_names.get((left, right))
        if names:
            kind = TYPE_NAMES.get(names[2], names[2])
            return [f"«{names[0]}» e «{names[1]}»: il sistema li tiene come due nodi separati ({kind})."]
    if question.kind is QuestionKind.UNREADABLE_PAGE:
        page = question.target.get("page")
        return [f"La pagina {page} è probabilmente una figura o una scansione: il sistema non è riuscito a leggerla."]
    return list(question.proposal)


def title(question: Question) -> str:
    if question.kind is QuestionKind.UNREADABLE_PAGE:
        return f"La pagina {question.target.get('page')} non si legge: la saltiamo?"
    return TITLES.get(question.kind, question.title)


class OptionView(BaseModel):
    option_id: str
    label_it: str
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


def question_views(run_dir: Path, questions: list[Question]) -> list[QuestionView]:
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
            question_id=question.question_id, kind=question.kind.value, title_it=title(question),
            source=[item.model_dump(mode="json") for item in question.source],
            claims_it=claims(question, relations, merge_names), proposal=list(question.proposal),
            options=[OptionView(option_id=option.option_id,
                                label_it=OPTION_LABELS.get(option.option_id, option.label),
                                needs_statements=question.kind is QuestionKind.RELATION_CHECK
                                and option.option_id == "correct",
                                needs_text=option.option_id == "transcribe")
                     for option in options],
            default_option_id=question.default_option_id, priority=question.priority,
        ))
    return views
