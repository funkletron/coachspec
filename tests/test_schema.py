from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from coachspec.schema import CoachSpec, load_coachspec, validate_coachspec


ROOT = Path(__file__).resolve().parents[1]


def test_loads_valid_example_coach() -> None:
    spec = load_coachspec(ROOT / "coaches" / "spirituality" / "bible_deep_dive.yaml")

    assert isinstance(spec, CoachSpec)
    assert spec.coach.id == "bible-deep-dive"
    assert spec.memory.mode == "session"
    assert "guided_questions" in spec.outputs.formats


def test_validate_coachspec_returns_errors_for_missing_section(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text(
        """
coach:
  id: incomplete
  name: Incomplete
  version: 0.1.0
purpose:
  summary: Missing required top-level sections.
""",
        encoding="utf-8",
    )

    spec, errors = validate_coachspec(invalid)

    assert spec is None
    assert errors
    assert any("identity" in error for error in errors)


def test_rejects_unknown_top_level_section() -> None:
    data = {
        "coach": {"id": "x", "name": "X", "version": "0.1.0"},
        "purpose": {"summary": "A purpose."},
        "identity": {"role": "Coach"},
        "interaction": {"style": "Direct"},
        "pedagogy": {"approach": "Guided"},
        "memory": {"mode": "none"},
        "constraints": {},
        "outputs": {},
        "evaluation": {},
        "provider": {"name": "not allowed"},
    }

    with pytest.raises(ValidationError):
        CoachSpec.model_validate(data)


def test_rejects_invalid_memory_mode() -> None:
    data = {
        "coach": {"id": "x", "name": "X", "version": "0.1.0"},
        "purpose": {"summary": "A purpose."},
        "identity": {"role": "Coach"},
        "interaction": {"style": "Direct"},
        "pedagogy": {"approach": "Guided"},
        "memory": {"mode": "forever"},
        "constraints": {},
        "outputs": {},
        "evaluation": {},
    }

    with pytest.raises(ValidationError):
        CoachSpec.model_validate(data)


def test_validate_coachspec_reports_non_mapping_section(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid-section.yaml"
    invalid.write_text(
        """
coach:
  id: malformed
  name: Malformed
  version: 0.1.0
purpose: []
identity:
  role: Coach
interaction:
  style: Direct
pedagogy:
  approach: Guided
memory: {}
constraints: {}
outputs: {}
evaluation: {}
""",
        encoding="utf-8",
    )

    spec, errors = validate_coachspec(invalid)

    assert spec is None
    assert any("purpose" in error and "section must be a mapping" in error for error in errors)
