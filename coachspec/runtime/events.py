from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, ClassVar

from coachspec.memory import utc_now


@dataclass(frozen=True)
class RuntimeEvent:
    """Provider-neutral runtime event emitted by a CoachSpec session."""

    session_id: str
    coach_id: str
    sequence: int
    created_at: datetime
    payload: dict[str, Any] = field(default_factory=dict)

    event_type: ClassVar[str] = "runtime_event"

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "session_id": self.session_id,
            "coach_id": self.coach_id,
            "sequence": self.sequence,
            "created_at": self.created_at.isoformat(),
            "payload": self.payload,
        }


class SessionStarted(RuntimeEvent):
    event_type: ClassVar[str] = "session_started"


class UserMessageReceived(RuntimeEvent):
    event_type: ClassVar[str] = "user_message_received"


class AssistantMessageGenerated(RuntimeEvent):
    event_type: ClassVar[str] = "assistant_message_generated"


class MemoryRead(RuntimeEvent):
    event_type: ClassVar[str] = "memory_read"


class MemoryWritten(RuntimeEvent):
    event_type: ClassVar[str] = "memory_written"


class SessionEnded(RuntimeEvent):
    event_type: ClassVar[str] = "session_ended"


EVENT_TYPES: dict[str, type[RuntimeEvent]] = {
    event.event_type: event
    for event in (
        SessionStarted,
        UserMessageReceived,
        AssistantMessageGenerated,
        MemoryRead,
        MemoryWritten,
        SessionEnded,
    )
}


class InMemoryEventCollector:
    """Append-only event collector for one local runtime session."""

    def __init__(self, events: tuple[RuntimeEvent, ...] | None = None) -> None:
        self._events: list[RuntimeEvent] = list(events or ())

    def emit(
        self,
        event_class: type[RuntimeEvent],
        *,
        session_id: str,
        coach_id: str,
        payload: dict[str, Any] | None = None,
    ) -> RuntimeEvent:
        event = event_class(
            session_id=session_id,
            coach_id=coach_id,
            sequence=len(self._events) + 1,
            created_at=utc_now(),
            payload=payload or {},
        )
        self._events.append(event)
        return event

    def snapshot(self) -> tuple[RuntimeEvent, ...]:
        return tuple(self._events)


def event_from_dict(data: object) -> RuntimeEvent:
    if not isinstance(data, dict):
        raise ValueError("event must be an object")

    event_type = data.get("event_type")
    event_class = EVENT_TYPES.get(event_type)
    if event_class is None:
        raise ValueError("event_type is not supported")

    session_id = data.get("session_id")
    coach_id = data.get("coach_id")
    sequence = data.get("sequence")
    created_at = data.get("created_at")
    payload = data.get("payload", {})

    if not isinstance(session_id, str) or not session_id:
        raise ValueError("session_id must be a non-empty string")
    if not isinstance(coach_id, str) or not coach_id:
        raise ValueError("coach_id must be a non-empty string")
    if not isinstance(sequence, int) or sequence < 1:
        raise ValueError("sequence must be a positive integer")
    if not isinstance(created_at, str):
        raise ValueError("created_at must be an ISO-8601 datetime string")
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")

    return event_class(
        session_id=session_id,
        coach_id=coach_id,
        sequence=sequence,
        created_at=datetime.fromisoformat(created_at),
        payload=payload,
    )
