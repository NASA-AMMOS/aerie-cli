"""Command-line interface."""
import typer

from . import plans


app = typer.Typer()
app.add_typer(plans.app, name="plans")


def main():
    app()


if __name__ == "__main__":
    main(prog_name="aerie-cli")  # pragma: no cover
