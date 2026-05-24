# Behavioral Modules

Behavioral modules are reusable coaching behaviors that can be named, discussed,
documented, and eventually referenced across coach specifications.

They are intentionally lightweight in this milestone. A behavioral module is a
shared definition of a coaching pattern, not a separate agent, plugin, runtime
orchestrator, prompt template, or executable workflow.

## Purpose

Many coaches reuse the same behavioral patterns:

- `socratic_questioning`
- `reflective_listening`
- `progressive_curriculum`
- `accountability_checkin`
- `contextual_explanation`
- `deliberate_practice`
- `habit_formation`
- `decision_framing`
- `spiritual_reflection`
- `evidence_based_feedback`

Naming these patterns gives CoachSpec a shared vocabulary without requiring
schema composition, runtime routing, or provider-specific behavior.

## Current Boundary

Behavioral modules are:

- reusable coaching behaviors
- declarative pattern definitions
- useful documentation and architecture vocabulary
- future candidates for schema references

Behavioral modules are not:

- separate agents
- plugins
- tools
- model providers
- runtime orchestration units
- automatic prompt imports
- YAML includes or inheritance

This keeps CoachSpec focused on being a specification system. A coach can still
express these patterns today through `pedagogy.methods`,
`interaction.turn_guidelines`, `constraints.rules`, and evaluation metadata.

## Registry

The lightweight registry lives in `coachspec.modules.registry`.

It provides:

- `BehavioralModule`: an immutable data model with `id`, `name`, and
  `description`
- `ModuleRegistry`: a small lookup object that enforces unique module IDs
- `default_registry`: the built-in set of initial module definitions

The registry is documentation-oriented and schema-compatible. It does not alter
validation, compilation, or runtime execution.

## Future Direction

A later schema version may add an optional field for module references, such as:

```yaml
modules:
  - socratic_questioning
  - reflective_listening
```

That field should remain declarative. The compiler may eventually use module
IDs as named inputs when rendering instructions, but runtime behavior should
still flow through the normal validated-spec and compiled-artifact path.

Until the schema explicitly supports module references, example coaches should
continue encoding these behaviors in existing schema sections.
