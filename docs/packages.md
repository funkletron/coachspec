# Local Coach Packages

CoachSpec packages make a validated coach portable as a local artifact. They are
zip files intended for file-based sharing, inspection, and archival.

This is not a hosted registry, marketplace, dependency resolver, signing system,
or auth mechanism. Packages stay local-first and provider-neutral.

## Create A Package

From the repository root:

```powershell
uv run python -m coachspec.cli package coaches/spirituality/bible_deep_dive.yaml
```

The command validates the CoachSpec YAML before writing the package. Invalid
coaches are rejected.

The output file is written next to the source YAML:

```text
bible-deep-dive.coachspec.zip
```

## Package Contents

Each package contains:

- `coach.yaml`: the validated CoachSpec YAML.
- `manifest.json`: portable metadata about the coach and package.
- `README.md`: a short generated package summary.
- `checksums.json`: SHA-256 checksums for package files.
- `examples/`: included only when an `examples/` directory exists next to the
  source YAML.

The manifest includes:

- `coach_id`
- `coach_name`
- `spec_version`
- `package_version`
- `created_at`
- `source_file`
- `checksum_references`
- `supported_runtime_version`

## Inspect A Package

```powershell
uv run python -m coachspec.cli inspect-package coaches/spirituality/bible-deep-dive.coachspec.zip
```

Inspection reads the manifest and checksums from the zip file and reports
whether the referenced checksums still match the package contents.

## Design Boundaries

Local packages do not change CoachSpec schema semantics. They only bundle a
validated YAML file with enough metadata to inspect and move it between local
systems.

No hosted registry, signing, dependency resolution, package marketplace, auth,
or provider-specific behavior is included.
