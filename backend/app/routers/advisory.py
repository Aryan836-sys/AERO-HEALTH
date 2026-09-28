from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.deps import get_optional_user
from app.core.limiter import PUBLIC_LIMIT, limiter
from app.crud.health_profiles import get_health_profile
from app.crud.locations import get_location
from app.crud.readings import get_latest_aqi_reading
from app.database import get_db
from app.models import User
from app.schemas.advisory import AdvisoryOut, AdvisoryRequest, ReasonOut
from app.services.advisory import ProfileInput, ReadingInput, evaluate_advisory

router = APIRouter(prefix="/advisory", tags=["advisory"])


@router.post("", response_model=AdvisoryOut)
@limiter.limit(PUBLIC_LIMIT)
def create_advisory(
    request: Request,
    body: AdvisoryRequest,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Explainable recommendation for a location.

    Profile used, in order: a what-if `profile` in the request (input only,
    never saved); else the logged-in caller's own stored profile (looked up
    from the token, never by an id in the request); else none -- a guest gets
    the general advisory."""
    if get_location(db, body.location_id) is None:
        raise HTTPException(status_code=404, detail="Location not found")

    reading = get_latest_aqi_reading(db, body.location_id)
    if reading is None:
        raise HTTPException(
            status_code=404, detail="No AQI reading is available for this location yet"
        )

    source = body.profile or (get_health_profile(db, user.id) if user else None)
    profile = (
        ProfileInput(
            age_group=source.age_group,
            asthma=source.asthma,
            respiratory_condition=source.respiratory_condition,
            heart_condition=source.heart_condition,
            pregnancy_status=source.pregnancy_status,
            outdoor_worker=source.outdoor_worker,
            activity_level=source.activity_level,
        )
        if source
        else None
    )

    result = evaluate_advisory(
        ReadingInput(reading.aqi, reading.main_pollutant, reading.recorded_at),
        profile,
        activity=body.activity,
        prolonged_exposure=body.prolonged_exposure,
    )
    return AdvisoryOut(
        location_id=body.location_id,
        aqi=result.aqi,
        aqi_category=result.aqi_category,
        risk_level=result.risk_level,
        recommendation=result.recommendation,
        reasons=[ReasonOut(code=r.code, message=r.message) for r in result.reasons],
        disclaimer=result.disclaimer,
        personalized=result.personalized,
        source=reading.source,
        reliability_status=reading.reliability_status,
        recorded_at=reading.recorded_at,
    )
