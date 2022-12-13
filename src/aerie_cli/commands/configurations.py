import typer
from rich.console import Console
from rich.table import Table

from aerie_cli.aerie_client import AerieClient
from aerie_cli.aerie_host import AuthMethod, AerieHostSession

app = typer.Typer()


@app.command('create')
def create_configuration(
    name: str = typer.Option(...,
        prompt=True, help='Name for this configuration', metavar='NAME'
    ),
    graphql_url: str = typer.Option(...,
        prompt=True, help='URL of GraphQL API endpoint', metavar='GRAPHQL_URL'
    ),
    gateway_url: str = typer.Option(...,
        prompt=True, help='URL of Aerie Gateway', metavar='GATEWAY_URL'
    ),
    auth_method: AuthMethod = typer.Option(
        AuthMethod.NONE, prompt=True, help='Authentication method', 
        case_sensitive=False, show_default='None'
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
            auth_url = typer.prompt('URL of Authentication endpoint: ')
        if username is None:
            username = typer.prompt('Username: ')
    
    pass

    # TODO store the configuration


@app.command('update')
def update_configuration(
    name: str = typer.Option(...,
        prompt=True, help='Name for this configuration', metavar='NAME'
    )
):

    # TODO get configuration values
    # TODO for each config value, issue a prompt with the default value populated
    # TODO overwrite the config
    pass

@app.command('select')
def select_configuration(
    name: str = typer.Option(...,
        prompt=True, help='Name for this configuration', metavar='NAME'
    )
):
    # TODO select configuration
    pass

@app.command('list')
def list_configurations():
    # TODO list configurations and print the route to the source JSON configuration file
    pass

@app.command('delete')
def delete_configuration(
    name: str = typer.Option(...,
        prompt=True, help='Name for this configuration', metavar='NAME'
    )
):
    # TODO delete the configuration
    pass
