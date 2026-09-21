import json
from pathlib import Path

import pytest

from app.adapters.openaq import OpenAqError, _build_sensor_param_map, extract_reading

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_sensor_param_map_builds_correctly():
    sensor_map = _build_sensor_param_map(_load("openaq_sensors_valid.json"))
    assert sensor_map == {7710: "pm25", 7711: "pm10"}


def test_extract_reading_valid():
    sensor_map = _build_sensor_param_map(_load("openaq_sensors_valid.json"))
    reading = extract_reading(_load("openaq_latest_valid.json"), sensor_map)

    assert reading["aqi"] is None  # OpenAQ never gives an AQI number
    assert reading["pm25"] == 21.0
    assert reading["pm10"] == 38.4
    assert reading["o3"] is None  # not present -- stays null, not 0
    assert reading["source"] == "openaq"
    assert reading["reliability_status"] == "sensor"
    # latest timestamp across matched sensors, not the unmapped sensor 9999's
    assert reading["recorded_at"].isoformat() == "2026-06-17T23:15:00+00:00"


def test_extract_reading_unmapped_sensor_is_skipped_not_errored():
    """sensorsId 9999 has no entry in the sensor map (simulates a pollutant
    OpenAQ tracks that we don't, e.g. bc/nh3) -- it must be silently skipped,
    not crash the whole extraction."""
    sensor_map = _build_sensor_param_map(_load("openaq_sensors_valid.json"))
    reading = extract_reading(_load("openaq_latest_valid.json"), sensor_map)
    # none of our tracked columns should have sensor 9999's value (12.6)
    assert 12.6 not in (reading["pm25"], reading["pm10"], reading["o3"])


def test_extract_reading_empty_results_raises():
    with pytest.raises(OpenAqError):
        extract_reading(_load("openaq_latest_empty.json"), {})


def test_extract_reading_no_matching_sensors_raises():
    """If /sensors returns nothing (or nothing matches), we must raise --
    never silently insert an all-null reading."""
    latest = _load("openaq_latest_valid.json")
    with pytest.raises(OpenAqError):
        extract_reading(latest, {})  # empty map -- nothing matches


def test_extract_reading_negative_value_rejected_not_stored():
    """A negative pollutant concentration is physically impossible -- OpenAQ
    sometimes passes through a raw sentinel like -0.999 instead of a real
    value (observed live from api.openaq.org, station 3459). Must be left
    null, not stored as if it were a real (very low) reading."""
    sensor_map = {7710: "o3"}
    latest = {
        "results": [
            {
                "sensorsId": 7710,
                "value": -0.999,
                "datetime": {"utc": "2026-06-17T23:15:00Z"},
            }
        ]
    }
    reading = extract_reading(latest, sensor_map)
    assert reading["o3"] is None
    # still a valid reading overall -- a bad sensor value doesn't invalidate
    # the whole extraction, it just leaves that one column null
    assert reading["recorded_at"] is not None