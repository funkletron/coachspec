from __future__ import annotations

import os
from typing import Any

from coachspec.adapters.base import BaseProviderAdapter, ProviderRequest, ProviderResponse


class OpenAIProviderConfigurationError(RuntimeError):
    """Raised when the optional OpenAI provider adapter cannot be configured."""


class OpenAIProviderResponseError(RuntimeError):
    """Raised when OpenAI returns a response CoachSpec cannot normalize."""


class OpenAIProviderAdapter(BaseProviderAdapter):
    provider_name = "openai"
    default_model = "gpt-4o-mini"

    def __init__(self, model: str = default_model, client: Any | None = None) -> None:
        self.model = model
        self._client = client or self._build_client()

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=self._messages_from_request(request),
        )
        choice = _first_choice(response)
        content = _choice_content(choice)

        return ProviderResponse(
            content=content,
            provider=self.provider_name,
            metadata={
                "coach_id": request.coach_id,
                "session_id": request.session_id,
                "model": self.model,
                "response_id": getattr(response, "id", None),
                "finish_reason": getattr(choice, "finish_reason", None),
            },
        )

    def _build_client(self) -> Any:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise OpenAIProviderConfigurationError(
                "OpenAI provider requires OPENAI_API_KEY to be set in the environment."
            )

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise OpenAIProviderConfigurationError(
                "OpenAI provider requires the optional 'openai' package. "
                "Install it with `uv sync --extra openai`."
            ) from exc

        return OpenAI(api_key=api_key)

    def _messages_from_request(self, request: ProviderRequest) -> list[dict[str, str]]:
        messages = [{"role": "system", "content": request.instructions}]
        messages.extend(
            {"role": message.role, "content": message.content}
            for message in request.memory_snapshot.messages
        )
        return messages


def _first_choice(response: Any) -> Any:
    choices = getattr(response, "choices", None)
    if not choices:
        raise OpenAIProviderResponseError("OpenAI response did not include any choices.")
    return choices[0]


def _choice_content(choice: Any) -> str:
    message = getattr(choice, "message", None)
    content = getattr(message, "content", None)

    if isinstance(content, str) and content:
        return content

    if isinstance(content, list):
        text = "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )
        if text:
            return text

    raise OpenAIProviderResponseError("OpenAI response did not include assistant content.")
