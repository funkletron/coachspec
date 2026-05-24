from __future__ import annotations

from dataclasses import dataclass

from coachspec.composition.strategies import (
    ExecutionStrategy,
    StrategyRegistry,
    default_strategy_registry,
)
from coachspec.modules import BehavioralModule, ModuleRegistry, default_registry
from coachspec.schema import CoachSpec


@dataclass(frozen=True)
class CoachComposition:
    """Declarative cognitive composition for a coach."""

    coach_id: str
    identity: str
    pedagogy: str
    behavioral_modules: tuple[BehavioralModule, ...]
    execution_strategy: ExecutionStrategy

    @classmethod
    def from_spec(
        cls,
        spec: CoachSpec,
        module_registry: ModuleRegistry = default_registry,
        strategy_registry: StrategyRegistry = default_strategy_registry,
    ) -> CoachComposition:
        module_ids = infer_module_ids(spec)
        strategy_id = infer_strategy_id(spec)
        return cls(
            coach_id=spec.coach.id,
            identity=spec.identity.role,
            pedagogy=spec.pedagogy.approach,
            behavioral_modules=tuple(module_registry.require(module_id) for module_id in module_ids),
            execution_strategy=strategy_registry.require(strategy_id),
        )

    def validate(self) -> None:
        if not self.coach_id.strip():
            raise ValueError("coach_id is required")
        if not self.identity.strip():
            raise ValueError("identity is required")
        if not self.pedagogy.strip():
            raise ValueError("pedagogy is required")
        if not self.execution_strategy.id.strip():
            raise ValueError("execution_strategy id is required")

        module_ids = [module.id for module in self.behavioral_modules]
        if len(module_ids) != len(set(module_ids)):
            raise ValueError("behavioral module ids must be unique")

    def module_ids(self) -> tuple[str, ...]:
        return tuple(module.id for module in self.behavioral_modules)


def infer_module_ids(spec: CoachSpec) -> tuple[str, ...]:
    text = _composition_text(spec)
    candidates: list[tuple[str, tuple[str, ...]]] = [
        ("socratic_questioning", ("socratic", "question")),
        ("reflective_listening", ("reflective", "reflection", "mirror")),
        ("progressive_curriculum", ("curriculum", "progressive", "scaffold", "learning path")),
        ("accountability_checkin", ("accountability", "commitment", "check-in", "progress")),
        ("contextual_explanation", ("context", "contextual", "background")),
        ("deliberate_practice", ("practice", "repetition", "feedback")),
        ("habit_formation", ("habit", "routine", "cue")),
        ("decision_framing", ("decision", "tradeoff", "option")),
        ("spiritual_reflection", ("bible", "spiritual", "theological", "pastoral")),
        ("evidence_based_feedback", ("evidence", "criteria", "observable")),
    ]
    module_ids = [module_id for module_id, keywords in candidates if any(keyword in text for keyword in keywords)]
    return tuple(dict.fromkeys(module_ids))


def infer_strategy_id(spec: CoachSpec) -> str:
    text = _composition_text(spec)
    if "socratic" in text or "question" in text:
        return "socratic_loop"
    if "curriculum" in text or "scaffold" in text or "learning path" in text:
        return "curriculum_progression"
    if "accountability" in text or "commitment" in text or "check-in" in text:
        return "accountability_cycle"
    if "reflect" in text:
        return "reflective_cycle"
    return "sequential_guidance"


def _composition_text(spec: CoachSpec) -> str:
    parts = [
        spec.coach.name,
        spec.coach.description or "",
        spec.coach.domain or "",
        spec.identity.role,
        spec.identity.persona or "",
        spec.interaction.style,
        spec.interaction.tone or "",
        spec.pedagogy.approach,
        *spec.coach.tags,
        *spec.identity.principles,
        *spec.interaction.turn_guidelines,
        *spec.pedagogy.methods,
        *spec.pedagogy.scaffolding,
        *spec.evaluation.criteria,
        *spec.evaluation.success_signals,
    ]
    return " ".join(parts).lower()
