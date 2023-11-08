import json

import arrow
import logging
import typer
from rich.console import Console
from rich.table import Table

from aerie_cli.commands.command_context import CommandContext

app = typer.Typer()

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
        "model_id": model_id,
        "plan_id": plan_id, 
        "name": name,
        "description": description,
        "definition": str_contents
    }
    constraint_id = client.upload_constraint(constraint)
    logging.info(f"Created constraint: {constraint_id}")

@app.command()
def delete(
    id: int = typer.Option(..., help="The constraint id to be deleted", prompt=True)
):
    """Delete a constraint"""

    client = CommandContext.get_client()
    client.delete_constraint(id)
    logging.info(f"Successfully deleted constraint {id}")

@app.command()
def update(
    id: int = typer.Option(..., help="The constraint id to be modifyed", prompt=True),
    constraint_file: str = typer.Option(..., help="The new constraint for the id", prompt=True)
):
    """Update a constraint"""
    
    client = CommandContext.get_client()
    constraint = client.get_constraint_by_id(id)
    with open(constraint_file) as in_file:
        contents = in_file.readlines()
        str_contents = " ".join(contents)
    constraint = {
        "model_id": constraint["model_id"],
        "plan_id": constraint["plan_id"], 
        "name": constraint["name"],
        "description": constraint["description"],
        "definition": str_contents
    }
    constraint_id = client.update_constraint(id, constraint)
    logging.info(f"Updated constraint: {constraint_id}")
    
@app.command()
def violations(
    plan_id: int = typer.Option(..., help="The plan id for the violation", prompt=True)
):

    client = CommandContext.get_client()
    constraint_violations = client.get_constraint_violations(plan_id)
    logging.info(f"Constraint violations: {constraint_violations}")
    


