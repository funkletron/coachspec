from __future__ import annotations

import importlib.util
from pathlib import Path


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
    assert payload["status"]["message_count"] == 0
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
    assert Path(export["transcript_path"]).exists()
    assert Path(export["events_path"]).exists()
    assert Path(export["metadata_path"]).exists()
