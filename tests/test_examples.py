from __future__ import annotations

from pathlib import Path

from coachspec.compiler import compile_prompt
from coachspec.schema import CoachSpec, load_coachspec


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = sorted((ROOT / "coaches").rglob("*.yaml"))


def test_example_library_contains_expected_coaches() -> None:
    assert {path.stem for path in EXAMPLES} == {
        "bible_deep_dive",
        "creative_development",
        "deep_reading",
        "financial_runway",
        "french_conversation",
        "leadership_reflection",
        "marathon_training",
        "reflective_journaling",
        "startup_mentor",
        "systems_thinking",
    }


def test_all_example_coaches_validate() -> None:
    assert EXAMPLES

    for path in EXAMPLES:
        spec = load_coachspec(path)
        assert isinstance(spec, CoachSpec), path
        assert spec.coach.id
        assert spec.purpose.summary
        assert spec.identity.role


def test_all_example_coaches_compile() -> None:
    for path in EXAMPLES:
        spec = load_coachspec(path)
        compiled = compile_prompt(spec)

        assert compiled.coach_id == spec.coach.id
        assert "# Coach Identity" in compiled.text
        assert spec.coach.name in compiled.text
        assert spec.identity.role in compiled.text
