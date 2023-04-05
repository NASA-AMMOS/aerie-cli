"""
API dataclasses emulate the structure of data for exchange with the Aerie GraphQL API.

"create" dataclasses model data for upload and "read" dataclasses model data for download.
"""

from dataclasses import dataclass
from dataclasses import field
from datetime import timedelta
from typing import Any
from typing import Dict
from typing import Optional
from typing import List

import arrow
from arrow import Arrow
from dataclasses_json import config
from dataclasses_json import dataclass_json
from dataclasses_json import LetterCase

from ..utils.serialization import postgres_interval_to_timedelta
from ..utils.serialization import timedelta_to_postgres_interval


@dataclass_json
@dataclass
class ApiEffectiveActivityArguments:
    arguments: dict[str, Any]


@dataclass_json
@dataclass
class ActivityBase:
    """Base dataclass for an activity directive

    Fields match GraphQL field names in Aerie.
    """

    type: str
    start_offset: timedelta = field(
        metadata=config(
            decoder=postgres_interval_to_timedelta,
            encoder=timedelta_to_postgres_interval,
        )
    )
    tags: Optional[List[str]] = field(default_factory=lambda: [], kw_only=True)
    metadata: Optional[Dict[str, str]] = field(default_factory=lambda: {}, kw_only=True)
    name: Optional[str] = field(default_factory=lambda: "", kw_only=True)
    arguments: Optional[Dict[str, Any]] = field(
        default_factory=lambda: [], kw_only=True
    )
    anchor_id: Optional[int] = field(default=None, kw_only=True)
    anchored_to_start: Optional[bool] = field(default=None, kw_only=True)

    def __post_init__(self):

        # Enforce that anchored_to_start must be specified if an anchor ID is given
        if self.anchored_to_start is None:
            if self.anchor_id is not None:
                raise ValueError(f"anchor_id was specified but anchored_to_start was not")
            self.anchored_to_start = True


@dataclass_json
@dataclass
class ApiActivityCreate(ActivityBase):
    """Format for uploading activity directives

    Plan ID is added because it's required to be included as part of the activity object.
    Tags are encoded to the `text[]` format for GraphQL/Postgres.
    """

    plan_id: int
    tags: list[str] = field(
        metadata=config(encoder=lambda ts: "{" + ",".join(ts) + "}")
    )


@dataclass_json
@dataclass
class ApiActivityRead(ActivityBase):
    """Format for downloading activity directives

    Downloaded activity directives have an ID which should be preserved, but is excluded in other cases (upload).
    """

    id: int


@dataclass_json
@dataclass
class ApiActivityPlanBase:
    model_id: int
    name: str
    start_time: Arrow = field(
        metadata=config(decoder=arrow.get, encoder=Arrow.isoformat)
    )


@dataclass_json
@dataclass
class ApiActivityPlanCreate(ApiActivityPlanBase):
    duration: timedelta = field(
        metadata=config(
            decoder=postgres_interval_to_timedelta,
            encoder=timedelta_to_postgres_interval,
        )
    )


@dataclass_json
@dataclass
class ApiActivityPlanRead(ApiActivityPlanBase):
    id: int
    simulations: list[int]
    duration: timedelta = field(
        metadata=config(
            decoder=postgres_interval_to_timedelta, encoder=timedelta.__str__
        )
    )
    activity_directives: Optional[List[ApiActivityRead]] = None


@dataclass_json
@dataclass
class ApiAsSimulatedActivity:
    type: str
    parent_id: Optional[str]
    start_timestamp: Arrow = field(
        metadata=config(
            letter_case=LetterCase.CAMEL, decoder=arrow.get, encoder=Arrow.isoformat
        )
    )
    children: list[str]
    duration: timedelta = field(
        metadata=config(
            decoder=lambda microseconds: timedelta(microseconds=microseconds),
            encoder=lambda dur: round(dur.total_seconds() * 1e6),
        )
    )
    arguments: dict[str, Any]


@dataclass_json
@dataclass
class ApiSimulatedResourceSample:
    x: timedelta = field(
        metadata=config(
            decoder=lambda microseconds: timedelta(microseconds=microseconds),
            encoder=lambda dur: round(dur.total_seconds() * 1e6),
        )
    )
    y: Any


@dataclass_json
@dataclass
class ApiSimulationResults:
    start: Arrow = field(metadata=config(decoder=arrow.get, encoder=Arrow.isoformat))
    activities: dict[str, ApiAsSimulatedActivity]
    unfinishedActivities: Any
    # TODO: implement constraints
    constraints: Any
    # TODO: implement events
    events: Any


@dataclass_json
@dataclass
class ApiResourceSampleResults:
    resourceSamples: dict[str, list[ApiSimulatedResourceSample]]


@dataclass_json
@dataclass
class ApiMissionModelCreate:
    name: str
    version: str
    mission: str
    jar_id: str


@dataclass_json
@dataclass
class ApiMissionModelRead(ApiMissionModelCreate):
    id: int
