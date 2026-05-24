from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfigurationError(RuntimeError):
    """Provider-neutral error for recoverable adapter configuration failures."""

    code: str
    message: str
    provider: str | None = None
    recoverable: bool = True

    def __post_init__(self) -> None:
        RuntimeError.__init__(self, self.message)

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "provider": self.provider,
            "recoverable": self.recoverable,
        }
