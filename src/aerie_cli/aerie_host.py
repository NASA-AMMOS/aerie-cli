from copy import deepcopy
from typing import Dict
from enum import Enum
import requests
import json

class AuthMethod(Enum):
    NONE = 'None'
    AERIE_NATIVE = 'Native'
    COOKIE = 'Cookie'


class AerieHostSession:
    """
    Encapsulate an authenticated session with an Aerie host.

    An instance stores the necessary URLs and authenticates using header or 
    cookie information stored in the `requests.Session` object, if necessary.
    """

    def __init__(self, session: requests.Session, graphql_url: str, gateway_url: str) -> None:
        """

        Args:
            session (requests.Session): HTTP session, with auth headers/cookies if necessary
            graphql_url (str): Route to Aerie host's GraphQL API
            gateway_url (str): Route to Aerie Gateway
        """
        self.session: session
        self.graphql_url: graphql_url
        self.gateway_url: gateway_url

    def post_to_graphql(self, query: str, **variables) -> Dict:
        """Issue a post request to the Aerie instance GraphQL API

        Args:
            query (str): GraphQL query text
            variables: keyword arguments for named variables for the query
        
        Raises:
            RuntimeError

        Returns:
            Dict: Query response data
        """

        try:

            resp = self.session.post(
                self.graphql_url,
                json={"query": query, "variables": variables}
            )

            if resp.ok:
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

            if "password" in kwargs:

                e = str(e)

                # Remove password
                pw_sub_str = "<Password removed in aerie-cli error handling>"
                e.replace(kwargs["password"], pw_sub_str)
                kwargs = deepcopy(kwargs)
                kwargs["password"] = pw_sub_str

                # Raise exception with query, variables, and original exception
                raise RuntimeError({
                    "query": deepcopy(query),
                    "variables": kwargs,
                    "exception": str(e)
                })

            else:

                # Decode response text if in JSON-parsable format
                try:
                    resp_contents = json.loads(resp.text)
                except json.decoder.JSONDecodeError:
                    resp_contents = resp.text

                # Raise exception with query, variables, original exception, and response
                raise RuntimeError(json.dumps({
                    "query": deepcopy(query),
                    "variables": deepcopy(kwargs),
                    "exception": e,
                    "response_text": resp_contents
                }, indent=2))

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
            files={"file": (file_name, file_contents)}
        )

        if resp.ok:
            return resp.json()
        else:
            raise RuntimeError(f"Error uploading file: {file_name}")

    @classmethod
    def session_helper(
        cls,
        auth_method: AuthMethod,
        graphql_url: str,
        gateway_url: str,
        auth_url: str = None,
        username: str = None,
        password: str = None
    ) -> 'AerieHostSession':
        """Helper function to create a session with an Aerie host

        Args:
            auth_method (AuthMethod): Authentication method to use
            graphql_url (str): Route to Graphql API
            gateway_url (str): Route to Aerie Gateway
            auth_url (str, optional): Route to Authentication endpoint. Ignore if no auth.
            username (str, optional): Username for Authentication. Ignore if no auth.
            password (str, optional): Password for Authentication. Ignore if no auth.

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
                auth_url, json={'username': username, 'password': password})
            if resp.json()["success"]:
                session.headers['x-auth-sso-token'] = resp.json()['ssoToken']
            else:
                raise RuntimeError(
                    f"Failed to authenticate at route: {auth_url}")

        elif auth_method is AuthMethod.COOKIE:
            # For cookie auth, simply query the login endpoint w/ credentials which will return the cookie to be stored in the session
            session.post(
                auth_url, json={'username': username, 'password': password})

        else:
            raise RuntimeError(
                f"No logic to generate an Aerie host session for auth method: {auth_method}")

        return cls(session, graphql_url, gateway_url)

