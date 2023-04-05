from dataclasses import dataclass
from dataclasses import field
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import arrow
from arrow import Arrow
from dataclasses_json import config
from dataclasses_json import dataclass_json

from ..utils.serialization import postgres_interval_to_timedelta
from .api import ApiActivityCreate
from .api import ApiActivityPlanCreate
from .api import ApiActivityPlanRead
from .api import ApiActivityRead
from .api import ApiAsSimulatedActivity
from .api import ApiResourceSampleResults
from .api import ApiSimulatedResourceSample
from .api import ApiSimulationResults


@dataclass_json
@dataclass
class ActivityCreate:
    type: str
    start_time: Arrow = field(
        metadata=config(decoder=arrow.get, encoder=Arrow.isoformat)
    )
    parameters: dict[str, Any]
    name: str
    tags: list[str]
    metadata: dict[str, str]

    def to_api_create(self, plan_id: int, plan_start_time: Arrow):
        return ApiActivityCreate(
            type=self.type,
            plan_id=plan_id,
            start_offset=self.start_time - plan_start_time,
            arguments=self.parameters,
            name=self.name,
            tags=self.to_api_array(self.tags),
            metadata=self.metadata
        )

    def to_api_array(self, entries: list[str]):
        """
        Format an array of strings as a Postgres style array.
        """
        vals = ",".join(entries)
        return f"{{{vals}}}"  # Wrap items in {}


@dataclass_json
@dataclass
class ActivityRead(ActivityCreate):
    id: int

    @classmethod
    def from_api_read(
        cls, api_activity_read: ApiActivityRead, plan_start_time: Arrow
    ) -> "ActivityRead":
        return ActivityRead(
            id=api_activity_read.id,
            name=api_activity_read.name,
            type=api_activity_read.type,
            start_time=plan_start_time + api_activity_read.start_offset,
            parameters=api_activity_read.arguments,
            tags=api_activity_read.tags,
            metadata=api_activity_read.metadata,
        )


@dataclass_json
@dataclass
class EmptyActivityPlan:
    name: str
    start_time: Arrow = field(
        metadata=config(decoder=arrow.get, encoder=Arrow.isoformat)
    )
    end_time: Arrow = field(metadata=config(
        decoder=arrow.get, encoder=Arrow.isoformat))

    def duration(self) -> timedelta:
        return self.end_time - self.start_time


@dataclass_json
@dataclass
class ActivityPlanCreate(EmptyActivityPlan):
    activities: list[ActivityCreate]

    @classmethod
    def from_plan_read(cls, plan_read: "ActivityPlanRead") -> "ActivityPlanCreate":
        return ActivityPlanCreate(
            name=plan_read.name,
            start_time=plan_read.start_time,
            end_time=plan_read.end_time,
            activities=plan_read.activities,
        )

    def to_api_create(self, model_id: int) -> "ApiActivityPlanCreate":
        return ApiActivityPlanCreate(
            model_id=model_id,
            name=self.name,
            start_time=self.start_time,
            duration=self.end_time - self.start_time,
        )


@dataclass_json
@dataclass
class ActivityPlanRead(EmptyActivityPlan):
    id: int
    model_id: int
    sim_id: int
    activities: Optional[List[ActivityRead]] = None

    @classmethod
    def from_api_read(cls, api_plan_read: ApiActivityPlanRead) -> "ActivityPlanRead":
        plan_start = arrow.get(api_plan_read.start_time)
        return ActivityPlanRead(
            id=api_plan_read.id,
            name=api_plan_read.name,
            model_id=api_plan_read.model_id,
            sim_id=api_plan_read.simulations[0]["id"],
            start_time=plan_start,
            end_time=plan_start + api_plan_read.duration,
            activities= None if api_plan_read.activity_directives is None else [
                ActivityRead.from_api_read(api_activity, plan_start)
                for api_activity in api_plan_read.activity_directives
            ],
        )


