import requests
from typing import Dict
import typer
from copy import deepcopy

from plandev_cli.plandev_host import PlanDevHost, PlanDevHostConfiguration, ExternalAuthConfiguration, PlanDevJWT
from plandev_cli.plandev_client import PlanDevClient
from plandev_cli.persistent import PersistentSessionManager

def get_active_session_client():
    """Instantiate PlanDevClient with the active host session

    Raises:
        NoActiveSessionError: if there is no active session

    Returns:
        PlanDevClient
    """
    session = PersistentSessionManager.get_active_session()
    return PlanDevClient(session)


def get_localhost_client() -> PlanDevClient:
    plandev_host = PlanDevHost("http://localhost:8080/v1/graphql", "http://localhost:9000")
    if not plandev_host.check_auth():
        raise RuntimeError(f"Failed to connect to host")
    return PlanDevClient(plandev_host)


def get_preauthenticated_client_native(encoded_jwt: str, graphql_url: str, gateway_url: str) -> PlanDevClient:
    """Get PlanDevClient instance preauthenticated with native PlanDev JWT auth

    Args:
        encoded_jwt (str): base64-encoded PlanDev JWT
        graphql_url (str) 
        gateway_url (str)

    Raises:
        RuntimeError: If connection to PlanDev host fails

    Returns:
        PlanDevClient
    """
    plandev_host = PlanDevHost(graphql_url, gateway_url)
    plandev_host.plandev_jwt = PlanDevJWT(encoded_jwt)
    if not plandev_host.check_auth():
        raise RuntimeError(f"Failed to connect to host")
    return PlanDevClient(plandev_host)


def get_preauthenticated_client_cookie(cookies: dict, encoded_jwt: str, graphql_url: str, gateway_url: str) -> PlanDevClient:
    """Get PlanDevClient instance preauthenticated with an external cookie(s) and JWT

    Args:
        cookies (dict): Browser-style cookies for external authentication
        encoded_jwt (str): base64-encoded PlanDev JWT
        graphql_url (str)
        gateway_url (str)

    Raises:
        RuntimeError: If connection to PlanDev host fails

    Returns:
        PlanDevClient
    """
    session = requests.Session()
    session.cookies = requests.cookies.cookiejar_from_dict(cookies)
    plandev_host = PlanDevHost(graphql_url, gateway_url, session=session)
    plandev_host.plandev_jwt = PlanDevJWT(encoded_jwt)
    if not plandev_host.check_auth():
        raise RuntimeError(f"Failed to connect to host")
    return PlanDevClient(plandev_host)


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
    configuration: PlanDevHostConfiguration,
    username: str = None, 
    password: str = None,
    secret_post_vars: Dict[str, str] = None,
    force: bool = False
):
    """Start and authenticate an PlanDev Host session, with prompts if necessary

    If username is not provided, it will be requested via CLI prompt.

    If password is not provided but the PlanDev instance has authentication enabled, it will be requested via CLI prompt.
    If the PlanDev instance has authentication disabled, a password is not necessary.

    If external authentication is specified in the configuration, `secret_post_vars` can be used to pass in 
    credentials. If external auth is specified with secrets and matching credentials aren't provided, they will be 
    requested via CLI prompt.

    Args:
        configuration (PlanDevHostConfiguration): Configuration of host to connect
        username (str, optional): PlanDev username.
        password (str, optional): PlanDev password.
        secret_post_vars (Dict[str, str], optional): Optionally provide values for some or all secret post request variable values. Defaults to None.
        force (bool, optional): Force connection to PlanDev host and ignore version compatibility. Defaults to False.

    Returns:
        PlanDevHost: 
    """

    if configuration.external_auth is None:
        session = requests.Session()
    else:
        session = authenticate_with_external(configuration.external_auth, secret_post_vars)

    hs = PlanDevHost(
        configuration.graphql_url,
        configuration.gateway_url,
        session,
        configuration.name,
    )

    if username is None:
        if configuration.username is None:
            username = typer.prompt("PlanDev Username")
        else:
            username = configuration.username

    if password is None and hs.is_auth_enabled():
        password = typer.prompt("PlanDev Password", hide_input=True)

    hs.authenticate(username, password, force)

    return hs
