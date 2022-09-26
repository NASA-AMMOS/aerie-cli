import sys
import time
from dataclasses import dataclass
from pathlib import Path

import arrow
import requests
import typer

from .schemas.api import ApiActivityPlanRead
from .schemas.api import ApiMissionModelCreate
from .schemas.api import ApiMissionModelRead
from .schemas.api import ApiResourceSampleResults
from .schemas.client import ActivityCreate
from .schemas.client import ActivityPlanCreate
from .schemas.client import ActivityPlanRead
from .schemas.client import SimulationResults

# from .schemas.api import ApiSimulationResults


@dataclass
class Auth:
    username: str
    password: str


class AerieClient:
    server_url: str
    sso_token: str

    def __init__(self, server_url: str, sso=""):
        self.server_url = server_url
        self.sso_token = sso

    @classmethod
    def from_local(cls, server_url: str):
        return cls(server_url=server_url)

    @classmethod
    def from_sso(cls, server_url: str, sso: str):
        return cls(server_url=server_url, sso=sso)

    @classmethod
    def from_userpass(cls, server_url: str, username: str, password: str):
        auth = Auth(username=username, password=password)
        sso = cls.cls_get_sso_token(server_url, auth)
        return cls(server_url=server_url, sso=sso)

    @classmethod
    def cls_graphql_path(cls, server_url: str) -> str:
        return server_url + ":8080/v1/graphql"

    @classmethod
    def cls_gateway_path(cls, server_url: str) -> str:
        return server_url + ":9000"

    @classmethod
    def cls_files_api_path(cls, server_url: str) -> str:
        return cls.cls_gateway_path(server_url) + "/file"

    @classmethod
    def cls_login_api_path(cls, server_url: str) -> str:
        return cls.cls_gateway_path(server_url) + "/auth/login"

    @classmethod
    def cls_ui_path(cls, server_url: str) -> str:
        return server_url

    @classmethod
    def cls_ui_models_path(cls, server_url: str) -> str:
        return cls.cls_ui_path(server_url) + "/models"

    @classmethod
    def cls_ui_plans_path(cls, server_url: str) -> str:
        return cls.cls_ui_path(server_url) + "/plans"

    @classmethod
    def cls_get_sso_token(cls, server_url: str, auth: Auth) -> str:
        resp = requests.post(
            url=cls.cls_login_api_path(server_url),
            json={"username": auth.username, "password": auth.password},
        )
        if not resp.json()["success"]:
            sys.exit("Authentication failed. Perhaps you provided bad credentials...")

        return resp.json()["ssoToken"]

    def graphql_path(self) -> str:
        return self.cls_graphql_path(self.server_url)

    def gateway_path(self) -> str:
        return self.cls_gateway_path(self.server_url)

    def files_api_path(self) -> str:
        return self.cls_files_api_path(self.server_url)

    def login_api_path(self) -> str:
        return self.cls_login_api_path(self.server_url)

    def ui_path(self) -> str:
        return self.cls_ui_path(self.server_url)

    def ui_models_path(self) -> str:
        return self.cls_ui_models_path(self.server_url)

    def ui_plans_path(self) -> str:
        return self.cls_ui_plans_path(self.server_url)
        
    def get_activity_plan_by_id(self, plan_id: int) -> ActivityPlanRead:
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
                activities {
                    id
                    plan_id
                    type
                    start_offset
                    arguments
                }
            }
        }
        """
        resp = self.__gql_query(query, plan_id=plan_id)
        api_plan = ApiActivityPlanRead.from_dict(resp)
        return ActivityPlanRead.from_api_read(api_plan)

    def get_all_activity_plans(self) -> list[ActivityPlanRead]:
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
                activities {
                    id
                    plan_id
                    type
                    start_offset
                    arguments
                }
            }
        }
        """
        resp = self.__gql_query(get_all_plans_query)
        activity_plans = [
            ActivityPlanRead.from_api_read(ApiActivityPlanRead.from_dict(plan))
            for plan in resp
        ]

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
        plan_resp = self.__gql_query(
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
        _ = self.__gql_query(
            create_simulation_mutation, simulation={"arguments": {}, "plan_id": plan_id}
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
        api_activity_create = activity_to_create.to_api_create(plan_id, plan_start_time)
        insert_activity_mutation = """
        mutation CreateActivity($activity: activity_insert_input!) {
            createActivity: insert_activity_one(object: $activity) {
                id
            }
        }
        """
        resp = self.__gql_query(
            insert_activity_mutation,
            activity=api_activity_create.to_dict(),
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
            return self.__gql_query(simulate_query, plan_id=plan_id)

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

        resource_sample_query = """
        query ResourceSamples($plan_id: Int!) {
            resourceSamples(planId: $plan_id){
                resourceSamples
            }
        }
        """
        resp = self.__gql_query(resource_sample_query, plan_id=plan_id)

        api_resource_timeline = ApiResourceSampleResults.from_dict(resp)
        return api_resource_timeline
        

        
    def get_simulation_results(self, plan_id: int, sim_dataset_id: int) -> str:

        sim_result_query = """
          query Simulation($plan_id: Int!, $sim_dataset_id: Int!) {
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
            resourceSamples(planId: $plan_id) {
              resourceSamples
            }
            constraintViolations(planId: $plan_id) {
              constraintViolations
            }
            plan_by_pk(id: $plan_id) {
              name
              start_time
            }
          }
        """
        resp = self.__gql_query(sim_result_query, plan_id=plan_id, sim_dataset_id=sim_dataset_id)
        return resp
        
    def get_simulation_results_by_id(self, sim_dataset_id: int) -> str:
        """Grab the simulation results by Simulation Dataset ID."""
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
        resp = self.__gql_query(sim_result_query, sim_dataset_id=sim_dataset_id)
        return resp

    def delete_plan(self, plan_id: int) -> str:

        delete_plan_mutation = """
        mutation deletePlan($plan_id: Int!) {
            delete_plan_by_pk(id: $plan_id){
                name
            }
        }
        """

        resp = self.__gql_query(delete_plan_mutation, plan_id=plan_id)

        return resp["name"]

    def upload_mission_model(
        self, mission_model_path: str, project_name: str, mission: str, version: str
    ) -> int:

        file_api_url = self.files_api_path()

        # Create unique jar identifier for server side
        upload_timestamp = arrow.utcnow().isoformat()
        server_side_jar_name = (
            Path(mission_model_path).stem + "--" + upload_timestamp + ".jar"
        )

        with open(mission_model_path, "rb") as jar_file:
            resp = requests.post(
                file_api_url,
                files={"file": (server_side_jar_name, jar_file)},
                headers={"x-auth-sso-token": self.sso_token},
            )

        jar_id = resp.json()["id"]

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

        resp = self.__gql_query(
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

        resp = self.__gql_query(
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

        resp = self.__gql_query(delete_model_mutation, model_id=model_id)

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

        resp = self.__gql_query(get_mission_model_query)
        api_mission_models = [ApiMissionModelRead.from_dict(model) for model in resp]

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

        resp = self.__gql_query(update_config_arg_query, sim_id=sim_id, args=args)

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

        resp = self.__gql_query(update_config_arg_query, sim_id=sim_id, args=final_args)

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

        resp = self.__gql_query(get_config_query, sim_id=sim_id)

        return resp["arguments"]

    def __gql_query(self, query: str, **kwargs):
        resp = requests.post(
            self.graphql_path(),
            json={"query": query, "variables": kwargs},
            headers=self.__auth_header(),
        )

        try:
            if resp.ok:
                resp_json = resp.json()["data"]
                data = next(iter(resp_json.values()))

            if data is None:
                raise RuntimeError

            if not resp.ok or (
                resp.ok
                and isinstance(data, dict)
                and "success" in data
                and not data["success"]
            ):
                raise RuntimeError

        except Exception:
            print("ERROR: The API call was unsuccessful!\n")

            if "password" not in kwargs:
                print(f"Variables: {kwargs}\n")

            sys.exit(f"Query: {query}\n Response: {resp.text}")

        return data

    def __auth_header(self) -> dict[str, str]:
        return {"x-auth-sso-token": self.sso_token}


def check_response_status(
    response: requests.Response, status_code: int, error_message: str = "Request failed"
):
    if response.status_code != status_code:
        raise RuntimeError(f"{error_message}\nServer response: {response.json()}")


def auth_helper(sso: str, username: str, password: str, server_url: str):
    """Aerie client authorization; \
    defaults to using sso token if sso & user/pass are provided."""
    
    LOCAL_URLS = ["local", "localhost", "http://localhost", "http://127.0.0.1"]
    if (server_url in LOCAL_URLS):
        client = AerieClient.from_local(server_url="http://localhost")
    # Assuming user has not provided valid credentials during command call
    elif (sso == "") and (username == "") and (password == ""):
        method = int(typer.prompt("Enter (1) for SSO Login or (2) for JPL Login"))
        if method == 1:
            sso = typer.prompt("SSO Token")
            client = AerieClient.from_sso(server_url=server_url, sso=sso)
        elif method == 2:
            user = typer.prompt("JPL Username")
            pwd = typer.prompt("JPL Password", hide_input=True)
            client = AerieClient.from_userpass(
                server_url=server_url, username=user, password=pwd
            )
        else:
            print(
                """
                Please select one of the following login options:
                1) SSO Token
                2) JPL Username+Password
                """
            )
            exit(1)
    elif sso != "":
        client = AerieClient.from_sso(server_url=server_url, sso=sso)
    elif (username != "") and (password != ""):
        client = AerieClient.from_userpass(
            server_url=server_url, username=username, password=password
        )
    else:
        print(
            "Please provide either --sso flag or both --username and --password flags"
        )
        exit(1)
    return client
