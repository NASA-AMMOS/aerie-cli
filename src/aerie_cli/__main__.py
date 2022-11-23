"""Command-line interface."""
import typer

from . import models
from . import plans
from . import scheduling


app = typer.Typer()
app.add_typer(plans.app, name="plans")
app.add_typer(models.app, name="models")
app.add_typer(scheduling.app, name="scheduling")


def main():
    app()


if __name__ == "__main__":
    main()  # pragma: no cover
