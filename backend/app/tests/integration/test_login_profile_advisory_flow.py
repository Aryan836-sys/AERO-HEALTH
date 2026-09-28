"""Day 10: "Test login -> profile -> advisory flow" from the work plan.

Register, log in, set a health profile, and get a personalized advisory
-- all through real HTTP calls against the real app, exercising real
bcrypt hashing, real JWT issuing/verification, real Pydantic validation,
and the real advisory_engine logic. Only the database layer is mocked
(crud functions), and mocked consistently to represent ONE coherent user
across every step, not independently per test.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.database import get_db
from app.main import app

client = TestClient(app)
app.dependency_overrides[get_db] = lambda: MagicMock()


def _make_fake_user(user_id, email, password):
    user = MagicMock()
    user.id = user_id
    user.full_name = "Integration Test User"
    user.email = email
    user.password_hash = hash_password(password)  # a REAL bcrypt hash
    user.preferred_language = "en"
    user.role = "registered"
    user.created_at = datetime.now(timezone.utc)
    return user


def _fake_profile(user_id):
    profile = MagicMock()
    profile.id = 1
    profile.user_id = user_id
    profile.age_group = "adult"
    profile.asthma = True
    profile.respiratory_condition = False
    profile.heart_condition = False
    profile.pregnancy_status = False
    profile.outdoor_worker = False
    profile.activity_level = "moderate"
    return profile


def _fake_location():
    loc = MagicMock()
    loc.id = 1
    loc.geometry = MagicMock()
    return loc


def _fake_reading(aqi=120):
    r = MagicMock()
    r.aqi = aqi
    return r


def test_full_login_to_personalized_advisory_flow():
    email, password = "integration@aerohealth.dev", "password123"

    # -- Register --
    with patch("app.routers.auth.get_user_by_email", return_value=None), \
         patch("app.routers.auth.create_user") as mock_create:
        mock_create.return_value = _make_fake_user(1, email, password)
        register_response = client.post(
            "/auth/register",
            json={"full_name": "Integration Test User", "email": email, "password": password},
        )
    assert register_response.status_code == 201
    # the password given to hash_password by the router must be the raw
    # one the client sent, not something already transformed
    assert mock_create.call_args.kwargs["password_hash"] != password

    fake_user = _make_fake_user(1, email, password)

    # -- Login --
    with patch("app.routers.auth.get_user_by_email", return_value=fake_user):
        login_response = client.post("/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # -- Set health profile (asthma) --
    with patch("app.core.dependencies.get_user", return_value=fake_user), \
         patch("app.routers.profile.upsert_health_profile", return_value=_fake_profile(1)):
        profile_response = client.post(
            "/profile", json={"age_group": "adult", "asthma": True}, headers=auth_headers
        )
    assert profile_response.status_code == 201
    assert profile_response.json()["asthma"] is True

    # -- Get a personalized advisory using that profile --
    with patch("app.core.dependencies.get_user", return_value=fake_user), \
         patch("app.routers.advisory.get_location", return_value=_fake_location()), \
         patch("app.routers.advisory.get_latest_reading", return_value=_fake_reading(aqi=120)), \
         patch("app.routers.advisory.get_health_profile", return_value=_fake_profile(1)):
        advisory_response = client.get("/advisory/1", headers=auth_headers)
    assert advisory_response.status_code == 200
    body = advisory_response.json()
    assert body["personalized"] is True
    assert body["aqi"] == 120
    # aqi 120 -> "Unhealthy for Sensitive Groups" -- asthma guidance
    # should be present since severity (3) >= the engine's threshold
    assert any("rescue medication" in r for r in body["recommendations"])


def test_the_same_flow_without_a_token_gets_the_unpersonalized_version():
    """Same location, same reading, but no login at all -- confirms
    personalization is genuinely gated on auth, not just always on."""
    with patch("app.routers.advisory.get_location", return_value=_fake_location()), \
         patch("app.routers.advisory.get_latest_reading", return_value=_fake_reading(aqi=120)):
        response = client.get("/advisory/1")
    assert response.status_code == 200
    assert response.json()["personalized"] is False
    assert not any("rescue medication" in r for r in response.json()["recommendations"])