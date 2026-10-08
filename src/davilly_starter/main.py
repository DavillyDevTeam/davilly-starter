import re
from importlib.resources import as_file, files
from pathlib import Path
from typing import Annotated

import typer
from copier import run_copy

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """Generate a FastAPI + React application."""


@app.command()
def new(
    destination: Annotated[Path, typer.Argument(help="New directory, e.g. my-app")],
    project_name: Annotated[str | None, typer.Option()] = None,
    author: Annotated[str, typer.Option()] = "Your team",
    license: Annotated[str, typer.Option()] = "MIT",
    locales: Annotated[
        str, typer.Option(help="en,pt-BR or either locale")
    ] = "en,pt-BR",
) -> None:
    """Write a parameterized Generated app without prompting or overwriting."""
    if destination.exists():
        raise typer.BadParameter("Destination already exists; choose a new directory.")
    slug = destination.name
    if re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", slug) is None:
        raise typer.BadParameter("Directory name must be a lowercase kebab-case slug.")
    selected = list(dict.fromkeys(part.strip() for part in locales.split(",")))
    if not selected or not set(selected) <= {"en", "pt-BR"}:
        raise typer.BadParameter("Supported locales: en,pt-BR.")
    if license not in {"MIT", "Apache-2.0", "UNLICENSED"}:
        raise typer.BadParameter("Supported licenses: MIT, Apache-2.0, UNLICENSED.")
    data: dict[str, str] = {
        "project_slug": slug,
        "project_name": project_name or slug,
        "author": author,
        "license": license,
        "locales": ",".join(selected),
    }
    with as_file(files("davilly_starter").joinpath("copier_root")) as source:
        _ = run_copy(str(source), str(destination), data=data, defaults=True)
    typer.echo(
        f"Created {destination}. Run: cd {destination} && docker compose up --build"
    )
