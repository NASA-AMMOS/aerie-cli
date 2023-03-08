import json
from typing import Union

import arrow
import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

from aerie_cli.utils.sessions import get_active_session_client
from aerie_cli.schemas.client import ActivityPlanCreate

app = typer.Typer()


@app.command()
def download(
    id: int = typer.Option(..., help="Plan ID", prompt=True),
    full_args: str = typer.Option(
        "",
        help="true, false, or comma separated list of activity types for which to get full arguments.  Otherwise only modified arguments are returned.  Defaults to false.",
    ),
    output: str = typer.Option(..., help="The output file destination", prompt=True)
):
    """Download a plan and save it locally as a JSON file."""
    plan = get_active_session_client().get_activity_plan_by_id(id, full_args)
    with open(output, "w") as out_file:
        out_file.write(plan.to_json(indent=2))
    typer.echo(f"Wrote activity plan to {output}")


@app.command()
def download_simulation(
    sim_id: int = typer.Option(
        ..., '--sim-id', '-s',
        help="Simulation ID", prompt=True),
    output: str = typer.Option(
        ..., '--output', '-s',
        help="The output file destination", prompt=True)
):
    """
    Download simulated activity instances and save to a JSON file
    """
    client = get_active_session_client()
    simulated_activities = client.get_simulation_results(sim_id)
    with open(output, "w") as out_file:
        out_file.write(json.dumps(simulated_activities, indent=2))
        typer.echo(f"Wrote activity plan to {output}")


@app.command()
def download_resources(
    sim_id: int = typer.Option(
        ..., '--sim-id', '-s',
        help="Simulation Dataset ID", prompt='Simulation Dataset ID'),
    csv: bool = typer.Option(
        False, "--csv/--json", help="Download as CSV"
    ),
    output: str = typer.Option(
        ..., '--output', '-o',
        help="The output file destination", prompt=True),
    absolute_time: bool = typer.Option(
        False, "--absolute-time", help="Change relative timestamps to absolute"
    ),
    specific_states: str = typer.Option(
        None, help="The file with the specific states [defaults to all]"
    )
):
    """
    Download resource timelines from a simulation and save to either JSON or CSV.

    JSON resource timelines are formatted as lists of time-value pairs. Relative timestamps are milliseconds since 
    plan start time. Absolute timestamps are of the form YYYY-DDDTh:mm:ss.sss

    CSV resource timeline relative timestamps are seconds since plan start time. Absolute timestamps are formatted the 
    same as the JSON outputs.
    """
    client = get_active_session_client()

    # reads the states
    contents = []
    if specific_states:
        with open(specific_states) as in_file:
            for line in in_file:
                contents.append(line.strip("\n"))

    # Get start time of plan
    plan_id = client.get_plan_id_by_sim_id(sim_id)
    start_time = client.get_activity_plan_by_id(plan_id, "").start_time
    # get resource timelines
    resources = client.get_resource_samples(sim_id, contents)

    if csv:
        # the key is the time and the value is a list of tuples: (activity, state)
        time_dictionary = {}

        # this stores the header names for the CSV
        field_name = ["Time (s)"]
        if absolute_time:
            field_name = ["Time (YYYY-DDDThh:mm:ss.sss)"]

        for activity in resources.get("resourceSamples"):
            list = resources.get("resourceSamples").get(activity)
            field_name.append(activity)
            for i in list:
                time_dictionary.setdefault(i.get("x"), []).append(
                    (activity, i.get("y"))
                )

        # a list of dictionaries that will be fed into the DictWriter method
        csv_dictionary = []

        for time in time_dictionary:
            seconds = 0
            if time != 0:
                seconds = time / 1000000
            if absolute_time:
                formatted = start_time.shift(seconds=seconds)
                formatted = formatted.format("YYYY-DDDDTHH:mm:ss.SSS")
                tempDict = {"Time (YYYY-DDDThh:mm:ss.sss)": formatted}
            else:
                tempDict = {"Time (s)": seconds}
            for activity in time_dictionary.get(time):
                tempDict[activity[0]] = activity[1]
            csv_dictionary.append(tempDict)

        # Sort the dictionary by time
        if absolute_time:
            sorted_by_time = sorted(csv_dictionary, key=lambda d: d["Time (YYYY-DDDThh:mm:ss.sss)"])
        else:
            sorted_by_time = sorted(csv_dictionary, key=lambda d: d["Time (s)"])

        # use panda to fill in missing data
        df = pd.DataFrame(sorted_by_time)
        # 'ffill' will fill each missing row with the value of the nearest one above it.
        df.fillna(method="ffill", inplace=True)

        # write to file
        with open(output, "w") as out_file:
            df.to_csv(out_file, index=False, header=field_name)
            typer.echo(f"Wrote resource timelines to {output}")

    else:
        if absolute_time:
            for activity in resources.get("resourceSamples"):
                list = resources.get("resourceSamples").get(activity)
                for i in list:
                    milliseconds = i.get("x")
                    seconds = 0
                    if milliseconds != 0:
                        seconds = milliseconds/1000000
                    i["x"] = str(start_time.shift(seconds=seconds).format("YYYY-DDDDTHH:mm:ss.SSS"))

        # write to file
        with open(output, "w") as out_file:
            out_file.write(json.dumps(resources, indent=2))
            typer.echo(f"Wrote resource timelines to {output}")


