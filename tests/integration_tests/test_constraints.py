from typer.testing import CliRunner

from .conftest import client, HASURA_ADMIN_SECRET
from aerie_cli.__main__ import app

from aerie_cli.schemas.client import ActivityPlanCreate

import os
import pytest
import arrow

runner = CliRunner(mix_stderr = False)

test_dir = os.path.dirname(os.path.abspath(__file__))

files_path = os.path.join(test_dir, "files")

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

# Constraint Variables
constraints_path = os.path.join(files_path, "constraints")
constraint_path = os.path.join(constraints_path, "constraint.ts")
constraint_id = -1

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

def test_constraint_upload():
    result = runner.invoke(app, ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "constraints", "upload"],
                           input="Test" + "\n" + constraint_path + "\n" + str(model_id) + "\n",
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Created constraint" in result.stdout
    global constraint_id
    for line in result.stdout.splitlines():
        if not "Created constraint: " in line:
            continue
        # get constraint id from the end of the line
        constraint_id = int(line.split(": ")[1])
    assert constraint_id != -1, "Could not find constraint ID, constraint upload may have failed"\
        f"{result.stdout}"\
        f"{result.stderr}"

def test_constraint_update():
    result = runner.invoke(app, ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "constraints", "update"],
                           input=str(constraint_id) + "\n" + constraint_path + "\n",
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Updated constraint" in result.stdout

def test_constraint_delete():
    result = runner.invoke(app, ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "constraints", "delete"],
                           input=str(constraint_id) + "\n" + constraint_path + "\n",
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert f"Successfully deleted constraint {str(constraint_id)}" in result.stdout

def test_constraint_violations():
    result = runner.invoke(app, ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "constraints", "violations"],
                           input=str(plan_id) + "\n",
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Constraint violations: " in result.stdout