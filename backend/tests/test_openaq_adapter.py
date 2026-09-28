import json
from pathlib import Path

import httpx
import respx

from datetime import datetime, timezone

from app.adapters.openaq import (
    get_openaq_location,
    get_openaq_locations,
    get_valley_openaq_locations,
    openaq_station_id,
    openaq_client,
    parse_openaq,
)

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_parse_openaq_official_monitor_skips_ppm_o3_keeps_ugm3_pm25():
    """Embassy Kathmandu: isMonitor=True, o3 reported in ppm (must be
    skipped -- aqi_readings expects µg/m³ and no conversion is specced),
    pm25 reported in µg/m³ (must be kept). Its o3 reading is also a stale
    -0.999 sentinel from over a year ago -- doubly a reason to skip it.
    """
    location = load_fixture("openaq_location_detail_official.json")["results"][0]
    latest = load_fixture("openaq_latest_official.json")["results"]

    reading = parse_openaq(location, latest)

    assert reading.source_station_id == "3459"
    assert reading.reliability_status == "official"
    assert reading.pm25 == 21.0
    assert reading.o3 is None
    # OpenAQ publishes no AQI; it's computed from pm25 (21.0 µg/m³ -> 73).
    assert reading.aqi == 73
    assert reading.main_pollutant == "pm25"


def test_parse_openaq_low_cost_sensor_tagged_sensor_not_official():
    location = load_fixture("openaq_location_detail_sensor.json")["results"][0]
    latest = load_fixture("openaq_latest_sensor.json")["results"]

    reading = parse_openaq(location, latest)

    assert reading.source_station_id == "5509787"
    assert reading.reliability_status == "sensor"
    assert reading.pm25 == 28.0
    assert reading.aqi == 86
    # pm1/relativehumidity/temperature/um003 aren't in NormalizedReading's
    # pollutant set -- must be ignored, not crash.
    assert reading.pm10 is None


@respx.mock
def test_get_openaq_locations_returns_results_with_ismonitor():
    payload = load_fixture("openaq_locations_kathmandu.json")
    respx.get("https://api.openaq.org/v3/locations").mock(
        return_value=httpx.Response(200, json=payload)
    )

    locations = get_openaq_locations(lat=27.70, lon=85.32, radius_m=25000, api_key="fake-key")

    assert len(locations) >= 1
    assert any(loc["isMonitor"] for loc in locations)
    assert any(not loc["isMonitor"] for loc in locations)


@respx.mock
def test_get_openaq_location_sends_api_key_header():
    payload = load_fixture("openaq_location_detail_official.json")
    route = respx.get("https://api.openaq.org/v3/locations/3459").mock(
        return_value=httpx.Response(200, json=payload)
    )

    location = get_openaq_location(location_id=3459, api_key="fake-key")

    assert location["isMonitor"] is True
    assert route.calls[0].request.headers["X-API-Key"] == "fake-key"


@respx.mock
def test_openaq_client_latest_has_no_parameter_field():
    """Documents the real (surprising) shape: /latest gives sensorsId +
    value + datetime only, never the parameter name."""
    payload = load_fixture("openaq_latest_official.json")
    respx.get("https://api.openaq.org/v3/locations/3459/latest").mock(
        return_value=httpx.Response(200, json=payload)
    )

    results = openaq_client(location_id=3459, api_key="fake-key")

    assert all("parameter" not in r for r in results)
    assert all("sensorsId" in r and "value" in r for r in results)


NOW = datetime(2026, 9, 20, 12, 0, tzinfo=timezone.utc)


def _loc(id, lat=27.70, lon=85.32, last="2026-09-20T10:00:00Z", mobile=False):
    return {
        "id": id,
        "isMobile": mobile,
        "coordinates": {"latitude": lat, "longitude": lon},
        "datetimeLast": {"utc": last} if last else None,
    }


@respx.mock
def test_get_valley_openaq_locations_keeps_only_fresh_fixed_in_box():
    results = [
        _loc(1),  # kept
        _loc(2, last="2026-09-18T10:00:00Z"),  # stale (>24h)
        _loc(3, last=None),  # never reported
        _loc(4, mobile=True),  # mobile
        _loc(5, lat=27.90),  # outside the valley box
        _loc(6, lat=27.60, lon=85.55),  # on the box edge -> kept
    ]
    respx.get("https://api.openaq.org/v3/locations").mock(
        return_value=httpx.Response(200, json={"results": results})
    )

    kept = get_valley_openaq_locations("key", now=NOW)

    assert [loc["id"] for loc in kept] == [1, 6]


def test_openaq_station_id_is_namespaced():
    assert openaq_station_id(5509787) == "openaq:5509787"
