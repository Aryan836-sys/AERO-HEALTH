from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user_optional
from app.database import get_db
from app.main import app

client = TestClient(app)
app.dependency_overrides[get_db] = lambda: MagicMock()


def _fake_reading(aqi=75):
    reading = MagicMock()
    reading.aqi = aqi
    return reading


def _fake_location(location_id=1):
    loc = MagicMock()
    loc.id = location_id
    return loc


def test_advisory_404s_for_an_unknown_location():
    app.dependency_overrides[get_current_user_optional] = lambda: None
    with patch("app.routers.advisory.get_location", return_value=None):
        response = client.get("/advisory/999")
    assert response.status_code == 404
    app.dependency_overrides.pop(get_current_user_optional, None)


def test_advisory_404s_when_theres_no_cached_reading_yet():
    app.dependency_overrides[get_current_user_optional] = lambda: None
    with patch("app.routers.advisory.get_location", return_value=_fake_location()), \
         patch("app.routers.advisory.get_latest_reading", return_value=None):
        response = client.get("/advisory/1")
    assert response.status_code == 404
    app.dependency_overrides.pop(get_current_user_optional, None)


def test_advisory_works_for_a_guest_with_no_profile():
    """Being logged out must not block getting an advisory -- only
    personalization requires being logged in."""
    app.dependency_overrides[get_current_user_optional] = lambda: None
    with patch("app.routers.advisory.get_location", return_value=_fake_location()), \
         patch("app.routers.advisory.get_latest_reading", return_value=_fake_reading(aqi=75)):
        response = client.get("/advisory/1")
    assert response.status_code == 200
    body = response.json()
    assert body["aqi"] == 75
    assert body["aqi_category"] == "Moderate"
    assert body["personalized"] is False
    assert "disclaimer" in body and len(body["disclaimer"]) > 0
    app.dependency_overrides.pop(get_current_user_optional, None)


def test_advisory_is_personalized_for_a_logged_in_user_with_a_profile():
    fake_user = MagicMock()
    fake_user.id = 1
    fake_profile = MagicMock()
    fake_profile.asthma = True
    fake_profile.respiratory_condition = False
    fake_profile.heart_condition = False
    fake_profile.pregnancy_status = False
    fake_profile.outdoor_worker = False
    fake_profile.age_group = None

    app.dependency_overrides[get_current_user_optional] = lambda: fake_user
    with patch("app.routers.advisory.get_location", return_value=_fake_location()), \
         patch("app.routers.advisory.get_latest_reading", return_value=_fake_reading(aqi=160)), \
         patch("app.routers.advisory.get_health_profile", return_value=fake_profile):
        response = client.get("/advisory/1")
    assert response.status_code == 200
    body = response.json()
    assert body["personalized"] is True
    # aqi 160 -> "Unhealthy" (severity 4) -> asthma rule for severity>=2
    # AND severity>=4 both fire, so both messages should be present
    joined = " ".join(body["recommendations"])
    assert "rescue medication" in joined
    assert "air purifier" in joined
    app.dependency_overrides.pop(get_current_user_optional, None)


def test_advisory_returns_503_when_reading_has_no_aqi():
    """An OpenWeatherMap-only row has aqi=None (see the scale-safety
    rule) -- there's genuinely nothing to advise on, and that must not
    be confused with a 404 (the location/reading do exist)."""
    app.dependency_overrides[get_current_user_optional] = lambda: None
    with patch("app.routers.advisory.get_location", return_value=_fake_location()), \
         patch("app.routers.advisory.get_latest_reading", return_value=_fake_reading(aqi=None)):
        response = client.get("/advisory/1")
    assert response.status_code == 503
    app.dependency_overrides.pop(get_current_user_optional, None)