from datetime import timedelta

from jose import jwt

from app.config import get_settings
from app.core.security import (
    ACCESS,
    REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from tests.conftest import PASSWORD, make_user


def test_password_hash_roundtrip_and_is_salted():
    h1, h2 = hash_password("hunter2hunter2"), hash_password("hunter2hunter2")
    assert h1 != h2 and "hunter2" not in h1
    assert verify_password("hunter2hunter2", h1)
    assert not verify_password("wrong", h1)
    assert not verify_password("x", "not-a-bcrypt-hash")


def test_register_returns_safe_fields_only(client):
    r = client.post(
        "/auth/register",
        json={"full_name": "Sita", "email": "Sita@Example.com", "password": PASSWORD},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "sita@example.com"  # normalized
    assert body["role"] == "user"
    assert "password" not in body and "password_hash" not in body


def test_register_cannot_choose_a_role(client):
    r = client.post(
        "/auth/register",
        json={"full_name": "Eve", "email": "eve@example.com", "password": PASSWORD, "role": "admin"},
    )
    assert r.status_code == 201
    assert r.json()["role"] == "user"


def test_register_duplicate_email_conflicts_case_insensitively(client):
    make_user(client, "dup@example.com")
    r = client.post(
        "/auth/register",
        json={"full_name": "X", "email": "DUP@example.com", "password": PASSWORD},
    )
    assert r.status_code == 409


def test_register_validation(client):
    bad = [
        {"full_name": "A", "email": "not-an-email", "password": PASSWORD},
        {"full_name": "A", "email": "a@example.com", "password": "short"},
        {"full_name": "  ", "email": "a@example.com", "password": PASSWORD},
        {"full_name": "A", "email": "a@example.com", "password": "x" * 100},  # > 72 bytes
        {"full_name": "A", "email": "a@example.com", "password": PASSWORD, "preferred_language": "fr"},
    ]
    for payload in bad:
        r = client.post("/auth/register", json=payload)
        assert r.status_code == 422, payload


def test_login_returns_tokens_and_user(client):
    make_user(client, "a@example.com")
    r = client.post("/auth/login", json={"email": "A@example.com", "password": PASSWORD})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert body["user"]["email"] == "a@example.com"


def test_login_fails_the_same_way_for_wrong_password_and_unknown_email(client):
    make_user(client, "a@example.com")
    wrong = client.post("/auth/login", json={"email": "a@example.com", "password": "nope-nope-nope"})
    unknown = client.post("/auth/login", json={"email": "who@example.com", "password": PASSWORD})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]


def test_protected_route_needs_a_valid_token(client, user):
    assert client.get("/me", headers=user).status_code == 200
    assert client.get("/me").status_code == 401
    assert client.get("/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    assert client.get("/me", headers={"Authorization": "Basic abc"}).status_code == 401


def test_refresh_token_cannot_be_used_as_access_token(client):
    _, u = make_user(client)
    refresh = create_refresh_token(u["id"])
    r = client.get("/me", headers={"Authorization": f"Bearer {refresh}"})
    assert r.status_code == 401


def test_access_token_cannot_be_used_to_refresh(client):
    _, u = make_user(client)
    r = client.post("/auth/refresh", json={"refresh_token": create_access_token(u["id"])})
    assert r.status_code == 401


def test_refresh_issues_working_tokens(client):
    make_user(client, "a@example.com")
    login = client.post("/auth/login", json={"email": "a@example.com", "password": PASSWORD}).json()
    r = client.post("/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert r.status_code == 200
    new_access = r.json()["access_token"]
    assert client.get("/me", headers={"Authorization": f"Bearer {new_access}"}).status_code == 200


def test_expired_token_is_rejected(client):
    _, u = make_user(client)
    settings = get_settings()
    from datetime import datetime, timezone

    expired = jwt.encode(
        {
            "sub": str(u["id"]),
            "type": ACCESS,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    assert client.get("/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401
    assert decode_token(expired, ACCESS) is None


def test_token_signed_with_another_secret_is_rejected(client):
    _, u = make_user(client)
    forged = jwt.encode({"sub": str(u["id"]), "type": ACCESS}, "another-secret-another-secret-0000", algorithm="HS256")
    assert client.get("/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_token_for_a_deleted_user_is_rejected(client):
    headers, _ = make_user(client)
    assert client.delete("/me", headers=headers).status_code == 204
    assert client.get("/me", headers=headers).status_code == 401


def test_token_types_are_distinct():
    assert decode_token(create_access_token(1), ACCESS) == 1
    assert decode_token(create_access_token(1), REFRESH) is None
    assert decode_token(create_refresh_token(1), REFRESH) == 1


# --- refresh cookie ---------------------------------------------------------------

from app.config import get_settings as _settings


def _cookie_name():
    return _settings().refresh_cookie_name


def test_login_sets_an_httponly_refresh_cookie(client):
    make_user(client, "c@example.com")
    r = client.post("/auth/login", json={"email": "c@example.com", "password": PASSWORD})
    header = r.headers["set-cookie"]
    assert header.startswith(f"{_cookie_name()}=")
    assert "HttpOnly" in header and "Path=/auth" in header and "SameSite=lax" in header


def test_refresh_works_from_the_cookie_alone(client):
    make_user(client, "c@example.com")
    client.post("/auth/login", json={"email": "c@example.com", "password": PASSWORD})
    # TestClient keeps the cookie jar; send no body at all, then an empty one.
    for kwargs in ({}, {"json": {}}):
        r = client.post("/auth/refresh", **kwargs)
        assert r.status_code == 200, kwargs
        access = r.json()["access_token"]
        assert client.get("/me", headers={"Authorization": f"Bearer {access}"}).status_code == 200


def test_refresh_without_any_token_is_401(client):
    assert client.post("/auth/refresh", json={}).status_code == 401
    assert client.post("/auth/refresh").status_code == 401


def test_logout_clears_the_cookie_so_refresh_fails(client):
    make_user(client, "c@example.com")
    client.post("/auth/login", json={"email": "c@example.com", "password": PASSWORD})
    assert client.post("/auth/refresh").status_code == 200
    out = client.post("/auth/logout")
    assert out.status_code == 204
    assert "Max-Age=0" in out.headers["set-cookie"] or "expires=" in out.headers["set-cookie"].lower()
    assert client.post("/auth/refresh").status_code == 401


# --- PATCH /me ----------------------------------------------------------------------


def test_user_can_change_preferred_language(client, user):
    r = client.patch("/me", json={"preferred_language": "ne"}, headers=user)
    assert r.status_code == 200 and r.json()["preferred_language"] == "ne"
    assert client.get("/me", headers=user).json()["preferred_language"] == "ne"


def test_patch_me_validates_and_cannot_change_role(client, user):
    assert client.patch("/me", json={"preferred_language": "fr"}, headers=user).status_code == 422
    r = client.patch("/me", json={"preferred_language": "en", "role": "admin"}, headers=user)
    assert r.json()["role"] == "user"
    assert client.patch("/me", json={"preferred_language": "en"}).status_code == 401
