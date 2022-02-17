import json
from typing import Union

import typer
import arrow

from .client import AerieClient
from .client import Auth
from .schemas.client import ActivityPlanCreate

app = typer.Typer()


@app.command()
def download(
    username: str = typer.Option(..., help="JPL username", prompt=True),
    password: str = typer.Option(
        ...,
        help="JPL password",
        prompt=True,
        hide_input=True,
    ),
    id: int = typer.Option(..., help="Plan ID", prompt=True),
    output: str = typer.Option(..., help="The output file destination", prompt=True),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
):
    """Download a plan and save it locally as a JSON file."""
    auth = Auth(username, password)
    client = AerieClient(server_url=server_url, auth=auth)
    plan = client.get_activity_plan(id)
    with open(output, "w") as out_file:
        out_file.write(plan.to_json())
    typer.echo(f"Wrote activity plan to {output}")


@app.command()
def upload(
    username: str = typer.Option(..., help="JPL username", prompt=True),
    password: str = typer.Option(
        ...,
        help="JPL password",
        prompt=True,
        hide_input=True,
    ),
    input: str = typer.Option(
        ..., help="The input file from which to create an Aerie plan", prompt=True
    ),
    model_id: int = typer.Option(
        ..., help="The mission model ID to associate with the plan", prompt=True
    ),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
    time_tag: bool = typer.Option(False, help = "Append time tag to plan name")
):
    """Create a plan from an input JSON file."""
    auth = Auth(username, password)
    client = AerieClient(server_url=server_url, auth=auth)
    with open(input) as in_file:
        contents = in_file.read()
    plan_to_create = ActivityPlanCreate.from_json(contents)
    if time_tag:
        plan_to_create.name += arrow.utcnow().isoformat("|")
    plan_id = client.create_activity_plan(model_id, plan_to_create)
    typer.echo(f"Created plan at: {client.ui_path()}/plans/{plan_id}")


@app.command()
def duplicate(
    username: str = typer.Option(..., help="JPL username", prompt=True),
    password: str = typer.Option(
        ...,
        help="JPL password",
        prompt=True,
        hide_input=True,
    ),
    id: int = typer.Option(..., help="Plan ID", prompt=True),
    duplicated_plan_name: str = typer.Option(
        ..., help="The name for the duplicated plan", prompt=True
    ),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
):
    """Duplicate an existing plan."""
    auth = Auth(username, password)
    client = AerieClient(server_url=server_url, auth=auth)
    plan = client.get_activity_plan(id)
    plan_to_duplicate = ActivityPlanCreate.from_plan_read(plan)
    plan_to_duplicate.name = duplicated_plan_name
    duplicated_plan_id = client.create_activity_plan(plan.model_id, plan_to_duplicate)
    typer.echo(
        f"Duplicated activity plan at: {client.ui_path()}/plans/{duplicated_plan_id}"
    )


@app.command()
def simulate(
    username: str = typer.Option(..., help="JPL username", prompt=True),
    password: str = typer.Option(
        ...,
        help="JPL password",
        prompt=True,
        hide_input=True,
    ),
    id: int = typer.Option(..., help="Plan ID", prompt=True),
    output: Union[str, None] = typer.Option(
        None, help="The output file destination for simulation results (if desired)"
    ),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
    poll_period: int = typer.Option(
        5,
        help="The period (seconds) at which to poll for simulation completion",
    ),
):
    """Download a plan and save it locally as a JSON file."""
    auth = Auth(username, password)
    client = AerieClient(server_url=server_url, auth=auth)
    typer.echo(f"Simulating activity plan at: {client.ui_path()}/plans/{id}")
    results = client.simulate_plan(id, poll_period)
    typer.echo(f"Simulated activity plan at: {client.ui_path()}/plans/{id}")
    if output:
        typer.echo("Writing simulation results...")
        with open(output, "w") as out_file:
            out_file.write(json.dumps(results, indent=4))
        typer.echo(f"Wrote results to {output}")


if __name__ == "__main__":
    app()
