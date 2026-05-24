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
