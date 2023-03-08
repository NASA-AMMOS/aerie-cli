import typer

from aerie_cli.utils.sessions import get_active_session_client

app = typer.Typer()

@app.command()
def upload(
    model_id: int = typer.Option(
        ..., help="The mission model ID to associate with the scheduling goal", prompt=True
    ),
    plan_id: int = typer.Option(
        ..., help="Plan ID", prompt=True
    ),
    scheduling_name: str = typer.Option(..., help="Name of scheduling goal", prompt=True
    ),
    schedule: str = typer.Option(
        ..., help="Text file with one path on each line to a scheduling rule file, in decreasing priority order", prompt=True
    )
): 
    """Upload scheduling goal"""
    client = get_active_session_client()

    with open(schedule) as in_file:
        i = 0
        for line in in_file:
            line = line.strip("\n")
            with open(line) as sch:
                contents = sch.readlines()
                str_contents = " ".join(contents)
                goal_id = client.upload_scheduling_goal(model_id, scheduling_name, str_contents)
                typer.echo("GOAL " + str(goal_id))
                specification_id = client.get_specification_for_plan(plan_id)
                typer.echo("SPEC " + str(specification_id))
                priority = client.add_goal_to_specification(specification_id, goal_id, i)
                i+=1
                typer.echo("Uploaded " + line + " as priority " + str(priority))

@app.command()
def delete(
    goal_id: int = typer.Option(
        ..., help="Goal ID of goal to be deleted", prompt=True
    )
):
    """Delete scheduling goal"""
    client = get_active_session_client()

    resp = client.delete_scheduling_goal(goal_id)
    typer.echo("Successfully deleted Goal ID: " + str(resp))
