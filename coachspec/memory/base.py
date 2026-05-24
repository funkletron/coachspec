from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal


MessageRole = Literal["user", "assistant", "system"]


@dataclass(frozen=True)
class ConversationMessage:
    role: MessageRole
    content: str
    created_at: datetime


@dataclass(frozen=True)
class SessionMemorySnapshot:
    messages: tuple[ConversationMessage, ...]

    @property
    def message_count(self) -> int:
        return len(self.messages)


class BaseMemory(ABC):
    @abstractmethod
    def append(self, role: MessageRole, content: str) -> ConversationMessage:
        """Append a conversation message and return the stored record."""

    @abstractmethod
    def snapshot(self) -> SessionMemorySnapshot:
        """Return an immutable snapshot of the current memory state."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all memory held by this store."""


def utc_now() -> datetime:
    return datetime.now(UTC)
