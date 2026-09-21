"""Day 5: OpenWeatherMap integration.

Two OWM endpoints combined into one reading:
- Air Pollution API: pollutant concentrations + OWM's own 1-5 AQI index
- Current Weather API: temperature, humidity, wind, pressure

Scale-safety rule (see models/aqi_reading.py): OWM's 1-5 index is a
DIFFERENT scale from WAQI's 0-500 US EPA `aqi` column. It only ever goes
into `owm_aqi_index`, never into `aqi`. Never blend the two.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv

from app.adapters.normalizer import normalize_reading

load_dotenv()

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
AIR_POLLUTION_URL = (
    "https://api.openweathermap.org/data/2.5/air_pollution"
    "?lat={lat}&lon={lon}&appid={key}"
)
WEATHER_URL = (
    "https://api.openweathermap.org/data/2.5/weather"
    "?lat={lat}&lon={lon}&units=metric&appid={key}"
)


class OpenWeatherError(Exception):
    """Raised when OWM's response can't be trusted as a real reading."""


def _fetch_json(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=15) as resp:
        return json.load(resp)


def get_air_pollution(lat: float, lon: float) -> dict[str, Any]:
    return _fetch_json(AIR_POLLUTION_URL.format(lat=lat, lon=lon, key=OPENWEATHER_API_KEY))


def get_weather(lat: float, lon: float) -> dict[str, Any]:
    return _fetch_json(WEATHER_URL.format(lat=lat, lon=lon, key=OPENWEATHER_API_KEY))


def extract_reading(pollution_payload: dict[str, Any], weather_payload: dict[str, Any]) -> dict[str, Any]:
    """Combine both OWM responses into one aqi_readings-shaped dict."""
    pollution_list = pollution_payload.get("list")
    if not pollution_list:
        raise OpenWeatherError(f"OWM air_pollution returned no data: {pollution_payload}")

    entry = pollution_list[0]
    owm_aqi = entry.get("main", {}).get("aqi")
    if owm_aqi not in (1, 2, 3, 4, 5):
        raise OpenWeatherError(f"OWM air_pollution has an invalid aqi index: {owm_aqi!r}")

    components = entry.get("components", {})
    dt = entry.get("dt")
    if not dt:
        raise OpenWeatherError(f"OWM air_pollution has no timestamp: {entry!r}")
    recorded_at = datetime.fromtimestamp(dt, tz=timezone.utc)

    weather_main = weather_payload.get("main")
    if not isinstance(weather_main, dict):
        raise OpenWeatherError(f"OWM weather returned no 'main' block: {weather_payload}")

    return {
        "aqi": None,  # never put OWM's 1-5 index here -- see module docstring
        "main_pollutant": None,
        "pm25": components.get("pm2_5"),
        "pm10": components.get("pm10"),
        "o3": components.get("o3"),
        "no2": components.get("no2"),
        "so2": components.get("so2"),
        "co": components.get("co"),
        "temperature": weather_main.get("temp"),
        "humidity": weather_main.get("humidity"),
        "wind": weather_payload.get("wind", {}).get("speed"),
        "pressure": weather_main.get("pressure"),
        "owm_aqi_index": owm_aqi,
        "source": "openweathermap",
        "reliability_status": "modelled",  # OWM's pollution data is model-based, not a ground sensor
        "recorded_at": recorded_at,
        "fetched_at": datetime.now(timezone.utc),
    }


def get_location_reading(lat: float, lon: float) -> dict[str, Any]:
    return normalize_reading(extract_reading(get_air_pollution(lat, lon), get_weather(lat, lon)))
