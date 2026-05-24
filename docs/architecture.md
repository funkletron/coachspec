# CoachSpec Architecture

CoachSpec is an open specification and runtime framework for AI coaching systems.
It should be treated first as a protocol and contract, then as a Python runtime.
The core design goal is to make a coach portable, inspectable, evaluable, and
runtime-independent.

CoachSpec is not a prompt library. A CoachSpec document describes the durable
structure of a coaching system: identity, goals, pedagogy, interaction style,
memory behavior, constraints, and evaluation metadata. Prompts are one possible
runtime artifact compiled from that structure.

## Architectural Layers

### 1. Specification Layer

The specification layer defines the public CoachSpec format.

Responsibilities:

- Define the canonical YAML document shape.
- Define required and optional fields.
- Define versioning rules for the spec.
- Define semantic meaning for concepts such as identity, goals, pedagogy,
  interaction style, memory behavior, constraints, and evaluation metadata.
- Stay independent from any model provider, orchestration framework, database,
  UI, or agent runtime.

Primary module:

- `coachspec.schema`

This layer is the standard. Everything else exists to validate, compile, run, or
test documents that conform to it.

### 2. Parsing and Validation Layer

The parsing and validation layer turns YAML into typed internal objects and
reports specification errors clearly.

Responsibilities:

- Load YAML from files, strings, or package resources.
- Parse documents into typed models.
- Validate structural correctness.
- Validate semantic constraints that can be checked statically.
- Preserve useful source-location context for diagnostics when possible.
- Produce stable error codes suitable for CLI output, editor integrations, and
  CI checks.

Primary module:

- `coachspec.schema`

This layer should answer: "Is this a valid CoachSpec document, and if not, why?"
It should not decide how to prompt a model, store memory, or run a coaching
session.

### 3. Compilation Layer

The compilation layer converts a validated coach specification into runtime-ready
artifacts.

Responsibilities:

- Normalize a validated spec into an internal representation.
- Resolve defaults and inherited behaviors.
- Compile identity, goals, pedagogy, constraints, and interaction style into a
  runtime instruction plan.
- Compile memory declarations into memory policies.
- Compile evaluation metadata into evaluator-facing descriptors.
- Provide deterministic output for the same input spec and compiler version.

Primary module:

- `coachspec.compiler`

The compiler should be provider-neutral. It may produce a prompt plan,
instruction bundle, policy graph, or execution manifest, but it should not call a
model. This keeps the specification portable and makes compilation testable.

### 4. Runtime Layer

The runtime layer executes a compiled coach in a conversation.

Responsibilities:

- Manage coaching sessions.
- Accept user messages and runtime context.
- Apply the compiled instruction plan.
- Invoke a model adapter.
- Apply constraints before and after model calls where appropriate.
- Coordinate memory reads and writes through memory interfaces.
- Emit structured events for observability and evaluation.

Primary module:

- `coachspec.runtime`

The runtime should depend on compiled artifacts, not raw YAML. Its job is
execution, not specification interpretation.

The initial runtime implementation establishes `CoachSession`, `SessionState`,
and `RuntimeContext`. It can load a validated coach, compile instructions,
initialize session state, expose runtime context, and maintain conversation
history through memory abstractions. It intentionally does not call an LLM.

### 5. Memory Layer

The memory layer defines how coaches declare, read, write, and constrain memory.

Responsibilities:

- Represent memory policies from the spec.
- Provide interfaces for memory stores.
- Separate short-term session state from durable user memory.
- Enforce memory scope, retention, consent, and redaction rules.
- Avoid coupling memory to a specific vector store or database.

Primary module:

- `coachspec.memory`

Memory should be policy-driven. A coach specification may declare what kinds of
memory are allowed or useful, but the runtime and host application decide which
memory backend is available.

The first memory implementation provides a `BaseMemory` interface,
`InMemoryConversationMemory`, and immutable `SessionMemorySnapshot` objects.
This keeps session memory testable and replaceable without introducing
databases, vector stores, or provider-specific retrieval.

### 6. Evaluation Layer

The evaluation layer describes how coaching quality, safety, and adherence can be
measured.

Responsibilities:

- Represent evaluation metadata from the spec.
- Define interfaces for transcript evaluators.
- Support checks for goal adherence, pedagogical consistency, constraint
  adherence, interaction style, and memory behavior.
- Produce machine-readable evaluation results.

Likely future module:

- `coachspec.evaluation`

This can start as metadata in the schema and expand into a module once there is a
clear need for executable evaluation.

### 7. Interface and Tooling Layer

The interface layer exposes CoachSpec to developers.

Responsibilities:

- Validate specs from the command line.
- Compile specs and inspect compiled artifacts.
- Run local smoke-test conversations.
- Generate documentation summaries for a coach.
- Support CI workflows.

Primary module:

- `coachspec.cli`

The CLI should be thin. It should call stable library APIs rather than contain
business logic.

### 8. Coach Catalog Layer

The coach catalog contains example and reference coach specifications.

Responsibilities:

