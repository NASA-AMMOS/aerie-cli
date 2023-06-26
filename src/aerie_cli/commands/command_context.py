import typer

app = typer.Typer()

class CommandContext:
    hasura_admin_secret = None
    def __init__(self) -> None:
        raise NotImplementedError
        