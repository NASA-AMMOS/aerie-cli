import json
from typing import Union

import arrow
import pandas as pd
import typer
import logging
from rich.console import Console
from rich.table import Table

from aerie_cli.commands.command_context import CommandContext
from aerie_cli.schemas.client import ActivityPlanCreate
from aerie_cli.utils.prompts import select_from_list

plans_app = typer.Typer()
collaborators_app = typer.Typer()
plans_app.add_typer(collaborators_app, name="collaborators")


@plans_app.command()
def download(
    id: int = typer.Option(..., "--plan-id", "--id", "-p", help="Plan ID", prompt=True),
    full_args: str = typer.Option(
        "",
        help="true, false, or comma separated list of activity types for which to get full arguments.  Otherwise only modified arguments are returned.  Defaults to false.",
    ),
    output: str = typer.Option(..., "--output", "-o", help="The output file destination", prompt=True)
):
    """Download a plan and save it locally as a JSON file."""
    plan = CommandContext.get_client().get_activity_plan_by_id(id, full_args)
    with open(output, "w") as out_file:
        out_file.write(plan.to_json(indent=2))
    logging.info(f"Wrote activity plan to {output}")


@plans_app.command()
def download_simulation(
    sim_id: int = typer.Option(
        ..., '--sim-id', '-s',
        help="Simulation Dataset ID", prompt=True),
    output: str = typer.Option(
        ..., '--output', '-o',
        help="The output file destination", prompt=True)
):
    """
    Download simulated activity instances and save to a JSON file
    """
    client = CommandContext.get_client()
    simulated_activities = client.get_simulation_results(sim_id)
    with open(output, "w") as out_file:
        out_file.write(json.dumps(simulated_activities, indent=2))
        logging.info(f"Wrote activity plan to {output}")


@plans_app.command()
def download_resources(
    sim_id: int = typer.Option(
        ..., '--sim-id', '-s',
        help="Simulation Dataset ID", prompt='Simulation Dataset ID'),
    csv: bool = typer.Option(
        False, "--csv/--json", help="Specify file format. Defaults to JSON"
    ),
    output: str = typer.Option(
        ..., '--output', '-o',
        help="The output file destination", prompt=True),
    absolute_time: bool = typer.Option(
        False, "--absolute-time", help="Change relative timestamps to absolute"
    ),
    specific_states: str = typer.Option(
        None, help="The file with the specific states, one state per line [defaults to all]"
    )
):
    """
    Download resource timelines from a simulation and save to either JSON or CSV.

    JSON resource timelines are formatted as lists of time-value pairs. Relative timestamps are milliseconds since 
    plan start time. Absolute timestamps are of the form YYYY-DDDTh:mm:ss.sss

    CSV resource timeline relative timestamps are seconds since plan start time. Absolute timestamps are formatted the 
    same as the JSON outputs.
    """
    client = CommandContext.get_client()

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
            logging.info(f"Wrote resource timelines to {output}")

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
            logging.info(f"Wrote resource timelines to {output}")


@plans_app.command()
def upload(
    input: str = typer.Option(
        ..., "--input", "-i", help="The input file from which to create an Aerie plan", prompt=True
    ),
    model_id: int = typer.Option(
        ..., "--model-id", "-m", help="The mission model ID to associate with the plan", prompt=True
    ),
    time_tag: bool = typer.Option(False, help="Append time tag to plan name"),
):
    """Create a plan from an input JSON file."""
    client = CommandContext.get_client()

    with open(input) as in_file:
        contents = in_file.read()
    plan_to_create = ActivityPlanCreate.from_json(contents)
    if time_tag:
        plan_to_create.name += arrow.utcnow().format("YYYY-MM-DDTHH-mm-ss")
    plan_id = client.create_activity_plan(model_id, plan_to_create)
    logging.info(f"Created plan ID: {plan_id}")


@plans_app.command()
def duplicate(
    id: int = typer.Option(..., "--plan-id", "--id", "-p", help="Plan ID", prompt=True),
    duplicated_plan_name: str = typer.Option(
        ..., "--duplicate-plan-name", "-n", help="The name for the duplicated plan", prompt=True
    )
):
    """Duplicate an existing plan."""
    client = CommandContext.get_client()

    plan = client.get_activity_plan_by_id(id)
    plan_to_duplicate = ActivityPlanCreate.from_plan_read(plan)
    plan_to_duplicate.name = duplicated_plan_name
    duplicated_plan_id = client.create_activity_plan(plan.model_id, plan_to_duplicate)
    logging.info(f"Duplicate activity plan created with ID: {duplicated_plan_id}")


