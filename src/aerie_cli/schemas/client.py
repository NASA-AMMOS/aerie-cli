"""
Client dataclasses store data in accessible formats and provide helper methods to convert to/from the API dataclasses.
"""

from datetime import timedelta
from typing import Any
from typing import Dict
from typing import List
from typing import Union
from typing import Optional
from enum import Enum

from attrs import define, field
from attrs import converters
import arrow
from arrow import Arrow
import json
from attrs import asdict

from aerie_cli.utils.serialization import parse_timedelta_str
from aerie_cli.schemas.api import ApiActivityCreate
from aerie_cli.schemas.api import ApiActivityUpdate
from aerie_cli.schemas.api import ApiActivityPlanCreate
from aerie_cli.schemas.api import ApiActivityPlanRead
from aerie_cli.schemas.api import ApiActivityRead
from aerie_cli.schemas.api import ApiSimulatedActivity
from aerie_cli.schemas.api import ApiResourceSampleResults
from aerie_cli.schemas.api import ApiSimulatedResourceSample
from aerie_cli.schemas.api import ApiSimulationDataset
from aerie_cli.schemas.api import ActivityBase
from aerie_cli.schemas.api import ApiParcelRead
from aerie_cli.schemas.api import ApiParcelCreate
from aerie_cli.schemas.api import ApiUserSequenceCreate
from aerie_cli.schemas.api import ApiUserSequenceRead

def parse_timedelta_str_converter(t) -> timedelta:
    if isinstance(t, str):
        return parse_timedelta_str(t)
    if isinstance(t, timedelta):
        return t
    raise TypeError(f"{type(t)} is not a supported input. Must be str or timedelta!")

def serialize_timedelta_to_str(inst, field, value):
    if isinstance(value, timedelta):
        return value.__str__()
    if isinstance(value, Arrow):
        return str(value)
    return value

class ClientSerialize:
    @classmethod
    def from_dict(cls, dictionary: dict) -> "ClientSerialize":
        return cls(**dictionary)
    def to_dict(self) -> dict:
        return asdict(self, value_serializer=serialize_timedelta_to_str)
    @classmethod
    def from_json(cls, dictionary: dict) -> "ClientSerialize":
        return cls(**json.loads(dictionary))
    def to_json(self, indent = 1) -> dict:
        self_as_dict = self.to_dict()
        return json.dumps(self_as_dict, indent=indent)

@define
class Activity(ActivityBase, ClientSerialize):
    """Activity Directive
    
    Dataclass designed for client-side manipulation of activity directives.
    Use helper methods to covert to and from API-compatible dataclasses.
    """
    start_offset: timedelta = field(
        converter = parse_timedelta_str_converter
    )
    id: Optional[int] = field(default=None)

    def to_api_create(self, plan_id: int):
        return ApiActivityCreate(
            type=self.type,
            plan_id=plan_id,
            start_offset=self.start_offset,
            arguments=self.arguments,
            name=self.name,
            metadata=self.metadata,
            anchor_id=self.anchor_id,
            anchored_to_start=self.anchored_to_start
        )

    def to_api_update(self):
        return ApiActivityUpdate(
            type=self.type,
            start_offset=self.start_offset,
            arguments=self.arguments,
            name=self.name,
            metadata=self.metadata,
            anchor_id=self.anchor_id,
            anchored_to_start=self.anchored_to_start
        )

    @classmethod
    def from_api_read(
        cls, api_activity_read: ApiActivityRead
    ) -> "Activity":
        return Activity(
            id=api_activity_read.id,
            name=api_activity_read.name,
            type=api_activity_read.type,
            start_offset=api_activity_read.start_offset,
            arguments=api_activity_read.arguments,
            metadata=api_activity_read.metadata,
            anchor_id=api_activity_read.anchor_id,
            anchored_to_start=api_activity_read.anchored_to_start
        )

@define
class EmptyActivityPlan(ClientSerialize):
    name: str
    start_time: Arrow = field(
        converter = arrow.get
    )
    end_time: Arrow = field(
        converter = arrow.get)
    tags: Optional[List[Dict]] 

    def duration(self) -> timedelta:
        return self.end_time - self.start_time


@define
class ActivityPlanCreate(EmptyActivityPlan):
    activities: List[Activity] = field(
        converter=converters.optional(
            lambda listOfDicts: [Activity.from_dict(d) if isinstance(d, dict) else d for d in listOfDicts])
    )

    id: Optional[int] = field(
        default=None
    )
    name: Optional[str] = field(
        default=None
    )
    start_time: Optional[Arrow] = field(
        default = None,
        converter = arrow.get
    )
    end_time: Optional[Arrow] = field(
        default = None,
        converter = arrow.get
    )
    model_id: Optional[int] = field(
        default=None
    )
    sim_id: Optional[int] = field(
        default=None
    )
    tags: Optional[List[Dict]] = field(
        default=[], 
        converter=converters.optional(
            lambda listOfDicts: [d for d in listOfDicts]
        )
    )

    @classmethod
    def from_plan_read(cls, plan_read: "ActivityPlanRead") -> "ActivityPlanCreate":
        return ActivityPlanCreate(
            name=plan_read.name,
            start_time=plan_read.start_time,
            end_time=plan_read.end_time,
            activities=plan_read.activities,
            tags=plan_read.tags
        )

    def to_api_create(self, model_id: int) -> "ApiActivityPlanCreate":
        return ApiActivityPlanCreate(
            model_id=model_id,
            name=self.name,
            start_time=self.start_time,
            duration=self.end_time - self.start_time,
        )


