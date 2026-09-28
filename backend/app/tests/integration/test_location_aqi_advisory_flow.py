"""Day 10: "Test location -> AQI -> advisory flow" from the work plan --
a real HTTP call through /locations/{id} and a real HTTP call through
/advisory/{id}, both backed by the SAME underlying reading, asserting
they agree with each other. Only the database layer is mocked (the
crud.get_location / crud.get_latest_reading boundary); everything above
that -- FastAPI routing, Pydantic validation, FrontendArea's shaping,
advisory_engine's real AQI-category logic -- runs for real.
"""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app

client = TestClient(app)
app.dependency_overrides[get_db] = lambda: MagicMock()


def _fake_location(location_id=1):
    loc = MagicMock()
    loc.id = location_id
    loc.area_name = "Pulchowk, Kathmandu, Nepal"
    loc.district = "Lalitpur"
    loc.geometry = MagicMock()
    return loc


def _fake_point():
    p = MagicMock()
    p.y, p.x = 27.68, 85.32
    return p


def _fake_reading(aqi=160):
    r = MagicMock()
    r.aqi = aqi
    r.main_pollutant = "pm25"
    r.pm25 = 100.0
    r.pm10 = r.o3 = r.no2 = r.so2 = r.co = None
    r.temperature = r.humidity = r.wind = None
    r.source = "openaq"
    r.reliability_status = "sensor"
    r.recorded_at.isoformat.return_value = "2026-09-23T00:00:00+00:00"
    return r


def test_location_and_advisory_endpoints_agree_on_the_same_aqi():
    reading = _fake_reading(aqi=160)
    location = _fake_location()

    with patch("app.routers.locations.locations_crud.get_location", return_value=location), \
         patch("app.routers.locations.readings_crud.get_latest_reading", return_value=reading), \
         patch("app.routers.advisory.get_location", return_value=location), \
         patch("app.routers.advisory.get_latest_reading", return_value=reading), \
         patch("app.schemas.frontend_area.to_shape", return_value=_fake_point()):
        location_response = client.get("/locations/1")
        advisory_response = client.get("/advisory/1")

    assert location_response.status_code == 200
    assert advisory_response.status_code == 200

    assert location_response.json()["reading"]["aqi"] == 160
    assert advisory_response.json()["aqi"] == 160
    # aqi 160 -> "Unhealthy" (151-200), the real advisory_engine logic,
    # not a mock -- proves the whole chain, not just each endpoint alone
    assert advisory_response.json()["aqi_category"] == "Unhealthy"
    assert advisory_response.json()["personalized"] is False


def test_a_location_with_no_reading_yet_is_null_on_locations_but_404_on_advisory():
    """The two endpoints have different, both-correct behaviors for
    "nothing cached yet": /locations shows reading: null (it's still a
    valid location to display), /advisory 404s (there's genuinely
    nothing to advise on) -- confirming neither silently fabricates
    data to paper over the gap."""
    location = _fake_location()

    with patch("app.routers.locations.locations_crud.get_location", return_value=location), \
         patch("app.routers.locations.readings_crud.get_latest_reading", return_value=None), \
         patch("app.routers.advisory.get_location", return_value=location), \
         patch("app.routers.advisory.get_latest_reading", return_value=None), \
         patch("app.schemas.frontend_area.to_shape", return_value=_fake_point()):
        location_response = client.get("/locations/1")
        advisory_response = client.get("/advisory/1")

    assert location_response.status_code == 200
    assert location_response.json()["reading"] is None
    assert advisory_response.status_code == 404