import json
from pathlib import Path

import pytest

from app.adapters.waqi import WaqiFeedError, extract_reading

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_extract_reading_valid():
    reading = extract_reading(_load("waqi_feed_valid.json"))

    assert reading["aqi"] == 121
    assert reading["main_pollutant"] == "pm25"
    assert reading["pm25"] == 121
    assert reading["pm10"] == 60.2
    assert reading["o3"] == 20.3
    assert reading["temperature"] == 22.4
    assert reading["humidity"] == 55
    assert reading["wind"] == 3.2
    assert reading["pressure"] == 1012.5
    assert reading["source"] == "waqi"
    assert reading["reliability_status"] == "official"
    assert reading["recorded_at"].isoformat() == "2026-09-19T14:00:00+05:45"


def test_extract_reading_error_status_raises():
    with pytest.raises(WaqiFeedError):
        extract_reading(_load("waqi_feed_invalid.json"))


def test_extract_reading_placeholder_aqi_raises():
    """WAQI's own '-' placeholder for a missing AQI must never become a
    fabricated reading -- this must raise, not silently insert garbage."""
    with pytest.raises(WaqiFeedError):
        extract_reading(_load("waqi_feed_no_data.json"))


def test_extract_reading_missing_data_key_raises():
    with pytest.raises(WaqiFeedError):
        extract_reading({"status": "ok"})