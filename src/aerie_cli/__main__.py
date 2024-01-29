"""Programmatic entrypoint for CLI application.
"""
import sys
import logging
import traceback

from aerie_cli.app import app
from aerie_cli.persistent import NoActiveSessionError, CURRENT_LOG_PATH
from aerie_cli.__version__ import __version__

def main():
    try:
        app()
    except NoActiveSessionError:
        logging.error(
            "There is no active session. Please start a session with aerie-cli activate"
        )
        sys.exit(-1)
    except Exception as e:
        logging.error(f"{type(e).__name__}\n"
                    "Check log file for more information:\n"
                    f"{CURRENT_LOG_PATH}")
        # We don't want to print the full traceback,
        # so we use debug
        logging.debug(traceback.format_exc())


if __name__ == "__main__":
    main()  # pragma: no cover
