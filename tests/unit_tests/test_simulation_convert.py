import pytest

from aerie_cli.utils.simulation_convert import (
    _normalize_duration,
    _classify,
    _real_segments,
    _discrete_segments,
    convert_activities,
    convert_resources,
    infer_window,
    build_simulation_upload,
    iso_to_doy,
    micros_to_extent,
)
from datetime import datetime, timezone


# --------------------------------------------------------------------------- #
# Time helpers
# --------------------------------------------------------------------------- #

def test_iso_to_doy_basic():
    assert iso_to_doy("2024-01-02T00:00:00+00:00") == "2024-002T00:00:00.000000"


def test_iso_to_doy_mid_year():
    # Day 60 of a leap year (2024): Feb 29
    assert iso_to_doy("2024-02-29T12:30:45.123456+00:00") == "2024-060T12:30:45.123456"


def test_iso_to_doy_assumes_utc_when_naive():
    assert iso_to_doy("2024-01-01T00:00:00") == "2024-001T00:00:00.000000"


def test_micros_to_extent_whole_seconds():
    assert micros_to_extent(3_600_000_000) == "01:00:00.000000"


def test_micros_to_extent_fractional():
    assert micros_to_extent(1_500_000) == "00:00:01.500000"


def test_micros_to_extent_hours_over_24():
    assert micros_to_extent(48 * 3_600_000_000) == "48:00:00.000000"


def test_micros_to_extent_zero():
    assert micros_to_extent(0) == "00:00:00.000000"


def test_micros_to_extent_negative_raises():
    with pytest.raises(ValueError):
        micros_to_extent(-1)


# --------------------------------------------------------------------------- #
# Duration normalisation
# --------------------------------------------------------------------------- #

def test_normalize_duration_no_fractional():
    assert _normalize_duration("01:30:00") == "01:30:00.000000"


def test_normalize_duration_short_fractional():
    assert _normalize_duration("00:00:16.05703") == "00:00:16.057030"


def test_normalize_duration_full_fractional():
    assert _normalize_duration("00:00:01.123456") == "00:00:01.123456"


def test_normalize_duration_truncates_excess():
    assert _normalize_duration("00:00:01.1234567") == "00:00:01.123456"


# --------------------------------------------------------------------------- #
# Resource classification
# --------------------------------------------------------------------------- #

def test_classify_real():
    assert _classify([{"x": 0, "y": 3.14}, {"x": 1000, "y": 6.28}]) == "real"


def test_classify_integer_is_real():
    assert _classify([{"x": 0, "y": 42}]) == "real"


def test_classify_boolean():
    assert _classify([{"x": 0, "y": True}]) == "boolean"


def test_classify_string():
    assert _classify([{"x": 0, "y": "SAFE"}]) == "string"


def test_classify_series():
    assert _classify([{"x": 0, "y": [1.0, 2.0, 3.0]}]) == "series"


def test_classify_all_null_defaults_string():
    assert _classify([{"x": 0, "y": None}]) == "string"


def test_classify_empty_defaults_string():
    assert _classify([]) == "string"


# --------------------------------------------------------------------------- #
# Real segments
# --------------------------------------------------------------------------- #

def test_real_segments_single_constant():
    # Two points, same y → rate = 0
    samples = [{"x": 0, "y": 5.0}, {"x": 1_000_000, "y": 5.0}]
    segs = _real_segments(samples)
    assert len(segs) == 1
    assert segs[0]["extent"] == "00:00:01.000000"
    assert segs[0]["dynamics"]["initial"] == pytest.approx(5.0)
    assert segs[0]["dynamics"]["rate"] == pytest.approx(0.0)


def test_real_segments_with_rate():
    # y goes from 0 → 10 over 10 seconds → rate = 1.0 per second
    samples = [{"x": 0, "y": 0.0}, {"x": 10_000_000, "y": 10.0}]
    segs = _real_segments(samples)
    assert len(segs) == 1
    assert segs[0]["dynamics"]["rate"] == pytest.approx(1.0)


def test_real_segments_skips_discontinuity_markers():
    # Samples with x1 == x0 (discontinuity) should be skipped
    samples = [
        {"x": 0, "y": 1.0},
        {"x": 1_000_000, "y": 2.0},
        {"x": 1_000_000, "y": 5.0},   # same x as previous → discontinuity marker
        {"x": 2_000_000, "y": 5.0},
    ]
    segs = _real_segments(samples)
    # Pair (0,1.0)→(1e6,2.0) and pair (1e6,5.0)→(2e6,5.0); the (1e6,2.0)→(1e6,5.0) pair is skipped
    assert len(segs) == 2


def test_real_segments_empty():
    assert _real_segments([]) == []


def test_real_segments_single_point():
    assert _real_segments([{"x": 0, "y": 1.0}]) == []


