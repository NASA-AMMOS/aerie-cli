from aerie_cli.aerie_client import AerieClient
from aerie_cli.persistent import PersistentSessionManager

def get_active_session_client():
    # TODO see if it's possible to call the configurations select command in the event one isn't running?
    session = PersistentSessionManager.get_active_session()
    return AerieClient(session)
