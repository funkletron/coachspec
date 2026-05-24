from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from coachspec.cli import app
from coachspec.compiler import CompiledPrompt, compile_prompt
from coachspec.schema import load_coachspec


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "coaches" / "spirituality" / "bible_deep_dive.yaml"


def test_compile_prompt_returns_deterministic_text() -> None:
    spec = load_coachspec(EXAMPLE)

    first = compile_prompt(spec)
    second = compile_prompt(spec)

    assert isinstance(first, CompiledPrompt)
    assert first == second
    assert first.coach_id == "bible-deep-dive"
    assert first.text.endswith("\n")


def test_compile_prompt_includes_core_sections() -> None:
    spec = load_coachspec(EXAMPLE)
    prompt = compile_prompt(spec).text

    assert "# Coach Identity" in prompt
    assert "Name: Bible Deep Dive Coach" in prompt
    assert "Role: Reflective Bible study coach" in prompt
    assert "# Purpose" in prompt
    assert "Help users examine biblical passages" in prompt
    assert "# Interaction Model" in prompt
    assert "Style: Socratic and structured" in prompt
    assert "# Pedagogy" in prompt
    assert "Approach: Guided close reading" in prompt
    assert "# Memory Behavior" in prompt
    assert "Mode: session" in prompt
    assert "# Constraints" in prompt
    assert "- Avoid presenting disputed theological claims as settled fact." in prompt
    assert "# Output Expectations" in prompt
    assert "Default format: guided_questions" in prompt


def test_cli_compile_prints_compiled_prompt() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["compile", str(EXAMPLE)])

    assert result.exit_code == 0
    assert "# Coach Identity" in result.stdout
    assert "Bible Deep Dive Coach" in result.stdout
    assert "Guided close reading" in result.stdout
