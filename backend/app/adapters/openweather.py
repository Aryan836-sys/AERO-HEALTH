"""OpenWeatherMap adapter (weather + modelled gap-fill) --
data-adapter-build-guide.md Phase 7.

NOTE: no OWM key is registered yet, so this is built and tested against
fixtures modeled on OWM's public docs
(tests/fixtures/openweather_*_EXAMPLE.json), not a live capture. Swap in
real responses once the key lands.

Use this for the "no station nearby" case -- clearly a modelled estimate
(reliability_status='modelled') -- and for the weather layer on real
stations. `main.aqi` is OWM's own 1-5 index: it goes into `owm_aqi_index`
and must NEVER be written into `aqi`, which is the US EPA 0-500 scale.
"""
from datetime import datetime, timezone

import httpx

from app.schemas import NormalizedReading

_COMPONENT_FIELD = {
    "pm2_5": "pm25",
    "pm10": "pm10",
    "o3": "o3",
    "no2": "no2",
    "so2": "so2",
    "co": "co",
}


def openweather_client(lat: float, lon: float, api_key: str, timeout: float = 15.0) -> dict:
    """Call /air_pollution for (lat, lon) and return the raw payload."""
    url = "https://api.openweathermap.org/data/2.5/air_pollution"
    response = httpx.get(
        url, params={"lat": lat, "lon": lon, "appid": api_key}, timeout=timeout
    )
    response.raise_for_status()
    return response.json()


def openweather_weather_client(lat: float, lon: float, api_key: str, timeout: float = 15.0) -> dict:
    """Call /weather for (lat, lon) and return the raw payload."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    response = httpx.get(
        url,
        params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def parse_openweather(
    pollution_raw: dict,
    weather_raw: dict | None = None,
    source_station_id: str | None = None,
    fetched_at: datetime | None = None,
) -> NormalizedReading:
    """Map one /air_pollution entry (+ optional /weather) to a
    NormalizedReading, tagged as a modelled estimate.
    """
    entry = pollution_raw["list"][0]
    components = entry["components"]
    fields = {
        field: components[key]
        for key, field in _COMPONENT_FIELD.items()
        if key in components
    }

    if weather_raw is not None:
        main = weather_raw.get("main", {})
        if "temp" in main:
            fields["temperature"] = main["temp"]
        if "humidity" in main:
            fields["humidity"] = main["humidity"]
        if "pressure" in main:
            fields["pressure"] = main["pressure"]
        wind = weather_raw.get("wind", {})
        if "speed" in wind:
            fields["wind"] = wind["speed"]

    recorded_at = datetime.fromtimestamp(entry["dt"], tz=timezone.utc)

    return NormalizedReading(
        source_station_id=source_station_id,
        aqi=None,
        owm_aqi_index=entry["main"]["aqi"],
        source="openweathermap",
        reliability_status="modelled",
        recorded_at=recorded_at,
        fetched_at=fetched_at or datetime.now(timezone.utc),
        **fields,
    )
