"""GET /readings/{locationId}?range=24h|7d|30d -- feeds the trend charts."""
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.crud import locations as locations_crud
from app.crud import readings as readings_crud
from app.database import get_db
from app.schemas.reading import ReadingOut

router = APIRouter(prefix="/readings", tags=["readings"])

_RANGE_TO_TIMEDELTA = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


@router.get("/{location_id}", response_model=list[ReadingOut])
def get_readings(
    location_id: int,
    range: Literal["24h", "7d", "30d"] = Query(
        "24h", description="How far back to return readings from."
    ),
    db: Session = Depends(get_db),
):
    """Readings for one location over the requested window, oldest first."""
    location = locations_crud.get_location(db, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")

    since = datetime.now(timezone.utc) - _RANGE_TO_TIMEDELTA[range]
    return readings_crud.get_readings(db, location_id, since)
