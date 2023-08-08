# Configure persistent session and configuration
# Note that we're setting global variables here rather than using pytest.VARIABLE
# The scope is global either way, but this allows for easier debugging, type hints, and autofill
import os
import sys
import pytest

from aerie_cli.aerie_client import AerieClient
from aerie_cli.aerie_host import AerieHostSession, AuthMethod
from aerie_cli.commands.configurations import delete_all_persistent_files, upload_configurations, deactivate_session, activate_session
from aerie_cli.utils.sessions import get_active_session_client

# in case src_path is not from aeri-cli src and from site-packages
src_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../src")
sys.path.insert(0, src_path)

GRAPHQL_URL = "http://localhost:8080/v1/graphql"
GATEWAY_URL = "http://localhost:9000"
AUTH_URL = "http://localhost:9000/auth/login"
AUTH_METHOD = AuthMethod.AERIE_NATIVE
USERNAME = ""
PASSWORD = ""
# This should only ever be set to the admin secret for a local instance of aerie
HASURA_ADMIN_SECRET = os.environ.get("HASURA_GRAPHQL_ADMIN_SECRET")

session = AerieHostSession.session_helper(
    AUTH_METHOD,
    GRAPHQL_URL,
    GATEWAY_URL,
    AUTH_URL,
    USERNAME,
    PASSWORD
)
session.session.headers["x-hasura-admin-secret"] = HASURA_ADMIN_SECRET
client = AerieClient(session)

DOWNLOADED_FILE_NAME = "downloaded_file.test"

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_PATH = os.path.join(TEST_DIR, "files")

# Configuration Variables
CONFIGURATIONS_PATH = os.path.join(FILES_PATH, "configuration")
CONFIGURATION_PATH = os.path.join(CONFIGURATIONS_PATH, "localhost_config.json")

# Resets the configurations and adds localhost
deactivate_session()
delete_all_persistent_files()
upload_configurations(CONFIGURATION_PATH)
activate_session("localhost")
persisent_client = None
try:
    persisent_client = get_active_session_client()
except:
    raise RuntimeError("Configuration is not active!")
assert persisent_client.host_session.gateway_url == GATEWAY_URL,\
    "Aerie instances are mismatched. Ensure test URLs are the same."