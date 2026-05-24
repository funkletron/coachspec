from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from coachspec.compiler import compile_prompt
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


def main() -> None:
    app()
