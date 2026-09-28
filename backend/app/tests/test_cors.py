"""Verifies the CORS middleware actually allows the frontend's origin --
the exact thing that broke silently earlier in this project (the
frontend showing "Cannot reach the API" isn't always a CORS problem,
but when it is, this is the check that would have caught it before a
person had to debug it by hand in the browser).
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_preflight_allows_the_configured_frontend_origin():
    response = client.options(
        "/locations",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_actual_request_includes_cors_headers_for_the_frontend_origin():
    response = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_credentials_are_allowed_for_cookie_or_auth_header_based_requests():
    response = client.get("/", headers={"Origin": "http://localhost:5173"})
    assert response.headers.get("access-control-allow-credentials") == "true"