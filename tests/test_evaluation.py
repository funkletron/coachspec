from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from coachspec.cli import app
from coachspec.evaluation import CoachEvaluationReport, EvaluationResult, evaluate_coachspec
from coachspec.schema import CoachSpec, load_coachspec


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "coaches" / "spirituality" / "bible_deep_dive.yaml"


def test_evaluation_report_creation() -> None:
    spec = load_coachspec(EXAMPLE)

    report = evaluate_coachspec(spec)

    assert isinstance(report, CoachEvaluationReport)
    assert report.coach_id == "bible-deep-dive"
    assert report.results
    assert all(isinstance(result, EvaluationResult) for result in report.results)


def test_evaluation_scores_are_in_range() -> None:
    spec = load_coachspec(EXAMPLE)
    report = evaluate_coachspec(spec)

    assert 0.0 <= report.overall_score <= 1.0
    for result in report.results:
        assert 0.0 <= result.score <= 1.0


def test_valid_coach_evaluation_scores_highly() -> None:
    spec = load_coachspec(EXAMPLE)

    report = evaluate_coachspec(spec)

    assert report.overall_score >= 0.75
    assert report.strengths


def test_weak_minimal_coach_evaluation_scores_lower() -> None:
    weak = CoachSpec.model_validate(
        {
            "coach": {"id": "weak", "name": "Weak", "version": "0.1.0"},
            "purpose": {"summary": "Help."},
            "identity": {"role": "Coach"},
            "interaction": {"style": "Direct"},
            "pedagogy": {"approach": "Guided"},
            "memory": {"mode": "session"},
            "constraints": {},
            "outputs": {},
            "evaluation": {},
        }
    )

    report = evaluate_coachspec(weak)

    assert report.overall_score < 0.5
    assert report.suggestions


def test_cli_evaluate_prints_report() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["evaluate", str(EXAMPLE)])

    assert result.exit_code == 0
    assert "CoachSpec Evaluation" in result.stdout
    assert "Overall score:" in result.stdout
    assert "Criteria:" in result.stdout
    assert "Strengths:" in result.stdout
    assert "Improvement suggestions:" in result.stdout
