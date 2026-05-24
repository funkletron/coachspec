from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ValidationError

from coachspec.persistence.models import (
    SerializedSession,
    SessionPersistenceError,
    message_to_dict,
    parse_message,
)
from coachspec.runtime import CoachSession, SessionState
from coachspec.schema import CoachSpec


class SessionSerializer:
    """Convert runtime sessions to and from explicit JSON-compatible data."""

    format_version = 1

    def serialize(self, session: CoachSession) -> SerializedSession:
        context = session.context()
        snapshot = context.memory_snapshot
        modules = tuple(
            {
                "id": module.id,
                "name": module.name,
                "description": module.description,
            }
            for module in session.composition.behavioral_modules
        )
        strategy = {
            "id": context.execution_strategy.id,
            "name": context.execution_strategy.name,
            "summary": context.execution_strategy.summary,
        }
        timestamps = {
            "created_at": session.state.created_at.isoformat(),
            "updated_at": session.state.updated_at.isoformat(),
            "closed_at": session.state.closed_at.isoformat() if session.state.closed_at else None,
        }

        return SerializedSession(
            metadata={
                "format": "coachspec.session",
                "format_version": self.format_version,
                "session_id": session.state.session_id,
                "coach_id": session.state.coach_id,
                "coach_name": session.spec.coach.name,
                "turn_count": session.state.turn_count,
                "is_active": session.state.is_active,
            },
            coach_spec=session.spec.model_dump(mode="json"),
            runtime_context={
                "coach_id": context.coach_id,
                "coach_name": context.coach_name,
                "session_id": context.session_id,
                "compiled_prompt": {
                    "coach_id": context.compiled_prompt.coach_id,
                    "text": context.compiled_prompt.text,
                },
                "memory_message_count": snapshot.message_count,
            },
            conversation_history=snapshot.messages,
            behavioral_modules=modules,
            execution_strategy=strategy,
            timestamps=timestamps,
        )

    def to_dict(self, session: CoachSession) -> dict[str, Any]:
        serialized = self.serialize(session)
        return {
            "metadata": serialized.metadata,
            "coach_spec": serialized.coach_spec,
            "runtime_context": serialized.runtime_context,
            "conversation_history": [
                message_to_dict(message) for message in serialized.conversation_history
            ],
            "behavioral_modules": list(serialized.behavioral_modules),
            "execution_strategy": serialized.execution_strategy,
            "timestamps": serialized.timestamps,
        }

    def from_dict(self, data: object) -> CoachSession:
        if not isinstance(data, dict):
            raise SessionPersistenceError("session file must contain a JSON object")

        metadata = self._require_dict(data, "metadata")
        if metadata.get("format") != "coachspec.session":
            raise SessionPersistenceError("session file format is not coachspec.session")
        if metadata.get("format_version") != self.format_version:
            raise SessionPersistenceError("unsupported session file format_version")

        coach_spec_data = self._require_dict(data, "coach_spec")
        timestamps = self._require_dict(data, "timestamps")
        history = data.get("conversation_history")
        if not isinstance(history, list):
            raise SessionPersistenceError("conversation_history must be a list")

        try:
            spec = CoachSpec.model_validate(coach_spec_data)
        except ValidationError as exc:
            raise SessionPersistenceError("coach_spec is not a valid CoachSpec") from exc

        session_id = metadata.get("session_id")
        coach_id = metadata.get("coach_id")
        turn_count = metadata.get("turn_count")
        is_active = metadata.get("is_active")
        if not isinstance(session_id, str) or not session_id:
            raise SessionPersistenceError("metadata.session_id must be a non-empty string")
        if not isinstance(coach_id, str) or not coach_id:
            raise SessionPersistenceError("metadata.coach_id must be a non-empty string")
        if not isinstance(turn_count, int) or turn_count < 0:
            raise SessionPersistenceError("metadata.turn_count must be a non-negative integer")
        if not isinstance(is_active, bool):
            raise SessionPersistenceError("metadata.is_active must be a boolean")

        state = SessionState(
            session_id=session_id,
            coach_id=coach_id,
            turn_count=turn_count,
            is_active=is_active,
            created_at=self._parse_timestamp(timestamps, "created_at"),
            updated_at=self._parse_timestamp(timestamps, "updated_at"),
            closed_at=self._parse_optional_timestamp(timestamps, "closed_at"),
        )
        snapshot = SerializedSession(
            metadata=metadata,
            coach_spec=coach_spec_data,
            runtime_context=self._require_dict(data, "runtime_context"),
            conversation_history=tuple(parse_message(message) for message in history),
            behavioral_modules=tuple(self._require_mapping_list(data, "behavioral_modules")),
            execution_strategy=self._require_dict(data, "execution_strategy"),
            timestamps=timestamps,
        ).memory_snapshot()

        return CoachSession.from_persisted_state(spec, state=state, memory_snapshot=snapshot)

    def _require_dict(self, data: dict[str, Any], key: str) -> dict[str, Any]:
        value = data.get(key)
        if not isinstance(value, dict):
            raise SessionPersistenceError(f"{key} must be an object")
        return value

    def _require_mapping_list(self, data: dict[str, Any], key: str) -> list[dict[str, str]]:
        value = data.get(key)
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise SessionPersistenceError(f"{key} must be a list of objects")
        return value

    def _parse_timestamp(self, timestamps: dict[str, Any], key: str) -> datetime:
        from coachspec.persistence.models import parse_datetime

        return parse_datetime(timestamps.get(key), f"timestamps.{key}")

    def _parse_optional_timestamp(self, timestamps: dict[str, Any], key: str) -> datetime | None:
        from coachspec.persistence.models import parse_optional_datetime

        return parse_optional_datetime(timestamps.get(key), f"timestamps.{key}")