@define
class ActivityPlanRead(EmptyActivityPlan):
    id: int
    model_id: int
    sim_id: int
    tags: Optional[List[Dict]] = field(
        default = [], 
        converter=converters.optional(
            lambda listOfDicts: [d for d in listOfDicts]
        )
    )
    activities: Optional[List[Activity]] = field(
        default = None,
        converter=converters.optional(
            lambda listOfDicts: [Activity.from_dict(d) if isinstance(d, dict) else d for d in listOfDicts])
    )

    def get_activity_start_time(self, activity: Union[int, Activity]) -> arrow.Arrow:
        """Get the effective start time of an activity instance

        Args:
            activity (Union[int, Activity]): Either the Activity Directive ID or actual object

        Returns:
            arrow.Arrow: Effective activity start time
        """

        # If an ID was given, get the activity
        if isinstance(activity, int):
            try:
                activity = next(filter(lambda a: a.id == activity, self.activities))
            except StopIteration:
                raise ValueError(f"Cannot find anchor for activity with ID {activity}")

        # If the current activity is anchored to the plan, evaluate the start time rel. to the plan
        if activity.anchor_id is None:
            if activity.anchored_to_start:
                return self.start_time + activity.start_offset
            else:
                return self.end_time + activity.start_offset

        # If the current activity is anchored to another activity, evaluate the start time rel. to that act
        if activity.anchored_to_start:
            return (
                self.get_activity_start_time(activity.anchor_id) + activity.start_offset
            )
        else:
            raise ValueError(
                f"Cannot evaluate activity start time for Activity with ID {activity.id} because it is anchored to the end of another activity"
            )

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
            tags=api_plan_read.tags,
            activities= None if api_plan_read.activity_directives is None else [
                Activity.from_api_read(api_activity)
                for api_activity in api_plan_read.activity_directives
            ],
        )


@define
class SimulatedActivity(ClientSerialize):
    id: str
    type: str
    arguments: Dict[str, Any]
    computed_attributes: Dict[str, Any]
    parent_id: Optional[str]
    start_time: Arrow = field(converter = arrow.get)
    end_time: Arrow = field(converter = arrow.get)
    start_offset: timedelta = field(converter = parse_timedelta_str_converter)
    duration: timedelta = field(converter = parse_timedelta_str_converter)
    directive: Optional[Activity]

    @classmethod
    def from_api_as_simulated_activity(
        cls, api_as_simulated_activity: ApiSimulatedActivity
    ):
        if api_as_simulated_activity.activity_directive is None:
            directive = None
        else:
            directive = Activity.from_api_read(api_as_simulated_activity.activity_directive)

        return SimulatedActivity(
            id=api_as_simulated_activity.id,
            type=api_as_simulated_activity.activity_type_name,
            arguments=api_as_simulated_activity.attributes["arguments"],
            computed_attributes=api_as_simulated_activity.attributes["computedAttributes"],
            parent_id=api_as_simulated_activity.parent_id,
            start_time=api_as_simulated_activity.start_time,
            end_time=api_as_simulated_activity.end_time,
            start_offset=api_as_simulated_activity.start_offset,
            duration=api_as_simulated_activity.duration,
            directive=directive
        )


@define
class SimulatedResourceSample(ClientSerialize):
    t: Arrow = field(
        converter = arrow.get
    )
    v: Any


