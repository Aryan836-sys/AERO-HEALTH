from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app

client = TestClient(app)
app.dependency_overrides[get_db] = lambda: MagicMock()


def _fake_location(location_id=1, area_name="Pulchowk, Kathmandu, Nepal", district="Lalitpur"):
    loc = MagicMock()
    loc.id = location_id
    loc.area_name = area_name
    loc.district = district
    loc.geometry = MagicMock()
    return loc


def _fake_point(lat=27.68, lng=85.32):
    point = MagicMock()
    point.y = lat
    point.x = lng
    return point


def test_list_locations_returns_every_location_shaped_for_the_frontend():
    with patch("app.routers.locations.locations_crud.list_locations", return_value=[_fake_location()]), \
         patch("app.routers.locations.readings_crud.get_latest_reading", return_value=None), \
         patch("app.schemas.frontend_area.to_shape", return_value=_fake_point()):
        response = client.get("/locations")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Pulchowk, Kathmandu, Nepal"
    assert body[0]["reading"] is None


def test_get_location_404s_for_an_unknown_id():
    with patch("app.routers.locations.locations_crud.get_location", return_value=None):
        response = client.get("/locations/999")
    assert response.status_code == 404


def test_get_location_returns_the_location_with_its_latest_reading():
    fake_reading = MagicMock()
    fake_reading.aqi = 88
    fake_reading.main_pollutant = "pm25"
    fake_reading.pm25 = 88.0
    fake_reading.pm10 = None
    fake_reading.o3 = None
    fake_reading.no2 = None
    fake_reading.so2 = None
    fake_reading.co = None
    fake_reading.source = "openaq"
    fake_reading.reliability_status = "sensor"
    fake_reading.recorded_at.isoformat.return_value = "2026-09-23T00:00:00+00:00"
    fake_reading.temperature = None
    fake_reading.humidity = None
    fake_reading.wind = None

    with patch("app.routers.locations.locations_crud.get_location", return_value=_fake_location()), \
         patch("app.routers.locations.readings_crud.get_latest_reading", return_value=fake_reading), \
         patch("app.schemas.frontend_area.to_shape", return_value=_fake_point()):
        response = client.get("/locations/1")
    assert response.status_code == 200
    body = response.json()
    assert body["reading"]["aqi"] == 88