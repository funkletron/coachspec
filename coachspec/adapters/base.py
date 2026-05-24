from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from coachspec.composition import ExecutionStrategy
from coachspec.memory import SessionMemorySnapshot


@dataclass(frozen=True)
class ProviderRequest:
    coach_id: str
    coach_name: str
    session_id: str
    instructions: str
    user_input: str
    execution_strategy: ExecutionStrategy
    memory_snapshot: SessionMemorySnapshot


@dataclass(frozen=True)
class ProviderResponse:
    content: str
    provider: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseProviderAdapter(ABC):
    provider_name: str

    @abstractmethod
    def generate(self, request: ProviderRequest) -> ProviderResponse:
        """Return a normalized assistant response for a provider-neutral request."""
