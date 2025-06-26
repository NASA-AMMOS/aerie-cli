# Configure persistent session and configuration
# Note that we're setting global variables here rather than using pytest.VARIABLE
# The scope is global either way, but this allows for easier debugging, type hints, and autofill
import os
import sys
import shutil
import inspect

from typer.testing import CliRunner

from aerie_cli.aerie_host import AerieHostConfiguration
from aerie_cli.commands.configurations import (
    delete_all_persistent_files,
    upload_configurations,
)
from aerie_cli.app import deactivate_session
from aerie_cli.persistent import PersistentConfigurationManager, PersistentSessionManager
from aerie_cli.utils.sessions import (
    get_active_session_client,
    start_session_from_configuration,
)

# in case src_path is not from aeri-cli src and from site-packages
src_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../src")
sys.path.insert(0, src_path)

# Configuration values mirror those in the test file localhost_config.json
GRAPHQL_URL = "http://localhost:8080/v1/graphql"
GATEWAY_URL = "http://localhost:9000"
USERNAME = "a"
PASSWORD = "a"
ANONYMOUS_LOCALHOST_CONF = AerieHostConfiguration("localhost", GRAPHQL_URL, GATEWAY_URL)

# Additional usernames to register with Aerie
ADDITIONAL_USERS = ["user1", "user2", "user3"]

# This should only ever be set to the admin secret for a local instance of aerie
HASURA_ADMIN_SECRET = os.environ.get("HASURA_GRAPHQL_ADMIN_SECRET")

# Test constants
DOWNLOADED_FILE_NAME = "downloaded_file.test"
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_PATH = os.path.join(TEST_DIR, "files")
ARTIFACTS_PATH = os.path.join(TEST_DIR, "artifacts")
CONFIGURATIONS_PATH = os.path.join(FILES_PATH, "configuration")
CONFIGURATION_PATH = os.path.join(CONFIGURATIONS_PATH, "localhost_config.json")
MODELS_PATH = os.path.join(FILES_PATH, "models")
MODEL_VERSION = os.environ.get("AERIE_VERSION", "3.2.0")
MODEL_JAR = os.path.join(MODELS_PATH, f"banananation-{MODEL_VERSION}.jar")
MODEL_NAME = "banananation"
MODEL_VERSION = "0.0.1"

def get_test_runner():
    kwargs = {}
    if "mix_stderr" in inspect.signature(CliRunner).parameters:
        # click < 8.2
        kwargs["mix_stderr"] = False
    return CliRunner(**kwargs)
RUNNER = get_test_runner()

# Clean any old artifacts and create folder
if os.path.exists(ARTIFACTS_PATH):
    shutil.rmtree(ARTIFACTS_PATH)
os.mkdir(ARTIFACTS_PATH)

# Login to add additional users to the `users` table
for username in ADDITIONAL_USERS:
    start_session_from_configuration(
        ANONYMOUS_LOCALHOST_CONF,
        username
    )

# Resets the configurations and adds localhost
deactivate_session()
delete_all_persistent_files()
upload_configurations(CONFIGURATION_PATH)

# Login as the main username, set role, and store session as persistent
localhost_conf = PersistentConfigurationManager.get_configuration_by_name("localhost")
aerie_host = start_session_from_configuration(localhost_conf, USERNAME, PASSWORD)
aerie_host.change_role("aerie_admin")
PersistentSessionManager.set_active_session(aerie_host)

client = None
try:
    client = get_active_session_client()
except:
    raise RuntimeError("Configuration is not active!")
assert (
    client.aerie_host.gateway_url == GATEWAY_URL
), "Aerie instances are mismatched. Ensure test URLs are the same."
