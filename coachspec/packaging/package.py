from __future__ import annotations

import hashlib
import json
import tomllib
import zipfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from coachspec.schema import CoachSpec, validate_coachspec


PACKAGE_VERSION = "1"
FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


class CoachPackageError(ValueError):
    """Raised when a local CoachSpec package cannot be created or inspected."""


@dataclass(frozen=True)
class CoachPackageResult:
    path: Path
    manifest: dict[str, Any]
    checksums: dict[str, str]


@dataclass(frozen=True)
class CoachPackageInspection:
    path: Path
    manifest: dict[str, Any]
    checksums: dict[str, str]
    valid_checksums: bool


def create_coach_package(coach_path: str | Path, output_dir: str | Path | None = None) -> CoachPackageResult:
    source_path = Path(coach_path)
    spec, errors = validate_coachspec(source_path)
    if errors or spec is None:
        joined_errors = "; ".join(errors) if errors else "invalid CoachSpec"
        raise CoachPackageError(f"cannot package invalid CoachSpec: {joined_errors}")

    package_dir = Path(output_dir) if output_dir is not None else source_path.parent
    package_dir.mkdir(parents=True, exist_ok=True)
    package_path = package_dir / f"{spec.coach.id}.coachspec.zip"

    coach_yaml = source_path.read_bytes()
    readme = _readme_for(spec).encode("utf-8")
    file_payloads: dict[str, bytes] = {
        "coach.yaml": coach_yaml,
        "README.md": readme,
    }
    file_payloads.update(_example_payloads(source_path))

    checksums = {
        name: _sha256(payload)
        for name, payload in sorted(file_payloads.items())
    }
    manifest = _manifest_for(
        spec=spec,
        source_path=source_path,
        checksum_references=checksums,
    )
    manifest_payload = _json_bytes(manifest)
    checksums["manifest.json"] = _sha256(manifest_payload)
    checksums_payload = _json_bytes(checksums)

    with zipfile.ZipFile(package_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in sorted(file_payloads.items()):
            _write_zip_entry(archive, name, payload)
        _write_zip_entry(archive, "manifest.json", manifest_payload)
        _write_zip_entry(archive, "checksums.json", checksums_payload)

    return CoachPackageResult(
        path=package_path,
        manifest=manifest,
        checksums=checksums,
    )


def inspect_coach_package(package_path: str | Path) -> CoachPackageInspection:
    path = Path(package_path)
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            required = {"coach.yaml", "manifest.json", "README.md", "checksums.json"}
            missing = required - names
            if missing:
                raise CoachPackageError(f"package missing required files: {', '.join(sorted(missing))}")

            manifest = _read_json_entry(archive, "manifest.json")
            checksums = _read_json_entry(archive, "checksums.json")
            if not all(isinstance(key, str) and isinstance(value, str) for key, value in checksums.items()):
                raise CoachPackageError("checksums.json must contain string checksum values")

            valid_checksums = _validate_checksums(archive, checksums)
    except zipfile.BadZipFile as exc:
        raise CoachPackageError(f"invalid CoachSpec package: {path}") from exc
    except OSError as exc:
        raise CoachPackageError(f"could not read CoachSpec package: {path}") from exc

    return CoachPackageInspection(
        path=path,
        manifest=manifest,
        checksums=checksums,
        valid_checksums=valid_checksums,
    )


def _manifest_for(
    spec: CoachSpec,
    source_path: Path,
    checksum_references: dict[str, str],
) -> dict[str, Any]:
    return {
        "coach_id": spec.coach.id,
        "coach_name": spec.coach.name,
        "spec_version": spec.coach.version,
        "package_version": PACKAGE_VERSION,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "source_file": str(source_path),
        "checksum_references": checksum_references,
        "supported_runtime_version": _runtime_version(),
    }


def _readme_for(spec: CoachSpec) -> str:
    return (
        f"# {spec.coach.name}\n\n"
        f"Coach ID: `{spec.coach.id}`\n\n"
        f"{spec.purpose.summary}\n\n"
        "This is a local CoachSpec package artifact. It contains a validated "
        "CoachSpec YAML file and local metadata for inspection and portability.\n"
    )


def _example_payloads(source_path: Path) -> dict[str, bytes]:
    examples_dir = source_path.parent / "examples"
    if not examples_dir.exists() or not examples_dir.is_dir():
        return {}

    payloads: dict[str, bytes] = {}
    for path in sorted(examples_dir.rglob("*")):
        if path.is_file():
            archive_name = Path("examples") / path.relative_to(examples_dir)
            payloads[str(archive_name).replace("\\", "/")] = path.read_bytes()
    return payloads


def _runtime_version() -> str | None:
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    except OSError:
        return None
    project = data.get("project", {})
    if not isinstance(project, dict):
        return None
    version = project.get("version")
    return version if isinstance(version, str) else None


def _json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write_zip_entry(archive: zipfile.ZipFile, name: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(name, date_time=FIXED_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    archive.writestr(info, payload)


def _read_json_entry(archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
    try:
        payload = json.loads(archive.read(name).decode("utf-8"))
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise CoachPackageError(f"{name} is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise CoachPackageError(f"{name} must contain a JSON object")
    return payload


def _validate_checksums(archive: zipfile.ZipFile, checksums: dict[str, str]) -> bool:
    for name, expected in checksums.items():
        try:
            actual = _sha256(archive.read(name))
        except KeyError:
            return False
        if actual != expected:
            return False
    return True
