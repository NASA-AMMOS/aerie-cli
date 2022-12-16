import typer
from rich.console import Console
from rich.table import Table

from aerie_cli.utils.sessions import get_active_session_client

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

    client.expand_simulation(
        simulation_dataset_id, expansion_set_id)

    # TODO print expansion run ID


@app.command()
def get_activity_interface():
    pass
