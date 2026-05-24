from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CoachSection(StrictModel):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    description: str | None = None
    domain: str | None = None
    tags: list[str] = Field(default_factory=list)


class PurposeSection(StrictModel):
    summary: str = Field(..., min_length=1)
    goals: list[str] = Field(default_factory=list)
    non_goals: list[str] = Field(default_factory=list)


class IdentitySection(StrictModel):
    role: str = Field(..., min_length=1)
    persona: str | None = None
    principles: list[str] = Field(default_factory=list)
    boundaries: list[str] = Field(default_factory=list)


class InteractionSection(StrictModel):
    style: str = Field(..., min_length=1)
    tone: str | None = None
    asks_questions: bool = True
    adapts_to_user: bool = True
    turn_guidelines: list[str] = Field(default_factory=list)


class PedagogySection(StrictModel):
    approach: str = Field(..., min_length=1)
    methods: list[str] = Field(default_factory=list)
    scaffolding: list[str] = Field(default_factory=list)


class MemorySection(StrictModel):
    mode: Literal["none", "session", "persistent"] = "session"
    stores: list[str] = Field(default_factory=list)
    retention: str | None = None
    consent_required: bool = True


class ConstraintsSection(StrictModel):
    rules: list[str] = Field(default_factory=list)
    refusals: list[str] = Field(default_factory=list)
    escalation: list[str] = Field(default_factory=list)


class OutputsSection(StrictModel):
    formats: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
    default_format: str | None = None


class EvaluationSection(StrictModel):
    criteria: list[str] = Field(default_factory=list)
    success_signals: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CoachSpec(StrictModel):
    coach: CoachSection
    purpose: PurposeSection
    identity: IdentitySection
    interaction: InteractionSection
    pedagogy: PedagogySection
    memory: MemorySection
    constraints: ConstraintsSection
    outputs: OutputsSection
    evaluation: EvaluationSection

    @field_validator(
        "coach",
        "purpose",
        "identity",
        "interaction",
        "pedagogy",
        "memory",
        "constraints",
        "outputs",
        "evaluation",
        mode="before",
    )
    @classmethod
    def require_mapping(cls, value: object) -> object:
        if not isinstance(value, dict):
            raise ValueError("section must be a mapping")
        return value
