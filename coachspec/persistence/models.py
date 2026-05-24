from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast

from coachspec.memory import ConversationMessage, MessageRole, SessionMemorySnapshot


class SessionPersistenceError(ValueError):
    """Raised when a persisted session cannot be read or restored."""


@dataclass(frozen=True)
class SerializedSession:
    """Explicit, inspectable representation of a persisted runtime session."""

    metadata: dict[str, Any]
    coach_spec: dict[str, Any]
    runtime_context: dict[str, Any]
    conversation_history: tuple[ConversationMessage, ...]
    behavioral_modules: tuple[dict[str, str], ...]
    execution_strategy: dict[str, str]
    timestamps: dict[str, str | None]

    def memory_snapshot(self) -> SessionMemorySnapshot:
        return SessionMemorySnapshot(messages=self.conversation_history)


def parse_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise SessionPersistenceError(f"{field_name} must be an ISO-8601 datetime string")

    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise SessionPersistenceError(f"{field_name} is not a valid ISO-8601 datetime") from exc


def parse_optional_datetime(value: object, field_name: str) -> datetime | None:
    if value is None:
        return None
    return parse_datetime(value, field_name)


def parse_message(value: object) -> ConversationMessage:
    if not isinstance(value, dict):
        raise SessionPersistenceError("conversation_history entries must be objects")

    role = value.get("role")
    if role not in {"user", "assistant", "system"}:
        raise SessionPersistenceError("conversation_history role must be user, assistant, or system")

    content = value.get("content")
    if not isinstance(content, str):
        raise SessionPersistenceError("conversation_history content must be a string")

    created_at = parse_datetime(value.get("created_at"), "conversation_history.created_at")
    return ConversationMessage(
        role=cast(MessageRole, role),
        content=content,
        created_at=created_at,
    )


def message_to_dict(message: ConversationMessage) -> dict[str, str]:
    return {
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }
