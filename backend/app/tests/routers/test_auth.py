"""Tests for the auth router, mocking at the crud boundary (create_user,
get_user_by_email, get_user) so these run against a real FastAPI app and
real JWT/bcrypt logic, without needing a live Postgres connection --
consistent with how test_reliability.py and test_cache_readings.py mock
their own external boundaries rather than hitting real services.
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.database import get_db
from app.main import app

client = TestClient(app)
app.dependency_overrides[get_db] = lambda: MagicMock()


def _fake_user(user_id=1, email="test@example.com", password="password123", role="registered"):
    user = MagicMock()
    user.id = user_id
    user.full_name = "Test User"
    user.email = email
    user.password_hash = hash_password(password)
    user.preferred_language = "en"
    user.role = role
    user.created_at = datetime.now(timezone.utc)
    return user


def test_register_creates_a_new_user():
    with patch("app.routers.auth.get_user_by_email", return_value=None), \
         patch("app.routers.auth.create_user", return_value=_fake_user()):
        response = client.post(
            "/auth/register",
            json={"full_name": "Test User", "email": "test@example.com", "password": "password123"},
        )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "test@example.com"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_rejects_a_duplicate_email():
    with patch("app.routers.auth.get_user_by_email", return_value=_fake_user()):
        response = client.post(
            "/auth/register",
            json={"full_name": "Test User", "email": "test@example.com", "password": "password123"},
        )
    assert response.status_code == 409


def test_register_rejects_an_invalid_email():
    response = client.post(
        "/auth/register",
        json={"full_name": "Test User", "email": "not-an-email", "password": "password123"},
    )
    assert response.status_code == 422


def test_login_succeeds_with_correct_credentials():
    user = _fake_user(password="password123")
    with patch("app.routers.auth.get_user_by_email", return_value=user):
        response = client.post(
            "/auth/login", json={"email": "test@example.com", "password": "password123"}
        )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_login_rejects_the_wrong_password():
    user = _fake_user(password="password123")
    with patch("app.routers.auth.get_user_by_email", return_value=user):
        response = client.post(
            "/auth/login", json={"email": "test@example.com", "password": "wrong-password"}
        )
    assert response.status_code == 401


def test_login_rejects_an_unknown_email():
    with patch("app.routers.auth.get_user_by_email", return_value=None):
        response = client.post(
            "/auth/login", json={"email": "nobody@example.com", "password": "password123"}
        )
    assert response.status_code == 401


def test_me_requires_a_token():
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_me_returns_the_current_user_with_a_valid_token():
    user = _fake_user(user_id=5)
    token = create_access_token(user_id=5)
    with patch("app.core.dependencies.get_user", return_value=user):
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["id"] == 5


def test_me_rejects_a_token_for_a_deleted_user():
    token = create_access_token(user_id=999)
    with patch("app.core.dependencies.get_user", return_value=None):
        response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_refresh_issues_a_new_token_pair():
    user = _fake_user(user_id=3)
    from app.core.security import create_refresh_token

    refresh_token = create_refresh_token(user_id=3)
    with patch("app.routers.auth.get_user", return_value=user):
        response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_rejects_an_access_token_used_as_a_refresh_token():
    """The same cross-type protection as the unit test in
    test_security.py, exercised through the actual HTTP endpoint."""
    access_token = create_access_token(user_id=3)
    response = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401