# in case src_path is not from aeri-cli src and from site-packages
import os
import sys

src_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../src")
sys.path.insert(0, src_path)

from typer.testing import CliRunner

from aerie_cli.aerie_client import AerieClient
from aerie_cli.aerie_host import AerieHostSession, AuthMethod
from aerie_cli.__main__ import app

runner = CliRunner(mix_stderr = False)

GRAPHQL_URL = "http://localhost:8080/v1/graphql"
GATEWAY_URL = "http://localhost:9000"
AUTH_URL = "http://localhost:9000/auth/login"
AUTH_METHOD = AuthMethod.AERIE_NATIVE
USERNAME = ""
PASSWORD = ""

session = AerieHostSession.session_helper(
    AUTH_METHOD,
    GRAPHQL_URL,
    GATEWAY_URL,
    AUTH_URL,
    USERNAME,
    PASSWORD
)
session.session.headers["x-hasura-admin-secret"] = "aerie"
client = AerieClient(session)

test_dir = os.path.dirname(os.path.abspath(__file__))

# Model Variables
model_jar = os.path.join(test_dir, "files/models/banananation.jar")
model_name = "banananation"
version = "0.0.1"

# Plan Variables
plan_json = "files/empty-2day-plan.json"
dup_plan_name = "empty-2day-plan-v2.json"
plan_id = 0
args_init = "files/args1.json"
args_update = "files/args2.json"


def test_model_upload():
    result = runner.invoke(
        app,
        ["--hasura-admin-secret", "aerie", "models", "upload", "--time-tag-version"],
        input=model_jar 
        + "\n"
        + model_name
        + "\n"
        + version
        + "\n",
        catch_exceptions=False
    )

    # Get model_id of uploaded mission model
    resp = client.get_mission_models()
    latest_model = resp[-1]
    global model_id
    model_id = latest_model.id

    assert result.exit_code == 0, \
        f"\nOutput was: \n\n{result.stdout}"\
        f"\nError was: \n\n {result.stderr}"
    assert (
        f"Created new mission model: {model_name} with Model ID: {model_id}"
        in result.stdout
    )


def test_model_delete():
    result = runner.invoke(app, ["delete"], input=str(model_id))
    assert result.exit_code == 0
    assert f"ID: {model_id} has been removed" in result.stdout


def test_model_list():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Current Mission Models" in result.stdout


def test_model_clean():
    result = runner.invoke(app, ["clean"])
    assert result.exit_code == 0
    assert (
        f"All mission models at {client.ui_models_path()} have been deleted"
        in result.stdout
    )


def test_plan_upload():
    # Upload mission model for setup
    runner.invoke(
        app,
        ["upload", "--time-tag-version"],
        input=model_jar
        + "\n"
        + model_name
        + "\n"
        + version
        + "\n"
       ,
    )

    # Get model_id of uploaded mission model
    resp = client.get_mission_models()
    latest_model = resp[-1]
    global model_id
    model_id = latest_model.id

    # Test plan upload
    result = runner.invoke(
        app,
        ["upload", "--time-tag"],
        input=plan_json + "\n" + str(model_id) + "\n",
    )

    # Get uploaded plan id
    resp = client.get_all_activity_plans()
    latest_plan = resp[-1]
    global plan_id
    plan_id = latest_plan.id

    assert result.exit_code == 0
    assert f"Created plan at: {client.ui_path()}/plans/" in result.stdout


def test_plan_duplicate():
    result = runner.invoke(
        app,
        ["duplicate"],
        input=str(plan_id) + "\n" + dup_plan_name + "\n",
    )
    assert result.exit_code == 0
    assert f"Duplicated activity plan at: {client.ui_path()}/plans/" in result.stdout


def test_plan_list():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Current Activity Plans" in result.stdout


def test_plan_simulate():
    result = runner.invoke(
        app,
        ["simulate", "--output", "temp.json"],
        input=str(plan_id) + "\n",
        catch_exceptions=False
    )
    assert result.exit_code == 0
    assert f"Simulating activity plan at: {client.ui_path()}/plans/{plan_id}"in result.stdout


def test_plan_create_config():
    result = runner.invoke(
        app,
        ["create-config"],
        input=str(plan_id) + "\n" + args_init + "\n",
    )
    assert result.exit_code == 0
    assert f"Configuration Arguments for Plan ID: {plan_id}" in result.stdout
    assert "foo: arg1" in result.stdout
    assert "num: 5" in result.stdout


def test_plan_update_config():
    result = runner.invoke(
        app,
        ["update-config"],
        input=str(plan_id) + "\n" + args_update + "\n",
    )
    assert result.exit_code == 0
    assert f"Configuration Arguments for Plan ID: {plan_id}" in result.stdout
    assert "foo: arg2" in result.stdout
    assert "num: 5" in result.stdout


def test_plan_delete():
    result = runner.invoke(app, ["delete"], input=str(plan_id) + "\n")
    assert result.exit_code == 0
    assert f"ID: {plan_id} has been removed." in result.stdout


def test_plan_clean():
    result = runner.invoke(app, ["clean"])
    assert result.exit_code == 0
    assert (
        f"All activity plans have been deleted"
        in result.stdout
    )
