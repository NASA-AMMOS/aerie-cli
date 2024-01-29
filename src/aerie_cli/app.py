"""Main CLI application

`app` is the CLI application with which all commands, subcommands, and callbacks are registered.
"""
import typer
import logging
import sys
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
from aerie_cli.persistent import (
    PersistentConfigurationManager,
    PersistentSessionManager,
    clear_old_log_files,
    CURRENT_LOG_PATH
)
from aerie_cli.utils.prompts import select_from_list
from aerie_cli.utils.sessions import (
    start_session_from_configuration,
    get_active_session_client,
)
from aerie_cli.utils.configurations import find_configuration
from aerie_cli.utils.logger import TyperLoggingHandler

app = typer.Typer()
app.add_typer(plans.plans_app, name="plans")
app.add_typer(models.app, name="models")
app.add_typer(configurations.app, name="configurations")
app.add_typer(expansion.app, name="expansion")
app.add_typer(constraints.app, name="constraints")
app.add_typer(scheduling.app, name="scheduling")
app.add_typer(metadata.app, name="metadata")


def print_version(print_version: bool):
    if print_version:
        logging.info(__version__)
        raise typer.Exit()


def set_alternate_configuration(configuration_identifier: str):
    if configuration_identifier == None:
        return
    found_configuration = find_configuration(configuration_identifier)

    CommandContext.alternate_configuration = found_configuration


def setup_global_command_context(hasura_admin_secret: str):
    CommandContext.hasura_admin_secret = hasura_admin_secret

def setup_logging(debug: bool):
    clear_old_log_files()
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    file_handler = logging.FileHandler(filename=str(CURRENT_LOG_PATH),
                                        mode='w',
                                        encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    console_formatter = logging.Formatter(
        '%(message)s'
    )
    console_handler = TyperLoggingHandler()
    level = logging.DEBUG if debug else logging.INFO
    console_handler.setLevel(level) # Set the level of the stream and file handlers to different ones
                                    # Debug should be in file, others should go into stdout
                                    # unless verbose/debug option is selected
    console_handler.setFormatter(console_formatter)
    logging.basicConfig(level=logging.DEBUG,
                        handlers=[file_handler,
                                  console_handler])


@app.callback()
def app_callback(
    debug: Optional[bool]=typer.Option(
        False,
        "--debug",
        "-d",
        callback=setup_logging,
        help="View the debug output",
    ),
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
    ),
    username: str = typer.Option(
        None, "--username", "-u", help="Specify/override configured Aerie username", metavar="USERNAME"
    ),
    role: str = typer.Option(
        None, "--role", "-r", help="Specify a non-default role", metavar="ROLE"
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

    session = start_session_from_configuration(conf, username)

    if role is not None:
        if role in session.aerie_jwt.allowed_roles:
            session.change_role(role)
        else:
            logging.info(f"Role {role} not in allowed roles")

    PersistentSessionManager.set_active_session(session)


@app.command("deactivate")
def deactivate_session():
    """
    Deactivate any active session
    """
    name = PersistentSessionManager.unset_active_session()
    if name is None:
        logging.info("No active session")
    else:
        logging.info(f"Deactivated session: {name}")


@app.command("role")
def change_role(
    role: str = typer.Option(
        None, "--role", "-r", help="New role to selec", metavar="ROLE"
    )
):
    """
    Change Aerie permissions role for the active session
    """
    client = get_active_session_client()

    if role is None:
        logging.info(f"Active Role: {client.aerie_host.active_role}")
        role = select_from_list(client.aerie_host.aerie_jwt.allowed_roles)

    client.aerie_host.change_role(role)

    PersistentSessionManager.set_active_session(client.aerie_host)

    logging.info(f"Changed role to: {client.aerie_host.active_role}")


@app.command("status")
def print_status():
    """
    Returns information about the current Aerie session.
    """

    client = CommandContext.get_client()

    if client.aerie_host.configuration_name:
        logging.info(f"Active configuration: {client.aerie_host.configuration_name}")

    logging.info(f"Active role: {client.aerie_host.active_role}")
