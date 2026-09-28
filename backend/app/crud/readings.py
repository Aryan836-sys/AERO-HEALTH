"""aqi_readings queries: the write path for M2's caching job, the read path
for M1's API (latest reading, trend charts).
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AqiReading
from app.schemas import NormalizedReading
from app.services.reliability import check_reliability


def insert_reading(db: Session, **fields) -> AqiReading:
    """Insert one reading from raw aqi_readings column values."""
    reading = AqiReading(**fields)
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


def insert_normalized_reading(
    db: Session, location_id: int, reading: NormalizedReading
) -> AqiReading:
    """Insert a NormalizedReading from any adapter -- the write path M2's
    caching job calls once `location_id` has been resolved from
    `source_station_id` (data-adapter-build-guide.md Phase 4/5).
    """
    check_reliability(reading.source, reading.reliability_status)
    fields = reading.model_dump(exclude={"source_station_id"})
    fields["location_id"] = location_id
    return insert_reading(db, **fields)


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


def get_latest_aqi_reading(db: Session, location_id: int) -> AqiReading | None:
    """Newest reading that actually has an AQI -- what the advisory engine
    needs (raw-concentration-only readings can't be scored)."""
    return (
        db.query(AqiReading)
        .filter(AqiReading.location_id == location_id, AqiReading.aqi.isnot(None))
        .order_by(AqiReading.recorded_at.desc())
        .first()
    )


def get_latest_readings(db: Session, location_ids: list[int]) -> dict[int, AqiReading]:
    """Newest reading per location in one query (Postgres DISTINCT ON), so
    listing N locations doesn't cost N+1 queries."""
    if not location_ids:
        return {}
    rows = (
        db.query(AqiReading)
        .filter(AqiReading.location_id.in_(location_ids))
        .distinct(AqiReading.location_id)
        .order_by(AqiReading.location_id, AqiReading.recorded_at.desc())
        .all()
    )
    return {r.location_id: r for r in rows}
