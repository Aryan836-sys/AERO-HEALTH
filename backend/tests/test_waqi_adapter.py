import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
import respx

from app.adapters.waqi import get_valley_stations, parse_waqi

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_parse_waqi_normal_station():
    bounds = load_fixture("waqi_bounds_kathmandu.json")
    station = next(s for s in bounds["data"] if s["uid"] == 9285)

    reading = parse_waqi(station, fetched_at=datetime.now(timezone.utc))

    assert reading.source_station_id == "9285"
    assert reading.aqi == 56
    assert reading.source == "waqi"
    assert reading.reliability_status == "official"
    assert reading.recorded_at.isoformat() == "2026-09-16T20:53:00+09:00"
    # Bounds/search never gives a pollutant breakdown for these stations
    # (see the module docstring) -- every pollutant field must stay None.
    assert reading.pm25 is None
    assert reading.main_pollutant is None


def test_parse_waqi_station_with_no_current_reading():
    """WAQI reports "-" for a stale/offline station -- must yield None,
    never a fabricated 0 or a crash."""
    bounds = load_fixture("waqi_bounds_kathmandu.json")
    station = next(s for s in bounds["data"] if s["uid"] == 14868)
    assert station["aqi"] == "-"

    reading = parse_waqi(station, fetched_at=datetime.now(timezone.utc))

    assert reading.aqi is None
    assert reading.source_station_id == "14868"


def test_parse_waqi_all_real_fixture_stations_parse_without_error():
    bounds = load_fixture("waqi_bounds_kathmandu.json")
    for station in bounds["data"]:
        parse_waqi(station, fetched_at=datetime.now(timezone.utc))


@respx.mock
def test_get_valley_stations_returns_raw_station_list():
    bounds = load_fixture("waqi_bounds_kathmandu.json")
    respx.get("https://api.waqi.info/map/bounds/").mock(
        return_value=httpx.Response(200, json=bounds)
    )

    stations = get_valley_stations(token="fake-token")

    assert len(stations) == 7
    assert {s["uid"] for s in stations} == {9285, 9287, 10493, 10495, 13592, 14866, 14868}


@respx.mock
def test_get_valley_stations_raises_on_non_ok_status():
    """Real, live data only -- a failed WAQI call must raise, never fall
    back to fabricated station data."""
    respx.get("https://api.waqi.info/map/bounds/").mock(
        return_value=httpx.Response(200, json={"status": "nope", "data": "can not connect"})
    )

    with pytest.raises(RuntimeError, match="WAQI bounds call failed"):
        get_valley_stations(token="fake-token")
