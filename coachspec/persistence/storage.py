from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

from coachspec.persistence.models import SessionPersistenceError
from coachspec.persistence.serializer import SessionSerializer
from coachspec.runtime import CoachSession


class SessionStorage(ABC):
    """Persistence boundary for runtime sessions."""

    @abstractmethod
    def save(self, session: CoachSession, path: str | Path) -> Path:
        """Persist a session and return the written path."""

    @abstractmethod
    def load(self, path: str | Path) -> CoachSession:
        """Load a persisted session."""


class JsonSessionStorage(SessionStorage):
    """Human-readable local filesystem storage for CoachSpec sessions."""

    def __init__(self, serializer: SessionSerializer | None = None) -> None:
        self.serializer = serializer or SessionSerializer()

    def save(self, session: CoachSession, path: str | Path) -> Path:
        session_path = Path(path)
        session_path.parent.mkdir(parents=True, exist_ok=True)
        payload = self.serializer.to_dict(session)
        session_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return session_path

    def load(self, path: str | Path) -> CoachSession:
        session_path = Path(path)
        try:
            raw = session_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise SessionPersistenceError(f"could not read session file: {session_path}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SessionPersistenceError(f"invalid JSON session file: {session_path}") from exc

        return self.serializer.from_dict(data)
