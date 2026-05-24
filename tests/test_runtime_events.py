from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from coachspec.cli import app
from coachspec.persistence import JsonSessionStorage, SessionExporter, SessionSerializer
from coachspec.runtime import CoachSession


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "coaches" / "spirituality" / "bible_deep_dive.yaml"


def test_session_generates_runtime_events() -> None:
    session = CoachSession.from_file(EXAMPLE)
    session.respond_stub("Help me study Romans 8.")
    session.close()

    event_types = [event.event_type for event in session.events()]

    assert event_types == [
        "session_started",
        "user_message_received",
        "memory_written",
        "assistant_message_generated",
        "memory_written",
        "session_ended",
    ]
    assert session.events()[1].payload["content"] == "Help me study Romans 8."
    assert session.events()[2].payload["role"] == "user"
    assert session.events()[4].payload["role"] == "assistant"


def test_session_event_ordering_uses_monotonic_sequence() -> None:
    session = CoachSession.from_file(EXAMPLE)
    session.respond_stub("First")
    session.respond_stub("Second")

    sequences = [event.sequence for event in session.events()]

    assert sequences == list(range(1, len(sequences) + 1))
    assert [event.event_type for event in session.events()[1:5]] == [
        "user_message_received",
        "memory_written",
        "assistant_message_generated",
        "memory_written",
    ]


def test_runtime_events_are_json_serializable_and_ordered() -> None:
    session = CoachSession.from_file(EXAMPLE)
    session.respond_stub("Help me study Romans 8.")
    session.close()

    serialized = [event.to_dict() for event in session.events()]
    encoded = json.dumps(serialized)
    decoded = json.loads(encoded)

    assert [event["sequence"] for event in decoded] == list(range(1, len(decoded) + 1))
    assert all(isinstance(event["created_at"], str) for event in decoded)
    assert decoded[0]["event_type"] == "session_started"
    assert decoded[-1]["event_type"] == "session_ended"


def test_session_serializer_round_trips_events() -> None:
    session = CoachSession.from_file(EXAMPLE)
    session.respond_stub("Help me study John 1.")

    payload = SessionSerializer().to_dict(session)
    reloaded = SessionSerializer().from_dict(payload)

    assert [event["event_type"] for event in payload["events"]][-1] == "memory_read"
    assert [event.event_type for event in reloaded.events()] == [
        event["event_type"] for event in payload["events"]
    ]


def test_session_export_writes_transcript_events_and_metadata(tmp_path: Path) -> None:
    session = CoachSession.from_file(EXAMPLE)
    session.respond_stub("Help me read Psalm 23.")
    session.close()

    result = SessionExporter().export(session, tmp_path / "export")

    transcript = json.loads(result.transcript_path.read_text(encoding="utf-8"))
    events = json.loads(result.events_path.read_text(encoding="utf-8"))
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))

    assert result.directory == tmp_path / "export"
    assert result.transcript_path.parent == result.directory
    assert result.events_path.parent == result.directory
    assert result.metadata_path.parent == result.directory
    assert [message["role"] for message in transcript] == ["user", "assistant"]
    assert transcript[0]["content"] == "Help me read Psalm 23."
    assert events[0]["event_type"] == "session_started"
    assert events[-1]["event_type"] == "session_ended"
    assert metadata["session_id"] == session.state.session_id
    assert metadata["message_count"] == 2
    assert metadata["event_count"] == len(events)


def test_cli_export_session_uses_persisted_local_session(tmp_path: Path) -> None:
    runner = CliRunner()
    session = CoachSession.from_file(EXAMPLE)
    session.respond_stub("Hello")
    JsonSessionStorage().save(session, tmp_path / "last_session.json")

    output_dir = tmp_path / "exported"
    result = runner.invoke(
        app,
        [
            "export-session",
            session.state.session_id,
            "--sessions-dir",
            str(tmp_path),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert result.exit_code == 0
    assert "Exported session" in result.stdout
    assert (output_dir / "transcript.json").exists()
    assert (output_dir / "events.json").exists()
    assert (output_dir / "metadata.json").exists()


def test_cli_mock_provider_run_persists_exportable_turns_events_and_counts(tmp_path: Path) -> None:
    runner = CliRunner()
    sessions_dir = tmp_path / "sessions"

    run_result = runner.invoke(
        app,
        [
            "run",
            str(EXAMPLE),
            "--mock-provider",
            "--sessions-dir",
            str(sessions_dir),
        ],
        input="Help me study John 1.\n/exit\n",
    )

    assert run_result.exit_code == 0
    session_files = list(sessions_dir.glob("*.json"))
    assert len(session_files) == 1

    persisted = JsonSessionStorage().load(session_files[0])
    session_id = persisted.state.session_id
    assert persisted.state.turn_count == 1
    assert persisted.state.is_active is False
    assert persisted.state.closed_at is not None
    assert [message.role for message in persisted.memory.snapshot().messages] == [
        "user",
        "assistant",
    ]
    assert "Mock provider response for Bible Deep Dive Coach" in (
        persisted.memory.snapshot().messages[1].content
    )
    assert "session_ended" in [event.event_type for event in persisted.events()]

    output_dir = tmp_path / "exported"
    export_result = runner.invoke(
        app,
        [
            "export-session",
            session_id,
            "--sessions-dir",
            str(sessions_dir),
            "--output-dir",
            str(output_dir),
        ],
    )

    assert export_result.exit_code == 0

    transcript = json.loads((output_dir / "transcript.json").read_text(encoding="utf-8"))
    events = json.loads((output_dir / "events.json").read_text(encoding="utf-8"))
    metadata = json.loads((output_dir / "metadata.json").read_text(encoding="utf-8"))

    assert [message["role"] for message in transcript] == ["user", "assistant"]
    assert transcript[0]["content"] == "Help me study John 1."
    assert any(event["event_type"] == "user_message_received" for event in events)
    assert any(event["event_type"] == "assistant_message_generated" for event in events)
    assert any(event["event_type"] == "session_ended" for event in events)
    assert metadata["turn_count"] == 1
    assert metadata["message_count"] == len(transcript) == 2
    assert metadata["event_count"] == len(events)
    assert metadata["is_active"] is False
    assert metadata["closed_at"] is not None
