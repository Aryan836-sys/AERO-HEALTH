"""Regression test for a real bug: get_latest_reading() used to order by
recorded_at alone, so an OpenWeatherMap-only row (aqi=None, always
fetched last by cache_readings.py, so almost always the most recent)
would silently mask a perfectly good earlier reading with a real aqi --
for the /locations display, reliability.py's stale-cache fallback, and
the advisory endpoint alike, since all three call this same function.

Uses a standalone in-memory SQLite table for just AqiReading -- not the
full app.database.Base.metadata (which includes Location's PostGIS
Geometry column, unsupported by SQLite) -- since this function only
touches aqi_readings.
"""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.crud.readings import get_latest_reading
from app.models.aqi_reading import AqiReading


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    AqiReading.__table__.create(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def _reading(location_id, aqi, minutes_ago, source="waqi"):
    return AqiReading(
        location_id=location_id,
        aqi=aqi,
        source=source,
        reliability_status="official" if source == "waqi" else "modelled",
        recorded_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
        fetched_at=datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
    )


def test_skips_a_more_recent_null_aqi_row_in_favor_of_an_older_real_one(db_session):
    """The exact bug scenario: a real AQI reading, then an OWM row with
    aqi=None fetched a moment later for the same location."""
    db_session.add(_reading(location_id=1, aqi=88, minutes_ago=5, source="openaq"))
    db_session.add(_reading(location_id=1, aqi=None, minutes_ago=1, source="openweathermap"))
    db_session.commit()

    result = get_latest_reading(db_session, location_id=1)
    assert result is not None
    assert result.aqi == 88
    assert result.source == "openaq"


def test_returns_the_most_recent_among_multiple_real_readings(db_session):
    db_session.add(_reading(location_id=1, aqi=50, minutes_ago=10, source="waqi"))
    db_session.add(_reading(location_id=1, aqi=90, minutes_ago=2, source="openaq"))
    db_session.commit()

    result = get_latest_reading(db_session, location_id=1)
    assert result.aqi == 90


def test_returns_none_when_every_reading_has_a_null_aqi(db_session):
    db_session.add(_reading(location_id=1, aqi=None, minutes_ago=1, source="openweathermap"))
    db_session.commit()

    assert get_latest_reading(db_session, location_id=1) is None


def test_returns_none_when_theres_no_reading_at_all(db_session):
    assert get_latest_reading(db_session, location_id=999) is None


def test_ignores_readings_from_a_different_location(db_session):
    db_session.add(_reading(location_id=2, aqi=200, minutes_ago=1, source="waqi"))
    db_session.commit()

    assert get_latest_reading(db_session, location_id=1) is None