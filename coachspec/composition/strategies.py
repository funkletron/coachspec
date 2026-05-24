from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExecutionStrategy:
    """A declarative turn-shaping strategy for a coach."""

    id: str
    name: str
    summary: str


class StrategyRegistry:
    def __init__(self, strategies: list[ExecutionStrategy] | tuple[ExecutionStrategy, ...]) -> None:
        ids = [strategy.id for strategy in strategies]
        duplicates = sorted({strategy_id for strategy_id in ids if ids.count(strategy_id) > 1})
        if duplicates:
            duplicate_list = ", ".join(duplicates)
            raise ValueError(f"duplicate strategy id(s): {duplicate_list}")

        self._strategies = tuple(strategies)
        self._by_id = {strategy.id: strategy for strategy in self._strategies}

    def all(self) -> tuple[ExecutionStrategy, ...]:
        return self._strategies

    def get(self, strategy_id: str) -> ExecutionStrategy | None:
        return self._by_id.get(strategy_id)

    def require(self, strategy_id: str) -> ExecutionStrategy:
        strategy = self.get(strategy_id)
        if strategy is None:
            raise KeyError(strategy_id)
        return strategy

    def ids(self) -> tuple[str, ...]:
        return tuple(strategy.id for strategy in self._strategies)


DEFAULT_STRATEGIES: tuple[ExecutionStrategy, ...] = (
    ExecutionStrategy(
        id="sequential_guidance",
        name="Sequential Guidance",
        summary="Moves through a clear sequence of explanation, user response, and next-step guidance.",
    ),
    ExecutionStrategy(
        id="socratic_loop",
        name="Socratic Loop",
        summary="Cycles through question, reflection, clarification, and deeper question before offering conclusions.",
    ),
    ExecutionStrategy(
        id="reflective_cycle",
        name="Reflective Cycle",
        summary="Mirrors the user's context, identifies meaning, and guides the next reflective action.",
    ),
    ExecutionStrategy(
        id="curriculum_progression",
        name="Curriculum Progression",
        summary="Advances through ordered learning stages with review, practice, and increasing complexity.",
    ),
    ExecutionStrategy(
        id="accountability_cycle",
        name="Accountability Cycle",
        summary="Reviews commitments, checks progress, identifies blockers, and confirms the next commitment.",
    ),
)


default_strategy_registry = StrategyRegistry(DEFAULT_STRATEGIES)
