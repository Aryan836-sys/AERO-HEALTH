from types import SimpleNamespace

from app.services.alerts import check_alerts_for_reading, find_crossed_alerts
from tests.conftest import make_user


def alert(threshold, active=True):
    return SimpleNamespace(aqi_threshold=threshold, active=active)


# --- crossing detection (pure) ------------------------------------------------


def test_find_crossed_alerts_returns_only_reached_thresholds():
    alerts = [alert(50), alert(100), alert(150), alert(200)]
    crossed = find_crossed_alerts(alerts, 120)
    assert [a.aqi_threshold for a in crossed] == [50, 100]


def test_threshold_is_inclusive():
    assert len(find_crossed_alerts([alert(100)], 100)) == 1
    assert len(find_crossed_alerts([alert(100)], 99)) == 0


def test_inactive_alerts_never_trigger():
    assert find_crossed_alerts([alert(10, active=False)], 300) == []


def test_reading_without_aqi_never_triggers():
    assert find_crossed_alerts([alert(1)], None) == []


def test_check_alerts_for_reading_uses_stored_alerts(client, db, user):
    from app.crud.readings import get_latest_reading

    client.post("/alerts", json={"location_id": 1, "aqi_threshold": 150}, headers=user)
    client.post("/alerts", json={"location_id": 1, "aqi_threshold": 180}, headers=user)
    off = client.post("/alerts", json={"location_id": 1, "aqi_threshold": 50}, headers=user).json()
    client.patch(f"/alerts/{off['id']}", json={"active": False}, headers=user)
    client.post("/alerts", json={"location_id": 2, "aqi_threshold": 10}, headers=user)  # other place

    latest = get_latest_reading(db, 1)  # AQI 160
    crossed = check_alerts_for_reading(db, latest)
    assert [a.aqi_threshold for a in crossed] == [150]


# --- favorites ------------------------------------------------------------------


def test_favorites_need_auth(client):
    assert client.get("/favorites").status_code == 401
    assert client.post("/favorites", json={"location_id": 1}).status_code == 401
    assert client.delete("/favorites/1").status_code == 401


def test_favorites_add_list_remove(client, user):
    assert client.get("/favorites", headers=user).json() == []
    r = client.post("/favorites", json={"location_id": 1}, headers=user)
    assert r.status_code == 201
    assert r.json()["location"]["area_name"] == "Kalanki"
    assert r.json()["location"]["latest_reading"]["aqi"] == 160

    client.post("/favorites", json={"location_id": 2}, headers=user)
    assert {f["location_id"] for f in client.get("/favorites", headers=user).json()} == {1, 2}

    assert client.delete("/favorites/1", headers=user).status_code == 204
    assert [f["location_id"] for f in client.get("/favorites", headers=user).json()] == [2]


def test_favorite_is_idempotent_and_validates_location(client, user):
    client.post("/favorites", json={"location_id": 1}, headers=user)
    assert client.post("/favorites", json={"location_id": 1}, headers=user).status_code == 201
    assert len(client.get("/favorites", headers=user).json()) == 1
    assert client.post("/favorites", json={"location_id": 999}, headers=user).status_code == 404


def test_favorites_are_private_per_user(client, user, other_user):
    client.post("/favorites", json={"location_id": 1}, headers=user)
    assert client.get("/favorites", headers=other_user).json() == []
    # Deleting "the same" favorite as another user does nothing to mine.
    client.delete("/favorites/1", headers=other_user)
    assert len(client.get("/favorites", headers=user).json()) == 1


# --- alerts ---------------------------------------------------------------------


def test_alerts_need_auth(client):
    assert client.get("/alerts").status_code == 401
    assert client.post("/alerts", json={"location_id": 1, "aqi_threshold": 100}).status_code == 401


def test_alert_create_list_toggle_delete(client, user):
    r = client.post(
        "/alerts",
        json={"location_id": 1, "aqi_threshold": 120, "notification_type": "email"},
        headers=user,
    )
    assert r.status_code == 201
    created = r.json()
    assert created["active"] is True and created["notification_type"] == "email"

    assert [a["id"] for a in client.get("/alerts", headers=user).json()] == [created["id"]]

    r = client.patch(f"/alerts/{created['id']}", json={"active": False}, headers=user)
    assert r.json()["active"] is False
    assert client.get("/alerts", headers=user).json()[0]["active"] is False

    assert client.delete(f"/alerts/{created['id']}", headers=user).status_code == 204
    assert client.get("/alerts", headers=user).json() == []


def test_alert_defaults_to_in_app(client, user):
    r = client.post("/alerts", json={"location_id": 1, "aqi_threshold": 100}, headers=user)
    assert r.json()["notification_type"] == "in-app"


def test_alert_validation(client, user):
    bad = [
        {"location_id": 1, "aqi_threshold": 0},
        {"location_id": 1, "aqi_threshold": 501},
        {"location_id": 1, "aqi_threshold": 100, "notification_type": "sms"},
        {"aqi_threshold": 100},
    ]
    for payload in bad:
        assert client.post("/alerts", json=payload, headers=user).status_code == 422, payload
    assert client.post("/alerts", json={"location_id": 999, "aqi_threshold": 100}, headers=user).status_code == 404


def test_users_cannot_touch_each_others_alerts(client, user, other_user):
    mine = client.post("/alerts", json={"location_id": 1, "aqi_threshold": 100}, headers=user).json()
    assert client.get("/alerts", headers=other_user).json() == []
    # 404, not 403 -- don't reveal that the id exists.
    assert client.patch(f"/alerts/{mine['id']}", json={"active": False}, headers=other_user).status_code == 404
    assert client.delete(f"/alerts/{mine['id']}", headers=other_user).status_code == 404
    still = client.get("/alerts", headers=user).json()
    assert len(still) == 1 and still[0]["active"] is True
