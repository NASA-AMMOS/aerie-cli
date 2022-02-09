import json
import math
from datetime import timedelta
from typing import Any

from arrow import Arrow

CUSTOM_ENCODERS = {Arrow: Arrow.for_json}


class CustomJsonEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        for data_type, custom_encoder in CUSTOM_ENCODERS.items():
            if isinstance(obj, data_type):
                return custom_encoder(obj)
        return json.JSONEncoder.default(self, obj)


def hms_string_to_timedelta(hms_string: str) -> timedelta:
    hours, minutes, seconds = hms_string.split(":")
    return timedelta(hours=int(hours), minutes=int(minutes), seconds=float(seconds))


def timedelta_to_postgres_interval(delta: timedelta) -> str:
    """Constructs a PostgresQL interval from two datetimes."""
    (seconds, partial_seconds) = divmod(delta.total_seconds(), 1)
    # what is appropriate rounding method?
    milliseconds = math.floor(partial_seconds * 1000)
    return f"{int(seconds)} seconds {milliseconds} milliseconds"
