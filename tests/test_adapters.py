from __future__ import annotations

import builtins
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from coachspec.adapters import MockProviderAdapter, OpenAIProviderAdapter, ProviderRequest, ProviderResponse
from coachspec.adapters.openai import OpenAIProviderConfigurationError
from coachspec.runtime import CoachSession


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "coaches" / "spirituality" / "bible_deep_dive.yaml"


def test_runtime_import_does_not_require_provider_sdks(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def reject_openai_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "openai" or name.startswith("openai."):
            raise AssertionError("runtime import attempted to import optional openai SDK")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", reject_openai_import)

    runtime_module = importlib.reload(importlib.import_module("coachspec.runtime"))
    session = runtime_module.CoachSession.from_file(EXAMPLE)

    assert session.respond_stub("Hello").startswith("Runtime is initialized")


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


def test_mock_provider_is_deterministic_for_same_request() -> None:
    session = CoachSession.from_file(EXAMPLE)
    session.append_user_message("Help me study Psalm 23.")
    request = session.build_provider_request("Help me study Psalm 23.")
    adapter = MockProviderAdapter(response_prefix="Local deterministic response")

    first = adapter.generate(request)
    second = adapter.generate(request)

    assert first == second
    assert first.provider == "mock"
    assert first.metadata["turn_count"] == request.memory_snapshot.message_count


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


def test_openai_provider_maps_request_to_chat_completion() -> None:
    session = CoachSession.from_file(EXAMPLE)
    session.append_user_message("Help me study Psalm 23.")
    request = session.build_provider_request("Help me study Psalm 23.")
    client = FakeOpenAIClient("Look closely at the passage structure.")
    adapter = OpenAIProviderAdapter(model="test-model", client=client)

    response = adapter.generate(request)

    assert response.content == "Look closely at the passage structure."
    assert response.provider == "openai"
    assert response.metadata["coach_id"] == "bible-deep-dive"
    assert response.metadata["session_id"] == session.state.session_id
    assert response.metadata["model"] == "test-model"
    assert response.metadata["response_id"] == "response-123"
    assert response.metadata["finish_reason"] == "stop"
    assert client.request_kwargs["model"] == "test-model"
    assert client.request_kwargs["messages"][0] == {
        "role": "system",
        "content": request.instructions,
    }
    assert client.request_kwargs["messages"][1] == {
        "role": "user",
        "content": "Help me study Psalm 23.",
    }


def test_openai_provider_requires_api_key_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(OpenAIProviderConfigurationError, match="OPENAI_API_KEY"):
        OpenAIProviderAdapter()


class FakeOpenAIClient:
    def __init__(self, content: str) -> None:
        self.request_kwargs: dict[str, object] = {}
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create),
        )
        self._content = content

    def _create(self, **kwargs: object) -> object:
        self.request_kwargs = kwargs
        return SimpleNamespace(
            id="response-123",
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self._content),
                    finish_reason="stop",
                )
            ],
        )
