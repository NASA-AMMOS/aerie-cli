import json
import requests
from copy import deepcopy
from typing import Dict
from typing import Optional
from base64 import b64decode

from attrs import define, field


def process_hasura_response(resp: requests.Response) -> dict:
    """Throw a RuntimeError if the Hasura response is malformed or contains errors

    Args:
        resp (requests.Response): Response from a Hasura request

    Returns:
        dict: Contents of response JSON
    """
    if not resp.ok:
        raise RuntimeError(f"Bad response from Hasura.")

    try:
        resp_json = resp.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError(f"Failed to get response JSON")

    if "errors" in resp_json.keys():
        raise RuntimeError(f"GraphQL Error: {json.dumps(resp_json['errors'])}")
    elif "success" in resp_json.keys() and not resp_json["success"]:
        raise RuntimeError(f"Hasura request was not successful")

    return resp_json


class AerieJWT:
    def __init__(self, encoded_jwt: str) -> None:
        jwt_components = encoded_jwt.split(".")
        if not len(jwt_components) == 3:
            raise ValueError(f"Invalid JWT: {encoded_jwt}")

        encoded_jwt_payload = b64decode(jwt_components[1] + "==", validate=False)
        try:
            payload = json.loads(encoded_jwt_payload)
            self.active_role = payload["activeRole"]
            self.allowed_roles = payload["https://hasura.io/jwt/claims"][
                "x-hasura-allowed-roles"
            ]

        except KeyError:
            raise ValueError(f"Missing fields in JWT: {encoded_jwt}")

        except json.decoder.JSONDecodeError:
            raise ValueError(f"Cannot decode JWT: {encoded_jwt}")

        self.encoded_jwt = encoded_jwt


class AerieHostSession:
    """
    Encapsulate an authenticated session with an Aerie host.

    An instance stores the necessary URLs and authenticates using header or
    cookie information stored in the `requests.Session` object, if necessary.
    """

    def __init__(
        self,
        session: requests.Session,
        aerie_jwt: AerieJWT,
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
        self.aerie_jwt = aerie_jwt
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
                headers=self.get_auth_headers(),
            )

            if resp.ok:
                try:
                    resp_json = resp.json()
                except json.decoder.JSONDecodeError:
                    raise RuntimeError(f"Failed to process response")

                if "success" in resp_json.keys() and not resp_json["success"]:
                    raise RuntimeError("GraphQL request was not successful")
                elif "errors" in resp_json.keys():
                    raise RuntimeError(
                        f"GraphQL Error: {json.dumps(resp_json['errors'])}"
                    )
                else:
                    data = next(iter(resp.json()["data"].values()))

            if data is None:
                raise RuntimeError(f"Failed to process response: {resp}")

            return data

        except RuntimeError as e:
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
            self.gateway_url + "/file",
            files={"file": (file_name, file_contents)},
            headers=self.get_auth_headers(),
        )

        if resp.ok:
            return resp.json()
        else:
            raise RuntimeError(f"Error uploading file: {file_name}")

    def change_role(self, new_role: str) -> None:
        """Change role for Aerie interaction

        Args:
            new_role (str): String name of new role.
        """

        if new_role not in self.aerie_jwt.allowed_roles:
            raise ValueError(
                f"Cannot set role {new_role}. Must be one of: {', '.join(self.aerie_jwt.allowed_roles)}"
            )

        resp = self.session.post(
            self.gateway_url + "/auth/changeRole",
            json={"role": new_role},
            headers=self.get_auth_headers(),
        )

        try:
            resp_json = resp.json()
        except json.decoder.JSONDecodeError:
            raise RuntimeError(f"Bad response")

        if "success" in resp_json.keys() and resp_json["success"]:
            try:
                self.aerie_jwt = AerieJWT(resp_json["token"])
            except KeyError:
                raise RuntimeError
        else:
            raise RuntimeError(f"Failed to select new role")

    def check_auth(self) -> bool:
        """Checks if authentication was successful. Looks for errors received after pinging GATEWAY_URL/auth/session.

        Returns:
            bool: True if there were no errors in a ping against GATEWAY_URL/auth/session, False otherwise
        """
        try:
            resp = self.session.get(
                self.gateway_url + "/auth/session", headers=self.get_auth_headers()
            )
        except requests.exceptions.ConnectionError:
            return False
        try:
            return resp.json()["success"]
        except Exception:
            return False

    def get_auth_headers(self):
        return {
            "Authorization": f"Bearer {self.aerie_jwt.encoded_jwt}",
            "x-hasura-role": self.aerie_jwt.active_role,
        }

    @classmethod
    def session_helper(
        cls,
        session: requests.Session,
        graphql_url: str,
        gateway_url: str,
        username: str,
        password: str = None,
        configuration_name: str = None,
    ) -> "AerieHostSession":
        """Helper function to create a session with an Aerie host

        Args:
            session: (requests.Session): Browser-like session authenticated to make requests against the Aerie instance
            graphql_url (str): Route to Graphql API
            gateway_url (str): Route to Aerie Gateway
            username (str): Username with Aerie
            password (str, optional): Password for Authentication. Ignore if authentication is disabled.
            configuration_name (str, optional): Name of source configuration. Ignore if not instantiating from a config.

        Returns:
            AerieHostSession: Client-side abstraction for authenticated interactions with Aerie
        """

        # # Check if authentication is enabled on this Aerie host
        # resp = session.get(gateway_url + "/auth/user")
        # auth_enabled = True
        # if resp.ok:
        #     try:
        #         resp_json = resp.json()
        #         if resp_json["message"] == "Authentication is disabled":
        #             auth_enabled = False
        #     except (json.decoder.JSONDecodeError, KeyError):
        #         pass

        # if auth_enabled:

        resp = session.post(
            gateway_url + "/auth/login",
            json={"username": username, "password": password},
        )

        if resp.ok:
            resp_json = resp.json()
        else:
            raise RuntimeError(f"Bad request. Response: {resp}")

        if not resp_json["success"]:
            raise ValueError(f"Failed to authenticate")

        aerie_jwt = AerieJWT(resp_json["token"])

        aerie_session = cls(
            session, aerie_jwt, graphql_url, gateway_url, configuration_name
        )

        if not aerie_session.check_auth():
            raise RuntimeError(f"Failed to open session")

        return aerie_session


@define
class AerieHostConfiguration:  # TODO add proxy information; make password optional?
    name: str
    graphql_url: str
    gateway_url: str
    username: Optional[str] = field(default=None)

    @classmethod
    def from_dict(cls, config: Dict) -> "AerieHostConfiguration":
        try:
            name = config["name"]
            graphql_url = config["graphql_url"]
            gateway_url = config["gateway_url"]
            if "username" in config.keys():
                username = config["username"]
            else:
                username = None

        except KeyError as e:
            raise ValueError(f"Configuration missing required field: {e.args[0]}")

        return cls(name, graphql_url, gateway_url, username)

    def to_dict(self) -> Dict:
        retval = {
            "name": self.name,
            "graphql_url": self.graphql_url,
            "gateway_url": self.gateway_url,
        }

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
            requests.Session(),
            self.graphql_url,
            self.gateway_url,
            username if username else self.username,
            password,
            self.name,
        )
