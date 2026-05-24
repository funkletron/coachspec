from __future__ import annotations

import json
import zipfile
from pathlib import Path

from typer.testing import CliRunner

from coachspec.cli import app
from coachspec.packaging import CoachPackageError, create_coach_package, inspect_coach_package


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "coaches" / "spirituality" / "bible_deep_dive.yaml"


def test_package_creation_writes_required_files(tmp_path: Path) -> None:
    result = create_coach_package(EXAMPLE, output_dir=tmp_path)

    assert result.path == tmp_path / "bible-deep-dive.coachspec.zip"
    assert result.path.exists()
    with zipfile.ZipFile(result.path) as archive:
        assert set(archive.namelist()) == {
            "README.md",
            "checksums.json",
            "coach.yaml",
            "manifest.json",
        }
        manifest = json.loads(archive.read("manifest.json"))

    assert manifest["coach_id"] == "bible-deep-dive"
    assert manifest["coach_name"] == "Bible Deep Dive Coach"
    assert manifest["spec_version"] == "0.1.0"
    assert manifest["package_version"] == "1"
    assert manifest["checksum_references"]["coach.yaml"] == result.checksums["coach.yaml"]


def test_package_inspection_reports_valid_checksums(tmp_path: Path) -> None:
    result = create_coach_package(EXAMPLE, output_dir=tmp_path)

    inspection = inspect_coach_package(result.path)

    assert inspection.manifest["coach_id"] == "bible-deep-dive"
    assert inspection.valid_checksums is True
    assert "coach.yaml" in inspection.checksums
    assert "manifest.json" in inspection.checksums


def test_package_checksum_generation_detects_tampering(tmp_path: Path) -> None:
    result = create_coach_package(EXAMPLE, output_dir=tmp_path)
    tampered = tmp_path / "tampered.coachspec.zip"
    with zipfile.ZipFile(result.path) as source, zipfile.ZipFile(tampered, "w") as target:
        for item in source.infolist():
            payload = source.read(item.filename)
            if item.filename == "coach.yaml":
                payload += b"\n# tampered\n"
            target.writestr(item, payload)

    inspection = inspect_coach_package(tampered)

    assert inspection.valid_checksums is False


def test_invalid_coach_cannot_be_packaged(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text(
        """
coach:
  id: invalid
  name: Invalid
  version: 0.1.0
""",
        encoding="utf-8",
    )

    try:
        create_coach_package(invalid, output_dir=tmp_path)
    except CoachPackageError as exc:
        assert "cannot package invalid CoachSpec" in str(exc)
    else:
        raise AssertionError("invalid CoachSpec was packaged")


def test_package_cli_create_and_inspect(tmp_path: Path) -> None:
    runner = CliRunner()

    with runner.isolated_filesystem(temp_dir=tmp_path):
        package_result = runner.invoke(app, ["package", str(EXAMPLE)])
        package_path = EXAMPLE.parent / "bible-deep-dive.coachspec.zip"
        inspect_result = runner.invoke(app, ["inspect-package", str(package_path)])
        package_path.unlink()

    assert package_result.exit_code == 0
    assert "Created CoachSpec package" in package_result.stdout
    assert inspect_result.exit_code == 0
    assert "CoachSpec Package" in inspect_result.stdout
    assert "Checksums valid: Yes" in inspect_result.stdout
