# CoachSpec Schema

This document describes the initial CoachSpec YAML schema. The schema is the
canonical contract for defining an AI coach. It is intentionally independent of
model providers, prompt libraries, web frameworks, and runtime execution.

The first schema layer is implemented in `coachspec.schema` with Pydantic models
and YAML loading helpers.

## Top-Level Sections

Every CoachSpec YAML file currently uses these top-level sections:

- `coach`: identity and package metadata for the coach specification.
- `purpose`: the reason the coach exists, including goals and non-goals.
- `identity`: the role, persona, principles, and boundaries of the coach.
- `interaction`: the coach's conversational style and turn-level guidelines.
- `pedagogy`: the teaching or coaching method the coach should use.
- `memory`: declared memory behavior and consent expectations.
- `constraints`: rules, refusals, and escalation guidance.
- `outputs`: expected response formats or artifacts.
- `evaluation`: criteria and signals used to assess coach quality.

Unknown top-level fields are rejected. This keeps the canonical schema explicit
while the project is young.

## Minimal Shape

```yaml
coach:
  id: example-coach
  name: Example Coach
  version: 0.1.0

purpose:
  summary: Help users with a clearly scoped coaching purpose.

identity:
  role: Example coaching role

interaction:
  style: Structured and reflective

pedagogy:
  approach: Guided practice

memory:
  mode: session

constraints: {}

outputs: {}

evaluation: {}
```

## Section Notes

### `coach`

Required fields:

- `id`
- `name`
- `version`

Optional fields:

- `description`
- `domain`
- `tags`

### `purpose`

Required fields:

- `summary`

Optional fields:

- `goals`
- `non_goals`

### `identity`

Required fields:

- `role`

Optional fields:

- `persona`
- `principles`
- `boundaries`

### `interaction`

Required fields:

- `style`

Optional fields:

- `tone`
- `asks_questions`
- `adapts_to_user`
- `turn_guidelines`

### `pedagogy`

Required fields:

- `approach`

Optional fields:

- `methods`
- `scaffolding`

### `memory`

Fields:

- `mode`: one of `none`, `session`, or `persistent`
- `stores`
- `retention`
- `consent_required`

Memory is declarative only at this layer. No memory backend or runtime execution
is implemented by the schema.

### `constraints`

Optional fields:

- `rules`
- `refusals`
- `escalation`

### `outputs`

Optional fields:

- `formats`
- `artifacts`
- `default_format`

### `evaluation`

Optional fields:

- `criteria`
- `success_signals`
- `failure_modes`
- `metadata`

Evaluation is metadata at this stage. The runtime evaluator is intentionally not
part of the first schema layer.

## Validation

Validate a coach file with:

```powershell
coachspec validate coaches/spirituality/bible_deep_dive.yaml
```

The same behavior is available from Python:

```python
from coachspec.schema import load_coachspec, validate_coachspec

spec = load_coachspec("coaches/spirituality/bible_deep_dive.yaml")
spec, errors = validate_coachspec("coaches/spirituality/bible_deep_dive.yaml")
```

## Current Boundaries

The schema does not include:

- runtime execution
- prompt rendering
- model/provider integrations
- web UI
- memory storage backends
- evaluator execution

Those concerns belong to later layers.
