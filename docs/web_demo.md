# CoachSpec Web Demo

The web demo is a tiny local host application that shows how a regular person
could use a CoachSpec coach through an end-user interface. It lists the example
coaches, starts a runtime session, sends chat messages through the built-in mock
provider, displays the transcript and session memory status, and exports the
same local artifacts used by the runtime exporter.

This demo is not the main CoachSpec product direction. CoachSpec remains the
infrastructure and protocol layer for defining, compiling, running, persisting,
and exporting coaching sessions. The demo intentionally avoids auth, databases,
hosted services, real LLM calls, and product-only concepts.

## What It Proves

The demo keeps the host app thin:

- Coach definitions still come from `coaches/*.yaml`.
- Session behavior uses `CoachSession`.
- Provider behavior uses `MockProviderAdapter` by default.
- Local persistence uses `JsonSessionStorage`.
- Export artifacts use `SessionExporter`.

That shows CoachSpec can power a user-facing coaching app without moving UI or
product semantics into the core schema.

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
