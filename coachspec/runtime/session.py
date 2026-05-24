from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from coachspec.adapters import BaseProviderAdapter, ProviderRequest
from coachspec.composition import CoachComposition, ExecutionStrategy
from coachspec.compiler import CompiledPrompt, compile_prompt
from coachspec.memory import BaseMemory, InMemoryConversationMemory, SessionMemorySnapshot, utc_now
from coachspec.runtime.events import (
    AssistantMessageGenerated,
    InMemoryEventCollector,
    MemoryRead,
    MemoryWritten,
    RuntimeEvent,
    SessionEnded,
    SessionStarted,
    UserMessageReceived,
)
from coachspec.schema import CoachSpec, load_coachspec


@dataclass
class SessionState:
    session_id: str
    coach_id: str
    turn_count: int = 0
    is_active: bool = True
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    closed_at: datetime | None = None


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
    provider_adapter: BaseProviderAdapter | None = None
    event_collector: InMemoryEventCollector = field(default_factory=InMemoryEventCollector)
    state: SessionState = field(init=False)

    def __post_init__(self) -> None:
        self.state = SessionState(session_id=str(uuid4()), coach_id=self.spec.coach.id)
        self._emit(
            SessionStarted,
            {
                "coach_name": self.spec.coach.name,
                "execution_strategy": self.composition.execution_strategy.id,
            },
        )

    @classmethod
    def from_spec(
        cls,
        spec: CoachSpec,
        memory: BaseMemory | None = None,
        provider_adapter: BaseProviderAdapter | None = None,
        event_collector: InMemoryEventCollector | None = None,
    ) -> CoachSession:
        composition = CoachComposition.from_spec(spec)
        return cls(
            spec=spec,
            composition=composition,
            compiled_prompt=compile_prompt(spec, composition=composition),
            memory=memory or InMemoryConversationMemory(),
            provider_adapter=provider_adapter,
            event_collector=event_collector or InMemoryEventCollector(),
        )

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        memory: BaseMemory | None = None,
        provider_adapter: BaseProviderAdapter | None = None,
    ) -> CoachSession:
        return cls.from_spec(
            load_coachspec(path),
            memory=memory,
            provider_adapter=provider_adapter,
        )

    @classmethod
    def from_persisted_state(
        cls,
        spec: CoachSpec,
        state: SessionState,
        memory_snapshot: SessionMemorySnapshot,
        provider_adapter: BaseProviderAdapter | None = None,
        events: tuple[RuntimeEvent, ...] | None = None,
    ) -> CoachSession:
        session = cls.from_spec(
            spec,
            memory=InMemoryConversationMemory.from_snapshot(memory_snapshot),
            provider_adapter=provider_adapter,
        )
        session.state = state
        if events is not None:
            session.event_collector = InMemoryEventCollector(events)
        return session

    def context(self) -> RuntimeContext:
        snapshot = self.memory.snapshot()
        self._emit(MemoryRead, {"message_count": snapshot.message_count, "source": "context"})
        return RuntimeContext(
            coach_id=self.spec.coach.id,
            coach_name=self.spec.coach.name,
            session_id=self.state.session_id,
            execution_strategy=self.composition.execution_strategy,
            compiled_prompt=self.compiled_prompt,
            memory_snapshot=snapshot,
        )

    def append_user_message(self, content: str) -> None:
        self._emit(UserMessageReceived, {"content": content})
        message = self.memory.append("user", content)
        self.state.turn_count += 1
        self.state.updated_at = utc_now()
        self._emit(
            MemoryWritten,
            {
                "role": message.role,
                "content": message.content,
                "message_created_at": message.created_at.isoformat(),
            },
        )

    def append_assistant_message(self, content: str) -> None:
        self._emit(AssistantMessageGenerated, {"content": content})
        message = self.memory.append("assistant", content)
        self.state.updated_at = utc_now()
        self._emit(
            MemoryWritten,
            {
                "role": message.role,
                "content": message.content,
                "message_created_at": message.created_at.isoformat(),
            },
        )

    def build_provider_request(self, user_input: str) -> ProviderRequest:
        snapshot = self.memory.snapshot()
        self._emit(MemoryRead, {"message_count": snapshot.message_count, "source": "provider_request"})
        return ProviderRequest(
            coach_id=self.spec.coach.id,
            coach_name=self.spec.coach.name,
            session_id=self.state.session_id,
            instructions=self.compiled_prompt.text,
            user_input=user_input,
            execution_strategy=self.composition.execution_strategy,
            memory_snapshot=snapshot,
        )

    def respond(self, user_input: str) -> str:
        self.append_user_message(user_input)
        if self.provider_adapter is not None:
            request = self.build_provider_request(user_input)
            provider_response = self.provider_adapter.generate(request)
            self.append_assistant_message(provider_response.content)
            return provider_response.content

        response = (
            "Runtime is initialized and memory recorded your message. "
            "No model provider is configured yet."
        )
        self.append_assistant_message(response)
        return response

    def respond_stub(self, user_input: str) -> str:
        return self.respond(user_input)

    def close(self) -> None:
        self.state.is_active = False
        self.state.updated_at = utc_now()
        self.state.closed_at = self.state.updated_at
        self._emit(SessionEnded, {"closed_at": self.state.closed_at.isoformat()})

    def events(self) -> tuple[RuntimeEvent, ...]:
        return self.event_collector.snapshot()

    def _emit(self, event_class: type[RuntimeEvent], payload: dict[str, object]) -> RuntimeEvent:
        return self.event_collector.emit(
            event_class,
            session_id=self.state.session_id,
            coach_id=self.state.coach_id,
            payload=payload,
        )
