from datetime import datetime, timezone
from unittest.mock import patch

from app.adapters.waqi import WaqiFeedError
from app.adapters.openweather import OpenWeatherError
from app.jobs.cache_readings import run_once


def _fake_waqi_fields(aqi=88):
    return {
        "aqi": aqi, "main_pollutant": "pm25", "pm25": 88.0, "pm10": None,
        "o3": None, "no2": None, "so2": None, "co": None,
        "owm_aqi_index": None, "source": "waqi", "reliability_status": "official",
        "recorded_at": datetime.now(timezone.utc), "fetched_at": datetime.now(timezone.utc),
    }


def _fake_owm_fields():
    return {
        "aqi": None, "main_pollutant": None, "pm25": 50.0, "pm10": None,
        "o3": None, "no2": None, "so2": None, "co": None,
        "temperature": 22.0, "humidity": 50, "wind": 2.0, "pressure": 1010,
        "owm_aqi_index": 3, "source": "openweathermap", "reliability_status": "modelled",
        "recorded_at": datetime.now(timezone.utc), "fetched_at": datetime.now(timezone.utc),
    }


def test_run_once_inserts_both_sources_for_each_location():
    with patch("app.jobs.cache_readings.get_station_reading", return_value=_fake_waqi_fields()), \
         patch("app.jobs.cache_readings.get_owm_reading", return_value=_fake_owm_fields()):
        stats = run_once()

    assert stats["waqi_inserted"] > 0
    assert stats["owm_inserted"] > 0
    assert stats["waqi_skipped"] == 0
    assert stats["owm_skipped"] == 0


def test_run_once_isolates_waqi_failure_from_owm():
    """One source failing for a location must not block the other source
    for that same location, or any source for any other location."""
    with patch("app.jobs.cache_readings.get_station_reading", side_effect=WaqiFeedError("boom")), \
         patch("app.jobs.cache_readings.get_owm_reading", return_value=_fake_owm_fields()):
        stats = run_once()

    assert stats["waqi_inserted"] == 0
    assert stats["waqi_skipped"] > 0
    assert stats["owm_inserted"] > 0  # OWM still ran despite WAQI failing every time


def test_run_once_isolates_owm_failure_from_waqi():
    with patch("app.jobs.cache_readings.get_station_reading", return_value=_fake_waqi_fields()), \
         patch("app.jobs.cache_readings.get_owm_reading", side_effect=OpenWeatherError("boom")):
        stats = run_once()

    assert stats["waqi_inserted"] > 0
    assert stats["owm_inserted"] == 0
    assert stats["owm_skipped"] > 0


def test_run_once_one_bad_location_does_not_stop_others():
    """If WAQI fails for every call, every location should still be
    attempted (skipped count == number of locations, not a crash)."""
    with patch("app.jobs.cache_readings.get_station_reading", side_effect=WaqiFeedError("boom")), \
         patch("app.jobs.cache_readings.get_owm_reading", side_effect=OpenWeatherError("boom")):
        stats = run_once()

    assert stats["waqi_skipped"] == stats["owm_skipped"]
    assert stats["waqi_skipped"] > 0
