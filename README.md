# CoachSpec

CoachSpec is an open specification and runtime framework for defining AI
coaching systems with structured YAML specifications. It is not a prompt
library.

## Examples

The `coaches/` directory contains a curated initial library of validated example
coach specifications, including:

- Bible Deep Dive Coach
- Marathon Training Coach
- French Conversation Coach
- Financial Runway Coach
- Creative Development Coach
- Leadership Reflection Coach
- Startup Mentor Coach
- Deep Reading Coach
- Systems Thinking Coach
- Reflective Journaling Coach

See `docs/examples.md` for the patterns these examples demonstrate.

Validate an example:

```powershell
uv run python -m coachspec.cli validate coaches/spirituality/bible_deep_dive.yaml
```

Compile an example:

```powershell
uv run python -m coachspec.cli compile coaches/spirituality/bible_deep_dive.yaml
```

## Behavioral Modules

Behavioral modules are reusable coaching pattern definitions such as
`socratic_questioning`, `reflective_listening`, `deliberate_practice`, and
`accountability_checkin`.

They are not separate agents, plugins, or runtime orchestration units. The
initial registry in `coachspec.modules` gives CoachSpec a shared vocabulary for
common behaviors while keeping the current schema, compiler, and runtime model
unchanged.

See `docs/behavioral_modules.md` for the current module boundary and future
schema direction.
