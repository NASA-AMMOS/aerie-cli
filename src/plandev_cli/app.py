"""Main CLI application

`app` is the CLI application with which all commands, subcommands, and callbacks are registered.
"""
import typer
from typing import Optional

from plandev_cli.commands import models
from plandev_cli.commands import plans
from plandev_cli.commands import configurations
# from plandev_cli.commands import expansion
from plandev_cli.commands import constraints
from plandev_cli.commands import scheduling
from plandev_cli.commands import metadata

from plandev_cli.commands.command_context import CommandContext
from plandev_cli.__version__ import __version__
from plandev_cli.persistent import (
    PersistentConfigurationManager,
    PersistentSessionManager,
)
from plandev_cli.utils.prompts import select_from_list
from plandev_cli.utils.sessions import (
    start_session_from_configuration,
    get_active_session_client,
)
from plandev_cli.utils.configurations import find_configuration

app = typer.Typer()
app.add_typer(plans.plans_app, name="plans")
app.add_typer(models.app, name="models")
app.add_typer(configurations.app, name="configurations")
# expansion is temporarily unsupported by plandev-cli, until support for template expansion is added
# app.add_typer(expansion.app, name="expansion")
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
        help="Print PlanDev-CLI package version and exit.",
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
    ),
    username: str = typer.Option(
        None, "--username", "-u", help="Specify/override configured PlanDev username", metavar="USERNAME"
    ),
    role: str = typer.Option(
        None, "--role", "-r", help="Specify a non-default role", metavar="ROLE"
    ),
    force: bool = typer.Option(False, "--force", help="Force connection to PlanDev host and ignore version compatibility")
):
    """
    Activate a session with a PlanDev host using a given configuration
    """
    if name is None:
        name = select_from_list(
            [c.name for c in PersistentConfigurationManager.get_configurations()]
        )

    conf = PersistentConfigurationManager.get_configuration_by_name(name)

    session = start_session_from_configuration(conf, username, force=force)

    if role is not None:
        if role in session.plandev_jwt.allowed_roles:
            session.change_role(role)
        else:
            typer.echo(f"Role {role} not in allowed roles")

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


@app.command("role")
def change_role(
    role: str = typer.Option(
        None, "--role", "-r", help="New role to selec", metavar="ROLE"
    )
):
    """
    Change PlanDev permissions role for the active session
    """
    client = get_active_session_client()

    if role is None:
        typer.echo(f"Active Role: {client.plandev_host.active_role}")
        role = select_from_list(client.plandev_host.plandev_jwt.allowed_roles)

    client.plandev_host.change_role(role)

    PersistentSessionManager.set_active_session(client.plandev_host)

    typer.echo(f"Changed role to: {client.plandev_host.active_role}")


@app.command("status")
def print_status():
    """
    Returns information about the current PlanDev session.
    """

    client = CommandContext.get_client()

    if client.plandev_host.configuration_name:
        typer.echo(f"Active configuration: {client.plandev_host.configuration_name}")

    typer.echo(f"Active role: {client.plandev_host.active_role}")
