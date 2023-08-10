"""configurations.py

Commands related to persistent storage of Aerie host configurations.
"""

import typer
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from aerie_cli.aerie_host import AuthMethod, AerieHostConfiguration
from aerie_cli.persistent import PersistentConfigurationManager, PersistentSessionManager, delete_all_persistent_files, NoActiveSessionError, CONFIGURATION_FILE_PATH
from aerie_cli.utils.prompts import select_from_list
from aerie_cli.utils.sessions import start_session_from_configuration

app = typer.Typer()


@app.command('create')
def create_configuration(
    name: str = typer.Option(
        ..., prompt=True, help='Name for this configuration', metavar='NAME'),
    graphql_url: str = typer.Option(
        ..., prompt='GraphQL URL', help='URL of GraphQL API endpoint', metavar='GRAPHQL_URL'),
    gateway_url: str = typer.Option(
        ..., prompt='Gateway URL', help='URL of Aerie Gateway', metavar='GATEWAY_URL'),
    auth_method: AuthMethod = typer.Option(
        'None', prompt='Authentication method', help='Authentication method',
        case_sensitive=False
    ),
    auth_url: str = typer.Option(
        None, help='URL of Authentication endpoint', metavar='AUTH_URL'
    ),
    username: str = typer.Option(
        None, help='Username for authentication', metavar='USERNAME'
    )
):
    """
    Define a configuration for an Aerie host
    """
    # Auth-only fields
    if auth_method is not AuthMethod.NONE:
        if auth_url is None:
            auth_url = typer.prompt('URL of Authentication endpoint')
        if username is None:
            if typer.confirm('Specify username'):
                username = typer.prompt('Username')
            else:
                username = None

    conf = AerieHostConfiguration(
        name, graphql_url, gateway_url, auth_method, auth_url, username)
    PersistentConfigurationManager.create_configuration(conf)


@app.command('update')
def update_configuration(
    name: str = typer.Option(
        None, '--name', '-n', help='Name of the configuration to update', metavar='NAME'
    )
):
    """
    Update an existing configuration for an Aerie host
    """

    # Give user prompt if no name is given
    if name is None:
        name = select_from_list(
            [c.name for c in PersistentConfigurationManager.get_configurations()])

    # Get corresponding configuration
    conf = PersistentConfigurationManager.get_configuration_by_name(name)

    conf.graphql_url = typer.prompt(
        'Url of GraphQL API endpoint', conf.graphql_url)
    conf.gateway_url = typer.prompt('Url of Aerie Gateway', conf.gateway_url)

    # Prompt user to select an auth method
    auth_methods = [e.value for e in AuthMethod]
    conf.auth_method = AuthMethod.from_string(select_from_list(auth_methods))

    # Auth-only fields
    if conf.auth_method is not AuthMethod.NONE:
        conf.auth_url = typer.prompt(
            'URL of Authentication endpoint', conf.auth_url)
        if typer.confirm('Specify username', default=(conf.username is None)):
            conf.username = typer.prompt('Username')
        else:
            conf.username = None

    PersistentConfigurationManager.update_configuration(conf)


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
        Console().print(f"Added configurations: {', '.join(new_confs)}")

    if len(updated_confs):
        Console().print(f"Updated configurations: {', '.join(updated_confs)}")


@app.command('activate')
def activate_session(
    name: str = typer.Option(
        None, '--name', '-n', help='Name for this configuration', metavar='NAME')
):
    """
    Activate a session with an Aerie host using a given configuration
    """
    if name is None:
        name = select_from_list(
            [c.name for c in PersistentConfigurationManager.get_configurations()])

    conf = PersistentConfigurationManager.get_configuration_by_name(name)

    session = start_session_from_configuration(conf)
    PersistentSessionManager.set_active_session(session)


@app.command('deactivate')
def deactivate_session():
    """
    Deactivate any active session
    """
    name = PersistentSessionManager.unset_active_session()
    if name is None:
        Console().print("No active session")
    else:
        Console().print(f"Deactivated session: {name}")


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

    typer.echo(f"Configuration file location: {CONFIGURATION_FILE_PATH}")
    typer.echo()

    table = Table(title='Aerie Host Configurations',
                  caption='Active configuration in red')
    table.add_column('Host Name', no_wrap=True)
    table.add_column('GraphQL API URL', no_wrap=True)
    table.add_column('Aerie Gateway URL', no_wrap=True)
    table.add_column('Authentication Method', no_wrap=True)
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
            c.auth_method.value,
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
    PersistentSessionManager.unset_active_session()
    PersistentConfigurationManager.reset()