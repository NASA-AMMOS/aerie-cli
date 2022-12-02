import math
import re
from datetime import timedelta


POSTGRES_INTERVAL_PATTERN = re.compile(
    r"(?P<seconds>\d+)\sseconds\s(?P<milliseconds>\d+)\smilliseconds"
)


def postgres_duration_to_timedelta(hms_string: str) -> timedelta:
    if ":" not in hms_string:
        hms_string += " 00:00:00"
    if 'days' in hms_string:
        days, hms_string = hms_string.split(' days ')
    elif 'day' in hms_string:
        days, hms_string = hms_string.split(' day ')
    else:
        days = 0
    hours, minutes, seconds = hms_string.split(":")
    return timedelta(days=int(days), hours=int(hours), minutes=int(minutes), seconds=float(seconds))


def postgres_duration_to_microseconds(hms_string: str) -> int:
    return int(round(postgres_duration_to_timedelta(hms_string).total_seconds() * (10**6)))


def timedelta_to_postgres_interval(delta: timedelta) -> str:
    """Constructs a PostgresQL interval from two datetimes."""
    (seconds, partial_seconds) = divmod(delta.total_seconds(), 1)
    # what is appropriate rounding method?
    milliseconds = math.floor(partial_seconds * 1000)
    return f"{int(seconds)} seconds {milliseconds} milliseconds"


def postgres_interval_to_timedelta(interval: str) -> timedelta:
    """Constructs a timedelta from a PostgresQL interval string."""
    match = POSTGRES_INTERVAL_PATTERN.match(interval)
    return timedelta(
        seconds=match.group("seconds"), milliseconds=match.group("milliseconds")
    )
