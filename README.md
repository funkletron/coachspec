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

Inspect an example summary:

```powershell
uv run python -m coachspec.cli inspect coaches/spirituality/bible_deep_dive.yaml
```

Evaluate an example:

```powershell
uv run python -m coachspec.cli evaluate coaches/spirituality/bible_deep_dive.yaml
```

Run a local smoke-test session:

```powershell
uv run python -m coachspec.cli run coaches/spirituality/bible_deep_dive.yaml
```

Exercise the provider adapter boundary with the deterministic local mock
provider:

```powershell
uv run python -m coachspec.cli run coaches/spirituality/bible_deep_dive.yaml --mock-provider
```

## Basic Functionality Smoke Test

Run the developer smoke test to validate, inspect, compile, exercise a short
mock-provider session, persist it locally, export transcript/events/metadata,
and run the lightweight evaluator:

```powershell
uv run python scripts/smoke_test.py
```

The smoke test uses `coaches/spirituality/bible_deep_dive.yaml`, the local
deterministic mock provider, and temporary filesystem artifacts. It does not
make real LLM calls, network calls, provider SDK calls, database calls, or UI
calls.

CoachSpec Eval v0 provides deterministic static checks for schema completeness,
purpose clarity, identity clarity, pedagogy specificity, constraints, outputs,
and memory behavior. It does not call LLM APIs or external scoring services.

Provider adapters are interface-first. The core package includes provider-neutral
request/response types and a mock adapter, but no provider SDK dependencies, API
key handling, or network calls.
