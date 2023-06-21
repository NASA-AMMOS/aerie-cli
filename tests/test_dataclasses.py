"""Test dataclasses and associated methods
"""

from pathlib import Path
import arrow
import json

from aerie_cli.schemas.client import ActivityPlanRead
import pytest
INPUTS_DIRECTORY = Path(__file__).parent.joinpath("files", "inputs")


def test_get_activity_start_time():
    with open(INPUTS_DIRECTORY.joinpath("get_activity_start_time.json"), "r") as fid:
        plan: ActivityPlanRead = ActivityPlanRead(**json.loads(fid.read()))

    # Activity anchored to plan start
    assert plan.get_activity_start_time(2) == arrow.get("2030-01-01T02:00:00+00:00")

    # Activity anchored to plan end
    assert plan.get_activity_start_time(5) == arrow.get("2030-01-01T06:00:00+00:00")

    # 1-long chain of valid anchoring
    assert plan.get_activity_start_time(1) == arrow.get("2030-01-01T01:00:00+00:00")

    # 2-long chain of valid anchoring
    assert plan.get_activity_start_time(4) == arrow.get("2030-01-01T07:00:00+00:00")

    # Invalid: references anchor to activity end
    with pytest.raises(ValueError):
        plan.get_activity_start_time(3)

    # Invalid: anchor doesn't exist
    with pytest.raises(ValueError):
        plan.get_activity_start_time(6)

    # Pass activity instance instead of ID
    assert plan.get_activity_start_time(plan.activities[1]) == arrow.get("2030-01-01T02:00:00+00:00")