from dataclasses import dataclass
from datetime import timedelta

import pytest

from aerie_cli.utils.serialization import postgres_interval_to_microseconds
from aerie_cli.utils.serialization import postgres_interval_to_timedelta
from aerie_cli.utils.serialization import timedelta_to_postgres_interval
from aerie_cli.utils.serialization import parse_timedelta_str


@dataclass
class ExampleDuration:
    as_timedelta: timedelta
    as_postgres_output: str
    as_postgres_input: str
    as_microseconds: int


TEST_CASES = [
    ExampleDuration(
        as_timedelta=timedelta(seconds=1),
        as_postgres_output="00:00:01",
        as_postgres_input="1 seconds 0 microseconds",
        as_microseconds=int(1e6),
    ),
    ExampleDuration(
        as_timedelta=timedelta(seconds=-1),
        as_postgres_output="-00:00:01",
        as_postgres_input="-1 seconds 0 microseconds",
        as_microseconds=int(-1e6),
    ),
    ExampleDuration(
        as_timedelta=timedelta(days=1, seconds=1),
        as_postgres_output="1 day 00:00:01",
        as_postgres_input="86401 seconds 0 microseconds",
        as_microseconds=int(1e6 * 86401),
    ),
    ExampleDuration(
        as_timedelta=timedelta(days=2, seconds=1),
        as_postgres_output="2 day 00:00:01",
        as_postgres_input="172801 seconds 0 microseconds",
        as_microseconds=int(1e6 * 172801),
    ),
    ExampleDuration(
        as_timedelta=timedelta(days=1, seconds=-1),
        as_postgres_output="23:59:59",
        as_postgres_input="86399 seconds 0 microseconds",
        as_microseconds=int(1e6 * 86399),
    ),
    ExampleDuration(
        as_timedelta=timedelta(days=-1, seconds=1),
        as_postgres_output="-23:59:59",
        as_postgres_input="-86399 seconds 0 microseconds",
        as_microseconds=int(-1e6 * 86399),
    ),
    ExampleDuration(
        as_timedelta=timedelta(days=-1, seconds=-1),
        as_postgres_output="-1 day -00:00:01",
        as_postgres_input="-86401 seconds 0 microseconds",
        as_microseconds=int(-1e6 * 86401),
    ),
    ExampleDuration(
        as_timedelta=timedelta(seconds=1, microseconds=123),
        as_postgres_output="00:00:01.000123",
        as_postgres_input="1 seconds 123 microseconds",
        as_microseconds=int(1e6 + 123),
    ),
    ExampleDuration(
        as_timedelta=timedelta(seconds=1, milliseconds=123),
        as_postgres_output="00:00:01.123",
        as_postgres_input="1 seconds 123000 microseconds",
        as_microseconds=int(1e6 + 123000),
    ),
]


@pytest.mark.parametrize("example_duration", TEST_CASES)
def test_postgres_interval_to_microseconds(example_duration: ExampleDuration):
    assert (
        postgres_interval_to_microseconds(example_duration.as_postgres_output)
        == example_duration.as_microseconds
    )


@pytest.mark.parametrize("example_duration", TEST_CASES)
def test_postgres_interval_to_timedelta(example_duration: ExampleDuration):
    assert (
        postgres_interval_to_timedelta(example_duration.as_postgres_output)
        == example_duration.as_timedelta
    )


@pytest.mark.parametrize("example_duration", TEST_CASES)
def test_timedelta_to_postgres_interval(example_duration: ExampleDuration):
    assert (
        timedelta_to_postgres_interval(example_duration.as_timedelta)
        == example_duration.as_postgres_input
    )


@pytest.mark.parametrize("example_duration", TEST_CASES)
def test_parse_timedelta_str(example_duration: ExampleDuration):
    assert (
        parse_timedelta_str(str(example_duration.as_timedelta))
        == example_duration.as_timedelta
    )
