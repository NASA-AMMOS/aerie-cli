import sys
import time
from pathlib import Path
from typing import Dict
from typing import List
from typing import Union
from copy import deepcopy

import arrow

from .schemas.api import ApiActivityPlanRead
from .schemas.api import ApiEffectiveActivityArguments
from .schemas.api import ApiMissionModelCreate
from .schemas.api import ApiMissionModelRead
from .schemas.api import ApiResourceSampleResults
from .schemas.api import ApiParcelRead
from .schemas.client import Activity
from .schemas.client import ActivityPlanCreate
from .schemas.client import ActivityPlanRead
from .schemas.client import DictionaryMetadata
from .schemas.client import DictionaryType
from .schemas.client import SequenceAdaptationMetadata
from .schemas.client import Parcel
from .schemas.client import ExpansionRun
from .schemas.client import ExpansionRule
from .schemas.client import ExpansionSet
from .schemas.client import ResourceType
from .utils.serialization import postgres_interval_to_microseconds
from .aerie_host import AerieHost


class AerieClient:
    """Client-side behavior for aerie-cli

    Class encapsulates logic to query and send files to a given Aerie host.
    """

    def __init__(self, aerie_host: AerieHost):
        """Instantiate a client with an authenticated host session

        Args:
            aerie_host (AerieHost): Aerie host information, including authentication if necessary
        """
        self.aerie_host = aerie_host

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
                tags {
                    tag {
                        id
                        name
                    }
                }
                activity_directives(order_by: { start_offset: asc }) {
                    id
                    name
                    type
                    start_offset
                    arguments
                    metadata
                    anchor_id
                    anchored_to_start
                }
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(query, plan_id=plan_id)
        api_plan = ApiActivityPlanRead.from_dict(resp)
        plan = ActivityPlanRead.from_api_read(api_plan)
        return self.__expand_activity_arguments(plan, full_args)

    def list_all_activity_plans(self) -> List[ActivityPlanRead]:
        list_all_plans_query = """
        query list_all_plans {
            plan(order_by: { id: asc }) {
                id
                model_id
                name
                start_time
                duration
                simulations{
                    id
                }
                tags {
                    tag {
                        id
                        name
                    }
                }
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(list_all_plans_query)
        activity_plans = []
        for plan in resp:
            plan = ApiActivityPlanRead.from_dict(plan)
            plan = ActivityPlanRead.from_api_read(plan)
            activity_plans.append(plan)
        return activity_plans

    def get_all_activity_plans(self, full_args: str = None) -> List[ActivityPlanRead]:
        """Get all activity plans

        Args:
            full_args (str): comma separated list of activity types for which to
            get full arguments, otherwise only modified arguments are returned.
            Set to "true" to get full arguments for all activity types.
            Disabled if missing, None, "false", or "".

        Returns:
            List[ActivityPlanRead]
        """

        # List all plans then loop to get activities from each
        plans_metadata = self.list_all_activity_plans()
        plans = [self.get_activity_plan_by_id(p.id, full_args) for p in plans_metadata]

        return plans

    def get_plan_id_by_sim_id(self, simulation_dataset_id: int) -> int:
        """Get Plan ID by Simulation Dataset ID

        Args:
            simulation_dataset_id (int): Aerie Simulation Dataset ID

        Returns:
            int: Plan ID
        """
        get_plan_id_query = """
        query PlanIdBySimDatasetId($simulation_dataset_id: Int!) {
            simulation_dataset_by_pk(id: $simulation_dataset_id) {
                simulation {
                    plan {
                        id
                    }
                }
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(
            get_plan_id_query,
            simulation_dataset_id=simulation_dataset_id
        )
        return resp['simulation']['plan']['id']
    
    def get_tag_id_by_name(self, tag_name: str):
        get_tags_by_name_query = """
        query GetTagByName($name: String) {
            tags(where: {name: {_eq: $name}}) {
                id
            }
        }
        """

        #make default color of tag white
        create_new_tag = """
        mutation CreateNewTag($name: String, $color: String = "#FFFFFF") {
            insert_tags_one(object: {name: $name, color: $color}) {
                id
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(
            get_tags_by_name_query, 
            name=tag_name
        )

        #if a tag with the specified name exists then returns the ID, else creates a new tag with this name
        if len(resp) > 0: 
            return resp[0]["id"]
        else: 
            new_tag_resp = self.aerie_host.post_to_graphql(
                create_new_tag, 
                name=tag_name
            )

            return new_tag_resp["id"]

    def add_plan_tag(self, plan_id: int, tag_name: str):
        add_tag_to_plan = """
        mutation AddTagToPlan($plan_id: Int, $tag_id: Int) {
            insert_plan_tags(objects: {plan_id: $plan_id, tag_id: $tag_id}) {
                returning {
                    tag_id
                }
            }
        }
        """
        
        #add tag to plan
        resp = self.aerie_host.post_to_graphql(
            add_tag_to_plan, 
            plan_id=plan_id, 
            tag_id=self.get_tag_id_by_name(tag_name)
        )

        return resp['returning'][0]

    def create_activity_plan(
        self, model_id: int, plan_to_create: ActivityPlanCreate
    ) -> int:

        api_plan_create = plan_to_create.to_api_create(model_id)
        create_plan_mutation = """
        mutation CreatePlan($plan: plan_insert_input!) {
            createPlan: insert_plan_one(object: $plan) {
                id
                revision
            }
        }
        """
        plan_resp = self.aerie_host.post_to_graphql(
            create_plan_mutation,
            plan=api_plan_create.to_dict(),
        )
        plan_id = plan_resp["id"]
        plan_revision = plan_resp["revision"]

        #add plan tags if exists from plan_to_create
        for tag in plan_to_create.tags:
            self.add_plan_tag(plan_id, tag["tag"]["name"])
                
        # This loop exists to make sure all anchor IDs are updated as necessary

        # Deep copy activities so we can augment and pop from the list
        activities_to_upload = deepcopy(plan_to_create.activities)

        # Map of old to new directive IDs
        directive_id_mapping = {}

        # Boolean catches errors to avoid an infinite loop
        running = True
        while len(activities_to_upload):
            running = False

            for act in activities_to_upload:
                # If activity is anchored and the anchor isn't known yet, pass
                # If activity is anchored and the anchor is known, add it
                if act.anchor_id and act.anchor_id not in directive_id_mapping.keys():
                    continue
                else:
                    if act.anchor_id:
                        act.anchor_id = directive_id_mapping[act.anchor_id]
                    directive_id_mapping[act.id] = self.create_activity(act, plan_id)
                    activities_to_upload.remove(act)
                    running = True

            if not running:
                raise RuntimeError(
                    f"Failed to anchor activities: {', '.join([act.name for act in activities_to_upload])}"
                )

        simulation_start_time = plan_to_create.start_time.isoformat()
        simulation_end_time = plan_to_create.end_time.isoformat()
        update_simulation_mutation = """
        mutation updateSimulationBounds($plan_id: Int!, $simulation_start_time: timestamptz!, $simulation_end_time: timestamptz!) {
            update_simulation(
                where: {plan_id: {_eq: $plan_id}},
                _set: {
                    simulation_start_time: $simulation_start_time,
                    simulation_end_time: $simulation_end_time
                }
            ){
                affected_rows
            }
        }
        """
        _ = self.aerie_host.post_to_graphql(
            update_simulation_mutation,
            plan_id=plan_id,
            simulation_start_time=simulation_start_time,
            simulation_end_time=simulation_end_time
        )

        return plan_id

    def create_activity(self, activity_to_create: Activity, plan_id: int) -> int:
        api_activity_create = activity_to_create.to_api_create(plan_id)
        insert_activity_mutation = """
        mutation CreateActivity($activity: activity_directive_insert_input!) {
            createActivity: insert_activity_directive_one(object: $activity) {
                id
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(
            insert_activity_mutation,
            activity=api_activity_create.to_dict()
        )
        activity_id = resp["id"]

        return activity_id

    def update_activity(
        self,
        activity_id: int,
        activity_to_update: Activity,
        plan_id: int
    ) -> int:
        activity_dict: Dict = activity_to_update.to_api_update().to_dict()
        update_activity_mutation = """
        mutation UpdateActvityDirective($id: Int!, $plan_id: Int!, $activity: activity_directive_set_input!) {
            updateActivity: update_activity_directive_by_pk(
            pk_columns: { id: $id, plan_id: $plan_id }, _set: $activity
            ) {
                id
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(
            update_activity_mutation,
            id=activity_id,
            plan_id=plan_id,
            activity=activity_dict,
        )
        return resp["id"]

    def get_all_activity_presets(self, m_id:int) -> List:
        get_all_presets_query = """
        query ($model_id: Int!) {
            activity_presets (where: {model_id:{_eq:$model_id}}){
                id
                model_id
                name
                associated_activity_type
                arguments
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(
            get_all_presets_query,
            model_id=m_id
        )
        return resp

    def upload_activity_presets(self, upload_obj):
        upload_activity_presets_query = """
        mutation upload_presets($object: [activity_presets_insert_input!]!) {
            insert_activity_presets(objects: $object, 
                                    on_conflict: {constraint: activity_presets_model_id_associated_activity_type_name_key, 
                                                  update_columns: arguments}
                                    ) {
                returning {
                    model_id
                    id
                    associated_activity_type
                    arguments
                    name
                }
            }
        }"""

        resp = self.aerie_host.post_to_graphql(
            upload_activity_presets_query, 
            object = upload_obj
        )

        return resp["returning"]

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
            return self.aerie_host.post_to_graphql(simulate_query, plan_id=plan_id)

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
        samples = self.get_resource_samples(self.get_simulation_dataset_ids_by_plan_id(plan_id)[0])
        api_resource_timeline = ApiResourceSampleResults.from_dict(samples)
        return api_resource_timeline

    def get_resource_samples(self, simulation_dataset_id: int, state_names: List=None):
        """Pull resource samples from a simulation dataset, optionally filtering for specific states

        Each resource's values are returned in a list of points {x: <time>, y: <value>}.
        
        Times are provided in microseconds from plan start.

        Numeric resources can be either discrete-valued or vary linearly between samples. Samples are processed such 
        that a linear interpolation between samples will always return a correct value. Two points at the same 
        timestamp indicate a discontinuity.

        Args:
            simulation_dataset_id (int)
            state_names (List, optional): List of state/resource names to pull. Defaults to None (all).

        Returns:
            Dict: Object with key "resourceSamples," the value of which is a dictionary of resource sample series keyed by resource name.
        """        

        # checks to see if user inputted specific states. If so, use this query.
        if state_names:
            resource_profile_query = """
            query GetSimulationDataset($simulation_dataset_id: Int!, $state_names: [String!]) {
                simulation_dataset_by_pk(id: $simulation_dataset_id) {
                    dataset {
                        profiles(where: { name: { _in: $state_names } }) {
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
            """

            resp = self.aerie_host.post_to_graphql(resource_profile_query, simulation_dataset_id=simulation_dataset_id, state_names=state_names)

        else:
            resource_profile_query = """
            query GetSimulationDataset($simulation_dataset_id: Int!) {
                simulation_dataset_by_pk(id: $simulation_dataset_id) {
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
            """
            resp = self.aerie_host.post_to_graphql(resource_profile_query, simulation_dataset_id=simulation_dataset_id)
        
        
        profiles = resp["dataset"]["profiles"]

        plan_duration_query = """
        query GetPlanDuration($plan_id: Int!) {
          plan_by_pk(id: $plan_id) {
            duration
          }
        }
        """
        resp = self.aerie_host.post_to_graphql(
            plan_duration_query,
            plan_id=self.get_plan_id_by_sim_id(simulation_dataset_id),
        )
        duration = postgres_interval_to_microseconds(resp["duration"])

        # Parse profile segments into resource timelines
        resources = {}
        for profile in sorted(profiles, key=lambda _: _["name"]):
            name = profile["name"]
            profile_segments = profile["profile_segments"]
            profile_type = profile["type"]["type"]
            values = []

            for i in range(len(profile_segments)):
                segment = profile_segments[i]

                # The segment offset is the offset from plan start to the beginning of this segment
                segment_start_time = postgres_interval_to_microseconds(
                    segment["start_offset"]
                )

                # If this is *not* the last segment, then this segment ends where the next segment starts
                if i + 1 < len(profile_segments):
                    segment_end_time = postgres_interval_to_microseconds(
                        profile_segments[i + 1]["start_offset"]
                    )

                # If this is the last segment, then this segment ends at the end of the plan
                else:
                    segment_end_time = duration

                dynamics = segment["dynamics"]

                # Discrete profiles don't have rates
                if profile_type == 'discrete':

                    # Define points at the start and end of this profile segment
                    start_value = {
                        "x": segment_start_time,
                        "y": dynamics,
                    }
                    end_value = {
                        "x": segment_end_time,
                        "y": dynamics,
                    }

                    # Check if the previous point is identical to this one
                    if len(values) and (values[-1] == start_value):

                        # If the resource value hasn't changed, remove the previous point and extend out to the end of this profile segment
                        values.pop()
                        values.append(end_value)

                    else:

                        # If the value has changed, add points at the boundaries of this segment
                        values.append(start_value)
                        values.append(end_value)

                # Real profiles can have rates over time
                elif profile_type == 'real':

                    start_value = {
                        "x": segment_start_time,
                        "y": dynamics["initial"],
                    }

                    # If the last value is not identical to this segment's start, then add the start
                    if (len(values) and values[-1] != start_value) or (
                        len(values) == 0
                    ):
                        values.append(start_value)

                    # Add a value at the end of this segment
                    values.append(
                        {
                            "x": segment_end_time,
                            "y": dynamics["initial"]
                            + dynamics["rate"]
                            * ((segment_end_time - segment_start_time) / 1e6),
                        }
                    )

                else:
                    raise ValueError(f"Unknown resource profile type: {profile_type}")

            resources[name] = values
        return {
            "resourceSamples": resources
        }

    def get_simulation_results(self, sim_dataset_id: int) -> str:

        sim_result_query = """
        query Simulation($sim_dataset_id: Int!) {
            simulated_activity(where: { simulation_dataset_id: { _eq: $sim_dataset_id } }, order_by: { start_offset: asc }) {
                activity_type_name
                attributes
                directive_id
                duration
                end_time
                id
                start_offset
                start_time
                simulation_dataset_id
                parent_id
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(
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

        resp = self.aerie_host.post_to_graphql(
            delete_plan_mutation, plan_id=plan_id)

        return resp["name"]

    def upload_file(self, path: str) -> int:
        upload_timestamp = arrow.utcnow().isoformat()
        path_obj = Path(path)
        server_side_path = (
                path_obj.stem + "--" + upload_timestamp + path_obj.suffix
        )
        with open(path, "rb") as f:
            resp = self.aerie_host.post_to_gateway_files(
                server_side_path, f)
            return resp["id"]

    def upload_mission_model(
        self, mission_model_path: str, project_name: str, mission: str, version: str
    ) -> int:

        # Create unique jar identifier for server side
        jar_id = self.upload_file(mission_model_path)

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

        resp = self.aerie_host.post_to_graphql(
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

        resp = self.aerie_host.post_to_graphql(
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

        resp = self.aerie_host.post_to_graphql(
            delete_model_mutation, model_id=model_id)

        return resp["name"]

    def get_mission_models(self) -> List[ApiMissionModelRead]:

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

        resp = self.aerie_host.post_to_graphql(get_mission_model_query)
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

        resp = self.aerie_host.post_to_graphql(
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

        resp = self.aerie_host.post_to_graphql(
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

        resp = self.aerie_host.post_to_graphql(
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
        data = self.aerie_host.post_to_graphql(
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
        parcel_id: str,
        name: str = None,
        description: str = None
    ) -> int:
        """Submit expansion logic to an Aerie instance

        Args:
            expansion_logic (str): String contents of the expansion file
            activity_name (str): Name of the activity
            model_id (str): Aerie model ID
            parcel_id (str): Aerie sequencing parcel ID
            name (str, Optional): Name of the expansion rule
            description (str, Optional): Description of the expansion rule

        Returns:
            int: Expansion Rule ID in Aerie
        """

        create_expansion_logic_query = """
        mutation CreateExpansionRule($rule: expansion_rule_insert_input!) {
            createExpansionRule: insert_expansion_rule_one(object: $rule) {
                id
            }
        }
        """
        rule = {
            "activity_type": activity_name,
            "parcel_id": parcel_id,
            "authoring_mission_model_id": model_id,
            "expansion_logic": expansion_logic,
            "name": name if (name is not None) else activity_name + arrow.utcnow().format("_YYYY-MM-DDTHH-mm-ss"),
            "description": description if (description is not None) else ""
        }
        data = self.aerie_host.post_to_graphql(
            create_expansion_logic_query,
            rule=rule
        )

        return data["id"]

    def create_expansion_set(
        self, parcel_id: int, model_id: int, expansion_ids: List[int], name: str, description: str=None
    ) -> int:
        """Create an Aerie expansion set given a list of activity IDs

        Args:
            parcel_id (int): Aerie sequencing parcel ID
            model_id (int): ID of Aerie mission model
            expansion_ids (List[int]): List of expansion IDs to include in the set
            name (str): Name of the expansion set
            description (str, Optional): Freeform description field

        Returns:
            int: Expansion set ID
        """

        create_expansion_set_query = """
        mutation CreateExpansionSet(
            $expansion_ids: [Int!]!,
            $mission_model_id: Int!,
            $parcel_id: Int!,
            $name: String!,
            $description: String!
        ) {
            createExpansionSet(
                expansionIds: $expansion_ids, 
                missionModelId: $mission_model_id, 
                parcelId: $parcel_id, 
                name: $name, 
                description: $description
            ) {
                id
            }
        }
        """
        data = self.aerie_host.post_to_graphql(
            create_expansion_set_query,
            parcel_id=parcel_id,
            mission_model_id=model_id,
            expansion_ids=expansion_ids,
            name=name,
            description="" if description is None else description
        )
        return data["id"]

    def list_expansion_sets(self) -> List[ExpansionSet]:
        list_sets_query = """
        query ListExpansionSets {
            expansion_set {
                id
                created_at
                updated_at
                owner
                updated_by
                parcel_id
                expansion_rules {
                    id
                }
                description
                name
                mission_model_id
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(list_sets_query)
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
        self.aerie_host.post_to_graphql(
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
        data = self.aerie_host.post_to_graphql(
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
                parcel_id
                name
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(list_rules_query)
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
        data = self.aerie_host.post_to_graphql(
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
        data = self.aerie_host.post_to_graphql(
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
        resp = self.aerie_host.post_to_graphql(
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
        resp = self.aerie_host.post_to_graphql(
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
            self.aerie_host.post_to_graphql(
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
        data = self.aerie_host.post_to_graphql(
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
                seqJson
            }
        }
        """
        data = self.aerie_host.post_to_graphql(
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
        query ListSequences($simulation_dataset_id: Int!) {
            sequence(where: { simulation_dataset_id: { _eq: $simulation_dataset_id } }) {
                seq_id
            }
        }
        """
        data = self.aerie_host.post_to_graphql(
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
        self.aerie_host.post_to_graphql(
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
        data = self.aerie_host.post_to_graphql(
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
        data = self.aerie_host.post_to_graphql(
            get_types_query, model_id=model_id)
        activity_types = [o["name"] for o in data]
        return activity_types

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
        query GetCommandDictionaryMetadata($command_dictionary_id: Int!) {
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

        data = self.aerie_host.post_to_graphql(
            get_command_dictionary_metadata_query,
            command_dictionary_id=command_dictionary_id,
        )[0]

        command_dictionary_mission = data["mission"]
        command_dictionary_version = data["version"]

        data = self.aerie_host.post_to_graphql(
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

    def get_scheduling_goals_by_specification(self, spec_id):
        list_all_goals_by_spec_query = """
        query ($spec: Int!){
            scheduling_specification_goals(where: {
                specification_id:{_eq:$spec}
            }){
                goal_metadata {
                    id
                    name
                    description
                    public
                    owner
                    updated_by
                    created_at
                    updated_at
                }
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(list_all_goals_by_spec_query, spec=spec_id)

        return resp

    def create_dictionary(self, dictionary: str) -> int:
        """Upload an AMPCS command, channel, or parameter dictionary to an Aerie instance

        Args:
            dictionary (str): Contents from XML dictionary file (newlne-delimited)
            type (Union[str, DictionaryType]): Type of dictionary to use

        Returns:
            int: Dictionary ID
        """

        query = """
        mutation CreateDictionary($dictionary: String!) {
            createDictionary: uploadDictionary(dictionary: $dictionary) {
                command
                channel
                parameter
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(
            query,
            dictionary=dictionary
        )
        return next(iter(resp.values()))["id"]


    def list_dictionaries(self) -> Dict[DictionaryType, List[DictionaryMetadata]]:
        """List all command, parameter, and channel dictionaries

        Returns:
            List[DictionaryMetadata]
        """

        command_dictionaries = self.aerie_host.post_to_graphql("""query ListDictionaries {
            command_dictionary {
                id
                version
                updated_at
                created_at
                mission
            }
        }
        """)
        channel_dictionaries = self.aerie_host.post_to_graphql("""query ListDictionaries {
            channel_dictionary {
                id
                version
                updated_at
                created_at
                mission
            }
        }
        """)
        parameter_dictionaries = self.aerie_host.post_to_graphql("""query ListDictionaries {
            parameter_dictionary {
                id
                version
                updated_at
                created_at
                mission
            }
        }
        """)
        return {
            DictionaryType.COMMAND: [DictionaryMetadata.from_dict(i) for i in command_dictionaries],
            DictionaryType.CHANNEL: [DictionaryMetadata.from_dict(i) for i in channel_dictionaries],
            DictionaryType.PARAMETER: [DictionaryMetadata.from_dict(
                i) for i in parameter_dictionaries]
        }

    def delete_dictionary(self, id: int, dictionary_type: Union[str, DictionaryType]) -> None:
        """Delete AMPCS dictionary

        Args:
            id (int): _description_
            dictionary_type (Union[str, DictionaryType]): _description_
        """
        
        if not isinstance(dictionary_type, DictionaryType):
            dictionary_type = DictionaryType(dictionary_type)

        queries = {
                DictionaryType.COMMAND: """
            mutation DeleteCommandDictionary($id: Int!) {
                delete_command_dictionary_by_pk(id: $id) {
                    id
                }
            }
            """,
            DictionaryType.CHANNEL: """
            mutation DeleteChannelDictionary($id: Int!) {
                delete_channel_dictionary_by_pk(id: $id) {
                    id
                }
            }
            """,
                DictionaryType.PARAMETER: """
            mutation DeleteParameterDictionary($id: Int!) {
                delete_parameter_dictionary_by_pk(id: $id) {
                    id
                }
            }
            """
        }
        self.aerie_host.post_to_graphql(queries[dictionary_type], id=id)

    def create_sequence_adaptation(self, adaptation: str) -> int:
        """Upload Phoenix Editor sequence adaptation

        Args:
            adaptation (str): String contents of adaptation JS file

        Returns:
            int: ID of sequence adaptation
        """        
        
        query = """
        mutation CreateSequenceAdaptation($adaptation: sequence_adaptation_insert_input!) {
            createSequenceAdaptation: insert_sequence_adaptation_one(object: $adaptation) {
                id
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(query, adaptation={"adaptation": adaptation})

        return resp["id"]

    def list_sequence_adaptations(self) -> List[SequenceAdaptationMetadata]:
        """List Phoenix Editor sequence adaptations

        Returns:
            List[SequenceAdaptationMetadata]: Metadata for all existing sequence adaptations
        """
        
        query = """
        query ListSequenceAdaptations {
            sequence_adaptation {
                id
                updated_at
                created_at
                owner
                updated_by
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(query)
        return [SequenceAdaptationMetadata.from_dict(i) for i in resp]

    def update_sequence_adaptation(self, adaptation: str, id: int) -> None:
        """Update Phoenix Editor sequence adaptation

        Args:
            adaptation (str): String contents of adaptation JS file
            id (int): ID of sequence adaptation to update
        """
        
        query = """
        mutation UpdateSequenceAdaptation($adaptation: String!, $id: Int!) {
            update_sequence_adaptation_by_pk(pk_columns: {id: $id}, _set: {adaptation: $adaptation}) {
                id
            }
        }
        """
        self.aerie_host.post_to_graphql(query, adaptation={"adaptation": adaptation}, id=id)

    def delete_sequence_adaptation(self, id: int) -> None:
        """Delete Phoenix Editor sequence adaptation

        Args:
            id (int): ID of adaptation to delete
        """

        query = """
        mutation DeleteSequenceAdaptation($id: Int!) {
            delete_sequence_adaptation_by_pk(id: $id) {
                id
            }
        }
        """
        self.aerie_host.post_to_graphql(query, id=id)

    def create_parcel(self, parcel: Parcel) -> int:
        """Create sequencing parcel

        Inserts parcel entry with command dictionary, channel dictionary, and sequencing adaptation IDs.
        Links parameter dictionaries to that parcel.

        Args:
            parcel (Parcel): Contents of parcel to create

        Returns:
            int: ID of created parcel
        """

        resp = self.aerie_host.post_to_graphql(
            """
            mutation CreateParcel($parcel: parcel_insert_input!) {
                createParcel: insert_parcel_one(object: $parcel) {
                    id
                }
            }
            """, parcel=parcel.to_api_create().to_dict()
        )
        parcel_id = resp["id"]

        parameter_dictionaries = [
            {
                "parameter_dictionary_id": p,
                "parcel_id": parcel_id
            } for p in parcel.parameter_dictionary_ids
        ]
        self.aerie_host.post_to_graphql(
            """
            mutation LinkParameterDictionariesToParcel($parameter_dictionaries: [parcel_to_parameter_dictionary_insert_input!]!) {
                insert_parcel_to_parameter_dictionary(objects: $parameter_dictionaries) {
                    affected_rows
                }
            }
            """,
            parameter_dictionaries=parameter_dictionaries
        )
        return parcel_id

    def list_parcels(self) -> List[Parcel]:
        """List sequencing parcels

        Returns:
            List[Parcel]: 
        """

        resp = self.aerie_host.post_to_graphql(
            """
            query GetParcels {
                parcel {
                    channel_dictionary_id
                    command_dictionary_id
                    id
                    name
                    sequence_adaptation_id
                    parameter_dictionaries {
                        parameter_dictionary_id
                    }
                }
            }
            """
        )
        return [Parcel.from_api_read(ApiParcelRead.from_dict(p)) for p in resp]

    def delete_parcel(self, id: int) -> None:
        """Delete sequencing parcel

        Args:
            id (int): ID of parcel to delete
        """        

        self.aerie_host.post_to_graphql(
            """
            mutation DeleteParcel($id: Int!) {
                delete_parcel_by_pk(id: $id) {
                    id
                }
            }
            """,
            id=id
        )

    def upload_scheduling_goals(self, upload_object):
        """
        Bulk upload operation for uploading scheduling goals.
        @param upload_object should be JSON-like with a definition key and metadata containing the goal name and model id
        [
            {
                definition: str
                metadata: {
                    name: str,
                    models_using: {
                        data: {
                            model_id: int
                        }
                    }
                }
            },
            ...
        ]
        """
        
        upload_scheduling_goals_query = """
        mutation InsertGoal($input: [scheduling_goal_definition_insert_input!]!){
            insert_scheduling_goal_definition(objects: $input){
                returning {goal_id}
            }
        }"""
        
        resp = self.aerie_host.post_to_graphql(
            upload_scheduling_goals_query,
            input=upload_object
        )

        return resp["returning"]

    def get_scheduling_specification_for_plan(self, plan_id):
        get_scheduling_specification_for_plan_query = """
        query GetSpecificationForPlan($plan_id: Int!) {
            scheduling_specification(where: {plan_id: {_eq: $plan_id}}) {
                id
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(
            get_scheduling_specification_for_plan_query, 
            plan_id=plan_id
        )
        return resp[0]["id"]

    def get_goal_id_for_name(self, name):
        get_goal_id_for_name_query = """
        query GetNameForGoalId($name: String!) {
            scheduling_goal_metadata(where: {name: {_eq: $name}}) {
                id
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(
            get_goal_id_for_name_query,
            name=name
        )
        if len(resp) == 0:
            raise RuntimeError(f"No goals found with name {name}.")
        elif len(resp) > 1:
            raise RuntimeError(f"Multiple goals found with name {name}.")
        return resp[0]["id"]

    def add_goals_to_specifications(self, upload_object):
        """
        Bulk operation to add goals to specification.
        @param upload_object should be JSON-like with keys goal_id, specification_id
        [
            {
                goal_id: int,
                specification_id: int
            },
            ...
        ]
        """

        add_goal_to_specification_query = """
        mutation AddGoalToSpec($object: [scheduling_specification_goals_insert_input!]!) {
            insert_scheduling_specification_goals(objects: $object) {
                returning {
                    enabled
                    goal_id
                    priority
                    simulate_after
                    specification_id
                }
            }
        }
        """
        resp = self.aerie_host.post_to_graphql(
            add_goal_to_specification_query, 
            object = upload_object
        )

        return resp['returning']

    def delete_scheduling_goal(self, goal_id):
        return self.delete_scheduling_goals(list([goal_id]))

    def delete_scheduling_goals(self, goal_id_list):
        # We must remove the goal(s) from any specifications before deleting them
        delete_scheduling_goals_from_all_specs_query = """
        mutation DeleteSchedulingGoalsFromAllSpecs($id_list: [Int!]!) {
            delete_scheduling_model_specification_goals (where: {goal_id: {_in:$id_list}}){
                returning {goal_id}
            }
            delete_scheduling_specification_goals (where: {goal_id: {_in:$id_list}}){
                returning {goal_id}
            }
        }
        """

        resp_for_deleting_from_specs = self.aerie_host.post_to_graphql(
            delete_scheduling_goals_from_all_specs_query, 
            id_list=goal_id_list
        )

        # Note that deleting the scheduling goal metadata entry will take care of the 
        # scheduling goal definition entry too
        delete_scheduling_goals_query = """
        mutation DeleteSchedulingGoals($id_list: [Int!]!) {
            delete_scheduling_goal_metadata (where: {id: {_in:$id_list}}){
                returning {id}
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(
            delete_scheduling_goals_query, 
            id_list=goal_id_list
        )

        return resp["returning"]

    def get_plan_revision(self, planId):
        get_plan_revision_query = """
        query get_plan_revision($plan_id:Int) {
            plan(where: {id: {_eq: $plan_id}}){
                revision
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(
            get_plan_revision_query, 
            plan_id=planId
        )

        return resp[0]["revision"]

    def __expand_activity_arguments(self, plan: ActivityPlanRead, full_args: str = None) -> ActivityPlanRead:
        if full_args is None or full_args == "" or full_args.lower() == "false":
            return plan
        expand_all = full_args.lower() == "true"
        expand_types = {} if expand_all else set(full_args.split(","))
        for activity in plan.activities:
            if expand_all or activity.type in expand_types:
                query = """
                query ($args: ActivityArguments!, $act_type: String!, $model_id: Int!) {
                    getActivityEffectiveArguments(
                        activityArguments: $args,
                        activityTypeName: $act_type,
                        missionModelId: $model_id
                    )
                    {
                        arguments
                        success
                    }
                }
                """
                resp = self.aerie_host.post_to_graphql(
                    query,
                    args=activity.arguments,
                    act_type=activity.type,
                    model_id=plan.model_id,
                )
                activity.arguments = ApiEffectiveActivityArguments.from_dict(
                    resp).arguments
        return plan

    def upload_constraint(self, constraint):
        upload_constraint_query = """
        mutation CreateConstraint($constraint: constraint_definition_insert_input!) {
            createConstraint: insert_constraint_definition_one(object: $constraint) {
                constraint_id
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(upload_constraint_query, constraint=constraint)
        return resp["constraint_id"]
    

    def add_constraint_to_plan(self, constraint_id, plan_id):
        """
        Add a constraint to a plan's constraint specification.
        @param constraint_id The constraint ID to add to the given plan
        @param plan_id The plan ID to add this constraint to
        """

        add_constraint_to_specification_query = """
            mutation InsertConstraintSpec($constraint_id: Int!, $plan_id: Int!) {
                insert_constraint_specification_one(object: {constraint_id: $constraint_id, plan_id: $plan_id}) {
                    constraint_id
                }
            }

        """
        resp = self.aerie_host.post_to_graphql(
            add_constraint_to_specification_query, 
            constraint_id = constraint_id,
            plan_id = plan_id
        )

        return resp['constraint_id']

    def delete_constraint(self, id):

        # We must remove the constraint from any specifications before deleting it
        delete_constraint_from_all_specs_query = """
        mutation DeleteConstraintsFromAllSpecs($id: Int!) {
            delete_constraint_specification(where: {constraint_id: {_eq: $id}}) {
                returning {
                    constraint_id
                    plan_id
                }
            }
        }
        """

        resp_for_deleting_from_specs = self.aerie_host.post_to_graphql(
            delete_constraint_from_all_specs_query, 
            id=id
        )

        delete_constraint_query = """
        mutation DeleteConstraint($id: Int!) {
            deleteConstraint: delete_constraint_metadata_by_pk(id: $id) {
                id
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(delete_constraint_query, id=id)
        return resp["id"]
    
    def update_constraint(self, id, definition):
        old_update_constraint_query = """
        mutation UpdateConstraint($constarint_id: Int!, $constraint: constraint_definition_set_input!) {
            update_constraint_definition_by_pk(
                pk_columns: { constarint_id: $constraint_id }, _set: $constraint
            ) {
                constarint_id
                definition
                author
                created_at
            }
        }
        """

        update_constraint_query = """
        mutation UpdateConstraint($constarint_id: Int!, $definition: String!) {
            update_constraint_definition_many(
                updates: {_set: {definition: $definition}, where: {constraint_id: {_eq: $constarint_id}}}) {
                returning {
                    constraint_id
                }
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(update_constraint_query, constarint_id=id, definition=definition)
        return resp
    
    def get_constraint_by_id(self, id):
        get_constraint_by_id_query = """
        query get_constraint($constraint_id: Int!) {
            constraint_definition(where: {constraint_id: {_eq: $constraint_id}}) {
                author
                definition
                metadata {
                    description
                    name
                    plans_using {
                        plan_id
                    }
                    models_using {
                        model_id
                    }
                }
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(get_constraint_by_id_query, constraint_id=id)
        return resp
    
    def get_constraint_specification_for_plan(self, plan_id):
        get_constraint_specification_for_plan_query = """
        query GetConstraintSpecificationForPlan($plan_id: Int!) {
            constraint_specification(where: {plan_id: {_eq: $plan_id}}) {
                constraint_id
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(
            get_constraint_specification_for_plan_query, 
            plan_id=plan_id
        )
        return resp[0]["id"]

    def get_constraint_violations(self, plan_id):
        get_violations_query = """
        query ($plan_id: Int!) {
            constraintResponses: constraintViolations(planId: $plan_id) {
                constraintId
                constraintName
                success
                results {
                    resourceIds
                    gaps {
                        end
                        start
                    }
                    violations {
                        activityInstanceIds
                        windows {
                            end
                            start
                        }
                    }
                }
                errors {
                    message
                    stack
                    location {
                        column
                        line
                    }
                }
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(get_violations_query, plan_id=plan_id)
        return resp

    def get_resource_types(self, model_id: int) -> List[ResourceType]:
        """Get resource types (value schema)

        Get the type information for each resource in a mission model.

        The schema format is described in the Aerie documentation [here](https://nasa-ammos.github.io/aerie-docs/mission-modeling/advanced-value-schemas/#value-schemas-in-json).

        Args:
            model_id (int): Mission model for resources

        Returns:
            List[ResourceType]
        """

        get_resource_types_query = """
        query ResourceTypes($missionModelId: Int!) {
            resourceTypes: resource_type(where: {model_id: {_eq: $missionModelId}}) {
                name
                schema
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(
            get_resource_types_query, missionModelId=model_id
        )
        return [ResourceType.from_dict(r) for r in resp]

    def get_directive_metadata(self) -> list:
        """Get metatdata

        Returns:
            list: a list of the metadata keys and schemas
        """
        get_metadata_query = """
        query GetMetadata {
            activity_directive_metadata_schema {
                key
                schema
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(get_metadata_query)
        return resp

    def add_directive_metadata_schemas(self, schemas: list) -> list:
        """Add metadata schemas

        The schema format should follow the documentation [here](https://nasa-ammos.github.io/aerie-docs/planning/activity-directive-metadata/).

        Args:
            schemas (list): a list of the schemas to add

        Returns:
            list: a list of the metadata keys and schemas that were added
        """
        add_schemas_query = """
        mutation CreateActivityDirectiveMetadataSchemas($schemas: [activity_directive_metadata_schema_insert_input!]!) {
            insert_activity_directive_metadata_schema(objects: $schemas) {
                returning {
                    key
                    schema
                }
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(
            add_schemas_query,
            schemas=schemas
        )
        return resp
        
    def delete_directive_metadata_schema(self, key) -> list:
        """Delete metadata schemas

        Returns:
            list: a list of the metadata keys that were deleted
        """
        delete_schema_query = """
        mutation DeleteDirectiveMetadataSchema($key: String!) {
            delete_activity_directive_metadata_schema_by_pk(key: $key) {
                key
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(
            delete_schema_query,
            key=key
        )
        return resp["key"]

    def list_plan_collaborators(self, plan_id: int) -> list:
        """List plan collaborators

        Args:
            plan_id (int): ID of Plan to list collaborators of

        Returns:
            list[str]: List of collaborator usernames
        """
        query = """
        query GetPlanCollaborators($plan_id: Int!) {
            plan_by_pk(id: $plan_id) {
                collaborators {
                    collaborator
                }
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(
            query,
            plan_id=plan_id
        )
        return [c["collaborator"] for c in resp["collaborators"]]

    def add_plan_collaborator(self, plan_id: int, user: str):
        """Add a plan collaborator

        Args:
            plan_id (int): ID of plan to add collaborator to
            user (str): Username of collaborator
        """
        query = """
        mutation addPlanCollaborator($plan_id: Int!, $collaborator: String!) {
            insert_plan_collaborators_one(object: {plan_id: $plan_id, collaborator: $collaborator}) {
                collaborator
            }
        }
        """

        self.aerie_host.post_to_graphql(
            query,
            plan_id=plan_id,
            collaborator=user
        )

    def delete_plan_collaborator(self, plan_id: int, user: str):
        """Delete a plan collaborator

        Args:
            plan_id (int): ID of the plan to delete a collaborator from
            user (str): Username of the collaborator
        """

        query = """
        mutation DeletePlanCollaborator($plan_id: Int!, $collaborator: String!) {
            delete_plan_collaborators_by_pk(collaborator: $collaborator, plan_id: $plan_id) {
                collaborator
                plan_id
            }
        }
        """

        resp = self.aerie_host.post_to_graphql(
            query,
            plan_id=plan_id,
            collaborator=user
        )

        if resp is None:
            raise RuntimeError(f"Failed to delete plan collaborator")
