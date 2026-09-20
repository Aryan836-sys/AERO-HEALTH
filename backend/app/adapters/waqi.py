"""Day 4: WAQI /feed/ integration.

Fetches real-time AQI data for one station and extracts it into the exact
shape `crud.readings.insert_reading()` expects (aqi_readings columns).

Real data only -- if WAQI's response is malformed, missing, or an error
status, this raises. It never fabricates or estimates a reading.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

load_dotenv()

WAQI_TOKEN = os.environ["WAQI_TOKEN"]
FEED_URL = "https://api.waqi.info/feed/@{uid}/?token={token}"


class WaqiFeedError(Exception):
    """Raised when WAQI's response can't be trusted as a real reading."""


def get_station_feed(station_uid: str) -> dict[str, Any]:
    """Call WAQI's /feed/@{uid}/ and return the raw response dict."""
    url = FEED_URL.format(uid=station_uid, token=WAQI_TOKEN)
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.load(resp)


def extract_reading(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract aqi_readings-shaped fields from a raw WAQI /feed/ response.

    Raises WaqiFeedError on anything that isn't a valid "ok" reading --
    including WAQI's own "-" placeholder for a missing AQI value, since a
    reading with no actual AQI number isn't safe to insert as real data.
    """
    if payload.get("status") != "ok":
        raise WaqiFeedError(f"WAQI feed call failed: {payload}")

    data = payload.get("data")
    if not isinstance(data, dict):
        raise WaqiFeedError(f"WAQI feed returned no station data: {payload}")

    aqi = data.get("aqi")
    if aqi in (None, "-", ""):
        raise WaqiFeedError(f"WAQI feed has no usable AQI value: {data.get('aqi')!r}")

    iaqi = data.get("iaqi", {})

    def _pollutant(key: str) -> float | None:
        entry = iaqi.get(key)
        return entry.get("v") if isinstance(entry, dict) else None

    time_info = data.get("time", {})
    recorded_at_iso = time_info.get("iso")
    if not recorded_at_iso:
        raise WaqiFeedError(f"WAQI feed has no reading timestamp: {time_info!r}")
    recorded_at = datetime.fromisoformat(recorded_at_iso)

    return {
        "aqi": int(aqi),
        "main_pollutant": data.get("dominentpol"),
        "pm25": _pollutant("pm25"),
        "pm10": _pollutant("pm10"),
        "o3": _pollutant("o3"),
        "no2": _pollutant("no2"),
        "so2": _pollutant("so2"),
        "co": _pollutant("co"),
        "temperature": _pollutant("t"),
        "humidity": _pollutant("h"),
        "wind": _pollutant("w"),
        "pressure": _pollutant("p"),
        "owm_aqi_index": None,  # WAQI doesn't provide this -- OpenWeatherMap does (Day 5)
        "source": "waqi",
        "reliability_status": "official",
        "recorded_at": recorded_at,
        "fetched_at": datetime.now(timezone.utc),
    }


def get_station_reading(station_uid: str) -> dict[str, Any]:
    """Fetch + extract in one call -- the function most callers want."""
    return extract_reading(get_station_feed(station_uid))