@dataclass_json
@dataclass
class AsSimulatedActivity:
    type: str
    id: str
    parent_id: Optional[str]
    start_time: Arrow = field(
        metadata=config(decoder=arrow.get, encoder=Arrow.isoformat)
    )
    children: list[str]
    duration: timedelta = field(
        metadata=config(decoder=postgres_interval_to_timedelta,
                        encoder=timedelta.__str__)
    )
    parameters: dict[str, Any]

    @classmethod
    def from_api_as_simulated_activity(
        cls, api_as_simulated_activity: ApiAsSimulatedActivity, id: str
    ):
        return AsSimulatedActivity(
            type=api_as_simulated_activity.type,
            id=id,
            parent_id=api_as_simulated_activity.parent_id,
            start_time=api_as_simulated_activity.start_timestamp,
            children=api_as_simulated_activity.children,
            duration=api_as_simulated_activity.duration,
            parameters=api_as_simulated_activity.arguments,
        )


@dataclass_json
@dataclass
class SimulatedResourceSample:
    t: Arrow = field(metadata=config(
        decoder=arrow.get, encoder=Arrow.isoformat))
    v: Any


@dataclass_json
@dataclass
class SimulatedResourceTimeline:
    name: str
    values: list[SimulatedResourceSample]

    @classmethod
    def from_api_sim_res_timeline(
        cls,
        name: str,
        api_sim_res_timeline: list[ApiSimulatedResourceSample],
        profile_start_time: arrow,
    ):
        return SimulatedResourceTimeline(
            name=name,
            values=[
                SimulatedResourceSample(
                    t=profile_start_time + sample.x, v=sample.y)
                for sample in api_sim_res_timeline
            ],
        )


@dataclass_json
@dataclass
class SimulationResults:
    start_time: Arrow = field(
        metadata=config(decoder=arrow.get, encoder=Arrow.isoformat)
    )
    activities: list[AsSimulatedActivity]
    resources: list[SimulatedResourceTimeline]

    @classmethod
    def from_api_results(
        cls,
        api_sim_results: ApiSimulationResults,
        api_resource_timeline: ApiResourceSampleResults,
    ):
        plan_start = api_sim_results.start
        return SimulationResults(
            start_time=plan_start,
            activities=[
                AsSimulatedActivity.from_api_as_simulated_activity(act, id)
                for id, act in api_sim_results.activities.items()
            ],
            resources=[
                SimulatedResourceTimeline.from_api_sim_res_timeline(
                    name, api_timeline, plan_start
                )
                for name, api_timeline in api_resource_timeline.resourceSamples.items()
            ],
        )


@dataclass_json
@dataclass
class ActivityInstanceCommand:
    activity_instance_id: int
    commands: List[Dict]
    errors: List[Dict]


@dataclass_json
@dataclass
class ExpansionRun:
    id: int
    expansion_set_id: int
    simulation_dataset_id: int
    created_at: Arrow = field(metadata=config(
        decoder=arrow.get, encoder=Arrow.isoformat))
    activity_instance_commands: Optional[List[ActivityInstanceCommand]] = None


@dataclass_json
@dataclass
class ExpansionSet:
    id: int
    created_at: Arrow = field(metadata=config(
        decoder=arrow.get, encoder=Arrow.isoformat))
    command_dictionary_id: int = field(
        metadata=config(field_name="command_dict_id"))
    expansion_rules: List[int] = field(metadata=config(
        decoder=lambda x: [i['id'] for i in x], encoder=lambda x: [{'id': i} for i in x]))


@dataclass_json
@dataclass
class CommandDictionaryInfo:
    id: int
    mission: str
    version: str
    created_at: Arrow = field(metadata=config(
        decoder=arrow.get, encoder=Arrow.isoformat))


@dataclass_json
@dataclass
class ExpansionRule:
    id: int
    activity_type: str
    authoring_mission_model_id: int
    authoring_command_dict_id: int
    expansion_logic: Optional[str] = None


@dataclass_json
@dataclass
class ResourceType:
    name: str
    schema: Dict
