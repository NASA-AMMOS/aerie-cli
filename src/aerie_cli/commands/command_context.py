import typer
from aerie_cli.aerie_client import AerieClient
from aerie_cli.utils.sessions import get_active_session_client
from aerie_cli.aerie_host import AerieHostConfiguration

app = typer.Typer()

class CommandContext:
    hasura_admin_secret: str = None
    alternate_configuration: AerieHostConfiguration = None

    def __init__(self) -> None:
        raise NotImplementedError

    @classmethod
    def get_client(cls) -> AerieClient:
        """Get the AerieClient for any command's execution.
        
        Returns:
            AerieClient
        """
        # If the configuration was set in the CLI by the user,
        # then the returned client will be derived from that configuration.
        client = None
        if cls.alternate_configuration != None and client == None:
            session = cls.alternate_configuration.start_session()
            client = AerieClient(session)

        if client == None:
            # no configuration specified in CLI, so the active session will be used instead
            client = get_active_session_client()

        if cls.hasura_admin_secret:
            client.host_session.session.headers["x-hasura-admin-secret"] = cls.hasura_admin_secret

        return client