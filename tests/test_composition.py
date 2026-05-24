from __future__ import annotations

from pathlib import Path

import pytest

from coachspec.composition import CoachComposition, ExecutionStrategy, StrategyRegistry
from coachspec.composition.strategies import default_strategy_registry
from coachspec.schema import load_coachspec


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "coaches" / "spirituality" / "bible_deep_dive.yaml"


def test_strategy_registry_loads_known_strategies() -> None:
    assert default_strategy_registry.get("sequential_guidance") is not None
    assert default_strategy_registry.get("socratic_loop") is not None
    assert default_strategy_registry.get("accountability_cycle") is not None


def test_strategy_registry_rejects_duplicate_ids() -> None:
    strategy = ExecutionStrategy(id="same", name="Same", summary="A strategy.")

    with pytest.raises(ValueError, match="duplicate strategy"):
        StrategyRegistry([strategy, strategy])


def test_composition_from_spec_validates() -> None:
    spec = load_coachspec(EXAMPLE)

    composition = CoachComposition.from_spec(spec)
    composition.validate()

    assert composition.coach_id == "bible-deep-dive"
    assert composition.execution_strategy.id == "socratic_loop"
    assert "socratic_questioning" in composition.module_ids()
    assert "spiritual_reflection" in composition.module_ids()
