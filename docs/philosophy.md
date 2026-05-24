# CoachSpec Philosophy

CoachSpec treats a coach definition as a portable contract, not as an active
conversation. A YAML file should describe durable coaching intent: identity,
purpose, pedagogy, interaction style, memory policy, constraints, outputs, and
evaluation expectations. It should not accumulate runtime state.

## Specification Is Not Session State

A specification is reusable. A session is temporary.

Keeping them separate protects the standard from accidental coupling:

- The same coach spec can be used in many applications.
- Multiple users can run independent sessions from the same spec.
- Session identifiers, message history, and turn counts do not pollute the YAML.
- Future runtimes can resume, fork, inspect, or evaluate sessions without
  changing the canonical coach definition.

This is why `CoachSession` owns mutable state and `CoachSpec` remains a parsed
description of intended behavior.

## Compilation Is Not Execution

The compiler turns a validated spec into deterministic instructions. That output
is still not a model call. It is a stable artifact that a runtime can inspect,
log, test, or pass to a future provider adapter.

This keeps CoachSpec provider-neutral. OpenAI, Anthropic, local models, or
future runtimes should be integration choices, not schema requirements.

## Composition Is Not Agents

A coach can be understood as a composition of identity, pedagogy, reusable
behavioral modules, and an execution strategy. That composition describes the
shape of coaching behavior; it does not create multiple agents or an autonomous
workflow.

Behavioral modules answer what patterns the coach uses. Execution strategies
answer how the coach tends to move through a conversation. Both remain
declarative inputs to compilation and runtime context.

This keeps CoachSpec focused on specification. It can name reusable coaching
patterns without introducing orchestration, planners, tool routing, async
systems, or provider-specific execution.

## Memory Is a Boundary

Memory is part of coaching behavior, but storage is an implementation detail.

The first memory layer is intentionally small:

- `BaseMemory` defines the runtime-facing interface.
- `InMemoryConversationMemory` stores messages for one process and one session.
- `SessionMemorySnapshot` exposes immutable reads of the current conversation.

This avoids premature commitment to databases, vector stores, embeddings, or
hosted memory systems. Those can arrive later behind the same boundary.

## Runtime Should Be Boring First

The first runtime does not need tools, agents, async orchestration, or model
provider integrations. It needs clear ownership:

- specs define reusable coaching intent
- compiler outputs stable instructions
- sessions hold mutable runtime state
- memory records conversation history
- context exposes the current execution frame

That architecture gives future features a place to attach without turning the
schema into an application framework.
