"""GET /locations and GET /locations/{id}.

Day 3 of the work plan: /locations/{id} returns the location plus its
latest cached AQI reading (never fetches live -- that's the cache job's job).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import locations as locations_crud
from app.crud import readings as readings_crud
from app.database import get_db
from app.schemas.frontend_area import FrontendArea

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[FrontendArea])
def list_locations(db: Session = Depends(get_db)):
    """All monitored locations, shaped to match the frontend's `Area` contract
    (see app/schemas/frontend_area.py for why this differs from the raw DB schema)."""
    locations = locations_crud.list_locations(db)
    results = []
    for loc in locations:
        latest = readings_crud.get_latest_reading(db, loc.id)
        results.append(FrontendArea.from_location(loc, latest))
    return results


@router.get("/{location_id}", response_model=FrontendArea)
def get_location(location_id: int, db: Session = Depends(get_db)):
    """One location, shaped to match the frontend's `Area` contract, with its
    most recent AQI reading nested under `reading` (null if none cached yet)."""
    location = locations_crud.get_location(db, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")

    latest_reading = readings_crud.get_latest_reading(db, location_id)
    return FrontendArea.from_location(location, latest_reading)