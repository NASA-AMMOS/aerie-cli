import sys
import time
from pathlib import Path
from typing import Dict
from typing import List

import arrow

from .schemas.api import ApiActivityPlanRead
from .schemas.api import ApiEffectiveActivityArguments
from .schemas.api import ApiMissionModelCreate
from .schemas.api import ApiMissionModelRead
from .schemas.api import ApiResourceSampleResults
from .schemas.client import ActivityCreate
from .schemas.client import ActivityPlanCreate
from .schemas.client import ActivityPlanRead
from .schemas.client import CommandDictionaryInfo
from .schemas.client import ExpansionRun
from .schemas.client import ExpansionRule
from .schemas.client import ExpansionSet
from .utils.serialization import postgres_duration_to_microseconds
from .aerie_host import AerieHostSession


class AerieClient:
    """Client-side behavior for aerie-cli

    Class encapsulates logic to query and send files to a given Aerie host.
    """

    def __init__(self, host_session: AerieHostSession):
        """Instantiate a client with an authenticated host session

        Args:
            host_session (AerieHostSession): Aerie host information, including authentication if necessary
        """
        self.host_session = host_session

    def get_activity_plan_by_id(self, plan_id: int, full_args: str = None) -> ActivityPlanRead:
        """Download activity plan from Aerie

        Args:
            plan_id (int): ID of the plan in Aerie
            full_args (str): comma separated list of activity types for which to
            get full arguments, otherwise only modified arguments are returned.
            Set to "true" to get full arguments for all activity types.
            Disabled if missing, None, "false", or "".

        Returns:
            ActivityPlanRead: the activity plan
        """
        query = """
        query get_plans ($plan_id: Int!) {
            plan_by_pk(id: $plan_id) {
                id
                model_id
                name
                start_time
                duration
                simulations{
                    id
                }
                activity_directives {
                    id
                    name
                    type
                    start_offset
                    arguments
                    metadata
                    tags
                }
            }
        }
        """
        resp = self.host_session.post_to_graphql(query, plan_id=plan_id)
        api_plan = ApiActivityPlanRead.from_dict(resp)
        plan = ActivityPlanRead.from_api_read(api_plan)
        return self.__expand_activity_arguments(plan, full_args)

    def list_all_activity_plans(self) -> List[Dict]:
        list_all_plans_query = """
        query list_all_plans {
            plan(order_by: { id: asc }) {
                id
                name
                model_id
                start_time
                duration
                simulations(limit: 1, order_by: { id: desc }) {
                    id
                }
            }
        }
        """
        resp = self.host_session.post_to_graphql(list_all_plans_query)
        return resp

    def get_all_activity_plans(self, full_args: str = None) -> list[ActivityPlanRead]:
        get_all_plans_query = """
        query get__all_plans {
            plan{
                id
                model_id
                name
                start_time
                duration
                simulations{
                    id
                }
                activity_directives {
                    id
                    name
                    type
                    start_offset
                    arguments
                    metadata
                    tags
                }
            }
        }
        """
        resp = self.host_session.post_to_graphql(get_all_plans_query)
        activity_plans = []
        for plan in resp:
            plan = ApiActivityPlanRead.from_dict(plan)
            plan = ActivityPlanRead.from_api_read(plan)
            plan = self.__expand_activity_arguments(plan, full_args)
            activity_plans.append(plan)

        return activity_plans

    def create_activity_plan(
        self, model_id: int, plan_to_create: ActivityPlanCreate
    ) -> int:

        api_plan_create = plan_to_create.to_api_create(model_id)
        create_plan_mutation = """
        mutation CreatePlan($plan: plan_insert_input!) {
            createPlan: insert_plan_one(object: $plan) {
                id
            }
        }
        """
        plan_resp = self.host_session.post_to_graphql(
            create_plan_mutation,
            plan=api_plan_create.to_dict(),
        )
        plan_id = plan_resp["id"]

        create_simulation_mutation = """
        mutation CreateSimulation($simulation: simulation_insert_input!) {
            createSimulation: insert_simulation_one(object: $simulation) {
                id
            }
        }
        """
        # TODO: determine how to handle arguments--should we accept another upload?
        _ = self.host_session.post_to_graphql(
            create_simulation_mutation, simulation={
                "arguments": {}, "plan_id": plan_id}
        )

        # TODO: move to batch insert once we confirm that the Aerie bug is fixed'
        for activity in plan_to_create.activities:
            self.create_activity(activity, plan_id, plan_to_create.start_time)

        return plan_id

    def create_activity(
        self,
        activity_to_create: ActivityCreate,
        plan_id: int,
        plan_start_time: arrow.Arrow,
    ) -> int:
        api_activity_create = activity_to_create.to_api_create(
            plan_id, plan_start_time)
        insert_activity_mutation = """
        mutation CreateActivity($activity: activity_directive_insert_input!) {
            createActivity: insert_activity_directive_one(object: $activity) {
                id
            }
        }
        """
        resp = self.host_session.post_to_graphql(
            insert_activity_mutation,
            activity=api_activity_create.to_dict(),
        )
        activity_id = resp["id"]

        return activity_id

    def update_activity(
        self,
        activity_id: int,
        activity_to_update: ActivityCreate,
        plan_id: int,
        plan_start_time: arrow.Arrow,
    ) -> int:
        activity_dict: Dict = activity_to_update.to_api_create(
            plan_id, plan_start_time).to_dict()
        update_activity_mutation = """
        mutation UpdateActvityDirective($id: Int!, $plan_id: Int!, $activity: activity_directive_set_input!) {
            updateActivity: update_activity_directive_by_pk(
            pk_columns: { id: $id, plan_id: $plan_id }, _set: $activity
            ) {
                id
            }
        }
        """
        resp = self.host_session.post_to_graphql(
            update_activity_mutation,
            id=activity_id,
            plan_id=plan_id,
            activity=activity_dict,
        )
        return resp["id"]

    def simulate_plan(self, plan_id: int, poll_period: int = 5) -> int:

        simulate_query = """
        query Simulate($plan_id: Int!) {
            simulate(planId: $plan_id) {
                status
                reason
                simulationDatasetId
            }
        }
        """

        def exec_sim_query():
            return self.host_session.post_to_graphql(simulate_query, plan_id=plan_id)

        resp = exec_sim_query()

        nonterminal_status = ["incomplete", "pending"]
        while resp["status"] in nonterminal_status:
            time.sleep(poll_period)
            resp = exec_sim_query()

        if resp["status"] == "failed":
            sys.exit(f"Simulation failed. Response:\n{resp}")

        sim_dataset_id = resp["simulationDatasetId"]
        return sim_dataset_id

    def get_resource_timelines(self, plan_id: int):
        samples = self.get_resource_samples(plan_id)
        api_resource_timeline = ApiResourceSampleResults.from_dict(samples)
        return api_resource_timeline

    def get_resource_samples(self, plan_id: int):
        resource_profile_query = """
        query GetSimulationDataset($plan_id: Int!) {
          simulation(where: { plan_id: { _eq: $plan_id } }, order_by: { id: desc }, limit: 1) {
            simulation_datasets(order_by: { id: desc }, limit: 1) {
              dataset {
                profiles {
                  name
                  profile_segments(order_by: { start_offset: asc }) {
                    dynamics
                    start_offset
                  }
                  type
                }
              }
            }
          }
        }
        """
        resp = self.host_session.post_to_graphql(
            resource_profile_query, plan_id=plan_id)
        profiles = resp[0]["simulation_datasets"][0]["dataset"]["profiles"]

        plan_duration_query = """
        query GetSimulationDataset($plan_id: Int!) {
          plan_by_pk(id: $plan_id) {
            duration
          }
        }
        """
        resp = self.host_session.post_to_graphql(
            plan_duration_query, plan_id=plan_id)
        duration = postgres_duration_to_microseconds(resp["duration"])

        # Parse profile segments into resource timelines
        resources = {}
        for profile in sorted(profiles, key=lambda _: _["name"]):
            name = profile["name"]
            profile_segments = profile["profile_segments"]
            profile_type = profile["type"]["type"]
            values = []

            for i in range(len(profile_segments)):
                segment = profile_segments[i]
                segmentOffset = postgres_duration_to_microseconds(
                    segment["start_offset"])
                if i + 1 < len(profile_segments):
                    nextSegmentOffset = postgres_duration_to_microseconds(
                        profile_segments[i + 1]["start_offset"])
                else:
                    nextSegmentOffset = duration

                dynamics = segment["dynamics"]

                if profile_type == 'discrete':
                    values.append({
                        "x": segmentOffset,
                        "y": dynamics,
                    })
                    values.append({
                        "x": nextSegmentOffset,
                        "y": dynamics,
                    })
                elif profile_type == 'real':
                    values.append({
                        "x": segmentOffset,
                        "y": dynamics["initial"],
                    })
                    values.append({
                        "x": nextSegmentOffset,
                        "y": dynamics["initial"] + dynamics["rate"] * ((nextSegmentOffset - segmentOffset) / 1000),
                    })

            resources[name] = values
        return {
            "resourceSamples": resources
        }

    def get_simulation_results(self, sim_dataset_id: int) -> str:

        sim_result_query = """
          query Simulation($sim_dataset_id: Int!) {
            simulated_activity(where: {simulation_dataset_id: {_eq: $sim_dataset_id}}) {
              activity_type_name
              attributes
              directive_id
              duration
              end_time
              id
              start_offset
              start_time
              simulation_dataset_id
            }
          }
        """
        resp = self.host_session.post_to_graphql(
            sim_result_query, sim_dataset_id=sim_dataset_id)
        return resp

    def delete_plan(self, plan_id: int) -> str:

        delete_plan_mutation = """
        mutation deletePlan($plan_id: Int!) {
            delete_plan_by_pk(id: $plan_id){
                name
            }
        }
        """

        resp = self.host_session.post_to_graphql(
            delete_plan_mutation, plan_id=plan_id)

        return resp["name"]

    def upload_mission_model(
        self, mission_model_path: str, project_name: str, mission: str, version: str
    ) -> int:

        # Create unique jar identifier for server side
        upload_timestamp = arrow.utcnow().isoformat()
        server_side_jar_name = (
            Path(mission_model_path).stem + "--" + upload_timestamp + ".jar"
        )
        with open(mission_model_path, "rb") as jar_file:
            resp = self.host_session.post_to_gateway_files(
                server_side_jar_name, jar_file)

        jar_id = resp["id"]

        create_model_mutation = """
        mutation CreateModel($model: mission_model_insert_input!) {
            createModel: insert_mission_model_one(object: $model) {
                id
            }
        }
        """

        api_mission_model = ApiMissionModelCreate(
            name=project_name, mission=mission, version=version, jar_id=jar_id
        )

        resp = self.host_session.post_to_graphql(
            create_model_mutation, model=api_mission_model.to_dict()
        )

        return resp["id"]

    def upload_sim_template(self, model_id: int, args: str, name: str):
        sim_template_mutation = """
            mutation uploadSimTemplate($model_id: Int!,
                                    $args: jsonb!,
                                    $name: String!) {
                insert_simulation_template(objects:
                    {
                    model_id: $model_id,
                    description: $name,
                    arguments: $args
                    }) {
                    returning {
                    id
                    }
                }
            }"""

        resp = self.host_session.post_to_graphql(
            sim_template_mutation, model_id=model_id, args=args, name=name
        )

        # Return simulation id
        return resp["returning"][0]["id"]

    def delete_mission_model(self, model_id: int) -> str:

        delete_model_mutation = """
        mutation deleteMissionModel($model_id: Int!) {
            delete_mission_model_by_pk(id: $model_id){
                name
            }
        }
        """

        resp = self.host_session.post_to_graphql(
            delete_model_mutation, model_id=model_id)

        return resp["name"]

    def get_mission_models(self) -> list[ApiMissionModelRead]:

        get_mission_model_query = """
        query getMissionModels {
            mission_model {
                name
                id
                version
                mission
                jar_id
            }
        }
        """

        resp = self.host_session.post_to_graphql(get_mission_model_query)
        api_mission_models = [
            ApiMissionModelRead.from_dict(model) for model in resp]

        return api_mission_models

    def create_config_args(self, plan_id: int, args: dict):

        update_config_arg_query = """
        mutation UpdateConfigArgument($sim_id: Int!, $args: jsonb!) {
            updateSimulation: update_simulation_by_pk(
            pk_columns: { id: $sim_id },
            _set: {
                arguments: $args
                simulation_template_id: null
            }) {
                arguments
                id
                template: simulation_template {
                    arguments
                    description
                    id
                }
            }
        }
        """

        plan = self.get_activity_plan_by_id(plan_id)
        sim_id = plan.sim_id

        resp = self.host_session.post_to_graphql(
            update_config_arg_query, sim_id=sim_id, args=args)

        return resp["arguments"]

    def update_config_args(self, plan_id: int, args: dict):

        update_config_arg_query = """
        mutation UpdateConfigArgument($sim_id: Int!, $args: jsonb!) {
            updateSimulation: update_simulation_by_pk(
            pk_columns: { id: $sim_id },
            _set: {
                arguments: $args
                simulation_template_id: null
            }) {
                arguments
                id
                template: simulation_template {
                    arguments
                    description
                    id
                }
            }
        }
        """
        plan = self.get_activity_plan_by_id(plan_id)
        sim_id = plan.sim_id

        # Get currently set arguments
        curr_args_dict = self.get_config(plan_id=plan_id)

        # Out of the current arguments, update provided value and keep
        # previous arguments the same
        final_args = {}
        for arg in curr_args_dict.keys():
            if args.get(arg) is None:
                final_args[arg] = curr_args_dict[arg]
            else:
                final_args[arg] = args[arg]
                args.pop(arg)

        # Add any new arguments not previously configured
        for arg in args:
            final_args[arg] = args[arg]

        resp = self.host_session.post_to_graphql(
            update_config_arg_query, sim_id=sim_id, args=final_args)

        return resp["arguments"]

    def get_config(self, plan_id: int):

        plan = self.get_activity_plan_by_id(plan_id)
        sim_id = plan.sim_id

        get_config_query = """
        query getConfig($sim_id: Int!) {
            simulation_by_pk(id: $sim_id) {
                arguments
            }
        }
        """

        resp = self.host_session.post_to_graphql(
            get_config_query, sim_id=sim_id)

        return resp["arguments"]

    def get_activity_interface(self, activity_name: str, model_id: int) -> str:
        """Download Typescript interface for an activity from Aerie model

        Args:
            activity_name (str): Model name of the activity
            model_id (int): ID of the model in Aerie

        Returns:
            str: Contents of the interface file
        """

        get_activity_interface_query = """
        query GetActivityTypescript(
            $activity_type_name: String!
            $mission_model_id: Int!
        ) {
            getActivityTypeScript(
                activityTypeName: $activity_type_name
                missionModelId: $mission_model_id
            ) {
                typescriptFiles {
                    content
                }
                reason
                status
            }
        }
        """
        data = self.host_session.post_to_graphql(
            get_activity_interface_query,
            activity_type_name=activity_name,
            mission_model_id=model_id,
        )
        return data["typescriptFiles"][0]["content"]

    def create_expansion_rule(
        self,
        expansion_logic: str,
        activity_name: str,
        model_id: str,
        command_dictionary_id: str,
    ) -> int:
        """Submit expansion logic to an Aerie instance

        Args:
            expansion_logic (str): String contents of the expansion file
            activity_name (str): Name of the activity
            model_id (str): Aerie model ID
            command_dictionary_id (str): Aerie command dictionary ID

        Returns:
            int: Expansion Rule ID in Aerie
        """

        create_expansion_logic_query = """
        mutation UploadExpansionLogic(
            $activity_type_name: String!
            $expansion_logic: String!
            $command_dictionary_id: Int!
            $mission_model_id: Int!
        ) {
            addCommandExpansionTypeScript(
                activityTypeName: $activity_type_name
                expansionLogic: $expansion_logic
                authoringCommandDictionaryId: $command_dictionary_id
                authoringMissionModelId: $mission_model_id
            ) {
                id
            }
        }
        """
        data = self.host_session.post_to_graphql(
            create_expansion_logic_query,
            activity_type_name=activity_name,
            expansion_logic=expansion_logic,
            mission_model_id=model_id,
            command_dictionary_id=command_dictionary_id,
        )

        return data["id"]

    def create_expansion_set(
        self, command_dictionary_id: int, model_id: int, expansion_ids: List[int]
    ) -> int:
        """Create an Aerie expansion set given a list of activity IDs

        Args:
            command_dictionary_id (int): ID of Aerie command dictionary
            model_id (int): ID of Aerie mission model
            expansion_ids (List[int]): List of expansion IDs to include in the set

        Returns:
            int: Expansion set ID
        """

        create_expansion_set_query = """
        mutation CreateExpansionSet(
            $command_dictionary_id: Int!
            $mission_model_id: Int!
            $expansion_ids: [Int!]!
        ) {
            createExpansionSet(
                commandDictionaryId: $command_dictionary_id
                missionModelId: $mission_model_id
                expansionIds: $expansion_ids
            ) {
                id
            }
        }
        """
        data = self.host_session.post_to_graphql(
            create_expansion_set_query,
            command_dictionary_id=command_dictionary_id,
            mission_model_id=model_id,
            expansion_ids=expansion_ids,
        )
        return data["id"]

    def list_expansion_sets(self) -> List[ExpansionSet]:
        list_sets_query = """
        query ListExpansionSets {
            expansion_set {
                id
                command_dict_id
                created_at
                expansion_rules {
                    id
                }
            }
        }
        """
        resp = self.host_session.post_to_graphql(list_sets_query)
        return [ExpansionSet.from_dict(i) for i in resp]

    def create_sequence(self, seq_id: str, simulation_dataset_id: int) -> None:
        """Create a sequence on a given simulation dataset

        Args:
            seq_id (str): ID of the new sequence
            simulation_dataset_id (int): ID of the parent simulation dataset
        """

        create_sequence_query = """
        mutation CreateSequence(
            $seq_id: String!
            $simulation_dataset_id: Int!
        ) {
            insert_sequence_one(
                object: {
                    simulation_dataset_id: $simulation_dataset_id,
                    seq_id: $seq_id
                }
            ) {
                seq_id
            }
        }
        """
        self.host_session.post_to_graphql(
            create_sequence_query,
            simulation_dataset_id=simulation_dataset_id,
            seq_id=seq_id,
        )

    def get_rule_ids_by_activity_type(self, activity_type: str) -> List[int]:
        """Get ID of all expansion rules for a given activity type

        Args:
            activity_type (str): Activity type name

        Returns:
            List[int]: Expansion rule IDs, in ascending order
        """

        get_expansion_ids_query = """
        query GetExpansionLogic(
            $activity_type: String!
        ) {
            expansion_rule(
                where: {
                    activity_type: {
                        _eq: $activity_type
                    }
                }
            ){
                id
            }
            }
        """
        data = self.host_session.post_to_graphql(
            get_expansion_ids_query, activity_type=activity_type)
        rule_ids = [int(v["id"]) for v in data]
        rule_ids.sort()
        return rule_ids

    def list_expansion_rules(self) -> List[ExpansionRule]:
        """List all expansion rules

        Returns:
            List[ExpansionRule]
        """
        list_rules_query = """
        query ListExpansionRules {
            expansion_rule {
                activity_type
                id
                authoring_mission_model_id
                authoring_command_dict_id
            }
        }
        """
        resp = self.host_session.post_to_graphql(list_rules_query)
        return [ExpansionRule.from_dict(r) for r in resp]

    def get_rules_by_type(self) -> Dict[str, List[ExpansionRule]]:
        """Get all expansion rules, sorted by activity type

        Returns:
            Dict[str, List[ExpansionRule]]
        """

        rules = self.list_expansion_rules()

        rules_by_type = {}
        for r in rules:
            if r.activity_type in rules_by_type.keys():
                rules_by_type[r.activity_type].append(r)
            else:
                rules_by_type[r.activity_type] = [r]

        return rules_by_type

    def get_simulation_dataset_ids_by_plan_id(self, plan_id: int) -> List[int]:
        """Get the IDs of the simulation datasets generated from a given plan

        Args:
            plan_id (int): ID of parent plan

        Returns:
            List[int]: IDs of simulation datasets in descending order
        """

        get_simulation_dataset_query = """
        query GetSimulationDatasetId($plan_id: Int!) {
          simulation(where: {plan_id: {_eq: $plan_id}}, order_by: { id: desc }, limit: 1) {
            simulation_datasets(order_by: { id: desc }) {
              id
            }
          }
        }
        """
        data = self.host_session.post_to_graphql(
            get_simulation_dataset_query, plan_id=plan_id)
        return [d["id"] for d in data[0]["simulation_datasets"]]

    def expand_simulation(
        self, simulation_dataset_id: int, expansion_set_id: int
    ) -> int:
        """Expand simulated activities from a simulation dataset given an expansion set

        Args:
            simulation_dataset_id (int): Dataset of activities to be expanded
            expansion_set_id (int): ID of expansion set to use

        Returns:
            int: Expansion Run ID
        """

        expand_simulation_query = """
        mutation ExpandPlan(
            $expansion_set_id: Int!
            $simulation_dataset_id: Int!
        ) {
            expandAllActivities(
                expansionSetId: $expansion_set_id,
                simulationDatasetId: $simulation_dataset_id
            ) {
                id
            }
        }
        """
        data = self.host_session.post_to_graphql(
            expand_simulation_query,
            expansion_set_id=expansion_set_id,
            simulation_dataset_id=simulation_dataset_id,
        )

        return int(data["id"])

    def list_expansion_runs(self, simulation_dataset_id: int) -> List[ExpansionRun]:
        """
        List all expansion runs from a given simulation dataset.
        """
        get_runs_query = """
        query GetExpansionRuns($simulation_dataset_id: Int!) {
            expansion_run(order_by: { created_at: desc }, where: { simulation_dataset_id: { _eq: $simulation_dataset_id } }) {
                created_at
                id
                expansion_set_id
                simulation_dataset_id
            }
        }
        """
        resp = self.host_session.post_to_graphql(
            get_runs_query,
            simulation_dataset_id=simulation_dataset_id
        )
        return [ExpansionRun.from_dict(r) for r in resp]

    def get_expansion_run(
        self, expansion_run_id: int, include_commands: bool = False
    ) -> ExpansionRun:
        """
        Get metadata about an expansion run and, optionally, all expanded 
        activity instance commands/errors.
        """
        get_run_query = """
        query GetExpansionRun($expansion_run_id: Int!, $include_commands: Boolean!) {
            expansion_run(order_by: { created_at: desc }, where: { id: { _eq: $expansion_run_id } }) {
                created_at
                id
                expansion_set_id
                simulation_dataset_id
                activity_instance_commands @include(if: $include_commands) {
                    activity_instance_id
                    commands
                    errors
                }
            }
        }
        """
        resp = self.host_session.post_to_graphql(
            get_run_query,
            expansion_run_id=expansion_run_id,
            include_commands=include_commands
        )
        return ExpansionRun.from_dict(resp[0])

    def link_activities_to_sequence(
        self, seq_id: str, simulation_dataset_id: int, simulated_activity_ids: List[int]
    ) -> None:
        """Link a set of simulated activities to a sequence for expansion

        Take a set of simulated activities (not plan activities) of a given
        simulation dataset and link them to an existing sequence so that
        expansion outputs from the given activities are included in the
        sequence.

        Args:
            seq_id (str): ID of the sequence to which activities will be linked
            simulation_dataset_id (int): Dataset which contains the activities being linked
            simulated_activity_ids (List[int]): IDs of simulated activities to be linked
        """

        for simulated_activity_id in simulated_activity_ids:

            link_activity_to_sequence_query = """
            mutation LinkSimulatedActivityToSequence(
                $seq_id: String!
                $simulation_dataset_id: Int!
                $simulated_activity_id: Int!
            ) {
                insert_sequence_to_simulated_activity_one(
                    object: {
                        seq_id: $seq_id
                        simulated_activity_id: $simulated_activity_id
                        simulation_dataset_id: $simulation_dataset_id
                    }
                ) {
                    seq_id
                }
            }
            """
            self.host_session.post_to_graphql(
                link_activity_to_sequence_query,
                seq_id=seq_id,
                simulated_activity_id=simulated_activity_id,
                simulation_dataset_id=simulation_dataset_id,
            )

    def get_simulated_activity_ids(self, simulation_dataset_id: int) -> List[int]:
        """Get the IDs of all simulated activities in a simulation dataset

        Args:
            simulation_dataset_id (int): ID of Aerie simulation dataset

        Returns:
            List[int]: List of simulated activity IDs
        """

        get_simulated_activity_ids_query = """
        query GetSimulatedActivities(
            $simulation_dataset_id: Int!
        ) {
            simulated_activity(
                where: {
                    simulation_dataset_id: { _eq: $simulation_dataset_id }
                }
            ) {
                id
            }
        }
        """
        data = self.host_session.post_to_graphql(
            get_simulated_activity_ids_query,
            simulation_dataset_id=simulation_dataset_id,
        )
        simulated_activity_ids = [int(o["id"]) for o in data]
        return simulated_activity_ids

    def get_expanded_sequence(self, seq_id: str, simulation_dataset_id: int) -> Dict:
        """Get SeqJson from an expanded Aerie sequence

        Args:
            seq_id (str): ID of the sequence
            simulation_dataset_id (int): ID of the simulation dataset being expanded

        Returns:
            Dict: SeqJson as Python Dictionary
        """

        get_expanded_sequence_query = """
        query GetSequenceSeqJson(
            $seq_id: String!
            $simulation_dataset_id: Int!
        ) {
            getSequenceSeqJson(
                seqId: $seq_id,
                simulationDatasetId: $simulation_dataset_id
            ) {
                seqJson {
                    steps {
                        args
                        metadata
                        stem
                        type
                        time {
                            tag
                            type
                        }
                    }
                    metadata
                    id
                }
            }
        }
        """
        data = self.host_session.post_to_graphql(
            get_expanded_sequence_query,
            seq_id=seq_id,
            simulation_dataset_id=simulation_dataset_id,
        )
        return data["seqJson"]

    def list_sequences(self, simulation_dataset_id: int) -> List[str]:
        """List all sequences tied to a simulation dataset

        Args:
            simulation_dataset_id (int): ID on the Aerie host

        Returns:
            List[str]: Sequence IDs
        """

        list_sequences_query = """
        query MyQuery($simulation_dataset_id: Int!) {
            sequence(where: { simulation_dataset_id: { _eq: $simulation_dataset_id } }) {
                seq_id
            }
        }
        """
        data = self.host_session.post_to_graphql(
            list_sequences_query,
            simulation_dataset_id=simulation_dataset_id
        )
        return [s["seq_id"] for s in data]

    def delete_sequence(self, seq_id: str, simulation_dataset_id: int) -> None:
        """Delete a command sequence

        Args:
            seq_id (str): Sequence ID
            simulation_dataset_id (int): ID of Simulation Dataset where the sequence exists
        """
        delete_sequence_query = """
        mutation DeleteExpansionSequence($seq_id: String!, $simulation_dataset_id: Int!) {
            deleteExpansionSequence: delete_sequence_by_pk(seq_id: $seq_id, simulation_dataset_id: $simulation_dataset_id) {
                seq_id
            }
        }
        """
        self.host_session.post_to_graphql(
            delete_sequence_query,
            seq_id=seq_id,
            simulation_dataset_id=simulation_dataset_id
        )

    def get_all_expansion_run_commands(self, expansion_run_id: int) -> List:
        """Get commands from all activity instances in an expansion run

        Provides commands without linking to a particular sequence.

        Args:
            expansion_run_id (int): ID of Aerie expansion run

        Returns:
            List: SeqJson-formatted command steps
        """

        expansion_run_commands_query = """
        query GetAllExpandedCommandsForExpansionRun(
            $expansion_run_id: Int!
        ) {
            activity_instance_commands(
                where: {
                    expansion_run: {
                        id: { _eq: $expansion_run_id }
                    }
                }
            ) {
                activity_instance_id
                commands
                errors
            }
        }
        """
        data = self.host_session.post_to_graphql(
            expansion_run_commands_query, expansion_run_id=expansion_run_id
        )

        expansion_run_commands = []
        for activity_instance in data:
            if activity_instance["commands"]:
                expansion_run_commands.extend(activity_instance["commands"])

        return expansion_run_commands

    def get_all_activity_types(self, model_id: int) -> List[str]:
        """Get a list of all activity types defined in a given mission model

        Args:
            model_id (int): ID of the Aerie mission model

        Returns:
            List[str]: List of activity type names
        """

        get_types_query = """
        query GetActivityTypes(
            $model_id: Int!
        ) {
            activity_type(where: { model_id: { _eq: $model_id } }) {
                name
            }
        }
        """
        data = self.host_session.post_to_graphql(
            get_types_query, model_id=model_id)
        activity_types = [o["name"] for o in data]
        return activity_types

    def list_command_dictionaries(self) -> List[CommandDictionaryInfo]:
        """List all command dictionaries on an Aerie host

        Returns:
            List[CommandDictionaryInfo]
        """
        list_dictionaries_query = """
        query ListCommandDictionaries {
            command_dictionary {
                id
                mission
                version
                created_at
            }
        }
        """
        resp = self.host_session.post_to_graphql(list_dictionaries_query)
        return [CommandDictionaryInfo.from_dict(i) for i in resp]

    def upload_command_dictionary(self, command_dictionary_string: str) -> int:
        """Upload an AMPCS command dictionary to an Aerie instance

        Args:
            command_dictionary_string (str): Contents from XML command dictionary file (newlne-delimited)

        Returns:
            int: Command Dictionary ID
        """

        upload_command_dictionary_query = """
        mutation Upload(
            $command_dictionary_string: String!
        ) {
            uploadDictionary(dictionary: $command_dictionary_string) {
                id
                command_types_typescript_path
                mission
                version
                created_at
                updated_at
            }
        }
        """
        data = self.host_session.post_to_graphql(
            upload_command_dictionary_query,
            command_dictionary_string=command_dictionary_string,
        )

        return data["id"]

    def get_typescript_dictionary(self, command_dictionary_id: int) -> str:
        """Download Typescript command dictionary for writing EDSL Sequences and Expansion

        Prepends mission model name and command dictionary version in a comment
        block header of the Typescript.

        Args:
            command_dictionary_id (int): ID of command dictionary in Aerie instance

        Returns:
            str: Typescript file contents
        """

        get_command_dictionary_metadata_query = """
        query MyQuery($command_dictionary_id: Int!) {
        command_dictionary(where: { id: { _eq: $command_dictionary_id } }) {
            mission
            version
        }
        }
        """

        get_typescript_dictionary_query = """
        query GetCommandTypescript($command_dictionary_id: Int!) {
        getCommandTypeScript(commandDictionaryId: $command_dictionary_id) {
            reason
            status
            typescriptFiles {
                content
                filePath
            }
        }
        }
        """

        data = self.host_session.post_to_graphql(
            get_command_dictionary_metadata_query,
            command_dictionary_id=command_dictionary_id,
        )[0]

        command_dictionary_mission = data["mission"]
        command_dictionary_version = data["version"]

        data = self.host_session.post_to_graphql(
            get_typescript_dictionary_query, command_dictionary_id=command_dictionary_id
        )

        typescript_dictionary_string = next(
            filter(
                lambda x: x["filePath"].endswith("command-types.ts"),
                data["typescriptFiles"],
            )
        )["content"]

        # TODO add Aerie version below once the API supports this
        # Include metadata about command dictionary in header
        typescript_dictionary_string = "\n".join(
            [
                "/**",
                f"* Mission:                    {command_dictionary_mission}",
                f"* Command Dictionary Version: R{command_dictionary_version}",
                "*/",
                "",
                typescript_dictionary_string,
            ]
        )

        return typescript_dictionary_string

    def __expand_activity_arguments(self, plan: ActivityPlanRead, full_args: str = None) -> ActivityPlanRead:
        if full_args is None or full_args == "" or full_args.lower() == "false":
            return plan
        expand_all = full_args.lower() == "true"
        expand_types = {} if expand_all else set(full_args.split(","))
        for activity in plan.activities:
            if expand_all or activity.type in expand_types:
                query = """
                query ($args: ActivityArguments!, $act_type: String!, $model_id: ID!) {
                    getActivityEffectiveArguments(
                        activityArguments: $args,
                        activityTypeName: $act_type,
                        missionModelId: $model_id
                    )
                    {
                        arguments
                        errors
                        success
                    }
                }
                """
                resp = self.host_session.post_to_graphql(
                    query,
                    args=activity.parameters,
                    act_type=activity.type,
                    model_id=plan.model_id,
                )
                activity.parameters = ApiEffectiveActivityArguments.from_dict(
                    resp).arguments
        return plan
