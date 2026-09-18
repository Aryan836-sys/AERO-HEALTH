"""GET /locations and GET /locations/{id}.

Day 3 of the work plan: /locations/{id} returns the location plus its
latest cached AQI reading (never fetches live -- that's the cache job's job).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import locations as locations_crud
from app.crud import readings as readings_crud
from app.database import get_db
from app.schemas.location import LocationOut, LocationWithLatestReading

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[LocationOut])
def list_locations(db: Session = Depends(get_db)):
    """All monitored locations (stations + user-picked points)."""
    locations = locations_crud.list_locations(db)
    return [LocationOut.from_location(loc) for loc in locations]


@router.get("/{location_id}", response_model=LocationWithLatestReading)
def get_location(location_id: int, db: Session = Depends(get_db)):
    """One location, with its most recent AQI reading (null if none cached yet)."""
    location = locations_crud.get_location(db, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")

    latest_reading = readings_crud.get_latest_reading(db, location_id)
    return LocationWithLatestReading.from_location_and_reading(location, latest_reading)
