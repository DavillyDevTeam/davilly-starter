import re
from importlib.resources import as_file, files
from pathlib import Path
from typing import Annotated

import typer
from copier import run_copy

app = typer.Typer(no_args_is_help=True)

ALLOWED_LOCALES: frozenset[str] = frozenset({"en", "pt-BR"})
ALLOWED_LICENSES: frozenset[str] = frozenset({"MIT", "Apache-2.0", "UNLICENSED"})


@app.callback()
def main() -> None:
    """Generate a FastAPI + React application."""


def parse_locales(value: str) -> list[str]:
    parts = (part.strip() for part in value.split(",") if part.strip())
    selected = list(dict.fromkeys(parts))
    if not selected or not set(selected) <= ALLOWED_LOCALES:
        raise typer.BadParameter("Supported locales: en,pt-BR.")
    return selected


@app.command()
def new(
    destination: Annotated[Path, typer.Argument(help="New directory, e.g. my-app")],
    project_name: Annotated[str | None, typer.Option()] = None,
    author: Annotated[str, typer.Option()] = "Your team",
    license: Annotated[str, typer.Option()] = "MIT",
    locales: Annotated[
        str, typer.Option(help="Comma-separated BCP 47 tags: en,pt-BR or a subset")
    ] = "en,pt-BR",
) -> None:
    """Write a parameterized Generated app without prompting or overwriting."""
    if destination.exists():
        raise typer.BadParameter("Destination already exists; choose a new directory.")
    slug = destination.name
    if re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", slug) is None:
        raise typer.BadParameter("Directory name must be a lowercase kebab-case slug.")
    selected = parse_locales(locales)
    if license not in ALLOWED_LICENSES:
        raise typer.BadParameter("Supported licenses: MIT, Apache-2.0, UNLICENSED.")
    data: dict[str, str | list[str]] = {
        "project_slug": slug,
        "project_name": project_name or slug,
        "author": author,
        "license": license,
        "locales": selected,
    }
    with as_file(files("davilly_starter").joinpath("copier_root")) as source:
        _ = run_copy(str(source), str(destination), data=data, defaults=True)
    typer.echo(
        f"Created {destination}. Run: cd {destination} && docker compose up --build"
    )
