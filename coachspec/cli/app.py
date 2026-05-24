from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from coachspec.adapters import MockProviderAdapter
from coachspec.composition import CoachComposition
from coachspec.compiler import compile_prompt
from coachspec.evaluation import evaluate_coachspec
from coachspec.persistence import JsonSessionStorage, SessionPersistenceError
from coachspec.runtime import CoachSession
from coachspec.schema import validate_coachspec


app = typer.Typer(help="Developer tools for CoachSpec files.")
console = Console()
DEFAULT_SESSION_PATH = Path("sessions") / "last_session.json"
DEFAULT_SESSION_COACH_PATH = Path("coaches") / "spirituality" / "bible_deep_dive.yaml"


@app.callback()
def root() -> None:
    """Developer tools for CoachSpec files."""


@app.command()
def validate(path: Path) -> None:
    """Validate a CoachSpec YAML file."""
    spec, errors = validate_coachspec(path)

    if errors:
        console.print(f"[red]Invalid CoachSpec:[/red] {path}")
        for error in errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1)

    console.print(f"[green]Valid CoachSpec:[/green] {path} ({spec.coach.id})")


@app.command()
def compile(path: Path) -> None:
    """Compile a CoachSpec YAML file into coach instructions."""
    spec, errors = validate_coachspec(path)

    if errors:
        console.print(f"[red]Invalid CoachSpec:[/red] {path}")
        for error in errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1)

    if spec is None:
        raise typer.Exit(code=1)

    compiled = compile_prompt(spec)
    typer.echo(compiled.text, nl=False)


@app.command()
def inspect(path: Path) -> None:
    """Display a structured summary of a CoachSpec YAML file."""
    spec, errors = validate_coachspec(path)

    if errors:
        console.print(f"[red]Invalid CoachSpec:[/red] {path}")
        for error in errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1)

    if spec is None:
        raise typer.Exit(code=1)

    composition = CoachComposition.from_spec(spec)

    console.print(f"[bold]CoachSpec Inspect[/bold]: {spec.coach.name} ({spec.coach.id})")
    console.print(f"Version: {spec.coach.version}")
    console.print(f"Domain: {_value(spec.coach.domain)}")
    console.print(f"Description: {_value(spec.coach.description)}")
    console.print(f"Tags: {_inline_list(spec.coach.tags)}")

    console.print("\n[bold]Identity[/bold]")
    console.print(f"Role: {spec.identity.role}")
    console.print(f"Persona: {_value(spec.identity.persona)}")
    _print_list("Principles", spec.identity.principles)
    _print_list("Boundaries", spec.identity.boundaries)

    console.print("\n[bold]Purpose[/bold]")
    console.print(f"Summary: {spec.purpose.summary}")
    _print_list("Goals", spec.purpose.goals)
    _print_list("Non-goals", spec.purpose.non_goals)

    console.print("\n[bold]Pedagogy[/bold]")
    console.print(f"Approach: {spec.pedagogy.approach}")
    _print_list("Methods", spec.pedagogy.methods)
    _print_list("Scaffolding", spec.pedagogy.scaffolding)

    console.print("\n[bold]Interaction[/bold]")
    console.print(f"Style: {spec.interaction.style}")
    console.print(f"Tone: {_value(spec.interaction.tone)}")
    console.print(f"Asks questions: {_yes_no(spec.interaction.asks_questions)}")
    console.print(f"Adapts to user: {_yes_no(spec.interaction.adapts_to_user)}")
    _print_list("Turn guidelines", spec.interaction.turn_guidelines)

    console.print("\n[bold]Memory[/bold]")
    console.print(f"Mode: {spec.memory.mode}")
    console.print(f"Retention: {_value(spec.memory.retention)}")
    console.print(f"Consent required: {_yes_no(spec.memory.consent_required)}")
    _print_list("Stores", spec.memory.stores)

    console.print("\n[bold]Constraints[/bold]")
    _print_list("Rules", spec.constraints.rules)
    _print_list("Refusals", spec.constraints.refusals)
    _print_list("Escalation", spec.constraints.escalation)

    console.print("\n[bold]Evaluation[/bold]")
    _print_list("Criteria", spec.evaluation.criteria)
    _print_list("Success signals", spec.evaluation.success_signals)
    _print_list("Failure modes", spec.evaluation.failure_modes)
    if spec.evaluation.metadata:
        console.print("Metadata:")
        for key in sorted(spec.evaluation.metadata):
            console.print(f"  - {key}: {spec.evaluation.metadata[key]}")
    else:
        console.print("Metadata: None declared.")

    console.print("\n[bold]Composition[/bold]")
    console.print(f"Execution strategy: {composition.execution_strategy.name}")
    console.print(f"Strategy id: {composition.execution_strategy.id}")
    console.print(f"Strategy summary: {composition.execution_strategy.summary}")
    _print_list("Behavioral modules", list(composition.module_ids()))


