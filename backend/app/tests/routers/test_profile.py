from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user
from app.database import get_db
from app.main import app

client = TestClient(app)
app.dependency_overrides[get_db] = lambda: MagicMock()


def _fake_user(user_id=1):
    user = MagicMock()
    user.id = user_id
    return user


def _fake_profile(user_id=1, **overrides):
    profile = MagicMock()
    profile.id = 1
    profile.user_id = user_id
    profile.age_group = overrides.get("age_group", "adult")
    profile.asthma = overrides.get("asthma", False)
    profile.respiratory_condition = overrides.get("respiratory_condition", False)
    profile.heart_condition = overrides.get("heart_condition", False)
    profile.pregnancy_status = overrides.get("pregnancy_status", False)
    profile.outdoor_worker = overrides.get("outdoor_worker", False)
    profile.activity_level = overrides.get("activity_level", "moderate")
    return profile


def _authed():
    app.dependency_overrides[get_current_user] = lambda: _fake_user(user_id=1)


def _clear_auth_override():
    app.dependency_overrides.pop(get_current_user, None)


def test_create_profile_requires_auth():
    _clear_auth_override()
    response = client.post("/profile", json={"asthma": True})
    assert response.status_code in (401, 403)


def test_create_profile_uses_the_authenticated_users_id_not_a_client_supplied_one():
    _authed()
    with patch("app.routers.profile.upsert_health_profile", return_value=_fake_profile(user_id=1)) as mock_upsert:
        response = client.post("/profile", json={"asthma": True, "age_group": "adult"})
    assert response.status_code == 201
    # user_id came from current_user, never from the request body (which
    # has no user_id field at all -- see schemas/health_profile.py)
    assert mock_upsert.call_args.kwargs["user_id"] == 1
    _clear_auth_override()


def test_read_profile_returns_404_when_none_exists():
    _authed()
    with patch("app.routers.profile.get_health_profile", return_value=None):
        response = client.get("/profile")
    assert response.status_code == 404
    _clear_auth_override()


def test_read_profile_returns_the_users_profile():
    _authed()
    with patch("app.routers.profile.get_health_profile", return_value=_fake_profile(user_id=1, asthma=True)):
        response = client.get("/profile")
    assert response.status_code == 200
    assert response.json()["asthma"] is True
    _clear_auth_override()


def test_update_profile_upserts():
    _authed()
    with patch("app.routers.profile.upsert_health_profile", return_value=_fake_profile(user_id=1)) as mock_upsert:
        response = client.put("/profile", json={"activity_level": "high"})
    assert response.status_code == 200
    assert mock_upsert.call_args.kwargs["user_id"] == 1
    _clear_auth_override()