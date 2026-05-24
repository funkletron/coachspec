from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from coachspec.compiler import compile_prompt
from coachspec.runtime import CoachSession
from coachspec.schema import validate_coachspec


app = typer.Typer(help="Developer tools for CoachSpec files.")
console = Console()


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
def run(path: Path) -> None:
    """Start a local runtime session without model-provider calls."""
    spec, errors = validate_coachspec(path)

    if errors:
        console.print(f"[red]Invalid CoachSpec:[/red] {path}")
        for error in errors:
            console.print(f"  - {error}")
        raise typer.Exit(code=1)

    if spec is None:
        raise typer.Exit(code=1)

    session = CoachSession.from_spec(spec)
    context = session.context()

    console.print(f"[bold]CoachSpec Runtime[/bold]: {context.coach_name} ({context.coach_id})")
    console.print(f"Session: {context.session_id}")
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


def main() -> None:
    app()
