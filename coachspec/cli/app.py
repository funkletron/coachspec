from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

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


def main() -> None:
    app()
