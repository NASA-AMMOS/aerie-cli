import os
import pytest

from typer.testing import CliRunner
from pathlib import Path

from aerie_cli.__main__ import app
from aerie_cli.commands import plans

from .conftest import client, HASURA_ADMIN_SECRET, DOWNLOADED_FILE_NAME

runner = CliRunner(mix_stderr = False)

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_PATH = os.path.join(TEST_DIR, "files")

DOWNLOADED_FILE_NAME = "downloaded_file.test"

# Model Variables
MODELS_PATH = os.path.join(FILES_PATH, "models")
MODEL_JAR = os.path.join(MODELS_PATH, "banananation-1.12.0.jar")
MODEL_NAME = "banananation"
MODEL_VERSION = "0.0.1"
model_id = -1

# Plan Variables
PLANS_PATH = os.path.join(FILES_PATH, "plans")
PLAN_JSON = os.path.join(PLANS_PATH, "bake_bread_plan.json")
DUP_PLAN_NAME = os.path.join(PLANS_PATH, "bake_bread_plan_2.json")
plan_id = -1
PLAN_ARGS_INIT = os.path.join(PLANS_PATH, "create_config.json")
PLAN_ARGS_UPDATE = os.path.join(PLANS_PATH, "update_config.json")

@pytest.fixture(scope="module", autouse=True)
def set_up_environment(request):
    resp = client.get_mission_models()
    for api_mission_model in resp:
        client.delete_mission_model(api_mission_model.id)

    global model_id
    model_id = client.upload_mission_model(
        mission_model_path=MODEL_JAR,
        project_name=MODEL_NAME, 
        mission="",
        version=MODEL_VERSION)

def cli_plan_simulate():
    return runner.invoke(
        app,
        ["plans", "simulate", "--output", "temp.json"],
        input=str(plan_id) + "\n",
        catch_exceptions=False
    )

#######################
# TEST AND SETUP PLAN
# Uses model
#######################

def test_plan_upload():
    # Clean out plans first
    plans.clean()

    # Test plan upload
    result = runner.invoke(
        app,
        ["plans", "upload", "--time-tag"],
        input=PLAN_JSON + "\n" + str(model_id) + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    
    # Get uploaded plan id
    resp = client.get_all_activity_plans()
    latest_plan = resp[-1]
    global plan_id
    plan_id = latest_plan.id

    assert f"Created plan ID: {plan_id}" in result.stdout

def test_plan_duplicate():
    result = runner.invoke(
        app,
        ["plans", "duplicate"],
        input=str(plan_id) + "\n" + DUP_PLAN_NAME + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"

    # Get duplicated plan id
    resp = client.get_all_activity_plans()
    latest_plan = resp[-1]
    duplicated_plan_id = latest_plan.id

    assert f"Duplicate activity plan created with ID: {duplicated_plan_id}" in result.stdout


def test_plan_list():
    result = runner.invoke(app, ["plans", "list"],
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Current Activity Plans" in result.stdout


#######################
# SIMULATE PLAN
# Uses plan
#######################

def test_plan_simulate():
    result = cli_plan_simulate()
    sim_ids = client.get_simulation_dataset_ids_by_plan_id(plan_id)
    global sim_id
    sim_id = sim_ids[-1]
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"Simulation completed" in result.stdout

def test_plan_download():
    result = runner.invoke(
        app,
        ["plans", "download"],
        input=str(plan_id) + "\n" + DOWNLOADED_FILE_NAME + "\n",
        catch_exceptions=False,
    )
    path_to_plan = Path(DOWNLOADED_FILE_NAME)
    assert path_to_plan.exists()
    path_to_plan.unlink()
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"Wrote activity plan" in result.stdout

def test_plan_download_resources():
    result = runner.invoke(
        app,
        ["plans", "download-resources"],
        input=str(sim_id) + "\n" + DOWNLOADED_FILE_NAME + "\n",
        catch_exceptions=False,
    )
    path_to_resources = Path(DOWNLOADED_FILE_NAME)
    assert path_to_resources.exists()
    path_to_resources.unlink()
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"Wrote resource timelines" in result.stdout

def test_plan_download_simulation():
    result = runner.invoke(
        app,
        ["plans", "download-simulation"],
        input=str(sim_id) + "\n" + DOWNLOADED_FILE_NAME + "\n",
        catch_exceptions=False,
    )
    path_to_resources = Path(DOWNLOADED_FILE_NAME)
    assert path_to_resources.exists()
    path_to_resources.unlink()
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"Wrote activity plan" in result.stdout

def test_plan_create_config():
    result = runner.invoke(
        app,
        ["plans", "create-config"],
        input=str(plan_id) + "\n" + PLAN_ARGS_INIT + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"Configuration Arguments for Plan ID: {plan_id}" in result.stdout
    assert "initialPlantCount: 2" in result.stdout
    assert "initialProducer: nobody" in result.stdout

def test_simulate_after_create_config():
    result = cli_plan_simulate()
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"Simulation completed" in result.stdout

def test_plan_update_config():
    result = runner.invoke(
        app,
        ["plans", "update-config"],
        input=str(plan_id) + "\n" + PLAN_ARGS_UPDATE + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"Configuration Arguments for Plan ID: {plan_id}" in result.stdout
    assert "initialPlantCount: 3" in result.stdout
    assert "initialProducer: somebody" in result.stdout

def test_simulate_after_update_config():
    result = cli_plan_simulate()
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"Simulation completed" in result.stdout

#######################
# DELETE PLANS
#######################

def test_plan_delete():
    result = runner.invoke(
        app,
        ["plans", "delete"],
        input=str(plan_id) + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"ID: {plan_id} has been removed." in result.stdout


def test_plan_clean():
    result = runner.invoke(
        app,
        ["plans", "clean"],
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert (
        f"All activity plans have been deleted"
        in result.stdout
    )

#######################
# DELETE MODELS
#######################

def test_model_delete():
    result = runner.invoke(
        app,
        ["models", "delete"],
        input=str(model_id),
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"ID: {model_id} has been removed" in result.stdout