- Provide high-quality example coaches.
- Demonstrate domain-specific patterns.
- Exercise the schema and compiler in tests.
- Avoid becoming a grab bag of prompts.

Primary directory:

- `coaches`

Examples should be treated as reference specifications, not as the core product.

## Module Responsibilities

### `coachspec.schema`

Owns the public document model.

Recommended responsibilities:

- YAML loading.
- Pydantic models or equivalent typed schema models.
- Spec version handling.
- Validation errors and warning types.
- JSON Schema export if useful for editor support.
- Compatibility checks across spec versions.

Should not own:

- Model calls.
- Prompt rendering.
- Memory storage.
- Conversation loops.
- Provider-specific behavior.

### `coachspec.compiler`

Owns transformation from validated spec to runtime contract.

Recommended responsibilities:

- `compile(spec) -> CompiledCoach`
- Default resolution.
- Static policy assembly.
- Prompt or instruction planning.
- Constraint normalization.
- Memory policy normalization.
- Evaluation descriptor extraction.

Should not own:

- YAML parsing.
- Provider SDK calls.
- Database access.
- CLI formatting.

### `coachspec.runtime`

Owns session execution.

Recommended responsibilities:

- `CoachRuntime`
- `CoachSession`
- Message handling.
- Runtime context handling.
- Model adapter invocation.
- Constraint enforcement hooks.
- Event emission.

Should not own:

- Spec validation.
- YAML file discovery.
- Concrete long-term memory infrastructure.
- Domain-specific coaching content.

### `coachspec.memory`

Owns memory abstractions and policies.

Recommended responsibilities:

- `MemoryStore` interface.
- `MemoryPolicy` model.
- session memory abstractions.
- durable memory abstractions.
- consent, retention, and scope concepts.

Should not own:

- Coach identity.
- Pedagogy.
- Prompt compilation.
- Provider-specific retrieval code.

### `coachspec.cli`

Owns developer-facing commands.

Recommended responsibilities:

- `coachspec validate path/to/coach.yaml`
- `coachspec compile path/to/coach.yaml`
- `coachspec inspect path/to/coach.yaml`
- Eventually, `coachspec run path/to/coach.yaml`

Should not own:

- Validation rules.
- Compiler semantics.
- Runtime behavior.

## Separation of Concerns

CoachSpec should preserve a strict flow:

```text
YAML spec
  -> parse and validate
  -> typed CoachSpec model
  -> compile
  -> CompiledCoach artifact
  -> execute in runtime
  -> events, memory updates, evaluation data
```

The key separations are:

- Specification vs. runtime: the YAML defines intent and policy; the runtime
  executes a compiled contract.
- Specification vs. session state: the spec remains static and reusable;
  `SessionState` holds mutable per-conversation facts such as session id,
  active status, and turn count.
- Compiled instructions vs. execution context: compiled prompts are stable
  artifacts; `RuntimeContext` adds the active session id and memory snapshot.
- Coach behavior vs. model provider: a coach should not depend on OpenAI,
  Anthropic, local models, LangChain, or any other provider.
- Memory policy vs. memory storage: the spec declares allowed memory behavior;
  the host application supplies storage.
- Pedagogy vs. prompting: pedagogy is a durable coaching method; prompts are a
  generated representation of that method.
- Evaluation metadata vs. evaluator implementation: specs can declare what good
  behavior means before the project has a full evaluator engine.
- CLI vs. library: the CLI exposes workflows; the library owns semantics.

## Recommended Core Interfaces

These are conceptual interfaces, not implementation commitments.

### `CoachSpec`

The parsed and validated representation of a YAML document.

Core fields:

- `version`
- `identity`
- `goals`
- `pedagogy`
- `interaction_style`
- `memory`
- `constraints`
- `evaluation`
- `metadata`

### `SpecLoader`

Loads a spec document from a source.

Expected behavior:

- Accept file paths, strings, and package resources.
- Return raw document data plus source metadata.
- Avoid validation beyond basic readability.

### `SpecValidator`

Validates raw document data.

Expected behavior:

- Return a typed `CoachSpec`.
- Return structured validation errors.
- Distinguish errors from warnings.

### `CoachCompiler`

Compiles a `CoachSpec` into a `CompiledCoach`.

Expected behavior:

- Produce deterministic compiled output.
- Resolve defaults.
- Normalize policies.
- Avoid model-provider calls.

### `CompiledCoach`

The provider-neutral execution contract.

Likely contents:

- instruction plan
- coaching goals
- interaction policy
- constraint policy
- memory policy
- evaluation descriptors
- source spec metadata

### `ModelAdapter`

Abstracts over model providers.

Expected behavior:

- Accept normalized runtime messages and instructions.
- Return normalized assistant output.
- Hide provider-specific request and response formats.

### `MemoryStore`

Abstracts over memory persistence.

Expected behavior:

- Read memory by scope and policy.
- Write memory only when permitted.
- Support deletion or expiration.
- Allow simple in-memory implementations for tests.

### `BaseMemory`

The current runtime-facing memory interface.