@app.command()
def upload(
    input: str = typer.Option(
        ..., help="The input file from which to create an Aerie plan", prompt=True
    ),
    model_id: int = typer.Option(
        ..., help="The mission model ID to associate with the plan", prompt=True
    ),
    time_tag: bool = typer.Option(False, help="Append time tag to plan name"),
):
    """Create a plan from an input JSON file."""
    client = get_active_session_client()

    with open(input) as in_file:
        contents = in_file.read()
    plan_to_create = ActivityPlanCreate.from_json(contents)
    if time_tag:
        plan_to_create.name += arrow.utcnow().format("YYYY-MM-DDTHH-mm-ss")
    plan_id = client.create_activity_plan(model_id, plan_to_create)
    typer.echo(f"Created plan ID: {plan_id}")


@app.command()
def duplicate(
    id: int = typer.Option(..., help="Plan ID", prompt=True),
    duplicated_plan_name: str = typer.Option(
        ..., help="The name for the duplicated plan", prompt=True
    )
):
    """Duplicate an existing plan."""
    client = get_active_session_client()

    plan = client.get_activity_plan_by_id(id)
    plan_to_duplicate = ActivityPlanCreate.from_plan_read(plan)
    plan_to_duplicate.name = duplicated_plan_name
    duplicated_plan_id = client.create_activity_plan(plan.model_id, plan_to_duplicate)
    typer.echo(
        f"Duplicated activity plan at: {client.ui_path()}/plans/{duplicated_plan_id}"
    )


@app.command()
def simulate(
    id: int = typer.Option(..., help="Plan ID", prompt=True),
    output: Union[str, None] = typer.Option(
        None, help="The output file destination for simulation results (if desired)"
    ),
    poll_period: int = typer.Option(
        5,
        help="The period (seconds) at which to poll for simulation completion",
    ),
):
    """Simulate a plan and optionally download the results."""
    client = get_active_session_client()

    start_time = arrow.utcnow()
    sim_dataset_id = client.simulate_plan(id, poll_period)
    end_time = arrow.utcnow()
    res = client.get_simulation_results(sim_dataset_id)
    total_sim_time = end_time - start_time
    typer.echo(f"Simulation completed in " + str(total_sim_time))

    if output:
        with open(output, "w") as out_file:
            out_file.write(json.dumps(res, indent=2))
        typer.echo(f"Wrote simulation results to {output}")


@app.command()
def list():
    """List uploaded plans."""

    client = get_active_session_client()
    resp = client.list_all_activity_plans()

    # Create output table
    table = Table(title="Current Activity Plans")
    table.add_column("Plan ID", no_wrap=True, style="magenta")
    table.add_column("Plan Name", style="cyan")
    table.add_column("Plan Start Time", no_wrap=True)
    table.add_column("Plan End Time", no_wrap=True)
    table.add_column("Latest Sim. Dataset ID", no_wrap=True)
    table.add_column("Model ID", no_wrap=True)
    for activity_plan in resp:
        sim_ids = client.get_simulation_dataset_ids_by_plan_id(activity_plan.id)
        if len(sim_ids):
            simulation_dataset_id = str(max(sim_ids))
        else:
            simulation_dataset_id = ''
            
        table.add_row(
            str(activity_plan.id),
            activity_plan.name,
            activity_plan.start_time.format("YYYY-DDDDTHH:mm:ss.SSS"),
            activity_plan.end_time.format("YYYY-DDDDTHH:mm:ss.SSS"),
            simulation_dataset_id,
            str(activity_plan.model_id)
        )

    Console().print(table)


@app.command()
def create_config(
    plan_id: int = typer.Option(..., help="Plan ID", prompt=True),
    arg_file: str = typer.Option(
        ..., help="JSON file with configuration arguments", prompt=True
    ),
):
    """Clean and Create New Configuration for a Given Plan."""
    with open(arg_file) as fid:
        json_obj = json.load(fid)

    resp = get_active_session_client().create_config_args(plan_id=plan_id, args=json_obj)

    typer.echo(f"Configuration Arguments for Plan ID: {plan_id}")
    for arg in resp:
        typer.echo(f"(*) {arg}: {resp[arg]}")


@app.command()
def update_config(
    plan_id: int = typer.Option(..., help="Plan ID", prompt=True),
    arg_file: str = typer.Option(
        ..., help="JSON file with configuration arguments", prompt=True
    ),
):
    """Update Configuration for a Given Plan."""

    with open(arg_file) as fid:
        json_obj = json.load(fid)

    resp = get_active_session_client().update_config_args(plan_id=plan_id, args=json_obj)

    typer.echo(f"Configuration Arguments for Plan ID: {plan_id}")
    for arg in resp:
        typer.echo(f"(*) {arg}: {resp[arg]}")


@app.command()
def delete(
    plan_id: int = typer.Option(..., help="Plan ID to be deleted", prompt=True),
):
    """Delete an activity plan by its id."""

    plan_name = get_active_session_client().delete_plan(plan_id)
    typer.echo(f"Plan `{plan_name}` with ID: {plan_id} has been removed.")


@app.command()
def clean():
    """Delete all activity plans."""
    client = get_active_session_client()

    resp = client.get_all_activity_plans()
    for activity_plan in resp:
        client.delete_plan(activity_plan.id)

    typer.echo(f"All activity plans have been deleted")

