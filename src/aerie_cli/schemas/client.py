import json
from dataclasses import asdict
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import arrow
from arrow import Arrow

from ..utils.serialization import CustomJsonEncoder
from .api import ApiActivityCreate
from .api import ApiActivityPlanCreate
from .api import ApiActivityPlanRead
from .api import ApiActivityRead


@dataclass
class ActivityCreate:
    type: str
    start_time: Arrow
    parameters: dict[str, Any]

    @classmethod
    def from_dict(cls, obj: dict) -> "ActivityCreate":
        return ActivityCreate(
            type=obj["type"],
            start_time=arrow.get(obj["start_time"]),
            parameters=obj["parameters"],
        )

    def to_api_create(self, plan_id: int, plan_start_time: Arrow):
        return ApiActivityCreate(
            type=self.type,
            plan_id=plan_id,
            start_offset=self.start_time - plan_start_time,
            arguments=self.parameters,
        )


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


@dataclass
class EmptyActivityPlan:
    name: str
    start_time: Arrow
    end_time: Arrow

    def duration(self) -> timedelta:
        return self.end_time - self.start_time


@dataclass
class ActivityPlanCreate(EmptyActivityPlan):
    activities: list[ActivityCreate]

    @classmethod
    def from_json(cls, json_str: str, time_tag: bool) -> "ActivityPlanCreate":
        return ActivityPlanCreate.from_dict(json.loads(json_str), time_tag)

    @classmethod
    def from_dict(cls, obj: dict, time_tag: bool) -> "ActivityPlanCreate":
        name = obj["name"] 
        if time_tag:
            name += arrow.utcnow().format(' YYYY-MM-DD HH:mm:ss ZZ')
        return ActivityPlanCreate(
            name=name,
            start_time=arrow.get(obj["start_time"]),
            end_time=arrow.get(obj["end_time"]),
            activities=[
                ActivityCreate.from_dict(activity_json)
                for activity_json in obj["activities"]
            ],
        )

    @classmethod
    def from_plan_read(cls, plan_read: "ActivityPlanRead", time_tag: bool) -> "ActivityPlanCreate":
        name = plan_read.name
        if time_tag:
            name += arrow.utcnow().format(' YYYY-MM-DD HH:mm:ss ZZ')
        return ActivityPlanCreate(
            name=name,
            start_time=plan_read.start_time,
            end_time=plan_read.end_time,
            activities=plan_read.activities,
        )

    def to_api_create(self, model_id: int, time_tag: bool) -> "ApiActivityPlanCreate":
        name = self.name
        if time_tag:
            name += arrow.utcnow().format(' YYYY-MM-DD HH:mm:ss ZZ')
        return ApiActivityPlanCreate(
            model_id=model_id,
            name=name,
            start_time=self.start_time,
            duration=self.end_time - self.start_time,
        )


@dataclass
class ActivityPlanRead(EmptyActivityPlan):
    id: int
    model_id: int
    activities: list[ActivityRead]

    def to_json(self) -> str:
        return json.dumps(asdict(self), cls=CustomJsonEncoder, indent=4)

    @classmethod
    def from_api_read(cls, api_plan_read: ApiActivityPlanRead) -> "ActivityPlanRead":
        return ActivityPlanRead(
            id=api_plan_read.id,
            name=api_plan_read.name,
            model_id=api_plan_read.model_id,
            start_time=api_plan_read.start_time,
            end_time=api_plan_read.start_time + api_plan_read.duration,
            activities=[
                ActivityRead.from_api_read(api_activity, api_plan_read.start_time)
                for api_activity in api_plan_read.activities
            ],
        )
