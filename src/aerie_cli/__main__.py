"""Command-line interface."""
import typer
import sys
from rich.console import Console

from aerie_cli.commands import models
from aerie_cli.commands import plans
from aerie_cli.commands import configurations
from aerie_cli.commands import expansion
from aerie_cli.commands import scheduling

from .persistent import NoActiveSessionError

app = typer.Typer()
app.add_typer(plans.app, name="plans")
app.add_typer(models.app, name="models")
app.add_typer(configurations.app, name="configurations")
app.add_typer(expansion.app, name="expansion")
app.add_typer(scheduling.app, name="scheduling")


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
