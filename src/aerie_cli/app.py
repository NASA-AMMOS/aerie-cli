"""Main CLI application

`app` is the CLI application with which all commands, subcommands, and callbacks are registered.
"""
import typer
from typing import Optional

from aerie_cli.commands import models
from aerie_cli.commands import plans
from aerie_cli.commands import configurations
from aerie_cli.commands import expansion
from aerie_cli.commands import constraints
from aerie_cli.commands import scheduling
from aerie_cli.commands import metadata

from aerie_cli.commands.command_context import CommandContext
from aerie_cli.__version__ import __version__
from aerie_cli.utils.configurations import find_configuration
from aerie_cli.persistent import (
    PersistentConfigurationManager,
    PersistentSessionManager,
)
from aerie_cli.utils.prompts import select_from_list
from aerie_cli.utils.sessions import start_session_from_configuration

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


def set_alternate_configuration(configuration_identifier: str):
    if configuration_identifier == None:
        return
    found_configuration = find_configuration(configuration_identifier)

    CommandContext.alternate_configuration = found_configuration


def setup_global_command_context(hasura_admin_secret: str):
    CommandContext.hasura_admin_secret = hasura_admin_secret


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
    configuration=typer.Option(
        None,
        "--configuration",
        "-c",
        callback=set_alternate_configuration,
        help="Set a configuration to use rather than the persistent configuration.\n\
            Accepts either a configuration name or the path to a configuration json.\n\
            Configuration names are prioritized over paths.",
    ),
):
    setup_global_command_context(hasura_admin_secret)


@app.command("activate")
def activate_session(
    name: str = typer.Option(
        None, "--name", "-n", help="Name for this configuration", metavar="NAME"
    )
):
    """
    Activate a session with an Aerie host using a given configuration
    """
    if name is None:
        name = select_from_list(
            [c.name for c in PersistentConfigurationManager.get_configurations()]
        )

    conf = PersistentConfigurationManager.get_configuration_by_name(name)

    session = start_session_from_configuration(conf)
    PersistentSessionManager.set_active_session(session)


@app.command("deactivate")
def deactivate_session():
    """
    Deactivate any active session
    """
    name = PersistentSessionManager.unset_active_session()
    if name is None:
        typer.echo("No active session")
    else:
        typer.echo(f"Deactivated session: {name}")