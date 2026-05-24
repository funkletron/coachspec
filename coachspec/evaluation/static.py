from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from coachspec.schema import CoachSpec


@dataclass(frozen=True)
class EvaluationCriterion:
    id: str
    name: str
    description: str


@dataclass(frozen=True)
class EvaluationResult:
    criterion: EvaluationCriterion
    score: float
    strengths: tuple[str, ...] = ()
    suggestions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0")


@dataclass(frozen=True)
class CoachEvaluationReport:
    coach_id: str
    overall_score: float
    results: tuple[EvaluationResult, ...]

    @property
    def strengths(self) -> tuple[str, ...]:
        return tuple(strength for result in self.results for strength in result.strengths)

    @property
    def suggestions(self) -> tuple[str, ...]:
        return tuple(suggestion for result in self.results for suggestion in result.suggestions)


StaticEvaluator = Callable[[CoachSpec], EvaluationResult]


SCHEMA_COMPLETENESS = EvaluationCriterion(
    id="schema_completeness",
    name="Schema Completeness",
    description="Checks that every core CoachSpec section has meaningful content.",
)
PURPOSE_CLARITY = EvaluationCriterion(
    id="purpose_clarity",
    name="Purpose Clarity",
    description="Checks whether purpose, goals, and non-goals are explicit.",
)
IDENTITY_CLARITY = EvaluationCriterion(
    id="identity_clarity",
    name="Identity Clarity",
    description="Checks whether role, persona, principles, and boundaries are clear.",
)
PEDAGOGY_SPECIFICITY = EvaluationCriterion(
    id="pedagogy_specificity",
    name="Pedagogy Specificity",
    description="Checks whether coaching methods and scaffolding are specific.",
)
CONSTRAINT_COVERAGE = EvaluationCriterion(
    id="constraint_coverage",
    name="Constraint Coverage",
    description="Checks whether rules, refusals, and escalation guidance are declared.",
)
OUTPUT_STRUCTURE_CLARITY = EvaluationCriterion(
    id="output_structure_clarity",
    name="Output Structure Clarity",
    description="Checks whether expected response formats and artifacts are specified.",
)
MEMORY_CLARITY = EvaluationCriterion(
    id="memory_clarity",
    name="Memory Clarity",
    description="Checks whether memory mode, stores, retention, and consent are clear.",
)


def evaluate_coachspec(spec: CoachSpec) -> CoachEvaluationReport:
    results = tuple(evaluator(spec) for evaluator in STATIC_EVALUATORS)
    overall_score = _round_score(sum(result.score for result in results) / len(results))
    return CoachEvaluationReport(
        coach_id=spec.coach.id,
        overall_score=overall_score,
        results=results,
    )


def evaluate_schema_completeness(spec: CoachSpec) -> EvaluationResult:
    checks = [
        bool(spec.coach.id and spec.coach.name and spec.coach.version),
        _has_text(spec.purpose.summary),
        _has_text(spec.identity.role),
        _has_text(spec.interaction.style),
        _has_text(spec.pedagogy.approach),
        _has_text(spec.memory.mode),
        _has_any(spec.constraints.rules, spec.constraints.refusals, spec.constraints.escalation),
        _has_any(spec.outputs.formats, spec.outputs.artifacts) or _has_text(spec.outputs.default_format),
        _has_any(spec.evaluation.criteria, spec.evaluation.success_signals, spec.evaluation.failure_modes),
    ]
    score = _ratio(checks)
    return _result(
        SCHEMA_COMPLETENESS,
        score,
        "Core sections are present with meaningful content.",
        "Add more detail to sparse sections so the compiled coach has a stronger contract.",
    )


def evaluate_purpose_clarity(spec: CoachSpec) -> EvaluationResult:
    checks = [
        _word_count(spec.purpose.summary) >= 8,
        len(spec.purpose.goals) >= 2,
        len(spec.purpose.non_goals) >= 1,
    ]
    score = _ratio(checks)
    return _result(
        PURPOSE_CLARITY,
        score,
        "Purpose includes a clear summary, goals, and boundaries of scope.",
        "Clarify the purpose with a specific summary, at least two goals, and explicit non-goals.",
    )


