from typer.testing import CliRunner

from .conftest import client, MODEL_JAR, MODEL_NAME, MODEL_VERSION
from aerie_cli.__main__ import app

from aerie_cli.schemas.client import ActivityPlanCreate

import os
import pytest
import arrow
import logging

runner = CliRunner(mix_stderr = False)

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_PATH = os.path.join(TEST_DIR, "files")

# Model Variables
model_id = -1

# Plan Variables
PLANS_PATH = os.path.join(FILES_PATH, "plans")
PLAN_PATH = os.path.join(PLANS_PATH, "bake_bread_plan.json")
plan_id = -1

# Constraint Variables
CONSTRAINTS_PATH = os.path.join(FILES_PATH, "constraints")
CONSTRAINT_PATH = os.path.join(CONSTRAINTS_PATH, "constraint.ts")
constraint_id = -1

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
    client.simulate_plan(plan_id)

def test_constraint_upload(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(app, ["constraints", "upload"],
                           input="Test" + "\n" + CONSTRAINT_PATH + "\n" + str(model_id) + "\n",
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert "Created constraint" in caplog.text
    global constraint_id
    for line in caplog.text.splitlines():
        if not "Created constraint: " in line:
            continue
        # get constraint id from the end of the line
        constraint_id = int(line.split(": ")[1])
    assert constraint_id != -1, "Could not find constraint ID, constraint upload may have failed"\
        f"{caplog.text}"\
        f"{result.stderr}"

def test_constraint_update(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(app, ["constraints", "update"],
                           input=str(constraint_id) + "\n" + CONSTRAINT_PATH + "\n",
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert "Updated constraint" in caplog.text

def test_constraint_violations(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(app, ["constraints", "violations"],
                           input=str(plan_id) + "\n",
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"

    # Check that a constraint violation is returned with the open bracket and curly brace
    # (The integration test constraint should report a violation)
    assert "Constraint violations: [{" in caplog.text

def test_constraint_delete(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(app, ["constraints", "delete"],
                           input=str(constraint_id) + "\n",
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert f"Successfully deleted constraint {str(constraint_id)}" in caplog.text
