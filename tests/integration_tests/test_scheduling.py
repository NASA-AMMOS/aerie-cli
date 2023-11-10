import os
import pytest
import arrow
import logging

from typer.testing import CliRunner
from pathlib import Path

from aerie_cli.__main__ import app
from aerie_cli.schemas.client import ActivityPlanCreate

from .conftest import client, MODEL_JAR, MODEL_NAME, MODEL_VERSION

runner = CliRunner(mix_stderr = False)

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_PATH = os.path.join(TEST_DIR, "files")

DOWNLOADED_FILE_NAME = "downloaded_file.test"

# Model Variables
model_id = 0

# Plan Variables
PLANS_PATH = os.path.join(FILES_PATH, "plans")
PLAN_PATH = os.path.join(PLANS_PATH, "bake_bread_plan.json")
plan_id = 0

# Simulation Variables
sim_id = 0

# Schedule Variables
GOALS_PATH = os.path.join(FILES_PATH, "goals")
GOAL_PATH = os.path.join(GOALS_PATH, "goal1.ts")
goal_id = -1

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
# TEST SCHEDULE
# Uses model, plan, and simulation
#######################

def cli_schedule_upload():
    schedule_file_path = os.path.join(GOALS_PATH, "schedule1.txt")
    with open(schedule_file_path, "w") as fid:
        fid.write(GOAL_PATH)
    result = runner.invoke(
        app,
        ["scheduling", "upload"],
        input=str(model_id) + "\n" + str(plan_id) + "\n" + schedule_file_path + "\n",
        catch_exceptions=False,
        )
    os.remove(schedule_file_path)
    return result

def test_schedule_upload(caplog):
    caplog.set_level(logging.INFO)
    result = cli_schedule_upload()
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert "Assigned goals in priority order" in caplog.text
    global goal_id
    for line in caplog.text.splitlines():
        if not "Assigned goals in priority order" in line:
            continue
        # get expansion id from the end of the line
        goal_id = int(line.split("ID ")[1][:-1])
    assert goal_id != -1, "Could not find goal ID, goal upload may have failed"\
        f"{caplog.text}"\
        f"{result.stderr}"
def test_schedule_delete(caplog):
    caplog.set_level(logging.INFO)
    assert goal_id != -1, "Goal id was not set"

    result = runner.invoke(
        app,
        ["scheduling", "delete"],
        input=str(goal_id) + "\n",
        catch_exceptions=False,
        )
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"Successfully deleted Goal" in caplog.text

def test_schedule_delete_all(caplog):
    caplog.set_level(logging.INFO)
    # Upload a goal to delete
    cli_schedule_upload()
    
    # Delete all goals
    result = runner.invoke(
        app,
        ["scheduling", "delete-all-goals-for-plan"],
        input=str(plan_id) + "\n",
        catch_exceptions=False,
        )
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"Deleting goals for Plan ID {plan_id}" in caplog.text
