"""Command-line interface."""
import typer

from .commands import models
from .commands import plans
from .commands import configurations


app = typer.Typer()
app.add_typer(plans.app, name="plans")
app.add_typer(models.app, name="models")
app.add_typer(configurations.app, name="configurations")


def main():
    app()


if __name__ == "__main__":
    main()  # pragma: no cover
