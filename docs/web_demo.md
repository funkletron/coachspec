# CoachSpec Web Demo

The web demo is a tiny local host application that shows how a regular person
could use a CoachSpec coach through an end-user interface. It lists the example
coaches, starts a runtime session, sends chat messages through a selected
provider adapter, displays the transcript and runtime events, and exports the
same local artifacts used by the runtime exporter.

This demo is not the main CoachSpec product direction. CoachSpec remains the
infrastructure and protocol layer for defining, compiling, running, persisting,
and exporting coaching sessions. The demo intentionally avoids auth, databases,
hosted services, streaming, agents, tools, telemetry, and product-only concepts.

## What It Proves

The demo keeps the host app thin:

- Coach definitions still come from `coaches/*.yaml`.
- Session behavior uses `CoachSession`.
- Provider behavior uses `MockProviderAdapter` by default.
- Optional OpenAI calls use `OpenAIProviderAdapter` behind the same provider
  boundary.
- Local persistence uses `JsonSessionStorage`.
- Export artifacts use `SessionExporter`.

That shows CoachSpec can power a user-facing coaching app without moving UI or
product semantics into the core schema.

## Providers

The default provider is the local deterministic mock provider. It requires no
network access, no API key, and no optional provider SDK:

```powershell
uv run python examples/web-demo/app.py --no-browser
```

OpenAI is optional and backend-only. The browser sends only the selected provider
name (`mock` or `openai`) to the local demo server. API keys stay in the backend
process environment and are not included in frontend state, session payloads,
exports, persistence, or runtime events.

Install the optional dependency:

```powershell
uv sync --extra openai
```

Set the API key for the current PowerShell process:

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

Start the demo and select OpenAI in the provider dropdown:

```powershell
uv run python examples/web-demo/app.py --no-browser
```

If `OPENAI_API_KEY` is missing or the optional dependency is not installed, the
backend returns a clear configuration error and does not start a broken OpenAI
session.

## Run It

From the repository root:

```powershell
uv run python examples/web-demo/app.py
```

The app prints a local URL and opens the browser by default. To only print the
URL:

```powershell
uv run python examples/web-demo/app.py --no-browser
```

The default URL is:

```text
http://127.0.0.1:8765
```

Local session files are written under:

```text
examples/web-demo/.local/sessions/
```

Exported transcript, events, and metadata files are written under:

```text
examples/web-demo/.local/exports/
```

## Validation

Run the automated checks from the repository root:

```powershell
uv run pytest
uv run python scripts/smoke_test.py
```

Manual mock validation:

```powershell
uv run python examples/web-demo/app.py --no-browser
```

Then open:

```text
http://127.0.0.1:8765
```