@define
class SimulatedResourceTimeline(ClientSerialize):
    name: str
    values: List[SimulatedResourceSample]

    @classmethod
    def from_api_sim_res_timeline(
        cls,
        name: str,
        api_sim_res_timeline: List[ApiSimulatedResourceSample],
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


@define
class SimulationDataset(ClientSerialize):
    id: int
    arguments: Dict[str, Any]
    status: str
    dataset_id: int
    start_time: Arrow = field(converter = arrow.get)
    end_time: Arrow = field(converter = arrow.get)
    activities: List[SimulatedActivity]
    # resources: List[SimulatedResourceTimeline]

    @classmethod
    def from_api_dict(cls, api_dict: Dict) -> "SimulationDataset":
        return cls.from_api_results(ApiSimulationDataset.from_dict(api_dict))

    @classmethod
    def from_api_results(
        cls,
        api_sim_results: ApiSimulationDataset,
        # api_resource_timeline: ApiResourceSampleResults,
    ) -> "SimulationDataset":
        return SimulationDataset(
            id=api_sim_results.id,
            arguments=api_sim_results.arguments,
            status=api_sim_results.status,
            dataset_id=api_sim_results.dataset_id,
            start_time=api_sim_results.simulation_start_time,
            end_time=api_sim_results.simulation_end_time,
            activities=[
                SimulatedActivity.from_api_as_simulated_activity(act)
                for act in api_sim_results.simulated_activities
            ]
            # resources=[
            #     SimulatedResourceTimeline.from_api_sim_res_timeline(
            #         name, api_timeline, plan_start
            #     )
            #     for name, api_timeline in api_resource_timeline.resourceSamples.items()
            # ],
        )


@define
class ActivityInstanceCommand(ClientSerialize):
    activity_instance_id: int
    commands: List[Dict]
    errors: List[Dict]


@define
class ExpansionRun(ClientSerialize):
    id: int
    expansion_set_id: int
    simulation_dataset_id: int
    created_at: Arrow = field(
        converter = arrow.get
    )
    activity_instance_commands: Optional[List[ActivityInstanceCommand]] = None


@define
class ExpansionSet(ClientSerialize):
    id: int
    created_at: Arrow = field(
        converter = arrow.get
    )
    updated_at: Arrow = field(
        converter = arrow.get
    )
    updated_by: str
    parcel_id: int
    expansion_rules: List[int] = field(
        converter = lambda x: [i['id'] for i in x])
    description: str
    name: str
    mission_model_id: int
    owner: str


@define
class ExpansionRule(ClientSerialize):
    id: int
    activity_type: str
    authoring_mission_model_id: int
    parcel_id: int
    expansion_logic: Optional[str] = None
    name: Optional[str] = None


@define
class ResourceType(ClientSerialize):
    name: str
    schema: Dict


@define
class ExpansionDeployRule(ClientSerialize):
    name: str
    activity_type: str
    file_name: str


@define
class ExpansionDeploySet(ClientSerialize):
    name: str
    rules: List[str]


@define
class ExpansionDeployConfiguration(ClientSerialize):
    rules: List[ExpansionDeployRule] = field(
        converter=converters.optional(
            lambda x: [ExpansionDeployRule.from_dict(d) if isinstance(d, dict) else d for d in x])
    )
    sets: List[ExpansionDeploySet] = field(
        converter=converters.optional(
            lambda x: [ExpansionDeploySet.from_dict(d) if isinstance(d, dict) else d for d in x])
    )


@define
class Parcel(ClientSerialize):
    name: str
    command_dictionary_id: int
    channel_dictionary_id: int
    sequence_adaptation_id: int
    parameter_dictionary_ids: List[int]
    id: Optional[int] = field(default=None)

    def to_api_create(self) -> ApiParcelCreate:
        return ApiParcelCreate(
            name=self.name,
            command_dictionary_id=self.command_dictionary_id,
            channel_dictionary_id=self.channel_dictionary_id,
            sequence_adaptation_id=self.sequence_adaptation_id
        )

    @classmethod
    def from_api_read(cls, api_parcel: ApiParcelRead) -> "Parcel":
        return cls(
            name=api_parcel.name,
            command_dictionary_id=api_parcel.command_dictionary_id,
            channel_dictionary_id=api_parcel.channel_dictionary_id,
            sequence_adaptation_id=api_parcel.sequence_adaptation_id,
            parameter_dictionary_ids=[p["parameter_dictionary_id"] for p in api_parcel.parameter_dictionaries],
            id = api_parcel.id
        )

class DictionaryType(Enum):
    COMMAND = 'COMMAND'
    CHANNEL = 'CHANNEL'
    PARAMETER = 'PARAMETER'


@define
class DictionaryMetadata(ClientSerialize):
    id: int
    mission: str
    version: str
    created_at: Arrow = field(
        converter=arrow.get
    )
    updated_at: Arrow = field(
        converter=arrow.get
    )


@define
class SequenceAdaptationMetadata(ClientSerialize):
    id: int
    owner: str
    updated_by: str
    created_at: Arrow = field(
        converter=arrow.get
    )
    updated_at: Arrow = field(
        converter=arrow.get
    )


@define
class Workspace(ClientSerialize):
    name: str
    id: int


@define
class UserSequence(ClientSerialize):
    name: str
    definition: str
    parcel_id: int
    workspace_id: int
    id: int = field(default=None)

    def to_api_create(self) -> ApiUserSequenceCreate:
        return ApiUserSequenceCreate(
            name=self.name,
            definition=self.definition,
            parcel_id=self.parcel_id,
            workspace_id=self.workspace_id
        )

    @classmethod
    def from_api_dict(cls, sequence: Dict) -> "UserSequence":
        return cls.from_api_read(ApiUserSequenceRead.from_dict(sequence))

    @classmethod
    def from_api_read(cls, sequence: ApiUserSequenceRead) -> "UserSequence":
        return cls(
            name=sequence.name,
            definition=sequence.definition,
            parcel_id=sequence.parcel_id,
            workspace_id=sequence.workspace_id,
            id=sequence.id
        )
