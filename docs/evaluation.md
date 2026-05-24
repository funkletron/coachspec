# CoachSpec Evaluation

CoachSpec Eval v0 is a deterministic, static evaluation layer for coach
specifications and compiled prompt inputs. It does not call an LLM, external
scoring service, benchmark platform, or model provider.

The goal is to give authors quick feedback about whether a coach specification
is clear enough to validate, compile, inspect, and improve.

## Concepts

The evaluation package lives in `coachspec.evaluation`.

Core concepts:

- `EvaluationCriterion`: a named quality dimension.
- `EvaluationResult`: the score, strengths, and suggestions for one criterion.
- `CoachEvaluationReport`: the overall score and full set of criterion results
  for a coach.

Scores are normalized from `0.0` to `1.0`. They are intentionally simple and
deterministic so they can be used in tests, CI, and local authoring workflows.

## Static Criteria

Eval v0 includes static evaluators for:

- schema completeness
- purpose clarity
- identity clarity
- pedagogy specificity
- constraint coverage
- output structure clarity
- memory clarity

These checks inspect the validated `CoachSpec` structure. They do not judge
truth, correctness, coaching effectiveness, or user outcomes.

## CLI Usage

Run evaluation with:

```powershell
uv run python -m coachspec.cli evaluate coaches/spirituality/bible_deep_dive.yaml
```

The output includes:

- overall score
- criterion scores
- strengths
- improvement suggestions

## Boundaries

CoachSpec Eval v0 is not:

- an LLM judge
- a user outcome benchmark
- a safety certification
- a hosted scoring service
- a replacement for expert review

It is a lightweight quality signal for static coach specifications.

## Future Direction

Future versions may add:

- transcript-level evaluation
- compiled prompt checks
- criterion configuration
- machine-readable report output
- regression thresholds for CI
- optional evaluator adapters

Those additions should preserve the core boundary: deterministic local checks
first, provider-backed evaluation only behind explicit optional integrations.
