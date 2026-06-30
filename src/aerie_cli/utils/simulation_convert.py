"""
Convert aerie-cli simulation downloads to the SimulationResultsWriter JSON format
accepted by PlanDev's uploadSimulationDataset endpoint.

Inputs:
  - activities : list returned by AerieClient.get_simulation_results()
  - resources  : dict returned by AerieClient.get_resource_samples()

Key format facts (verified against the parser source):
  * Activity `arguments` and `attributes` are RAW serialized values (no {type,value} wrapper).
      - a string is just "MARS", a number is 16057033, an optional is {"value":..,"present":..}
        exactly as aerie-cli already emits it.
  * Real profile segment dynamics = {"initial": <float>, "rate": <float per SECOND>}.
  * Discrete profile segment dynamics = the RAW value ("NONE", false, [x,y,z], ...).
  * `schema` types accepted: real, int, boolean, string, duration, path, series, struct, variant.
  * Timestamps are DOY strings  YYYY-DDDThh:mm:ss.ssssss
  * Durations / extents are strings  HH:MM:SS.ssssss
"""

from datetime import datetime, timezone, timedelta
from typing import Any


# --------------------------------------------------------------------------- #
# Time helpers
# --------------------------------------------------------------------------- #

def _parse_iso(iso_str: str) -> datetime:
    """Parse an ISO-8601 timestamp (as emitted by aerie-cli) to an aware datetime."""
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def iso_to_doy(iso_str: str) -> str:
    """ISO-8601 -> DOY string 'YYYY-DDDThh:mm:ss.ssssss'."""
    return dt_to_doy(_parse_iso(iso_str))


def dt_to_doy(dt: datetime) -> str:
    doy = dt.timetuple().tm_yday
    return (f"{dt.year:04d}-{doy:03d}T"
            f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}.{dt.microsecond:06d}")


