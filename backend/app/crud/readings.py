"""aqi_readings queries: the write path for M2's caching job, the read path
for M1's API (latest reading, trend charts).
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AqiReading


def insert_reading(db: Session, **fields) -> AqiReading:
    """Insert one normalized reading.

    Once the data-adapter layer's NormalizedReading contract exists (see
    data-adapter-build-guide.md Phase 1), call this as
    `insert_reading(db, **reading.model_dump())`. Until then, pass the
    aqi_readings columns directly as keyword arguments.
    """
    reading = AqiReading(**fields)
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def get_latest_reading(db: Session, location_id: int) -> AqiReading | None:
    return (
        db.query(AqiReading)
        .filter(AqiReading.location_id == location_id)
        .order_by(AqiReading.recorded_at.desc())
        .first()
    )


def get_readings(db: Session, location_id: int, since: datetime) -> list[AqiReading]:
    """Readings for one location from `since` onward, oldest first -- feeds
    the 24h/7d/30d trend charts directly."""
    return (
        db.query(AqiReading)
        .filter(AqiReading.location_id == location_id, AqiReading.recorded_at >= since)
        .order_by(AqiReading.recorded_at.asc())
        .all()
    )
