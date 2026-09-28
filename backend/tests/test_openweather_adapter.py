import json
from pathlib import Path

import httpx
import respx

from app.adapters.openweather import (
    openweather_client,
    openweather_weather_client,
    parse_openweather,
)

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_parse_openweather_keeps_owm_index_separate_from_aqi():
    pollution = load_fixture("openweather_air_pollution_kathmandu.json")

    reading = parse_openweather(pollution, source_station_id=None)

    assert reading.owm_aqi_index == 5
    assert reading.aqi is None  # never blended, per the module docstring
    assert reading.pm25 == 79.57
    assert reading.source == "openweathermap"
    assert reading.reliability_status == "modelled"


def test_parse_openweather_merges_weather_fields():
    pollution = load_fixture("openweather_air_pollution_kathmandu.json")
    weather = load_fixture("openweather_weather_kathmandu.json")

    reading = parse_openweather(pollution, weather_raw=weather)

    assert reading.temperature == 22.15
    assert reading.humidity == 83
    assert reading.pressure == 1014
    assert reading.wind == 1.03


def test_parse_openweather_without_weather_leaves_weather_fields_none():
    pollution = load_fixture("openweather_air_pollution_kathmandu.json")

    reading = parse_openweather(pollution)

    assert reading.temperature is None
    assert reading.humidity is None


@respx.mock
def test_openweather_client_calls_air_pollution_endpoint():
    payload = load_fixture("openweather_air_pollution_kathmandu.json")
    respx.get("https://api.openweathermap.org/data/2.5/air_pollution").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = openweather_client(lat=27.7172, lon=85.324, api_key="fake-key")

    assert result["list"][0]["main"]["aqi"] == 5


@respx.mock
def test_openweather_weather_client_calls_weather_endpoint():
    payload = load_fixture("openweather_weather_kathmandu.json")
    respx.get("https://api.openweathermap.org/data/2.5/weather").mock(
        return_value=httpx.Response(200, json=payload)
    )

    result = openweather_weather_client(lat=27.7172, lon=85.324, api_key="fake-key")

    assert result["main"]["temp"] == 22.15
