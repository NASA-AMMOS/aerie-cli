import typer
from typing import List
from rich.console import Console
from rich.table import Table

from aerie_cli.utils.sessions import get_active_session_client
from aerie_cli.schemas.client import ExpansionRun

app = typer.Typer()
sequence_app = typer.Typer()
app.add_typer(sequence_app, name='sequence')


@app.command('run')
def expand_simulation(
    simulation_dataset_id: str = typer.Option(
        ..., '--sim-id', '-s', prompt=True,
        help='Simulation Dataset ID'
    ),
    expansion_set_id: str = typer.Option(
        ..., '--expansion-set', '-e', prompt=True,
        help='Expansion Set ID'
    )
):
    """
    Run command expansion on a simulation dataset
    """
    client = get_active_session_client()

    expansion_run_id = client.expand_simulation(
        int(simulation_dataset_id), int(expansion_set_id))

    print(f"Expansion Run ID: {expansion_run_id}")


@app.command('list-runs')
def list_expansion_runs(
    plan_id: str = typer.Option(
        ..., '--plan-id', '-p', prompt=True,
        help='Plan ID'
    )
):
    """
    List expansion runs for a given simulation.

    Runs are listed in reverse chronological order.
    """
    client = get_active_session_client()

    simulation_datasets = client.get_simulation_dataset_ids_by_plan_id(plan_id)

    runs: List[ExpansionRun] = []
    for sd in simulation_datasets:
        runs += client.list_expansion_runs(sd)

    table = Table(
        title="Expansion Runs"
    )
    table.add_column("Run ID", no_wrap=True)
    table.add_column("Expansion Set", no_wrap=True)
    table.add_column("Simulation Dataset ID", no_wrap=True)
    table.add_column("Creation Time", no_wrap=True)
    for run in runs:
        table.add_row(
            str(run.id),
            str(run.expansion_set_id),
            str(run.simulation_dataset_id),
            run.created_at.ctime()
        )

    Console().print(table)


@app.command()
def get_activity_interface():
    pass
