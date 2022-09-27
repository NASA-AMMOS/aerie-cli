import json
from typing import Union

import arrow
import typer
from rich.console import Console
from rich.table import Table

from .client import auth_helper
from .schemas.client import ActivityPlanCreate

# from aerie_cli.schemas.api import ApiResourceSampleResults
# from .schemas.client import SimulationResults

app = typer.Typer()


@app.command()
def download(
    sso: str = typer.Option("", help="SSO Token"),
    username: str = typer.Option("", help="JPL username"),
    password: str = typer.Option(
        "",
        help="JPL password",
        hide_input=True,
    ),
    id: int = typer.Option(..., help="Plan ID", prompt=True),
    output: str = typer.Option(..., help="The output file destination", prompt=True),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
):
    """Download a plan and save it locally as a JSON file."""
    client = auth_helper(
        sso=sso, username=username, password=password, server_url=server_url
    )

    plan = client.get_activity_plan_by_id(id)
    with open(output, "w") as out_file:
        out_file.write(plan.to_json(indent=2))
    typer.echo(f"Wrote activity plan to {output}")

@app.command()
def download_simulation(
    sso: str = typer.Option("", help="SSO Token"),
    username: str = typer.Option("", help="JPL username"),
    password: str = typer.Option(
        "",
        help="JPL password",
        hide_input=True,
    ),
    plan_id: int = typer.Option(..., help="Plan ID", prompt=True),
    sim_id: int = typer.Option(..., help="Simulation ID", prompt=True),
    output: str = typer.Option(..., help="The output file destination", prompt=True),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
):
    """Download a simulation result and save it locally as a JSON file."""
    client = auth_helper(
        sso=sso, username=username, password=password, server_url=server_url
    )

    sim = client.get_simulation_results(plan_id, sim_id)
    with open(output, "w") as out_file:
        out_file.write(json.dumps(sim, indent=2))
    typer.echo(f"Wrote activity plan to {output}")


