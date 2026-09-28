from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.limiter import PUBLIC_LIMIT, limiter
from app.crud.locations import get_location
from app.crud.readings import get_readings
from app.database import get_db
from app.schemas.location import ReadingOut, ReadingRange

router = APIRouter(prefix="/readings", tags=["readings"])

WINDOWS = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}


@router.get("/{location_id}", response_model=list[ReadingOut])
@limiter.limit(PUBLIC_LIMIT)
def read_readings(
    request: Request,
    location_id: int,
    range: ReadingRange = Query("24h"),
    db: Session = Depends(get_db),
):
    """Cached readings for one location over the window, oldest first --
    shaped for trend charts. May be empty; gaps are real, not filled in."""
    if get_location(db, location_id) is None:
        raise HTTPException(status_code=404, detail="Location not found")
    since = datetime.now(timezone.utc) - WINDOWS[range]
    return get_readings(db, location_id, since)
