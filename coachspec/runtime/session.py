from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from coachspec.composition import CoachComposition, ExecutionStrategy
from coachspec.compiler import CompiledPrompt, compile_prompt
from coachspec.memory import BaseMemory, InMemoryConversationMemory, SessionMemorySnapshot
from coachspec.schema import CoachSpec, load_coachspec


@dataclass
class SessionState:
    session_id: str
    coach_id: str
    turn_count: int = 0
    is_active: bool = True


@dataclass(frozen=True)
class RuntimeContext:
    coach_id: str
    coach_name: str
    session_id: str
    execution_strategy: ExecutionStrategy
    compiled_prompt: CompiledPrompt
    memory_snapshot: SessionMemorySnapshot


@dataclass
class CoachSession:
    spec: CoachSpec
    composition: CoachComposition
    compiled_prompt: CompiledPrompt
    memory: BaseMemory = field(default_factory=InMemoryConversationMemory)
    state: SessionState = field(init=False)

    def __post_init__(self) -> None:
        self.state = SessionState(session_id=str(uuid4()), coach_id=self.spec.coach.id)

    @classmethod
    def from_spec(
        cls,
        spec: CoachSpec,
        memory: BaseMemory | None = None,
    ) -> CoachSession:
        composition = CoachComposition.from_spec(spec)
        return cls(
            spec=spec,
            composition=composition,
            compiled_prompt=compile_prompt(spec, composition=composition),
            memory=memory or InMemoryConversationMemory(),
        )

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        memory: BaseMemory | None = None,
    ) -> CoachSession:
        return cls.from_spec(load_coachspec(path), memory=memory)

    def context(self) -> RuntimeContext:
        return RuntimeContext(
            coach_id=self.spec.coach.id,
            coach_name=self.spec.coach.name,
            session_id=self.state.session_id,
            execution_strategy=self.composition.execution_strategy,
            compiled_prompt=self.compiled_prompt,
            memory_snapshot=self.memory.snapshot(),
        )

    def append_user_message(self, content: str) -> None:
        self.memory.append("user", content)
        self.state.turn_count += 1

    def append_assistant_message(self, content: str) -> None:
        self.memory.append("assistant", content)

    def respond_stub(self, user_input: str) -> str:
        self.append_user_message(user_input)
        response = (
            "Runtime is initialized and memory recorded your message. "
            "No model provider is configured yet."
        )
        self.append_assistant_message(response)
        return response

    def close(self) -> None:
        self.state.is_active = False
