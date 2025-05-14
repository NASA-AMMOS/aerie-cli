from builtins import list as list_builtin
from genericpath import isdir, isfile
from os import walk
from posixpath import commonpath, join, normpath, relpath
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from aerie_cli.commands.command_context import CommandContext

app = typer.Typer()

app.command()


@app.command()
def create(
    name: str = typer.Option(
        ...,
        "--name",
        "-n",
        help="The name of the workspace",
    ),
    parcel: int = typer.Option(
        ...,
        "--parcel_id",
        "-p",
        help="The parcel id",
    ),
):
    """Create workspace and provide parcel foreign key"""
    client = CommandContext.get_client()
    resp = client.create_workspace(name=name, parcel_id=parcel)
    typer.echo(f"Created new workspaces with id: {resp}")


@app.command()
def list(
    workspace_id: Optional[int] = typer.Option(
        None, "--workspace_id", "-w", help="The workspace id"
    ),
    base_directory: Optional[str] = typer.Option(
        None, "--base_directory", "-b", help="Path of directory within workspace"
    ),
    depth: Optional[int] = typer.Option(
        None, "--depth", "-d", help="Path of directory within workspace"
    ),
):
    """List workspaces or their contents if a workspace_id is provided.

    Depth is counted as number of levels below,
    0 indicates only the current level,
    1 includes next level of children"""

    if workspace_id is None:
        list_workspaces()
    else:
        list_workspace_contents(workspace_id, base_directory, depth)


def list_workspaces():
    client = CommandContext.get_client()
    resp = client.list_workspaces()

    # Create output table
    table = Table(title="Current Workspaces")
    table.add_column("Workspace ID", style="magenta")
    table.add_column("Workspace Name", no_wrap=True)
    table.add_column("Workspace Disk Location", no_wrap=True)
    for workspace in resp:
        table.add_row(
            str(workspace["id"]),
            workspace["name"],
            workspace["disk_location"],
        )

    console = Console()
    console.print(table)


def list_workspace_contents(
    workspace_id: int,
    prefix: Optional[str] = None,
    depth: Optional[int] = -1,
):
    client = CommandContext.get_client()
    resp = client.list_files(workspace_id, prefix, depth)
    console = Console()
    console.print(resp.text)


@app.command()
def save(
    workspace_id: int = typer.Option(
        ..., "--workspace_id", "-w", help="The workspace id"
    ),
    workspace_path: str = typer.Option(
        ..., "--path", "-p", help="The relative path within the workspace"
    ),
    local_path: str = typer.Option(..., "--file", "-f", help="The local path"),
):
    """Save file passed in via local_path to workspace_path within workspace_id"""
    client = CommandContext.get_client()

    for filepath in contained_files(local_path):
        if isdir(filepath):
            client.put_workspace_directory(workspace_id, filepath)
        else:
            ws_path = normpath(join(workspace_path, relpath(filepath, local_path)))
            with open(filepath, "rb") as f:
                resp = client.put_workspace_file(
                    workspace_id=workspace_id,
                    filepath=ws_path,
                    contents=f.read(),
                )
                typer.echo(f'File saved to "{resp}"')


def contained_files(path: str):
    """Returns directory paths first to not rely on file store creating them automatically"""
    yield path
    if isdir(path):
        for dirpath, dirs, files in walk(path):
            for d in dirs:
                yield join(dirpath, d)
            for f in files:
                yield join(dirpath, f)


@app.command()
def get(
    workspace_id: int = typer.Option(
        ..., "--workspace_id", "-w", help="The workspace id"
    ),
    workspace_path: str = typer.Option(
        ..., "--path", "-p", help="The relative path within the workspace"
    ),
    local_path: Optional[str] = typer.Option(
        None, "--file", "-f", help="The local path to write file to"
    ),
):
    client = CommandContext.get_client()
    resp = client.get_workspace_file(workspace_id, workspace_path)
    if local_path is not None:
        with open(local_path, "wb") as f:
            f.write(resp)
    else:
        typer.echo(resp)
