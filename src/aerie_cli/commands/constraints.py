import json

import arrow
import typer
from rich.console import Console
from rich.table import Table

from aerie_cli.commands.command_context import CommandContext

app = typer.Typer()

def construct_constraint_metadata(name, description, model_id, plan_id):
    """
    Utility function to create metadata for a given constraint.
    @param name The constraint name
    @param description The constraint description
    @param model_id The model ID that will be using this constraint
    @param plan_id The plan ID that will be using this constraint
    """
    metadata = {
        "data": {
            "name": name, 
            "description": description
        }
    }
    if model_id != None:
        if model_id is int:
            metadata["data"]["models_using"] = {
                "data": {
                    "model_id": model_id
                }
            }
        elif model_id is list:
            metadata["data"]["models_using"] = model_id
    if plan_id != None:
        if plan_id is int:
            metadata["data"]["plans_using"] = {
                "data": {
                    "plan_id": plan_id
                }
            }
        elif plan_id is list:
            metadata["data"]["plans_using"] = plan_id
    return metadata

@app.command()
def upload(
    model_id: int = typer.Option(None, help="The model id associated with the constraint (do not input plan id)"),
    plan_id: int = typer.Option(None, help="The plan id associated with the constraint (do not input model id)"),
    name: str = typer.Option(..., help="The name of the constraint", prompt=True),
    description: str = typer.Option("", help="The description of the constraint"), # optional
    constraint_file: str = typer.Option(..., help="The file that holds the constraint", prompt=True)
):
    """Upload a constraint"""

    if model_id is None and plan_id is None:
        model_id = typer.prompt("Model id")

    client = CommandContext.get_client()
    with open(constraint_file) as in_file:
        contents = in_file.readlines()
        str_contents = " ".join(contents) 
    constraint = {
        "definition": str_contents,
        "metadata": construct_constraint_metadata(name, description, model_id, plan_id)
    }
    constraint_id = client.upload_constraint(constraint)
    typer.echo(f"Created constraint: {constraint_id}")


@app.command()
def add_to_plan(
    plan_id: int = typer.Option(None, help="The plan id associated with the constraint (do not input model id)", prompt=True),
    constraint_id: int = typer.Option(..., help="The id of the constraint", prompt=True)
):
    """Associate a constraint with a plan's constraint specification."""

    client = CommandContext.get_client()
    client.add_constraint_to_plan(constraint_id=constraint_id, plan_id=plan_id)
    typer.echo(f"Added constraint: {constraint_id} to plan: {plan_id} constraint specification")


@app.command()
def delete(
    id: int = typer.Option(..., help="The constraint id to be deleted", prompt=True)
):
    """Delete a constraint"""

    client = CommandContext.get_client()
    client.delete_constraint(id)
    typer.echo(f"Successfully deleted constraint {id}")

@app.command()
def update(
    id: int = typer.Option(..., help="The constraint id to be modified", prompt=True),
    constraint_file: str = typer.Option(..., help="The new constraint for the id", prompt=True)
):
    """Update a constraint"""
    
    client = CommandContext.get_client()
    constraint = client.get_constraint_by_id(id)
    with open(constraint_file) as in_file:
        contents = in_file.readlines()
        str_contents = " ".join(contents)
    response = client.update_constraint(id, str_contents)
    for r in response:
        typer.echo(f"Updated constraint: {r['returning']}")
    
@app.command()
def violations(
    plan_id: int = typer.Option(..., help="The plan id for the violation", prompt=True)
):

    client = CommandContext.get_client()
    constraint_violations = client.get_constraint_violations(plan_id)
    typer.echo(f"Constraint violations: {constraint_violations}")
    


