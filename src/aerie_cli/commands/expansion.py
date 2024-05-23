import json
import typer
from typing import List, Dict
from pathlib import Path
import fnmatch

import arrow

from rich.console import Console
from rich.table import Table

from aerie_cli.commands.command_context import CommandContext
from aerie_cli.utils.prompts import select_from_list
from aerie_cli.schemas.client import ExpansionRun, ExpansionDeployConfiguration

app = typer.Typer()
sequences_app = typer.Typer()
runs_app = typer.Typer()
sets_app = typer.Typer()
app.add_typer(sequences_app, name='sequences', help='Commands for sequences')
app.add_typer(runs_app, name='runs', help='Commands for expansion runs')
app.add_typer(sets_app, name='sets', help='Commands for expansion sets')

# === Bulk Deploy Command ===

@app.command('deploy')
def bulk_deploy(
    model_id: int = typer.Option(
        ..., '--model-id', '-m', prompt='Mission Model ID',
        help='Mission Model ID'
    ),
    parcel_id: int = typer.Option(
        ..., '--parcel-id', '-p', prompt='Parcel ID',
        help='Parcel ID'
    ),
    config_file: str = typer.Option(
        ..., "--config-file", "-c", prompt="Configuration file",
        help="Deploy configuration JSON file"
    ),
    rules_path: Path = typer.Option(
        Path.cwd(), help="Path to folder containing expansion rule files"
    ),
    time_tag: bool = typer.Option(False, help="Append time tags to create unique expansion rule/set names")
):
    """
    Bulk deploy command expansion rules and sets to an Aerie instance according to a JSON configuration file.

    The configuration file contains a list of rules and a list of sets:

    ```
    {
        "rules": [...],
        "sets": [...]
    }
    ```

    Each rule must provide a unique rule name, the activity type name, and the name of the file with expansion logic:

    ```
    {
        "name": "Expansion Rule Name",
        "activity_type": "Activity Type Name",
        "file_name": "my_file.ts"
    }
    ```

    Each set must provide a unique set name and a list of rule names to add:

    ```
    {
        "name": "Expansion Set Name",
        "rules": ["Expansion Rule Name", ...]
    }
    ```
    """

    client = CommandContext.get_client()

    with open(Path(config_file), "r") as fid:
        configuration: ExpansionDeployConfiguration = ExpansionDeployConfiguration.from_dict(json.load(fid))

    name_suffix = arrow.utcnow().format("_YYYY-MM-DDTHH-mm-ss") if time_tag else ""

    # Loop and upload all expansion rules
    uploaded_rules = {}
    for rule in configuration.rules:
        try:
            with open(rules_path.joinpath(rule.file_name), "r") as fid:
                expansion_logic = fid.read()

            rule_id = client.create_expansion_rule(
                expansion_logic=expansion_logic,
                activity_name=rule.activity_type,
                model_id=model_id,
                parcel_id=parcel_id,
                name=rule.name + name_suffix
            )
            typer.echo(f"Created expansion rule {rule.name + name_suffix}: {rule_id}")
            uploaded_rules[rule.name] = rule_id
        except:
            typer.echo(f"Failed to create expansion rule {rule.name}")

    for set in configuration.sets:
        try:
            rule_ids = []
            for rule_name in set.rules:
                if rule_name in uploaded_rules.keys():
                    rule_ids.append(uploaded_rules[rule_name])
                else:
                    typer.echo(f"No uploaded rule {rule_name} for set {set.name}")
            
            assert len(rule_ids)

            set_id = client.create_expansion_set(
                parcel_id=parcel_id,
                model_id=model_id,
                expansion_ids=rule_ids,
                name=set.name + name_suffix
            )

            typer.echo(f"Created expansion set {set.name + name_suffix}: {set_id}")
        except:
            typer.echo(f"Failed to create expansion set {set.name}")


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
    client = CommandContext.get_client()

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
    List expansion runs for a given plan or simulation dataset

    Runs are listed in reverse chronological order.
    """

    if simulation_dataset_id is None and plan_id is None:
        choice = select_from_list(
            ['Plan ID', 'Simulation Dataset ID'], 'Choose one to specify')
        if choice == 'Plan ID':
            plan_id = typer.prompt('Enter Plan ID')
        elif choice == 'Simulation Dataset ID':
            simulation_dataset_id = typer.prompt('Enter Simulation Dataset ID')

    client = CommandContext.get_client()

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
    List sequences for a given plan or simulation dataset

    Sequences are listed in alphabetical order.
    """

    if simulation_dataset_id is None and plan_id is None:
        choice = select_from_list(
            ['Plan ID', 'Simulation Dataset ID'], 'Choose one to specify')
        if choice == 'Plan ID':
            plan_id = typer.prompt('Enter Plan ID')
        elif choice == 'Simulation Dataset ID':
            simulation_dataset_id = typer.prompt('Enter Simulation Dataset ID')

    client = CommandContext.get_client()

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
    """
    Create a sequence on a simulation dataset
    """
    client = CommandContext.get_client()
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
    """
    Delete sequence on a simulation dataset
    """
    CommandContext.get_client().delete_sequence(
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
    """
    Download a SeqJson file from an Aerie sequence
    """
    if not output_fn.endswith('.json'):
        output_fn == '.json'
    output_fn = Path(output_fn)

    client = CommandContext.get_client()

    seq_dict = client.get_expanded_sequence(seq_id, int(simulation_dataset_id))

    with open(output_fn, 'w') as fid:
        json.dump(seq_dict, fid, indent=2)

# === Commands for expansion sets ===


@sets_app.command('list')
def list_expansion_sets():
    """
    List all expansion sets
    """
    client = CommandContext.get_client()
    sets = client.list_expansion_sets()
    parcels = client.list_parcels()
    parcels_by_id = {p.id: p for p in parcels}

    table = Table(
        title="Expansion Sets"
    )
    table.add_column("ID", no_wrap=True)
    table.add_column("Name", no_wrap=True)
    table.add_column("Model ID", no_wrap=True)
    table.add_column("Parcel", no_wrap=True)
    table.add_column("Owner", no_wrap=True)
    for e_set in sets:
        table.add_row(
            str(e_set.id),
            str(e_set.name),
            str(e_set.mission_model_id),
            parcels_by_id[e_set.parcel_id].name,
            e_set.owner
        )

    Console().print(table)


@sets_app.command('get')
def get_expansion_set(
    expansion_set_id: str = typer.Option(
        ..., '--expansion-set', '-e', prompt='Expansion Set ID',
        help='Expansion Set ID'
    )
):
    """
    View all rules in an expansion set
    """
    client = CommandContext.get_client()
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
    parcel_id: int = typer.Option(
        ..., '--parcel-id', '-p', prompt='Parcel ID',
        help='Parcel ID'
    ),
    name: str = typer.Option(
        ..., "--name", "-n", prompt="Expansion set name",
        help="Expansion set name"
    ),
    activity_types: List[str] = typer.Option(
        None, '--activity-types', '-a',
        help='Activity types to be included in the set'
    ),
    rule_ids: List[int] = typer.Option(
        None, '--rule-ids', '-r',
        help='Expansion rules to be included in the set'
    )
):
    """
    Create an expansion set

    Uses the newest expansion rules for each given activity type.
    Specify either a list of activity type names or rule IDs. If activity type 
    names are given, rules are filtered to only those designated for the given 
    mission model and sequencing parcel, then the highest rule ID is used for 
    each activity type named.
    """
    client = CommandContext.get_client()
    expansion_rules = client.get_rules_by_type()

    if activity_types and rule_ids:
        Console().print(
            "Only specify either activity type name(s) or rule ID(s).", style='red')
        return

    if not activity_types and not rule_ids:
        choice = select_from_list(
            ["By name", "By expansion rule ID"], "Choose how to specify rules")
        if choice == "By name":
            types_str = typer.prompt('Activity Types (separate with spaces)')
            activity_types = types_str.split(' ')
        else:
            rule_ids_str = typer.prompt(
                'Expansion rule IDs (separate with spaces)')
            rule_ids = [int(r) for r in rule_ids_str.split(' ')]

    if activity_types:

        rule_ids = []
        for at in activity_types:

            try:
                at_rules = expansion_rules[at]
                for r in at_rules:
                    if not r.parcel_id == parcel_id:
                        at_rules.remove(r)
                        continue
                    if not r.authoring_mission_model_id == model_id:
                        at_rules.remove(r)
                        continue
                rule_ids.append(max([r.id for r in at_rules]))
            except (KeyError, ValueError) as e:
                print(e)
                Console().print(
                    f"No expansion rules for activity type: {at}", style='red')
                return

    set_id = client.create_expansion_set(
        parcel_id, model_id, rule_ids, name)
    Console().print(f"Created expansion set: {set_id}")
