from __future__ import annotations

from pathlib import Path

from coachspec.adapters import MockProviderAdapter, ProviderRequest, ProviderResponse
from coachspec.runtime import CoachSession


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "coaches" / "spirituality" / "bible_deep_dive.yaml"


def test_mock_provider_response() -> None:
    session = CoachSession.from_file(EXAMPLE)
    session.append_user_message("Help me study Psalm 23.")
    request = session.build_provider_request("Help me study Psalm 23.")
    adapter = MockProviderAdapter()

    response = adapter.generate(request)

    assert isinstance(response, ProviderResponse)
    assert response.provider == "mock"
    assert "Mock provider response for Bible Deep Dive Coach" in response.content
    assert "Help me study Psalm 23." in response.content
    assert response.metadata["coach_id"] == "bible-deep-dive"


def test_session_with_provider_adapter_records_mock_response() -> None:
    session = CoachSession.from_file(EXAMPLE, provider_adapter=MockProviderAdapter())

    response = session.respond_stub("What should I notice in John 1?")
    snapshot = session.memory.snapshot()

    assert "Mock provider response" in response
    assert session.state.turn_count == 1
    assert snapshot.message_count == 2
    assert snapshot.messages[0].role == "user"
    assert snapshot.messages[1].role == "assistant"
    assert snapshot.messages[1].content == response


def test_provider_request_construction() -> None:
    session = CoachSession.from_file(EXAMPLE)
    session.append_user_message("How do I read this passage carefully?")

    request = session.build_provider_request("How do I read this passage carefully?")

    assert isinstance(request, ProviderRequest)
    assert request.coach_id == "bible-deep-dive"
    assert request.coach_name == "Bible Deep Dive Coach"
    assert request.session_id == session.state.session_id
    assert request.user_input == "How do I read this passage carefully?"
    assert "# Coach Identity" in request.instructions
    assert request.execution_strategy.id == "socratic_loop"
    assert request.memory_snapshot.message_count == 1
