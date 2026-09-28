from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.crud.audit_logs import list_actions, record_action
from app.crud.pollution_reports import (
    count_reports,
    count_reports_by_category,
    get_report,
    list_reports,
    update_report_status,
)
from app.crud.users import count_users
from app.database import get_db
from app.models import User
from app.schemas.report import (
    AdminReportOut,
    AuditLogOut,
    ModerationRequest,
    ReportStatus,
    StatsOut,
    report_to_admin_out,
)

# Every route here requires the admin role -- a non-admin gets 403.
router = APIRouter(
    prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)]
)


@router.get("/reports", response_model=list[AdminReportOut])
def moderation_queue(
    status: ReportStatus | Literal["all"] = Query("unverified"),
    db: Session = Depends(get_db),
):
    """Reports awaiting moderation (default `unverified`); pass `status` to
    view another state, or `all`."""
    wanted = None if status == "all" else status
    return [report_to_admin_out(r) for r in list_reports(db, verification_status=wanted)]


@router.patch("/reports/{report_id}", response_model=AdminReportOut)
def moderate_report(
    report_id: int,
    body: ModerationRequest,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    report = get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    previous = report.verification_status
    updated = update_report_status(db, report_id, body.verification_status)
    record_action(
        db,
        actor_id=admin.id,
        action=f"report.{body.verification_status}",
        target_type="pollution_report",
        target_id=report_id,
        detail=f"{previous} -> {body.verification_status}",
    )
    return report_to_admin_out(updated)


@router.get("/stats", response_model=StatsOut)
def stats(db: Session = Depends(get_db)):
    return StatsOut(
        users=count_users(db),
        reports=count_reports(db),
        pending=count_reports(db, "unverified"),
        flagged=count_reports(db, "flagged"),
        reports_by_category=count_reports_by_category(db),
    )


@router.get("/audit-log", response_model=list[AuditLogOut])
def audit_log(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)):
    return list_actions(db, limit)
