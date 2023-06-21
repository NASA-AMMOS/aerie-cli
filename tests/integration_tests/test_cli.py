# in case src_path is not from aeri-cli src and from site-packages
import os
import sys

src_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../src")
sys.path.insert(0, src_path)

from typer.testing import CliRunner

from aerie_cli.aerie_client import auth_helper
from aerie_cli.commands.models import app as m_app
from aerie_cli.commands.plans import app as p_app

runner = CliRunner()

sso = "sso"
username = ""
password = ""
server_url = "http://localhost"
client = auth_helper(
    sso=sso, username=username, password=password, server_url=server_url
)

# Model Variables
model_jar = "TODO"
model_name = "data-simple"
mission_name = "eurc"
version = "0.11.2"
login_str = "1\nsso\n"
model_id = 0

# Plan Variables
plan_json = "files/empty-2day-plan.json"
dup_plan_name = "empty-2day-plan-v2.json"
plan_id = 0
args_init = "files/args1.json"
args_update = "files/args2.json"


def test_model_upload():
    result = runner.invoke(
        m_app,
        ["upload", "--time-tag-version"],
        input=model_jar 
        + "\n"
        + model_name
        + "\n"
        + mission_name
        + "\n"
        + version
        + "\n"
        + args_init
        + "\n"
        + login_str,
        catch_exceptions=False
    )

    # Get model_id of uploaded mission model
    resp = client.get_mission_models()
    latest_model = resp[-1]
    global model_id
    model_id = latest_model.id

    assert result.exit_code == 0
    assert f"Attached simulation template to model {model_id}" in result.stdout
    assert (
        f"Created new mission model: {model_name} at \
            {client.ui_path()}/models with Model ID: {model_id}"
        in result.stdout
    )


def test_model_delete():
    result = runner.invoke(m_app, ["delete"], input=str(model_id) + "\n" + login_str)
    assert result.exit_code == 0
    assert f"ID: {model_id} has been removed" in result.stdout


def test_model_list():
    result = runner.invoke(m_app, ["list"], input=login_str)
    assert result.exit_code == 0
    assert "Current Mission Models" in result.stdout


def test_model_clean():
    result = runner.invoke(m_app, ["clean"], input=login_str)
    assert result.exit_code == 0
    assert (
        f"All mission models at {client.ui_models_path()} have been deleted"
        in result.stdout
    )


def test_plan_upload():
    # Upload mission model for setup
    runner.invoke(
        m_app,
        ["upload", "--time-tag-version"],
        input=model_jar
        + "\n"
        + model_name
        + "\n"
        + mission_name
        + "\n"
        + version
        + "\n"
        + login_str,
    )

    # Get model_id of uploaded mission model
    resp = client.get_mission_models()
    latest_model = resp[-1]
    global model_id
    model_id = latest_model.id

    # Test plan upload
    result = runner.invoke(
        p_app,
        ["upload", "--time-tag"],
        input=plan_json + "\n" + str(model_id) + "\n" + login_str,
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
        p_app,
        ["duplicate"],
        input=str(plan_id) + "\n" + dup_plan_name + "\n" + login_str,
    )
    assert result.exit_code == 0
    assert f"Duplicated activity plan at: {client.ui_path()}/plans/" in result.stdout


def test_plan_list():
    result = runner.invoke(p_app, ["list"], input=login_str)
    assert result.exit_code == 0
    assert "Current Activity Plans" in result.stdout


def test_plan_simulate():
    result = runner.invoke(
        p_app,
        ["simulate", "--output", "temp.json"],
        input=str(plan_id) + "\n" + login_str,
        catch_exceptions=False
    )
    assert result.exit_code == 0
    assert f"Simulating activity plan at: {client.ui_path()}/plans/{plan_id}"in result.stdout


def test_plan_create_config():
    result = runner.invoke(
        p_app,
        ["create-config"],
        input=str(plan_id) + "\n" + args_init + "\n" + login_str,
    )
    assert result.exit_code == 0
    assert f"Configuration Arguments for Plan ID: {plan_id}" in result.stdout
    assert "foo: arg1" in result.stdout
    assert "num: 5" in result.stdout


def test_plan_update_config():
    result = runner.invoke(
        p_app,
        ["update-config"],
        input=str(plan_id) + "\n" + args_update + "\n" + login_str,
    )
    assert result.exit_code == 0
    assert f"Configuration Arguments for Plan ID: {plan_id}" in result.stdout
    assert "foo: arg2" in result.stdout
    assert "num: 5" in result.stdout


def test_plan_delete():
    result = runner.invoke(p_app, ["delete"], input=str(plan_id) + "\n" + login_str)
    assert result.exit_code == 0
    assert f"ID: {plan_id} has been removed." in result.stdout


def test_plan_clean():
    result = runner.invoke(p_app, ["clean"], input=login_str)
    assert result.exit_code == 0
    assert (
        f"All activity plans have been deleted"
        in result.stdout
    )