def micros_to_extent(us: int) -> str:
    """Microseconds -> 'HH:MM:SS.ssssss'. Hours are NOT capped at 24."""
    if us < 0:
        raise ValueError(f"Negative extent ({us} us); samples out of order or past sim end.")
    total_seconds, micros = divmod(us, 1_000_000)
    hours, rem = divmod(total_seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{micros:06d}"


# --------------------------------------------------------------------------- #
# Activities
# --------------------------------------------------------------------------- #

def convert_activities(activities: list) -> tuple:
    """
    aerie-cli activity records -> SimulationResultsWriter `simulatedActivities`.

    childIds are derived from parent_id back-references so decomposed activities
    keep their hierarchy.
    """
    children: dict = {}
    for a in activities:
        pid = a.get("parent_id")
        if pid is not None:
            children.setdefault(pid, []).append(a["id"])

    simulated = []
    for a in activities:
        attrs = a.get("attributes") or {}
        simulated.append({
            "id": a["id"],
            "type": a["activity_type_name"],
            "directiveId": a.get("directive_id"),
            "parentId": a.get("parent_id"),
            "childIds": sorted(children.get(a["id"], [])),
            "startTime": iso_to_doy(a["start_time"]),
            "duration": _normalize_duration(a["duration"]),
            # Raw serialized values - NO {type,value} wrapping.
            "arguments": attrs.get("arguments", {}),
            "attributes": attrs.get("computedAttributes", {}),
        })

    # No notion of "unfinished" survives the CLI download, so this is always empty.
    return simulated, []


def _normalize_duration(dur: str) -> str:
    """
    aerie-cli emits durations like '00:00:00', '00:00:01', '00:00:16.05703'.
    Duration.fromString expects HH:MM:SS with optional fractional seconds. Pad
    the fractional part to 6 digits and ensure one is present.
    """
    if "." in dur:
        head, frac = dur.split(".", 1)
        frac = (frac + "000000")[:6]
        return f"{head}.{frac}"
    return f"{dur}.000000"


# --------------------------------------------------------------------------- #
# Resources
# --------------------------------------------------------------------------- #

def _classify(samples: list) -> str:
    """Return one of: 'real', 'string', 'boolean', 'series', 'struct'."""
    for p in samples:
        y = p.get("y")
        if y is None:
            continue
        if isinstance(y, bool):
            return "boolean"
        if isinstance(y, (int, float)):
            return "real"
        if isinstance(y, str):
            return "string"
        if isinstance(y, list):
            return "series"
        if isinstance(y, dict):
            return "struct"
    return "string"  # all-null / empty: harmless default


def _schema_for(kind: str, sample_value: Any) -> dict:
    if kind == "real":
        return {"type": "real"}
    if kind == "string":
        return {"type": "string"}
    if kind == "boolean":
        return {"type": "boolean"}
    if kind == "series":
        item = "real"
        if isinstance(sample_value, list) and sample_value:
            v0 = sample_value[0]
            if isinstance(v0, bool):
                item = "boolean"
            elif isinstance(v0, str):
                item = "string"
            elif isinstance(v0, (int, float)):
                item = "real"
        return {"type": "series", "items": {"type": item}}
    if kind == "struct":
        # Without per-field schema we cannot fully describe a struct; fall back to string schema.
        return {"type": "string"}
    return {"type": "string"}


def _real_segments(samples: list) -> list:
    """
    Reverse aerie-cli's real-profile flattening.

    The CLI wrote each original segment {initial, rate} as two points:
        (seg_start, initial) and (seg_end, initial + rate * dt_seconds),
    deduplicating a start point when it equals the previous end point. So each
    consecutive pair of points with x1 > x0 is one segment; recover
        extent  = x1 - x0
        initial = y0
        rate    = (y1 - y0) / ((x1 - x0) / 1e6)     # per SECOND
    Pairs sharing the same x (discontinuities) are skipped as boundaries.
    """
    segs = []
    for i in range(len(samples) - 1):
        x0, y0 = samples[i]["x"], samples[i]["y"]
        x1, y1 = samples[i + 1]["x"], samples[i + 1]["y"]
        if x1 <= x0:
            continue
        extent_us = x1 - x0
        rate = (y1 - y0) / (extent_us / 1_000_000)
        segs.append({
            "extent": micros_to_extent(extent_us),
            "dynamics": {"initial": float(y0), "rate": float(rate)},
        })
    return segs


def _discrete_segments(samples: list, sim_end_us: int) -> list:
    """
    Reverse aerie-cli's discrete-profile flattening into value-held segments.

    A value holds from its x until the x where it next changes. Collapse the point
    list into runs of constant value; each run becomes one segment whose extent
    reaches the start of the next run (or the simulation end for the final run).
    Lists are compared by value, so vector resources collapse correctly.
    """
    changes = []  # list[(x, value)]
    for p in samples:
        x, y = p["x"], p["y"]
        if changes and changes[-1][1] == y:
            continue  # value unchanged - no new boundary
        changes.append((x, y))

    segs = []
    for i, (x, val) in enumerate(changes):
        end = changes[i + 1][0] if i + 1 < len(changes) else sim_end_us
        extent_us = end - x
        if extent_us <= 0:
            continue
        segs.append({"extent": micros_to_extent(extent_us), "dynamics": val})
    return segs


def convert_resources(resources: dict, sim_end_us: int) -> tuple:
    """
    aerie-cli resourceSamples -> (realProfiles, discreteProfiles).

    Real profiles carry {initial, rate} dynamics; everything else (string,
    boolean, series/vector) is a discrete profile whose dynamics is the raw value.
    """
    real_profiles, discrete_profiles = [], []
    resource_samples = resources.get("resourceSamples", {})

    for name in sorted(resource_samples):
        samples = resource_samples[name]
        if not samples:
            continue
        kind = _classify(samples)
        first_val = next((p["y"] for p in samples if p.get("y") is not None), None)

        if kind == "real":
            real_profiles.append({
                "name": name,
                "schema": {"type": "real"},
                "segments": _real_segments(samples),
            })
        else:
            discrete_profiles.append({
                "name": name,
                "schema": _schema_for(kind, first_val),
                "segments": _discrete_segments(samples, sim_end_us),
            })

    return real_profiles, discrete_profiles


# --------------------------------------------------------------------------- #
# Simulation window
# --------------------------------------------------------------------------- #

def infer_window(activities: list, resources: dict) -> tuple:
    """
    Start = earliest activity start_time.
    End   = start + max resource sample offset (resources span the full sim;
            activities may end earlier). Falls back to latest activity end_time.
    """
    if not activities:
        raise ValueError("No activities; cannot infer simulation window.")
    start_dt = min(_parse_iso(a["start_time"]) for a in activities)

    max_offset_us = 0
    for samples in resources.get("resourceSamples", {}).values():
        if samples:
            max_offset_us = max(max_offset_us, max(p["x"] for p in samples))

    if max_offset_us == 0:
        end_dt = max(_parse_iso(a["end_time"]) for a in activities)
    else:
        end_dt = start_dt + timedelta(microseconds=max_offset_us)
    return start_dt, end_dt


# --------------------------------------------------------------------------- #
# Top-level conversion
# --------------------------------------------------------------------------- #

def build_simulation_upload(activities: list, resources: dict) -> dict:
    """
    Convert aerie-cli simulation and resource downloads to the PlanDev
    SimulationResultsWriter upload format.

    Args:
        activities: list returned by AerieClient.get_simulation_results()
        resources:  dict returned by AerieClient.get_resource_samples()

    Returns:
        dict ready to be serialized as JSON and uploaded via uploadSimulationDataset.
    """
    start_dt, end_dt = infer_window(activities, resources)
    sim_end_us = int((end_dt - start_dt).total_seconds() * 1_000_000)

    simulated_activities, unfinished = convert_activities(activities)
    real_profiles, discrete_profiles = convert_resources(resources, sim_end_us)

    return {
        "simulationStartTime": dt_to_doy(start_dt),
        "simulationEndTime": dt_to_doy(end_dt),
        "profiles": {
            "realProfiles": real_profiles,
            "discreteProfiles": discrete_profiles,
        },
        "spans": {
            "simulatedActivities": simulated_activities,
            "unfinishedActivities": unfinished,
        },
    }
