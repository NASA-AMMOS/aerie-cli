import os

from typer.testing import CliRunner

from aerie_cli.__main__ import app

from .conftest import client, MODEL_JAR, MODEL_NAME, MODEL_VERSION

runner = CliRunner(mix_stderr = False)

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_PATH = os.path.join(TEST_DIR, "files")

# Model Variables
model_id = -1

def test_model_clean():
    result = runner.invoke(
        app,
        ["models", "clean"],
        catch_exceptions=False,
        )
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert (
        f"All mission models have been deleted"
        in result.stdout
    )

def test_model_upload():
    result = runner.invoke(
        app,
        ["models", "upload", "--time-tag-version"],
        input=MODEL_JAR 
        + "\n"
        + MODEL_NAME
        + "\n"
        + MODEL_VERSION
        + "\n",
        catch_exceptions=False,
    )

    # Get model_id of uploaded mission model
    resp = client.get_mission_models()
    latest_model = resp[-1]
    global model_id
    model_id = latest_model.id

    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert (
        f"Created new mission model: {MODEL_NAME} with Model ID: {model_id}"
        in result.stdout
    )

def test_model_list():
    result = runner.invoke(
        app,
        ["models", "list"],
        catch_exceptions=False,)
    assert result.exit_code == 0,\
        f"{result.stdout}"\
        f"{result.stderr}"
    assert "Current Mission Models" in result.stdout

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
