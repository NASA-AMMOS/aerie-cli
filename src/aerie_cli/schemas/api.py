import json
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from typing import Optional

import arrow
from arrow import Arrow

from ..utils.serialization import hms_string_to_timedelta


@dataclass
class ApiActivityCreate:
    type: str
    plan_id: int
    start_offset: timedelta
    arguments: dict[str, Any]


@dataclass
class ApiActivityRead(ApiActivityCreate):
    id: int

    @classmethod
    def from_json(cls, json_str: str) -> "ApiActivityRead":
        return ApiActivityRead.from_dict(json.loads(json_str))

    @classmethod
    def from_dict(cls, obj: dict) -> "ApiActivityRead":
        return ApiActivityRead(
            type=obj["type"],
            plan_id=obj["plan_id"],
            start_offset=hms_string_to_timedelta(obj["start_offset"]),
            arguments=obj["arguments"],
            id=obj["id"],
        )


@dataclass
class ApiActivityPlanCreate:
    model_id: int
    name: str
    start_time: Arrow
    duration: timedelta


@dataclass
class ApiActivityPlanRead(ApiActivityPlanCreate):
    id: int
    activities: list[ApiActivityRead]

    @classmethod
    def from_json(cls, json_str: str) -> "ApiActivityPlanRead":
        return ApiActivityPlanRead.from_dict(json.loads(json_str))

    @classmethod
    def from_dict(cls, obj: dict) -> "ApiActivityPlanRead":
        return ApiActivityPlanRead(
            id=obj["id"],
            model_id=obj["model_id"],
            name=obj["name"],
            start_time=arrow.get(obj["start_time"]),
            duration=hms_string_to_timedelta(obj["duration"]),
            activities=[
                ApiActivityRead.from_dict(activity_dict)
                for activity_dict in obj["activities"]
            ],
        )


@dataclass
class ApiAsSimulatedActivity:
    type: str
    parent: Optional[str]
    start_timestamp: Arrow
    children: list[str]
    duration: int  # microseconds
    parameters: dict[str, Any]

    @classmethod
    def from_json(cls, json_str: str) -> "ApiAsSimulatedActivity":
        return ApiAsSimulatedActivity.from_dict(json.loads(json_str))

    @classmethod
    def from_dict(cls, obj: dict) -> "ApiAsSimulatedActivity":
        print(obj)
        return ApiAsSimulatedActivity(
            type=obj["type"],
            parent=obj["parent"],
            startTimestamp=arrow.get(obj["startTimestamp"]),
            children=obj["children"],
            duration=obj["duration"],
            parameters=obj["parameters"],
        )


@dataclass
class ApiSimulatedResourceSample:
    x: int  # microseconds since profile start
    y: Any


@dataclass
class ApiSimulationResults:
    start: Arrow
    activities: dict[str, ApiAsSimulatedActivity]
    # TODO: implement constraints
    constraints: Any
    resources: dict[str, list[ApiSimulatedResourceSample]]
    # TODO: implement events
    events: Any

    @classmethod
    def from_json(cls, json_str: str) -> "ApiSimulationResults":
        return ApiSimulationResults.from_dict(json.loads(json_str))

    @classmethod
    def from_dict(cls, obj: dict) -> "ApiSimulationResults":
        return ApiSimulationResults(
            start=arrow.get(obj["start"]),
            activities={
                id: ApiAsSimulatedActivity.from_dict(act)
                for id, act in obj["activities"].items()
            },
            constraints=obj["constraints"],
            resources={
                name: [
                    ApiSimulatedResourceSample(x=sample["x"], y=sample["y"])
                    for sample in samples
                ]
                for name, samples in obj["resources"].items()
            },
            events=obj["events"],
        )
