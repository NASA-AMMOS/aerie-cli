import os
import pytest
import arrow

from typer.testing import CliRunner
from pathlib import Path

from aerie_cli.__main__ import app
from aerie_cli.schemas.client import ActivityPlanCreate

from .conftest import client, HASURA_ADMIN_SECRET

runner = CliRunner(mix_stderr = False)

test_dir = os.path.dirname(os.path.abspath(__file__))

files_path = os.path.join(test_dir, "files")

DOWNLOADED_FILE_NAME = "downloaded_file.test"

# Model Variables
models_path = os.path.join(files_path, "models")
model_jar = os.path.join(models_path, "banananation-1.6.2.jar")
model_name = "banananation"
version = "0.0.1"
model_id = 0

# Plan Variables
plans_path = os.path.join(files_path, "plans")
plan_json = os.path.join(plans_path, "bake_bread_plan.json")
plan_id = 0

# Simulation Variables
sim_id = 0

# Command Dictionary Variables
command_dictionaries_path = os.path.join(files_path, "command_dicts")
command_dictionary_path = os.path.join(command_dictionaries_path, "command_banananation.xml")
command_dictionary_id = 0

# Expansion Variables
expansion_set_id = -1
expansion_sequence_id = 1

@pytest.fixture(scope="module", autouse=True)
def set_up_environment(request):
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