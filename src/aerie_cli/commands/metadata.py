import json

import arrow
import typer
import logging
from rich.console import Console
from rich.table import Table

from aerie_cli.commands.command_context import CommandContext

app = typer.Typer()


@app.command()
def upload(
    schema_path: str = typer.Option(
        ...,
        "--schema-path",
        "-i",
        help="path to JSON file defining the schema to be created",
        prompt=True,
    ),
):
    """Add to the metadata schema from a .json file.

    JSON file contents should include a list schemas, each containing a key for its name and value for its type.
    """
    client = CommandContext.get_client()

    with open(schema_path) as in_file:
        contents = in_file.read()
    schema_data = json.loads(contents)
    result = client.add_directive_metadata_schemas(schema_data["schemas"])
    logging.info(f"{len(schema_data['schemas'])} new schema have been added.")


@app.command()
def delete(
    schema_name: str = typer.Option(
        ..., "--schema-name", "-n", help="Name of schema to be deleted", prompt=True
    ),
):
    """Delete a metadata schema by its name."""
    resp = CommandContext.get_client().delete_directive_metadata_schema(schema_name)
    logging.info(f"Schema `{resp}` has been removed.")


@app.command()
def list():
    """List uploaded metadata schemas."""

    resp = CommandContext.get_client().get_directive_metadata()

    table = Table(title="Metadata Schemas")
    table.add_column("Key", style="magenta")
    table.add_column("Schema", no_wrap=True)
    for schema in resp:
        table.add_row(
            str(schema["key"]),
            str(schema["schema"]["type"]),
        )

    console = Console()
    console.print(table)


@app.command()
def clean():
    """Delete all metadata schemas."""
    client = CommandContext.get_client()

    resp = client.get_directive_metadata()
    for schema in resp:
        client.delete_directive_metadata_schema(schema["key"])

    logging.info(f"All metadata schemas have been deleted")
