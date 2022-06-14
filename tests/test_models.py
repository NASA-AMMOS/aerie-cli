from typer.testing import CliRunner

from aerie_cli.client import auth_helper
from aerie_cli.models import app

runner = CliRunner()

sso = "sso"
username = ""
password = ""
server_url = "http://localhost"

model_jar = "files/data-simple.jar\n"
model_name = "data-simple\n"
mission_name = "eurc\n"
version = "0.11.2\n"
login_str = "1\nsso\n"
model_id = 0


def test_upload():
    result = runner.invoke(
        app,
        ["upload", "--time-tag-version"],
        input=model_jar + model_name + mission_name + version + login_str,
    )

    # Get model_id of uploaded mission model
    client = auth_helper(
        sso=sso, username=username, password=password, server_url=server_url
    )
    resp = client.get_mission_models()
    latest_model = resp[-1]
    global model_id
    model_id = latest_model.id

    assert result.exit_code == 0
    assert "Created new mission model: " in result.stdout


def test_delete():
    result = runner.invoke(app, ["delete"], input=str(model_id) + "\n" + login_str)
    assert result.exit_code == 0
    assert f"ID: {model_id} has been removed." in result.stdout


def test_list():
    result = runner.invoke(app, ["list"], input=login_str)
    assert result.exit_code == 0
    assert "Current Mission Models" in result.stdout


def test_clean():
    result = runner.invoke(app, ["clean"], input=login_str)
    assert result.exit_code == 0
    assert "All mission models" in result.stdout
