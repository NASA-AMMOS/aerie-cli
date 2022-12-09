import pytest
import pickle
import datetime
from pathlib import Path

from aerie_cli import persistent

from aerie_cli.aerie_host import AerieHostSession
from aerie_cli.persistent import PersistentSessionManager


class MockAerieHostSession(AerieHostSession):
    """
    Mock Aerie Host Session for testing session persistence.
    """

    def __init__(self, ping_success: bool = True, name: str = "Test") -> None:
        self.ping_success = ping_success
        self.configuration_name = name
        self.graphql_url = "Test"
        self.gateway_url = "Test"

    def ping_gateway(self) -> bool:
        return self.ping_success


TEST_TIME = datetime.datetime(2025, 1, 1, 0, 0, 0)


@pytest.fixture
def persistent_path(tmp_path: Path):

    # Set the path the session manager uses
    persistent.SESSION_FILE_DIRECTORY = tmp_path

    # Set session manager to initial state
    PersistentSessionManager._active_session = None

    return tmp_path


def test_get_session_empty(persistent_path: Path):
    """
    Test loading a persistent session with no saved sessions
    """

    with pytest.raises(persistent.NoActiveSessionError):
        PersistentSessionManager.get_active_session()


def test_get_session_expired(persistent_path: Path):
    """
    Test loading a persistent session with an expired timestamp
    """

    # Create a mock old session with an "expired" session
    old_session = MockAerieHostSession()
    old_time = datetime.datetime.utcnow() - persistent.SESSION_TIMEOUT - \
        datetime.timedelta(seconds=1)
    old_fn = old_time.strftime(
        persistent.SESSION_TIMESTAMP_FSTRING) + '.aerie_cli.session'
    with open(persistent_path.joinpath(old_fn), 'wb') as fid:
        pickle.dump(old_session, fid)

    # Expect this to fail
    with pytest.raises(persistent.NoActiveSessionError):
        PersistentSessionManager.get_active_session()


def test_get_session_broken(persistent_path: Path):
    """
    Test loading a persistent session which fails to ping the gateway
    """

    # Create a mock old session which fails the ping test
    old_session = MockAerieHostSession(False)
    old_time = datetime.datetime.utcnow()
    old_fn = old_time.strftime(
        persistent.SESSION_TIMESTAMP_FSTRING) + '.aerie_cli.session'
    with open(persistent_path.joinpath(old_fn), 'wb') as fid:
        pickle.dump(old_session, fid)

    # Expect this to fail
    with pytest.raises(persistent.NoActiveSessionError):
        PersistentSessionManager.get_active_session()


def test_get_session(persistent_path: Path):
    """
    Test loading a valid persistent session.
    Only one file in the session directory.
    """

    # Create a mock good session
    old_session = MockAerieHostSession()
    old_time = datetime.datetime.utcnow()
    old_fn = old_time.strftime(
        persistent.SESSION_TIMESTAMP_FSTRING) + '.aerie_cli.session'
    with open(persistent_path.joinpath(old_fn), 'wb') as fid:
        pickle.dump(old_session, fid)

    # Expect this to pass
    s = PersistentSessionManager.get_active_session()
    assert isinstance(s, AerieHostSession)


def test_get_session_multiple(persistent_path: Path):
    """
    Test loading a valid persistent session.
    Only one file in the session directory.
    """

    # Create a mock good session
    for i in range(2):
        old_session = MockAerieHostSession()
        old_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=i)
        old_fn = old_time.strftime(
            persistent.SESSION_TIMESTAMP_FSTRING) + '.aerie_cli.session'
        with open(persistent_path.joinpath(old_fn), 'wb') as fid:
            pickle.dump(old_session, fid)

    # Expect this to pass
    s = PersistentSessionManager.get_active_session()
    assert isinstance(s, AerieHostSession)

    # Check that the directory has been cleaned up
    assert len(list(persistent_path.iterdir())) == 1


def test_set_session_broken(persistent_path: Path):
    """
    Test setting a single session that fails ping test
    """
    session = MockAerieHostSession(False)

    # Method should return false because it doesn't set the session
    assert PersistentSessionManager.set_active_session(session) == False

    # Check that the directory is still empty
    assert len(list(persistent_path.iterdir())) == 0


def test_set_session(persistent_path: Path):
    """
    Test setting a single session that passes the ping test. There isn't 
    an active session.
    """
    session = MockAerieHostSession()

    # Method should return true
    assert PersistentSessionManager.set_active_session(session) == True

    # Check that the directory has a file in it
    assert len(list(persistent_path.iterdir())) == 1


def test_set_session(persistent_path: Path):
    """
    Test setting a single session that passes the ping test while another
    active session is set.
    """
    session_1 = MockAerieHostSession()
    session_2 = MockAerieHostSession()

    PersistentSessionManager.set_active_session(session_1)

    # Method should return true
    assert PersistentSessionManager.set_active_session(session_2) == True

    # Check that the directory still has only one file in it
    assert len(list(persistent_path.iterdir())) == 1


def test_unset_session_startup_clean(persistent_path: Path):
    """
    Test unsetting active session on a clean startup without a persistent session saved.
    """

    assert PersistentSessionManager.unset_active_session() == None


def test_unset_session_startup_persistent(persistent_path: Path):
    """
    Test unsetting a session an a clean startup with a persistent session saved.
    """

    # Create a mock good session
    old_session = MockAerieHostSession(name="Old Session")
    old_time = datetime.datetime.utcnow()
    old_fn = old_time.strftime(
        persistent.SESSION_TIMESTAMP_FSTRING) + '.aerie_cli.session'
    with open(persistent_path.joinpath(old_fn), 'wb') as fid:
        pickle.dump(old_session, fid)

    assert PersistentSessionManager.unset_active_session() == "Old Session"


def test_unset_session_active(persistent_path: Path):
    """
    Test unsetting a session that was set during this runtime.
    """
    old_session = MockAerieHostSession(name="Old Session")
    PersistentSessionManager.set_active_session(old_session)

    assert PersistentSessionManager.unset_active_session() == "Old Session"
