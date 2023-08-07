from typer.testing import CliRunner

from .conftest import client, HASURA_ADMIN_SECRET
from aerie_cli.__main__ import app

import os
import pytest

runner = CliRunner(mix_stderr = False)

test_dir = os.path.dirname(os.path.abspath(__file__))

files_path = os.path.join(test_dir, "files")

# Model Variables
models_path = os.path.join(files_path, "models")
model_jar = os.path.join(models_path, "banananation-1.6.2.jar")
model_name = "banananation"
version = "0.0.1"
model_id = 0

# Constraint Variables
constraints_path = os.path.join(files_path, "constraints")
constraint_path = os.path.join(constraints_path, "constraint.json")

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

def test_constraint_upload():
    result = runner.invoke(app, ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "metadata", "upload"],
                           input="Test" + "\n" + constraint_path + "\n" + str(model_id) + "\n",
                                   catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "2 new schema have been added" in result.stdout