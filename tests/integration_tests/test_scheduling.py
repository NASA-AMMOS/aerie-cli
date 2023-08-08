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

# Schedule Variables
goals_path = os.path.join(files_path, "goals")
goal_path = os.path.join(goals_path, "goal1.ts")

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
# TEST SCHEDULE
# Uses model, plan, and simulation
#######################

def test_schedule_upload():
    schedule_file_path = os.path.join(goals_path, "schedule1.txt")
    with open(schedule_file_path, "x") as fid:
        fid.write(goal_path)
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "scheduling", "upload"],
        input=str(model_id) + "\n" + str(sim_id) + "\n" + schedule_file_path + "\n",
        catch_exceptions=False,
        )
    os.remove(schedule_file_path)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Assigned goals in priority order" in result.stdout

def test_schedule_delete():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "scheduling", "delete"],
        input=str(model_id) + "\n" + str(sim_id) + "\n" + goal_path + "\n",
        catch_exceptions=False,
        )
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"Successfully deleted Goal" in result.stdout

def test_schedule_delete_all():
    result = runner.invoke(
        app,
        ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "scheduling", "delete-all-goals-for-plan"],
        input=str(plan_id) + "\n",
        catch_exceptions=False,
        )
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "No goals to delete." in result.stdout