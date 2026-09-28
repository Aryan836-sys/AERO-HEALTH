from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_reports_ok():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_reports_database_ok_when_reachable():
    fake_conn = MagicMock()
    fake_conn.__enter__.return_value.execute.return_value = None
    with patch("app.main.engine.connect", return_value=fake_conn):
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["api"] == "ok"
    assert body["database"] == "ok"
    assert body["error"] is None


def test_health_reports_database_unreachable_without_crashing():
    """A DB outage must be reported as data, not surfaced as a 500 --
    /health is exactly the endpoint that has to keep answering when the
    database is the thing that's down."""
    with patch("app.main.engine.connect", side_effect=Exception("connection refused")):
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["api"] == "ok"
    assert body["database"] == "unreachable"
    assert "connection refused" in body["error"]