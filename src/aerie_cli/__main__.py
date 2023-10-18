"""Programmatic entrypoint for CLI application.
"""
import sys
import logging
import traceback

from aerie_cli.app import app
from aerie_cli.persistent import NoActiveSessionError, clear_old_log_files, CURRENT_LOG_PATH
from aerie_cli.__version__ import __version__

def main():
    clear_old_log_files()
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    file_handler = logging.FileHandler(filename=str(CURRENT_LOG_PATH),
                                        mode='w',
                                        encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    console_formatter = logging.Formatter(
        '%(message)s'
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO) # Set the level of the stream and file handlers to different ones
                                        # Debug should be in file, others should go into stdout
    console_handler.setFormatter(console_formatter)
    logging.basicConfig(level=logging.DEBUG,
                        handlers=[file_handler,
                                  console_handler])
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
