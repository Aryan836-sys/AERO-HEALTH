from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app

client = TestClient(app)
app.dependency_overrides[get_db] = lambda: MagicMock()


def _fake_reading(aqi=75):
    r = MagicMock()
    r.id = 1
    r.location_id = 1
    r.aqi = aqi
    r.main_pollutant = "pm25"
    r.pm25, r.pm10, r.o3, r.no2, r.so2, r.co = 75.0, None, None, None, None, None
    r.temperature = r.humidity = r.wind = r.pressure = None
    r.owm_aqi_index = None
    r.source = "openaq"
    r.reliability_status = "sensor"
    r.recorded_at = datetime.now(timezone.utc)
    r.fetched_at = datetime.now(timezone.utc)
    return r


def test_get_readings_404s_for_an_unknown_location():
    with patch("app.routers.readings.locations_crud.get_location", return_value=None):
        response = client.get("/readings/999")
    assert response.status_code == 404


def test_get_readings_defaults_to_24h():
    with patch("app.routers.readings.locations_crud.get_location", return_value=MagicMock()), \
         patch("app.routers.readings.readings_crud.get_readings", return_value=[_fake_reading()]) as mock_get:
        response = client.get("/readings/1")
    assert response.status_code == 200
    assert len(response.json()) == 1
    # confirm the "since" window matches roughly 24h back, not 7d/30d
    since_arg = mock_get.call_args[0][2]
    delta = datetime.now(timezone.utc) - since_arg
    assert 23.9 < delta.total_seconds() / 3600 < 24.1


def test_get_readings_accepts_7d_and_30d():
    with patch("app.routers.readings.locations_crud.get_location", return_value=MagicMock()), \
         patch("app.routers.readings.readings_crud.get_readings", return_value=[]):
        assert client.get("/readings/1?range=7d").status_code == 200
        assert client.get("/readings/1?range=30d").status_code == 200


def test_get_readings_rejects_an_invalid_range():
    with patch("app.routers.readings.locations_crud.get_location", return_value=MagicMock()):
        response = client.get("/readings/1?range=bogus")
    assert response.status_code == 422