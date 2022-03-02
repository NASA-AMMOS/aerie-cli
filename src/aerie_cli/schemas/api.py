from dataclasses import dataclass
from dataclasses import field
from datetime import timedelta
from typing import Any
from typing import Optional

import arrow
from arrow import Arrow
from dataclasses_json import config
from dataclasses_json import dataclass_json
from dataclasses_json import LetterCase

from ..utils.serialization import hms_string_to_timedelta


@dataclass_json
@dataclass
class ApiActivityCreate:
    type: str
    plan_id: int
    start_offset: timedelta = field(
        metadata=config(decoder=hms_string_to_timedelta, encoder=timedelta.__str__)
    )
    arguments: dict[str, Any]


@dataclass_json
@dataclass
class ApiActivityRead(ApiActivityCreate):
    id: int


@dataclass_json
@dataclass
class ApiActivityPlanCreate:
    model_id: int
    name: str
    start_time: Arrow = field(
        metadata=config(decoder=arrow.get, encoder=Arrow.isoformat)
    )
    duration: timedelta = field(
        metadata=config(decoder=hms_string_to_timedelta, encoder=timedelta.__str__)
    )


@dataclass_json
@dataclass
class ApiActivityPlanRead(ApiActivityPlanCreate):
    id: int
    activities: list[ApiActivityRead]


@dataclass_json
@dataclass
class ApiAsSimulatedActivity:
    type: str
    parent: Optional[str]
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
    parameters: dict[str, Any]


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
    # TODO: implement constraints
    constraints: Any
    resources: dict[str, list[ApiSimulatedResourceSample]]
    # TODO: implement events
    events: Any
