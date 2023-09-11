import typer
from aerie_cli.aerie_client import AerieClient
from aerie_cli.utils.sessions import get_active_session_client, start_session_from_configuration
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
        If an alternate configuration has been specified, this method will attempt to find the persistent configuration or load a file with that name. If no alternate configuration is specified, then the active session is used.
        Returns:
            AerieClient
        """
        # If the configuration was set in the CLI by the user,
        # then the returned client will be derived from that configuration.
        client = None
        if cls.alternate_configuration != None and client == None:
            session = start_session_from_configuration(cls.alternate_configuration)
            client = AerieClient(session)

        if client == None:
            # no configuration specified in CLI, so the active session will be used instead
            client = get_active_session_client()

        if cls.hasura_admin_secret:
            if client.aerie_host.aerie_jwt is None:
                raise RuntimeError(f"Unauthenticated Aerie session")
            client.aerie_host.session.headers["x-hasura-admin-secret"] = cls.hasura_admin_secret
            client.aerie_host.session.headers["x-hasura-role"] = "aerie_admin"
            client.aerie_host.session.headers["x-hasura-user-id"] = client.aerie_host.aerie_jwt.username

        return client
