"""OpenAQ adapter (fallback source) -- data-adapter-build-guide.md Phase 6.

Real-data corrections made after registering a key and inspecting actual
responses (the original version of this file was written against OpenAQ's
public docs and got two things wrong):

1. `/v3/locations/{id}/latest` does NOT include the parameter name or
   units -- only `sensorsId`, `value`, `datetime`. The parameter/units
   live on the *location* (`/v3/locations/{id}` -> `sensors[].parameter`),
   so parsing needs both responses, joined on `sensorsId`.
2. Kathmandu-valley OpenAQ locations are a mix of real government
   reference monitors (`isMonitor: true`, e.g. "Embassy Kathmandu", fed by
   AirNow) and ~50 low-cost community sensors ("GD Labs" / AirGradient
   units, `isMonitor: false`). These are NOT equally reliable --
   `reliability_status` must reflect `isMonitor`, not be hardcoded.

Also real: the AirNow-fed monitor reports O3 in **ppm**, while every
low-cost sensor reports PM2.5 in **µg/m³**. Blending those into the same
column without conversion would silently corrupt the value by ~1000x, so
`parse_openaq` only maps a field when the reported units match what
`aqi_readings` expects (µg/m³) -- anything else is skipped and logged, not
guessed at or converted (no EPA conversion factor is specced anywhere).
A stale/error sentinel (negative concentration, e.g. -0.999) is skipped
the same way -- concentrations can't be negative.
"""
import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.adapters.waqi import VALLEY_BOUNDS
from app.schemas import NormalizedReading
from app.services.aqi import pm25_to_aqi

logger = logging.getLogger(__name__)

# OpenAQ parameter name -> (NormalizedReading field, expected units).
# Only these are mapped; anything else (pm1, relativehumidity, um003, ...)
# is intentionally ignored.
_PARAMETER_FIELD = {
    "pm25": ("pm25", "µg/m³"),
    "pm10": ("pm10", "µg/m³"),
    "o3": ("o3", "µg/m³"),
    "no2": ("no2", "µg/m³"),
    "so2": ("so2", "µg/m³"),
    "co": ("co", "µg/m³"),
}


def get_openaq_locations(
    lat: float, lon: float, radius_m: int, api_key: str, timeout: float = 15.0
) -> list[dict]:
    """Discover OpenAQ locations within `radius_m` of (lat, lon). Each
    result includes `isMonitor`, coordinates, and its `sensors` list
    (id -> parameter/units) -- everything `parse_openaq` needs, without a
    second call, when the caller already has this from discovery.
    """
    url = "https://api.openaq.org/v3/locations"
    response = httpx.get(
        url,
        params={"coordinates": f"{lat},{lon}", "radius": radius_m, "limit": 100},
        headers={"X-API-Key": api_key},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["results"]


# Circle covering the whole valley box (VALLEY_BOUNDS); results are then
# clipped to the box itself.
VALLEY_CENTER = (27.70, 85.375)
VALLEY_RADIUS_M = 25000
# A sensor silent for longer than this is skipped -- a marker with no
# current data is worse than no marker.
MAX_STATION_AGE = timedelta(hours=24)


def openaq_station_id(openaq_id: int) -> str:
    """Namespaced `locations.source_station_id`, so an OpenAQ id can never
    collide with a WAQI uid."""
    return f"openaq:{openaq_id}"


def get_valley_openaq_locations(
    api_key: str, now: datetime | None = None, timeout: float = 15.0
) -> list[dict]:
    """Fixed (non-mobile) OpenAQ locations inside the valley box that have
    reported within MAX_STATION_AGE."""
    now = now or datetime.now(timezone.utc)
    sw_lat, sw_lng, ne_lat, ne_lng = (float(v) for v in VALLEY_BOUNDS.split(","))

    stations = []
    for loc in get_openaq_locations(*VALLEY_CENTER, VALLEY_RADIUS_M, api_key, timeout):
        coords = loc["coordinates"]
        last = (loc.get("datetimeLast") or {}).get("utc")
        if loc.get("isMobile") or not last:
            continue
        if not (
            sw_lat <= coords["latitude"] <= ne_lat
            and sw_lng <= coords["longitude"] <= ne_lng
        ):
            continue
        if now - datetime.fromisoformat(last.replace("Z", "+00:00")) > MAX_STATION_AGE:
            continue
        stations.append(loc)
    return stations


def get_openaq_location(location_id: int, api_key: str, timeout: float = 15.0) -> dict:
    """Fetch one location's detail (isMonitor + sensor->parameter map)."""
    url = f"https://api.openaq.org/v3/locations/{location_id}"
    response = httpx.get(url, headers={"X-API-Key": api_key}, timeout=timeout)
    response.raise_for_status()
    return response.json()["results"][0]


def openaq_client(location_id: int, api_key: str, timeout: float = 15.0) -> list[dict]:
    """Call GET /v3/locations/{id}/latest. Each result is `{sensorsId,
    value, datetime, coordinates}` -- no parameter name, must be joined
    against the location's `sensors` list to mean anything.
    """
    url = f"https://api.openaq.org/v3/locations/{location_id}/latest"
    response = httpx.get(url, headers={"X-API-Key": api_key}, timeout=timeout)
    response.raise_for_status()
    return response.json()["results"]


def parse_openaq(
    location: dict, latest_results: list[dict], fetched_at: datetime | None = None
) -> NormalizedReading:
    """Join a location's sensor map against its /latest values into one
    NormalizedReading. Unknown parameters, unit mismatches, and negative
    sentinel values are skipped (logged), not guessed at.
    """
    sensor_parameter = {s["id"]: s["parameter"] for s in location["sensors"]}

    fields: dict = {}
    recorded_at = None

    for result in latest_results:
        parameter = sensor_parameter.get(result["sensorsId"])
        if parameter is None:
            continue

        mapping = _PARAMETER_FIELD.get(parameter["name"])
        if mapping is None:
            continue
        field, expected_units = mapping

        if parameter["units"] != expected_units:
            logger.warning(
                "OpenAQ location %s sensor %s reports %s in %r, expected %r; skipping",
                location["id"],
                result["sensorsId"],
                parameter["name"],
                parameter["units"],
                expected_units,
            )
            continue

        value = result["value"]
        if value < 0:
            logger.warning(
                "OpenAQ location %s sensor %s reported a negative value (%s), "
                "treating as no data",
                location["id"],
                result["sensorsId"],
                value,
            )
            continue

        fields[field] = value

        candidate = datetime.fromisoformat(result["datetime"]["utc"].replace("Z", "+00:00"))
        if recorded_at is None or candidate > recorded_at:
            recorded_at = candidate

    if recorded_at is None:
        raise ValueError(
            f"OpenAQ location {location['id']}: no usable sensor values in latest_results"
        )

    # OpenAQ never publishes an AQI; this one is computed from PM2.5.
    aqi = pm25_to_aqi(fields.get("pm25"))

    return NormalizedReading(
        source_station_id=str(location["id"]),
        aqi=aqi,
        main_pollutant="pm25" if aqi is not None else None,
        source="openaq",
        reliability_status="official" if location["isMonitor"] else "sensor",
        recorded_at=recorded_at,
        fetched_at=fetched_at or datetime.now(timezone.utc),
        **fields,
    )
