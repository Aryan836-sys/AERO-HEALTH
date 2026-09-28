"""Day 8: GET /advisory/{location_id} -- the endpoint the frontend's
"Explainable Advisory" card actually calls (it was showing "Not Found"
before this router existed; services/advisory_engine.py was built but
never wired to an HTTP route).

Works for guests and logged-in users alike -- get_current_user_optional
means being logged in only personalizes the recommendations (via the
caller's health profile, if they have one); it never gates access to
getting an advisory at all. A location with no cached reading yet
correctly 404s rather than fabricating an AQI to advise on.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_optional
from app.crud.health_profiles import get_health_profile
from app.crud.locations import get_location
from app.crud.readings import get_latest_reading
from app.database import get_db
from app.models import User
from app.schemas.advisory import AdvisoryOut
from app.services.advisory_engine import AdvisoryError, generate_advisory

router = APIRouter(prefix="/advisory", tags=["advisory"])


@router.get("/{location_id}", response_model=AdvisoryOut)
def get_advisory(
    location_id: int,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    location = get_location(db, location_id)
    if location is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found.")

    reading = get_latest_reading(db, location_id)
    if reading is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No cached reading yet for this location -- nothing to advise on.",
        )

    profile = get_health_profile(db, current_user.id) if current_user is not None else None

    try:
        advisory = generate_advisory(reading.aqi, profile)
    except AdvisoryError as exc:
        # reading.aqi is null (e.g. an OpenWeatherMap-only row -- see
        # aqi_reading.py's scale-safety rule) or somehow out of range.
        # Not the client's fault, but there is genuinely no valid AQI to
        # advise on for this location right now.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Cannot generate an advisory right now: {exc}",
        )

    return AdvisoryOut(
        location_id=location_id,
        aqi=advisory.aqi,
        aqi_category=advisory.aqi_category,
        severity=advisory.severity,
        recommendations=advisory.recommendations,
        disclaimer=advisory.disclaimer,
        personalized=profile is not None,
    )