from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from coachspec.adapters import MockProviderAdapter
from coachspec.composition import CoachComposition
from coachspec.compiler import compile_prompt
from coachspec.evaluation import evaluate_coachspec
from coachspec.persistence import JsonSessionStorage, SessionExporter
from coachspec.runtime import CoachSession
from coachspec.schema import validate_coachspec


EXAMPLE_COACH = ROOT / "coaches" / "spirituality" / "bible_deep_dive.yaml"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="coachspec-smoke-") as temp_dir:
        workspace = Path(temp_dir)

        spec, errors = validate_coachspec(EXAMPLE_COACH)
        _assert(not errors, f"validation failed: {errors}")
        _assert(spec is not None, "validation did not return a CoachSpec")
        print("validation passed")

        composition = CoachComposition.from_spec(spec)
        composition.validate()
        _assert(composition.execution_strategy.id == "socratic_loop", "unexpected execution strategy")
        _assert(tuple(composition.module_ids()), "inspect found no behavioral modules")
        print("inspect passed")

        compiled = compile_prompt(spec, composition=composition)
        _assert(compiled.coach_id == spec.coach.id, "compiled prompt coach id mismatch")
        _assert("# Coach Identity" in compiled.text, "compiled prompt missing identity section")
        _assert(spec.coach.name in compiled.text, "compiled prompt missing coach name")
        print("compile passed")

        session = CoachSession.from_spec(
            spec,
            provider_adapter=MockProviderAdapter(response_prefix="Smoke test mock response"),
        )
        response = session.respond_stub("Help me study John 1 in three short steps.")
        session.close()
        snapshot = session.memory.snapshot()
        _assert("Smoke test mock response for Bible Deep Dive Coach" in response, "mock response mismatch")
        _assert(session.state.turn_count == 1, "session should contain one user turn")
        _assert(snapshot.message_count == 2, "session should contain user and assistant messages")
        _assert(session.events()[-1].event_type == "session_ended", "session did not close cleanly")
        print("mock session passed")

        session_path = workspace / "sessions" / f"{session.state.session_id}.json"
        storage = JsonSessionStorage()
        written = storage.save(session, session_path)
        reloaded = storage.load(written)
        _assert(written.exists(), "session file was not written")
        _assert(reloaded.state.session_id == session.state.session_id, "persisted session id mismatch")
        _assert(reloaded.memory.snapshot().message_count == 2, "persisted message count mismatch")
        print("persistence passed")

        export_dir = workspace / "exports" / session.state.session_id
        export_result = SessionExporter().export(reloaded, export_dir)
        transcript = _read_json(export_result.transcript_path)
        events = _read_json(export_result.events_path)
        metadata = _read_json(export_result.metadata_path)
        _assert([message["role"] for message in transcript] == ["user", "assistant"], "bad transcript export")
        _assert(events[0]["event_type"] == "session_started", "bad events export")
        _assert(metadata["session_id"] == session.state.session_id, "bad metadata export")
        _assert(metadata["message_count"] == 2, "bad metadata message count")
        print("export passed")

        report = evaluate_coachspec(spec)
        _assert(report.coach_id == spec.coach.id, "evaluation coach id mismatch")
        _assert(report.overall_score >= 0.75, "evaluation score below smoke threshold")
        _assert(report.results, "evaluation produced no criteria")
        print("evaluation passed")

    print("smoke test completed successfully")


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


if __name__ == "__main__":
    main()
