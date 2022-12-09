"""persistent.py

Manage persistent storage of Aerie host configurations and active sessions
"""

from copy import deepcopy
from pathlib import Path
from typing import List
import json
import pickle
from datetime import datetime, timedelta

from appdirs import AppDirs

from aerie_cli.aerie_host import AerieHostSession, AerieHostConfiguration

# TODO add app version s.t. changes to configuration formats can be managed
APP_DIRS = AppDirs('aerie_cli')
CONFIGURATION_FILE_DIRECTORY = Path(
    APP_DIRS.user_config_dir).resolve().absolute()
CONFIGURATION_FILE_PATH = CONFIGURATION_FILE_DIRECTORY.joinpath('config.json')

SESSION_FILE_DIRECTORY = Path(APP_DIRS.user_state_dir).resolve().absolute()
SESSION_TIMESTAMP_FSTRING = r'%Y-%jT%H:%M:%S.%f'
SESSION_TIMEOUT = timedelta(minutes=30)


def delete_all_persistent_files():
    # TODO write a method that will clear out all directories in-use (i.e., configurations and sessions)
    raise NotImplementedError


class PersistentConfigurationManager:
    configurations: List[AerieHostConfiguration]

    @classmethod
    def get_configuration_by_name(cls, configuration_name: str) -> AerieHostConfiguration:
        try:
            return next(filter(lambda c: c.name == configuration_name, cls.configurations))
        except StopIteration:
            raise ValueError(f"Unknown configuration: {configuration_name}")

    @classmethod
    def create_configuration(cls, configuration: AerieHostConfiguration) -> None:
        if configuration.name in [c.name for c in cls.configurations]:
            raise ValueError(
                f"Configuration already exists: {configuration.name}")

        cls.configurations.append(configuration)
        cls.write_configurations()

    @classmethod
    def update_configuration(cls, configuration: AerieHostConfiguration) -> None:
        cls.delete_configuration(configuration.name)
        cls.configurations.append(configuration)
        cls.write_configurations()

    @classmethod
    def delete_configuration(cls, configuration_name: str) -> None:
        old_configuration = cls.get_configuration_by_name(configuration_name)
        cls.configurations.remove(old_configuration)
        cls.write_configurations()

    @classmethod
    def write_configurations(cls) -> None:
        confs = [c.to_dict() for c in cls.configurations]
        CONFIGURATION_FILE_DIRECTORY.mkdir(exist_ok=True)
        with open(CONFIGURATION_FILE_PATH, 'w') as fid:
            json.dump(confs, fid, indent=2)

    @classmethod
    def read_configurations(cls) -> None:
        CONFIGURATION_FILE_DIRECTORY.mkdir(exist_ok=True)
        if CONFIGURATION_FILE_PATH.is_file():
            with open(CONFIGURATION_FILE_PATH, 'r') as fid:
                try:
                    raw_confs = json.load(fid)
                except json.JSONDecodeError:
                    raise RuntimeError(
                        f"Unable to read configuration file: {str(CONFIGURATION_FILE_PATH)}")
            cls.configurations = [
                AerieHostConfiguration.from_dict(c) for c in raw_confs]
        else:
            cls.configurations = []


PersistentConfigurationManager.read_configurations()


class PersistentSessionManager:
    _active_session = None

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
        if not session.ping_gateway():
            fn.unlink()
            raise NoActiveSessionError

        cls.set_active_session(session)

    @classmethod
    def get_active_session(cls) -> AerieHostSession:
        cls._load_active_session()
        return cls._active_session

    @classmethod
    def set_active_session(cls, session: AerieHostSession) -> bool:

        cls._active_session = session

        if not session.ping_gateway():
            return False

        fs: List[Path] = [
            f for f in SESSION_FILE_DIRECTORY.glob('*.aerie_cli.session')]
        for fn in fs:
            fn.unlink()

        fn = datetime.utcnow().strftime(SESSION_TIMESTAMP_FSTRING) + '.aerie_cli.session'
        fn = SESSION_FILE_DIRECTORY.joinpath(fn)

        with open(fn, 'wb') as fid:
            pickle.dump(session, fid)

    @classmethod
    def unset_active_session(cls) -> str:
        cls._load_active_session()

        fs: List[Path] = [
            f for f in SESSION_FILE_DIRECTORY.glob('*.aerie_cli.session')]
        for fn in fs:
            fn.unlink()

        if cls._active_session:
            name = deepcopy(cls._active_session.configuration_name)
            cls._active_session = None
            return name
        else:
            return None


class NoActiveSessionError(Exception):
    pass
