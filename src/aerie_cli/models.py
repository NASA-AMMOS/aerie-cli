import json
from typing import Union

import typer
import arrow

from .client import AerieClient
from .client import Auth
from .schemas.client import ActivityPlanCreate

from rich.console import Console
from rich.table import Table

app = typer.Typer()

@app.command()
# Upload a single mission model
def upload(
    username: str = typer.Option(..., help="JPL username", prompt=True),
    password: str = typer.Option(
        ...,
        help="JPL password",
        prompt=True,
        hide_input=True,
    ),
    server_url: str = typer.Option(
        "http://localhost", 
        help="The URL of the Aerie deployment"
    ),
    mission_model_path: str = typer.Option(
        ..., 
        help="The input file from which to create an Aerie model", 
        prompt=True
    ),
    model_name: str = typer.Option(
        ..., 
        help="Name of mission model", 
        prompt = True
    ),
    mission: str = typer.Option(
        ..., 
        help="Mission to associate with the model", 
        prompt=True),
    time_tag_version: bool = typer.Option(
        False,
        "--time-tag-verison", 
        help="Use timestamp for model version"),
    version: str = typer.Option(
        "", 
        help="Mission model verison",
        show_default=True,
        prompt=True,)
):
    # Determine Aerie UI model version 
    if time_tag_version:
        version = arrow.utcnow.isoformat()
    
    auth = Auth(username, password)
    client = AerieClient(server_url=server_url, auth=auth)

    # Upload mission model file to Aerie server
    model_id = client.upload_mission_model(
        mission_model_path=mission_model_path, 
        project_name=model_name,
        mission=mission,
        version=version
        )

    typer.echo(f"Created new mission model: {model_name} at {client.ui_path()}/models with Model ID: {model_id}")


@app.command()
# Delete a single mission model
def prune(
    username: str = typer.Option(..., help="JPL username", prompt=True),
    password: str = typer.Option(
        ...,
        help="JPL password",
        prompt=True,
        hide_input=True
    ),
    server_url: str = typer.Option(
        "http://localhost", 
        help="The URL of the Aerie deployment"
    ),
    model_id: int = typer.Option(
        ..., 
        help= "Mission model ID to be deleted", 
        prompt=True
    )
):
    auth = Auth(username, password)
    client = AerieClient(server_url=server_url, auth=auth)

    model_name = client.delete_mission_model(model_id)
    typer.echo(f"Mission Model {model_name} with ID: {model_id} has been removed")


@app.command()
# Delete all mission models
def clean(
    username: str = typer.Option(..., help="JPL username", prompt=True),
    password: str = typer.Option(
        ...,
        help="JPL password",
        prompt=True,
        hide_input=True,
    ),
    server_url: str = typer.Option(
        "http://localhost", 
        help="The URL of the Aerie deployment"
    ),
):
    auth = Auth(username, password)
    client = AerieClient(server_url=server_url, auth=auth)

    resp = client.get_mission_models()
    for api_mission_model in resp:
        client.delete_mission_model(api_mission_model.id)
    
    typer.echo(f"All mission models at {client.ui_path()}/models have been deleted")


@app.command()
# List of current uploaded mission models
def list(
    username: str = typer.Option(..., help="JPL username", prompt=True),
    password: str = typer.Option(
        ...,
        help="JPL password",
        prompt=True,
        hide_input=True,
    ),
    server_url: str = typer.Option(
        "http://localhost", 
        help="The URL of the Aerie deployment"
    ),
):
    auth = Auth(username, password)
    client = AerieClient(server_url=server_url, auth=auth)

    resp = client.get_mission_models()
    
    # Create output table
    table = Table(title="Current Mission Models")
    table.add_column("Model ID", style="magenta")
    table.add_column("Model Name", no_wrap=True)
    for api_mission_model in resp:
        table.add_row(str(api_mission_model.id), api_mission_model.name)
    
    console = Console()
    console.print(table)

