from __future__ import annotations

from backend.schemas.actions import HumanAction
from backend.schemas.chat_events import validate_chat_event
from backend.schemas.widgets import WidgetType, validate_widget_payload
from tests.chat_event_fixtures import (
    KNOWN_WIDGET_TYPES,
    sample_chat_events,
    sample_widget_payloads,
)


def test_characterized_chat_events_validate_against_schema_contract():
    for event in sample_chat_events():
        validate_chat_event(event)


def test_characterized_widget_payloads_validate_against_schema_contract():
    for widget, payload in sample_widget_payloads().items():
        validate_widget_payload({"widget": widget, **payload})


def test_widget_type_enum_matches_characterized_widget_set():
    assert {item.value for item in WidgetType} == KNOWN_WIDGET_TYPES


def test_human_action_accepts_current_chat_action_shape():
    action = HumanAction.model_validate(
        {
            "action": "approve_triplet",
            "payload": {"index": 0},
            "client_action_id": "client-approve",
            "gate_result": {"allowed": True},
        }
    )

    assert action.action == "approve_triplet"
    assert action.payload == {"index": 0}
    assert action.client_action_id == "client-approve"
