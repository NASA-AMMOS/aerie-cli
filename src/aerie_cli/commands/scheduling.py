import typer
from pathlib import Path
from typing import Optional

from aerie_cli.commands.command_context import CommandContext

app = typer.Typer()

@app.command()
def new(
        path: Path = typer.Argument(default=...),
        description: Optional[str] = typer.Option(
            None, '--description', '-d', help="Description metadata"
        ),
        public: bool = typer.Option(False, '--public', '-pub', help="Indicates a public goal visible to all users (default false)"),
        name: Optional[str] = typer.Option(
            None, '--name', '-n', help="Name of the new goal (default is the file name without extension)"
        ),
        model_id: Optional[int] = typer.Option(
            None, '--model', '-m', help="Mission model ID to associate with the scheduling goal"
        ),
        plan_id: Optional[int] = typer.Option(
            None, '--plan', '-p', help="Plan ID of the specification to add this to"
        )
):
    """Upload new scheduling goal"""

    client = CommandContext.get_client()
    filename = path.stem
    extension = path.suffix
    if name is None:
        name = filename
    upload_obj = {}
    if extension == '.ts':
        with open(path, "r") as f:
            upload_obj["definition"] = f.read()
        upload_obj["type"] = "EDSL"
    elif extension == '.jar':
        jar_id = client.upload_file(path)
        upload_obj["uploaded_jar_id"] = jar_id
        upload_obj["parameter_schema"] = {}
        upload_obj["type"] = "JAR"
    else:
        raise RuntimeError(f"Unsupported goal file extension: {extension}")
    metadata = {"name": name}
    if description is not None:
        metadata["description"] = description
    metadata["public"] = public
    if model_id is not None:
        metadata["models_using"] = {"data": {"model_id": model_id}}
    if plan_id is not None:
        spec_id = client.get_scheduling_specification_for_plan(plan_id)
        metadata["plans_using"] = {"data": {"specification_id": spec_id}}
    upload_obj["metadata"] = {"data": metadata}
    resp = client.upload_scheduling_goals([upload_obj])
    id = resp[0]["goal_id"]
    typer.echo(f"Uploaded scheduling goal to venue. ID: {id}")


@app.command()
def update(
        path: Path = typer.Argument(default=...),
        goal_id: Optional[int] = typer.Option(None, '--goal', '-g', help="Goal ID of goal to be updated (will search by name if omitted)"),
        name: Optional[str] = typer.Option(None, '--name', '-n', help="Name of the goal to be updated (ignored if goal is provided, default is the file name without extension)"),
):
    """Upload an update to a scheduling goal"""
    client = CommandContext.get_client()
    filename = path.stem
    extension = path.suffix
    if goal_id is None:
        if name is None:
            name = filename
        goal_id = client.get_goal_id_for_name(name)
    upload_obj = {"goal_id": goal_id}
    if extension == '.ts':
        with open(path, "r") as f:
            upload_obj["definition"] = f.read()
        upload_obj["type"] = "EDSL"
    elif extension == '.jar':
        jar_id = client.upload_file(path)
        upload_obj["uploaded_jar_id"] = jar_id
        upload_obj["parameter_schema"] = {}
        upload_obj["type"] = "JAR"
    else:
        raise RuntimeError(f"Unsupported goal file extension: {extension}")

    resp = client.upload_scheduling_goals([upload_obj])
    id = resp[0]["goal_id"]
    typer.echo(f"Uploaded new version of scheduling goal to venue. ID: {id}")


@app.command()
def delete(
    goal_id: int = typer.Option(
        ..., '--goal', '-g', help="Goal ID of goal to be deleted", prompt=True
    )
):
    """Delete scheduling goal"""
    client = CommandContext.get_client()    

    resp = client.delete_scheduling_goal(goal_id)
    typer.echo("Successfully deleted Goal ID: " + str(resp))

@app.command()
def delete_all_goals_for_plan(
    plan_id: int = typer.Option(
        ..., help="Plan ID", prompt=True
    ),
):
    client = CommandContext.get_client()

    specification = client.get_scheduling_specification_for_plan(plan_id)
    clear_goals = client.get_scheduling_goals_by_specification(specification)  # response is in asc order

    if len(clear_goals) == 0:  # no goals to clear
        typer.echo("No goals to delete.")
        return
    
    typer.echo("Deleting goals for Plan ID {plan}: ".format(plan=plan_id), nl=False)
    goal_ids = []
    for goal in clear_goals:
        goal_ids.append(goal["goal_metadata"]["id"])
        typer.echo(str(goal["goal_metadata"]["id"]) + " ", nl=False)
    typer.echo()

    client.delete_scheduling_goals(goal_ids)