# --------------------------------------------------------------------------- #
# Discrete segments
# --------------------------------------------------------------------------- #

SIM_END_US = 10_000_000  # 10 seconds


def test_discrete_segments_single_constant():
    samples = [{"x": 0, "y": "SAFE"}]
    segs = _discrete_segments(samples, SIM_END_US)
    assert len(segs) == 1
    assert segs[0]["dynamics"] == "SAFE"
    assert segs[0]["extent"] == "00:00:10.000000"


def test_discrete_segments_two_values():
    samples = [{"x": 0, "y": "SAFE"}, {"x": 5_000_000, "y": "NOMINAL"}]
    segs = _discrete_segments(samples, SIM_END_US)
    assert len(segs) == 2
    assert segs[0]["dynamics"] == "SAFE"
    assert segs[0]["extent"] == "00:00:05.000000"
    assert segs[1]["dynamics"] == "NOMINAL"
    assert segs[1]["extent"] == "00:00:05.000000"


def test_discrete_segments_deduplicates_repeats():
    # Repeated value emitted twice shouldn't create two segments
    samples = [
        {"x": 0, "y": "SAFE"},
        {"x": 2_000_000, "y": "SAFE"},   # same value → no new boundary
        {"x": 5_000_000, "y": "NOMINAL"},
    ]
    segs = _discrete_segments(samples, SIM_END_US)
    assert len(segs) == 2
    assert segs[0]["extent"] == "00:00:05.000000"  # holds until NOMINAL


def test_discrete_segments_boolean():
    samples = [{"x": 0, "y": False}, {"x": 4_000_000, "y": True}]
    segs = _discrete_segments(samples, SIM_END_US)
    assert segs[0]["dynamics"] is False
    assert segs[1]["dynamics"] is True


def test_discrete_segments_vector():
    v = [1.0, 2.0, 3.0]
    samples = [{"x": 0, "y": v}]
    segs = _discrete_segments(samples, SIM_END_US)
    assert segs[0]["dynamics"] == v


# --------------------------------------------------------------------------- #
# convert_activities
# --------------------------------------------------------------------------- #

ACTIVITY_A = {
    "id": 1,
    "activity_type_name": "MyActivity",
    "directive_id": 10,
    "parent_id": None,
    "start_time": "2024-01-02T00:00:00+00:00",
    "end_time": "2024-01-02T01:00:00+00:00",
    "duration": "01:00:00",
    "attributes": {
        "arguments": {"speed": 42},
        "computedAttributes": {"result": "ok"},
    },
}

ACTIVITY_B = {
    "id": 2,
    "activity_type_name": "ChildActivity",
    "directive_id": None,
    "parent_id": 1,
    "start_time": "2024-01-02T00:30:00+00:00",
    "end_time": "2024-01-02T01:00:00+00:00",
    "duration": "00:30:00",
    "attributes": None,
}


def test_convert_activities_renames_fields():
    simulated, unfinished = convert_activities([ACTIVITY_A])
    a = simulated[0]
    assert a["type"] == "MyActivity"
    assert a["directiveId"] == 10
    assert a["parentId"] is None
    assert a["startTime"] == "2024-002T00:00:00.000000"
    assert a["duration"] == "01:00:00.000000"


def test_convert_activities_arguments_and_attributes():
    simulated, _ = convert_activities([ACTIVITY_A])
    a = simulated[0]
    assert a["arguments"] == {"speed": 42}
    assert a["attributes"] == {"result": "ok"}


def test_convert_activities_none_attributes_default_to_empty():
    simulated, _ = convert_activities([ACTIVITY_B])
    a = simulated[0]
    assert a["arguments"] == {}
    assert a["attributes"] == {}


def test_convert_activities_child_ids_derived():
    simulated, _ = convert_activities([ACTIVITY_A, ACTIVITY_B])
    parent = next(a for a in simulated if a["id"] == 1)
    child = next(a for a in simulated if a["id"] == 2)
    assert parent["childIds"] == [2]
    assert child["childIds"] == []
    assert child["parentId"] == 1


def test_convert_activities_unfinished_always_empty():
    _, unfinished = convert_activities([ACTIVITY_A])
    assert unfinished == []


# --------------------------------------------------------------------------- #
# convert_resources
# --------------------------------------------------------------------------- #

RESOURCES_REAL = {
    "resourceSamples": {
        "temperature": [
            {"x": 0, "y": 20.0},
            {"x": 3_600_000_000, "y": 20.0},  # constant over 1 hour
        ]
    }
}

RESOURCES_DISCRETE = {
    "resourceSamples": {
        "mode": [
            {"x": 0, "y": "SAFE"},
            {"x": 1_800_000_000, "y": "NOMINAL"},
        ]
    }
}

