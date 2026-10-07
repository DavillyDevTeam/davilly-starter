"""Generator entry point; Template expansion is owned by task #8."""

from typing import Annotated

import typer

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """Generate an app with the Davilly Starter."""


@app.command()
def new(name: Annotated[str, typer.Argument(help="Generated app directory.")]) -> None:
    """Reserve the public interface until Template generation lands."""
    typer.echo(f"Generation of {name!r} is not implemented yet (task #8).", err=True)
    raise typer.Exit(code=1)
