from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from coachspec.schema.models import CoachSpec


class CoachSpecLoadError(ValueError):
    """Raised when a CoachSpec file cannot be read or parsed as YAML."""


def load_yaml(path: str | Path) -> dict[str, Any]:
    spec_path = Path(path)

    try:
        raw = spec_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CoachSpecLoadError(f"Could not read CoachSpec file: {spec_path}") from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise CoachSpecLoadError(f"Invalid YAML in CoachSpec file: {spec_path}") from exc

    if not isinstance(data, dict):
        raise CoachSpecLoadError("CoachSpec YAML must contain a top-level mapping.")

    return data


def load_coachspec(path: str | Path) -> CoachSpec:
    return CoachSpec.model_validate(load_yaml(path))


def validate_coachspec(path: str | Path) -> tuple[CoachSpec | None, list[str]]:
    try:
        return load_coachspec(path), []
    except CoachSpecLoadError as exc:
        return None, [str(exc)]
    except ValidationError as exc:
        return None, [format_validation_error(error) for error in exc.errors()]


def format_validation_error(error: dict[str, Any]) -> str:
    location = ".".join(str(part) for part in error.get("loc", ())) or "<root>"
    message = error.get("msg", "Invalid value")
    return f"{location}: {message}"