def evaluate_identity_clarity(spec: CoachSpec) -> EvaluationResult:
    checks = [
        _word_count(spec.identity.role) >= 3,
        _word_count(spec.identity.persona) >= 5,
        len(spec.identity.principles) >= 2,
        len(spec.identity.boundaries) >= 1,
    ]
    score = _ratio(checks)
    return _result(
        IDENTITY_CLARITY,
        score,
        "Identity defines role, persona, operating principles, and boundaries.",
        "Strengthen identity with a richer role, persona, principles, and boundaries.",
    )


def evaluate_pedagogy_specificity(spec: CoachSpec) -> EvaluationResult:
    checks = [
        _word_count(spec.pedagogy.approach) >= 3,
        len(spec.pedagogy.methods) >= 2,
        len(spec.pedagogy.scaffolding) >= 2,
    ]
    score = _ratio(checks)
    return _result(
        PEDAGOGY_SPECIFICITY,
        score,
        "Pedagogy names concrete methods and scaffolding steps.",
        "Add concrete methods and staged scaffolding so the coaching approach is inspectable.",
    )


def evaluate_constraint_coverage(spec: CoachSpec) -> EvaluationResult:
    checks = [
        len(spec.constraints.rules) >= 2,
        len(spec.constraints.refusals) >= 1,
        len(spec.constraints.escalation) >= 1,
    ]
    score = _ratio(checks)
    return _result(
        CONSTRAINT_COVERAGE,
        score,
        "Constraints include behavioral rules, refusals, and escalation guidance.",
        "Add rules, refusal boundaries, and escalation guidance for safer coach behavior.",
    )


def evaluate_output_structure_clarity(spec: CoachSpec) -> EvaluationResult:
    checks = [
        _has_text(spec.outputs.default_format),
        len(spec.outputs.formats) >= 2,
        len(spec.outputs.artifacts) >= 1,
    ]
    score = _ratio(checks)
    return _result(
        OUTPUT_STRUCTURE_CLARITY,
        score,
        "Outputs define formats, artifacts, and a default response structure.",
        "Declare expected formats, artifacts, and a default output structure.",
    )


def evaluate_memory_clarity(spec: CoachSpec) -> EvaluationResult:
    checks = [
        _has_text(spec.memory.mode),
        spec.memory.mode == "none" or len(spec.memory.stores) >= 1,
        spec.memory.mode == "none" or _has_text(spec.memory.retention),
        isinstance(spec.memory.consent_required, bool),
    ]
    score = _ratio(checks)
    return _result(
        MEMORY_CLARITY,
        score,
        "Memory behavior declares mode, stores, retention, and consent expectations.",
        "Clarify memory stores and retention, or set memory mode to none if memory is not needed.",
    )


STATIC_EVALUATORS: tuple[StaticEvaluator, ...] = (
    evaluate_schema_completeness,
    evaluate_purpose_clarity,
    evaluate_identity_clarity,
    evaluate_pedagogy_specificity,
    evaluate_constraint_coverage,
    evaluate_output_structure_clarity,
    evaluate_memory_clarity,
)


def _result(
    criterion: EvaluationCriterion,
    score: float,
    strength: str,
    suggestion: str,
) -> EvaluationResult:
    rounded = _round_score(score)
    return EvaluationResult(
        criterion=criterion,
        score=rounded,
        strengths=(strength,) if rounded >= 0.75 else (),
        suggestions=(suggestion,) if rounded < 1.0 else (),
    )


def _ratio(checks: list[bool]) -> float:
    return sum(1 for check in checks if check) / len(checks)


def _round_score(score: float) -> float:
    return round(score, 2)


def _has_text(value: str | None) -> bool:
    return bool(value and value.strip())


def _has_any(*items: list[str]) -> bool:
    return any(item.strip() for values in items for item in values)


def _word_count(value: str | None) -> int:
    if value is None:
        return 0
    return len(value.split())
