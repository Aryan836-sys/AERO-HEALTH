from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.limiter import PUBLIC_LIMIT, limiter
from app.crud.locations import get_location, list_locations
from app.crud.readings import get_latest_reading, get_latest_readings
from app.database import get_db
from app.schemas.location import CompareOut, LocationOut, location_to_out

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("", response_model=list[LocationOut])
@limiter.limit(PUBLIC_LIMIT)
def list_all_locations(request: Request, db: Session = Depends(get_db)):
    """Every supported location, each with its latest reading (or null)."""
    locations = list_locations(db)
    latest = get_latest_readings(db, [loc.id for loc in locations])
    return [location_to_out(loc, latest.get(loc.id)) for loc in locations]


# Declared before /{location_id}: otherwise "compare" would be parsed as an id.
@router.get("/compare", response_model=CompareOut)
@limiter.limit(PUBLIC_LIMIT)
def compare_locations(
    request: Request,
    a: int = Query(...),
    b: int = Query(...),
    db: Session = Depends(get_db),
):
    if a == b:
        raise HTTPException(status_code=400, detail="Choose two different locations to compare")
    location_a, location_b = get_location(db, a), get_location(db, b)
    if location_a is None or location_b is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return CompareOut(
        a=location_to_out(location_a, get_latest_reading(db, a)),
        b=location_to_out(location_b, get_latest_reading(db, b)),
    )


@router.get("/{location_id}", response_model=LocationOut)
@limiter.limit(PUBLIC_LIMIT)
def read_location(request: Request, location_id: int, db: Session = Depends(get_db)):
    location = get_location(db, location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return location_to_out(location, get_latest_reading(db, location_id))
