import json
from copy import deepcopy
from enum import Enum
from typing import Dict
from typing import Optional

from attrs import define, field

import requests


class AuthMethod(Enum):
    NONE = "None"
    AERIE_NATIVE = "Native"
    COOKIE = "Cookie"

    @classmethod
    def from_string(cls, string_name: str) -> "AuthMethod":
        try:
            return next(filter(lambda x: x.value == string_name, cls))
        except StopIteration:
            raise ValueError(f"Unknown auth method: {string_name}")


class AerieHostSession:
    """
    Encapsulate an authenticated session with an Aerie host.

    An instance stores the necessary URLs and authenticates using header or
    cookie information stored in the `requests.Session` object, if necessary.
    """

    def __init__(
        self,
        session: requests.Session,
        graphql_url: str,
        gateway_url: str,
        configuration_name: str = None,
    ) -> None:
        """

        Args:
            session (requests.Session): HTTP session, with auth headers/cookies if necessary
            graphql_url (str): Route to Aerie host's GraphQL API
            gateway_url (str): Route to Aerie Gateway
            configuration_name (str, optional): Name of configuration for this session
        """
        self.session = session
        self.graphql_url = graphql_url
        self.gateway_url = gateway_url
        self.configuration_name = configuration_name

    def post_to_graphql(self, query: str, **kwargs) -> Dict:
        """Issue a post request to the Aerie instance GraphQL API

        Args:
            query (str): GraphQL query text
            kwargs: keyword arguments for named variables for the query

        Raises:
            RuntimeError

        Returns:
            Dict: Query response data
        """

        try:

            resp = self.session.post(
                self.graphql_url,
                json={"query": query, "variables": kwargs},
            )

            if resp.ok:
                if "errors" in resp.json().keys():
                    err = resp.json()["errors"]
                    for error in err:
                        print(error["message"])
                else:
                    resp_json = resp.json()["data"]
                    data = next(iter(resp_json.values()))

            if data is None:
                raise RuntimeError

            if not resp.ok or (
                resp.ok
                and isinstance(data, dict)
                and "success" in data
                and not data["success"]
            ):
                raise RuntimeError

            return data

        except Exception as e:
            # Re-raise with additional information
            e = str(e)

            if "password" in kwargs:

                # Remove password
                pw_sub_str = "<Password removed in aerie-cli error handling>"
                e.replace(kwargs["password"], pw_sub_str)
                kwargs = deepcopy(kwargs)
                kwargs["password"] = pw_sub_str

                # Raise exception with query, variables, and original exception
                raise RuntimeError(
                    {"query": deepcopy(query), "variables": kwargs, "exception": e}
                )

            else:

                # Decode response text if in JSON-parsable format
                try:
                    resp_contents = json.loads(resp.text)
                except json.decoder.JSONDecodeError:
                    resp_contents = resp.text

                # Raise exception with query, variables, original exception, and response
                raise RuntimeError(
                    json.dumps(
                        {
                            "query": deepcopy(query),
                            "variables": deepcopy(kwargs),
                            "exception": e,
                            "response_text": resp_contents,
                        },
                        indent=2,
                    )
                )

    def post_to_gateway_files(self, file_name: str, file_contents: bytes) -> Dict:
        """Issue a post request to upload a file via the Aerie gateway

        Args:
            file_name (str): Name of the file being uploaded
            file_contents (bytes): File contents

        Raises:
            RuntimeError: Raised if the request receives an error response

        Returns:
            Dist: JSON response
        """

        resp = self.session.post(
            self.gateway_url + "/file", files={"file": (file_name, file_contents)}
        )

        if resp.ok:
            return resp.json()
        else:
            raise RuntimeError(f"Error uploading file: {file_name}")

    def ping_gateway(self) -> bool:

        try:
            resp = self.session.get(self.gateway_url + "/health")
        except requests.exceptions.ConnectionError:
            return False
        try:
            if "uptimeMinutes" in resp.json().keys():
                return True
        except Exception:
            return False

    @classmethod
    def session_helper(
        cls,
        auth_method: AuthMethod,
        graphql_url: str,
        gateway_url: str,
        auth_url: str = None,
        username: str = None,
        password: str = None,
        configuration_name: str = None,
    ) -> "AerieHostSession":
        """Helper function to create a session with an Aerie host

        Args:
            auth_method (AuthMethod): Authentication method to use
            graphql_url (str): Route to Graphql API
            gateway_url (str): Route to Aerie Gateway
            auth_url (str, optional): Route to Authentication endpoint. Ignore if no auth.
            username (str, optional): Username for Authentication. Ignore if no auth.
            password (str, optional): Password for Authentication. Ignore if no auth.
            configuration_name (str, optional): Name of source configuration. Ignore if not instantiating from a config.

        Returns:
            AerieHostSession: HTTP session, with auth headers/cookies if necessary
        """

        session = requests.Session()

        if auth_method is AuthMethod.NONE:
            # If no auth is required, leave the session as-is
            pass

        elif auth_method is AuthMethod.AERIE_NATIVE:
            # For aerie native auth, pass the SSO token in query headers
            resp = session.post(
                auth_url, json={"username": username, "password": password}
            )
            if resp.json()["success"]:
                if "token" in resp.json().keys():
                    token = resp.json().get("token")
                    if token is not None:  # a string token should include prefix
                        token = "Bearer " + token
                    session.headers["x-auth-sso-token"] = token
                else:
                    session.headers["x-auth-sso-token"] = resp.json()["ssoToken"]
            else:
                raise RuntimeError(f"Failed to authenticate at route: {auth_url}")

        elif auth_method is AuthMethod.COOKIE:
            # For cookie auth, simply query the login endpoint w/ credentials which will return the cookie to be stored in the session
            session.post(auth_url, json={"username": username, "password": password})

        else:
            raise RuntimeError(
                f"No logic to generate an Aerie host session for auth method: {auth_method}"
            )

        aerie_session = cls(session, graphql_url, gateway_url, configuration_name)

        if not aerie_session.ping_gateway():
            raise RuntimeError(f"Failed to open session")

        return aerie_session


