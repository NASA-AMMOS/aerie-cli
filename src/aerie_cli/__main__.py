"""Command-line interface."""
import typer

from . import models
from . import plans


app = typer.Typer()
app.add_typer(plans.app, name="plans")
app.add_typer(models.app, name="models")


def main():
    app()


if __name__ == "__main__":
    main(prog_name="aerie-cli")  # pragma: no cover
