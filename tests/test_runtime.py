from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from coachspec.cli import app
from coachspec.memory import InMemoryConversationMemory, SessionMemorySnapshot
from coachspec.runtime import CoachSession, RuntimeContext, SessionState
from coachspec.schema import load_coachspec


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "coaches" / "spirituality" / "bible_deep_dive.yaml"


def test_session_initialization_loads_spec_and_compiled_prompt() -> None:
    session = CoachSession.from_file(EXAMPLE)

    assert isinstance(session.state, SessionState)
    assert session.state.coach_id == "bible-deep-dive"
    assert session.state.turn_count == 0
    assert session.state.is_active is True
    assert session.compiled_prompt.coach_id == "bible-deep-dive"
    assert "# Coach Identity" in session.compiled_prompt.text


def test_memory_persistence_and_snapshot() -> None:
    memory = InMemoryConversationMemory()

    memory.append("user", "What is context?")
    memory.append("assistant", "Context is the surrounding passage and setting.")
    snapshot = memory.snapshot()

    assert isinstance(snapshot, SessionMemorySnapshot)
    assert snapshot.message_count == 2
    assert snapshot.messages[0].role == "user"
    assert snapshot.messages[0].content == "What is context?"
    assert snapshot.messages[1].role == "assistant"


def test_runtime_context_creation() -> None:
    spec = load_coachspec(EXAMPLE)
    session = CoachSession.from_spec(spec)

    context = session.context()

    assert isinstance(context, RuntimeContext)
    assert context.coach_id == "bible-deep-dive"
    assert context.coach_name == "Bible Deep Dive Coach"
    assert context.session_id == session.state.session_id
    assert context.memory_snapshot.message_count == 0


def test_session_message_append_behavior() -> None:
    session = CoachSession.from_file(EXAMPLE)

    session.append_user_message("Help me study John 1.")
    session.append_assistant_message("No provider is configured yet.")
    snapshot = session.memory.snapshot()

    assert session.state.turn_count == 1
    assert snapshot.message_count == 2
    assert [message.role for message in snapshot.messages] == ["user", "assistant"]


def test_session_stub_response_records_conversation() -> None:
    session = CoachSession.from_file(EXAMPLE)

    response = session.respond_stub("Help me study Romans 8.")
    snapshot = session.memory.snapshot()

    assert "No model provider is configured yet." in response
    assert session.state.turn_count == 1
    assert snapshot.message_count == 2
    assert snapshot.messages[0].content == "Help me study Romans 8."


def test_cli_run_accepts_input_and_exits() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["run", str(EXAMPLE)], input="Hello\n/exit\n")

    assert result.exit_code == 0
    assert "CoachSpec Runtime" in result.stdout
    assert "No LLM provider is configured." in result.stdout
    assert "Runtime is initialized and memory recorded your message." in result.stdout
