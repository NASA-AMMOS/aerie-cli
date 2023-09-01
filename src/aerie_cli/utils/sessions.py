import requests
from typing import Dict
import typer
from copy import deepcopy

from aerie_cli.aerie_host import AerieHostSession, AerieHostConfiguration, ExternalAuthConfiguration
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


def authenticate_with_external(
    configuration: ExternalAuthConfiguration, secret_post_vars: Dict[str, str] = None
) -> requests.Session:
    """Authenticate requests.Session object with an external service

    Send a post request with static and secret variables defined in `configuration` to `auth_url`.
    Cookies returned from the request are stored in the returned requests.Session object.

    Args:
        configuration (ProxyConfiguration): Proxy server configuration
        secret_post_vars (Dict[str, str], optional): Optionally provide values for some or all secret post request variable values. Defaults to None.

    Raises:
        RuntimeError: Failure to authenticate with proxy

    Returns:
        requests.Session: Session with any cookies acquired for proxy authentication
    """

    session = requests.Session()

    post_vars = deepcopy(configuration.static_post_vars)

    if secret_post_vars is None:
        secret_post_vars = {}

    for secret_var_name in configuration.secret_post_vars:
        if secret_var_name in secret_post_vars.keys():
            post_vars[secret_var_name] = secret_post_vars[secret_var_name]
        else:
            post_vars[secret_var_name] = typer.prompt(f"External authentication - {secret_var_name}", hide_input=True)

    resp = session.post(configuration.auth_url, json=post_vars)

    if not resp.ok:
        raise RuntimeError(
            f"Failed to authenticate with proxy: {configuration.auth_url}"
        )

    return session


def start_session_from_configuration(
    configuration: AerieHostConfiguration, 
    username: str = None, 
    password: str = None,
    secret_post_vars: Dict[str, str] = None
):
    """Start and authenticate an Aerie Host session, with prompts if necessary

    If username is not provided, it will be requested via CLI prompt.

    If password is not provided but the Aerie instance has authentication enabled, it will be requested via CLI prompt.
    If the Aerie instance has authentication disabled, a password is not necessary.

    If external authentication is specified in the configuration, `secret_post_vars` can be used to pass in 
    credentials. If external auth is specified with secrets and matching credentials aren't provided, they will be 
    requested via CLI prompt.

    Args:
        configuration (AerieHostConfiguration): Configuration of host to connect
        username (str, optional): Aerie username.
        password (str, optional): Aerie password.
        secret_post_vars (Dict[str, str], optional): Optionally provide values for some or all secret post request variable values. Defaults to None.

    Returns:
        AerieHostSession: 
    """

    if configuration.external_auth is None:
        session = requests.Session()
    else:
        session = authenticate_with_external(configuration.external_auth, secret_post_vars)

    hs = AerieHostSession(
        session,
        configuration.graphql_url,
        configuration.gateway_url,
        configuration.name,
    )

    if configuration.username is None:
        username = typer.prompt("Aerie Username")
    else:
        username = configuration.username

    if password is None and hs.is_auth_enabled():
        password = typer.prompt("Aerie Password", hide_input=True)

    hs.authenticate(username, password)

    return hs
