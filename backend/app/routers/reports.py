from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.deps import get_optional_user
from app.core.limiter import PUBLIC_LIMIT, REPORT_LIMIT, limiter
from app.crud.locations import get_location, get_locations_within_radius, get_nearest_location
from app.crud.pollution_reports import create_report, list_public_reports
from app.database import get_db
from app.models import User
from app.schemas.report import (
    ReportCategory,
    ReportOut,
    ReportSeverity,
    report_to_out,
)
from app.services.uploads import save_image

router = APIRouter(prefix="/reports", tags=["reports"])

# A report pinned to a point must land near a monitored location; beyond
# this it's outside the area the app covers.
MAX_SNAP_DISTANCE_KM = 30.0


@router.post("", response_model=ReportOut, status_code=201)
@limiter.limit(REPORT_LIMIT)
async def submit_report(
    request: Request,
    category: Annotated[ReportCategory, Form()],
    description: Annotated[str | None, Form(max_length=2000)] = None,
    severity: Annotated[ReportSeverity | None, Form()] = None,
    location_id: Annotated[int | None, Form()] = None,
    latitude: Annotated[float | None, Form(ge=-90, le=90)] = None,
    longitude: Annotated[float | None, Form(ge=-180, le=180)] = None,
    anonymous: Annotated[bool, Form()] = False,
    image: Annotated[UploadFile | None, File()] = None,
    user: User | None = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """Submit a community report (multipart). It always starts `unverified`.

    Guests may submit too (always anonymous); the per-IP rate limit is
    stricter than for other writes because there is no account to hold to.

    Pin it with either `location_id` or a `latitude`+`longitude` (snapped to
    the nearest monitored location). With `anonymous=true` the report is
    stored without the submitter's id, so it can't be traced back to them.
    """
    if location_id is not None:
        if get_location(db, location_id) is None:
            raise HTTPException(status_code=404, detail="Location not found")
    elif latitude is not None and longitude is not None:
        nearest = get_nearest_location(db, latitude, longitude)
        if nearest is None or nearest[1] > MAX_SNAP_DISTANCE_KM:
            raise HTTPException(
                status_code=422, detail="That point is outside the supported area"
            )
        location_id = nearest[0].id
    else:
        raise HTTPException(
            status_code=422, detail="Provide location_id, or both latitude and longitude"
        )

    # Browsers send an empty file part when no file was chosen.
    image_url = await save_image(image) if image is not None and image.filename else None

    report = create_report(
        db,
        location_id=location_id,
        category=category,
        user_id=None if (anonymous or user is None) else user.id,
        description=description.strip() if description else None,
        image_url=image_url,
        severity=severity,
    )
    return report_to_out(report)


@router.get("", response_model=list[ReportOut])
@limiter.limit(PUBLIC_LIMIT)
def list_reports(
    request: Request,
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    radius_km: float = Query(5.0, gt=0, le=50),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Recent public reports (unverified and verified; rejected and flagged
    are hidden), newest first. Pass `lat` and `lng` to limit to reports near
    a point. Only public-safe fields -- never who submitted them."""
    if (lat is None) != (lng is None):
        raise HTTPException(status_code=422, detail="Provide both lat and lng, or neither")

    location_ids = None
    if lat is not None:
        nearby = get_locations_within_radius(db, lat, lng, radius_km * 1000)
        location_ids = [loc.id for loc in nearby]

    return [report_to_out(r) for r in list_public_reports(db, location_ids=location_ids, limit=limit)]
