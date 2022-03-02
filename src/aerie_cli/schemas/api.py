from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Optional

from dataclasses_json import config
from dataclasses_json import dataclass_json
from dataclasses_json import LetterCase


@dataclass_json
@dataclass
class ApiActivityCreate:
    type: str
    plan_id: int
    start_offset: str  # HMS string
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
    start_time: str  # ISO format
    duration: str  # HMS string


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
    start_timestamp: str = field(
        metadata=config(letter_case=LetterCase.CAMEL)
    )  # ISO format
    children: list[str]
    duration: int  # microseconds since plan start
    parameters: dict[str, Any]


@dataclass_json
@dataclass
class ApiSimulatedResourceSample:
    x: int  # microseconds since plan start
    y: Any


@dataclass_json
@dataclass
class ApiSimulationResults:
    start: str
    activities: dict[str, ApiAsSimulatedActivity]
    # TODO: implement constraints
    constraints: Any
    resources: dict[str, list[ApiSimulatedResourceSample]]
    # TODO: implement events
    events: Any
