"""Shared test setup.

API tests run against a *separate* Postgres database (`<name>_test`), built
by running the real Alembic migrations, so they exercise the true schema
without ever touching the dev data. The env vars below must be set before
`app` is imported anywhere, which is why they live at import time here.
"""
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parent.parent

_dev_url = os.environ.get("DATABASE_URL") or dotenv_values(BACKEND_DIR / ".env")["DATABASE_URL"]
_url = make_url(_dev_url)
TEST_DB_NAME = f"{_url.database}_test"
TEST_URL = _url.set(database=TEST_DB_NAME)

os.environ["DATABASE_URL"] = TEST_URL.render_as_string(hide_password=False)
os.environ["JWT_SECRET"] = "test-secret-test-secret-test-secret-1234"
os.environ["ENVIRONMENT"] = "test"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["CACHE_READINGS_ENABLED"] = "false"  # no live provider calls in tests
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="aero-test-uploads-")

assert TEST_DB_NAME.endswith("_test")  # guard: never run against the dev DB


def _ensure_database():
    admin = create_engine(_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": TEST_DB_NAME}
        ).scalar()
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin.dispose()

    test_engine = create_engine(TEST_URL, isolation_level="AUTOCOMMIT")
    with test_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    test_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    _ensure_database()
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        check=True,
        capture_output=True,
    )

    from app.database import SessionLocal
    from app.models import AqiReading, Location

    db = SessionLocal()
    db.execute(text("TRUNCATE locations RESTART IDENTITY CASCADE"))
    now = datetime.now(timezone.utc)

    def reading(location, aqi, hours_ago, **extra):
        db.add(
            AqiReading(
                location=location,
                aqi=aqi,
                main_pollutant=extra.pop("main_pollutant", "pm25" if aqi else None),
                source="waqi",
                reliability_status="official",
                recorded_at=now - timedelta(hours=hours_ago),
                fetched_at=now - timedelta(hours=hours_ago),
                **extra,
            )
        )

    # id 1: Unhealthy now, with history at 2h / 30h / 8d ago
    kalanki = Location(area_name="Kalanki", geometry="SRID=4326;POINT(85.2810 27.6930)", source_station_id="k1")
    # id 2: Good
    kirtipur = Location(area_name="Kirtipur", geometry="SRID=4326;POINT(85.2893 27.6817)", source_station_id="k2")
    # id 3: only a reading with no AQI (raw concentrations)
    pulchowk = Location(area_name="Pulchowk", geometry="SRID=4326;POINT(85.3188 27.6826)", source_station_id="k3")
    # id 4: no readings at all
    sankhu = Location(area_name="Sankhu", geometry="SRID=4326;POINT(85.4680 27.7340)")
    db.add_all([kalanki, kirtipur, pulchowk, sankhu])
    reading(kalanki, 160, 0.5, pm25=80.0, temperature=21.0, humidity=55.0)
    reading(kalanki, 120, 2)
    reading(kalanki, 90, 30)
    reading(kalanki, 70, 24 * 8)
    reading(kirtipur, 40, 0.5, pm25=9.0)
    reading(pulchowk, None, 0.5, pm25=30.0)
    db.commit()
    db.close()
    yield


_USER_TABLES = (
    "audit_logs, pollution_reports, user_alerts, favorite_locations, "
    "health_profiles, users"
)


@pytest.fixture(autouse=True)
def _clean_user_data(_test_database):
    yield
    from app.database import engine

    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {_USER_TABLES} RESTART IDENTITY CASCADE"))


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    from app.database import SessionLocal

    session = SessionLocal()
    yield session
    session.close()


PASSWORD = "correct-horse-battery"


def make_user(client, email="user@example.com", name="Test User"):
    """Register + log in; returns (auth headers, user dict)."""
    r = client.post(
        "/auth/register", json={"full_name": name, "email": email, "password": PASSWORD}
    )
    assert r.status_code == 201, r.text
    login = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, login.text
    body = login.json()
    return {"Authorization": f"Bearer {body['access_token']}"}, body["user"]


@pytest.fixture
def user(client):
    return make_user(client)[0]


@pytest.fixture
def other_user(client):
    return make_user(client, "other@example.com", "Other User")[0]


@pytest.fixture
def admin(client, db):
    from app.models import User

    headers, u = make_user(client, "admin@example.com", "Admin")
    db.query(User).filter(User.id == u["id"]).update({"role": "admin"})
    db.commit()
    return headers
