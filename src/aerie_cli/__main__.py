"""Command-line interface."""
import typer
import sys
from rich.console import Console

from .commands import models
from .commands import plans
from .commands import configurations

from .persistent import NoActiveSessionError

app = typer.Typer()
app.add_typer(plans.app, name="plans")
app.add_typer(models.app, name="models")
app.add_typer(configurations.app, name="configurations")


def main():
    try:
        app()
    except NoActiveSessionError:
        Console().print(
            "There is no active session. Please start a session with aerie-cli configurations activate")
        sys.exit(-1)
    except Exception:
        Console().print_exception()


if __name__ == "__main__":
    main()  # pragma: no cover
