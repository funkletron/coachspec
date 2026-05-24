# CoachSpec Runtime Contract v0

This document describes the current runtime boundary for CoachSpec. It is a small
stability checkpoint for tests and downstream implementation work, not a new
feature roadmap.

## CoachSession Responsibilities

`CoachSession` owns one local execution session for a validated `CoachSpec`.
It:

- stores immutable session identity and mutable session state in `SessionState`
- holds the `CoachComposition` and `CompiledPrompt` produced before the turn loop
- appends user and assistant messages to the configured `BaseMemory`
- builds provider-neutral `ProviderRequest` objects from compiled instructions and memory snapshots
- delegates model output to an optional `BaseProviderAdapter`
- emits ordered `RuntimeEvent` records for session, message, and memory activity
- closes the session by marking state inactive and emitting `session_ended`

The session loop consumes compiled runtime artifacts. It must not reinterpret raw
YAML during a turn.

## RuntimeContext Responsibilities

`RuntimeContext` is a read model for the current session. It contains:

- coach identity
- session identity
- execution strategy
- compiled prompt
- immutable memory snapshot

Creating a context emits a `memory_read` event because it snapshots session
memory.

## ProviderRequest / ProviderResponse Boundary

`ProviderRequest` is the runtime-to-provider boundary. It carries:

- coach id and name
- session id
- compiled instructions
- current user input
- execution strategy
- immutable memory snapshot

`ProviderResponse` is the provider-to-runtime boundary. It carries normalized
assistant content, provider name, and optional provider metadata. Runtime code
must not depend on provider SDK response objects.

## BaseProviderAdapter Boundary

`BaseProviderAdapter.generate(request)` accepts a `ProviderRequest` and returns a
`ProviderResponse`. Adapters isolate provider-specific API clients, credentials,
request mapping, response parsing, and errors.

The runtime package must remain usable without provider SDKs installed. Optional
adapters may require optional dependencies only when they are configured or
instantiated for live use.

The built-in `MockProviderAdapter` is local and deterministic for a given
request.

## BaseMemory / SessionMemorySnapshot Boundary

`BaseMemory` defines the memory store interface:

- `append(role, content)` records a conversation message
- `snapshot()` returns an immutable `SessionMemorySnapshot`
- `clear()` removes stored memory

`SessionMemorySnapshot` is the transfer object passed to runtime contexts,
provider requests, persistence, and exports. It contains conversation messages
and exposes `message_count`.

## RuntimeEvent Sequence and Event Types

Runtime events are append-only records with:

- `event_type`
- `session_id`
- `coach_id`
- monotonic positive `sequence`
- ISO-8601 `created_at`
- JSON-compatible `payload`

Current event types are:

- `session_started`
- `user_message_received`
- `assistant_message_generated`
- `memory_read`
- `memory_written`
- `session_ended`

The normal local turn sequence is:

1. `session_started`
2. `user_message_received`
3. `memory_written`
4. optional `memory_read` when building a provider request
5. `assistant_message_generated`
6. `memory_written`
7. `session_ended` when closed

## Session Persistence Snapshot Expectations

Session persistence writes explicit, inspectable JSON. A persisted session
contains:

- metadata and timestamps
- full validated coach spec data
- runtime context summary, including compiled prompt text
- conversation history
- behavioral module and execution strategy summaries
- serialized runtime events

Persistence snapshots must not serialize live provider adapter instances,
provider clients, file handles, or other process-local objects. Loading a session
restores state, memory, compiled behavior, and events. Provider adapters are
reattached explicitly by the caller if needed.

## Transcript, Events, and Metadata Export Expectations

Session export writes local JSON artifacts:

- `transcript.json` for ordered user and assistant messages
- `events.json` for serialized runtime events
- `metadata.json` for session, coach, count, timing, and execution strategy data

Exports are filesystem-local, human-inspectable, and independent of cloud
storage, telemetry, or provider SDKs.

## Runtime Non-Ownership

The runtime does not own:

- provider SDK installation or global provider configuration
- provider-specific response object formats outside adapters
- cloud persistence or remote storage
- telemetry pipelines
- vector memory, retrieval, indexing, or embeddings
- multi-agent orchestration, workflow engines, or async job scheduling
- raw YAML interpretation inside the session turn loop
- evaluation scoring policy beyond consuming already validated specs
