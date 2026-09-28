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


def _fake_alert(alert_id=1, user_id=1, location_id=2, active=True):
    alert = MagicMock()
    alert.id = alert_id
    alert.user_id = user_id
    alert.location_id = location_id
    alert.aqi_threshold = 150
    alert.notification_type = "in_app"
    alert.active = active
    return alert


def _authed(user_id=1):
    app.dependency_overrides[get_current_user] = lambda: _fake_user(user_id=user_id)


def _clear_auth():
    app.dependency_overrides.pop(get_current_user, None)


def test_create_alert_requires_auth():
    _clear_auth()
    response = client.post(
        "/alerts", json={"location_id": 2, "aqi_threshold": 150, "notification_type": "in_app"}
    )
    assert response.status_code in (401, 403)


def test_create_alert_rejects_a_threshold_outside_0_500():
    _authed()
    response = client.post(
        "/alerts", json={"location_id": 2, "aqi_threshold": 999, "notification_type": "in_app"}
    )
    assert response.status_code == 422
    _clear_auth()


def test_create_alert_uses_the_authenticated_users_id():
    _authed()
    with patch("app.routers.alerts.create_alert", return_value=_fake_alert()) as mock_create:
        response = client.post(
            "/alerts", json={"location_id": 2, "aqi_threshold": 150, "notification_type": "in_app"}
        )
    assert response.status_code == 201
    assert mock_create.call_args.kwargs["user_id"] == 1
    _clear_auth()


def test_read_alerts_returns_the_users_list():
    _authed()
    with patch("app.routers.alerts.list_alerts_for_user", return_value=[_fake_alert()]):
        response = client.get("/alerts")
    assert response.status_code == 200
    assert len(response.json()) == 1
    _clear_auth()


def test_toggle_active_on_someone_elses_alert_returns_404():
    """The real ownership check: alert_id 1 exists (user_id=99), but the
    caller is user_id=1 -- must not be able to toggle it, and the error
    must not distinguish "not yours" from "doesn't exist"."""
    _authed(user_id=1)
    fake_db = MagicMock()
    fake_db.get.return_value = _fake_alert(alert_id=1, user_id=99)
    app.dependency_overrides[get_db] = lambda: fake_db

    response = client.patch("/alerts/1", json={"active": False})
    assert response.status_code == 404

    app.dependency_overrides[get_db] = lambda: MagicMock()
    _clear_auth()


def test_toggle_active_on_your_own_alert_succeeds():
    _authed(user_id=1)
    fake_db = MagicMock()
    fake_db.get.return_value = _fake_alert(alert_id=1, user_id=1)
    app.dependency_overrides[get_db] = lambda: fake_db

    with patch("app.routers.alerts.set_alert_active", return_value=_fake_alert(alert_id=1, user_id=1, active=False)):
        response = client.patch("/alerts/1", json={"active": False})
    assert response.status_code == 200
    assert response.json()["active"] is False

    app.dependency_overrides[get_db] = lambda: MagicMock()
    _clear_auth()


def test_toggle_active_on_a_nonexistent_alert_returns_404():
    _authed(user_id=1)
    fake_db = MagicMock()
    fake_db.get.return_value = None
    app.dependency_overrides[get_db] = lambda: fake_db

    response = client.patch("/alerts/999", json={"active": False})
    assert response.status_code == 404

    app.dependency_overrides[get_db] = lambda: MagicMock()
    _clear_auth()