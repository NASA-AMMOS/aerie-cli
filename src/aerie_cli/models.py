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


