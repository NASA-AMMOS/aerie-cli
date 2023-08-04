# in case src_path is not from aeri-cli src and from site-packages
import os
import sys

import pytest

src_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../src")
sys.path.insert(0, src_path)

from typer.testing import CliRunner

from aerie_cli.aerie_client import AerieClient
from aerie_cli.aerie_host import AerieHostSession, AuthMethod
from aerie_cli.__main__ import app
from aerie_cli.commands.configurations import delete_all_persistent_files, upload_configurations, deactivate_session, activate_session
from aerie_cli.utils.sessions import get_active_session_client
from aerie_cli.commands import plans

runner = CliRunner(mix_stderr = False)

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

test_dir = os.path.dirname(os.path.abspath(__file__))

# Configuration Variables
config_json = os.path.join(test_dir, "files/configuration/localhost_config.json")

# Model Variables
model_jar = os.path.join(test_dir, "files/models/banananation-1.6.2.jar")
model_name = "banananation"
version = "0.0.1"
model_id = 0

# Plan Variables
plan_json = os.path.join(test_dir, "files/plans/bake_bread_plan.json")
dup_plan_name = os.path.join(test_dir, "files/plans/bake_bread_plan_2.json")
plan_id = 0
args_init = os.path.join(test_dir, "files/plans/create_config.json")
args_update = os.path.join(test_dir, "files/plans/update_config.json")

@pytest.fixture(scope="session", autouse=True)
def set_up_environment(request):
    # Resets the configurations and adds localhost
    deactivate_session()
    delete_all_persistent_files()
    upload_configurations(config_json)
    activate_session("localhost")
    client = None
    try:
        client = get_active_session_client()
    except:
        raise RuntimeError("Configuration is not active!")
    assert client.host_session.gateway_url == GATEWAY_URL,\
        "Aerie instances are mismatched. Ensure test URLs are the same."

def test_model_clean():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "models", "clean"],
        catch_exceptions=False,
        )
    assert result.exit_code == 0
    assert (
        f"All mission models have been deleted"
        in result.stdout
    )

def cli_upload_banana_model():
    return runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "models", "upload", "--time-tag-version"],
        input=model_jar 
        + "\n"
        + model_name
        + "\n"
        + version
        + "\n",
        catch_exceptions=False,
    )

def test_model_upload():
    result = cli_upload_banana_model()

    # Get model_id of uploaded mission model
    resp = client.get_mission_models()
    latest_model = resp[-1]
    global model_id
    model_id = latest_model.id

    assert result.exit_code == 0
    assert (
        f"Created new mission model: {model_name} with Model ID: {model_id}"
        in result.stdout
    )

def test_model_list():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "models", "list"],
        catch_exceptions=False,)
    assert result.exit_code == 0
    assert "Current Mission Models" in result.stdout

def test_plan_upload():
    # Clean out plans first
    plans.clean()
    # Upload mission model for setup
    result = cli_upload_banana_model()
    
    # Get model_id of uploaded mission model
    resp = client.get_mission_models()
    latest_model = resp[-1]
    global model_id
    model_id = latest_model.id

    # Test plan upload
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "plans", "upload", "--time-tag"],
        input=plan_json + "\n" + str(model_id) + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    
    # Get uploaded plan id
    resp = client.get_all_activity_plans()
    latest_plan = resp[-1]
    global plan_id
    plan_id = latest_plan.id

    assert f"Created plan ID: {plan_id}" in result.stdout




def test_plan_duplicate():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "plans", "duplicate"],
        input=str(plan_id) + "\n" + dup_plan_name + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    # Get duplicated plan id
    resp = client.get_all_activity_plans()
    latest_plan = resp[-1]
    duplicated_plan_id = latest_plan.id

    assert f"Duplicate activity plan created with ID: {duplicated_plan_id}" in result.stdout


def test_plan_list():
    result = runner.invoke(app, ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "plans", "list"],
                                   catch_exceptions=False,)
    assert result.exit_code == 0
    assert "Current Activity Plans" in result.stdout


def test_plan_simulate():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "plans", "simulate", "--output", "temp.json"],
        input=str(plan_id) + "\n",
        catch_exceptions=False
    )
    assert result.exit_code == 0
    assert f"Simulation completed" in result.stdout


def test_plan_create_config():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "plans", "create-config"],
        input=str(plan_id) + "\n" + args_init + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert f"Configuration Arguments for Plan ID: {plan_id}" in result.stdout
    assert "foo: arg1" in result.stdout
    assert "num: 5" in result.stdout


def test_plan_update_config():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "plans", "update-config"],
        input=str(plan_id) + "\n" + args_update + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0
    assert f"Configuration Arguments for Plan ID: {plan_id}" in result.stdout
    assert "foo: arg2" in result.stdout
    assert "num: 5" in result.stdout


def test_plan_delete():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "plans", "delete"],
        input=str(plan_id) + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0
    assert f"ID: {plan_id} has been removed." in result.stdout


def test_plan_clean():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "plans", "clean"],
        catch_exceptions=False,)
    assert result.exit_code == 0
    assert (
        f"All activity plans have been deleted"
        in result.stdout
    )

def test_model_delete():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "models", "delete"],
        input=str(model_id),
        catch_exceptions=False,)
    assert result.exit_code == 0
    assert f"ID: {model_id} has been removed" in result.stdout