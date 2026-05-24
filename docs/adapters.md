# Provider Adapters

CoachSpec provider adapters define the boundary between the runtime and any
future LLM provider integration. They normalize runtime data into a
provider-neutral request and normalize provider output back into an assistant
message.

This milestone is interface-first only. It does not add real provider SDKs, read
API keys, make network calls, stream responses, or introduce async execution.

## Interfaces

The adapter package lives in `coachspec.adapters`.

- `ProviderRequest` contains the compiled instructions, active session id,
  coach identity, user input, execution strategy, and current memory snapshot.
- `ProviderResponse` contains normalized assistant content, the provider name,
  and optional metadata.
- `BaseProviderAdapter` defines the synchronous `generate(request)` method that
  provider integrations will implement later.
- `MockProviderAdapter` is a deterministic local adapter for tests and CLI smoke
  runs.

## Runtime Integration

`CoachSession` can optionally accept a provider adapter:

```python
from coachspec.adapters import MockProviderAdapter
from coachspec.runtime import CoachSession

session = CoachSession.from_file(
    "coaches/spirituality/bible_deep_dive.yaml",
    provider_adapter=MockProviderAdapter(),
)
response = session.respond_stub("Help me study John 1.")
```

If no adapter is configured, `CoachSession` keeps the existing local stub
behavior and returns a safe message explaining that no model provider is
configured.

## CLI Smoke Runs

The `run` command remains local by default:

```powershell
uv run python -m coachspec.cli run coaches/spirituality/bible_deep_dive.yaml
```

To exercise the adapter boundary without external calls, use:

```powershell
uv run python -m coachspec.cli run coaches/spirituality/bible_deep_dive.yaml --mock-provider
```

The mock provider is intentionally deterministic. It is useful for validating
request construction, session memory updates, and CLI wiring without coupling
CoachSpec to OpenAI, Anthropic, local model servers, or hosted APIs.