RESOURCES_MIXED = {
    "resourceSamples": {
        "temperature": [
            {"x": 0, "y": 20.0},
            {"x": 3_600_000_000, "y": 20.0},
        ],
        "mode": [
            {"x": 0, "y": "SAFE"},
            {"x": 1_800_000_000, "y": "NOMINAL"},
        ],
    }
}

SIM_END_1HR = 3_600_000_000


def test_convert_resources_real_profile():
    real, discrete = convert_resources(RESOURCES_REAL, SIM_END_1HR)
    assert len(real) == 1
    assert len(discrete) == 0
    assert real[0]["name"] == "temperature"
    assert real[0]["schema"] == {"type": "real"}
    assert real[0]["segments"][0]["dynamics"]["initial"] == pytest.approx(20.0)
    assert real[0]["segments"][0]["dynamics"]["rate"] == pytest.approx(0.0)


def test_convert_resources_discrete_profile():
    real, discrete = convert_resources(RESOURCES_DISCRETE, SIM_END_1HR)
    assert len(real) == 0
    assert len(discrete) == 1
    assert discrete[0]["name"] == "mode"
    assert discrete[0]["schema"] == {"type": "string"}
    assert discrete[0]["segments"][0]["dynamics"] == "SAFE"
    assert discrete[0]["segments"][1]["dynamics"] == "NOMINAL"


def test_convert_resources_sorted_by_name():
    resources = {
        "resourceSamples": {
            "z_real": [{"x": 0, "y": 1.0}, {"x": 1_000_000, "y": 2.0}],
            "a_real": [{"x": 0, "y": 5.0}, {"x": 1_000_000, "y": 5.0}],
            "z_str": [{"x": 0, "y": "B"}],
            "a_str": [{"x": 0, "y": "A"}],
        }
    }
    real, discrete = convert_resources(resources, SIM_END_1HR)
    real_names = [p["name"] for p in real]
    disc_names = [p["name"] for p in discrete]
    assert real_names == sorted(real_names)
    assert disc_names == sorted(disc_names)


def test_convert_resources_empty_samples_skipped():
    resources = {"resourceSamples": {"empty": []}}
    real, discrete = convert_resources(resources, SIM_END_1HR)
    assert real == []
    assert discrete == []


def test_convert_resources_no_resource_samples():
    real, discrete = convert_resources({}, SIM_END_1HR)
    assert real == []
    assert discrete == []


# --------------------------------------------------------------------------- #
# infer_window
# --------------------------------------------------------------------------- #

def test_infer_window_uses_resource_offset():
    activities = [ACTIVITY_A]
    resources = {"resourceSamples": {"x": [{"x": 0, "y": 1.0}, {"x": 7_200_000_000, "y": 1.0}]}}
    start, end = infer_window(activities, resources)
    assert start == datetime(2024, 1, 2, tzinfo=timezone.utc)
    delta_us = int((end - start).total_seconds() * 1_000_000)
    assert delta_us == 7_200_000_000


def test_infer_window_falls_back_to_end_time():
    activities = [ACTIVITY_A]
    resources = {"resourceSamples": {}}
    start, end = infer_window(activities, resources)
    assert end == datetime(2024, 1, 2, 1, 0, 0, tzinfo=timezone.utc)


def test_infer_window_no_activities_raises():
    with pytest.raises(ValueError):
        infer_window([], {})


# --------------------------------------------------------------------------- #
# build_simulation_upload (integration)
# --------------------------------------------------------------------------- #

def test_build_simulation_upload_top_level_keys():
    result = build_simulation_upload([ACTIVITY_A], RESOURCES_MIXED)
    assert "simulationStartTime" in result
    assert "simulationEndTime" in result
    assert "profiles" in result
    assert "spans" in result


def test_build_simulation_upload_profiles_structure():
    result = build_simulation_upload([ACTIVITY_A], RESOURCES_MIXED)
    assert "realProfiles" in result["profiles"]
    assert "discreteProfiles" in result["profiles"]


def test_build_simulation_upload_spans_structure():
    result = build_simulation_upload([ACTIVITY_A], RESOURCES_MIXED)
    assert "simulatedActivities" in result["spans"]
    assert "unfinishedActivities" in result["spans"]
    assert result["spans"]["unfinishedActivities"] == []


def test_build_simulation_upload_activity_count():
    result = build_simulation_upload([ACTIVITY_A, ACTIVITY_B], RESOURCES_MIXED)
    assert len(result["spans"]["simulatedActivities"]) == 2


def test_build_simulation_upload_timestamps_are_doy():
    result = build_simulation_upload([ACTIVITY_A], RESOURCES_MIXED)
    # DOY format: YYYY-DDDThh:mm:ss.ssssss
    import re
    doy_pattern = r"^\d{4}-\d{3}T\d{2}:\d{2}:\d{2}\.\d{6}$"
    assert re.match(doy_pattern, result["simulationStartTime"])
    assert re.match(doy_pattern, result["simulationEndTime"])