@app.command()
def upload(
    sso: str = typer.Option("", help="SSO Token"),
    username: str = typer.Option("", help="JPL username"),
    password: str = typer.Option(
        "",
        help="JPL password",
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
    time_tag: bool = typer.Option(False, help="Append time tag to plan name"),
):
    """Create a plan from an input JSON file."""
    client = auth_helper(
        sso=sso, username=username, password=password, server_url=server_url
    )

    with open(input) as in_file:
        contents = in_file.read()
    plan_to_create = ActivityPlanCreate.from_json(contents)
    if time_tag:
        plan_to_create.name += arrow.utcnow().format("YYYY-MM-DDTHH-mm-ss")
    plan_id = client.create_activity_plan(model_id, plan_to_create)
    typer.echo(f"Created plan at: {client.ui_path()}/plans/{plan_id}")


@app.command()
def duplicate(
    sso: str = typer.Option("", help="SSO Token"),
    username: str = typer.Option("", help="JPL username"),
    password: str = typer.Option(
        "",
        help="JPL password",
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
    client = auth_helper(
        sso=sso, username=username, password=password, server_url=server_url
    )

    plan = client.get_activity_plan_by_id(id)
    plan_to_duplicate = ActivityPlanCreate.from_plan_read(plan)
    plan_to_duplicate.name = duplicated_plan_name
    duplicated_plan_id = client.create_activity_plan(plan.model_id, plan_to_duplicate)
    typer.echo(
        f"Duplicated activity plan at: {client.ui_path()}/plans/{duplicated_plan_id}"
    )


@app.command()
def simulate(
    sso: str = typer.Option("", help="SSO Token"),
    username: str = typer.Option("", help="JPL username"),
    password: str = typer.Option(
        "",
        help="JPL password",
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
    """Simulate a plan and optionally download the results."""
    client = auth_helper(
        sso=sso, username=username, password=password, server_url=server_url
    )

    typer.echo(f"Simulating activity plan at: {client.ui_path()}/plans/{id}")
    sim_dataset_id = client.simulate_plan(id, poll_period)
    res = client.get_simulation_results(id, sim_dataset_id)
            
    if output:
        with open(output, "w") as out_file:
            out_file.write(json.dumps(res, indent=2))
        typer.echo(f"Wrote simulation results to {output}")
        


@app.command()
def list(
    sso: str = typer.Option("", help="SSO Token"),
    username: str = typer.Option("", help="JPL username"),
    password: str = typer.Option(
        "",
        help="JPL password",
        hide_input=True,
    ),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
):
    """List uploaded plans."""
    client = auth_helper(
        sso=sso, username=username, password=password, server_url=server_url
    )

    resp = client.get_all_activity_plans()

    # Create output table
    table = Table(title="Current Activity Plans")
    table.add_column("Plan ID", no_wrap=True, style="magenta")
    table.add_column("Plan Name", style="cyan")
    table.add_column("Plan Start Time", no_wrap=True)
    table.add_column("Plan End Time", no_wrap=True)
    table.add_column("Simulation ID", no_wrap=True)
    table.add_column("Model ID", no_wrap=True)
    for activity_plan in resp:
        table.add_row(
            str(activity_plan.id),
            str(activity_plan.name),
            str(activity_plan.start_time),
            str(activity_plan.end_time),
            str(activity_plan.sim_id),
            str(activity_plan.model_id),
        )

    console = Console()
    console.print(table)


@app.command()
def create_config(
    sso: str = typer.Option("", help="SSO Token"),
    username: str = typer.Option("", help="JPL username"),
    password: str = typer.Option(
        "",
        help="JPL password",
        hide_input=True,
    ),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
    plan_id: int = typer.Option(..., help="Plan ID", prompt=True),
    arg_file: str = typer.Option(
        ..., help="JSON file with configuration arguments", prompt=True
    ),
):
    """Clean and Create New Configuration for a Given Plan."""
    client = auth_helper(
        sso=sso, username=username, password=password, server_url=server_url
    )

    with open(arg_file) as in_file:
        contents = in_file.read()

    json_obj = json.loads(contents)

    resp = client.create_config_args(plan_id=plan_id, args=json_obj)

    print("Configuration Arguments for Plan ID:", plan_id)
    for arg in resp:
        print("(*) " + arg + ":", resp[arg])


@app.command()
def update_config(
    sso: str = typer.Option("", help="SSO Token"),
    username: str = typer.Option("", help="JPL username"),
    password: str = typer.Option(
        "",
        help="JPL password",
        hide_input=True,
    ),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
    plan_id: int = typer.Option(..., help="Plan ID", prompt=True),
    arg_file: str = typer.Option(
        ..., help="JSON file with configuration arguments", prompt=True
    ),
):
    """Update Configuration for a Given Plan."""
    client = auth_helper(
        sso=sso, username=username, password=password, server_url=server_url
    )

    with open(arg_file) as in_file:
        contents = in_file.read()

    json_obj = json.loads(contents)

    resp = client.update_config_args(plan_id=plan_id, args=json_obj)

    print("Configuration Arguments for Plan ID:", plan_id)
    for arg in resp:
        print("(*) " + arg + ":", resp[arg])


@app.command()
def delete(
    sso: str = typer.Option("", help="SSO Token"),
    username: str = typer.Option("", help="JPL username"),
    password: str = typer.Option(
        "",
        help="JPL password",
        hide_input=True,
    ),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
    plan_id: int = typer.Option(..., help="Plan ID to be deleted", prompt=True),
):
    """Delete an activity plan by its id."""
    client = auth_helper(
        sso=sso, username=username, password=password, server_url=server_url
    )

    plan_name = client.delete_plan(plan_id)
    typer.echo(f"Plan `{plan_name}` with ID: {plan_id} has been removed.")


@app.command()
def clean(
    sso: str = typer.Option("", help="SSO Token"),
    username: str = typer.Option("", help="JPL username"),
    password: str = typer.Option(
        "",
        help="JPL password",
        hide_input=True,
    ),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
):
    """Delete all activity plans."""
    client = auth_helper(
        sso=sso, username=username, password=password, server_url=server_url
    )

    resp = client.get_all_activity_plans()
    for activity_plan in resp:
        client.delete_plan(activity_plan.id)

    typer.echo(f"All activity plans at {client.ui_plans_path()} have been deleted")


if __name__ == "__main__":
    app()
