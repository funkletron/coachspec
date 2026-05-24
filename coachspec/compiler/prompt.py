from __future__ import annotations

from dataclasses import dataclass

from coachspec.composition import CoachComposition
from coachspec.schema import CoachSpec


@dataclass(frozen=True)
class CompiledPrompt:
    coach_id: str
    text: str


def compile_prompt(
    spec: CoachSpec,
    composition: CoachComposition | None = None,
) -> CompiledPrompt:
    """Compile a validated CoachSpec into deterministic coach instructions."""
    composition = composition or CoachComposition.from_spec(spec)
    composition.validate()
    sections = [
        _section(
            "Coach Identity",
            [
                ("Name", spec.coach.name),
                ("ID", spec.coach.id),
                ("Version", spec.coach.version),
                ("Domain", spec.coach.domain),
                ("Description", spec.coach.description),
                ("Tags", _inline_list(spec.coach.tags)),
                ("Role", spec.identity.role),
                ("Persona", spec.identity.persona),
                ("Principles", _bullet_list(spec.identity.principles)),
                ("Boundaries", _bullet_list(spec.identity.boundaries)),
            ],
        ),
        _section(
            "Purpose",
            [
                ("Summary", spec.purpose.summary),
                ("Goals", _bullet_list(spec.purpose.goals)),
                ("Non-goals", _bullet_list(spec.purpose.non_goals)),
            ],
        ),
        _section(
            "Interaction Model",
            [
                ("Style", spec.interaction.style),
                ("Tone", spec.interaction.tone),
                ("Asks questions", _yes_no(spec.interaction.asks_questions)),
                ("Adapts to user", _yes_no(spec.interaction.adapts_to_user)),
                ("Turn guidelines", _bullet_list(spec.interaction.turn_guidelines)),
            ],
        ),
        _section(
            "Pedagogy",
            [
                ("Approach", spec.pedagogy.approach),
                ("Methods", _bullet_list(spec.pedagogy.methods)),
                ("Scaffolding", _bullet_list(spec.pedagogy.scaffolding)),
            ],
        ),
        _section(
            "Coach Composition",
            [
                ("Identity", composition.identity),
                ("Pedagogy", composition.pedagogy),
                ("Behavioral modules", _module_list(composition)),
                ("Execution strategy", composition.execution_strategy.name),
                ("Strategy summary", composition.execution_strategy.summary),
            ],
        ),
        _section(
            "Memory Behavior",
            [
                ("Mode", spec.memory.mode),
                ("Stores", _bullet_list(spec.memory.stores)),
                ("Retention", spec.memory.retention),
                ("Consent required", _yes_no(spec.memory.consent_required)),
            ],
        ),
        _section(
            "Constraints",
            [
                ("Rules", _bullet_list(spec.constraints.rules)),
                ("Refusals", _bullet_list(spec.constraints.refusals)),
                ("Escalation", _bullet_list(spec.constraints.escalation)),
            ],
        ),
        _section(
            "Output Expectations",
            [
                ("Default format", spec.outputs.default_format),
                ("Formats", _bullet_list(spec.outputs.formats)),
                ("Artifacts", _bullet_list(spec.outputs.artifacts)),
            ],
        ),
    ]

    prompt = "\n\n".join(sections)
    return CompiledPrompt(coach_id=spec.coach.id, text=f"{prompt}\n")


def _section(title: str, fields: list[tuple[str, str | None]]) -> str:
    lines = [f"# {title}"]
    for label, value in fields:
        lines.extend(_field(label, value))
    return "\n".join(lines)


def _field(label: str, value: str | None) -> list[str]:
    if value is None or value == "":
        return [f"{label}: Not specified."]
    if value.startswith("- "):
        return [f"{label}:", value]
    if "\n" not in value:
        return [f"{label}: {value}"]
    return [f"{label}:", value]


def _bullet_list(items: list[str]) -> str:
    if not items:
        return "None declared."
    return "\n".join(f"- {item}" for item in items)


def _inline_list(items: list[str]) -> str:
    if not items:
        return "None declared."
    return ", ".join(items)


def _module_list(composition: CoachComposition) -> str:
    if not composition.behavioral_modules:
        return "None inferred."
    return "\n".join(
        f"- {module.id}: {module.description}" for module in composition.behavioral_modules
    )


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"
