"""Persistent question store of a run for the interface: ``people.json`` in the run folder.

It implements the ``QuestionStore`` protocol of ``reviewers.py``. It keeps the budget
of questions for a person over every resume of a run (the pipeline counts it per
process), and it leaves out the approval, which is the person's button.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

from backend.kg_v3.contracts import Answer, Question, QuestionKind, validate_answer

STORE_NAME = "people.json"


class FileQuestionStore:
    def __init__(self, path: Path, budget: int = 10) -> None:
        self.path = path
        self.budget = budget
        data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        self.questions = [Question.model_validate(item) for item in data.get("questions", [])]
        self.answers = {key: Answer.model_validate(value) for key, value in (data.get("answers") or {}).items()}
        self.applied: list[str] = list(data.get("applied", []))

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({
            "budget": self.budget,
            "questions": [question.model_dump(mode="json") for question in self.questions],
            "answers": {key: answer.model_dump(mode="json") for key, answer in self.answers.items()},
            "applied": self.applied,
        }, ensure_ascii=False, indent=1), encoding="utf-8")

    # QuestionStore -------------------------------------------------------------

    def publish(self, questions: Sequence[Question]) -> None:
        known = {question.question_id for question in self.questions}
        for question in questions:
            if question.kind is QuestionKind.GRAPH_APPROVAL or question.question_id in known:
                continue
            if len(self.questions) >= self.budget:
                break
            self.questions.append(question)
            known.add(question.question_id)
        self._save()

    def answer_for(self, question_id: str) -> Answer | None:
        return self.answers.get(question_id)

    # Interface -------------------------------------------------------------------

    def open_questions(self) -> list[Question]:
        return [question for question in self.questions if question.question_id not in self.answers]

    def submit(self, answer: Answer) -> None:
        question = next((item for item in self.questions if item.question_id == answer.question_id), None)
        if question is None:
            raise KeyError(answer.question_id)
        validate_answer(question, answer)
        self.answers[answer.question_id] = answer
        self._save()

    def unapplied(self) -> list[str]:
        return [key for key in self.answers if key not in self.applied]

    def mark_applied(self) -> None:
        self.applied = list(self.answers)
        self._save()
