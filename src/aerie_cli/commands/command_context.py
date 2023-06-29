import typer
from aerie_cli.aerie_client import AerieClient
from aerie_cli.utils.sessions import get_active_session_client

app = typer.Typer()

class CommandContext:
    hasura_admin_secret = None
    def __init__(self) -> None:
        raise NotImplementedError

    @classmethod
    def get_client(cls) -> AerieClient:
        client = get_active_session_client()
        if CommandContext.hasura_admin_secret:
            client.host_session.session.headers["x-hasura-admin-secret"] = CommandContext.hasura_admin_secret
        return client