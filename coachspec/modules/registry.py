from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BehavioralModule:
    """A reusable, declarative coaching behavior."""

    id: str
    name: str
    description: str


class ModuleRegistry:
    def __init__(self, modules: list[BehavioralModule] | tuple[BehavioralModule, ...]) -> None:
        ids = [module.id for module in modules]
        duplicates = sorted({module_id for module_id in ids if ids.count(module_id) > 1})
        if duplicates:
            duplicate_list = ", ".join(duplicates)
            raise ValueError(f"duplicate module id(s): {duplicate_list}")

        self._modules = tuple(modules)
        self._by_id = {module.id: module for module in self._modules}

    def all(self) -> tuple[BehavioralModule, ...]:
        return self._modules

    def get(self, module_id: str) -> BehavioralModule | None:
        return self._by_id.get(module_id)

    def require(self, module_id: str) -> BehavioralModule:
        module = self.get(module_id)
        if module is None:
            raise KeyError(module_id)
        return module

    def ids(self) -> tuple[str, ...]:
        return tuple(module.id for module in self._modules)


DEFAULT_MODULES: tuple[BehavioralModule, ...] = (
    BehavioralModule(
        id="socratic_questioning",
        name="Socratic Questioning",
        description="Uses sequenced questions to help the learner examine assumptions, evidence, and implications.",
    ),
    BehavioralModule(
        id="reflective_listening",
        name="Reflective Listening",
        description="Mirrors user intent and emotion before offering guidance, correction, or next steps.",
    ),
    BehavioralModule(
        id="progressive_curriculum",
        name="Progressive Curriculum",
        description="Structures coaching as an ordered path from fundamentals to increasingly complex practice.",
    ),
    BehavioralModule(
        id="accountability_checkin",
        name="Accountability Check-in",
        description="Reviews commitments, progress, blockers, and next actions across coaching sessions.",
    ),
    BehavioralModule(
        id="contextual_explanation",
        name="Contextual Explanation",
        description="Adapts explanations to the user's current context, background, vocabulary, and goals.",
    ),
    BehavioralModule(
        id="deliberate_practice",
        name="Deliberate Practice",
        description="Creates focused practice loops with clear targets, feedback, repetition, and increasing challenge.",
    ),
    BehavioralModule(
        id="habit_formation",
        name="Habit Formation",
        description="Helps users define cues, routines, rewards, friction, and review rhythms for behavior change.",
    ),
    BehavioralModule(
        id="decision_framing",
        name="Decision Framing",
        description="Clarifies options, criteria, tradeoffs, risks, and reversible versus irreversible choices.",
    ),
    BehavioralModule(
        id="spiritual_reflection",
        name="Spiritual Reflection",
        description="Supports reflective engagement with beliefs, values, practices, texts, and lived commitments.",
    ),
    BehavioralModule(
        id="evidence_based_feedback",
        name="Evidence-based Feedback",
        description="Grounds feedback in observable behavior, stated goals, explicit criteria, and concrete examples.",
    ),
)


default_registry = ModuleRegistry(DEFAULT_MODULES)
