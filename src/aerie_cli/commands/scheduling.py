import typer

from aerie_cli.commands.command_context import CommandContext

app = typer.Typer()

@app.command()
def upload(
    model_id: int = typer.Option(
        ..., help="The mission model ID to associate with the scheduling goal", prompt=True
    ),
    plan_id: int = typer.Option(
        ..., help="Plan ID", prompt=True
    ),
    schedule: str = typer.Option(
        ..., help="Text file with one path on each line to a scheduling rule file, in decreasing priority order", prompt=True
    )
): 
    """Upload scheduling goal"""
    client = CommandContext.get_client()

    upload_obj = []
    with open(schedule, "r") as infile:
        for filepath in infile.readlines():
            filepath = filepath.strip()
            filename = filepath.split("/")[-1]
            with open(filepath, "r") as f:
                # Note that as of Aerie v2.3.0, the metadata (incl. model_id and goal name) are stored in a separate table,
                # so we need to create a metadata entry along with the definition:
                goal_obj = {
                    "definition": f.read(),
                    "metadata": {
                        "data": {
                            "name": filename, 
                            "models_using": {
                                "data": {
                                    "model_id": model_id
                                }
                            }
                        }
                    }
                }
                upload_obj.append(goal_obj)
    
    resp = client.upload_scheduling_goals(upload_obj)
            
    typer.echo(f"Uploaded scheduling goals to venue.")

    uploaded_ids = [kv["goal_id"] for kv in resp]

    #priority order is order of filenames in decreasing priority order
    #will append to existing goals in specification priority order
    specification = client.get_scheduling_specification_for_plan(plan_id)

    upload_to_spec = [{"goal_id": goal_id, "specification_id": specification} for goal_id in uploaded_ids]

    client.add_goals_to_specifications(upload_to_spec)

    typer.echo(f"Assigned goals in priority order to plan ID {plan_id}.")


@app.command()
def delete(
    goal_id: int = typer.Option(
        ..., help="Goal ID of goal to be deleted", prompt=True
    )
):
    """Delete scheduling goal"""
    client = CommandContext.get_client()    

    resp = client.delete_scheduling_goal(goal_id)
    typer.echo("Successfully deleted Goal ID: " + str(resp))

@app.command()
def delete_all_goals_for_plan(
    plan_id: int = typer.Option(
        ..., help="Plan ID", prompt=True
    ),
):

    client = CommandContext.get_client()

    specification = client.get_scheduling_specification_for_plan(plan_id)
    clear_goals = client.get_scheduling_goals_by_specification(specification) #response is in asc order

    if len(clear_goals) == 0: #no goals to clear
        typer.echo("No goals to delete.")
        return
    
    typer.echo("Deleting goals for Plan ID {plan}: ".format(plan=plan_id), nl=False)
    goal_ids = []
    for goal in clear_goals:
        goal_ids.append(goal["goal_metadata"]["id"])
        typer.echo(str(goal["goal_metadata"]["id"]) + " ", nl=False)
    typer.echo()

    client.delete_scheduling_goals(goal_ids)