@app.command()
def evaluate(path: Path) -> None:
    """Evaluate a CoachSpec YAML file without model-provider calls."""
    spec, errors = validate_coachspec(path)

    if errors:
        console.print(f"[red]Invalid CoachSpec:[/red] {path}")
        for error in errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1)

    if spec is None:
        raise typer.Exit(code=1)

    report = evaluate_coachspec(spec)

    console.print(f"[bold]CoachSpec Evaluation[/bold]: {spec.coach.name} ({report.coach_id})")
    console.print(f"Overall score: {report.overall_score:.2f}")
    console.print("Criteria:")
    for result in report.results:
        console.print(f"  - {result.criterion.name}: {result.score:.2f}")

    console.print("Strengths:")
    if report.strengths:
        for strength in report.strengths:
            console.print(f"  - {strength}")
    else:
        console.print("  - None identified.")

    console.print("Improvement suggestions:")
    if report.suggestions:
        for suggestion in report.suggestions:
            console.print(f"  - {suggestion}")
    else:
        console.print("  - None.")


@app.command()
def run(
    path: Path,
    mock_provider: bool = typer.Option(
        False,
        "--mock-provider",
        help="Use the built-in local mock provider adapter.",
    ),
) -> None:
    """Start a local runtime session without model-provider calls."""
    spec, errors = validate_coachspec(path)

    if errors:
        console.print(f"[red]Invalid CoachSpec:[/red] {path}")
        for error in errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1)

    if spec is None:
        raise typer.Exit(code=1)

    provider_adapter = MockProviderAdapter() if mock_provider else None
    session = CoachSession.from_spec(spec, provider_adapter=provider_adapter)
    context = session.context()

    console.print(f"[bold]CoachSpec Runtime[/bold]: {context.coach_name} ({context.coach_id})")
    console.print(f"Session: {context.session_id}")
    if mock_provider:
        console.print("Compiled instructions loaded. Using local mock provider adapter.")
    else:
        console.print("Compiled instructions loaded. No LLM provider is configured.")
    console.print("Instruction summary:")
    console.print(f"  Role: {spec.identity.role}")
    console.print(f"  Purpose: {spec.purpose.summary}")
    console.print(f"  Interaction: {spec.interaction.style}")
    console.print(f"  Strategy: {context.execution_strategy.name}")
    console.print(f"  Memory: {spec.memory.mode}")
    console.print("Enter messages below. Type /exit to end the session.")

    while session.state.is_active:
        try:
            user_input = input("You: ")
        except (EOFError, KeyboardInterrupt):
            console.print("\nSession ended.")
            session.close()
            break

        if user_input.strip().lower() in {"/exit", "exit", "quit"}:
            session.close()
            console.print("Session ended.")
            break

        response = session.respond_stub(user_input)
        console.print(f"CoachSpec: {response}")


@app.command()
def save_session(
    coach_path: Path = typer.Option(
        DEFAULT_SESSION_COACH_PATH,
        "--coach",
        "-c",
        help="CoachSpec YAML file to initialize before saving.",
    ),
    output: Path = typer.Option(
        DEFAULT_SESSION_PATH,
        "--output",
        "-o",
        help="Local JSON session file to write.",
    ),
    message: str | None = typer.Option(
        None,
        "--message",
        "-m",
        help="Optional user message to record before saving.",
    ),
) -> None:
    """Save a local runtime session as inspectable JSON."""
    spec, errors = validate_coachspec(coach_path)

    if errors:
        console.print(f"[red]Invalid CoachSpec:[/red] {coach_path}")
        for error in errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1)

    if spec is None:
        raise typer.Exit(code=1)

    session = CoachSession.from_spec(spec)
    if message:
        session.respond_stub(message)

    path = JsonSessionStorage().save(session, output)
    console.print(f"[green]Saved session:[/green] {path}")
    console.print(f"Session: {session.state.session_id}")
    console.print(f"Coach: {session.spec.coach.name} ({session.spec.coach.id})")
    console.print(f"Messages: {session.memory.snapshot().message_count}")


@app.command()
def load_session(
    path: Path = typer.Option(
        DEFAULT_SESSION_PATH,
        "--path",
        "-p",
        help="Local JSON session file to load.",
    ),
) -> None:
    """Load a persisted runtime session from local JSON."""
    try:
        session = JsonSessionStorage().load(path)
    except SessionPersistenceError as exc:
        console.print(f"[red]Invalid session file:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    context = session.context()
    console.print(f"[bold]Loaded CoachSpec Session[/bold]: {context.coach_name} ({context.coach_id})")
    console.print(f"Session: {context.session_id}")
    console.print(f"Active: {session.state.is_active}")
    console.print(f"Turns: {session.state.turn_count}")
    console.print(f"Strategy: {context.execution_strategy.name}")
    console.print(f"Messages: {context.memory_snapshot.message_count}")


def main() -> None:
    app()


def _value(value: str | None) -> str:
    return value if value else "Not specified."


def _inline_list(items: list[str]) -> str:
    return ", ".join(items) if items else "None declared."


def _print_list(label: str, items: list[str]) -> None:
    console.print(f"{label}:")
    if not items:
        console.print("  - None declared.")
        return
    for item in items:
        console.print(f"  - {item}")


def _yes_no(value: bool) -> str:
    return "Yes" if value else "No"
