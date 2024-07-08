import os
import pytest
import arrow

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
GOAL_PATH_1 = os.path.join(GOALS_PATH, "goal1.ts")
GOAL_PATH_2 = os.path.join(GOALS_PATH, "goal2.jar")
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

def cli_goal_upload_ts():
    result = runner.invoke(
        app,
        ["goals", "new", GOAL_PATH_1, "-p", plan_id],
        catch_exceptions=False,
    )
    return result

def cli_goal_upload_jar():
    result = runner.invoke(
        app,
        ["goals", "new", GOAL_PATH_2, "-p", plan_id],
        catch_exceptions=False
    )
    return result

def test_schedule_upload():
    result = cli_goal_upload_ts()
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Uploaded scheduling goal to venue." in result.stdout

    result = cli_goal_upload_jar()
    assert result.exit_code == 0, \
        f"{result.stdout}" \
        f"{result.stderr}"
    assert "Uploaded scheduling goal to venue." in result.stdout

    global goal_id
    for line in result.stdout.splitlines():
        if not "Uploaded scheduling goal to venue" in line:
            continue
        # get expansion id from the end of the line
        goal_id = int(line.split("ID: ")[1])

    assert goal_id != -1, "Could not find goal ID, goal upload may have failed"\
        f"{result.stdout}"\
        f"{result.stderr}"

def test_goal_update():
    result = runner.invoke(
        app,
        ["goals", "update", GOAL_PATH_2],
        catch_exceptions=False
    )
    assert result.exit_code == 0, \
        f"{result.stdout}" \
        f"{result.stderr}"
    assert "Uploaded new version of scheduling goal to venue." in result.stdout

def test_goal_delete():
    assert goal_id != -1, "Goal id was not set"

    result = runner.invoke(
        app,
        ["goals", "delete"],
        input=str(goal_id) + "\n",
        catch_exceptions=False,
        )
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"Successfully deleted Goal" in result.stdout

def test_schedule_delete_all():
    # Upload a goal to delete
    cli_goal_upload_jar()
    
    # Delete all goals
    result = runner.invoke(
        app,
        ["goals", "delete-all-goals-for-plan"],
        input=str(plan_id) + "\n",
        catch_exceptions=False,
        )
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"Deleting goals for Plan ID {plan_id}" in result.stdout
