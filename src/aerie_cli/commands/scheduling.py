import typer
import logging

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
    keys = ["name", "model_id", "definition"]
    with open(schedule, "r") as infile:
        for filepath in infile.readlines():
            filepath = filepath.strip()
            filename = filepath.split("/")[-1]
            with open(filepath, "r") as f:
                d = dict(zip(keys, [filename, model_id, f.read()]))
                upload_obj.append(d)
    
    resp = client.upload_scheduling_goals(upload_obj)
            
    logging.info(f"Uploaded scheduling goals to venue.")

    uploaded_ids = [kv["id"] for kv in resp]

    #priority order is order of filenames in decreasing priority order
    #will append to existing goals in specification priority order
    specification = client.get_specification_for_plan(plan_id)

    upload_to_spec = [{"goal_id": goal_id, "specification_id": specification} for goal_id in uploaded_ids]

    client.add_goals_to_specifications(upload_to_spec)

    logging.info(f"Assigned goals in priority order to plan ID {plan_id}.")


@app.command()
def delete(
    goal_id: int = typer.Option(
        ..., help="Goal ID of goal to be deleted", prompt=True
    )
):
    """Delete scheduling goal"""
    client = CommandContext.get_client()

    resp = client.delete_scheduling_goal(goal_id)
    logging.info("Successfully deleted Goal ID: " + str(resp))

@app.command()
def delete_all_goals_for_plan(
    plan_id: int = typer.Option(
        ..., help="Plan ID", prompt=True
    ),
):

    client = CommandContext.get_client()

    specification = client.get_specification_for_plan(plan_id)
    clear_goals = client.get_scheduling_goals_by_specification(specification) #response is in asc order

    if len(clear_goals) == 0: #no goals to clear
        logging.info("No goals to delete.")
        return
    
    logging.info("Deleting goals for Plan ID {plan}: ".format(plan=plan_id), nl=False)
    goal_ids = []
    for goal in clear_goals:
        goal_ids.append(goal["goal"]["id"])
        logging.info(str(goal["goal"]["id"]) + " ", nl=False)
        
    client.delete_scheduling_goals(goal_ids)
