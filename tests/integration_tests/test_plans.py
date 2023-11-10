import os
import pytest
import logging

from typer.testing import CliRunner
from pathlib import Path

from aerie_cli.__main__ import app
from aerie_cli.commands import plans

from .conftest import client, DOWNLOADED_FILE_NAME, ADDITIONAL_USERS, MODEL_JAR, MODEL_NAME, MODEL_VERSION

runner = CliRunner(mix_stderr = False)

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_PATH = os.path.join(TEST_DIR, "files")

DOWNLOADED_FILE_NAME = "downloaded_file.test"

# Model Variables
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

def test_plan_upload(caplog):
    caplog.set_level(logging.INFO)
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
        f"{caplog.text}"\
        f"{result.stderr}"
    
    # Get uploaded plan id
    resp = client.get_all_activity_plans()
    latest_plan = resp[-1]
    global plan_id
    plan_id = latest_plan.id

    assert f"Created plan ID: {plan_id}" in caplog.text

def test_plan_duplicate(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(
        app,
        ["plans", "duplicate"],
        input=str(plan_id) + "\n" + DUP_PLAN_NAME + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"

    # Get duplicated plan id
    resp = client.get_all_activity_plans()
    latest_plan = resp[-1]
    duplicated_plan_id = latest_plan.id

    assert f"Duplicate activity plan created with ID: {duplicated_plan_id}" in caplog.text


def test_plan_list(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(app, ["plans", "list"],
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert "Current Activity Plans" in result.stdout


#######################
# ADD/LIST/DELETE COLLABORATORS
# Uses plan
#######################


def test_list_empty_plan_collaborators(caplog):
    caplog.set_level(logging.INFO)
    """
    Should be no plan collaborators to start
    """
    result = runner.invoke(
        app,
        ["plans", "collaborators", "list"],
        input=str(plan_id) + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0, f"{caplog.text}" f"{result.stderr}"

    assert "No collaborators" in caplog.text


def test_add_collaborators(caplog):
    caplog.set_level(logging.INFO)
    """
    Add all users as collaborators and check the final list
    """

    # Add all additional users as collaborators
    for username in ADDITIONAL_USERS:
        result = runner.invoke(
            app,
            ["plans", "collaborators", "add"],
            input=str(plan_id) + "\n" + username + "\n",
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"{caplog.text} {result.stderr}"

        assert "Success" in caplog.text

    # Check full list of collaborators
    assert ADDITIONAL_USERS == client.list_plan_collaborators(plan_id)


def test_list_plan_collaborators(caplog):
    caplog.set_level(logging.INFO)
    """
    Check that the `plans collaborators list` command lists all collaborators
    """
    result = runner.invoke(
        app,
        ["plans", "collaborators", "list"],
        input=str(plan_id) + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0, f"{caplog.text} {result.stderr}"

    for username in ADDITIONAL_USERS:
        assert username in caplog.text


def test_delete_collaborators(caplog):
    caplog.set_level(logging.INFO)
    """
    Delete a collaborator and verify the result
    """
    user_to_delete = ADDITIONAL_USERS[0]
    result = runner.invoke(
        app,
        ["plans", "collaborators", "delete"],
        input=str(plan_id) + "\n" + "1" + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0, f"{caplog.text} {result.stderr}"

    assert "Success" in caplog.text


#######################
# SIMULATE PLAN
# Uses plan
#######################

def test_plan_simulate(caplog):
    caplog.set_level(logging.INFO)
    result = cli_plan_simulate()
    sim_ids = client.get_simulation_dataset_ids_by_plan_id(plan_id)
    global sim_id
    sim_id = sim_ids[-1]
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"Simulation completed" in caplog.text

def test_plan_download(caplog):
    caplog.set_level(logging.INFO)
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
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"Wrote activity plan" in caplog.text

def test_plan_download_expanded_args(caplog):
    caplog.set_level(logging.INFO)
    """
    Download a plan, exercising the --full-args option to get effective activity arguments
    """
    result = runner.invoke(
        app,
        ["plans", "download", "--full-args", "true"],
        input=str(plan_id) + "\n" + DOWNLOADED_FILE_NAME + "\n",
        catch_exceptions=False,
    )
    path_to_plan = Path(DOWNLOADED_FILE_NAME)
    assert path_to_plan.exists()
    path_to_plan.unlink()
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"Wrote activity plan" in caplog.text

def test_plan_download_resources(caplog):
    caplog.set_level(logging.INFO)
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
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"Wrote resource timelines" in caplog.text

def test_plan_download_simulation(caplog):
    caplog.set_level(logging.INFO)
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
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"Wrote activity plan" in caplog.text

def test_plan_create_config(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(
        app,
        ["plans", "create-config"],
        input=str(plan_id) + "\n" + PLAN_ARGS_INIT + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"Configuration Arguments for Plan ID: {plan_id}" in caplog.text
    assert "initialPlantCount: 2" in caplog.text
    assert "initialProducer: nobody" in caplog.text

def test_simulate_after_create_config(caplog):
    caplog.set_level(logging.INFO)
    result = cli_plan_simulate()
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"Simulation completed" in caplog.text

def test_plan_update_config(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(
        app,
        ["plans", "update-config"],
        input=str(plan_id) + "\n" + PLAN_ARGS_UPDATE + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"Configuration Arguments for Plan ID: {plan_id}" in caplog.text
    assert "initialPlantCount: 3" in caplog.text
    assert "initialProducer: somebody" in caplog.text

def test_simulate_after_update_config(caplog):
    caplog.set_level(logging.INFO)
    result = cli_plan_simulate()
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"Simulation completed" in caplog.text

#######################
# DELETE PLANS
#######################

def test_plan_delete(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(
        app,
        ["plans", "delete"],
        input=str(plan_id) + "\n",
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"ID: {plan_id} has been removed." in caplog.text


def test_plan_clean(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(
        app,
        ["plans", "clean"],
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert (
        f"All activity plans have been deleted"
        in caplog.text
    )

#######################
# DELETE MODELS
#######################

def test_model_delete(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(
        app,
        ["models", "delete"],
        input=str(model_id),
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"ID: {model_id} has been removed" in caplog.text
