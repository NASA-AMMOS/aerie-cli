"""Programmatic entrypoint for CLI application.
"""
import sys
from rich.console import Console


from aerie_cli.app import app
from aerie_cli.persistent import NoActiveSessionError
from aerie_cli.__version__ import __version__


def main():
    try:
        app()
    except NoActiveSessionError:
        Console().print(
            "There is no active session. Please start a session with aerie-cli activate"
        )
        sys.exit(-1)
    except Exception:
        Console().print_exception()


if __name__ == "__main__":
    main()  # pragma: no cover
