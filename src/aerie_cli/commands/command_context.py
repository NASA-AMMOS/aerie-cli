from aerie_cli.aerie_client import AerieClient
import typer
from types import SimpleNamespace

app = typer.Typer()



class CommandContext:
    def __init__(self, hasura_admin_secret: str) -> None:
        self._hasura_admin_secret = hasura_admin_secret
    def get_hasura_admin_secret(self) -> str:
        return self._hasura_admin_secret

class CommandContextManager:
    context: CommandContext = None
    def __init__(self) -> None:
        raise NotImplementedError
        