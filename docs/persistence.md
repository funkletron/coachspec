# CoachSpec Session Persistence

CoachSpec sessions can be saved as local JSON files and loaded back into the
runtime. This keeps coaching sessions longitudinal without introducing a
database, vector store, cloud service, authentication layer, or sync system.

Persistence is intentionally lightweight and inspectable. A saved session should
be readable in a text editor, portable across machines, and useful for tests,
debugging, evaluation, and future host applications.

## What Is Persisted

The JSON session format stores:

- session metadata such as session id, coach id, turn count, and active state
- the validated CoachSpec data needed to reconstruct the runtime session
- runtime context identifiers and compiled prompt text
- conversation history with role, content, and message timestamps
- selected behavioral modules
- selected execution strategy
- session timestamps for creation, last update, and close time
- provider-neutral runtime events emitted during the session

The format is explicit rather than compact. That is deliberate: persisted
sessions are part of the developer-facing surface and should be easy to inspect.

## Library API

The persistence package exposes three primary interfaces:

- `SessionSerializer` converts `CoachSession` objects to and from
  JSON-compatible dictionaries.
- `SessionStorage` defines the storage boundary.
- `JsonSessionStorage` implements local filesystem JSON persistence.

Example:

```python
from coachspec.persistence import JsonSessionStorage
from coachspec.runtime import CoachSession

session = CoachSession.from_file("coaches/spirituality/bible_deep_dive.yaml")
session.respond_stub("Help me study John 1.")

storage = JsonSessionStorage()
storage.save(session, "sessions/last_session.json")

reloaded = storage.load("sessions/last_session.json")
assert reloaded.state.session_id == session.state.session_id
```

## CLI

Save a default local session:

```bash
python -m coachspec.cli save-session
```

Load the default local session:

```bash
python -m coachspec.cli load-session
```

Export transcript, events, and metadata for a saved session:

```bash
python -m coachspec.cli export-session <session-id>
```

Use explicit paths:

```bash
python -m coachspec.cli save-session \
  --coach coaches/spirituality/bible_deep_dive.yaml \
  --output sessions/bible-session.json \
  --message "Help me study Psalm 23."

python -m coachspec.cli load-session --path sessions/bible-session.json

python -m coachspec.cli export-session <session-id> \
  --sessions-dir sessions \
  --output-dir exports/bible-session
```

The default output path is `sessions/last_session.json`. The `sessions/`
directory is ignored by git because saved sessions are local runtime artifacts,
not source files.

## Runtime vs. Persisted State

The runtime owns live execution:

- provider adapter references
- mutable session state
- in-memory conversation objects
- compiled prompt and composition objects

The persisted file owns a stable snapshot:

- JSON-compatible session metadata
- serialized CoachSpec data
- serialized conversation history
- selected module and strategy identifiers
- timestamps

Loading a session reconstructs a fresh `CoachSession` from the persisted
snapshot. Provider adapters are not serialized because they may hold process
state, credentials, sockets, SDK clients, or host-specific configuration.

## Export Artifacts

Session export writes three local JSON files:

- `transcript.json`: ordered user and assistant messages
- `events.json`: ordered runtime events with event type, sequence, timestamp,
  session id, coach id, and payload
- `metadata.json`: session id, coach id, coach name, turn count, timestamps,
  message count, event count, and execution strategy

These artifacts are intended for evaluation, replay, debugging, observability,
transcript inspection, and future UI integration. They are not telemetry and do
not imply network upload or analytics infrastructure.

## Corrupted Sessions

Invalid JSON, unsupported format versions, missing required fields, invalid
timestamps, and invalid embedded CoachSpec data raise `SessionPersistenceError`.
The CLI reports these as invalid session files and exits with a non-zero status.

## Extensibility

The storage boundary is intentionally small. Future storage backends can
implement `SessionStorage` without changing runtime session semantics.

Potential future integrations include:

- SQLite or document databases
- vector stores for retrieval-oriented memory
- encrypted local files
- application-managed cloud sync
- host-specific retention and deletion policies

Those are out of scope for the current milestone. CoachSpec remains local-first
for now so persistence stays portable, inspectable, deterministic in tests, and
independent from infrastructure choices.
