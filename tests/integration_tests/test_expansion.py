import os
import pytest
import arrow

from pathlib import Path

from aerie_cli.__main__ import app
from aerie_cli.schemas.client import ActivityPlanCreate
from aerie_cli.schemas.client import Parcel

from .conftest import client, MODEL_JAR, MODEL_NAME, MODEL_VERSION, ARTIFACTS_PATH, RUNNER

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_PATH = os.path.join(TEST_DIR, "files")

DOWNLOADED_FILE_NAME = "downloaded_file.test"

EXPANSION_ARTIFACTS_PATH = Path(ARTIFACTS_PATH).joinpath("expansion")
EXPANSION_ARTIFACTS_PATH.mkdir()

# Model Variables
model_id = -1

# Plan Variables
PLANS_PATH = os.path.join(FILES_PATH, "plans")
PLAN_PATH = os.path.join(PLANS_PATH, "bake_bread_plan.json")
plan_id = -1

# Simulation Variables
sim_id = -1

# Command Dictionary Variables
COMMAND_DICTIONARIES_PATH = os.path.join(FILES_PATH, "dictionaries")
COMMAND_DICTIONARY_PATH = os.path.join(COMMAND_DICTIONARIES_PATH, "command_banananation.xml")
command_dictionary_id = -1

# Expansion Variables
expansion_set_id = -1
expansion_sequence_id = 1
EXPANSION_FILES_PATH = os.path.join(FILES_PATH, "expansion")
EXPANSION_DEPLOY_CONFIG_PATH = os.path.join(EXPANSION_FILES_PATH, "expansion_deploy_config.json")

@pytest.fixture(scope="module", autouse=True)
def set_up_environment(request):
    resp = client.get_mission_models()
    # delete all plans and models
    for api_mission_model in resp:
        client.delete_mission_model(api_mission_model.id)
    for plan in client.get_all_activity_plans():
        client.delete_plan(plan.id)

    # upload model
    global model_id
    model_id = client.upload_mission_model(
        mission_model_path=MODEL_JAR,
        project_name=MODEL_NAME, 
        mission="",
        version=MODEL_VERSION)

    global command_dictionary_id
    with open(COMMAND_DICTIONARY_PATH, 'r') as fid:
        command_dictionary_id = client.create_dictionary(fid.read())

    global parcel_id
    parcel_id = client.create_parcel(Parcel("Integration Test", command_dictionary_id, None, None, []))

    # upload plan
    with open(PLAN_PATH) as fid:
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

def test_get_typescript_dictionary():
    ts_dict = client.get_typescript_dictionary(command_dictionary_id)
    with open(EXPANSION_ARTIFACTS_PATH.joinpath("command_dict.ts"), "w") as fid:
        fid.write(ts_dict)

def test_expansion_sequence_create():
    result = RUNNER.invoke(
        app,
        ["expansion", "sequences", "create"],
        input=str(sim_id) + "\n" + str(expansion_sequence_id) + "\n" + str(2) + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Successfully created sequence" in result.stdout

def test_expansion_sequence_list():
    result = RUNNER.invoke(
        app,
        ["expansion", "sequences", "list"],
        input="2" + "\n" + str(sim_id) + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "All sequences for Simulation Dataset" in result.stdout

def test_expansion_sequence_download():
    result = RUNNER.invoke(
        app,
        ["expansion", "sequences", "download"],
        input=str(sim_id) + "\n" + str(expansion_sequence_id) + "\n" + DOWNLOADED_FILE_NAME + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    path_to_sequence = Path(DOWNLOADED_FILE_NAME)
    assert path_to_sequence.exists()
    path_to_sequence.unlink()

def test_expansion_sequence_delete():
    result = RUNNER.invoke(
        app,
        ["expansion", "sequences", "delete"],
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


def test_expansion_deploy():
    result = RUNNER.invoke(
        app,
        [
            "expansion",
            "deploy",
            "-m",
            str(model_id),
            "-p",
            str(parcel_id),
            "-c",
            EXPANSION_DEPLOY_CONFIG_PATH,
            "--rules-path",
            EXPANSION_FILES_PATH,
            "--time-tag"
        ],
        catch_exceptions=False
    )
    assert result.exit_code == 0, \
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Created expansion rule integration_test_BakeBananaBread" in result.stdout
    assert "Created expansion rule integration_test_BiteBanana" in result.stdout
    assert "Failed to create expansion rule integration_test_bad" in result.stdout
    assert "Created expansion set integration_test_set" in result.stdout

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
        parcel_id=parcel_id
    )
    result = RUNNER.invoke(
        app,
        [
            "expansion", 
            "sets", 
            "create", 
            "-m", 
            str(model_id), 
            "-p", 
            str(parcel_id), 
            "-n", 
            "integration_test-" + arrow.utcnow().format("YYYY-MM-DDTHH-mm-ss"),
            "-a",
            "BakeBananaBread"
        ],
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
    result = RUNNER.invoke(
        app,
        ["expansion", "sets", "get"],
        input=str(expansion_set_id) + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Expansion Set" in result.stdout and "Contents" in result.stdout

def test_expansion_set_list():
    result = RUNNER.invoke(
        app,
        ["expansion", "sets", "list"],
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Expansion Sets" in result.stdout
    assert "integration_test" in result.stdout

#######################
# TEST EXPANSION RUNS
# Uses plan and simulation dataset
#######################
def test_expansion_run_create():
    result = RUNNER.invoke(
        app,
        ["expansion", "runs", "create"],
        input=str(sim_id) + "\n" + str(expansion_set_id) + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Expansion Run ID: " in result.stdout

def test_expansion_runs_list():
    result = RUNNER.invoke(
        app,
        ["expansion", "runs", "list"],
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
    result = RUNNER.invoke(
        app,
        ["models", "delete"],
        input=str(model_id),
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"ID: {model_id} has been removed" in result.stdout
