from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from backend.schemas.widgets import validate_widget_payload


class _ChatEventBase(BaseModel):
    model_config = ConfigDict(extra="allow")


class ProgressEvent(_ChatEventBase):
    type: Literal["progress"]
    phase: str = ""
    message: str = ""


class ChatDeltaEvent(_ChatEventBase):
    type: Literal["chat_delta"]
    text: str = ""


class WidgetEvent(_ChatEventBase):
    type: Literal["widget"]
    widget: str
    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_payload_contract(self) -> "WidgetEvent":
        validate_widget_payload({"widget": self.widget, **self.payload})
        return self


class CritiqueEvent(_ChatEventBase):
    type: Literal["critique"]
    message: str = ""
    entity_id: str | None = None
    suggestion: str | None = None


class NeedsInputEvent(_ChatEventBase):
    type: Literal["needs_input"]
    message: str = ""


class DoneEvent(_ChatEventBase):
    type: Literal["done"]
    summary: str = ""


class ErrorEvent(_ChatEventBase):
    type: Literal["error"]
    message: str = ""


class ThinkingEvent(_ChatEventBase):
    type: Literal["thinking"]


ChatEvent = Annotated[
    ProgressEvent
    | ChatDeltaEvent
    | WidgetEvent
    | CritiqueEvent
    | NeedsInputEvent
    | DoneEvent
    | ErrorEvent
    | ThinkingEvent,
    Field(discriminator="type"),
]

_CHAT_EVENT_ADAPTER = TypeAdapter(ChatEvent)


def validate_chat_event(event: dict[str, Any]):
    return _CHAT_EVENT_ADAPTER.validate_python(event)
