import typer

from .client import auth_helper

app = typer.Typer()

@app.command()
def upload(
    sso: str = typer.Option("", help="SSO Token"),
    username: str = typer.Option("", help="JPL username"),
    password: str = typer.Option(
        "",
        help="JPL password",
        hide_input=True,
    ),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
    model_id: int = typer.Option(
        ..., help="The mission model ID to associate with the scheduling goal", prompt=True
    ),
    plan_id: int = typer.Option(
        ..., help="Plan ID", prompt=True
    ),
    scheduling_name: str = typer.Option(..., help="Name of scheduling goal", prompt=True
    ),
    schedule: str = typer.Option(
        ..., help="The input file from which to create an Aerie plan", prompt=True
    )
): 
    """Upload scheduling goal"""
    client = auth_helper(
        sso=sso, username=username, password=password, server_url=server_url
    )

    with open(schedule) as in_file:
        i = 0
        for line in in_file:
            with open(line) as sch:
                contents = sch.readlines()
                str_contents = " ".join(contents)
                goal_id = client.upload_scheduling_goal(model_id, scheduling_name, str_contents)
                typer.echo("GOAL " + str(goal_id))
                specification_id = client.get_specification_for_plan(plan_id)
                typer.echo(specification_id)
                priority = client.add_goal_to_specification(specification_id, goal_id, i)
                i+=1
                typer.echo("Uploaded " + sch + " as priority " + priority)

@app.command()
def delete(
    sso: str = typer.Option("", help="SSO Token"),
    username: str = typer.Option("", help="JPL username"),
    password: str = typer.Option(
        "",
        help="JPL password",
        hide_input=True,
    ),
    server_url: str = typer.Option(
        "http://localhost", help="The URL of the Aerie deployment"
    ),
    goal_id: int = typer.Option(
        ..., help="Goal ID of goal to be deleted", prompt=True
    )
):
    client = auth_helper(
        sso=sso, username=username, password=password, server_url=server_url
    )

    resp = client.delete_scheduling_goal(goal_id)
    typer.echo("Successfully deleted Goal ID: " + str(resp))

    
       