import pytest
import json
from pathlib import Path

from plandev_cli.plandev_host import PlanDevHostConfiguration
from plandev_cli import persistent
from plandev_cli.persistent import PersistentConfigurationManager


@pytest.fixture(autouse=True)
def persistent_path(tmp_path: Path):
    """
    Fixture sets up by reverting the PersistentConfigurationManager state and
    setting a new temporary path for the configuration file directory
    """

    # Set the paths the configuration manager uses
    persistent.CONFIGURATION_FILE_DIRECTORY = tmp_path.joinpath("tmp")
    persistent.CONFIGURATION_FILE_PATH = tmp_path.joinpath("tmp", "config.json")

    # Set configuration manager to initial state
    PersistentConfigurationManager._configurations = None
    PersistentConfigurationManager._initialized = False


def test_read_configurations_none():
    """
    Read configurations when there is no configuration file
    """
    PersistentConfigurationManager.read_configurations()
    assert PersistentConfigurationManager._configurations == []


def test_read_configurations_empty():
    """
    Read configurations when the configurations file is empty
    """
    persistent.CONFIGURATION_FILE_DIRECTORY.mkdir()
    with open(persistent.CONFIGURATION_FILE_PATH, "w") as fid:
        fid.write("[]")

    PersistentConfigurationManager.read_configurations()
    assert PersistentConfigurationManager._configurations == []


def test_read_configurations_multiple():
    """
    Read configurations when there are several defined
    """
    stored_configurations = [
        PlanDevHostConfiguration("a", "http://a.com", "http://a.com"),
        PlanDevHostConfiguration("b", "http://b.com", "http://b.com"),
        PlanDevHostConfiguration("c", "http://c.com", "http://c.com", "abcd"),
        PlanDevHostConfiguration("d", "http://d.com", "http://d.com", "abcd"),
        PlanDevHostConfiguration("e", "http://e.com", "http://e.com", None),
    ]

    persistent.CONFIGURATION_FILE_DIRECTORY.mkdir()
    with open(persistent.CONFIGURATION_FILE_PATH, "w") as fid:
        json.dump([s.to_dict() for s in stored_configurations], fid)

    PersistentConfigurationManager.read_configurations()
    read_configurations = PersistentConfigurationManager._configurations
    assert read_configurations == stored_configurations


def test_empty_username():
    """
    Write and read configurations with empty/null usernames
    """

    configurations_to_write = [
        PlanDevHostConfiguration("a", "http://a.com", "http://a.com"),
        PlanDevHostConfiguration("b", "http://b.com", "http://b.com", "abcd"),
        PlanDevHostConfiguration("c", "http://c.com", "http://c.com", None),
        PlanDevHostConfiguration("d", "http://d.com", "http://d.com"),
    ]

    # Expect the same as if a None type was passed
    expected = [
        PlanDevHostConfiguration("a", "http://a.com", "http://a.com"),
        PlanDevHostConfiguration("b", "http://b.com", "http://b.com", "abcd"),
        PlanDevHostConfiguration("c", "http://c.com", "http://c.com", None),
        PlanDevHostConfiguration("d", "http://d.com", "http://d.com"),
    ]

    persistent.CONFIGURATION_FILE_DIRECTORY.mkdir()
    with open(persistent.CONFIGURATION_FILE_PATH, "w") as fid:
        json.dump([s.to_dict() for s in configurations_to_write], fid)

    PersistentConfigurationManager.read_configurations()
    read_configurations = PersistentConfigurationManager._configurations
    assert read_configurations == expected


def test_write_configurations_none():
    """
    Write configurations when the file doesn't yet exist
    """
    configuration_to_write = [
        PlanDevHostConfiguration("a", "http://a.com", "http://a.com")
    ]
    PersistentConfigurationManager._configurations = configuration_to_write
    PersistentConfigurationManager.write_configurations()
    with open(persistent.CONFIGURATION_FILE_PATH, "r") as fid:
        assert [configuration_to_write[0].to_dict()] == json.load(fid)


