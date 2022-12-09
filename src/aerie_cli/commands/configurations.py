import typer
from rich.console import Console
from rich.table import Table

from aerie_cli.aerie_host import AuthMethod, AerieHostConfiguration
from aerie_cli.persistent import PersistentConfigurationManager, PersistentSessionManager, delete_all_persistent_files, NoActiveSessionError
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
    # Auth-only fields
    if auth_method is not AuthMethod.NONE:
        if auth_url is None:
            auth_url = typer.prompt('URL of Authentication endpoint')
        if username is None:
            username = typer.prompt('Username')

    conf = AerieHostConfiguration(
        name, graphql_url, gateway_url, auth_method, auth_url, username)
    PersistentConfigurationManager.create_configuration(conf)


@app.command('update')
def update_configuration(
    name: str = typer.Option(...,
                             prompt=True, help='Name for this configuration', metavar='NAME'
                             )
):
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
        conf.username = typer.prompt('Username', conf.username)

    PersistentConfigurationManager.update_configuration(conf)


@app.command('activate')
def activate_session(
    name: str = typer.Option(
        None, help='Name for this configuration', metavar='NAME')
):
    if name is None:
        name = select_from_list(
            [c.name for c in PersistentConfigurationManager.configurations])

    conf = PersistentConfigurationManager.get_configuration_by_name(name)

    if conf.auth_method != AuthMethod.NONE:
        password = typer.prompt('Password', hide_input=True)
    else:
        password = None

    session = conf.start_session(password)
    PersistentSessionManager.set_active_session(session)


@app.command('deactivate')
def deactivate_session():
    name = PersistentSessionManager.unset_active_session()
    Console().print(f"Deactivated session: {name}")


@app.command('list')
def list_configurations():

    # Get the name of the active session configuration, if any
    try:
        s = PersistentSessionManager.get_active_session()
        active_config = s.configuration_name
    except NoActiveSessionError:
        active_config = None

    table = Table(title='Aerie Host Configurations',
                  caption='Active configuration in red')
    table.add_column('Host Name', no_wrap=True)
    table.add_column('GraphQL API URL', no_wrap=True)
    table.add_column('Aerie Gateway URL', no_wrap=True)
    table.add_column('Authentication Method', no_wrap=True)
    table.add_column('Username', no_wrap=True)
    for c in PersistentConfigurationManager.configurations:
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
        "", help='Name for this configuration', metavar='NAME', show_default=False)
):
    names = [c.name for c in PersistentConfigurationManager.configurations]
    if not name:
        name = select_from_list(names)

    PersistentConfigurationManager.delete_configuration(name)

    try:
        s = PersistentSessionManager.get_active_session()
        if name == s.configuration_name:
            PersistentSessionManager.unset_active_session()
    except NoActiveSessionError:
        pass


@app.command('uninstall')
def delete_all_files(
    not_interactive: bool = typer.Option(
        False, help='Disable interactive prompt')
):
    # Please don't flame me for this double negative, it had to be done
    if not not_interactive:
        if not typer.confirm("Delete all persistent files associated with aerie-cli? "):
            return

    delete_all_persistent_files()
