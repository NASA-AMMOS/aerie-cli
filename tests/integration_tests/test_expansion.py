# in case src_path is not from aeri-cli src and from site-packages
import os
import sys

import pytest

src_path = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../src")
sys.path.insert(0, src_path)

from typer.testing import CliRunner
from pathlib import Path

from aerie_cli.aerie_client import AerieClient
from aerie_cli.aerie_host import AerieHostSession, AuthMethod
from aerie_cli.__main__ import app
from aerie_cli.commands.configurations import delete_all_persistent_files, upload_configurations, deactivate_session, activate_session
from aerie_cli.utils.sessions import get_active_session_client

import arrow
from aerie_cli.schemas.client import ActivityPlanCreate
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

files_path = os.path.join(test_dir, "files")

DOWNLOADED_FILE_NAME = "downloaded_file.test"

# Configuration Variables
configurations_path = os.path.join(files_path, "configuration")
config_json = os.path.join(configurations_path, "localhost_config.json")

# Model Variables
models_path = os.path.join(files_path, "models")
model_jar = os.path.join(models_path, "banananation-1.6.2.jar")
model_name = "banananation"
version = "0.0.1"
model_id = 0

# Plan Variables
plans_path = os.path.join(files_path, "plans")
plan_json = os.path.join(plans_path, "bake_bread_plan.json")
dup_plan_name = os.path.join(plans_path, "bake_bread_plan_2.json")
plan_id = 0
args_init = os.path.join(plans_path, "create_config.json")
args_update = os.path.join(plans_path, "update_config.json")

# Simulation Variables
sim_id = 0

# Schedule Variables
goals_path = os.path.join(files_path, "goals")
goal_path = os.path.join(goals_path, "goal1.ts")


# Command Dictionary Variables
command_dictionaries_path = os.path.join(files_path, "command_dicts")
command_dictionary_path = os.path.join(command_dictionaries_path, "command_banananation.xml")
command_dictionary_id = 0

# Expansion Variables
expansion_set_id = -1
expansion_sequence_id = 1

@pytest.fixture(scope="session", autouse=True)
def set_up_environment(request):
    # Resets the configurations and adds localhost
    deactivate_session()
    delete_all_persistent_files()
    upload_configurations(config_json)
    activate_session("localhost")
    persisent_client = None
    try:
        persisent_client = get_active_session_client()
    except:
        raise RuntimeError("Configuration is not active!")
    assert persisent_client.host_session.gateway_url == GATEWAY_URL,\
        "Aerie instances are mismatched. Ensure test URLs are the same."

    resp = client.get_mission_models()
    for api_mission_model in resp:
        client.delete_mission_model(api_mission_model.id)
    
    global model_id
    model_id = client.upload_mission_model(
        mission_model_path=model_jar,
        project_name=model_name, 
        mission="",
        version=version)

    global command_dictionary_id
    with open(command_dictionary_path, 'r') as fid:
        command_dictionary_id = client.upload_command_dictionary(fid.read())
    
    # upload plan
    with open(plan_json) as fid:
        contents = fid.read()
    plan_to_create = ActivityPlanCreate.from_json(contents)
    plan_to_create.name += arrow.utcnow().format("YYYY-MM-DDTHH-mm-ss")
    global plan_id
    plan_id = client.create_activity_plan(model_id, plan_to_create)
    
    # simulate plan
    global sim_id
    sim_id = client.simulate_plan(plan_id)

#######################
# TEST EXPANSION SEQUENCES
# Uses plan and simulation dataset
#######################

def test_expansion_sequence_create():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "expansion", "sequences", "create"],
        input=str(sim_id) + "\n" + str(expansion_sequence_id) + "\n" + str(2) + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Successfully created sequence" in result.stdout

def test_expansion_sequence_list():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "expansion", "sequences", "list"],
        input="2" + "\n" + str(sim_id) + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "All sequences for Simulation Dataset" in result.stdout

def test_expansion_sequence_download():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "expansion", "sequences", "download"],
        input=str(sim_id) + "\n" + str(expansion_sequence_id) + "\n" + DOWNLOADED_FILE_NAME + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    path_to_sequence = Path(DOWNLOADED_FILE_NAME)
    assert path_to_sequence.exists()
    path_to_sequence.unlink()

def test_expansion_sequence_delete():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "expansion", "sequences", "delete"],
        input=str(sim_id) + "\n" + str(expansion_sequence_id) + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Successfully deleted sequence" in result.stdout

#######################
# TEST EXPANSION SETS
# Uses model, command dictionary, and activity types
#######################

def test_expansion_set_create():
    client.create_expansion_rule(
        expansion_logic="""
            export default function MyExpansion(props: {
            activityInstance: ActivityType
            }): ExpansionReturn {
            const { activityInstance } = props;
            return [];
            }
            """,
        activity_name="BakeBananaBread",
        model_id=model_id,
        command_dictionary_id=command_dictionary_id
    )
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "expansion", "sets", "create"],
        input=str(model_id) + "\n" + str(command_dictionary_id) + "\n" + "BakeBananaBread" + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    global expansion_set_id
    for line in result.stdout.splitlines():
        if not "Created expansion set: " in line:
            continue
        # get expansion id from the end of the line
        expansion_set_id = int(line.split(": ")[1])
    assert expansion_set_id != -1, "Could not find expansion run ID, expansion create may have failed"\
        f"{result.stdout}"\
        f"{result.stderr}"

def test_expansion_set_get():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "expansion", "sets", "get"],
        input=str(expansion_set_id) + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Expansion Set" in result.stdout and "Contents" in result.stdout

def test_expansion_set_list():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "expansion", "sets", "list"],
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Expansion Sets" in result.stdout

#######################
# TEST EXPANSION RUNS
# Uses plan and simulation dataset
#######################
def test_expansion_run_create():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "expansion", "runs", "create"],
        input=str(sim_id) + "\n" + str(expansion_set_id) + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Expansion Run ID: " in result.stdout

def test_expansion_runs_list():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "expansion", "runs", "list"],
        input="2" + "\n" + str(sim_id) + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Expansion Runs" in result.stdout

#######################
# DELETE MODELS
#######################

def test_model_delete():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "models", "delete"],
        input=str(model_id),
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"ID: {model_id} has been removed" in result.stdout