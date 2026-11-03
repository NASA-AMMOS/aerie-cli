"""Programmatic entrypoint for CLI application.
"""
import sys
from rich.console import Console


from plandev_cli.app import app
from plandev_cli.persistent import NoActiveSessionError


def main():
    try:
        app()
    except NoActiveSessionError:
        Console().print(
            "There is no active session. Please start a session with plandev-cli activate"
        )
        sys.exit(-1)
    except Exception:
        Console().print_exception()
        sys.exit(1)


if __name__ == "__main__":
    main()  # pragma: no cover
