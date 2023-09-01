import requests
import typer

from aerie_cli.aerie_host import AerieHostSession, AerieHostConfiguration
from aerie_cli.aerie_client import AerieClient
from aerie_cli.persistent import PersistentSessionManager

def get_active_session_client():
    """Instantiate AerieClient with the active host session

    Raises:
        NoActiveSessionError: if there is no active session

    Returns:
        AerieClient
    """
    session = PersistentSessionManager.get_active_session()
    return AerieClient(session)


def get_localhost_client() -> AerieClient:
    session = requests.Session()
    aerie_session = AerieHostSession(
        session, "http://localhost:8080/v1/graphql", "http://localhost:9000")
    if not aerie_session.ping_gateway():
        raise RuntimeError(f"Failed to connect to host")
    return AerieClient(aerie_session)


def get_preauthenticated_client_native(sso_token: str, graphql_url: str, gateway_url: str) -> AerieClient:
    """Get AerieClient instance preauthenticated with native Aerie SSO auth

    Args:
        sso_token (str): SSO Token for Aerie authentication
        graphql_url (str) 
        gateway_url (str)

    Raises:
        RuntimeError: If connection to Aerie host fails

    Returns:
        AerieClient
    """
    session = requests.Session()
    session.headers['x-auth-sso-token'] = sso_token
    aerie_session = AerieHostSession(session, graphql_url, gateway_url)
    if not aerie_session.ping_gateway():
        raise RuntimeError(f"Failed to connect to host")
    return AerieClient(aerie_session)


def get_preauthenticated_client_cookie(cookie_name: str, cookie_value: str, graphql_url: str, gateway_url: str) -> AerieClient:
    """Get AerieClient instance preauthenticated with a cookie

    Args:
        cookie_name (str): Name of cookie
        cookie_value (str): Value of cookie
        graphql_url (str)
        gateway_url (str)

    Raises:
        RuntimeError: If connection to Aerie host fails

    Returns:
        AerieClient
    """
    session = requests.Session()
    session.cookies = requests.cookies.cookiejar_from_dict(
        {cookie_name: cookie_value})
    aerie_session = AerieHostSession(session, graphql_url, gateway_url)
    if not aerie_session.ping_gateway():
        raise RuntimeError(f"Failed to connect to host")
    return AerieClient(aerie_session)

def start_session_from_configuration(
    configuration: AerieHostConfiguration, username: str = None, password: str = None
):
    """Start and authenticate an Aerie Host session, with prompts if necessary

    If username is not provided, it will be requested via CLI prompt.

    If password is not provided but the Aerie instance has authentication enabled, it will be requested via CLI prompt.
    If the Aerie instance has authentication disabled, a password is not necessary.

    Args:
        configuration (AerieHostConfiguration): Configuration of host to connect
        username (str, optional): Aerie username.
        password (str, optional): Aerie password.

    Returns:
        AerieHostSession: 
    """

    hs = AerieHostSession(
        requests.Session(),
        configuration.graphql_url,
        configuration.gateway_url,
        configuration.name,
    )

    if configuration.username is None:
        username = typer.prompt("Username")
    else:
        username = configuration.username

    if password is None and hs.is_auth_enabled():
        password = typer.prompt("Password", hide_input=True)

    hs.authenticate(username, password)

    return hs
