from __future__ import annotations

from coachspec.memory.base import (
    BaseMemory,
    ConversationMessage,
    MessageRole,
    SessionMemorySnapshot,
    utc_now,
)


class InMemoryConversationMemory(BaseMemory):
    """Simple session-scoped conversation memory."""

    def __init__(self) -> None:
        self._messages: list[ConversationMessage] = []

    def append(self, role: MessageRole, content: str) -> ConversationMessage:
        message = ConversationMessage(role=role, content=content, created_at=utc_now())
        self._messages.append(message)
        return message

    def snapshot(self) -> SessionMemorySnapshot:
        return SessionMemorySnapshot(messages=tuple(self._messages))

    def clear(self) -> None:
        self._messages.clear()
