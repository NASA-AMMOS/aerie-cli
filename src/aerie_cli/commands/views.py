import json
from typing import Union

import typer
from rich.console import Console
from rich.table import Table

from aerie_cli.utils.sessions import get_active_session_client

app = typer.Typer()


@app.command()
def download(
    id: int = typer.Option(..., help="View ID", prompt=True),
    output: str = typer.Option(..., help="The output file destination", prompt=True)
):
    """Download a view and save it locally as a JSON file."""
    view = get_active_session_client().get_view_by_id(id)
    with open(output, "w") as out_file:
        json.dump(view, out_file, indent=2)
    typer.echo(f"Wrote view to {output}")

@app.command()
def list():
    """List uploaded views."""

    client = get_active_session_client()
    resp = client.list_all_views()

    # Create output table
    table = Table(title="All Views")
    table.add_column("View ID", no_wrap=True, style="magenta")
    table.add_column("View Name", style="cyan")
    for view in resp:
        table.add_row(
            str(view.id),
            str(view.name)
        )
    Console().print(table)


@app.command()
def upload(
    input: str = typer.Option(..., help="The input file from which to create an Aerie view", prompt=True),
    name: str = typer.Option(..., help="The name of the new Aerie view", prompt=True)
):
    """Create a view from an input JSON file."""
    client = get_active_session_client()

    with open(input) as in_file:
        view_to_create = json.load(in_file)
    view_upload_object = {"name": name, "definition": view_to_create}
    plan_id = client.create_view(view_upload_object)
    typer.echo(f"Created view ID: {plan_id}")
