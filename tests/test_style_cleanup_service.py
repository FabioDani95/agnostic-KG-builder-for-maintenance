import json

from backend.services import style_cleanup_service


def _style_cleanup_config(**overrides):
    config = {
        "enabled": True,
        "deterministic_enabled": True,
        "llm_enabled": False,
        "timeout_seconds": 120,
        "max_output_tokens": 6000,
        "preserve_numbers_units_codes": True,
        "preserve_page_refs": True,
        "reject_on_semantic_drift": True,
        "max_name_tokens": 10,
        "max_description_sentences": 2,
        "editable_fields": {
            "Asset": ["name", "description"],
            "Component": ["name", "description", "category"],
            "Symptom": ["name", "description"],
            "FailureMode": ["name", "description", "material_context"],
            "CorrectiveAction": ["name", "description", "instruction_text"],
            "ErrorCode": ["name", "description"],
        },
    }
    config.update(overrides)
    return config


def _base_ontology():
    return {
        "ontology_name": "DiagnosticOntology",
        "version": "1.0",
        "language": "en",
        "source_type": "Service manual",
        "source_title": "Mock Robot",
        "nodes": {
            "Asset": [],
            "Component": [],
            "Symptom": [],
            "FailureMode": [],
            "CorrectiveAction": [],
            "ErrorCode": [],
        },
        "relations": [],
    }


class _FakePromptTokenDetails:
    cached_tokens = 0


class _FakeUsage:
    def __init__(self, prompt_tokens=120, completion_tokens=60):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens
        self.prompt_tokens_details = _FakePromptTokenDetails()


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content, model="gpt-5.4"):
        self.choices = [_FakeChoice(content)]
        self.usage = _FakeUsage()
        self.model = model


class _FakeCompletions:
    def __init__(self, content, model="gpt-5.4"):
        self._content = content
        self._model = model

    def create(self, **kwargs):
        return _FakeResponse(self._content, model=self._model)


class _FakeChat:
    def __init__(self, content, model="gpt-5.4"):
        self.completions = _FakeCompletions(content, model=model)


class _FakeOpenAI:
    def __init__(self, *args, content="{}", model="gpt-5.4", **kwargs):
        self.chat = _FakeChat(content, model=model)


def test_cleanup_export_ontology_applies_deterministic_normalization(monkeypatch):
    monkeypatch.setattr(
        "backend.services.style_cleanup_service.get_style_cleanup_config",
        lambda: _style_cleanup_config(llm_enabled=False),
    )
    ontology = _base_ontology()
    ontology["nodes"]["Symptom"] = [
        {
            "symptom_id": "SYM-001",
            "name": "  robot does not start. ",
            "description": " startup failure  ",
            "severity": "High",
        }
    ]
    ontology["nodes"]["FailureMode"] = [
        {
            "failure_mode_id": "FM-001",
            "name": " power board fault ",
            "description": " blown fuse detected ",
            "material_context": " power board. ",
        }
    ]
    ontology["nodes"]["CorrectiveAction"] = [
        {
            "action_id": "CA-001",
            "name": " replace fuse. ",
            "description": " replace the blown fuse ",
            "instruction_text": "check fuse; replace fuse",
        }
    ]

    cleaned, usage, report = style_cleanup_service.cleanup_export_ontology(ontology, target_language="en")

    assert cleaned["nodes"]["Symptom"][0]["name"] == "Robot does not start"
    assert cleaned["nodes"]["Symptom"][0]["description"] == "Startup failure."
    assert cleaned["nodes"]["FailureMode"][0]["material_context"] == "Power board"
    assert cleaned["nodes"]["CorrectiveAction"][0]["instruction_text"] == "1. Check fuse. 2. Replace fuse."
    assert usage == {}
    assert report["deterministic_fields_changed"] >= 6


def test_cleanup_export_ontology_accepts_guarded_llm_rewrites(monkeypatch):
    monkeypatch.setattr(
        "backend.services.style_cleanup_service.get_style_cleanup_config",
        lambda: _style_cleanup_config(deterministic_enabled=False, llm_enabled=True),
    )
    monkeypatch.setattr(
        "backend.services.style_cleanup_service.OpenAI",
        lambda *args, **kwargs: _FakeOpenAI(
            content=json.dumps({
                "node__Symptom__0__name": "Power board fault",
                "node__Symptom__0__description": "Power board startup fault.",
                "node__CorrectiveAction__0__instruction_text": "1. Replace the blown 10 A fuse. 2. Restart the controller.",
            }),
            model="gpt-5.4-mini",
        ),
    )
    ontology = _base_ontology()
    ontology["nodes"]["Symptom"] = [
        {
            "symptom_id": "SYM-001",
            "name": "power board fault.",
            "description": "power board startup fault",
            "severity": "High",
        }
    ]
    ontology["nodes"]["CorrectiveAction"] = [
        {
            "action_id": "CA-001",
            "name": "replace fuse",
            "description": "replace the blown fuse",
            "instruction_text": "1. replace the blown 10 A fuse 2. restart the controller",
        }
    ]

    cleaned, usage, report = style_cleanup_service.cleanup_export_ontology(
        ontology,
        target_language="en",
        model_name="gpt-5.4-mini",
    )

    assert cleaned["nodes"]["Symptom"][0]["name"] == "Power board fault"
    assert cleaned["nodes"]["Symptom"][0]["description"] == "Power board startup fault."
    assert cleaned["nodes"]["CorrectiveAction"][0]["instruction_text"] == (
        "1. Replace the blown 10 A fuse. 2. Restart the controller."
    )
    assert usage["operation"] == "style_cleanup"
    assert usage["model"] == "gpt-5.4-mini"
    assert report["llm_fields_changed"] == 3
    assert report["llm_fields_rejected"] == 0


def test_cleanup_export_ontology_rejects_llm_rewrites_with_numeric_drift(monkeypatch):
    monkeypatch.setattr(
        "backend.services.style_cleanup_service.get_style_cleanup_config",
        lambda: _style_cleanup_config(deterministic_enabled=False, llm_enabled=True),
    )
    monkeypatch.setattr(
        "backend.services.style_cleanup_service.OpenAI",
        lambda *args, **kwargs: _FakeOpenAI(
            content=json.dumps({
                "node__CorrectiveAction__0__instruction_text": "1. Replace the blown 48 V fuse. 2. Restart the controller.",
            }),
            model="gpt-5.4",
        ),
    )
    ontology = _base_ontology()
    ontology["nodes"]["CorrectiveAction"] = [
        {
            "action_id": "CA-001",
            "name": "replace fuse",
            "description": "replace the blown fuse",
            "instruction_text": "1. Replace the blown 24 V fuse. 2. Restart the controller.",
        }
    ]

    cleaned, usage, report = style_cleanup_service.cleanup_export_ontology(
        ontology,
        target_language="en",
        model_name="gpt-5.4",
    )

    assert cleaned["nodes"]["CorrectiveAction"][0]["instruction_text"] == (
        "1. Replace the blown 24 V fuse. 2. Restart the controller."
    )
    assert usage["operation"] == "style_cleanup"
    assert report["llm_fields_changed"] == 0
    assert report["llm_fields_rejected"] == 1
