import json
from typing import Union

import typer
import arrow

from .client import AerieClient
from .client import Auth
from .schemas.client import ActivityPlanCreate

app = typer.Typer()

@app.command()
def upload(
    username: str = typer.Option(..., help="JPL username", prompt=True),
    password: str = typer.Option(
        ...,
        help="JPL password",
        prompt=True,
        hide_input=True,
    ),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
    mission_model_path: str = typer.Option(
        ..., help="The input file from which to create an Aerie model", prompt=True
    ),
    model_name: str = typer.Option(
        ..., help="Name of mission model", prompt = True
    )
):
    auth = Auth(username, password)
    client = AerieClient(server_url=server_url, auth=auth)
    
    # Upload mission model file to Aerie server
    model_id = client.upload_mission_model(mission_model_path=mission_model_path, project_name=model_name)

    typer.echo(f"Created new mission model: {model_name} at {client.ui_path()}/models with Model ID: {model_id}")


@app.command()
def delete(
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
    delete_all: bool = typer.Option(False, help = "Delete all current mission models"),
    model_id: int = typer.Option(None, 
        help= "Mission model ID to be deleted", 
        prompt=True,
        show_default=True)
):
    auth = Auth(username, password)
    client = AerieClient(server_url=server_url, auth=auth)

    # Get all models if delete all
    if delete_all:
        resp = client.get_mission_models()
        for model in resp:
            client.delete_mission_model(model["id"])

    # If model id id provided, delete that model
    elif model_id is not None:
        model_name = client.delete_mission_model(model_id)
        typer.echo(f"Mission Model {model_name} with ID: {model_id} has been removed")

    # Prompt user to input a model id or delete all
    else:
        typer.echo(f"Error: Please provide a model id to delete or use --delete-all flag to delete all models")

@app.command()
def show(
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
    
    for model in resp:
        typer.echo(f"Model Name: {model['name']}, ID:  {model['id']}")