Expected behavior:

- Append normalized conversation messages.
- Return immutable session snapshots.
- Allow simple clearing for test and session lifecycle use.
- Remain independent of databases, vector stores, and embedding systems.

### `Constraint`

Represents a runtime-checkable rule.

Expected behavior:

- Support static validation where possible.
- Support pre-response and post-response checks later.
- Return structured violations.

### `CoachSession`

Represents one conversation between a user and a compiled coach.

Expected behavior:

- Hold session state.
- Process user turns.
- Coordinate runtime, model adapter, constraints, and memory.
- Emit structured events.

The first implementation records user and assistant messages and returns stub
assistant responses. Provider-backed response generation belongs behind a future
adapter boundary.

### `EvaluationResult`

Represents assessment output for a transcript or session.

Expected behavior:

- Link findings to goals, constraints, pedagogy, or interaction style.
- Be machine-readable.
- Support CI and benchmark use cases later.

## Extensibility Boundaries

The long-term health of CoachSpec depends on stable boundaries.

### Keep the YAML Spec Stable and Versioned

Every CoachSpec document should declare a spec version. Breaking changes should
be explicit. New optional fields are safer than silent semantic changes.

Recommended boundary:

- `version` controls schema interpretation.
- compiler behavior is version-aware.
- old specs can be migrated or warned on.

### Treat Providers as Plugins

No provider SDK should leak into schema or compiler types. Provider-specific
behavior belongs behind `ModelAdapter`.

Recommended boundary:

- core runtime accepts a `ModelAdapter`.
- provider integrations live in optional packages later, such as
  `coachspec-openai` or `coachspec-anthropic`.

### Treat Memory Backends as Plugins

Memory storage should remain replaceable.

Recommended boundary:

- core defines `MemoryStore`.
- built-in memory starts with simple in-memory and file-backed options only.
- vector databases and hosted stores come later as integrations.

### Keep Evaluation Declarative First

Evaluation can become complex quickly. The initial spec should define metadata
and expected behaviors before building a full scoring engine.

Recommended boundary:

- schema supports evaluation descriptors.
- runtime emits events and transcripts.
- evaluator engine can arrive later without changing coach definitions.

### Separate Reference Coaches from Core Semantics

The `coaches` directory should demonstrate the standard but not define it.

Recommended boundary:

- examples must validate against the schema.
- tests may use examples as fixtures.
- no domain-specific assumptions should enter core modules.

### Keep Compilation Deterministic

Compilation should be pure where possible.

Recommended boundary:

- same spec plus same compiler version gives same compiled artifact.
- compilation does not call models, load user memory, or inspect live sessions.

## Future Scaling Considerations

Likely scaling pressure points:

- Spec versioning: once external users write YAML, compatibility becomes a core
  feature.
- Diagnostics: validation errors need stable codes and helpful locations for
  editor integrations.
- Prompt portability: different model families may need different rendering
  strategies while preserving the same coaching semantics.
- Memory governance: consent, retention, deletion, redaction, and scope will
  become important as coaches become personal.
- Evaluation: open benchmarks and regression tests will matter if CoachSpec is
  treated as a standard.
- Registries: teams may want shared coach catalogs, signed specs, or package
  metadata.
- Composition: future coaches may import traits, pedagogical methods, or
  constraint bundles.
- Localization: identity, tone, pedagogy, and examples may need language-aware
  variants.
- Security: untrusted specs should not execute arbitrary code.
- Observability: runtimes should emit structured events without coupling to any
  specific tracing platform.
- Session lifecycle: future hosts will need explicit start, pause, resume, and
  close semantics without mutating the original coach specification.
- Runtime adapters: model providers, tool execution, and evaluators should plug
  into the runtime without changing schema models or memory stores.
- Governance: as an open standard, the project may eventually need a formal
  change process for schema evolution.

## What Not to Build Yet

Avoid building these too early:

- A large prompt template library.
- A complex agent framework.
- A visual coach builder.
- A hosted registry.
- A full benchmark platform.
- Provider-specific first-class schema fields.
- A custom DSL beyond YAML.
- Multi-agent orchestration.
- Advanced vector memory integrations.
- Automatic pedagogy generation.
- Fine-tuning workflows.
- Authentication, accounts, or SaaS infrastructure.
- A plugin marketplace.

The first milestone should prove that a coach can be defined clearly, validated
reliably, compiled deterministically, and executed through a minimal runtime
without tying the standard to one model provider or application framework.

## Initial Project Shape

The current package layout is a good starting point:

```text
coachspec/
  schema/      public spec models, YAML loading, validation
  compiler/    spec-to-runtime compilation
  runtime/     sessions, adapters, event flow
  memory/      memory policies and store interfaces
  cli/         developer commands

coaches/       reference coach specs by domain
docs/          standard, architecture, philosophy, schema notes
tests/         schema, compiler, runtime, and fixture tests
```

The next architectural step should be to define the minimal v0 schema and the
typed objects that correspond to it. After that, build the smallest validator and
compiler that can process one or two reference coaches end to end.
