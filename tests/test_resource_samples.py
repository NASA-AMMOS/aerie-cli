from src.aerie_cli.client import AerieClient
from src.aerie_cli.plans import download_simulation


def test_resource_samples():
    client = AerieClient("http://localhost")
    print(client.get_resource_timelines(1))


def test_resource_samples_old():
    client = AerieClient("http://localhost")
    print(client.get_resource_samples(1))

def test_download_simulation():
    csv = True
    plan_id = 1

    client = AerieClient("http://localhost")
    # get resource timelines and sim results from GraphQL
    resources = client.get_resource_samples(plan_id)
    sim = client.get_simulation_results(sim_id)
    # add sim results and resources to the same dictionary
    resources["simulationResults"] = sim

    if csv:
        # the key is the time and the value is a list of tuples: (activity, state)
        time_dictionary = {}

        # this stores the header names for the CSV
        field_name = ["Time (s)"]

        for activity in resources.get("resourceSamples"):
            list = resources.get("resourceSamples").get(activity)
            field_name.append(activity)
            for i in list:
                time_dictionary.setdefault(i.get("x"), []).append(
                    (activity, i.get("y"))
                )

        # a list of dictionaries that will be fed into the DictWriter method
        csv_dictionary = []

        for time in time_dictionary:
            seconds = 0
            if time != 0:
                seconds = time / 1000000
            tempDict = {"Time (s)": seconds}
            for activity in time_dictionary.get(time):
                tempDict[activity[0]] = activity[1]
            csv_dictionary.append(tempDict)

        # Sort the dictionary by time
        sorted_by_time = sorted(csv_dictionary, key=lambda d: d["Time (s)"])

        # use panda to fill in missing data
        df = pd.DataFrame(sorted_by_time)
        # 'ffill' will fill each missing row with the value of the nearest one above it.
        df.fillna(method="ffill", inplace=True)

        # write to file
        with open(output, "w") as out_file:
            df.to_csv(out_file, index=False, header=field_name)
            typer.echo(f"Wrote activity plan to {output}")

    else:
        # write to file
        with open(output, "w") as out_file:
            out_file.write(json.dumps(resources, indent=2))
            typer.echo(f"Wrote activity plan to {output}")


if __name__ == "__main__":
    test_resource_samples()

# {'resourceSamples': {'/data/line_count': [{'x': 0, 'y': 12}, {'x': 1209600000000, 'y': 12}], '/flag': [{'x': 0, 'y': 'A'}, {'x': 401126992000, 'y': 'A'}, {'x': 401126992000, 'y': 'B'}, {'x': 848896658000, 'y': 'B'}, {'x': 848896658000, 'y': 'A'}, {'x': 960839074000, 'y': 'A'}, {'x': 960839074000, 'y': 'A'}, {'x': 1209600000000, 'y': 'A'}], '/flag/conflicted': [{'x': 0, 'y': False}, {'x': 401126992000, 'y': False}, {'x': 401126992000, 'y': False}, {'x': 848896658000, 'y': False}, {'x': 848896658000, 'y': False}, {'x': 960839074000, 'y': False}, {'x': 960839074000, 'y': False}, {'x': 1209600000000, 'y': False}], '/fruit': [{'x': 0, 'y': 4.0}, {'x': 401126992000, 'y': 4.0}, {'x': 401126992000, 'y': 1.0}, {'x': 848896658000, 'y': 1.0}, {'x': 848896658000, 'y': 0.0}, {'x': 960839074000, 'y': 0.0}, {'x': 960839074000, 'y': -1.0}, {'x': 1209600000000, 'y': -1.0}], '/peel': [{'x': 0, 'y': 4.0}, {'x': 1209600000000, 'y': 4.0}], '/plant': [{'x': 0, 'y': 200}, {'x': 185015937000, 'y': 200}, {'x': 185015937000, 'y': 185}, {'x': 1209600000000, 'y': 185}], '/producer': [{'x': 0, 'y': 'Chiquita'}, {'x': 1209600000000, 'y': 'Chiquita'}]}}