import typer
from aerie_cli.aerie_client import AerieClient
from aerie_cli.utils.sessions import get_active_session_client
from aerie_cli.aerie_host import AerieHostConfiguration

app = typer.Typer()

class CommandContext:
    hasura_admin_secret: str = None
    alternate_configuration: AerieHostConfiguration = None
    __client: AerieClient = None

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
        if cls.alternate_configuration != None and cls.__client == None:
            session = cls.alternate_configuration.start_session()
            cls.__client = AerieClient(session)

        if cls.__client == None:
            # no configuration specified in CLI, so the active session will be used instead
            cls.__client = get_active_session_client()

        if cls.hasura_admin_secret:
            cls.__client.host_session.session.headers["x-hasura-admin-secret"] = cls.hasura_admin_secret

        return cls.__client