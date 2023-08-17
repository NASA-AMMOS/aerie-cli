"""
API dataclasses emulate the structure of data for exchange with the Aerie GraphQL API.

"create" dataclasses model data for upload and "read" dataclasses model data for download.
"""

from datetime import timedelta, datetime
from typing import Any
from typing import Dict
from typing import Optional
from typing import List
from typing import Union

from attrs import define, field
from attrs import converters
from attrs import asdict
from attrs import Attribute

import arrow
from arrow import Arrow

from aerie_cli.utils.serialization import postgres_interval_to_timedelta
from aerie_cli.utils.serialization import timedelta_to_postgres_interval

import json

def convert_to_time_delta(t: Union[str, timedelta]) -> timedelta:
    """Convert a string to timedelta.

    If the input is of type timedelta, does nothing and returns the input.
    This is used in certain fields to accept both strings and timedeltas."""
    if isinstance(t, timedelta):
        return t
    return postgres_interval_to_timedelta(t)

def serialize_api(inst: type, field: Attribute, value: Any):
    if isinstance(value, timedelta):
        return timedelta_to_postgres_interval(value)
    if isinstance(value, Arrow):
        return str(value)
    if isinstance(value, List) and field.name == "tags":
        return "{" + ",".join(value) + "}"
    return value

class ApiSerialize:
    @classmethod
    def from_dict(cls, dictionary: Dict) -> "ApiSerialize":
        return cls(**dictionary)
    def to_dict(self) -> Dict:
        return asdict(self, value_serializer=serialize_api)
    @classmethod
    def from_json(cls, dictionary: Dict) -> "ApiSerialize":
        return cls(**json.loads(dictionary))

@define
class ApiEffectiveActivityArguments(ApiSerialize):
    arguments: Dict[str, Any]

@define
class ActivityBase(ApiSerialize):
    """Base dataclass for an activity directive

    Fields match GraphQL field names in Aerie.
    """

    type: str
    start_offset: timedelta = field(
        converter = convert_to_time_delta
    )
    tags: Optional[List[str]] = field(factory=lambda: [], kw_only=True)
    metadata: Optional[Dict[str, str]] = field(factory=lambda: {}, kw_only=True)
    name: Optional[str] = field(factory=lambda: "", kw_only=True)
    arguments: Optional[Dict[str, Any]] = field(
        factory=lambda: [], kw_only=True
    )
    anchor_id: Optional[int] = field(default=None, kw_only=True)
    anchored_to_start: Optional[bool] = field(default=None, kw_only=True)

    def __attrs_post_init__(self):

        # Enforce that anchored_to_start must be specified if an anchor ID is given
        if self.anchored_to_start is None:
            if self.anchor_id is not None:
                raise ValueError(f"anchor_id was specified but anchored_to_start was not")
            self.anchored_to_start = True


@define
class ApiActivityCreate(ActivityBase):
    """Format for uploading activity directives

    Plan ID is added because it's required to be included as part of the activity object.
    Tags are encoded to the `text[]` format for GraphQL/Postgres.
    """

    plan_id: int
    tags: List[str]


@define
class ApiActivityRead(ActivityBase):
    """Format for downloading activity directives

    Downloaded activity directives have an ID which should be preserved, but is excluded in other cases (upload).
    """

    id: int

@define
class ApiActivityPlanBase(ApiSerialize):
    model_id: int
    name: str
    start_time: Arrow = field(
        converter=arrow.get
    )

@define
class ApiActivityPlanCreate(ApiActivityPlanBase):
    duration: timedelta = field(
        converter = convert_to_time_delta,
    )

@define
class ApiActivityPlanRead(ApiActivityPlanBase):
    id: int
    simulations: List[int]
    duration: timedelta = field(
        converter = convert_to_time_delta,
    )
    activity_directives: Optional[List[ApiActivityRead]] = field(
        default = None,
        converter=converters.optional(
            lambda listOfDicts: [ApiActivityRead.from_dict(d) if isinstance(d, dict) else d for d in listOfDicts])
    )


@define
class ApiAsSimulatedActivity(ApiSerialize):
    type: str
    parent_id: Optional[str]
    start_timestamp: Arrow = field(
        converter = arrow.get
    )
    children: List[str]
    duration: timedelta = field(
        converter = lambda microseconds: timedelta(microseconds=microseconds)
    )
    arguments: Dict[str, Any]


@define
class ApiSimulatedResourceSample(ApiSerialize):
    x: timedelta = field(
        converter = lambda microseconds: timedelta(microseconds=microseconds)
    )
    y: Any


@define
class ApiSimulationResults(ApiSerialize):
    start: Arrow = field(
        converter = arrow.get
    )
    activities: Dict[str, ApiAsSimulatedActivity]
    unfinishedActivities: Any
    # TODO: implement constraints
    constraints: Any
    # TODO: implement events
    events: Any


@define
class ApiResourceSampleResults(ApiSerialize):
    resourceSamples: Dict[str, List[ApiSimulatedResourceSample]]


@define
class ApiMissionModelCreate(ApiSerialize):
    name: str
    version: str
    mission: str
    jar_id: str


@define
class ApiMissionModelRead(ApiMissionModelCreate):
    id: int
