from pathlib import Path

from app.config import get_settings
from app.core.limiter import limiter
from tests.conftest import PASSWORD, make_user


# --- error shape ------------------------------------------------------------------


def test_errors_share_one_json_shape(client, user):
    cases = [
        client.get("/locations/999"),  # 404 (HTTPException)
        client.get("/me"),  # 401
        client.get("/admin/stats", headers=user),  # 403
        client.get("/readings/1", params={"range": "bad"}),  # 422
        client.get("/no-such-route"),  # 404 (router)
    ]
    for r in cases:
        body = r.json()
        assert {"detail", "status", "code"} <= body.keys(), r.url
        assert body["status"] == r.status_code
        assert isinstance(body["detail"], str)


def test_validation_errors_list_fields(client):
    r = client.post("/auth/register", json={"full_name": "A", "email": "bad", "password": "x"})
    body = r.json()
    assert body["code"] == "validation_error"
    fields = {e["field"] for e in body["errors"]}
    assert {"email", "password"} <= fields


def test_unhandled_errors_do_not_leak_internals(client, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app
    import app.routers.locations as locations

    def boom(*a, **k):
        raise RuntimeError("secret db password is hunter2")

    monkeypatch.setattr(locations, "list_locations", boom)
    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.get("/locations")
    assert r.status_code == 500
    assert "hunter2" not in r.text
    assert r.json()["code"] == "error"


# --- headers & CORS ---------------------------------------------------------------


def test_secure_headers_are_set(client):
    h = client.get("/health").headers
    assert h["x-content-type-options"] == "nosniff"
    assert h["x-frame-options"] == "DENY"
    assert h["referrer-policy"] == "no-referrer"
    assert "default-src 'none'" in h["content-security-policy"]


def test_swagger_docs_still_load_under_the_headers(client):
    r = client.get("/docs")
    assert r.status_code == 200
    assert "content-security-policy" not in r.headers  # docs need their CDN


def test_cors_allows_only_the_configured_origin(client):
    ok = client.options(
        "/locations",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = client.options(
        "/locations",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in bad.headers
    assert client.get("/health", headers={"Origin": "https://evil.example"}).headers.get(
        "access-control-allow-origin"
    ) is None


# --- rate limiting ----------------------------------------------------------------


def test_login_is_rate_limited(client):
    limiter.enabled = True
    limiter.reset()
    try:
        statuses = [
            client.post("/auth/login", json={"email": "a@example.com", "password": "nope-nope"}).status_code
            for _ in range(12)
        ]
    finally:
        limiter.enabled = False
        limiter.reset()
    assert statuses[:10] == [401] * 10
    assert 429 in statuses[10:]


def test_rate_limit_response_uses_the_common_error_shape(client):
    limiter.enabled = True
    limiter.reset()
    try:
        for _ in range(11):
            r = client.post("/auth/login", json={"email": "a@example.com", "password": "nope-nope"})
    finally:
        limiter.enabled = False
        limiter.reset()
    assert r.status_code == 429
    assert r.json()["code"] == "rate_limited"


# --- delete-my-data ---------------------------------------------------------------


def test_delete_me_removes_all_personal_data(client, db):
    from app.models import FavoriteLocation, HealthProfile, PollutionReport, User, UserAlert

    headers, me = make_user(client, "leaving@example.com")
    stay, _ = make_user(client, "staying@example.com")
    client.post("/profile", json={"asthma": True}, headers=headers)
    client.post("/favorites", json={"location_id": 1}, headers=headers)
    client.post("/alerts", json={"location_id": 1, "aqi_threshold": 100}, headers=headers)
    client.post("/favorites", json={"location_id": 2}, headers=stay)
    jpeg = b"\xff\xd8\xff\xe0" + b"\x00" * 32
    url = client.post(
        "/reports", data={"category": "dust", "location_id": "1"},
        files={"image": ("p.jpg", jpeg, "image/jpeg")}, headers=headers,
    ).json()["image_url"]
    stored = Path(get_settings().upload_dir) / url.removeprefix("/uploads/")
    assert stored.exists()

    assert client.delete("/me", headers=headers).status_code == 204

    db.expire_all()
    assert db.query(User).filter(User.id == me["id"]).count() == 0
    for model in (HealthProfile, UserAlert, FavoriteLocation, PollutionReport):
        assert db.query(model).filter(model.user_id == me["id"]).count() == 0, model
    assert not stored.exists()
    # ...and nobody else's data was touched.
    assert len(client.get("/favorites", headers=stay).json()) == 1


def test_delete_me_requires_auth(client):
    assert client.delete("/me").status_code == 401


# --- access-control sweep ---------------------------------------------------------


def test_every_user_scoped_route_rejects_guests(client):
    routes = [
        ("get", "/me"), ("delete", "/me"),
        ("get", "/profile"), ("post", "/profile"), ("put", "/profile"), ("delete", "/profile"),
        ("get", "/favorites"), ("post", "/favorites"), ("delete", "/favorites/1"),
        ("get", "/alerts"), ("post", "/alerts"), ("patch", "/alerts/1"), ("delete", "/alerts/1"),
    ]
    for method, path in routes:
        r = getattr(client, method)(path)
        assert r.status_code == 401, (method, path, r.status_code)


def test_public_routes_need_no_token(client):
    for path in ("/health", "/locations", "/locations/1", "/locations/compare?a=1&b=2",
                 "/readings/1", "/reports"):
        assert client.get(path).status_code == 200, path


def test_no_response_ever_contains_a_password_hash(client, user):
    blob = "".join(
        client.get(path, headers=user).text for path in ("/me", "/profile", "/favorites", "/alerts")
    )
    assert "password" not in blob and "$2b$" not in blob


def test_passwords_are_stored_hashed(client, db):
    from app.models import User

    make_user(client, "h@example.com")
    stored = db.query(User).one().password_hash
    assert stored != PASSWORD and stored.startswith("$2")
