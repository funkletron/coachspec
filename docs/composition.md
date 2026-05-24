# Coach Composition

Coach composition describes how a coach's durable behavior is assembled from a
small set of declarative parts:

- identity
- pedagogy
- behavioral modules
- execution strategy

This is structured cognitive composition. It gives CoachSpec a way to name how a
coach thinks, teaches, asks, reflects, and progresses without turning the
runtime into an agent system.

## What Composition Is

Composition is a lightweight internal model that summarizes a validated
`CoachSpec` as:

- `CoachComposition`: the coach's identity, pedagogy, behavioral modules, and
  execution strategy
- `BehavioralModule`: a reusable coaching behavior such as
  `socratic_questioning` or `reflective_listening`
- `ExecutionStrategy`: the turn-level pattern that shapes how the coach moves
  through a conversation

The initial implementation derives composition from existing schema fields. It
does not add a new YAML section yet.

## What Composition Is Not

Composition is not:

- multi-agent orchestration
- autonomous agents
- distributed systems
- workflow automation
- a planner/executor architecture
- a plugin mechanism
- a model-provider integration

A composed coach is still one coach. The runtime still owns a single session and
a single compiled instruction artifact.

## Behavioral Modules

Behavioral modules describe reusable coaching patterns. Examples include:

- `socratic_questioning`
- `reflective_listening`
- `contextual_explanation`
- `deliberate_practice`
- `spiritual_reflection`
- `evidence_based_feedback`

Modules answer: "What behaviors should this coach reuse?"

They are declarative. They do not execute independently, route messages, or call
tools.

## Execution Strategies

Execution strategies describe how a coach tends to move through turns. The
initial registry includes:

- `sequential_guidance`
- `socratic_loop`
- `reflective_cycle`
- `curriculum_progression`
- `accountability_cycle`

Strategies answer: "What conversational pattern should organize the coach's
behavior?"

They are summaries that the compiler can include in generated instructions and
the runtime can expose in context. They are not workflow engines.

## Compiler and Runtime Behavior

The compiler includes a `Coach Composition` section in compiled instructions.
That section summarizes inferred behavioral modules and the selected execution
strategy.

The runtime exposes the selected `ExecutionStrategy` through `RuntimeContext`.
This lets future runtime adapters inspect the declared strategy without changing
the session model or creating agent orchestration.

## Future Direction

A later schema version may support explicit composition fields, for example:

```yaml
composition:
  modules:
    - socratic_questioning
    - reflective_listening
  strategy: socratic_loop
```

That future field should remain declarative. The compiler can use it to produce
clearer instructions, and runtimes can inspect it, but it should not imply
autonomous agents, hidden control flow, or provider-specific behavior.
