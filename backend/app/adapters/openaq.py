"""Day 5: OpenAQ integration.

OpenAQ's v3 /latest endpoint only returns `sensorsId` + `value` + `datetime`
-- it does NOT tell you which pollutant each sensor measures (confirmed
against OpenAQ's own docs, and against a real API call that returned no
`parameter` field at all). To know that, you need a separate call to
/v3/locations/{id}/sensors, which maps each sensorsId to a parameter name.

So every real reading takes two calls: get_location_sensors() +
get_latest_measurements(), combined by extract_reading().

OpenAQ gives real sensor *concentrations* (µg/m³), never a computed AQI --
that's WAQI's job (or our own EPA-formula computation, not built yet). So
`aqi` and `main_pollutant` are always None here. Never fabricate them.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

from app.adapters.normalizer import normalize_reading

load_dotenv()

OPENAQ_API_KEY = os.environ.get("OPENAQ_API_KEY", "")
LATEST_URL = "https://api.openaq.org/v3/locations/{location_id}/latest"
SENSORS_URL = "https://api.openaq.org/v3/locations/{location_id}/sensors"

_PARAM_TO_COLUMN = {
    "pm25": "pm25",
    "pm10": "pm10",
    "o3": "o3",
    "no2": "no2",
    "so2": "so2",
    "co": "co",
}


class OpenAqError(Exception):
    """Raised when OpenAQ's response can't be trusted as a real reading."""


def _fetch(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"X-API-Key": OPENAQ_API_KEY})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)


def get_location_sensors(location_id: str) -> dict[str, Any]:
    return _fetch(SENSORS_URL.format(location_id=location_id))


def get_latest_measurements(location_id: str) -> dict[str, Any]:
    return _fetch(LATEST_URL.format(location_id=location_id))


def _build_sensor_param_map(sensors_payload: dict[str, Any]) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for sensor in sensors_payload.get("results", []):
        sensor_id = sensor.get("id")
        param_name = sensor.get("parameter", {}).get("name")
        if sensor_id is not None and param_name is not None:
            mapping[sensor_id] = param_name
    return mapping


def extract_reading(
    latest_payload: dict[str, Any], sensor_param_map: dict[int, str]
) -> dict[str, Any]:
    results = latest_payload.get("results")
    if not results:
        raise OpenAqError(f"OpenAQ returned no measurements: {latest_payload}")

    fields: dict[str, Any] = {
        "aqi": None,
        "main_pollutant": None,
        "pm25": None,
        "pm10": None,
        "o3": None,
        "no2": None,
        "so2": None,
        "co": None,
        "owm_aqi_index": None,
        "source": "openaq",
        "reliability_status": "sensor",
    }

    latest_time = None
    matched_any = False

    for result in results:
        sensor_id = result.get("sensorsId")
        param_name = sensor_param_map.get(sensor_id)
        column = _PARAM_TO_COLUMN.get(param_name)
        if column is None:
            continue

        matched_any = True  # a known, tracked sensor -- even if its value gets rejected below

        value = result.get("value")
        if value is not None and value >= 0:
            fields[column] = value
        elif value is not None and value < 0:
            # OpenAQ occasionally passes through a sensor's raw error/missing
            # sentinel (observed: -0.999) instead of a real concentration.
            # A negative pollutant concentration is physically impossible --
            # never store it as if it were real data. Leave the column null.
            pass

        ts = result.get("datetime", {}).get("utc")
        if ts:
            parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if latest_time is None or parsed > latest_time:
                latest_time = parsed

    if not matched_any or latest_time is None:
        raise OpenAqError(
            f"No results matched a tracked pollutant sensor. "
            f"sensor_param_map={sensor_param_map}, results={results}"
        )

    fields["recorded_at"] = latest_time
    fields["fetched_at"] = datetime.now(timezone.utc)
    return fields


def get_location_reading(location_id: str) -> dict[str, Any]:
    sensor_param_map = _build_sensor_param_map(get_location_sensors(location_id))
    latest = get_latest_measurements(location_id)
    return normalize_reading(extract_reading(latest, sensor_param_map))