from __future__ import annotations

from coachspec.adapters.base import BaseProviderAdapter, ProviderRequest, ProviderResponse


class MockProviderAdapter(BaseProviderAdapter):
    provider_name = "mock"

    def __init__(self, response_prefix: str = "Mock provider response") -> None:
        self.response_prefix = response_prefix

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        content = (
            f"{self.response_prefix} for {request.coach_name}: "
            f"received '{request.user_input}'."
        )
        return ProviderResponse(
            content=content,
            provider=self.provider_name,
            metadata={
                "coach_id": request.coach_id,
                "session_id": request.session_id,
                "turn_count": request.memory_snapshot.message_count,
            },
        )
