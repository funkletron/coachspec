# Example Coach Library

CoachSpec includes a small curated library of example coaches. These examples
are reference specifications, not a prompt collection. Their purpose is to show
how reusable coaching systems can be described with the canonical YAML schema.

Each example validates against the current schema and compiles into deterministic
coach instructions.

## Included Coaches

- `coaches/spirituality/bible_deep_dive.yaml`: close reading, humility, and
  reflective study.
- `coaches/fitness/marathon_training.yaml`: progressive planning, recovery, and
  safety boundaries.
- `coaches/education/french_conversation.yaml`: language immersion, correction,
  and fluency practice.
- `coaches/finance/financial_runway.yaml`: assumption-driven cash runway and
  scenario planning.
- `coaches/creativity/creative_development.yaml`: creative practice, constraints,
  critique, and project momentum.
- `coaches/leadership/leadership_reflection.yaml`: accountable reflection,
  stakeholder thinking, and next-action discipline.
- `coaches/business/startup_mentor.yaml`: startup assumptions, customer
  discovery, and experiment design.
- `coaches/education/deep_reading.yaml`: text-centered reading, annotation, and
  synthesis.
- `coaches/systems/systems_thinking.yaml`: systems mapping, feedback loops, and
  intervention design.
- `coaches/journaling/reflective_journaling.yaml`: reflective prompts, emotional
  naming, and user-led insight.

## Design Patterns Demonstrated

### Structured Inquiry

Several coaches begin by clarifying the user's situation before offering any
guidance. This pattern appears in the Bible, leadership, startup, financial, and
systems examples.

### Progressive Scaffolding

The marathon, French, deep reading, and creative examples show how pedagogy can
define a sequence of support: assess, practice, review, and adapt.

### Safety and Scope Boundaries

Examples in finance, fitness, journaling, and leadership demonstrate how a coach
can be useful while making professional boundaries explicit.

### Memory as Declared Policy

The examples use `memory` to describe what would be useful to remember during a
session. They do not assume a database, vector store, or durable memory backend.

### Evaluation Metadata

Each coach includes criteria, success signals, and failure modes. This metadata
is not executable yet, but it establishes how a future evaluator could judge
whether the coach is behaving according to the spec.

## Current Schema Gaps

The current schema is intentionally small. While creating the examples, a few
future needs became visible:

- richer domain metadata for audience, prerequisite knowledge, and risk level
- structured safety categories instead of plain lists
- optional example interactions or fixture conversations
- reusable traits or imports for common coaching patterns
- localization metadata for language-specific coaches

These gaps are documented rather than added now. The examples should put
pressure on the schema, but schema expansion should happen only when repeated
usage proves the need.
