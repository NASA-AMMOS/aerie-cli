"""persistent.py

Manage persistent storage of Aerie host configurations and active sessions
"""

from copy import deepcopy
from pathlib import Path
from typing import List
import json
import shutil
import pickle
from datetime import datetime, timedelta

from appdirs import AppDirs

from aerie_cli.aerie_host import AerieHostSession, AerieHostConfiguration

# TODO add app version s.t. changes to configuration formats can be managed
APP_DIRS = AppDirs('aerie_cli')
CONFIGURATION_FILE_DIRECTORY = Path(
    APP_DIRS.user_config_dir).resolve().absolute()
CONFIGURATION_FILE_PATH = CONFIGURATION_FILE_DIRECTORY.joinpath('config.json')

SESSION_FILE_DIRECTORY = Path(APP_DIRS.user_config_dir).resolve().absolute()
SESSION_TIMESTAMP_FSTRING = r'%Y-%jT%H-%M-%S.%f'
SESSION_TIMEOUT = timedelta(hours=12)


def delete_all_persistent_files():
    shutil.rmtree(CONFIGURATION_FILE_DIRECTORY, ignore_errors=True)
    shutil.rmtree(SESSION_FILE_DIRECTORY, ignore_errors=True)


class PersistentConfigurationManager:
    _configurations: List[AerieHostConfiguration] = None

    def __init__(self) -> None:
        """Pseudo-singleton"""
        raise NotImplementedError

    @classmethod
    def _initialize(cls) -> None:
        if cls._configurations is None:
            cls.read_configurations()

    @classmethod
    def get_configurations(cls) -> List[AerieHostConfiguration]:
        cls._initialize()
        return cls._configurations

    @classmethod
    def get_configuration_by_name(cls, configuration_name: str) -> AerieHostConfiguration:
        cls._initialize()
        try:
            return next(filter(lambda c: c.name == configuration_name, cls._configurations))
        except StopIteration:
            raise ValueError(f"Unknown configuration: {configuration_name}")

    @classmethod
    def create_configuration(cls, configuration: AerieHostConfiguration) -> None:
        cls._initialize()
        if configuration.name in [c.name for c in cls._configurations]:
            raise ValueError(
                f"Configuration already exists: {configuration.name}")

        cls._configurations.append(configuration)
        cls.write_configurations()

    @classmethod
    def update_configuration(cls, configuration: AerieHostConfiguration) -> None:
        cls._initialize()
        old_configuration = cls.get_configuration_by_name(configuration.name)
        idx = cls._configurations.index(old_configuration)
        cls._configurations[idx] = (configuration)
        cls.write_configurations()

    @classmethod
    def delete_configuration(cls, configuration_name: str) -> None:
        cls._initialize()
        old_configuration = cls.get_configuration_by_name(configuration_name)
        cls._configurations.remove(old_configuration)
        cls.write_configurations()

    @classmethod
    def write_configurations(cls) -> None:
        confs = [c.to_dict() for c in cls._configurations]
        CONFIGURATION_FILE_DIRECTORY.mkdir(exist_ok=True, parents=True)
        with open(CONFIGURATION_FILE_PATH, 'w') as fid:
            json.dump(confs, fid, indent=2)

    @classmethod
    def read_configurations(cls) -> None:
        CONFIGURATION_FILE_DIRECTORY.mkdir(exist_ok=True, parents=True)
        if CONFIGURATION_FILE_PATH.is_file():
            with open(CONFIGURATION_FILE_PATH, 'r') as fid:
                try:
                    raw_confs = json.load(fid)
                except json.JSONDecodeError:
                    raise RuntimeError(
                        f"Unable to read configuration file: {str(CONFIGURATION_FILE_PATH)}")
            cls._configurations = [
                AerieHostConfiguration.from_dict(c) for c in raw_confs]
        else:
            cls._configurations = []

    @classmethod
    def reset(cls) -> None:
        cls._configurations = None


class PersistentSessionManager:
    _active_session = None

    def __init__(self) -> None:
        """Pseudo-singleton"""
        raise NotImplementedError

    @classmethod
    def _load_active_session(cls) -> None:

        if cls._active_session is not None:
            return

        # Get any/all open sessions. List in chronological order, newest first
        fs: List[Path] = [
            f for f in SESSION_FILE_DIRECTORY.glob('*.aerie_cli.session')]
        fs.sort(reverse=True)

        if not len(fs):
            raise NoActiveSessionError

        # Delete any sessions older than the newest
        for fn in fs[1:]:
            fn.unlink()

        # Get timestamp of newest session
        fn = fs[0]
        t = datetime.strptime(
            fn.name[:-(len('.aerie_cli.session'))], SESSION_TIMESTAMP_FSTRING)

        # If session hasn't been used since timeout, mark as inactive
        if (datetime.utcnow() - t) > SESSION_TIMEOUT:
            fn.unlink()
            raise NoActiveSessionError

        # Un-pickle the session
        with open(fn, 'rb') as fid:
            session: AerieHostSession = pickle.load(fid)

        # If gateway ping fails, mark session as inactive
        if not cls.set_active_session(session):
            fn.unlink()
            raise NoActiveSessionError

    @classmethod
    def get_active_session(cls) -> AerieHostSession:
        cls._load_active_session()
        return cls._active_session

    @classmethod
    def set_active_session(cls, session: AerieHostSession) -> bool:

        if not session.ping_gateway():
            return False

        fs: List[Path] = [
            f for f in SESSION_FILE_DIRECTORY.glob('*.aerie_cli.session')]
        for fn in fs:
            fn.unlink()

        cls._active_session = session

        fn = datetime.utcnow().strftime(SESSION_TIMESTAMP_FSTRING) + '.aerie_cli.session'
        fn = SESSION_FILE_DIRECTORY.joinpath(fn)

        with open(fn, 'wb') as fid:
            pickle.dump(session, fid)

        return True

    @classmethod
    def unset_active_session(cls) -> str:
        """Unset any active session

        Returns:
            str: Name of unset session if any, otherwise None
        """

        try:
            cls._load_active_session()
        except NoActiveSessionError:
            return None

        fs: List[Path] = [
            f for f in SESSION_FILE_DIRECTORY.glob('*.aerie_cli.session')]
        for fn in fs:
            fn.unlink()

        name = deepcopy(cls._active_session.configuration_name)
        cls._active_session = None
        return name

    @classmethod
    def reset(cls) -> None:
        cls._active_session = None

        # Get any/all open sessions. List in chronological order, newest first
        fs: List[Path] = [
            f for f in SESSION_FILE_DIRECTORY.glob('*.aerie_cli.session')]
        if not len(fs):
            return
        # Delete all session files
        for fn in fs:
            fn.unlink()


class NoActiveSessionError(Exception):
    pass
