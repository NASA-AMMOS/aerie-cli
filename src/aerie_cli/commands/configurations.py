"""configurations.py

Commands related to persistent storage of Aerie host configurations.
"""

import typer
import logging
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from aerie_cli.aerie_host import AerieHostConfiguration
from aerie_cli.persistent import PersistentConfigurationManager, PersistentSessionManager, delete_all_persistent_files, NoActiveSessionError, CONFIGURATION_FILE_PATH
from aerie_cli.utils.prompts import select_from_list

app = typer.Typer()


@app.command('create')
def create_configuration(
    name: str = typer.Option(
        ..., prompt=True, help='Name for this configuration', metavar='NAME'),
    graphql_url: str = typer.Option(
        ..., prompt='GraphQL URL', help='URL of GraphQL API endpoint', metavar='GRAPHQL_URL'),
    gateway_url: str = typer.Option(
        ..., prompt='Gateway URL', help='URL of Aerie Gateway', metavar='GATEWAY_URL'),
    username: str = typer.Option(
        None, help='Username for authentication', metavar='USERNAME'
    )
):
    """
    Define a configuration for an Aerie host
    """
    if typer.confirm('Specify username'):
        username = typer.prompt('Username')
    else:
        username = None

    conf = AerieHostConfiguration(
        name, graphql_url, gateway_url, username)
    PersistentConfigurationManager.create_configuration(conf)


@app.command('load')
def upload_configurations(
    filename: Path = typer.Option(
        ..., '--filename', '-i', prompt='Input filename',
        help='Name of input JSON file'
    ),
    allow_overwrite: bool = typer.Option(
        False, '--allow-overwrite',
        help='Allow overwriting existing configurations'
    )
):
    """
    Load one or more configurations from a JSON file
    """
    with open(filename, 'r') as fid:
        configurations = json.load(fid)

    if isinstance(configurations, list):
        configurations = [AerieHostConfiguration.from_dict(
            c) for c in configurations]
    else:
        configurations = [AerieHostConfiguration.from_dict(configurations)]

    new_confs = []
    updated_confs = []

    for c in configurations:
        try:
            PersistentConfigurationManager.create_configuration(c)
            new_confs.append(c.name)
        except ValueError as e:
            if allow_overwrite and 'Configuration already exists' in e.args[0]:
                PersistentConfigurationManager.update_configuration(c)
                updated_confs.append(c.name)
            else:
                raise e

    if len(new_confs):
        logging.info(f"Added configurations: {', '.join(new_confs)}")

    if len(updated_confs):
        logging.info(f"Updated configurations: {', '.join(updated_confs)}")


@app.command('list')
def list_configurations():
    """
    List available Aerie host configurations
    """

    # Get the name of the active session configuration, if any
    try:
        s = PersistentSessionManager.get_active_session()
        active_config = s.configuration_name
    except NoActiveSessionError:
        active_config = None

    logging.info(f"Configuration file location: {CONFIGURATION_FILE_PATH}")

    table = Table(title='Aerie Host Configurations',
                  caption='Active configuration in red')
    table.add_column('Host Name', no_wrap=True)
    table.add_column('GraphQL API URL', no_wrap=True)
    table.add_column('Aerie Gateway URL', no_wrap=True)
    table.add_column('Username', no_wrap=True)
    for c in PersistentConfigurationManager.get_configurations():
        if c.name == active_config:
            style = 'red'
        else:
            style = None
        table.add_row(
            c.name,
            c.graphql_url,
            c.gateway_url,
            c.username if c.username else "",
            style=style
        )

    Console().print(table)


@app.command('delete')
def delete_configuration(
    name: str = typer.Option(
        None, '--name', '-n', help='Name for this configuration', metavar='NAME', show_default=False)
):
    """
    Delete an Aerie host configuration
    """
    names = [c.name for c in PersistentConfigurationManager.get_configurations()]
    if not name:
        name = select_from_list(names)

    PersistentConfigurationManager.delete_configuration(name)

    try:
        s = PersistentSessionManager.get_active_session()
        if name == s.configuration_name:
            PersistentSessionManager.unset_active_session()
    except NoActiveSessionError:
        pass


@app.command('clean')
def delete_all_files(
    not_interactive: bool = typer.Option(
        False, help='Disable interactive prompt')
):
    """
    Remove all persistent aerie-cli files
    """
    # Please don't flame me for this double negative, it had to be done
    if not not_interactive:
        if not typer.confirm("Delete all persistent files associated with aerie-cli?"):
            return

    delete_all_persistent_files()
    # Update the PersistentConfigurationManager's cached configurations to account for the clean
    PersistentSessionManager.reset()
    PersistentConfigurationManager.reset()
