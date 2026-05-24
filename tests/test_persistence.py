from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from coachspec.cli import app
from coachspec.persistence import JsonSessionStorage, SessionPersistenceError, SessionSerializer
from coachspec.runtime import CoachSession


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "coaches" / "spirituality" / "bible_deep_dive.yaml"


def test_session_serializer_records_runtime_state() -> None:
    session = CoachSession.from_file(EXAMPLE)
    session.respond_stub("Help me study John 1.")

    payload = SessionSerializer().to_dict(session)

    assert payload["metadata"]["format"] == "coachspec.session"
    assert payload["metadata"]["session_id"] == session.state.session_id
    assert payload["metadata"]["turn_count"] == 1
    assert payload["runtime_context"]["coach_id"] == "bible-deep-dive"
    assert payload["execution_strategy"]["id"] == "socratic_loop"
    assert payload["behavioral_modules"][0]["id"] == "socratic_questioning"
    assert [message["role"] for message in payload["conversation_history"]] == [
        "user",
        "assistant",
    ]
    assert payload["timestamps"]["created_at"]
    assert payload["timestamps"]["updated_at"]


def test_session_reload_restores_state_and_history() -> None:
    session = CoachSession.from_file(EXAMPLE)
    session.respond_stub("What should I notice in Romans 8?")
    session.close()

    reloaded = SessionSerializer().from_dict(SessionSerializer().to_dict(session))

    assert reloaded.state.session_id == session.state.session_id
    assert reloaded.state.turn_count == 1
    assert reloaded.state.is_active is False
    assert reloaded.state.closed_at == session.state.closed_at
    assert reloaded.context().execution_strategy.id == "socratic_loop"
    assert reloaded.memory.snapshot().messages[0].content == "What should I notice in Romans 8?"


def test_json_session_storage_persists_to_filesystem(tmp_path: Path) -> None:
    path = tmp_path / "session.json"
    session = CoachSession.from_file(EXAMPLE)
    session.respond_stub("Help me read Psalm 23.")

    written = JsonSessionStorage().save(session, path)
    loaded = JsonSessionStorage().load(written)

    assert written == path
    assert json.loads(path.read_text(encoding="utf-8"))["metadata"]["session_id"]
    assert loaded.state.session_id == session.state.session_id
    assert loaded.memory.snapshot().message_count == 2


def test_json_session_storage_rejects_corrupted_json(tmp_path: Path) -> None:
    path = tmp_path / "corrupt.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(SessionPersistenceError, match="invalid JSON session file"):
        JsonSessionStorage().load(path)


def test_json_session_storage_rejects_invalid_session_shape(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps({"metadata": {}}), encoding="utf-8")

    with pytest.raises(SessionPersistenceError):
        JsonSessionStorage().load(path)


def test_cli_save_and_load_session(tmp_path: Path) -> None:
    runner = CliRunner()
    path = tmp_path / "saved-session.json"

    save_result = runner.invoke(
        app,
        ["save-session", "--coach", str(EXAMPLE), "--output", str(path), "--message", "Hello"],
    )
    load_result = runner.invoke(app, ["load-session", "--path", str(path)])

    assert save_result.exit_code == 0
    assert "Saved session" in save_result.stdout
    assert load_result.exit_code == 0
    assert "Loaded CoachSpec Session" in load_result.stdout
    assert "Messages: 2" in load_result.stdout
