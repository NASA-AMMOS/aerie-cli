import json

import arrow
import typer
from rich.console import Console
from rich.table import Table

from aerie_cli.utils.sessions import get_active_session_client

app = typer.Typer()


@app.command()
def upload(
    mission_model_path: str = typer.Option(
        ..., help="The input file from which to create an Aerie model", prompt=True
    ),
    model_name: str = typer.Option(..., help="Name of mission model", prompt=True),
    mission: str = typer.Option(
        ..., help="Mission to associate with the model", prompt=True
    ),
    time_tag_version: bool = typer.Option(
        False, "--time-tag-version", help="Use timestamp for model version"
    ),
    version: str = typer.Option(
        "",
        help="Mission model verison",
        show_default=True,
        prompt=True,
    ),
    sim_template: str = typer.Option(
        "",
        help="Simulation template file",
        show_default=True,
        prompt=True,
    ),
):
    """Upload a single mission model from a .jar file."""
    # Determine Aerie UI model version
    if time_tag_version:
        version = arrow.utcnow().isoformat()

    # Initialize Aerie client
    client = get_active_session_client()

    # Upload mission model file to Aerie server
    model_id = client.upload_mission_model(
        mission_model_path=mission_model_path,
        project_name=model_name,
        mission=mission,
        version=version,
    )

    if sim_template != "":
        # Get file name
        name = sim_template.split(".")[0]

        # Read args as json
        with open(sim_template) as in_file:
            json_obj = json.load(in_file)

        # Attach sim template to model
        client.upload_sim_template(model_id=model_id, args=json_obj, name=name)
        print(f"Attached simulation template to model {model_id}.")

    typer.echo(
        f"Created new mission model: {model_name} with Model ID: {model_id}"
    )


@app.command()
def delete(
    model_id: int = typer.Option(
        ..., help="Mission model ID to be deleted", prompt=True
    ),
):
    """Delete a mission model by its model id."""

    model_name = get_active_session_client().delete_mission_model(model_id)
    typer.echo(f"Mission Model `{model_name}` with ID: {model_id} has been removed.")


@app.command()
def clean():
    """Delete all mission models."""
    client = get_active_session_client()

    resp = client.get_mission_models()
    for api_mission_model in resp:
        client.delete_mission_model(api_mission_model.id)

    typer.echo(f"All mission models have been deleted")


@app.command()
def list():
    """List uploaded mission models."""

    resp = get_active_session_client().get_mission_models()

    # Create output table
    table = Table(title="Current Mission Models")
    table.add_column("Model ID", style="magenta")
    table.add_column("Model Name", no_wrap=True)
    table.add_column("Model Version", no_wrap=True)
    for api_mission_model in resp:
        table.add_row(
            str(api_mission_model.id),
            str(api_mission_model.name),
            str(api_mission_model.version),
        )

    console = Console()
    console.print(table)
