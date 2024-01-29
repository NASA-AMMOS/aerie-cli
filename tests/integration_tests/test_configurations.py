import os

from typer.testing import CliRunner

from aerie_cli.__main__ import app
import pytest
import logging

from .conftest import\
    HASURA_ADMIN_SECRET,\
    GRAPHQL_URL,\
    GATEWAY_URL,\
    USERNAME
from aerie_cli.persistent import PersistentConfigurationManager, PersistentSessionManager, NoActiveSessionError
from aerie_cli.utils.sessions import start_session_from_configuration

runner = CliRunner(mix_stderr = False)

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_PATH = os.path.join(TEST_DIR, "files")

# Configuration Variables
CONFIGURATIONS_PATH = os.path.join(FILES_PATH, "configuration")
CONFIGURATION_PATH = os.path.join(CONFIGURATIONS_PATH, "localhost_config.json")

CONFIGURATION_NAME = "localhost"
configuration_id = -1

def test_configurations_clean(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(
        app,
        ["configurations", "clean"],
        input="y" + "\n",
        catch_exceptions=False,
    )
    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"

    assert len(PersistentConfigurationManager.get_configurations()) == 0,\
        f"CONFIGURATIONS NOT CLEARED! CONFIGURATIONS: {PersistentConfigurationManager.get_configurations()}\n"\
        f"{caplog.text}"\
        f"{result.stderr}"

    no_session_error = False
    try:
        runner.invoke(
            app,
            ["-c", "localhost", "--hasura-admin-secret", HASURA_ADMIN_SECRET, "models", "list"],
            catch_exceptions=False,)
    except (NoActiveSessionError, FileNotFoundError) as err:
        no_session_error = True

    if not no_session_error:
        # We raise an error to prevent tests running when configurations are broken
        pytest.exit(f"CONFIGURATION SHOULD NOT EXIST. Failed when using active -c option {other}\n",
                     returncode=pytest.ExitCode.TESTS_FAILED)
    try:
        runner.invoke(
            app,
            ["--hasura-admin-secret", HASURA_ADMIN_SECRET, "models", "list"],
            catch_exceptions=False,)
    except NoActiveSessionError as err:
        return
    except Exception as other:
        # We raise an error to prevent tests running when configurations are broken
        pytest.exit(
            f"CONFIGURATION SHOULD NOT EXIST. Failed when using active configuration. UNEXPECTED ERROR: {other}\n",
                returncode=pytest.ExitCode.TESTS_FAILED)
    # We raise an error to prevent tests running when configurations are broken
    pytest.exit("CONFIGURATION SHOULD NOT EXIST. Failed when using active configuration\n",
                returncode=pytest.ExitCode.TESTS_FAILED)

def test_configurations_create(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(
        app,
        ["configurations", "create"],
        input=CONFIGURATION_NAME + "\n"
        + GRAPHQL_URL + "\n"
        + GATEWAY_URL + "\n"
        + "y" + "\n"
        + USERNAME + "\n",
        catch_exceptions=False,
    )

    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"

    global configuration_id
    for i, configuration in enumerate(PersistentConfigurationManager.get_configurations()):
        if configuration.name != "localhost":
            continue
        configuration_id = i
    assert configuration_id != -1, "CONFIGURATION NOT LOADED, is it's name localhost?"

def test_activate(caplog):
    caplog.set_level(logging.INFO)
    before_refresh = len(PersistentConfigurationManager.get_configurations())
    assert before_refresh > 0
    PersistentConfigurationManager.read_configurations()
    assert len(PersistentConfigurationManager.get_configurations()) == before_refresh

    result = runner.invoke(
        app,
        ["activate"],
        input=str(configuration_id) + "\n",
        catch_exceptions=False,
    )

    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert PersistentSessionManager.get_active_session().configuration_name == "localhost"

def test_deactivate(caplog):
    caplog.set_level(logging.INFO)
    before_refresh = len(PersistentConfigurationManager.get_configurations())
    assert before_refresh > 0
    PersistentConfigurationManager.read_configurations()
    assert len(PersistentConfigurationManager.get_configurations()) == before_refresh

    assert PersistentSessionManager.get_active_session().configuration_name == "localhost"
    result = runner.invoke(
        app,
        ["deactivate"],
        input=str(configuration_id) + "\n",
        catch_exceptions=False,
    )

    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert (
        f"Deactivated session: {CONFIGURATION_NAME}"
        in caplog.text
    )
    
    try:
        runner.invoke(
            app,
            ["--hasura-admin-secret", HASURA_ADMIN_SECRET, "models", "list"],
            catch_exceptions=False,)
    except NoActiveSessionError as err:
        return
    except Exception as other:
        # We raise an error to prevent tests running when configurations are broken
        pytest.exit(
            f"CONFIGURATION SHOULD NOT BE ACTIVE. UNEXPECTED ERROR: {other}\n",
                returncode=pytest.ExitCode.TESTS_FAILED)
    try:
        active_config = PersistentSessionManager.get_active_session().configuration_name
    except Exception as e:
        active_config = str(type(e))
    # We raise an error to prevent tests running when configurations are broken
    pytest.exit(
        f"CONFIGURATION SHOULD NOT BE ACTIVE. Active config: {active_config}",
        returncode=pytest.ExitCode.TESTS_FAILED)

def test_configurations_delete(caplog):
    caplog.set_level(logging.INFO)
    before_refresh = len(PersistentConfigurationManager.get_configurations())
    assert before_refresh > 0
    PersistentConfigurationManager.read_configurations()
    assert len(PersistentConfigurationManager.get_configurations()) == before_refresh
    assert PersistentConfigurationManager.get_configurations()[configuration_id].name == ("localhost")
    
    # First re-active the config to test if deleting an active configuration works properly
    conf = PersistentConfigurationManager.get_configuration_by_name("localhost")
    session = start_session_from_configuration(conf)
    PersistentSessionManager.set_active_session(session)
    assert PersistentSessionManager.get_active_session().configuration_name == "localhost"

    result = runner.invoke(
        app,
        ["configurations", "delete"],
        input=str(configuration_id) + "\n",
        catch_exceptions=False,
    )

    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"

def test_configurations_load(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(
        app,
        ["configurations", "load"],
        input=CONFIGURATION_PATH + "\n",
        catch_exceptions=False,
    )

    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert (
        "Added configurations"
        in caplog.text
    )

# def test_configurations_update():
#     before_refresh = len(PersistentConfigurationManager.get_configurations())
#     assert before_refresh > 0
#     PersistentConfigurationManager.read_configurations()
#     assert len(PersistentConfigurationManager.get_configurations()) == before_refresh
#     assert PersistentConfigurationManager.get_configurations()[configuration_id].name == ("localhost")

#     result = runner.invoke(
#         app,
#         ["configurations", "update"],
#         input=str(configuration_id) + "\n"
#         + GRAPHQL_URL + "\n"
#         + GATEWAY_URL + "\n"
#         + "1" + "\n",
#         catch_exceptions=False,
#     )

#     assert result.exit_code == 0,\
#         f"{caplog.text}"\
#         f"{result.stderr}"

def test_configurations_list(caplog):
    caplog.set_level(logging.INFO)
    result = runner.invoke(
        app,
        ["configurations", "list"],
        catch_exceptions=False,
    )

    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert (
        "Aerie Host Configurations"
        in result.stdout # we use Console.print for this, not log
    )
# We're activating at the end to ensure that localhost is still active
# for other integration tests.
def test_last_activate(caplog):
    caplog.set_level(logging.INFO)
    before_refresh = len(PersistentConfigurationManager.get_configurations())
    assert before_refresh > 0
    PersistentConfigurationManager.read_configurations()
    assert len(PersistentConfigurationManager.get_configurations()) == before_refresh

    assert PersistentConfigurationManager.get_configurations()[configuration_id].name == ("localhost")

    result = runner.invoke(
        app,
        ["activate", "-r", "aerie_admin"],
        input=str(configuration_id) + "\n",
        catch_exceptions=False,
    )

    assert result.exit_code == 0,\
        f"{caplog.text}"\
        f"{result.stderr}"
    assert PersistentSessionManager.get_active_session().configuration_name == "localhost"
