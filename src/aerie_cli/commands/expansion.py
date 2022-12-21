import json
import typer
from typing import List, Dict
from pathlib import Path
import fnmatch

from rich.console import Console
from rich.table import Table

from aerie_cli.utils.sessions import get_active_session_client
from aerie_cli.utils.prompts import select_from_list
from aerie_cli.schemas.client import ExpansionRun

app = typer.Typer()
sequences_app = typer.Typer()
runs_app = typer.Typer()
sets_app = typer.Typer()
app.add_typer(sequences_app, name='sequences')
app.add_typer(runs_app, name='runs')
app.add_typer(sets_app, name='sets')

# === Commands for expansion runs ===


@runs_app.command('create')
def expand_simulation(
    simulation_dataset_id: str = typer.Option(
        ..., '--sim-id', '-s', prompt='Simulation Dataset ID',
        help='Simulation Dataset ID'
    ),
    expansion_set_id: str = typer.Option(
        ..., '--expansion-set', '-e', prompt='Expansion Set ID',
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


@runs_app.command('list')
def list_expansion_runs(
    plan_id: str = typer.Option(
        None, '--plan-id', '-p',
        help='Plan ID'
    ),
    simulation_dataset_id: str = typer.Option(
        None, '--sim-id', '-s',
        help='Simulation Dataset ID'
    )
):
    """
    List expansion runs for a given plan or simulation dataset.

    Runs are listed in reverse chronological order.
    """

    if simulation_dataset_id is None and plan_id is None:
        choice = select_from_list(
            ['Plan ID', 'Simulation Dataset ID'], 'Choose one to specify')
        if choice == 'Plan ID':
            plan_id = typer.prompt('Enter Plan ID')
        elif choice == 'Simulation Dataset ID':
            simulation_dataset_id = typer.prompt('Enter Simulation Dataset ID')

    client = get_active_session_client()

    if simulation_dataset_id is None:
        simulation_datasets = client.get_simulation_dataset_ids_by_plan_id(
            plan_id)
        table_caption = f'All runs for Plan ID {plan_id}'
    else:
        simulation_datasets = [simulation_dataset_id]
        table_caption = f'All runs for Simulation Dataset ID {simulation_dataset_id}'

    runs: List[ExpansionRun] = []
    for sd in simulation_datasets:
        runs += client.list_expansion_runs(sd)

    table = Table(
        title="Expansion Runs",
        caption=table_caption
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

# === Commands for sequences ===


@sequences_app.command('list')
def list_sequences(
    plan_id: str = typer.Option(
        None, '--plan-id', '-p',
        help='Plan ID'
    ),
    simulation_dataset_id: str = typer.Option(
        None, '--sim-id', '-s',
        help='Simulation Dataset ID'
    )
):
    """
    List sequences for a given plan or simulation dataset.

    Sequences are listed in alphabetical order.
    """

    if simulation_dataset_id is None and plan_id is None:
        choice = select_from_list(
            ['Plan ID', 'Simulation Dataset ID'], 'Choose one to specify')
        if choice == 'Plan ID':
            plan_id = typer.prompt('Enter Plan ID')
        elif choice == 'Simulation Dataset ID':
            simulation_dataset_id = typer.prompt('Enter Simulation Dataset ID')

    client = get_active_session_client()

    if simulation_dataset_id is None:
        simulation_datasets = client.get_simulation_dataset_ids_by_plan_id(
            plan_id)
        table_caption = f'All sequences for Plan ID {plan_id}'
    else:
        simulation_datasets = [simulation_dataset_id]
        table_caption = f'All sequences for Simulation Dataset ID {simulation_dataset_id}'

    seq_ids_by_dataset: Dict[List[str]] = {}
    for sd in simulation_datasets:
        seq_ids_by_dataset[sd] = client.list_sequences(sd)

    table = Table(
        title="Sequences",
        caption=table_caption
    )
    table.add_column("Sequence ID", no_wrap=True)
    table.add_column("Simulation Dataset ID", no_wrap=True)
    for sim_dataset, seq_ids in seq_ids_by_dataset.items():
        for seq_id in seq_ids:
            table.add_row(
                seq_id,
                str(sim_dataset)
            )

    Console().print(table)


@sequences_app.command('create')
def create_sequence(
    simulation_dataset_id: str = typer.Option(
        ..., '--sim-id', '-s', prompt='Simulation Dataset ID',
        help='Simulation Dataset ID'
    ),
    seq_id: str = typer.Option(
        ..., '--sequence-id', '-t', prompt='Sequence ID',
        help='Sequence ID to download'
    )
):
    client = get_active_session_client()
    existing_sequences = client.list_sequences(simulation_dataset_id)
    if seq_id in existing_sequences:
        Console().print(f"Sequence already exists: {seq_id}", style='red')
        return

    client.create_sequence(seq_id, simulation_dataset_id)
    Console().print(f"Successfully created sequence: {seq_id}", style='green')

    selection_methods = [
        'Select activity types by glob string',
        'Add all activities from expansion run',
        'Blank sequence (no activities)'
    ]

    selection_method = select_from_list(
        selection_methods,
        'Choose how to add simulated activities to the sequence'
    )

    if selection_methods.index(selection_method) == 0:
        match_str = typer.prompt('Enter glob string')
        sim_results = client.get_simulation_results(simulation_dataset_id)
        ids_to_add = []
        for act in sim_results:
            if len(fnmatch.filter([act['activity_type_name']], match_str)):
                ids_to_add.append(act['id'])

    elif selection_methods.index(selection_method) == 1:
        ids_to_add = client.get_simulated_activity_ids(simulation_dataset_id)

    elif selection_methods.index(selection_method) == 2:
        ids_to_add = []

    if len(ids_to_add):
        client.link_activities_to_sequence(
            seq_id, simulation_dataset_id, ids_to_add)

        Console().print(f"Added activities to {seq_id}", style='green')
    else:
        Console().print("No activities added to sequence.", style='green')


@sequences_app.command('delete')
def delete_sequence(
    simulation_dataset_id: str = typer.Option(
        ..., '--sim-id', '-s', prompt='Simulation Dataset ID',
        help='Simulation Dataset ID'
    ),
    seq_id: str = typer.Option(
        ..., '--sequence-id', '-t', prompt='Sequence ID',
        help='Sequence ID to download'
    )
):
    get_active_session_client().delete_sequence(
        seq_id, simulation_dataset_id)

    Console().print(f"Successfully deleted sequence: {seq_id}", style='green')


@sequences_app.command('download')
def download_sequence(
    simulation_dataset_id: str = typer.Option(
        ..., '--sim-id', '-s', prompt='Simulation Dataset ID',
        help='Simulation Dataset ID'
    ),
    seq_id: str = typer.Option(
        ..., '--sequence-id', '-t', prompt='Sequence ID',
        help='Sequence ID to download'
    ),
    output_fn: str = typer.Option(
        ..., '--output', '-o', prompt='Output File',
        help='Name of output JSON file'
    )
):
    if not output_fn.endswith('.json'):
        output_fn == '.json'
    output_fn = Path(output_fn)

    client = get_active_session_client()

    seq_dict = client.get_expanded_sequence(seq_id, int(simulation_dataset_id))

    with open(output_fn, 'w') as fid:
        json.dump(seq_dict, fid)

# === Commands for expansion sets ===


@sets_app.command('list')
def list_expansion_sets():
    client = get_active_session_client()
    sets = client.list_expansion_sets()
    cmd_dicts = client.list_command_dictionaries()
    cmd_dicts = {c.id: c for c in cmd_dicts}

    table = Table(
        title="Expansion Sets"
    )
    table.add_column("Set ID", no_wrap=True)
    table.add_column("Mission", no_wrap=True)
    table.add_column("CMD Dict. Version", no_wrap=True)
    table.add_column("CMD Dict. ID", no_wrap=True)
    table.add_column("Created At", no_wrap=True)
    for e_set in sets:
        table.add_row(
            str(e_set.id),
            cmd_dicts[e_set.command_dictionary_id].mission,
            cmd_dicts[e_set.command_dictionary_id].version,
            str(e_set.command_dictionary_id),
            e_set.created_at.ctime()
        )

    Console().print(table)


@sets_app.command('get')
def get_expansion_set(
    expansion_set_id: str = typer.Option(
        ..., '--expansion-set', '-e', prompt='Expansion Set ID',
        help='Expansion Set ID'
    )
):
    client = get_active_session_client()
    sets = client.list_expansion_sets()
    try:
        set = next(filter(lambda s: s.id == int(expansion_set_id), sets))
    except StopIteration:
        Console().print(
            f"No expansion set with ID: {expansion_set_id}", style='red')
        return

    rules = client.list_expansion_rules()
    rules = list(filter(lambda r: r.id in set.expansion_rules, rules))

    table = Table(title=f"Expansion Set {expansion_set_id} Contents")
    table.add_column("Rule ID", no_wrap=True)
    table.add_column("Activity Type", no_wrap=True)
    for r in rules:
        table.add_row(
            str(r.id),
            r.activity_type
        )
    Console().print(table)


@sets_app.command('create')
def create_expansion_set(
    model_id: int = typer.Option(
        ..., '--model-id', '-m', prompt='Mission Model ID',
        help='Mission Model ID'
    ),
    command_dictionary_id: int = typer.Option(
        ..., '--command-dict-id', '-d', prompt='Command Dictionary ID',
        help='Command Dictionary ID'
    ),
    activity_types: List[str] = typer.Option(
        None, '--activity-types', '-a',
        help='Activity types to be included in the set'
    )
):
    client = get_active_session_client()
    expansion_rules = client.get_rules_by_type()

    if not activity_types:
        types_str = typer.prompt('Activity Types (separate with spaces)')
        activity_types = types_str.split(' ')

    rule_ids = []
    for at in activity_types:

        try:
            at_rules = expansion_rules[at]
            for r in at_rules:
                if not r.authoring_command_dict_id == command_dictionary_id:
                    at_rules.remove(r)
                if not r.authoring_mission_model_id == model_id:
                    at_rules.remove(r)
            rule_ids.append(max([r.id for r in at_rules]))
        except (KeyError, ValueError):
            Console().print(
                f"No expansion rules for activity type: {at}", style='red')
            return

    set_id = client.create_expansion_set(
        command_dictionary_id, model_id, rule_ids)
    Console().print(f"Created expansion set: {set_id}")
