import sys
import time
from dataclasses import dataclass
from pathlib import Path

import arrow
import requests

from .schemas.api import ApiActivityPlanRead
from .schemas.api import ApiMissionModelCreate
from .schemas.api import ApiMissionModelRead
from .schemas.api import ApiSimulationResults
from .schemas.client import ActivityCreate
from .schemas.client import ActivityPlanCreate
from .schemas.client import ActivityPlanRead
from .schemas.client import SimulationResults


@dataclass
class Auth:
    username: str
    password: str


class AerieClient:
    server_url: str
    sso_token: str

    def __init__(self, server_url: str, **kwargs):
        auth = kwargs["auth"]
        if type(auth) != str:
            self.server_url = server_url
            self.sso_token = self.get_sso_token(auth)
        else:
            self.server_url = server_url
            self.sso_token = auth

    def graphql_path(self) -> str:
        return self.server_url + ":8080/v1/graphql"

    def gateway_path(self) -> str:
        return self.server_url + ":9000"

    def files_api_path(self) -> str:
        return self.gateway_path() + "/file"

    def login_api_path(self) -> str:
        return self.gateway_path() + "/auth/login"

    def ui_path(self) -> str:
        return self.server_url

    def ui_models_path(self) -> str:
        return self.ui_path() + "/models"

    def get_sso_token(self, auth: Auth) -> str:
        resp = requests.post(
            url=self.login_api_path(),
            json={"username": auth.username, "password": auth.password},
        )
        if not resp.json()["success"]:
            sys.exit("Authentication failed. Perhaps you provided bad credentials...")

        return resp.json()["ssoToken"]

    def get_activity_plan_by_id(self, plan_id: int) -> ActivityPlanRead:
        query = """
        query get_plans ($plan_id: Int!) {
            plan_by_pk(id: $plan_id) {
                id
                model_id
                name
                start_time
                duration
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

    def simulate_plan(self, plan_id: int, poll_period: int = 5) -> SimulationResults:

        simulate_query = """
        query Simulate($plan_id: Int!) {
            simulate(planId: $plan_id) {
                status
                reason
                results
            }
        }
        """

        def exec_sim_query():
            # Note: Aerie API schema says that the plan ID should be an int,
            # but that fails; it requires a str
            return self.__gql_query(simulate_query, plan_id=str(plan_id))

        resp = exec_sim_query()

        while resp["status"] == "incomplete":
            time.sleep(poll_period)
            resp = exec_sim_query()

        if resp["status"] == "failed":
            sys.exit(f"Simulation failed. Response:\n{resp}")

        api_sim_results = ApiSimulationResults.from_dict(resp["results"])
        return SimulationResults.from_api_sim_results(api_sim_results)

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
