from dataclasses import dataclass
from dataclasses import field
from datetime import timedelta
from typing import Any
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
class ApiActivityBase:
    type: str
    arguments: dict[str, Any]
    name: str
    tags: list[str]
    metadata: dict[str, str]


@dataclass_json
@dataclass
class ApiActivityCreate(ApiActivityBase):
    plan_id: int
    start_offset: timedelta = field(
        metadata=config(
            decoder=postgres_interval_to_timedelta,
            encoder=timedelta_to_postgres_interval,
        )
    )


@dataclass_json
@dataclass
class ApiActivityRead(ApiActivityBase):
    id: int
    start_offset: timedelta = field(
        metadata=config(decoder=postgres_duration_to_timedelta, encoder=timedelta.__str__)
    )


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
