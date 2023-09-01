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
        self.aerie_jwt = None

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
            resp_json = process_hasura_response(resp)
            self.aerie_jwt = AerieJWT(resp_json["token"])
        except (RuntimeError, KeyError):
            raise RuntimeError(f"Failed to select new role")

    def check_auth(self) -> bool:
        """Checks if session is correctly authenticated with Aerie host
        
        Looks for errors received after pinging GATEWAY_URL/auth/session.
        Also returns False if the session has not yet been authenticated (no JWT).

        Returns:
            bool: True if there were no errors in a ping against GATEWAY_URL/auth/session, False otherwise
        """
        if self.aerie_jwt is None:
            return False

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

    def is_auth_enabled(self) -> bool:
        """Check if authentication is enabled on an Aerie host

        Returns:
            bool: False if authentication is disabled, otherwise True
        """
        resp = self.session.get(self.gateway_url + "/auth/user")
        if resp.ok:
            try:
                resp_json = resp.json()
                if (
                    "message" in resp_json.keys()
                    and resp_json["message"] == "Authentication is disabled"
                ):
                    return False
            except requests.exceptions.JSONDecodeError:
                pass

        return True

    def authenticate(self, username: str, password: str = None):

        resp = self.session.post(
            self.gateway_url + "/auth/login",
            json={"username": username, "password": password},
        )

        try:
            resp_json = process_hasura_response(resp)
        except RuntimeError:
            raise RuntimeError("Failed to authenticate")

        self.aerie_jwt = AerieJWT(resp_json["token"])

        if not self.check_auth():
            raise RuntimeError(f"Failed to open session")


@define
class AerieHostConfiguration:  # TODO add proxy information
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
            "username": self.username
        }

        return retval
