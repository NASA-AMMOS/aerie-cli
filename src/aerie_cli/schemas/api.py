import json
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

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
class ApiMissionModel:
    name: str
    id: int
    verison: str

    @classmethod
    def multi_from_dict(cls, obj: dict) -> list["ApiMissionModel"]:
        return [ApiMissionModel(id=model["id"], name=model["name"]) for model in obj]
