from __future__ import annotations

import importlib.util
from http import HTTPStatus
from pathlib import Path

import pytest

from coachspec.adapters import BaseProviderAdapter, ProviderRequest, ProviderResponse


ROOT = Path(__file__).resolve().parents[1]
APP_PATH = ROOT / "examples" / "web-demo" / "app.py"


def load_demo_module():
    spec = importlib.util.spec_from_file_location("coachspec_web_demo", APP_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_web_demo_lists_example_coaches() -> None:
    module = load_demo_module()
    demo = module.WebDemo(root=ROOT)

    coaches = demo.list_coaches()

    assert any(coach["id"] == "bible-deep-dive" for coach in coaches)
    bible = next(coach for coach in coaches if coach["id"] == "bible-deep-dive")
    assert bible["name"] == "Bible Deep Dive Coach"
    assert "biblical passages" in bible["summary"]


def test_web_demo_creates_persisted_mock_session(tmp_path: Path) -> None:
    module = load_demo_module()
    demo = module.WebDemo(
        root=ROOT,
        sessions_dir=tmp_path / "sessions",
        exports_dir=tmp_path / "exports",
    )

    payload = demo.start_session("bible-deep-dive")

    assert payload["coach"]["name"] == "Bible Deep Dive Coach"
    assert payload["runtime"]["provider"] == "mock"
    assert payload["runtime"]["session_id"] == payload["session_id"]
    assert payload["runtime"]["event_count"] == len(payload["events"])
    assert payload["runtime"]["started_at"]
    assert payload["status"]["provider"] == "mock"
    assert payload["status"]["message_count"] == 0
    assert Path(payload["status"]["session_path"]).exists()


def test_web_demo_explicit_mock_provider_creates_session(tmp_path: Path) -> None:
    module = load_demo_module()
    demo = module.WebDemo(
        root=ROOT,
        sessions_dir=tmp_path / "sessions",
        exports_dir=tmp_path / "exports",
    )

    payload = demo.start_session("bible-deep-dive", provider="mock")

    assert payload["runtime"]["provider"] == "mock"
    assert Path(payload["status"]["session_path"]).exists()


def test_web_demo_records_mock_response_and_exports(tmp_path: Path) -> None:
    module = load_demo_module()
    demo = module.WebDemo(
        root=ROOT,
        sessions_dir=tmp_path / "sessions",
        exports_dir=tmp_path / "exports",
    )
    session = demo.start_session("bible-deep-dive")

    reply = demo.send_message(session["session_id"], "Help me study John 1.")
    export = demo.export_session(session["session_id"])

    assert "Mock provider response for Bible Deep Dive Coach" in reply["response"]
    assert reply["status"]["turn_count"] == 1
    assert [message["role"] for message in reply["transcript"]] == ["user", "assistant"]
    assert [event["sequence"] for event in reply["events"]] == list(
        range(1, len(reply["events"]) + 1)
    )
    assert any(event["event_type"] == "memory_read" for event in reply["events"])
    assert reply["runtime"]["event_count"] == len(reply["events"])
    assert Path(export["transcript_path"]).exists()
    assert Path(export["events_path"]).exists()
    assert Path(export["metadata_path"]).exists()


def test_web_demo_rejects_unsupported_provider(tmp_path: Path) -> None:
    module = load_demo_module()
    demo = module.WebDemo(
        root=ROOT,
        sessions_dir=tmp_path / "sessions",
        exports_dir=tmp_path / "exports",
    )

    with pytest.raises(module.DemoError) as exc_info:
        demo.start_session("bible-deep-dive", provider="unsupported")

    assert exc_info.value.status == HTTPStatus.BAD_REQUEST
    assert "Unsupported provider" in exc_info.value.message


def test_web_demo_missing_openai_api_key_returns_configuration_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_demo_module()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    demo = module.WebDemo(
        root=ROOT,
        sessions_dir=tmp_path / "sessions",
        exports_dir=tmp_path / "exports",
    )

    with pytest.raises(module.DemoError) as exc_info:
        demo.start_session("bible-deep-dive", provider="openai")

    assert exc_info.value.status == HTTPStatus.BAD_REQUEST
    assert "OPENAI_API_KEY" in exc_info.value.message
    assert demo.sessions == {}


def test_web_demo_openai_dependency_error_is_clear(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_demo_module()
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    class MissingDependencyAdapter:
        def __init__(self) -> None:
            raise module.OpenAIProviderConfigurationError(
                "OpenAI provider requires the optional 'openai' package."
            )

    monkeypatch.setattr(module, "OpenAIProviderAdapter", MissingDependencyAdapter)
    demo = module.WebDemo(
        root=ROOT,
        sessions_dir=tmp_path / "sessions",
        exports_dir=tmp_path / "exports",
    )

    with pytest.raises(module.DemoError) as exc_info:
        demo.start_session("bible-deep-dive", provider="openai")

    assert exc_info.value.status == HTTPStatus.BAD_REQUEST
    assert "optional 'openai' package" in exc_info.value.message
    assert demo.sessions == {}


def test_web_demo_config_reports_provider_status_without_secrets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_demo_module()
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    demo = module.WebDemo(
        root=ROOT,
        sessions_dir=tmp_path / "sessions",
        exports_dir=tmp_path / "exports",
    )

    payload = demo.config()

    assert payload["default_provider"] == "mock"
    assert payload["providers"]["mock"]["available"] is True
    assert "test-secret" not in str(payload)


def test_web_demo_message_path_uses_coach_session_respond(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_demo_module()
    called = False
    original_respond = module.CoachSession.respond

    def track_respond(self: object, user_input: str) -> str:
        nonlocal called
        called = True
        return original_respond(self, user_input)

    monkeypatch.setattr(module.CoachSession, "respond", track_respond)
    demo = module.WebDemo(
        root=ROOT,
        sessions_dir=tmp_path / "sessions",
        exports_dir=tmp_path / "exports",
    )
    session = demo.start_session("bible-deep-dive")

    demo.send_message(session["session_id"], "Help me study John 1.")

    assert called is True


def test_web_demo_openai_path_can_use_fake_adapter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = load_demo_module()

    class FakeOpenAIProviderAdapter(BaseProviderAdapter):
        provider_name = "openai"

        def generate(self, request: ProviderRequest) -> ProviderResponse:
            return ProviderResponse(
                content=f"Fake OpenAI response for {request.coach_name}.",
                provider=self.provider_name,
            )

    monkeypatch.setattr(module, "OpenAIProviderAdapter", FakeOpenAIProviderAdapter)
    demo = module.WebDemo(
        root=ROOT,
        sessions_dir=tmp_path / "sessions",
        exports_dir=tmp_path / "exports",
    )
    session = demo.start_session("bible-deep-dive", provider="openai")

    reply = demo.send_message(session["session_id"], "Help me study John 1.")

    assert reply["runtime"]["provider"] == "openai"
    assert reply["response"] == "Fake OpenAI response for Bible Deep Dive Coach."
    assert [message["role"] for message in reply["transcript"]] == ["user", "assistant"]
