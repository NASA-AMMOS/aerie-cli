from dataclasses import dataclass
from dataclasses import field
from datetime import timedelta
from typing import Any
from typing import Optional

import arrow
from arrow import Arrow
from dataclasses_json import config
from dataclasses_json import dataclass_json

from ..utils.serialization import hms_string_to_timedelta
from .api import ApiActivityCreate
from .api import ApiActivityPlanCreate
from .api import ApiActivityPlanRead
from .api import ApiActivityRead
from .api import ApiAsSimulatedActivity
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

    def to_api_create(self, plan_id: int, plan_start_time: Arrow):
        return ApiActivityCreate(
            type=self.type,
            plan_id=plan_id,
            start_offset=self.start_time - plan_start_time,
            arguments=self.parameters,
        )


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
            type=api_activity_read.type,
            start_time=plan_start_time + api_activity_read.start_offset,
            parameters=api_activity_read.arguments,
        )


@dataclass_json
@dataclass
class EmptyActivityPlan:
    name: str
    start_time: Arrow = field(
        metadata=config(decoder=arrow.get, encoder=Arrow.isoformat)
    )
    end_time: Arrow = field(metadata=config(decoder=arrow.get, encoder=Arrow.isoformat))

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
    activities: list[ActivityRead]

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
            activities=[
                ActivityRead.from_api_read(api_activity, plan_start)
                for api_activity in api_plan_read.activities
            ],
        )


@dataclass_json
@dataclass
class AsSimulatedActivity:
    type: str
    id: str
    parent: Optional[str]
    start_time: Arrow = field(
        metadata=config(decoder=arrow.get, encoder=Arrow.isoformat)
    )
    children: list[str]
    duration: timedelta = field(
        metadata=config(decoder=hms_string_to_timedelta, encoder=timedelta.__str__)
    )
    parameters: dict[str, Any]

    @classmethod
    def from_api_as_simulated_activity(
        cls, api_as_simulated_activity: ApiAsSimulatedActivity, id: str
    ):
        return AsSimulatedActivity(
            type=api_as_simulated_activity.type,
            id=id,
            parent=api_as_simulated_activity.parent,
            start_time=api_as_simulated_activity.start_timestamp,
            children=api_as_simulated_activity.children,
            duration=api_as_simulated_activity.duration,
            parameters=api_as_simulated_activity.arguments,
        )


@dataclass_json
@dataclass
class SimulatedResourceSample:
    t: Arrow = field(metadata=config(decoder=arrow.get, encoder=Arrow.isoformat))
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
                SimulatedResourceSample(t=profile_start_time + sample.x, v=sample.y)
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
    def from_api_sim_results(cls, api_sim_results: ApiSimulationResults):
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
                for name, api_timeline in api_sim_results.resources.items()
            ],
        )