@define
class AerieHostConfiguration:
    name: str
    graphql_url: str
    gateway_url: str
    auth_method: AuthMethod
    auth_url: str = None
    username: Optional[str] = field(
        default=None
    )

    @classmethod
    def from_dict(cls, config: Dict) -> "AerieHostConfiguration":
        try:
            name = config["name"]
            graphql_url = config["graphql_url"]
            gateway_url = config["gateway_url"]
            auth_method = AuthMethod.from_string(config["auth_method"])

            if auth_method == AuthMethod.NONE:
                auth_url = None
                username = None
            else:
                auth_url = config["auth_url"]
                if "username" in config.keys():
                    username = config["username"]
                else:
                    username = None

        except KeyError as e:
            raise ValueError(f"Configuration missing required field: {e.args[0]}")

        return cls(name, graphql_url, gateway_url, auth_method, auth_url, username)

    def to_dict(self) -> Dict:
        retval = {
            "name": self.name,
            "graphql_url": self.graphql_url,
            "gateway_url": self.gateway_url,
            "auth_method": self.auth_method.value,
        }

        if self.auth_method != AuthMethod.NONE:
            retval["auth_url"] = self.auth_url
            retval["username"] = self.username

        return retval

    def start_session(self, username=None, password: str = None) -> AerieHostSession:
        """Start an Aerie host session from this configuration

        Args:
            username (str, optional): Override stored username. Defaults to None.
            password (str, optional): Provide a password, if necessary. Defaults to None.

        Returns:
            AerieHostSession
        """
        return AerieHostSession.session_helper(
            self.auth_method,
            self.graphql_url,
            self.gateway_url,
            self.auth_url,
            username if username else self.username,
            password,
            self.name,
        )