@plans_app.command()
def simulate(
    id: int = typer.Option(..., help="Plan ID", prompt=True),
    output: Union[str, None] = typer.Option(
        None, "--output", "-o", help="The output file destination for simulation results (if desired)"
    ),
    poll_period: int = typer.Option(
        5,
        help="The period (seconds) at which to poll for simulation completion",
    ),
):
    """Simulate a plan and optionally download the results."""
    client = CommandContext.get_client()

    start_time = arrow.utcnow()
    sim_dataset_id = client.simulate_plan(id, poll_period)
    end_time = arrow.utcnow()
    res = client.get_simulation_results(sim_dataset_id)
    total_sim_time = end_time - start_time
    logging.info(f"Simulation completed in " + str(total_sim_time))

    if output:
        with open(output, "w") as out_file:
            out_file.write(json.dumps(res, indent=2))
        logging.info(f"Wrote simulation results to {output}")


@plans_app.command()
def list():
    """List uploaded plans."""

    client = CommandContext.get_client()
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


@plans_app.command()
def create_config(
    plan_id: int = typer.Option(..., help="Plan ID", prompt=True),
    arg_file: str = typer.Option(
        ..., help="JSON file with configuration arguments", prompt=True
    ),
):
    """Clean and Create New Configuration for a Given Plan."""
    with open(arg_file) as fid:
        json_obj = json.load(fid)

    resp = CommandContext.get_client().create_config_args(plan_id=plan_id, args=json_obj)

    logging.info(f"Configuration Arguments for Plan ID: {plan_id}")
    for arg in resp:
        logging.info(f"(*) {arg}: {resp[arg]}")


@plans_app.command()
def update_config(
    plan_id: int = typer.Option(..., help="Plan ID", prompt=True),
    arg_file: str = typer.Option(
        ..., help="JSON file with configuration arguments", prompt=True
    ),
):
    """Update Configuration for a Given Plan."""

    with open(arg_file) as fid:
        json_obj = json.load(fid)

    resp = CommandContext.get_client().update_config_args(plan_id=plan_id, args=json_obj)

    logging.info(f"Configuration Arguments for Plan ID: {plan_id}")
    for arg in resp:
        logging.info(f"(*) {arg}: {resp[arg]}")


@plans_app.command()
def delete(
    plan_id: int = typer.Option(..., "--plan-id", "-p", help="Plan ID to be deleted", prompt=True),
):
    """Delete an activity plan by its id."""

    plan_name = CommandContext.get_client().delete_plan(plan_id)
    logging.info(f"Plan `{plan_name}` with ID: {plan_id} has been removed.")


@plans_app.command()
def clean():
    """Delete all activity plans."""
    client = CommandContext.get_client()

    resp = client.get_all_activity_plans()
    for activity_plan in resp:
        client.delete_plan(activity_plan.id)

    logging.info(f"All activity plans have been deleted")

@collaborators_app.command("list")
def list_collaborators(
    plan_id: int = typer.Option(
        ..., "--plan-id", "-p", help="Plan ID to list collaborators of", prompt="Plan ID"
    )
):
    client = CommandContext.get_client()

    collaborators = client.list_plan_collaborators(plan_id)
    if len(collaborators):
        logging.info("\n".join(collaborators))
    else:
        logging.info("No collaborators")


@collaborators_app.command("add")
def add_collaborator(
    plan_id: int = typer.Option(
        ..., "--plan-id", "-p", help="Plan ID to add collaborator", prompt="Plan ID"
    ),
    user: str = typer.Option(
        ..., "--user", "-u", help="Username of collaborator to add", prompt="Collaborator Username"
    ),
):
    client = CommandContext.get_client()

    client.add_plan_collaborator(plan_id, user)
    if user in client.list_plan_collaborators(plan_id):
        logging.info(f"Successfully added collaborator: {user}")
    else:
        logging.info(f"Failed to add collaborator")


@collaborators_app.command("delete")
def delete_collaborator(
    plan_id: int = typer.Option(
        ..., "--plan-id", "-p", help="Plan ID to delete collaborator from", prompt="Plan ID"
    ),
    user: str = typer.Option(
        None, "--user", "-u", help="Username of collaborator to delete"
    ),
):
    client = CommandContext.get_client()

    if user is None:
        collaborators = client.list_plan_collaborators(plan_id)
        user = select_from_list(collaborators, "Select a collaborator to remove")
    client.delete_plan_collaborator(plan_id, user)

    if user not in client.list_plan_collaborators(plan_id):
        logging.info("Successfully deleted collaborator")
    else:
        logging.info("Failed to delete collaborator")
