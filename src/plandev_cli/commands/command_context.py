import typer
from plandev_cli.plandev_client import PlanDevClient
from plandev_cli.utils.sessions import get_active_session_client, start_session_from_configuration
from plandev_cli.plandev_host import PlanDevHostConfiguration

app = typer.Typer()

class CommandContext:
    hasura_admin_secret: str = None
    alternate_configuration: PlanDevHostConfiguration = None

    def __init__(self) -> None:
        raise NotImplementedError

    @classmethod
    def get_client(cls) -> PlanDevClient:
        """Get the PlanDevClient for any command's execution.
        If an alternate configuration has been specified, this method will attempt to find the persistent configuration or load a file with that name. If no alternate configuration is specified, then the active session is used.
        Returns:
            PlanDevClient
        """
        # If the configuration was set in the CLI by the user,
        # then the returned client will be derived from that configuration.
        client = None
        if cls.alternate_configuration != None and client == None:
            session = start_session_from_configuration(cls.alternate_configuration)
            client = PlanDevClient(session)

        if client == None:
            # no configuration specified in CLI, so the active session will be used instead
            client = get_active_session_client()

        if cls.hasura_admin_secret:
            if client.plandev_host.plandev_jwt is None:
                raise RuntimeError(f"Unauthenticated PlanDev session")
            client.plandev_host.session.headers["x-hasura-admin-secret"] = cls.hasura_admin_secret
            client.plandev_host.session.headers["x-hasura-role"] = "aerie_admin"
            client.plandev_host.session.headers["x-hasura-user-id"] = client.plandev_host.plandev_jwt.username

        return client