def test_write_configurations():
    """
    Write configurations by overwriting the existing file
    """

    old_configuration = [PlanDevHostConfiguration("a", "http://a.com", "http://a.com")]
    persistent.CONFIGURATION_FILE_DIRECTORY.mkdir()
    with open(persistent.CONFIGURATION_FILE_PATH, "w") as fid:
        json.dump([s.to_dict() for s in old_configuration], fid)

    configuration_to_write = [
        PlanDevHostConfiguration("b", "http://b.com", "http://b.com"),
        PlanDevHostConfiguration("c", "http://c.com", "http://c.com"),
    ]

    PersistentConfigurationManager._configurations = configuration_to_write
    PersistentConfigurationManager.write_configurations()
    with open(persistent.CONFIGURATION_FILE_PATH, "r") as fid:
        assert [s.to_dict() for s in configuration_to_write] == json.load(fid)


def test_delete_configuration_broken():
    """
    Try to delete a configuration that doesn't exist
    """
    PersistentConfigurationManager._configurations = [
        PlanDevHostConfiguration("a", "http://a.com", "http://a.com"),
        PlanDevHostConfiguration("b", "http://b.com", "http://b.com"),
        PlanDevHostConfiguration(
            "c",
            "http://c.com",
            "abcd",
        ),
        PlanDevHostConfiguration(
            "d",
            "http://d.com",
            "http://d.com",
            "http://d.com/auth",
            "abcd",
        ),
    ]
    with pytest.raises(ValueError):
        PersistentConfigurationManager.delete_configuration("BAD")


def test_delete_configuration_valid():
    """
    Delete a configuration
    """

    # Define and store configuration before deleting 'b'
    configurations_before = [
        PlanDevHostConfiguration("a", "http://a.com", "http://a.com"),
        PlanDevHostConfiguration("b", "http://b.com", "http://b.com"),
        PlanDevHostConfiguration(
            "c",
            "http://c.com",
            "http://c.com",
            "abcd",
        ),
        PlanDevHostConfiguration(
            "d",
            "http://d.com",
            "http://d.com",
            "abcd",
        ),
    ]
    PersistentConfigurationManager._configurations = configurations_before
    persistent.CONFIGURATION_FILE_DIRECTORY.mkdir()
    with open(persistent.CONFIGURATION_FILE_PATH, "w") as fid:
        json.dump([s.to_dict() for s in configurations_before], fid)

    configurations_after = [
        PlanDevHostConfiguration("a", "http://a.com", "http://a.com"),
        PlanDevHostConfiguration(
            "c",
            "http://c.com",
            "http://c.com",
            "abcd",
        ),
        PlanDevHostConfiguration(
            "d",
            "http://d.com",
            "http://d.com",
            "abcd",
        ),
    ]

    PersistentConfigurationManager.delete_configuration("b")

    assert PersistentConfigurationManager._configurations == configurations_after
    with open(persistent.CONFIGURATION_FILE_PATH, "r") as fid:
        assert [s.to_dict() for s in configurations_after] == json.load(fid)


def test_update_configuration_broken():
    """
    Try to update a configuration that doesn't exist
    """
    PersistentConfigurationManager._configurations = [
        PlanDevHostConfiguration("a", "http://a.com", "http://a.com"),
        PlanDevHostConfiguration("b", "http://b.com", "http://b.com"),
        PlanDevHostConfiguration(
            "c",
            "http://c.com",
            "http://c.com",
            "abcd",
        ),
        PlanDevHostConfiguration(
            "d",
            "http://d.com",
            "http://d.com",
            "abcd",
        ),
    ]

    bad_update_config = PlanDevHostConfiguration("e", "http://e.com", "http://e.com")

    with pytest.raises(ValueError):
        PersistentConfigurationManager.update_configuration(bad_update_config)


