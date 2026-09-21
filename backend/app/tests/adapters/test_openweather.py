import json
from pathlib import Path

import pytest

from app.adapters.openweather import OpenWeatherError, extract_reading

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_extract_reading_valid():
    pollution = _load("openweather_pollution_valid.json")
    weather = _load("openweather_weather_valid.json")
    reading = extract_reading(pollution, weather)

    assert reading["aqi"] is None  # never put OWM's 1-5 index here
    assert reading["owm_aqi_index"] == 4
    assert reading["pm25"] == 95.1
    assert reading["pm10"] == 130.4
    assert reading["temperature"] == 24.6
    assert reading["humidity"] == 48
    assert reading["wind"] == 2.6
    assert reading["pressure"] == 1013
    assert reading["source"] == "openweathermap"
    assert reading["reliability_status"] == "modelled"


def test_extract_reading_bad_aqi_index_raises():
    bad_pollution = {"list": [{"main": {"aqi": 99}, "components": {}, "dt": 1758290400}]}
    weather = _load("openweather_weather_valid.json")
    with pytest.raises(OpenWeatherError):
        extract_reading(bad_pollution, weather)


def test_extract_reading_no_list_raises():
    weather = _load("openweather_weather_valid.json")
    with pytest.raises(OpenWeatherError):
        extract_reading({"list": []}, weather)
