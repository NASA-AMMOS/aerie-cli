from dataclasses import dataclass
from datetime import timedelta

import pytest

from aerie_cli.utils.serialization import postgres_interval_to_microseconds
from aerie_cli.utils.serialization import postgres_interval_to_timedelta
from aerie_cli.utils.serialization import timedelta_to_postgres_interval


@dataclass
class ExampleDuration:
    as_timedelta: timedelta
    as_output_interval: str
    as_input_interval: str
    as_microseconds: int


TEST_CASES = [
    ExampleDuration(
        as_timedelta=timedelta(seconds=1),
        as_output_interval="00:00:01",
        as_input_interval="1 seconds 0 microseconds",
        as_microseconds=int(1e6),
    ),
    ExampleDuration(
        as_timedelta=timedelta(seconds=-1),
        as_output_interval="-00:00:01",
        as_input_interval="-1 seconds 0 microseconds",
        as_microseconds=int(-1e6),
    ),
    ExampleDuration(
        as_timedelta=timedelta(days=1, seconds=1),
        as_output_interval="1 day 00:00:01",
        as_input_interval="86401 seconds 0 microseconds",
        as_microseconds=int(1e6 * 86401),
    ),
    ExampleDuration(
        as_timedelta=timedelta(days=1, seconds=-1),
        as_output_interval="23:59:59",
        as_input_interval="86399 seconds 0 microseconds",
        as_microseconds=int(1e6 * 86399),
    ),
    ExampleDuration(
        as_timedelta=timedelta(days=-1, seconds=1),
        as_output_interval="-23:59:59",
        as_input_interval="-86399 seconds 0 microseconds",
        as_microseconds=int(-1e6 * 86399),
    ),
    ExampleDuration(
        as_timedelta=timedelta(days=-1, seconds=-1),
        as_output_interval="-1 day -00:00:01",
        as_input_interval="-86401 seconds 0 microseconds",
        as_microseconds=int(-1e6 * 86401),
    ),
    ExampleDuration(
        as_timedelta=timedelta(seconds=1, microseconds=123),
        as_output_interval="00:00:01.000123",
        as_input_interval="1 seconds 123 microseconds",
        as_microseconds=int(1e6 + 123),
    ),
    ExampleDuration(
        as_timedelta=timedelta(seconds=1, milliseconds=123),
        as_output_interval="00:00:01.123",
        as_input_interval="1 seconds 123000 microseconds",
        as_microseconds=int(1e6 + 123000),
    ),
]


@pytest.mark.parametrize("example_duration", TEST_CASES)
def test_postgres_interval_to_microseconds(example_duration: ExampleDuration):
    assert (
        postgres_interval_to_microseconds(example_duration.as_output_interval)
        == example_duration.as_microseconds
    )


@pytest.mark.parametrize("example_duration", TEST_CASES)
def test_postgres_interval_to_timedelta(example_duration: ExampleDuration):
    assert (
        postgres_interval_to_timedelta(example_duration.as_output_interval)
        == example_duration.as_timedelta
    )


@pytest.mark.parametrize("example_duration", TEST_CASES)
def test_timedelta_to_postgres_interval(example_duration: ExampleDuration):
    assert (
        timedelta_to_postgres_interval(example_duration.as_timedelta)
        == example_duration.as_input_interval
    )
