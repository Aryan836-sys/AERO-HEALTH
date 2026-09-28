"""Day 9: submit and retrieve community pollution reports.

Submission works for guests too (get_current_user_optional) -- the
model itself documents anonymous reports as allowed
(pollution_report.py: "nullable: anonymous reports are allowed").
Retrieval is public; verification_status is an optional filter, not a
restriction -- moderation/admin-only actions on reports are a later
day's scope, not this one's.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user_optional
from app.crud.pollution_reports import create_report, list_reports
from app.database import get_db
from app.models import User
from app.schemas.report import ReportCreate, ReportOut

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportOut, status_code=201)
def submit_report(
    payload: ReportCreate,
    current_user: User | None = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    return create_report(
        db,
        location_id=payload.location_id,
        category=payload.category,
        user_id=current_user.id if current_user is not None else None,
        description=payload.description,
        image_url=payload.image_url,
        severity=payload.severity,
    )


@router.get("", response_model=list[ReportOut])
def read_reports(verification_status: str | None = None, db: Session = Depends(get_db)):
    return list_reports(db, verification_status=verification_status)