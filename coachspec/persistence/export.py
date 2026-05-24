from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from coachspec.memory import ConversationMessage
from coachspec.runtime import CoachSession


@dataclass(frozen=True)
class SessionExportResult:
    directory: Path
    transcript_path: Path
    events_path: Path
    metadata_path: Path


class SessionExporter:
    """Export local runtime session artifacts as inspectable JSON files."""

    def export(self, session: CoachSession, directory: str | Path) -> SessionExportResult:
        export_dir = Path(directory)
        export_dir.mkdir(parents=True, exist_ok=True)

        transcript_path = export_dir / "transcript.json"
        events_path = export_dir / "events.json"
        metadata_path = export_dir / "metadata.json"

        self._write_json(transcript_path, self._transcript(session))
        self._write_json(events_path, [event.to_dict() for event in session.events()])
        self._write_json(metadata_path, self._metadata(session))

        return SessionExportResult(
            directory=export_dir,
            transcript_path=transcript_path,
            events_path=events_path,
            metadata_path=metadata_path,
        )

    def _transcript(self, session: CoachSession) -> list[dict[str, str]]:
        return [self._message_to_dict(message) for message in session.memory.snapshot().messages]

    def _metadata(self, session: CoachSession) -> dict[str, Any]:
        snapshot = session.memory.snapshot()
        return {
            "session_id": session.state.session_id,
            "coach_id": session.state.coach_id,
            "coach_name": session.spec.coach.name,
            "turn_count": session.state.turn_count,
            "is_active": session.state.is_active,
            "created_at": session.state.created_at.isoformat(),
            "updated_at": session.state.updated_at.isoformat(),
            "closed_at": session.state.closed_at.isoformat() if session.state.closed_at else None,
            "message_count": snapshot.message_count,
            "event_count": len(session.events()),
            "execution_strategy": session.composition.execution_strategy.id,
        }

    def _message_to_dict(self, message: ConversationMessage) -> dict[str, str]:
        return {
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
        }

    def _write_json(self, path: Path, payload: object) -> None:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