def test_update_configuration():
    """
    Update a configuration
    """

    # Define and store configuration before updating 'c'
    configurations_before = [
        PlanDevHostConfiguration("a", "http://a.com", "http://a.com"),
        PlanDevHostConfiguration("b", "http://b.com", "http://b.com"),
        PlanDevHostConfiguration("c", "http://c.com", "http://c.com", "abcd"),
        PlanDevHostConfiguration("d", "http://d.com", "http://d.com", "abcd"),
    ]
    PersistentConfigurationManager._configurations = configurations_before
    persistent.CONFIGURATION_FILE_DIRECTORY.mkdir()
    with open(persistent.CONFIGURATION_FILE_PATH, "w") as fid:
        json.dump([s.to_dict() for s in configurations_before], fid)

    config_to_update = PlanDevHostConfiguration("c", "https://c.co", "https://c.co")

    # Preserve order
    configurations_after = [
        PlanDevHostConfiguration("a", "http://a.com", "http://a.com"),
        PlanDevHostConfiguration("b", "http://b.com", "http://b.com"),
        PlanDevHostConfiguration("c", "https://c.co", "https://c.co"),
        PlanDevHostConfiguration("d", "http://d.com", "http://d.com", "abcd"),
    ]

    PersistentConfigurationManager.update_configuration(config_to_update)

    assert PersistentConfigurationManager._configurations == configurations_after
    with open(persistent.CONFIGURATION_FILE_PATH, "r") as fid:
        assert [s.to_dict() for s in configurations_after] == json.load(fid)


def test_create_configuration_broken():
    """
    Try to define a configuration that already exists
    """

    # Define and store configuration before trying to create a new configuration
    configurations_before = [
        PlanDevHostConfiguration("a", "http://a.com", "http://a.com"),
        PlanDevHostConfiguration("b", "http://b.com", "http://b.com"),
        PlanDevHostConfiguration("c", "http://c.com", "http://c.com", "abcd"),
        PlanDevHostConfiguration("d", "http://d.com", "http://d.com", "abcd"),
    ]
    PersistentConfigurationManager._configurations = configurations_before
    persistent.CONFIGURATION_FILE_DIRECTORY.mkdir()
    with open(persistent.CONFIGURATION_FILE_PATH, "w") as fid:
        json.dump([s.to_dict() for s in configurations_before], fid)

    config_to_create = PlanDevHostConfiguration("c", "https://c.co", "https://c.co")

    with pytest.raises(ValueError):
        PersistentConfigurationManager.create_configuration(config_to_create)


def test_create_configuration_valid():
    """
    Create a configuration
    """

    # Define and store configuration before trying to create a new configuration
    configurations_before = [
        PlanDevHostConfiguration("a", "http://a.com", "http://a.com"),
        PlanDevHostConfiguration("b", "http://b.com", "http://b.com"),
        PlanDevHostConfiguration("c", "http://c.com", "http://c.com", "abcd"),
        PlanDevHostConfiguration("d", "http://d.com", "http://d.com", "abcd"),
    ]
    PersistentConfigurationManager._configurations = configurations_before
    persistent.CONFIGURATION_FILE_DIRECTORY.mkdir()
    with open(persistent.CONFIGURATION_FILE_PATH, "w") as fid:
        json.dump([s.to_dict() for s in configurations_before], fid)

    config_to_create = PlanDevHostConfiguration("e", "https://e.co", "https://e.co")

    # Preserve order
    configurations_after = [
        PlanDevHostConfiguration("a", "http://a.com", "http://a.com"),
        PlanDevHostConfiguration("b", "http://b.com", "http://b.com"),
        PlanDevHostConfiguration("c", "http://c.com", "http://c.com", "abcd"),
        PlanDevHostConfiguration("d", "http://d.com", "http://d.com", "abcd"),
        PlanDevHostConfiguration("e", "https://e.co", "https://e.co"),
    ]

    PersistentConfigurationManager.create_configuration(config_to_create)

    assert PersistentConfigurationManager._configurations == configurations_after
    with open(persistent.CONFIGURATION_FILE_PATH, "r") as fid:
        assert [s.to_dict() for s in configurations_after] == json.load(fid)
