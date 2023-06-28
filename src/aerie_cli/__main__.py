"""Command-line interface."""
import typer
import sys
from rich.console import Console
from typing import Optional

from aerie_cli.commands import models
from aerie_cli.commands import plans
from aerie_cli.commands import configurations
from aerie_cli.commands import expansion
from aerie_cli.commands import constraints
from aerie_cli.commands import scheduling
from aerie_cli.commands import metadata

from .persistent import NoActiveSessionError
from aerie_cli.commands.command_context import CommandContext
from aerie_cli.__version__ import __version__

app = typer.Typer()
app.add_typer(plans.app, name="plans")
app.add_typer(models.app, name="models")
app.add_typer(configurations.app, name="configurations")
app.add_typer(expansion.app, name="expansion")
app.add_typer(constraints.app, name="constraints")
app.add_typer(scheduling.app, name="scheduling")
app.add_typer(metadata.app, name="metadata")


def print_version(print_version: bool):
    if print_version:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def app_callback(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=print_version,
        help="Print Aerie-CLI package version and exit.",
    ),
    hasura_admin_secret=typer.Option(
        default="",
        help="Hasura admin secret that will be put in the header of graphql requests.",
    ),
):
    setup_global_command_context(hasura_admin_secret)


def setup_global_command_context(hasura_admin_secret: str):
    CommandContext.hasura_admin_secret = hasura_admin_secret


def main():
    try:
        app()
    except NoActiveSessionError:
        Console().print(
            "There is no active session. Please start a session with aerie-cli configurations activate"
        )
        sys.exit(-1)
    except Exception:
        Console().print_exception()


if __name__ == "__main__":
    main()  # pragma: no cover
